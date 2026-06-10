import os
from pathlib import Path
from typing import Dict, Any

class MetricsCollector:
    @staticmethod
    def calculate_metrics(file_content: str, extension: str) -> Dict[str, int]:
        """
        Analyzes file content to calculate total lines (LOC), 
        source lines (SLOC), and comments.
        """
        lines = file_content.splitlines()
        loc = len(lines)
        sloc = 0
        comments = 0
        blanks = 0

        # Define comment prefixes based on language extension
        # Expandable as we add more languages to GitGaze
        script_comments = {".py", ".sh", ".yaml", ".yml"}
        c_style_comments = {".js", ".ts", ".jsx", ".tsx", ".json", ".css"}

        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                blanks += 1
                continue

            # Check for Python/Shell style comments
            if extension in script_comments and stripped.startswith("#"):
                comments += 1
                continue

            # Check for JS/TS single-line comments
            if extension in c_style_comments and stripped.startswith("//"):
                comments += 1
                continue

            # If it's not blank and not a comment line, it's source code
            sloc += 1

        return {
            "loc": loc,
            "sloc": sloc,
            "comments": comments,
            "blanks": blanks
        }

    def analyze_file(self, full_path: Path) -> Dict[str, Any]:
        """Reads a file safely and calculates its metrics."""
        try:
            if not full_path.exists() or not full_path.is_file():
                return {"loc": 0, "sloc": 0, "comments": 0, "blanks": 0}
            
            # Read using UTF-8 and ignore errors for binary/corrupted text file data
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            return self.calculate_metrics(content, full_path.suffix.lower())
        except Exception:
            # Fallback for unexpected file access issues
            return {"loc": 0, "sloc": 0, "comments": 0, "blanks": 0}