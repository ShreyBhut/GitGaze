import pytest
from analysis.adapters.javascript_adapter import JavascriptAdapter

def test_javascript_adapter_extraction():
    adapter = JavascriptAdapter()
    
    # Sample JS/TS code
    sample_code = b"""
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
const fs = require('fs');

function myStandardFunction() {
    return true;
}

const myArrowFunction = () => {
    console.log("hello");
};
"""
    
    adapter.parse(sample_code)
    
    # Test Imports
    imports = adapter.extract_imports()
    assert "react" in imports
    assert "@/components/ui/button" in imports
    assert "fs" in imports
    
    # Test Functions
    functions = adapter.extract_functions()
    func_names = [f["name"] for f in functions]
    
    assert "myStandardFunction" in func_names
    assert "myArrowFunction" in func_names
    
    # Check lines for the arrow function (starts line 9, ends line 11)
    # Note: 0-indexed in Tree-sitter!
    target_func = next(f for f in functions if f["name"] == "myArrowFunction")
    assert target_func["start_line"] == 9
    assert target_func["end_line"] == 11