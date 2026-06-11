from pathlib import Path
from typing import Dict, Any

from .traversal import RepositoryWalker
from .metrics import MetricsCollector
from .adapters.python_adapter import PythonAdapter
from .adapters.javascript_adapter import JavascriptAdapter

class AnalyzerOrchestrator:
    def __init__(self, target_repo_path: str):
        self.target_repo_path = Path(target_repo_path)
        self.walker = RepositoryWalker(target_repo_path)
        self.metrics_collector = MetricsCollector()
        
        # Registry of supported languages mapping extensions to their parsers
        self.adapters = {
            ".py": PythonAdapter(),
            ".js": JavascriptAdapter(),
            ".ts": JavascriptAdapter(),
            ".jsx": JavascriptAdapter(),
            ".tsx": JavascriptAdapter(),
        }

    def analyze_repo(self) -> Dict[str, Any]:
        """
        Runs the full analysis pipeline on the target repository.
        Returns a dictionary mapping relative file paths to their analysis data.
        """
        results = {}
        
        # 1. Get all eligible files from the walker
        for rel_path in self.walker.walk():
            full_path = self.target_repo_path / rel_path
            extension = full_path.suffix.lower()
            
            # 2. Extract basic line metrics
            file_data = self.metrics_collector.analyze_file(full_path)
            file_data["extension"] = extension
            file_data["path"] = str(rel_path)
            
            # 3. Parse AST for imports and functions if language is supported
            if extension in self.adapters:
                adapter = self.adapters[extension]
                try:
                    # Tree-sitter requires raw bytes
                    with open(full_path, "rb") as f:
                        source_code = f.read()
                    
                    adapter.parse(source_code)
                    file_data["imports"] = adapter.extract_imports()
                    file_data["functions"] = adapter.extract_functions()
                except Exception as e:
                    # Safe fallback if a specific file fails to parse
                    file_data["imports"] = []
                    file_data["functions"] = []
                    file_data["error"] = str(e)
            else:
                # Unsupported languages just get basic metrics (LOC, SLOC, etc.)
                file_data["imports"] = []
                file_data["functions"] = []

            # Store the data using the file's relative path as the key
            # Standardize paths to use forward slashes for frontend consistency
            normalized_path = str(rel_path).replace("\\", "/")
            results[normalized_path] = file_data
            
        return results