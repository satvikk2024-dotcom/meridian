import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


def sse_message(event: str, data: dict) -> str:
    """
    Format a single Server-Sent Event message.
    The double newline is the SSE message terminator — without it the
    browser's EventSource will buffer indefinitely and never fire.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _fake_run_stream():
    """
    Simulates the event sequence a real run will produce.
    Each yield pushes one SSE message to the connected client.
    In Phase 5 this gets replaced by the real orchestrator's event queue.
    """
    steps = [
        ("planning_started",      {"message": "Planner is deciding which agents to run"}),
        ("agents_dispatched",     {"agents": ["financial", "market", "people", "customer"]}),
        ("agent_started",         {"agent": "financial"}),
        ("agent_started",         {"agent": "market"}),
        ("agent_started",         {"agent": "people"}),
        ("agent_started",         {"agent": "customer"}),
        ("agent_completed",       {"agent": "financial", "findings": 8}),
        ("agent_completed",       {"agent": "market",    "findings": 6}),
        ("agent_completed",       {"agent": "people",    "findings": 4}),
        ("agent_completed",       {"agent": "customer",  "findings": 5}),
        ("critic_started",        {"total_findings": 23}),
        ("critic_completed",      {"approved": 20, "flagged": 3}),
        ("synthesis_started",     {}),
        ("memo_ready",            {"sections": 6}),
    ]

    for event, data in steps:
        yield sse_message(event, data)
        await asyncio.sleep(0.6)  # simulate processing time


@router.get("/demo/stream")
async def demo_stream():
    """
    Proof-of-concept SSE endpoint. Streams a fake due diligence run.
    Open in browser: http://localhost:8000/api/demo/stream
    Or test with: curl -N http://localhost:8000/api/demo/stream
    """
    return StreamingResponse(
        _fake_run_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disables nginx buffering in production
            "Connection": "keep-alive",
        },
    )
