"""
workers/analysis_worker.py

The background function invoked by FastAPI's BackgroundTasks.

Flow:
  1. Receives snapshot_id, project_path, and an asyncio.Queue pre-created by the route.
  2. Opens its own AsyncSession (the request session is closed after the HTTP response).
  3. Calls orchestrator.analyze_and_persist() which pushes granular progress events.
  4. Pushes a final "done" or "error" sentinel that closes the SSE stream.
  5. Keeps the queue alive for 60 s so late-connecting SSE clients can still drain it.

Design note (AD-001):
  BackgroundTasks runs in the same event loop as the server — no separate threads,
  no Redis, no Celery. Correct for a single-user local developer tool.
"""
import asyncio

from database import AsyncSessionLocal
from analysis.orchestrator import AnalyzerOrchestrator
from workers.progress_store import remove_queue


async def run_analysis(
    snapshot_id: str,
    project_path: str,
    queue: "asyncio.Queue[dict]",
) -> None:
    """
    Entry point for the analysis background task.

    Parameters
    ----------
    snapshot_id:  UUID of the Snapshot row already created by the route handler.
    project_path: Absolute filesystem path to the repository root.
    queue:        The asyncio.Queue registered in progress_store for this snapshot.
    """
    async with AsyncSessionLocal() as session:
        try:
            orchestrator = AnalyzerOrchestrator(project_path)
            await orchestrator.analyze_and_persist(
                session,
                snapshot_id,
                progress_queue=queue,
            )
            # Signal successful completion — SSE consumer will close the stream
            await queue.put({"type": "done", "snapshot_id": snapshot_id})

        except Exception as exc:
            # Signal failure — SSE consumer will close the stream with an error
            await queue.put({"type": "error", "message": str(exc)})

        finally:
            import os
            sleep_time = 0.1 if os.environ.get("TESTING") == "1" else 60
            # Keep the queue alive so clients that connect slightly after completion
            # can still receive the terminal event. Cleaned up after 60 s (0.1s in tests).
            await asyncio.sleep(sleep_time)
            remove_queue(snapshot_id)
