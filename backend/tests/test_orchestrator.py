import pytest
from pathlib import Path
from analysis.orchestrator import AnalyzerOrchestrator

def test_orchestrator_full_analysis(tmp_path):
    # Setup dummy repo with one Python file and one JS file
    py_file = tmp_path / "main.py"
    py_file.write_text("import os\n\ndef hello():\n    pass\n")
    
    js_file = tmp_path / "app.js"
    js_file.write_text("const fs = require('fs');\n\nfunction test() {}\n")
    
    # Initialize and run
    orchestrator = AnalyzerOrchestrator(str(tmp_path))
    results = orchestrator.analyze_repo()
    
    # Assert Python file was processed
    assert "main.py" in results
    assert results["main.py"]["extension"] == ".py"
    assert "os" in results["main.py"]["imports"]
    assert results["main.py"]["functions"][0]["name"] == "hello"
    
    # Assert JS file was processed
    assert "app.js" in results
    assert results["app.js"]["extension"] == ".js"
    assert "fs" in results["app.js"]["imports"]
    assert results["app.js"]["functions"][0]["name"] == "test"
    
    # Assert metrics were collected
    assert results["main.py"]["loc"] > 0
    assert results["app.js"]["loc"] > 0