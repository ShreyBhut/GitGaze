import pytest
from analysis.adapters.python_adapter import PythonAdapter

def test_python_adapter_extraction():
    adapter = PythonAdapter()
    
    # Sample code to parse (must be bytes, which is why there's a 'b' prefix)
    sample_code = b"""
import os
import sys
from pathlib import Path
import tree_sitter_python as tspython

def my_cool_function():
    pass

class MyClass:
    def method_in_class(self):
        print("hello")
"""
    
    # 1. Parse the code
    adapter.parse(sample_code)
    
    # 2. Test Import Extraction
    imports = adapter.extract_imports()
    
    assert "os" in imports
    assert "sys" in imports
    assert "pathlib" in imports
    
    # 3. Test Function Extraction
    functions = adapter.extract_functions()
    func_names = [f["name"] for f in functions]
    
    assert "my_cool_function" in func_names
    assert "method_in_class" in func_names
    
    # Verify line numbers for my_cool_function (0-indexed in Tree-sitter)
    # my_cool_function starts on line 6 (index 6) and ends on line 7 (index 7)
    target_func = next(f for f in functions if f["name"] == "my_cool_function")
    assert target_func["start_line"] == 6
    assert target_func["end_line"] == 7