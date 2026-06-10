from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LanguageAdapter(ABC):
    """
    Abstract base class for all Tree-sitter language parsers.
    Enforces a standard interface for dependency extraction.
    """

    @abstractmethod
    def parse(self, source_code: bytes) -> None:
        """Parses the source code into a syntax tree."""
        pass

    @abstractmethod
    def extract_imports(self) -> List[str]:
        """
        Extracts all imported modules/files.
        Returns a list of raw import strings (e.g., ['react', './utils']).
        """
        pass

    @abstractmethod
    def extract_functions(self) -> List[Dict[str, Any]]:
        """
        Extracts function definitions for potential AI context.
        Returns a list of dicts with 'name', 'start_line', 'end_line'.
        """
        pass