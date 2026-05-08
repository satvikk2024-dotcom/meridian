"""
Critic agent. Runs after all research agents complete and scores each
finding for citation support.

Why a separate agent, not inline validation?
- Separation of concerns: research agents produce claims; the critic verifies them.
- The critic uses a different prompt persona (skeptic vs analyst).
- It can be disabled, swapped, or run async without touching agent code.

Schema design note:
- We intentionally avoid list[NestedModel] in the output schema.
  qwen2.5:7b handles flat lists reliably but collapses nested list-of-objects
  into flat strings. Instead, findings are categorised into three flat lists
  (supported / partially_supported / unsupported). Same information, simpler shape.

Scoring rubric:
  supported           — the finding directly references a number or fact in evidence
  partially_supported — some claims grounded, some extrapolated
  unsupported         — no evidence in the payload supports this claim
"""
import asyncio
import dataclasses
import json

import structlog
from pydantic import Field

from app.agents.base import AgentResult
from app.llm.schemas import LLMOutputBase, parse_response

logger = structlog.get_logger()

CRITIC_SYSTEM = """You are a strict fact-checker reviewing AI-generated research findings.
Your job is to categorise each finding by how well it is supported by the evidence.

Definitions:
- supported: the finding directly references a number or fact present in the evidence
- partially_supported: mostly grounded but includes some inference or extrapolation
- unsupported: makes a claim with NO basis in the provided evidence (potential hallucination)

Be strict. Confident language does not make a finding supported — only evidence does.
Respond by placing each finding KEY (not value) into the correct list."""


class AgentCriticOutput(LLMOutputBase):
    """
    Flat-list schema to work reliably with small models.
    Each list contains the finding field *keys* (e.g. "revenue_trend").
    """
    agent: str = Field(description="Name of the agent being reviewed")
    supported: list[str] = Field(
        description="Finding keys clearly supported by the evidence"
    )
    partially_supported: list[str] = Field(
        description="Finding keys partially supported — some inference used"
    )
    unsupported: list[str] = Field(
        description="Finding keys with no evidence basis — potential hallucinations"
    )
    summary: str = Field(
        description="One sentence overall quality assessment of this agent's findings"
    )


@dataclasses.dataclass
class CriticResult:
    scores: list[AgentCriticOutput]
    hallucination_rate: float   # fraction of findings scored 'unsupported'
    flagged_agents: list[str]   # agents with at least one unsupported finding


def _build_critic_prompt(result: AgentResult) -> str:
    # List the finding keys and values
    finding_lines = []
    for key, val in result.findings.items():
        val_str = json.dumps(val) if isinstance(val, (list, dict)) else str(val)
        finding_lines.append(f"  {key}: {val_str[:250]}")

    # Flatten evidence to readable key: value lines
    evidence_lines: list[str] = []
    for source, data in result.evidence.items():
        if not isinstance(data, dict):
            continue
        evidence_lines.append(f"\n  [{source}]")
        for k, v in data.items():
            if k.startswith("_") or k in ("business_summary", "summary", "title", "url", "found"):
                continue
            if isinstance(v, str) and len(v) > 200:
                v = v[:200] + "..."
            evidence_lines.append(f"    {k}: {v}")

    finding_keys = list(result.findings.keys())

    return (
        f"Review the '{result.agent_name}' agent's findings against the evidence.\n\n"
        f"=== FINDING KEYS TO CATEGORISE ===\n"
        f"  {finding_keys}\n\n"
        f"=== FINDINGS ===\n" + "\n".join(finding_lines) + "\n\n"
        f"=== EVIDENCE THE AGENT HAD ACCESS TO ===\n" + "\n".join(evidence_lines) + "\n\n"
        f"Place each finding key into supported, partially_supported, or unsupported.\n"
        f"The agent name is '{result.agent_name}'."
    )


async def _score_one(result: AgentResult) -> AgentCriticOutput | None:
    """Score a single agent's findings. Returns None if no findings."""
    if not result.findings:
        logger.warning("critic_skip_no_findings", agent=result.agent_name)
        return None

    prompt = _build_critic_prompt(result)
    try:
        output = await parse_response(AgentCriticOutput, prompt, system=CRITIC_SYSTEM)
        logger.info(
            "critic_scored",
            agent=result.agent_name,
            unsupported=len(output.unsupported),
        )
        return output
    except Exception as exc:
        logger.error("critic_score_failed", agent=result.agent_name, error=str(exc))
        return None


async def run_critic(results: list[AgentResult]) -> CriticResult:
    """
    Score all agent results in parallel and compute a hallucination rate.

    Args:
        results: Successful AgentResults from all research agents.
    """
    logger.info("critic_start", agent_count=len(results))

    scored = await asyncio.gather(*[_score_one(r) for r in results])
    valid: list[AgentCriticOutput] = [s for s in scored if s is not None]

    total = sum(
        len(s.supported) + len(s.partially_supported) + len(s.unsupported)
        for s in valid
    )
    unsupported_count = sum(len(s.unsupported) for s in valid)
    rate = round(unsupported_count / total, 3) if total > 0 else 0.0
    flagged = [s.agent for s in valid if s.unsupported]

    logger.info(
        "critic_done",
        total_findings=total,
        unsupported=unsupported_count,
        hallucination_rate=rate,
        flagged_agents=flagged,
    )

    return CriticResult(scores=valid, hallucination_rate=rate, flagged_agents=flagged)
