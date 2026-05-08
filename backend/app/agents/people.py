"""
People agent. Analyses leadership quality and key-person risk using
the officers list from yfinance and Wikipedia background context.
"""
import structlog
from pydantic import Field

from app.agents.base import Agent, AgentResult, Citation
from app.llm.schemas import LLMOutputBase, parse_response
from app.sources.bse import fetch_stock_data
from app.sources.wikipedia import fetch_summary

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are an executive research analyst covering Indian public companies.
You assess leadership quality and key-person risk based on available data.

Rules:
- Only reference executives named in the data. Do not invent names or roles.
- Note any concentration risk (e.g. founder-led, single dominant leader).
- Keep assessments factual and grounded in the data provided.
"""


class PeopleFindings(LLMOutputBase):
    leadership_overview: str = Field(description="Summary of the leadership team composition")
    key_person_risk: str = Field(description="Assessment of key-person concentration risk")
    founder_presence: str = Field(description="Is the company founder-led? Implications.")
    succession_note: str = Field(description="Any visible succession planning signals")
    key_risks: list[str] = Field(description="Top 2 people/governance risks")
    confidence: float = Field(description="0.0-1.0 — limited by available data")


def _extract_officers(stock_data: dict) -> list[dict]:
    """Pull officer names and titles from yfinance info dict."""
    return stock_data.get("_officers_raw", [])


def _build_prompt(company: str, officers: list[dict], wiki: dict) -> str:
    lines = [f"Analyse the leadership team of {company}.", "", "=== KEY EXECUTIVES ==="]
    if officers:
        for o in officers[:8]:  # cap at 8 to keep prompt tight
            name = o.get("name", "Unknown")
            title = o.get("title", "Unknown")
            lines.append(f"  - {name} ({title})")
    else:
        lines.append("  No officer data available from exchange.")

    if wiki.get("found"):
        lines += ["", "=== COMPANY BACKGROUND ===", wiki["summary"][:600]]

    lines += ["", "Produce a structured leadership analysis using ONLY the data above."]
    return "\n".join(lines)


class PeopleAgent(Agent):
    name = "people"

    async def run(self, company: str, ticker: str) -> AgentResult:
        import asyncio
        import yfinance as yf

        logger.info("people_agent_start", company=company, ticker=ticker)

        # yfinance officers list is inside the info dict; fetch in parallel with Wikipedia
        async def fetch_officers() -> list[dict]:
            import asyncio as _asyncio
            loop = _asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: yf.Ticker(ticker).info)
            return info.get("companyOfficers", [])

        officers, wiki_data = await asyncio.gather(
            fetch_officers(),
            fetch_summary(company),
        )

        stock_data = {"_officers_raw": officers, "ticker": ticker}

        citations = []
        if officers:
            citations.append(Citation(
                source="yfinance", label="Executive Team",
                value=f"{len(officers)} officers listed",
                url=f"https://finance.yahoo.com/quote/{ticker}/profile",
            ))
        if wiki_data.get("found"):
            citations.append(Citation(
                source="wikipedia", label="Company Background",
                value=wiki_data["title"], url=wiki_data["url"],
            ))

        prompt = _build_prompt(company, officers, wiki_data)
        try:
            findings = await parse_response(PeopleFindings, prompt, system=SYSTEM_PROMPT)
            logger.info("people_agent_done", company=company)
            return AgentResult(
                agent_name=self.name,
                company=company,
                findings=findings.model_dump(),
                evidence={"officers": officers, "wikipedia": wiki_data},
                citations=citations,
            )
        except Exception as exc:
            logger.error("people_agent_failed", company=company, error=str(exc))
            return AgentResult(
                agent_name=self.name,
                company=company,
                evidence={"officers": officers, "wikipedia": wiki_data},
                citations=citations,
                error=str(exc),
            )
