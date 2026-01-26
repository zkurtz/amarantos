"""Test that CLI aliases are properly configured."""

import tomllib
from pathlib import Path


def test_cli_aliases_configured():
    """Verify that both 'amarantos' and 'amos' aliases are defined in pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    
    scripts = data.get("project", {}).get("scripts", {})
    
    # Check that both aliases exist
    assert "amarantos" in scripts, "Primary 'amarantos' CLI command not found"
    assert "amos" in scripts, "Short alias 'amos' not found"
    
    # Check that both point to the same entry point
    assert scripts["amarantos"] == "amarantos.rank:main", "amarantos entry point incorrect"
    assert scripts["amos"] == "amarantos.rank:main", "amos entry point incorrect"
    
    # Verify they both point to the same function
    assert scripts["amarantos"] == scripts["amos"], "Aliases should point to the same entry point"
