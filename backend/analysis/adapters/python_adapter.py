import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor
from typing import List, Dict, Any
from .base import LanguageAdapter


class PythonAdapter(LanguageAdapter):
    def __init__(self):
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        self.tree = None

    def parse(self, source_code: bytes) -> None:
        """Parses the raw bytes of a Python file into a Tree-sitter tree."""
        self.tree = self.parser.parse(source_code)

    def _captures(self, query_string: str) -> dict:
        """
        Executes a Tree-sitter query and returns the captures dict.
        Uses QueryCursor(query) which is compatible with tree-sitter >= 0.23.
        Returns an empty dict if the tree has not been parsed yet.
        """
        if not self.tree:
            return {}
        query = Query(self.language, query_string)
        cursor = QueryCursor(query)
        result = cursor.captures(self.tree.root_node)
        # result is always a dict: {capture_name: [Node, ...]}
        return result if isinstance(result, dict) else {}

    def extract_imports(self) -> List[str]:
        query_string = """
        (import_statement name: (dotted_name) @import_name)
        (import_from_statement module_name: (dotted_name) @from_name)
        """
        captures = self._captures(query_string)
        imports: set = set()

        for node in captures.get("import_name", []):
            if node.text:
                imports.add(node.text.decode("utf-8"))

        for node in captures.get("from_name", []):
            if node.text:
                imports.add(node.text.decode("utf-8"))

        return list(imports)

    def extract_functions(self) -> List[Dict[str, Any]]:
        query_string = "(function_definition name: (identifier) @func_name)"
        captures = self._captures(query_string)
        functions = []

        for node in captures.get("func_name", []):
            parent_node = node.parent
            if parent_node and node.text:
                functions.append({
                    "name": node.text.decode("utf-8"),
                    "start_line": parent_node.start_point[0],
                    "end_line": parent_node.end_point[0],
                })

        return functions