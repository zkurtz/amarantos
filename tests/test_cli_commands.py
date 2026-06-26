"""Test CLI commands."""

from click.testing import CliRunner

from amarantos.rank import main


def test_stats_command():
    """Test that the stats command runs and displays expected sections."""
    runner = CliRunner()
    result = runner.invoke(main, ["stats"])

    assert result.exit_code == 0, f"stats command failed: {result.output}"

    # Check for expected sections in output
    assert "Dataset Statistics" in result.output
    assert "Total choices:" in result.output
    assert "Total references:" in result.output
    assert "Choices by Domain" in result.output
    assert "Citation Coverage" in result.output
    assert "Effects with citations:" in result.output


def test_stats_shows_nonzero_counts():
    """Test that stats command shows actual data counts."""
    runner = CliRunner()
    result = runner.invoke(main, ["stats"])

    assert result.exit_code == 0

    # Verify we have actual data (not zero counts)
    # The output format is "    Total choices:    N"
    lines = result.output.split("\n")
    for line in lines:
        if "Total choices:" in line:
            count = int(line.split(":")[-1].strip())
            assert count > 0, "Expected at least one choice"
        if "Total references:" in line:
            count = int(line.split(":")[-1].strip())
            assert count > 0, "Expected at least one reference"
