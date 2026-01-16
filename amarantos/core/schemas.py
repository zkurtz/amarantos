"""Schemas for choice data and user profiles."""

import re
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


@attrs.frozen
class Effect:
    """A Gaussian-distributed health effect estimate."""

    outcome: str
    mean: float
    std: float

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
class Choice:
    """A wellness choice with effect estimates."""

    domain: str
    name: str
    effects: tuple[Effect, ...]
    annual_cost: float | None = None
    literature: list[str] | None = None

    @property
    def path(self) -> Path:
        """Default path for this choice."""
        return CHOICES_DIR / self.domain / _name_to_filename(self.name)

    @classmethod
    def load(cls, path: Path) -> "Choice":
        """Load a choice from a YAML file."""
        data = dummio.yaml.load(filepath=path)
        data["effects"] = tuple(Effect(**e) for e in data["effects"])
        return cls(**data)

    def save(self, path: Path | None = None) -> None:
        """Save this choice to a YAML file."""
        if path is None:
            path = self.path
        data = {
            "domain": self.domain,
            "name": self.name,
            "effects": [attrs.asdict(e) for e in self.effects],
        }
        if self.annual_cost is not None:
            data["annual_cost"] = self.annual_cost
        if self.literature is not None:
            data["literature"] = self.literature
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
