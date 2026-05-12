"""
Meridian benchmark runner.

Runs the full multi-agent pipeline (+ optional baseline) on benchmark companies,
computes all metrics, and writes a structured markdown report.

Usage:
    cd backend
    python -m app.eval.benchmark                  # all 15 benchmark companies
    python -m app.eval.benchmark --only tcs        # one company by slug
    python -m app.eval.benchmark --no-baseline     # skip baseline comparison
    python -m app.eval.benchmark --quick           # first 6 companies only

Output:
    data/eval/results.json      full results (JSON)
    data/eval/report.md         detailed markdown report
"""
import argparse
import asyncio
import json
import time
from pathlib import Path

import structlog

from app.agents.critic import run_critic
from app.eval.baseline import run_baseline
from app.eval.metrics import compute_all, worst_findings
from app.eval.report import generate_report
from app.orchestrator.planner import agents_for

logger = structlog.get_logger()

DATASET_PATH   = Path(__file__).parent / "dataset" / "companies.json"
GT_DIR         = Path(__file__).parent / "dataset"
RESULTS_PATH   = Path(__file__).parent.parent.parent.parent / "data" / "eval" / "results.json"
REPORT_PATH    = Path(__file__).parent.parent.parent.parent / "data" / "eval" / "report.md"
BASELINE_LOCK  = Path(__file__).parent.parent.parent.parent / "data" / "eval" / "baseline_locked.json"


def load_dataset(
    only: str | None = None,
    quick: bool = False,
    count: int | None = None,
) -> list[dict]:
    companies = json.loads(DATASET_PATH.read_text())
    if only:
        return [c for c in companies if c["slug"] == only]
    companies = [c for c in companies if c["benchmark"]]
    if quick:
        return companies[:6]
    if count is not None:
        return companies[:count]
    return companies


def load_ground_truth(slug: str) -> list[dict]:
    """Load verified claims for a company, or return empty list if none exist."""
    path = GT_DIR / f"{slug}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text()).get("claims", [])


async def run_system(company: str, ticker: str, slug: str) -> dict:
    """Run the full multi-agent pipeline and return metrics."""
    agents = agents_for(company, ticker)
    start  = time.perf_counter()

    raw_results = await asyncio.gather(
        *[a.run(company, ticker) for a in agents],
        return_exceptions=True,
    )
    results = [
        r for r in raw_results
        if not isinstance(r, Exception) and not r.error
    ]
    failed = len(raw_results) - len(results)

    critic   = await run_critic(results)
    elapsed  = round(time.perf_counter() - start, 2)
    gt_claims = load_ground_truth(slug)

    return {
        "company":       company,
        "ticker":        ticker,
        "slug":          slug,
        "mode":          "system",
        "duration_s":    elapsed,
        "agent_count":   len(results),
        "failed_agents": failed,
        "_results":      results,   # kept for worst_findings; stripped before JSON save
        "_critic":       critic,    # kept for worst_findings; stripped before JSON save
        **compute_all(results, critic, gt_claims or None),
    }


def _strip_internal(row: dict) -> dict:
    """Remove non-serialisable internal fields before saving to JSON."""
    return {k: v for k, v in row.items() if not k.startswith("_")}


def fmt_pct(v: float) -> str:
    return f"{round(v * 100)}%"


