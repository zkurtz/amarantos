"""Load choice data from YAML files."""

from amarantos.core.schemas import CHOICES_DIR, Choice


def load_all_choices(domain: str | None = None) -> list[Choice]:
    """Load all choices, optionally filtered by domain."""
    if domain:
        paths = sorted((CHOICES_DIR / domain).glob("*.yaml"))
    else:
        paths = sorted(CHOICES_DIR.glob("**/*.yaml"))

    return [Choice.load(path) for path in paths]
