"""
Meridian benchmark runner.

Runs the full multi-agent pipeline + baseline on the 6 benchmark companies,
computes metrics, and prints a markdown results table.

Usage:
    cd backend
    python -m app.eval.benchmark               # run all 6 benchmark companies
    python -m app.eval.benchmark --only tcs    # run one company by slug
    python -m app.eval.benchmark --no-baseline # skip baseline comparison

Output:
    data/eval/results.json     full results
    prints markdown table to stdout
"""
import argparse
import asyncio
import json
import time
from pathlib import Path

import structlog

from app.agents.critic import run_critic
from app.eval.baseline import run_baseline
from app.eval.metrics import compute_all
from app.orchestrator.planner import agents_for

logger = structlog.get_logger()

DATASET_PATH = Path(__file__).parent / "dataset" / "companies.json"
RESULTS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "eval" / "results.json"


def load_dataset(only: str | None = None) -> list[dict]:
    companies = json.loads(DATASET_PATH.read_text())
    if only:
        companies = [c for c in companies if c["slug"] == only]
    else:
        companies = [c for c in companies if c["benchmark"]]
    return companies


async def run_system(company: str, ticker: str) -> dict:
    """Run the full multi-agent pipeline and return metrics."""
    agents = agents_for(company, ticker)
    start = time.perf_counter()

    raw_results = await asyncio.gather(
        *[a.run(company, ticker) for a in agents],
        return_exceptions=True,
    )
    results = [
        r for r in raw_results
        if not isinstance(r, Exception) and not r.error
    ]
    failed = len(raw_results) - len(results)

    critic = await run_critic(results)
    elapsed = round(time.perf_counter() - start, 2)

    return {
        "company":       company,
        "ticker":        ticker,
        "mode":          "system",
        "duration_s":    elapsed,
        "agent_count":   len(results),
        "failed_agents": failed,
        **compute_all(results, critic),
    }


def fmt_pct(v: float) -> str:
    return f"{round(v * 100)}%"


def print_table(system_rows: list[dict], baseline_rows: list[dict]) -> None:
    baseline_by_company = {r["company"]: r for r in baseline_rows}

    print("\n## Meridian Benchmark Results\n")
    print(
        "| Company | Sys HAL% | Base HAL% | Citations | Completeness | Duration |"
    )
    print(
        "|---------|----------|-----------|-----------|--------------|----------|"
    )
    for s in system_rows:
        b = baseline_by_company.get(s["company"], {})
        b_hal = fmt_pct(b.get("hallucination_rate", 1.0)) if b else "n/a"
        print(
            f"| {s['company']:<22} "
            f"| {fmt_pct(s['hallucination_rate']):<8} "
            f"| {b_hal:<9} "
            f"| {s['citation_count']:<9} "
            f"| {fmt_pct(s['finding_completeness']):<12} "
            f"| {s['duration_s']}s |"
        )

    # Summary row
    if system_rows:
        avg_hal   = sum(r["hallucination_rate"]   for r in system_rows) / len(system_rows)
        avg_cit   = sum(r["citation_count"]        for r in system_rows) / len(system_rows)
        avg_comp  = sum(r["finding_completeness"]  for r in system_rows) / len(system_rows)
        b_avg_hal = (
            sum(r.get("hallucination_rate", 1.0) for r in baseline_rows) / len(baseline_rows)
            if baseline_rows else None
        )
        b_hal_str = fmt_pct(b_avg_hal) if b_avg_hal is not None else "n/a"
        print(
            f"| **Average**             "
            f"| **{fmt_pct(avg_hal)}**   "
            f"| **{b_hal_str}**   "
            f"| {avg_cit:.1f}      "
            f"| **{fmt_pct(avg_comp)}**    "
            f"|        |"
        )
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Meridian benchmark runner")
    parser.add_argument("--only", help="Run a single company by slug")
    parser.add_argument("--no-baseline", action="store_true", help="Skip baseline comparison")
    parser.add_argument("--output", default=str(RESULTS_PATH))
    args = parser.parse_args()

    companies = load_dataset(args.only)
    if not companies:
        print(f"No companies found. Check --only slug or companies.json.")
        return

    logger.info("benchmark_start", companies=[c["slug"] for c in companies])

    system_rows: list[dict] = []
    baseline_rows: list[dict] = []

    for c in companies:
        name, ticker = c["name"], c["ticker"]

        print(f"\n→ {name} ({ticker})")

        print("  [system]   running agents…", end=" ", flush=True)
        s = await run_system(name, ticker)
        system_rows.append(s)
        print(
            f"done  hal={fmt_pct(s['hallucination_rate'])}  "
            f"cit={s['citation_count']}  "
            f"comp={fmt_pct(s['finding_completeness'])}  "
            f"{s['duration_s']}s"
        )

        if not args.no_baseline:
            print("  [baseline] running…", end=" ", flush=True)
            b = await run_baseline(name, ticker)
            baseline_rows.append(b)
            print(f"done  hal={fmt_pct(b['hallucination_rate'])}")

    # Print results
    print_table(system_rows, baseline_rows)

    # Save JSON
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    all_results = {"system": system_rows, "baseline": baseline_rows}
    out.write_text(json.dumps(all_results, indent=2))
    print(f"Full results → {out}")


if __name__ == "__main__":
    asyncio.run(main())
