"""
analysis/orchestrator.py

Coordinates the full per-repository analysis pipeline.

Public API
----------
analyze_repo()           — synchronous, returns raw dict. Used by unit tests.
analyze_and_persist()    — async, writes FileNode + DependencyEdge rows to SQLite
                           and optionally streams progress events via asyncio.Queue.
"""
import asyncio
import hashlib
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .traversal import RepositoryWalker
from .metrics import MetricsCollector
from .adapters.python_adapter import PythonAdapter
from .adapters.javascript_adapter import JavascriptAdapter


# Map file extensions → adapter classes (instantiated lazily per file)
_ADAPTER_MAP = {
    ".py": PythonAdapter,
    ".js": JavascriptAdapter,
    ".ts": JavascriptAdapter,
    ".jsx": JavascriptAdapter,
    ".tsx": JavascriptAdapter,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    """SHA-256 hex digest of a file's binary content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65_536), b""):
            h.update(chunk)
    return h.hexdigest()


async def _push(queue: Optional["asyncio.Queue[dict]"], event: dict) -> None:
    """Safely push a progress event if a queue is registered."""
    if queue is not None:
        await queue.put(event)


def _analyze_single_file(full_path: Path, rel_path: Path) -> Dict[str, Any]:
    """
    Runs the full per-file pipeline synchronously.
    Returns a dict with metrics, imports, functions, and metadata.
    Kept synchronous so both the async persist path and legacy test path can use it.
    """
    extension = full_path.suffix.lower()
    metrics_collector = MetricsCollector()
    file_data: Dict[str, Any] = metrics_collector.analyze_file(full_path)
    file_data["extension"] = extension
    file_data["path"] = rel_path.as_posix()

    if extension in _ADAPTER_MAP:
        adapter = _ADAPTER_MAP[extension]()
        try:
            with open(full_path, "rb") as f:
                source_code = f.read()
            adapter.parse(source_code)
            file_data["imports"] = adapter.extract_imports()
            file_data["functions"] = adapter.extract_functions()
        except Exception as e:
            file_data["imports"] = []
            file_data["functions"] = []
            file_data["parse_error"] = str(e)
    else:
        file_data["imports"] = []
        file_data["functions"] = []

    return file_data


def _resolve_import(
    import_str: str,
    source_dir: str,
    known_paths: set,
) -> Optional[str]:
    """
    Resolve a raw import string to a relative repo path string.
    Returns None for third-party / stdlib imports that can't be mapped.
    """
    if not import_str.startswith("."):
        # Bare name — check if a repo file matches directly
        for ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
            candidate = import_str.replace(".", "/") + ext
            if candidate in known_paths:
                return candidate
        return None

    # Relative import — resolve from source_dir
    base = (source_dir + "/" + import_str) if source_dir else import_str
    parts: List[str] = []
    for part in base.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)

    resolved_base = "/".join(parts)

    for ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
        candidate = resolved_base + ext
        if candidate in known_paths:
            return candidate

    if resolved_base in known_paths:
        return resolved_base

    return None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class AnalyzerOrchestrator:
    def __init__(self, target_repo_path: str):
        self.target_repo_path = Path(target_repo_path)
        self.walker = RepositoryWalker(target_repo_path)
        self.metrics_collector = MetricsCollector()

    # ------------------------------------------------------------------
    # Legacy synchronous API — keeps existing unit tests passing
    # ------------------------------------------------------------------

    def analyze_repo(self) -> Dict[str, Any]:
        """
        Runs the full analysis pipeline and returns a raw dict.
        Does NOT touch the database. Used by unit tests.
        """
        results: Dict[str, Any] = {}
        for rel_path in self.walker.walk():
            full_path = self.target_repo_path / rel_path
            file_data = _analyze_single_file(full_path, rel_path)
            results[file_data["path"]] = file_data
        return results

    # ------------------------------------------------------------------
    # Async DB-persisting API — used by the background worker
    # ------------------------------------------------------------------

    async def analyze_and_persist(
        self,
        session: AsyncSession,
        snapshot_id: str,
        progress_queue: Optional["asyncio.Queue[dict]"] = None,
    ) -> None:
        """
        Full analysis pipeline that persists FileNode + DependencyEdge rows to SQLite.
        Pushes granular progress events to progress_queue if provided.

        Stages:
          0% — start
          5% — traversal (listing files)
          10–85% — per-file analysis
          85–95% — edge resolution
          100% — committed (terminal "done" is sent by the worker, not here)
        """
        from models import Snapshot, FileNode, DependencyEdge  # noqa: PLC0415

        await _push(progress_queue, {
            "type": "progress", "stage": "start", "pct": 0,
            "message": "Starting analysis…",
        })

        # --- 1. Mark snapshot processing ---
        result = await session.execute(
            select(Snapshot).where(Snapshot.id == snapshot_id)
        )
        snapshot = result.scalar_one()
        snapshot.status = "processing"
        await session.commit()

        # --- 2. Traverse repo and collect file paths ---
        rel_paths = list(self.walker.walk())
        total = len(rel_paths) or 1  # avoid division by zero

        await _push(progress_queue, {
            "type": "progress", "stage": "traversal", "pct": 5,
            "message": f"Found {total} file{'s' if total != 1 else ''}",
        })

        # --- 3. Analyse each file and insert FileNode rows ---
        path_to_node_id: Dict[str, str] = {}
        raw_results: Dict[str, Dict[str, Any]] = {}

        for i, rel_path in enumerate(rel_paths):
            full_path = self.target_repo_path / rel_path
            file_data = _analyze_single_file(full_path, rel_path)
            posix_path = rel_path.as_posix()
            content_hash = _sha256(full_path)

            node = FileNode(
                snapshot_id=snapshot_id,
                file_path=posix_path,
                content_hash=content_hash,
                node_type="file",
                language=file_data.get("extension"),
                metrics={
                    "loc": file_data.get("loc", 0),
                    "sloc": file_data.get("sloc", 0),
                    "comments": file_data.get("comments", 0),
                    "blanks": file_data.get("blanks", 0),
                },
                imports=file_data.get("imports", []),
                functions=file_data.get("functions", []),
            )
            session.add(node)
            await session.flush()  # assigns node.id

            path_to_node_id[posix_path] = node.id
            raw_results[posix_path] = {**file_data, "node_id": node.id}

            # Report progress: 10% → 85% spread across all files
            pct = 10 + int((i + 1) / total * 75)
            await _push(progress_queue, {
                "type": "progress", "stage": "analysis", "pct": pct,
                "message": f"Analysing {posix_path} ({i + 1}/{total})",
            })

        # --- 4. Resolve imports → DependencyEdge rows ---
        await _push(progress_queue, {
            "type": "progress", "stage": "edges", "pct": 85,
            "message": "Resolving dependency edges…",
        })

        known_paths = set(path_to_node_id.keys())
        seen_edges: set = set()

        for posix_path, file_data in raw_results.items():
            source_node_id = path_to_node_id[posix_path]
            source_dir = posix_path.rsplit("/", 1)[0] if "/" in posix_path else ""

            for import_str in file_data.get("imports", []):
                target_path = _resolve_import(import_str, source_dir, known_paths)
                if target_path is None:
                    continue

                target_node_id = path_to_node_id[target_path]
                edge_key = (source_node_id, target_node_id)
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)

                session.add(DependencyEdge(
                    snapshot_id=snapshot_id,
                    source_node_id=source_node_id,
                    target_node_id=target_node_id,
                    import_string=import_str,
                    edge_type="import",
                ))

        # --- 5. Finalise ---
        await _push(progress_queue, {
            "type": "progress", "stage": "saving", "pct": 95,
            "message": "Saving results…",
        })

        snapshot.status = "completed"
        snapshot.completed_at = datetime.now(UTC)

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        await _push(progress_queue, {
            "type": "progress", "stage": "done", "pct": 100,
            "message": "Analysis complete",
        })