"""Tests for evidence validation module."""

from amarantos.core.validation import ValidationResult, validate_evidence_linkage


def test_validation_result_coverage():
    """Test ValidationResult coverage calculation."""
    # 0 effects = 0% coverage
    result = ValidationResult(
        total_effects=0,
        effects_with_refs=0,
        missing_refs=frozenset(),
        choices_without_refs=(),
    )
    assert result.coverage == 0.0

    # 5/10 effects = 50% coverage
    result = ValidationResult(
        total_effects=10,
        effects_with_refs=5,
        missing_refs=frozenset(),
        choices_without_refs=(),
    )
    assert result.coverage == 50.0

    # All effects = 100% coverage
    result = ValidationResult(
        total_effects=10,
        effects_with_refs=10,
        missing_refs=frozenset(),
        choices_without_refs=(),
    )
    assert result.coverage == 100.0


def test_validate_evidence_linkage():
    """Test validate_evidence_linkage returns valid result."""
    result = validate_evidence_linkage()

    assert isinstance(result, ValidationResult)
    assert result.total_effects >= 0
    assert result.effects_with_refs >= 0
    assert result.effects_with_refs <= result.total_effects
    assert 0.0 <= result.coverage <= 100.0
    assert isinstance(result.missing_refs, frozenset)
    assert isinstance(result.choices_without_refs, tuple)
