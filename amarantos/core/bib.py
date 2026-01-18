"""Bibliography schemas for reference management."""

from enum import StrEnum
from pathlib import Path

import attrs
import dummio.yaml

DATA_DIR = Path(__file__).parent.parent / "data"
REFS_DIR = DATA_DIR / "refs"


class EvidenceType(StrEnum):
    """Classification of evidence strength/type."""

    RCT = "Randomized controlled trial"
    META_ANALYSIS = "Meta-analysis"
    COHORT = "Prospective cohort study"
    CASE_CONTROL = "Case-control study"
    CROSS_SECTIONAL = "Cross-sectional study"
    NATURAL_EXPERIMENT = "Natural experiment"
    MENDELIAN_RANDOMIZATION = "Mendelian randomization"
    MECHANISTIC = "Mechanistic/first-principles"
    EXPERT_OPINION = "Expert opinion"


class ReferenceType(StrEnum):
    """Type of publication."""

    JOURNAL_ARTICLE = "Journal article"
    META_ANALYSIS = "Meta-analysis"
    REVIEW = "Review article"
    BOOK = "Book"
    BOOK_CHAPTER = "Book chapter"
    PREPRINT = "Preprint"
    REPORT = "Report"
    WEBSITE = "Website"


def _to_evidence_type(value: EvidenceType | str) -> EvidenceType:
    """Convert string to EvidenceType enum."""
    if isinstance(value, EvidenceType):
        return value
    return EvidenceType(value)


def _to_reference_type(value: ReferenceType | str) -> ReferenceType:
    """Convert string to ReferenceType enum."""
    if isinstance(value, ReferenceType):
        return value
    return ReferenceType(value)


@attrs.frozen
class Claim:
    """A specific claim extracted from a reference.

    Attributes:
        summary: Brief description of what the claim states.
        choice: The choice/intervention this claim relates to (e.g., "running").
        evidence_type: How the evidence was gathered.
        effect_size: Point estimate (e.g., hazard ratio, relative risk).
        effect_ci_lower: Lower bound of confidence interval.
        effect_ci_upper: Upper bound of confidence interval.
        outcome: What is being measured (e.g., "all-cause mortality").
        population: Who was studied (e.g., "adults 40-70 years").
        sample_size: Number of participants.
        followup_years: Duration of follow-up for longitudinal studies.
        notes: Additional context or caveats.
    """

    summary: str
    choice: str
    evidence_type: EvidenceType = attrs.field(converter=_to_evidence_type)
    effect_size: float | None = None
    effect_ci_lower: float | None = None
    effect_ci_upper: float | None = None
    outcome: str = ""
    population: str = ""
    sample_size: int | None = None
    followup_years: float | None = None
    notes: str = ""


@attrs.frozen
class Reference:
    """A bibliography entry with associated claims.

    Attributes:
        id: Unique identifier (e.g., "aune2016", "ekelund2019").
        title: Full title of the work.
        authors: Tuple of author names.
        year: Publication year.
        reference_type: Type of publication.
        journal: Journal name (for articles).
        doi: Digital Object Identifier.
        pmid: PubMed ID.
        url: Direct URL to the resource.
        claims: Tuple of claims extracted from this reference.
        abstract: Optional abstract text.
    """

    id: str
    title: str
    authors: tuple[str, ...]
    year: int
    reference_type: ReferenceType = attrs.field(converter=_to_reference_type)
    claims: tuple[Claim, ...] = ()
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    pmid: str = ""
    url: str = ""
    abstract: str = ""

    @property
    def pubmed_url(self) -> str | None:
        """Generate PubMed URL from PMID."""
        if self.pmid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        return None

    @property
    def doi_url(self) -> str | None:
        """Generate DOI URL."""
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return None

    @property
    def path(self) -> Path:
        """Default path for this reference."""
        return REFS_DIR / f"{self.id}.yaml"

    @classmethod
    def load(cls, path: Path) -> "Reference":
        """Load a reference from a YAML file."""
        data = dummio.yaml.load(filepath=path)
        data["authors"] = tuple(data.get("authors", []))
        data["claims"] = tuple(Claim(**c) for c in data.get("claims", []))
        return cls(**data)

    def save(self, path: Path | None = None) -> None:
        """Save this reference to a YAML file."""
        if path is None:
            path = self.path
        data = attrs.asdict(self)
        data["authors"] = list(self.authors)
        data["claims"] = [attrs.asdict(c) for c in self.claims]
        # Convert enums to strings
        data["reference_type"] = str(self.reference_type)
        for claim in data["claims"]:
            claim["evidence_type"] = str(claim["evidence_type"])
        dummio.yaml.save(data, filepath=path)
