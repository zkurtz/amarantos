"""Pydantic schemas for intervention data."""

from pathlib import Path

import dummio.yaml
from pydantic import BaseModel


class EffectEstimate(BaseModel):
    """A health effect estimate with confidence bounds."""

    outcome: str
    estimate: float
    ci_lower: float
    ci_upper: float

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

    @property
    def uncertainty_width(self) -> float:
        """Width of the confidence interval."""
        return self.ci_upper - self.ci_lower


class Intervention(BaseModel):
    """A wellness intervention with effect estimates."""

    id: str
    domain: str
    name: str
    effects: list[EffectEstimate]

    @classmethod
    def load(cls, path: Path) -> "Intervention":
        """Load an intervention from a YAML file."""
        data = dummio.yaml.load(filepath=path)
        return cls(**data)

    def save(self, path: Path) -> None:
        """Save this intervention to a YAML file."""
        dummio.yaml.save(self.model_dump(), filepath=path)
