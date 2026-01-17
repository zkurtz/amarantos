"""Core CLI for amarantos wellness interventions.

Usage:
    python -m amarantos.core.cli list
    python -m amarantos.core.cli list --domain exercise
    python -m amarantos.core.cli list --domain diet
"""

import click

from amarantos.core.loaders import load_all_choices
from amarantos.core.schemas import Choice, Effect, Outcome


@click.group()
def cli() -> None:
    """Amarantos wellness interventions CLI."""
    pass


@cli.command("list")
@click.option(
    "--domain",
    "-d",
    type=str,
    help="Filter by domain (e.g., 'diet', 'exercise')",
)
def list_choices(domain: str | None) -> None:
    """List all wellness interventions.

    Example:
        python -m amarantos.core.cli list
        python -m amarantos.core.cli list --domain exercise
    """
    choices = load_all_choices(domain)

    if domain:
        click.echo(f"\n{domain.capitalize()} interventions ({len(choices)} total):\n")
    else:
        click.echo(f"\nAll interventions ({len(choices)} total):\n")

    # Group by domain
    by_domain: dict[str, list[Choice]] = {}
    for choice in choices:
        if choice.domain not in by_domain:
            by_domain[choice.domain] = []
        by_domain[choice.domain].append(choice)

    # Print grouped by domain
    for domain_name in sorted(by_domain.keys()):
        domain_choices = by_domain[domain_name]
        click.echo(f"[{domain_name.upper()}] ({len(domain_choices)} interventions)")
        for choice in sorted(domain_choices, key=lambda x: x.name.lower()):
            effect = choice.effects[0]
            status = "✓" if effect.is_beneficial else ("?" if effect.is_uncertain else "✗")
            click.echo(
                f"  {status} {choice.name:<50} "
                f"Effect: {effect.mean:.3f} (CI: {effect.ci_lower:.2f}-{effect.ci_upper:.2f})"
            )
        click.echo()


def get_effect_by_outcome(choice: Choice, outcome: Outcome) -> Effect | None:
    """Extract a specific effect from a choice by outcome type."""
    for effect in choice.effects:
        if effect.outcome == outcome:
            return effect
    return None


@cli.command("roi")
@click.option(
    "-h",
    "--dollars-per-hour",
    type=float,
    required=True,
    help="Value of your time in dollars per hour",
)
@click.option(
    "-s",
    "--dollars-per-subjective-improvement",
    type=float,
    required=True,
    help="Value per subjective wellbeing unit in dollars",
)
@click.option(
    "-y",
    "--dollars-per-year",
    type=float,
    required=True,
    help="Value per life-year in dollars",
)
def roi(
    dollars_per_hour: float,
    dollars_per_subjective_improvement: float,
    dollars_per_year: float,
) -> None:
    """Calculate annual net value (ROI) of each wellness choice.

    Example:
        python -m amarantos.core.cli roi -h 50 -s 1000 -y 100000
    """
    choices = load_all_choices()

    results: list[tuple[str, float]] = []
    for choice in choices:
        # Cost
        cost = choice.specification.annual_cost_h * dollars_per_hour + choice.specification.annual_cost_usd

        # Benefit
        benefit = 0.0
        aging_effect = get_effect_by_outcome(choice, Outcome.DELAYED_AGING)
        if aging_effect:
            benefit += aging_effect.mean * dollars_per_year

        wellbeing_effect = get_effect_by_outcome(choice, Outcome.SUBJECTIVE_WELLBEING)
        if wellbeing_effect:
            benefit += wellbeing_effect.mean * dollars_per_subjective_improvement

        roi_value = benefit - cost
        results.append((choice.name, roi_value))

    # Sort by ROI descending
    results.sort(key=lambda x: x[1], reverse=True)

    # Display top 10
    click.echo("\nTOP 10 CHOICES (highest ROI):")
    for i, (name, value) in enumerate(results[:10], 1):
        sign = "+" if value >= 0 else ""
        click.echo(f"  {i:2}. {name:<40} {sign}${value:,.0f}/year")

    # Display bottom 10
    click.echo("\nBOTTOM 10 CHOICES (lowest ROI):")
    bottom_10 = results[-10:]
    bottom_10.reverse()
    for i, (name, value) in enumerate(bottom_10, 1):
        sign = "+" if value >= 0 else ""
        click.echo(f"  {i:2}. {name:<40} {sign}${value:,.0f}/year")

    click.echo()


if __name__ == "__main__":
    cli()
