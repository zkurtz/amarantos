"""CLI to rank wellness choices by conservative lifespan impact estimate.

Usage:
    python -m amarantos.rank
    python -m amarantos.rank -n 5
"""

import click

from amarantos.core.loaders import load_all_choices
from amarantos.core.schemas import Choice, Effect, Outcome

# 30th percentile z-score for normal distribution
Z_30 = -0.524


def get_effect_by_outcome(choice: Choice, outcome: Outcome) -> Effect | None:
    """Extract a specific effect from a choice by outcome type."""
    for effect in choice.effects:
        if effect.outcome == outcome:
            return effect
    return None


def percentile_30(effect: Effect) -> float:
    """Calculate 30th percentile of effect estimate."""
    return effect.mean + Z_30 * effect.std


@click.command()
@click.option(
    "-n",
    "--num-top-bottom",
    type=int,
    default=None,
    help="Show only top N and bottom N choices (default: show all)",
)
def main(num_top_bottom: int | None) -> None:
    """Rank wellness choices by 30th percentile lifespan impact."""
    choices = load_all_choices()

    results: list[tuple[str, float, float, float]] = []
    for choice in choices:
        aging_effect = get_effect_by_outcome(choice, Outcome.DELAYED_AGING)
        if aging_effect:
            p30 = percentile_30(aging_effect)
            results.append(
                (
                    choice.name,
                    p30,
                    choice.specification.annual_cost_usd,
                    choice.specification.annual_cost_h,
                )
            )

    # Sort by 30th percentile descending
    results.sort(key=lambda x: x[1], reverse=True)

    # Header
    click.echo()
    click.echo(f"{'Choice':<40} {'P30 (years)':>12} {'$/year':>10} {'h/year':>10}")
    click.echo("-" * 74)

    if num_top_bottom is None:
        # Show all
        for name, p30, cost_usd, cost_h in results:
            click.echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>10.0f} {cost_h:>10.0f}")
    else:
        # Show top N
        click.echo(f"TOP {num_top_bottom}:")
        for name, p30, cost_usd, cost_h in results[:num_top_bottom]:
            click.echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>10.0f} {cost_h:>10.0f}")

        click.echo()
        click.echo(f"BOTTOM {num_top_bottom}:")
        for name, p30, cost_usd, cost_h in results[-num_top_bottom:]:
            click.echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>10.0f} {cost_h:>10.0f}")

    click.echo()


if __name__ == "__main__":
    main()
