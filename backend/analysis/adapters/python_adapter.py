import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Query, QueryCursor
from typing import List, Dict, Any
from .base import LanguageAdapter

class PythonAdapter(LanguageAdapter):
    def __init__(self):
        # Load the Python grammar
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        self.tree = None

    def parse(self, source_code: bytes) -> None:
        """Parses the raw bytes of a Python file into a Tree-sitter tree."""
        self.tree = self.parser.parse(source_code)

    def extract_imports(self) -> List[str]:
        if not self.tree:
            return []

        # Tree-sitter query to find 'import X' and 'from X import Y'
        query_string = """
        (import_statement name: (dotted_name) @import_name)
        (import_from_statement module_name: (dotted_name) @from_name)
        """
        query = Query(self.language, query_string)
        
        # Create a QueryCursor and execute it to get captures
        cursor = QueryCursor(query)
        captures = cursor.captures(self.tree.root_node)

        imports = []
        
        # captures is a dictionary. We grab the nodes by their tag name.
        for node in captures.get("import_name", []):
            imports.append(node.text.decode('utf-8'))
            
        for node in captures.get("from_name", []):
            imports.append(node.text.decode('utf-8'))
        
        return list(set(imports)) # Return unique imports

    def extract_functions(self) -> List[Dict[str, Any]]:
        if not self.tree:
            return []

        # Tree-sitter query to find function definitions
        query_string = "(function_definition name: (identifier) @func_name)"
        query = Query(self.language, query_string)
        
        # Create a QueryCursor and execute it to get captures
        cursor = QueryCursor(query)
        captures = cursor.captures(self.tree.root_node)

        functions = []
        
        for node in captures.get("func_name", []):
            # 'node' is just the name (e.g., "my_cool_function"). 
            # Its parent is the entire function block!
            parent_node = node.parent 
            
            if parent_node:
                functions.append({
                    "name": node.text.decode('utf-8'),
                    "start_line": parent_node.start_point[0], 
                    "end_line": parent_node.end_point[0]
                })
        
        return functions