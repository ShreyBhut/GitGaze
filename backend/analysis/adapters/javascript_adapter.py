import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, Query, QueryCursor
from typing import List, Dict, Any
from .base import LanguageAdapter


class JavascriptAdapter(LanguageAdapter):
    def __init__(self):
        self.language = Language(tsjavascript.language())
        self.parser = Parser(self.language)
        self.tree = None

    def parse(self, source_code: bytes) -> None:
        """Parses the raw bytes of a JS/TS/JSX/TSX file into a Tree-sitter tree."""
        self.tree = self.parser.parse(source_code)

    def _captures(self, query_string: str) -> dict:
        """
        Executes a Tree-sitter query using QueryCursor(query) — compatible with
        tree-sitter >= 0.23. Returns an empty dict if the tree hasn't been parsed.
        """
        if not self.tree:
            return {}
        query = Query(self.language, query_string)
        cursor = QueryCursor(query)
        result = cursor.captures(self.tree.root_node)
        return result if isinstance(result, dict) else {}

    def extract_imports(self) -> List[str]:
        # Matches: import X from 'y'   AND   const x = require('y')
        query_string = """
        (import_statement source: (string (string_fragment) @import_path))
        (call_expression
            function: (identifier) @func_name (#eq? @func_name "require")
            arguments: (arguments (string (string_fragment) @require_path))
        )
        """
        captures = self._captures(query_string)
        imports = []

        for node in captures.get("import_path", []):
            if node.text:
                imports.append(node.text.decode("utf-8"))

        for node in captures.get("require_path", []):
            if node.text:
                imports.append(node.text.decode("utf-8"))

        return list(set(imports))

    def extract_functions(self) -> List[Dict[str, Any]]:
        # Matches standard function declarations and arrow functions assigned to variables
        query_string = """
        (function_declaration name: (identifier) @func_name)
        (variable_declarator
            name: (identifier) @func_name
            value: [(arrow_function) (function_expression)]
        )
        """
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