import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, Query, QueryCursor
from typing import List, Dict, Any
from .base import LanguageAdapter

class JavascriptAdapter(LanguageAdapter):
    def __init__(self):
        # Load the JavaScript grammar
        self.language = Language(tsjavascript.language())
        self.parser = Parser(self.language)
        self.tree = None

    def parse(self, source_code: bytes) -> None:
        """Parses the raw bytes of a JS/TS file into a Tree-sitter tree."""
        self.tree = self.parser.parse(source_code)

    def extract_imports(self) -> List[str]:
        if not self.tree:
            return []

        # Matches: import X from 'y' AND const x = require('y')
        query_string = """
        (import_statement source: (string (string_fragment) @import_path))
        (call_expression 
            function: (identifier) @func_name (#eq? @func_name "require")
            arguments: (arguments (string (string_fragment) @require_path))
        )
        """
        query = Query(self.language, query_string)
        cursor = QueryCursor(query)
        captures = cursor.captures(self.tree.root_node)

        imports = []
        for node in captures.get("import_path", []):
            imports.append(node.text.decode('utf-8'))
            
        for node in captures.get("require_path", []):
            imports.append(node.text.decode('utf-8'))
            
        return list(set(imports))

    def extract_functions(self) -> List[Dict[str, Any]]:
        if not self.tree:
            return []

        # Matches standard functions and arrow functions assigned to variables
        query_string = """
        (function_declaration name: (identifier) @func_name)
        (variable_declarator 
            name: (identifier) @func_name 
            value: [(arrow_function) (function_expression)]
        )
        """
        query = Query(self.language, query_string)
        cursor = QueryCursor(query)
        captures = cursor.captures(self.tree.root_node)

        functions = []
        for node in captures.get("func_name", []):
            parent_node = node.parent
            if parent_node:
                functions.append({
                    "name": node.text.decode('utf-8'),
                    "start_line": parent_node.start_point[0],
                    "end_line": parent_node.end_point[0]
                })
        
        return functions