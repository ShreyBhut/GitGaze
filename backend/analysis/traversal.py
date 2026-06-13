import os
from pathlib import Path
from typing import Generator, List, Optional, Set

try:
    import pathspec  # type: ignore
    _PATHSPEC_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PATHSPEC_AVAILABLE = False


# Directories that are always skipped regardless of .gitignore
# Kept as a fast first-pass guard before pathspec evaluation
_HARD_IGNORE_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".DS_Store",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    ".coverage",
}


class RepositoryWalker:
    """
    Walks a local repository, yielding relative paths to every eligible file.

    Skipping strategy (in order):
      1. Hard-ignore set — fastest, catches the most common dirs.
      2. .gitignore rules — parsed via pathspec if available and .gitignore exists.
      3. Optional caller-supplied extra ignore set.
    """

    def __init__(
        self,
        root_path: str,
        extra_ignores: Optional[Set[str]] = None,
    ):
        self.root_path = Path(root_path).resolve()
        self.extra_ignores = extra_ignores or set()

        # Combine hard ignores with any caller-supplied extras
        self._ignore_names: Set[str] = _HARD_IGNORE_DIRS | self.extra_ignores

        # Load .gitignore rules if pathspec is available
        self._gitignore_spec: Optional[object] = None
        if _PATHSPEC_AVAILABLE:
            self._gitignore_spec = self._load_gitignore()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_gitignore(self) -> Optional[object]:
        """
        Reads the repository root .gitignore and compiles it into a pathspec.
        Returns None if the file doesn't exist or pathspec is unavailable.
        """
        gitignore_path = self.root_path / ".gitignore"
        if not gitignore_path.is_file():
            return None

        try:
            lines = gitignore_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", lines)  # type: ignore
        except Exception:
            # Never crash because of a malformed .gitignore
            return None

    def _is_hard_ignored(self, relative_path: Path) -> bool:
        """Returns True if any path component matches the hard-ignore set."""
        return any(part in self._ignore_names for part in relative_path.parts)

    def _is_gitignore_ignored(self, relative_path: Path) -> bool:
        """Returns True if the path matches any .gitignore rule."""
        if self._gitignore_spec is None:
            return False
        # pathspec expects forward-slash strings
        posix_path = relative_path.as_posix()
        return self._gitignore_spec.match_file(posix_path)  # type: ignore

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def should_ignore(self, relative_path: Path) -> bool:
        """
        Central decision point. Returns True if the file/dir should be skipped.
        """
        return self._is_hard_ignored(relative_path) or self._is_gitignore_ignored(relative_path)

    def walk(self) -> Generator[Path, None, None]:
        """
        Yields relative Path objects for all eligible files under root_path.
        Raises FileNotFoundError if the root path does not exist.
        """
        if not self.root_path.exists():
            raise FileNotFoundError(
                f"Target repository path does not exist: {self.root_path}"
            )

        for abs_path in self.root_path.rglob("*"):
            if abs_path.is_file():
                relative_path = abs_path.relative_to(self.root_path)
                if not self.should_ignore(relative_path):
                    yield relative_path

    def scan_summary(self) -> List[str]:
        """Convenience wrapper — returns all eligible paths as forward-slash strings."""
        return [p.as_posix() for p in self.walk()]