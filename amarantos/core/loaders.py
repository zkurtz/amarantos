"""Load choice data from YAML files."""

from click import ClickException, confirm, echo, prompt

from amarantos.core.schemas import CHOICES_DIR, Choice


def load_all_choices(domain: str | None = None) -> list[Choice]:
    """Load all choices, optionally filtered by domain."""
    if domain:
        paths = sorted((CHOICES_DIR / domain).glob("*.yaml"))
    else:
        paths = sorted(CHOICES_DIR.glob("**/*.yaml"))

    return [Choice.load(path) for path in paths]


def find_choice_by_name(name: str) -> Choice:
    """Find a choice by name.

    Exact matches (case-insensitive) are returned directly. For partial matches,
    prompts the user to confirm. Raises ClickException if no match found.
    """
    choices = load_all_choices()
    name_lower = name.lower()

    # Try exact match first (case-insensitive)
    for choice in choices:
        if choice.name.lower() == name_lower:
            return choice

    # Collect candidates: prefix matches first, then substring matches
    candidates: list[Choice] = []
    for choice in choices:
        if choice.name.lower().startswith(name_lower):
            candidates.append(choice)

    for choice in choices:
        if name_lower in choice.name.lower() and choice not in candidates:
            candidates.append(choice)

    if not candidates:
        raise ClickException(f"No choice found matching '{name}'")

    if len(candidates) == 1:
        if confirm(f"Did you mean '{candidates[0].name}'?"):
            return candidates[0]
        raise ClickException(f"No choice found matching '{name}'")

    # Multiple candidates - let user pick
    echo("Did you mean one of these?")
    for i, candidate in enumerate(candidates, 1):
        echo(f"  {i}. {candidate.name}")

    selection = prompt("Enter number", type=int, default=1)
    if 1 <= selection <= len(candidates):
        return candidates[selection - 1]

    raise ClickException("Invalid selection")
