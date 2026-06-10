import pytest
from pathlib import Path
from analysis.traversal import RepositoryWalker

def test_repository_walker_ignores_dirs(tmp_path):
    # Setup dummy directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.json").write_text("{}")
    
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("")

    walker = RepositoryWalker(str(tmp_path))
    files = walker.scan_summary()

    # Assertions
    assert "src/main.py" in files or "src\\main.py" in [f.replace('\\', '/') for f in files]
    assert not any("node_modules" in f for f in files)
    assert not any(".git" in f for f in files)