"""CLI to calculate ROI of wellness choices.

Usage:
    python -m amarantos.core.roi
    python -m amarantos.core.roi -h 75 -s 2000 -y 150000
"""

import click

from amarantos.core.loaders import load_all_choices
from amarantos.core.schemas import Choice, Effect, Outcome


def get_effect_by_outcome(choice: Choice, outcome: Outcome) -> Effect | None:
    """Extract a specific effect from a choice by outcome type."""
    for effect in choice.effects:
        if effect.outcome == outcome:
            return effect
    return None


@click.command()
@click.option(
    "-h",
    "--dollars-per-hour",
    type=float,
    default=50.0,
    show_default=True,
    help="Value of your time in dollars per hour",
)
@click.option(
    "-s",
    "--dollars-per-subjective-improvement",
    type=float,
    default=1000.0,
    show_default=True,
    help="Value per subjective wellbeing unit in dollars",
)
@click.option(
    "-y",
    "--dollars-per-year",
    type=float,
    default=100000.0,
    show_default=True,
    help="Value per life-year in dollars",
)
def main(
    dollars_per_hour: float,
    dollars_per_subjective_improvement: float,
    dollars_per_year: float,
) -> None:
    """Calculate annual net value (ROI) of each wellness choice."""
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
    main()
