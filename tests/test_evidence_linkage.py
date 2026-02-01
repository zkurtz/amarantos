"""Tests for evidence linkage between choices and references."""

from amarantos.core.loaders import load_all_choices, load_reference_index


def test_all_citations_resolve_to_existing_refs():
    """All [@ref_id] citations in evidence text must resolve to existing references."""
    choices = load_all_choices()
    ref_index = load_reference_index()

    all_effects = [(choice, effect) for choice in choices for effect in choice.effects]
    all_ref_ids = [ref_id for _, effect in all_effects for ref_id in effect.ref_ids]

    effects_with_refs = sum(1 for _, effect in all_effects if effect.ref_ids)
    missing_refs = [ref_id for ref_id in all_ref_ids if ref_id not in ref_index]

    # At least one effect has ref_ids (walking.yaml)
    assert effects_with_refs >= 1, "Expected at least one effect with ref_ids"

    # All referenced ref_ids must exist
    assert not missing_refs, f"Missing references: {missing_refs}"
