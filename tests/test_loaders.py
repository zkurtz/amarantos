from amarantos.core.loaders import load_all_choices
from amarantos.core.schemas import Outcome


def test_load_all_choices():
    """Test loading all choice YAML files to ensure compatibility with the Choice dataclass."""
    choices = load_all_choices()

    # Verify that at least some choices are loaded
    assert len(choices) > 0, "No choices were loaded"

    # Verify each choice has required attributes
    for choice in choices:
        assert choice.domain, f"Choice {choice.name or 'unknown'} missing domain"
        assert choice.name, f"Choice in domain {choice.domain or 'unknown'} missing name"
        assert choice.effects, f"Choice {choice.name or 'unknown'} has no effects"
        assert len(choice.effects) > 0, f"Choice {choice.name or 'unknown'} has empty effects"

        # Verify each effect has required attributes
        for effect in choice.effects:
            assert effect.outcome, f"Effect in {choice.name} missing outcome"
            assert effect.mean is not None, f"Effect in {choice.name} missing mean"
            assert effect.std is not None, f"Effect in {choice.name} missing std"


def test_load_all_choices_by_domain():
    """Test loading choices filtered by domain."""
    # First load all choices to get a domain that exists
    all_choices = load_all_choices()
    assert len(all_choices) > 0, "No choices available for testing"

    # Pick the first available domain
    test_domain = all_choices[0].domain

    # Load choices from that specific domain
    domain_choices = load_all_choices(domain=test_domain)

    # Verify that some choices are loaded
    assert len(domain_choices) > 0, f"No choices were loaded for domain '{test_domain}'"

    # Verify all loaded choices are from the expected domain
    for choice in domain_choices:
        assert (
            choice.domain == test_domain
        ), f"Choice {choice.name} has domain {choice.domain}, expected '{test_domain}'"


def test_effect_outcome_is_enum():
    """Test that effect.outcome is an Outcome enum, not a string.

    This is a regression test for a bug where YAML loading returned strings
    instead of Outcome enums, causing `effect.outcome.value` to fail.
    """
    choices = load_all_choices()
    assert len(choices) > 0

    for choice in choices:
        for effect in choice.effects:
            # Verify outcome is an Outcome enum instance
            assert isinstance(effect.outcome, Outcome), (
                f"Effect outcome in {choice.name} is {type(effect.outcome).__name__}, " f"expected Outcome enum"
            )
            # Verify .value works (this was the original bug)
            assert isinstance(effect.outcome.value, str)
