"""Tests for evidence linkage between choices and references."""

import re

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


def test_majority_of_primary_effects_have_citations():
    """Most primary mortality effects with evidence should have citations.

    This is a coverage check, not a strict requirement. Some effects may have
    evidence text without citations when data doesn't exist (e.g., "No mortality
    studies exist for ACV"). The goal is to ensure citation migration was
    successful for files that had URLs.
    """
    choices = load_all_choices()
    total_primary = 0
    with_citations = 0
    for choice in choices:
        for effect in choice.effects:
            if effect.evidence and effect.outcome.value == "Relative mortality risk":
                total_primary += 1
                if effect.ref_ids:
                    with_citations += 1

    # Expect at least 85% citation coverage for primary effects
    coverage = with_citations / total_primary if total_primary > 0 else 0
    assert coverage >= 0.85, (
        f"Citation coverage too low: {with_citations}/{total_primary} " f"({coverage:.0%}). Expected at least 85%."
    )


def test_no_raw_urls_in_evidence():
    """Evidence must use [@ref_id] citations, not raw URLs."""
    choices = load_all_choices()
    url_pattern = re.compile(r"https?://[^\s)]+")
    violations = []
    for choice in choices:
        for effect in choice.effects:
            if effect.evidence and url_pattern.search(effect.evidence):
                violations.append(choice.name)
                break
    assert not violations, "Files with raw URLs:\n" + "\n".join(violations)
