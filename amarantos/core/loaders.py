"""Load intervention data from YAML files."""

from pathlib import Path

from amarantos.core.schemas import Intervention

DATA_DIR = Path(__file__).parent.parent.parent / "data"
INTERVENTIONS_DIR = DATA_DIR / "interventions"


def load_all_interventions(domain: str | None = None) -> list[Intervention]:
    """Load all interventions, optionally filtered by domain."""
    interventions = []

    if domain:
        domain_dir = INTERVENTIONS_DIR / domain
        if domain_dir.exists():
            for path in sorted(domain_dir.glob("*.yaml")):
                interventions.append(Intervention.load(path))
    else:
        for domain_dir in sorted(INTERVENTIONS_DIR.iterdir()):
            if domain_dir.is_dir():
                for path in sorted(domain_dir.glob("*.yaml")):
                    interventions.append(Intervention.load(path))

    return interventions
