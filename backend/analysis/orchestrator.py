import hashlib
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .traversal import RepositoryWalker
from .metrics import MetricsCollector
from .adapters.python_adapter import PythonAdapter
from .adapters.javascript_adapter import JavascriptAdapter


# Map file extensions to their adapter classes
_ADAPTER_MAP = {
    ".py": PythonAdapter,
    ".js": JavascriptAdapter,
    ".ts": JavascriptAdapter,
    ".jsx": JavascriptAdapter,
    ".tsx": JavascriptAdapter,
}


def _sha256(path: Path) -> str:
    """Returns the SHA-256 hex digest of a file's binary content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _analyze_single_file(full_path: Path, rel_path: Path) -> Dict[str, Any]:
    """
    Runs the full per-file analysis pipeline synchronously.
    Returns a dict with metrics, imports, functions and metadata.
    This is intentionally sync so it can be called both from the
    async persist path and the legacy sync test path.
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


class AnalyzerOrchestrator:
    def __init__(self, target_repo_path: str):
        self.target_repo_path = Path(target_repo_path)
        self.walker = RepositoryWalker(target_repo_path)
        self.metrics_collector = MetricsCollector()

    # ------------------------------------------------------------------
    # Legacy synchronous API — kept so existing unit tests keep passing
    # ------------------------------------------------------------------

    def analyze_repo(self) -> Dict[str, Any]:
        """
        Runs the full analysis pipeline and returns a raw dict.
        Does NOT touch the database.
        Used by unit tests and for quick ad-hoc inspection.
        """
        results: Dict[str, Any] = {}

        for rel_path in self.walker.walk():
            full_path = self.target_repo_path / rel_path
            file_data = _analyze_single_file(full_path, rel_path)
            results[file_data["path"]] = file_data

        return results

    # ------------------------------------------------------------------
    # Async DB-persisting API — used by the FastAPI route
    # ------------------------------------------------------------------

    async def analyze_and_persist(self, session: AsyncSession, snapshot_id: str) -> None:
        """
        Runs the full analysis pipeline and persists the results to SQLite.

        Flow:
          1. Mark snapshot as "processing".
          2. Walk and analyse each file.
          3. Insert FileNode rows.
          4. Resolve imports to other known files → insert DependencyEdge rows.
          5. Mark snapshot as "completed". On any error, mark as "failed".
        """
        # Import here to avoid circular imports at module load time
        from models import Snapshot, FileNode, DependencyEdge  # noqa: PLC0415

        try:
            # --- 1. Mark snapshot processing ---
            result = await session.execute(
                select(Snapshot).where(Snapshot.id == snapshot_id)
            )
            snapshot = result.scalar_one()
            snapshot.status = "processing"
            await session.commit()

            # --- 2. Walk repo and build file data ---
            # file_path_str → FileNode id  (for edge resolution)
            path_to_node_id: Dict[str, str] = {}
            raw_results: Dict[str, Dict[str, Any]] = {}

            for rel_path in self.walker.walk():
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
                # Flush to get the node id assigned before we need it
                await session.flush()

                path_to_node_id[posix_path] = node.id
                raw_results[posix_path] = {**file_data, "node_id": node.id}

            # --- 3. Resolve imports → DependencyEdge rows ---
            # Build a set of all known paths without extensions for relative resolution
            known_paths = set(path_to_node_id.keys())

            for posix_path, file_data in raw_results.items():
                source_node_id = path_to_node_id[posix_path]
                source_dir = posix_path.rsplit("/", 1)[0] if "/" in posix_path else ""

                for import_str in file_data.get("imports", []):
                    target_path = _resolve_import(import_str, source_dir, known_paths)
                    if target_path is None:
                        continue  # third-party / stdlib — no edge

                    target_node_id = path_to_node_id[target_path]

                    # Avoid duplicates (the UniqueConstraint will also guard this)
                    edge = DependencyEdge(
                        snapshot_id=snapshot_id,
                        source_node_id=source_node_id,
                        target_node_id=target_node_id,
                        import_string=import_str,
                        edge_type="import",
                    )
                    session.add(edge)

            # --- 4. Mark completed ---
            snapshot.status = "completed"
            snapshot.completed_at = datetime.now(UTC)
            await session.commit()

        except Exception as exc:
            await session.rollback()
            # Try to persist the failure reason so the frontend can surface it
            try:
                result = await session.execute(
                    select(Snapshot).where(Snapshot.id == snapshot_id)
                )
                snapshot = result.scalar_one_or_none()
                if snapshot:
                    snapshot.status = "failed"
                    snapshot.error_message = str(exc)
                    await session.commit()
            except Exception:
                pass  # If we can't even write the failure, give up gracefully
            raise


def _resolve_import(
    import_str: str,
    source_dir: str,
    known_paths: set,
) -> Optional[str]:
    """
    Attempts to resolve a raw import string to a relative repo path.
    Returns the matching path string, or None if unresolvable (third-party/stdlib).

    Handles:
      - Relative imports starting with "./" or "../"
      - Bare module names that match a file in the repo (e.g. "utils" → "utils.py")
    """
    if not import_str.startswith("."):
        # Bare name — not a relative import. Check if it matches a repo file directly.
        # This catches sibling-dir imports like `from utils import foo`
        for ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
            candidate = import_str.replace(".", "/") + ext
            if candidate in known_paths:
                return candidate
        return None  # third-party or stdlib

    # Relative import: resolve from source_dir
    if source_dir:
        base = source_dir + "/" + import_str
    else:
        base = import_str

    # Normalize "./" and "../" components
    parts = []
    for part in base.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)

    resolved_base = "/".join(parts)

    # Try each supported extension
    for ext in (".py", ".js", ".ts", ".jsx", ".tsx"):
        candidate = resolved_base + ext
        if candidate in known_paths:
            return candidate

    # Also try as-is (import might already include extension)
    if resolved_base in known_paths:
        return resolved_base

    return None