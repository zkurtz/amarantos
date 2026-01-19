"""Bibliography schemas for reference management."""

import re
from enum import StrEnum
from pathlib import Path
from typing import Self

import attrs
import dummio.yaml

from amarantos.core.schemas import BaseEffect, Z_95

# URL validation pattern (basic but catches obvious errors)
_URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:[\w-]+\.)+[\w-]+"  # domain
    r"(?:/[^\s]*)?"  # optional path
    r"$"
)

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


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL format."""
    return bool(_URL_PATTERN.match(url))


@attrs.frozen
class SoftClaim:
    """A qualitative claim from non-quantitative sources (news, expert opinion, etc.).

    Attributes:
        summary: What the source claims in plain English.
        choice: The choice/intervention this relates to.
        source_type: Type of source (expert opinion, news, review, etc.).
        notes: Additional context or caveats.
    """

    summary: str
    choice: str
    source_type: str = ""  # e.g., "expert opinion", "news article", "review"
    notes: str = ""


@attrs.frozen
class Claim:
    """A quantitative claim with effect sizes from research.

    Attributes:
        summary: Brief description of what the claim states.
        choice: The choice/intervention this claim relates to (e.g., "running").
        evidence_type: How the evidence was gathered.
        effects: List of effect estimates for different outcomes.
        population: Who was studied (e.g., "adults 40-70 years").
        sample_size: Number of participants.
        followup_years: Duration of follow-up for longitudinal studies.
        notes: Additional context or caveats.
    """

    summary: str
    choice: str
    evidence_type: EvidenceType = attrs.field(converter=_to_evidence_type)
    effects: tuple[BaseEffect, ...] = ()
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
        keywords: 10-30 words sorted by relevance to longevity/wellness.
        soft_claims: Qualitative claims from non-quantitative sources.
        hard_claims: Quantitative claims with effect sizes from research.
        journal: Journal name (for articles).
        doi: Digital Object Identifier.
        pmid: PubMed ID.
        url: Direct URL to the resource.
        summary: Brief plain-English summary (1-5 sentences).
    """

    id: str
    title: str
    authors: tuple[str, ...]
    year: int
    reference_type: ReferenceType = attrs.field(converter=_to_reference_type)
    url: str = attrs.field()
    keywords: tuple[str, ...] = ()
    soft_claims: tuple[SoftClaim, ...] = ()
    hard_claims: tuple[Claim, ...] = ()
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    pmid: str = ""
    summary: str = ""

    @url.validator  # type: ignore[attr-defined]
    def _validate_url(self, attribute: attrs.Attribute, value: str) -> None:
        """Validate that url is a properly formatted URL."""
        if not value:
            raise ValueError(f"Reference '{self.id}' must have a url")
        if not is_valid_url(value):
            raise ValueError(f"Reference '{self.id}' has invalid url: {value}")

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
    def load(cls, path: Path) -> Self:
        """Load a reference from a YAML file."""
        data = dummio.yaml.load(filepath=path)
        data["authors"] = tuple(data.get("authors", []))
        data["keywords"] = tuple(data.get("keywords", []))
        data["soft_claims"] = tuple(SoftClaim(**c) for c in data.get("soft_claims", []))
        
        # Handle hard_claims conversion
        hard_claims_data = data.get("hard_claims", [])
        hard_claims = []
        for claim_dict in hard_claims_data:
            # Check if this is the old format (with effect_size, effect_ci_lower, effect_ci_upper, outcome)
            if "effect_size" in claim_dict or "outcome" in claim_dict:
                # Convert old format to new format
                effects = []
                if claim_dict.get("effect_size") is not None and claim_dict.get("outcome"):
                    # Calculate std from CI bounds
                    effect_size = claim_dict["effect_size"]
                    ci_lower = claim_dict.get("effect_ci_lower")
                    ci_upper = claim_dict.get("effect_ci_upper")
                    
                    if ci_lower is not None and ci_upper is not None:
                        # std = (CI_upper - CI_lower) / (2 * Z_95)
                        std = (ci_upper - ci_lower) / (2 * Z_95)
                    else:
                        # If CI bounds are missing, use a default std (conservative estimate)
                        # Assume 50% relative uncertainty: std = effect_size * 0.25
                        std = abs(effect_size) * 0.25
                    
                    effect = BaseEffect(
                        outcome=claim_dict["outcome"],
                        mean=effect_size,
                        std=std
                    )
                    effects.append(effect)
                
                # Create new claim with effects
                new_claim = {
                    "summary": claim_dict.get("summary", ""),
                    "choice": claim_dict.get("choice", ""),
                    "evidence_type": claim_dict.get("evidence_type", ""),
                    "effects": tuple(effects),
                    "population": claim_dict.get("population", ""),
                    "sample_size": claim_dict.get("sample_size"),
                    "followup_years": claim_dict.get("followup_years"),
                    "notes": claim_dict.get("notes", ""),
                }
                hard_claims.append(Claim(**new_claim))
            else:
                # New format: already has effects
                if "effects" in claim_dict:
                    claim_dict["effects"] = tuple(BaseEffect(**e) for e in claim_dict["effects"])
                hard_claims.append(Claim(**claim_dict))
        
        data["hard_claims"] = tuple(hard_claims)
        
        # Handle legacy 'abstract' field
        if "abstract" in data:
            data["summary"] = data.pop("abstract")
        # Remove legacy 'claims' field if present
        data.pop("claims", None)
        return cls(**data)

    def save(self, path: Path | None = None) -> None:
        """Save this reference to a YAML file."""
        if path is None:
            path = self.path
        data = attrs.asdict(self)
        data["authors"] = list(self.authors)
        data["keywords"] = list(self.keywords)
        data["soft_claims"] = [attrs.asdict(c) for c in self.soft_claims]
        data["hard_claims"] = [attrs.asdict(c) for c in self.hard_claims]
        # Convert enums to strings
        data["reference_type"] = str(self.reference_type)
        for claim in data["hard_claims"]:
            claim["evidence_type"] = str(claim["evidence_type"])
            # Convert effects tuple to list of dicts
            claim["effects"] = [attrs.asdict(e) for e in claim["effects"]]
        dummio.yaml.save(data, filepath=path)
