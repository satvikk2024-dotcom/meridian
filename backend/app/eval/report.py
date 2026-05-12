"""
Markdown report generator for Meridian benchmark runs.

Produces a structured report from benchmark results, including:
  - Summary table with per-agent HAL breakdown
  - Cross-agent hallucination analysis
  - Source coverage breakdown
  - Top worst findings (unsupported, with full context)
  - Ground-truth coverage per company

Usage (called by benchmark.py after all runs complete):
    report_md = generate_report(system_rows, baseline_rows, worst_list)
    Path("data/eval/report.md").write_text(report_md)
"""
from datetime import datetime


def _pct(v: float) -> str:
    return f"{round(v * 100)}%"


def generate_report(
    system_rows: list[dict],
    baseline_rows: list[dict],
    worst_list: list[dict],
) -> str:
    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append("# Meridian Benchmark Report")
    lines.append(f"_Generated: {now} | Companies: {len(system_rows)}_\n")

    # ------------------------------------------------------------------
    # 1. Summary table
    # ------------------------------------------------------------------
    lines.append("## Summary\n")
    lines.append(
        "| Company | HAL% | Citations | Completeness | GT Coverage |"
    )
    lines.append(
        "|---------|------|-----------|--------------|-------------|"
    )
    for s in system_rows:
        gt = s.get("ground_truth_coverage")
        gt_str = _pct(gt) if gt is not None else "n/a"
        lines.append(
            f"| {s['company']:<25} "
            f"| {_pct(s['hallucination_rate']):<5} "
            f"| {s['citation_count']:<9} "
            f"| {_pct(s['finding_completeness']):<12} "
            f"| {gt_str} |"
        )

    if system_rows:
        avg_hal  = sum(r["hallucination_rate"]  for r in system_rows) / len(system_rows)
        avg_cit  = sum(r["citation_count"]       for r in system_rows) / len(system_rows)
        avg_comp = sum(r["finding_completeness"] for r in system_rows) / len(system_rows)
        gt_vals  = [r["ground_truth_coverage"] for r in system_rows if "ground_truth_coverage" in r]
        avg_gt   = sum(gt_vals) / len(gt_vals) if gt_vals else None
        gt_avg_str = _pct(avg_gt) if avg_gt is not None else "n/a"
        lines.append(
            f"| **Average**                "
            f"| **{_pct(avg_hal)}** "
            f"| {avg_cit:.1f}      "
            f"| **{_pct(avg_comp)}**  "
            f"| {gt_avg_str} |"
        )
    lines.append("")

    # ------------------------------------------------------------------
    # 2. Per-agent hallucination breakdown
    # ------------------------------------------------------------------
    lines.append("## Per-Agent Hallucination Rates\n")
    agent_rates: dict[str, list[float]] = {}
    for s in system_rows:
        for agent, rate in s.get("per_agent_hal", {}).items():
            agent_rates.setdefault(agent, []).append(rate)

    lines.append("| Agent | Avg HAL% | Worst | Best |")
    lines.append("|-------|----------|-------|------|")
    for agent, rates in sorted(agent_rates.items()):
        avg   = sum(rates) / len(rates)
        worst = max(rates)
        best  = min(rates)
        lines.append(
            f"| {agent:<12} "
            f"| {_pct(avg):<9} "
            f"| {_pct(worst):<6} "
            f"| {_pct(best)} |"
        )
    lines.append("")

    # Per-company agent breakdown table
    lines.append("### By Company\n")
    agents_seen = sorted({
        a for s in system_rows for a in s.get("per_agent_hal", {})
    })
    header = "| Company | " + " | ".join(f"{a[:8]}" for a in agents_seen) + " |"
    sep    = "|---------|" + "|".join("-" * (len(a[:8]) + 2) for a in agents_seen) + "|"
    lines.append(header)
    lines.append(sep)
    for s in system_rows:
        per = s.get("per_agent_hal", {})
        cells = " | ".join(_pct(per.get(a, 0.0)) for a in agents_seen)
        lines.append(f"| {s['company']:<25} | {cells} |")
    lines.append("")

    # ------------------------------------------------------------------
    # 3. Source citation breakdown
    # ------------------------------------------------------------------
    lines.append("## Citation Source Breakdown\n")
    source_totals: dict[str, int] = {}
    for s in system_rows:
        for src, cnt in s.get("source_breakdown", {}).items():
            source_totals[src] = source_totals.get(src, 0) + cnt

    total_cit = sum(source_totals.values()) or 1
    lines.append("| Source | Total Citations | Share |")
    lines.append("|--------|-----------------|-------|")
    for src, cnt in sorted(source_totals.items(), key=lambda x: -x[1]):
        lines.append(f"| {src:<12} | {cnt:<15} | {_pct(cnt / total_cit)} |")
    lines.append("")

    # ------------------------------------------------------------------
    # 4. Baseline comparison
    # ------------------------------------------------------------------
    if baseline_rows:
        lines.append("## Baseline vs System\n")
        bl_by = {r["company"]: r for r in baseline_rows}
        lines.append("| Company | Sys HAL% | Base HAL% | Sys Citations | Base Citations |")
        lines.append("|---------|----------|-----------|---------------|----------------|")
        for s in system_rows:
            b = bl_by.get(s["company"], {})
            b_hal = _pct(b.get("hallucination_rate", 1.0)) if b else "n/a"
            b_cit = b.get("citation_count", 0) if b else "n/a"
            lines.append(
                f"| {s['company']:<25} "
                f"| {_pct(s['hallucination_rate']):<9} "
                f"| {b_hal:<9} "
                f"| {s['citation_count']:<13} "
                f"| {b_cit} |"
            )
        lines.append("")

    # ------------------------------------------------------------------
    # 5. Top worst findings
    # ------------------------------------------------------------------
    if worst_list:
        lines.append("## Top Problematic Findings\n")
        lines.append(
            "_Findings flagged as unsupported by the critic across all companies:_\n"
        )
        for i, f in enumerate(worst_list, 1):
            lines.append(
                f"### {i}. `{f['finding_key']}` — {f['agent']} agent — {f['company']}"
            )
            lines.append(f"> {f['finding_value']}\n")

    return "\n".join(lines)
