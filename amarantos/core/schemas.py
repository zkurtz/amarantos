"""Schemas for choice data and user profiles."""

import re
from pathlib import Path

import attrs
import dummio.yaml
from pydantic import BaseModel, Field

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


# User Profile Models


class Demographics(BaseModel):
    """User demographic information."""

    age: int | None = None
    biological_sex: str | None = None


class Goals(BaseModel):
    """User health goals."""

    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)


class RiskLevel(BaseModel):
    """Risk factor level."""

    level: str | None = None


class RiskFactors(BaseModel):
    """User risk factors."""

    cardiovascular: RiskLevel | None = None
    metabolic: RiskLevel | None = None
    cognitive: RiskLevel | None = None


class Diet(BaseModel):
    """Dietary behaviors."""

    fatty_fish_servings_per_week: int | None = None


class Exercise(BaseModel):
    """Exercise behaviors."""

    cardio_minutes_per_week: int | None = None


class CurrentBehaviors(BaseModel):
    """User current behaviors."""

    diet: Diet | None = None
    exercise: Exercise | None = None
    sleep_hours_per_night: float | None = None


class Biomarkers(BaseModel):
    """User biomarkers."""

    vitamin_d_ng_ml: float | None = None
    triglycerides_mg_dl: float | None = None


class UserProfile(BaseModel):
    """User profile for personalized recommendations."""

    demographics: Demographics | None = None
    goals: Goals | None = None
    risk_factors: RiskFactors | None = None
    current_behaviors: CurrentBehaviors | None = None
    biomarkers: Biomarkers | None = None

    def completeness(self) -> float:
        """Calculate profile completeness as a percentage (0-100).

        Returns:
            Completeness percentage based on non-None fields.
        """
        # Count all possible leaf fields
        total_fields = 0
        filled_fields = 0

        # Demographics
        if self.demographics:
            total_fields += 2  # age, biological_sex
            if self.demographics.age is not None:
                filled_fields += 1
            if self.demographics.biological_sex is not None:
                filled_fields += 1
        else:
            total_fields += 2

        # Goals
        if self.goals:
            total_fields += 2  # primary, secondary
            if self.goals.primary:
                filled_fields += 1
            if self.goals.secondary:
                filled_fields += 1
        else:
            total_fields += 2

        # Risk factors
        if self.risk_factors:
            total_fields += 3  # cardiovascular, metabolic, cognitive
            if self.risk_factors.cardiovascular and self.risk_factors.cardiovascular.level:
                filled_fields += 1
            if self.risk_factors.metabolic and self.risk_factors.metabolic.level:
                filled_fields += 1
            if self.risk_factors.cognitive and self.risk_factors.cognitive.level:
                filled_fields += 1
        else:
            total_fields += 3

        # Current behaviors
        if self.current_behaviors:
            total_fields += 3  # diet (1 field), exercise (1 field), sleep
            if self.current_behaviors.diet and self.current_behaviors.diet.fatty_fish_servings_per_week is not None:
                filled_fields += 1
            if self.current_behaviors.exercise and self.current_behaviors.exercise.cardio_minutes_per_week is not None:
                filled_fields += 1
            if self.current_behaviors.sleep_hours_per_night is not None:
                filled_fields += 1
        else:
            total_fields += 3

        # Biomarkers
        if self.biomarkers:
            total_fields += 2  # vitamin_d, triglycerides
            if self.biomarkers.vitamin_d_ng_ml is not None:
                filled_fields += 1
            if self.biomarkers.triglycerides_mg_dl is not None:
                filled_fields += 1
        else:
            total_fields += 2

        return round((filled_fields / total_fields) * 100, 1) if total_fields > 0 else 0.0
