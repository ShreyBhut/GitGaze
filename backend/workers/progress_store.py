"""
workers/progress_store.py

Global in-memory registry mapping snapshot_id → asyncio.Queue.

The background analysis worker pushes typed event dicts into the queue.
The SSE endpoint reads from the same queue and streams them to the client.

Why a module-level dict?
  FastAPI runs everything in a single process with a single event loop.
  A plain dict is safe here — no locking needed because asyncio is single-threaded.
  This is intentionally simple (AD-001: no Redis/Celery for a local dev tool).
"""
import asyncio
from typing import Dict, Optional


# snapshot_id → asyncio.Queue[dict]
_queues: Dict[str, "asyncio.Queue[dict]"] = {}


def create_queue(snapshot_id: str) -> "asyncio.Queue[dict]":
    """Create and register a new progress queue for a snapshot."""
    q: asyncio.Queue = asyncio.Queue()
    _queues[snapshot_id] = q
    return q


def get_queue(snapshot_id: str) -> Optional["asyncio.Queue[dict]"]:
    """Return the queue for a snapshot, or None if it doesn't exist."""
    return _queues.get(snapshot_id)


def remove_queue(snapshot_id: str) -> None:
    """Deregister and discard the queue for a snapshot."""
    _queues.pop(snapshot_id, None)