def print_table(system_rows: list[dict], baseline_rows: list[dict]) -> None:
    baseline_by = {r["company"]: r for r in baseline_rows}

    print("\n## Meridian Benchmark Results\n")
    print("| Company | Sys HAL% | Base HAL% | Citations | Completeness | GT Cov | Duration |")
    print("|---------|----------|-----------|-----------|--------------|--------|----------|")
    for s in system_rows:
        b     = baseline_by.get(s["company"], {})
        b_hal = fmt_pct(b.get("hallucination_rate", 1.0)) if b else "n/a"
        gt    = s.get("ground_truth_coverage")
        gt_s  = fmt_pct(gt) if gt is not None else "n/a"
        print(
            f"| {s['company']:<22} "
            f"| {fmt_pct(s['hallucination_rate']):<8} "
            f"| {b_hal:<9} "
            f"| {s['citation_count']:<9} "
            f"| {fmt_pct(s['finding_completeness']):<12} "
            f"| {gt_s:<6} "
            f"| {s['duration_s']}s |"
        )

    if system_rows:
        avg_hal  = sum(r["hallucination_rate"]  for r in system_rows) / len(system_rows)
        avg_cit  = sum(r["citation_count"]       for r in system_rows) / len(system_rows)
        avg_comp = sum(r["finding_completeness"] for r in system_rows) / len(system_rows)
        gt_vals  = [r["ground_truth_coverage"] for r in system_rows if "ground_truth_coverage" in r]
        avg_gt   = sum(gt_vals) / len(gt_vals) if gt_vals else None
        b_avg    = (
            sum(r.get("hallucination_rate", 1.0) for r in baseline_rows) / len(baseline_rows)
            if baseline_rows else None
        )
        print(
            f"| **Average**             "
            f"| **{fmt_pct(avg_hal)}**   "
            f"| **{fmt_pct(b_avg) if b_avg is not None else 'n/a'}**   "
            f"| {avg_cit:.1f}      "
            f"| **{fmt_pct(avg_comp)}**    "
            f"| {fmt_pct(avg_gt) if avg_gt is not None else 'n/a'}   "
            f"|        |"
        )
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Meridian benchmark runner")
    parser.add_argument("--only",        help="Run a single company by slug")
    parser.add_argument("--no-baseline", action="store_true", help="Skip baseline")
    parser.add_argument("--quick",       action="store_true", help="First 6 companies only")
    parser.add_argument("--count",       type=int,            help="Run first N benchmark companies")
    parser.add_argument("--output",      default=str(RESULTS_PATH))
    args = parser.parse_args()

    companies = load_dataset(args.only, args.quick, args.count)
    if not companies:
        print("No companies found. Check --only slug or companies.json.")
        return

    logger.info("benchmark_start", companies=[c["slug"] for c in companies])

    system_rows:   list[dict] = []
    baseline_rows: list[dict] = []

    for c in companies:
        name, ticker, slug = c["name"], c["ticker"], c["slug"]

        print(f"\n→ {name} ({ticker})")

        print("  [system]   running agents…", end=" ", flush=True)
        s = await run_system(name, ticker, slug)
        system_rows.append(s)
        gt_str = f"  gt={fmt_pct(s['ground_truth_coverage'])}" if "ground_truth_coverage" in s else ""
        print(
            f"done  hal={fmt_pct(s['hallucination_rate'])}  "
            f"cit={s['citation_count']}  "
            f"comp={fmt_pct(s['finding_completeness'])}"
            f"{gt_str}  {s['duration_s']}s"
        )

        if not args.no_baseline:
            print("  [baseline] running…", end=" ", flush=True)
            b = await run_baseline(name, ticker)
            baseline_rows.append(b)
            print(f"done  hal={fmt_pct(b['hallucination_rate'])}")

    # Collect worst findings across all companies (top 10)
    all_worst: list[dict] = []
    for s in system_rows:
        results = s.get("_results", [])
        critic  = s.get("_critic")
        if results and critic:
            all_worst.extend(worst_findings(results, critic, n=3))
    all_worst = all_worst[:10]

    # Print summary table
    print_table(system_rows, baseline_rows)

    # Save JSON (strip internal fields first)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    all_results = {
        "system":   [_strip_internal(r) for r in system_rows],
        "baseline": baseline_rows,
    }
    out.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"Full results → {out}")

    # Generate and save markdown report
    clean_rows = [_strip_internal(r) for r in system_rows]
    report_md  = generate_report(clean_rows, baseline_rows, all_worst)
    rp = Path(str(REPORT_PATH))
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(report_md)
    print(f"Report       → {rp}")

    # Save locked baseline (first run after a milestone = reference for next fixes)
    if not BASELINE_LOCK.exists():
        BASELINE_LOCK.write_text(json.dumps(all_results, indent=2, default=str))
        print(f"Baseline locked → {BASELINE_LOCK}")
    else:
        print(f"Baseline already locked (delete {BASELINE_LOCK} to reset)")


if __name__ == "__main__":
    asyncio.run(main())
