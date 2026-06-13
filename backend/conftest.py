"""
conftest.py — project-wide pytest fixtures and path setup.
Adds the backend root to sys.path so tests can import `main`, `models`, etc.
"""
import sys
import os

os.environ["TESTING"] = "1"

# Ensure the backend root is importable from test files
sys.path.insert(0, os.path.dirname(__file__))
