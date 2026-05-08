"""
Base agent interface. All research agents inherit from Agent.

Why a base class?
- Forces every agent to produce the same shape of output (AgentResult).
- The orchestrator can call any agent without knowing its internals.
- Interviewers immediately recognise this as a well-designed interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Citation:
    """A pointer from a finding back to the raw evidence that supports it."""
    source: str       # e.g. "yfinance", "bse_filing", "wikipedia"
    label: str        # human-readable description, e.g. "Revenue FY2024"
    value: str        # the actual fact: "₹8.97L Cr"
    url: str = ""     # original URL if available


@dataclass
class AgentResult:
    """
    Structured output returned by every agent.

    findings  — LLM-generated analysis (interpretive, may be wrong)
    evidence  — raw facts fetched from sources (verifiable)
    citations — links each finding back to supporting evidence
    error     — non-empty if the agent failed; findings will be empty
    """
    agent_name: str
    company: str
    findings: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)
    citations: list[Citation] = field(default_factory=list)
    error: str = ""


class Agent(ABC):
    """Abstract base class for all research agents."""

    name: str = "base"

    @abstractmethod
    async def run(self, company: str, ticker: str) -> AgentResult:
        """
        Fetch data for `company` / `ticker` and return structured findings.

        Args:
            company: Human-readable name, e.g. "Reliance Industries"
            ticker:  Exchange ticker, e.g. "RELIANCE.NS" or "RELIANCE.BO"
        """
        ...
