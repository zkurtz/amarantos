"""Validation utilities for evidence linkage."""

from collections import Counter

import attrs

from amarantos.core.bib import EvidenceType, Reference
from amarantos.core.loaders import load_all_choices, load_reference_index
from amarantos.core.schemas import Choice


@attrs.frozen
class ValidationResult:
    """Result of evidence linkage validation.

    Attributes:
        total_effects: Total number of effects across all choices.
        effects_with_refs: Number of effects that have at least one ref_id.
        missing_refs: Set of ref_ids that are referenced but not found in refs/.
        choices_without_refs: List of choice names where no effects have ref_ids.
    """

    total_effects: int
    effects_with_refs: int
    missing_refs: frozenset[str]
    choices_without_refs: tuple[str, ...]

    @property
    def coverage(self) -> float:
        """Percentage of effects with references (0-100)."""
        if self.total_effects == 0:
            return 0.0
        return 100.0 * self.effects_with_refs / self.total_effects


def validate_evidence_linkage() -> ValidationResult:
    """Validate that effects have ref_ids and those refs exist.

    Returns:
        ValidationResult with coverage statistics and any missing references.
    """
    choices = load_all_choices()
    ref_index = load_reference_index()

    total_effects = 0
    effects_with_refs = 0
    missing_refs: set[str] = set()
    choices_without_refs: list[str] = []

    for choice in choices:
        choice_has_refs = False
        for effect in choice.effects:
            total_effects += 1
            if effect.ref_ids:
                effects_with_refs += 1
                choice_has_refs = True
                for ref_id in effect.ref_ids:
                    if ref_id not in ref_index:
                        missing_refs.add(ref_id)

        if not choice_has_refs:
            choices_without_refs.append(choice.name)

    return ValidationResult(
        total_effects=total_effects,
        effects_with_refs=effects_with_refs,
        missing_refs=frozenset(missing_refs),
        choices_without_refs=tuple(sorted(choices_without_refs)),
    )


def get_evidence_type_distribution(choice: Choice, ref_index: dict[str, Reference]) -> Counter[EvidenceType]:
    """Count evidence types for a choice's linked references.

    Args:
        choice: The choice to analyze.
        ref_index: Index of references by ID.

    Returns:
        Counter mapping EvidenceType to count of claims.
    """
    counts: Counter[EvidenceType] = Counter()

    for effect in choice.effects:
        for ref_id in effect.ref_ids:
            ref = ref_index.get(ref_id)
            if ref:
                for claim in ref.hard_claims:
                    counts[claim.evidence_type] += 1

    return counts
