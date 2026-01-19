"""Tests for the bibliography module."""

import tempfile
from pathlib import Path

import pytest

from amarantos.core.bib import (
    REFS_DIR,
    EvidenceType,
    HardClaim,
    Reference,
    ReferenceType,
    SoftClaim,
    is_valid_url,
)


class TestUrlValidation:
    """Test URL validation functionality."""

    def test_valid_urls(self) -> None:
        """Test that valid URLs pass validation."""
        valid_urls = [
            "https://pubmed.ncbi.nlm.nih.gov/12345678/",
            "https://doi.org/10.1234/example",
            "http://example.com",
            "https://www.nature.com/articles/s41586-023-06088-9",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC123456/",
        ]
        for url in valid_urls:
            assert is_valid_url(url), f"Expected valid: {url}"

    def test_invalid_urls(self) -> None:
        """Test that invalid URLs fail validation."""
        invalid_urls = [
            "",
            "not a url",
            "ftp://example.com",
            "example.com",
            "https://",
            "http:/example.com",
        ]
        for url in invalid_urls:
            assert not is_valid_url(url), f"Expected invalid: {url}"

    def test_reference_requires_url(self) -> None:
        """Test that Reference raises ValueError without url."""
        with pytest.raises(ValueError, match="must have a url"):
            Reference(
                id="test",
                title="Test Reference",
                authors=("Author A",),
                year=2024,
                reference_type=ReferenceType.JOURNAL_ARTICLE,
                url="",
            )

    def test_reference_rejects_invalid_url(self) -> None:
        """Test that Reference raises ValueError for invalid url."""
        with pytest.raises(ValueError, match="invalid url"):
            Reference(
                id="test",
                title="Test Reference",
                authors=("Author A",),
                year=2024,
                reference_type=ReferenceType.JOURNAL_ARTICLE,
                url="not-a-valid-url",
            )

    def test_reference_accepts_valid_url(self) -> None:
        """Test that Reference accepts valid url."""
        ref = Reference(
            id="test",
            title="Test Reference",
            authors=("Author A",),
            year=2024,
            reference_type=ReferenceType.JOURNAL_ARTICLE,
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        )
        assert ref.url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"


class TestReferenceLoadSave:
    """Test Reference load/save functionality."""

    def test_save_and_load_roundtrip(self) -> None:
        """Test that a reference can be saved and loaded."""
        hard_claim = HardClaim(
            summary="Test hard claim",
            choice="test_choice",
            evidence_type=EvidenceType.META_ANALYSIS,
            effect_size=0.8,
            effect_ci_lower=0.7,
            effect_ci_upper=0.9,
            outcome="all-cause mortality",
            population="adults",
            sample_size=10000,
        )
        soft_claim = SoftClaim(
            summary="Test soft claim",
            choice="test_choice",
            source_type="expert opinion",
            notes="Test notes",
        )
        ref = Reference(
            id="test_ref",
            title="Test Reference Title",
            authors=("Author A", "Author B"),
            year=2024,
            reference_type=ReferenceType.META_ANALYSIS,
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            keywords=("longevity", "mortality", "meta-analysis"),
            soft_claims=(soft_claim,),
            hard_claims=(hard_claim,),
            journal="Test Journal",
            volume="1",
            issue="2",
            pages="100-110",
            doi="10.1234/test",
            pmid="12345678",
            summary="A test reference summary.",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_ref.yaml"
            ref.save(path)

            loaded = Reference.load(path)

            assert loaded.id == ref.id
            assert loaded.title == ref.title
            assert loaded.authors == ref.authors
            assert loaded.year == ref.year
            assert loaded.reference_type == ref.reference_type
            assert loaded.url == ref.url
            assert loaded.keywords == ref.keywords
            assert loaded.summary == ref.summary
            assert len(loaded.hard_claims) == 1
            assert loaded.hard_claims[0].summary == hard_claim.summary
            assert loaded.hard_claims[0].effect_size == hard_claim.effect_size
            assert len(loaded.soft_claims) == 1
            assert loaded.soft_claims[0].summary == soft_claim.summary
            assert loaded.soft_claims[0].source_type == soft_claim.source_type


class TestAllRefsValid:
    """Test that all reference files in the repository are valid."""

    def test_all_refs_load_successfully(self) -> None:
        """Test that all reference YAML files load without error."""
        refs = list(REFS_DIR.glob("*.yaml"))
        assert len(refs) > 0, "No reference files found"

        for path in refs:
            ref = Reference.load(path)
            assert ref.id == path.stem, f"ID mismatch for {path}"
            assert ref.url, f"Missing url for {path}"
            assert is_valid_url(ref.url), f"Invalid url for {path}: {ref.url}"
            assert ref.title, f"Missing title for {path}"
            assert ref.authors, f"Missing authors for {path}"
            assert ref.year > 1900, f"Invalid year for {path}"

    def test_all_refs_have_keywords(self) -> None:
        """Test that all references have keywords."""
        for path in REFS_DIR.glob("*.yaml"):
            ref = Reference.load(path)
            assert len(ref.keywords) >= 5, f"{ref.id} should have at least 5 keywords"
