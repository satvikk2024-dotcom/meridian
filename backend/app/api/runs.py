"""
/api/runs — HTTP routes for triggering and streaming a due diligence run.

Single endpoint for MVP:
  GET /api/runs/stream?company=Reliance+Industries&ticker=RELIANCE.NS

The client opens this as an EventSource. The server runs all agents in
parallel and streams SSE events until run_complete.
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.orchestrator.runner import run_all

router = APIRouter()


@router.get("/runs/stream")
async def stream_run(
    company: str = Query(..., description="Company name, e.g. 'Reliance Industries'"),
    ticker: str = Query(..., description="Exchange ticker, e.g. 'RELIANCE.NS'"),
) -> StreamingResponse:
    """
    Start a due diligence run and stream progress as Server-Sent Events.

    Connect with:
        const es = new EventSource('/api/runs/stream?company=...&ticker=...')
        es.addEventListener('agent_done', e => console.log(JSON.parse(e.data)))
    """
    return StreamingResponse(
        run_all(company, ticker),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering for SSE
        },
    )
