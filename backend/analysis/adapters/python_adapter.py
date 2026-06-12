import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query
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

    def _get_captures(self, query_string: str, tag_name: str) -> List[Any]:
        """Safely executes a query and returns nodes, ignoring Tree-sitter version differences."""
        if not self.tree:
            return []
        
        query = Query(self.language, query_string)
        
        # Standard execution supported across most Tree-sitter versions
        try:
            captures = query.captures(self.tree.root_node)
        except AttributeError:
            # Absolute fallback for unconventional local bindings
            from tree_sitter import QueryCursor
            cursor = QueryCursor()
            captures = cursor.captures(query, self.tree.root_node)
            
        # Handle Tree-sitter >= 0.22 (Returns Dict)
        if isinstance(captures, dict):
            return captures.get(tag_name, [])
            
        # Handle Tree-sitter < 0.22 (Returns List of Tuples)
        elif isinstance(captures, list):
            return [node for node, tag in captures if tag == tag_name]
            
        return []

    def extract_imports(self) -> List[str]:
        query_string = """
        (import_statement name: (dotted_name) @import_name)
        (import_from_statement module_name: (dotted_name) @from_name)
        """
        imports = set()
        
        for node in self._get_captures(query_string, "import_name"):
            if node.text:
                imports.add(node.text.decode('utf-8'))
                
        for node in self._get_captures(query_string, "from_name"):
            if node.text:
                imports.add(node.text.decode('utf-8'))
        
        return list(imports)

    def extract_functions(self) -> List[Dict[str, Any]]:
        query_string = "(function_definition name: (identifier) @func_name)"
        functions = []
        
        for node in self._get_captures(query_string, "func_name"):
            parent_node = node.parent 
            if parent_node and node.text:
                functions.append({
                    "name": node.text.decode('utf-8'),
                    "start_line": parent_node.start_point[0], 
                    "end_line": parent_node.end_point[0]
                })
        
        return functions