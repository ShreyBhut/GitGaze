import os
from pathlib import Path
from typing import Generator, List, Set

class RepositoryWalker:
    def __init__(self, root_path: str, default_ignores: Set[str] = None):
        self.root_path = Path(root_path).resolve()
        # Standard safety blocks to keep analysis fast and secure
        self.ignores = default_ignores or {
            ".git", 
            "node_modules", 
            "__pycache__", 
            ".venv", 
            "venv", 
            "dist", 
            "build",
            ".DS_Store"
        }

    def should_ignore(self, path: Path) -> bool:
        """Check if any segment of the path falls under ignored directories."""
        return any(part in self.ignores for part in path.parts)

    def walk(self) -> Generator[Path, None, None]:
        """Yields relative file paths for all eligible files in the project."""
        if not self.root_path.exists():
            raise FileNotFoundError(f"Target repository path does not exist: {self.root_path}")

        for cert_path in self.root_path.rglob("*"):
            # Ensure it's a file and not hidden/ignored
            if cert_path.is_file():
                # Get path relative to the repository root
                relative_path = cert_path.relative_to(self.root_path)
                if not self.should_ignore(relative_path):
                    yield relative_path

    def scan_summary(self) -> List[str]:
        """Convenience method to return all scanned file tracks as strings."""
        return [str(file) for file in self.walk()]