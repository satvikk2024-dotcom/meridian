"""
Runner: executes agents in parallel and yields SSE-formatted progress events.

Why asyncio.Queue as a message bus?
- asyncio.gather() runs tasks concurrently, but an async generator can only
  yield one value at a time. The Queue bridges the two: tasks push events in
  as they happen; the generator pulls and yields them out.
- This pattern is interview gold — it's a real async fan-out/fan-in design.

Event sequence for a full run:
  run_started   (1 event)
  agent_started (4 events, near-simultaneous)
  agent_done    (4 events, as each finishes — order varies)
  critic_done   (1 event, after all agents complete)
  run_complete  (1 event)
"""
import asyncio
import dataclasses
import json
import time
from typing import AsyncGenerator

import structlog

from app.agents.base import Agent, AgentResult
from app.agents.critic import run_critic
from app.orchestrator import planner

logger = structlog.get_logger()


def _sse(event: str, data: dict) -> str:
    """Format a dict as an SSE message string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def run_all(company: str, ticker: str) -> AsyncGenerator[str, None]:
    """
    Run all agents in parallel and yield SSE event strings as they complete.

    This is an async generator. FastAPI's StreamingResponse iterates it and
    sends each yielded string directly to the client over the HTTP connection.
    """
    agents = planner.agents_for(company, ticker)
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    start = time.perf_counter()

    logger.info("orchestrator_run_start", company=company, ticker=ticker,
                agent_count=len(agents))

    yield _sse("run_started", {
        "company": company,
        "ticker": ticker,
        "agents": [a.name for a in agents],
    })

    async def run_one(agent: Agent) -> AgentResult:
        await queue.put(_sse("agent_started", {"agent": agent.name}))
        result = await agent.run(company, ticker)
        await queue.put(_sse("agent_done", {
            "agent": agent.name,
            "findings": result.findings,
            "citations": [dataclasses.asdict(c) for c in result.citations],
            "error": result.error or None,
        }))
        return result

    # Kick off all agent tasks concurrently — none waits for the others.
    tasks = [asyncio.create_task(run_one(a)) for a in agents]

    # Each agent emits exactly 2 events (started + done), so we drain 2 × n.
    for _ in range(len(agents) * 2):
        yield await queue.get()

    # All tasks must be done by now, but await to surface any unexpected errors.
    results: list[AgentResult] = await asyncio.gather(*tasks)
    failed = [r.agent_name for r in results if r.error]

    # Run the critic on all successful results
    successful = [r for r in results if not r.error]
    critic_result = await run_critic(successful)

    yield _sse("critic_done", {
        "hallucination_rate": critic_result.hallucination_rate,
        "flagged_agents": critic_result.flagged_agents,
        "scores": [
            {
                "agent": s.agent,
                "supported": s.supported,
                "partially_supported": s.partially_supported,
                "unsupported": s.unsupported,
                "summary": s.summary,
            }
            for s in critic_result.scores
        ],
    })

    duration = round(time.perf_counter() - start, 2)
    logger.info("orchestrator_run_complete", company=company, duration_s=duration,
                failed=failed, hallucination_rate=critic_result.hallucination_rate)

    yield _sse("run_complete", {
        "company": company,
        "duration_s": duration,
        "failed_agents": failed,
        "agent_count": len(agents),
        "hallucination_rate": critic_result.hallucination_rate,
    })
