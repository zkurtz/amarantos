"""Schemas for choice data and user profiles."""

import re
from enum import StrEnum
from pathlib import Path

import attrs
import dummio.yaml

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CHOICES_DIR = DATA_DIR / "choices"

# 95% CI uses 1.96 standard deviations
Z_95 = 1.96


def _name_to_filename(name: str) -> str:
    """Convert a choice name to a valid filename."""
    clean = name.lower()
    clean = re.sub(r"\s*\([^)]*\)", "", clean)  # Remove parentheses content
    clean = re.sub(r"[^a-z0-9]+", "_", clean)  # Replace non-alphanumeric with _
    return clean.strip("_") + ".yaml"


class Outcome(StrEnum):
    """Health outcomes that can be measured -- at least in principle -- on a continuous scale."""

    RELATIVE_MORTALITY_RISK = "Relative mortality risk"
    DELAYED_AGING = "Years of delayed aging"
    SUBJECTIVE_WELLBEING = "Subjective wellbeing - number of just-noticeable differences"


@attrs.frozen
class Effect:
    """A Gaussian-distributed health effect estimate.

    Attributes:
        outcome: The health outcome being measured.
        evidence: A summary of the evidence supporting this effect. Open-ended, but ideally includes things such as
            the nature of the studies, sample sizes, and any relevant statistical measures, or first-principles
            reasoning.
        mean: The mean effect estimate.
        std: The standard deviation of the effect estimate.
    """

    outcome: Outcome
    mean: float
    std: float
    evidence: str = ""

    @property
    def ci_lower(self) -> float:
        """Lower bound of 95% confidence interval."""
        return self.mean - Z_95 * self.std

    @property
    def ci_upper(self) -> float:
        """Upper bound of 95% confidence interval."""
        return self.mean + Z_95 * self.std

    @property
    def is_beneficial(self) -> bool:
        """Effect is beneficial if upper bound < 1.0."""
        return self.ci_upper < 1.0

    @property
    def is_harmful(self) -> bool:
        """Effect is harmful if lower bound > 1.0."""
        return self.ci_lower > 1.0

    @property
    def is_uncertain(self) -> bool:
        """Effect is uncertain if CI crosses 1.0."""
        return self.ci_lower < 1.0 < self.ci_upper


@attrs.frozen
class Specification:
    """Detailed specification of a wellness choice.

    Attributes:
        duration_h: Average duration of one session of the activity in hours.
            For running, ~0.5. For taking a pill, ~0.001.
        weekly_freq: How many times per week on average. Running might be 4,
            taking a pill might be 7, fasting might be 1.
        annual_cost_h: Total annual time cost including preparation, cleanup,
            and actually doing the activity. Sleep optimization should count
            bedtime ritual plus extra sleep time.
        annual_cost_usd: Total annual dollar cost excluding time. For running,
            maybe $100 for shoes.
        description: Plain english description of the choice noting common
            variations in implementation and citing evidence where available.
    """

    duration_h: float
    weekly_freq: float
    annual_cost_h: float
    annual_cost_usd: float
    description: str = ""


@attrs.frozen
class Choice:
    """A wellness choice with effect estimates."""

    domain: str
    name: str
    effects: tuple[Effect, ...]
    specification: Specification
    summary: str = ""

    @property
    def path(self) -> Path:
        """Default path for this choice."""
        return CHOICES_DIR / self.domain / _name_to_filename(self.name)

    @classmethod
    def load(cls, path: Path) -> "Choice":
        """Load a choice from a YAML file."""
        data = dummio.yaml.load(filepath=path)
        data["effects"] = tuple(Effect(**e) for e in data["effects"])
        data["specification"] = Specification(**data["specification"])
        data.pop("literature", None)  # Remove legacy field if present
        data.pop("annual_cost", None)  # Remove legacy field if present
        return cls(**data)

    def save(self, path: Path | None = None) -> None:
        """Save this choice to a YAML file."""
        if path is None:
            path = self.path
        data = {
            "domain": self.domain,
            "name": self.name,
            "specification": attrs.asdict(self.specification),
            "effects": [attrs.asdict(e) for e in self.effects],
        }
        if self.summary:
            data["summary"] = self.summary
        dummio.yaml.save(data, filepath=path)


@attrs.frozen
class User:
    """User attributes for personalized recommendations."""

    is_male: bool | None = None
    age: int | None = None
    height_cm: float | None = None
    body_fat_pct: float | None = None
    blood_pressure_systolic: int | None = None
    is_vegan: bool | None = None
    is_vegetarian: bool | None = None
    diet_quality_pctl: float | None = None
    exercise_cardio_pctl: float | None = None
    exercise_resistance_pctl: float | None = None
    sleep_hours: float | None = None
