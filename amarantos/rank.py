"""CLI to rank wellness choices by conservative lifespan impact estimate."""

import textwrap

import click

from amarantos.core.loaders import find_choice_by_name, load_all_choices
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


@click.group()
def main() -> None:
    """Amarantos: Rank and explore wellness choices."""
    pass


@main.command()
@click.option(
    "-n",
    "--num-top-bottom",
    type=int,
    default=None,
    help="Show only top N and bottom N choices",
)
@click.option(
    "-d",
    "--domain",
    type=str,
    default=None,
    help="Filter by domain (e.g., 'diet', 'exercise')",
)
@click.option(
    "--maxd",
    type=int,
    default=None,
    help="Show only top N choices from each domain",
)
def rank(num_top_bottom: int | None, domain: str | None, maxd: int | None) -> None:
    """Rank wellness choices by 30th percentile lifespan impact."""
    choices = load_all_choices(domain)

    results: list[tuple[str, str, float, float, float]] = []
    for choice in choices:
        aging_effect = get_effect_by_outcome(choice, Outcome.DELAYED_AGING)
        if aging_effect:
            p30 = percentile_30(aging_effect)
            results.append(
                (
                    choice.name,
                    choice.domain,
                    p30,
                    choice.specification.annual_cost_usd,
                    choice.specification.annual_cost_h,
                )
            )

    # Sort by 30th percentile descending
    results.sort(key=lambda x: x[2], reverse=True)

    # Apply maxd filter if specified
    if maxd is not None:
        domain_counts: dict[str, int] = {}
        filtered: list[tuple[str, str, float, float, float]] = []
        for item in results:
            d = item[1]
            domain_counts[d] = domain_counts.get(d, 0) + 1
            if domain_counts[d] <= maxd:
                filtered.append(item)
        results = filtered

    # Header
    click.echo()
    click.echo(f"{'Choice':<40} {'P30 (years)':>12} {'$/year':>10} {'h/year':>10}")
    click.echo("-" * 74)

    if num_top_bottom is None:
        for name, _, p30, cost_usd, cost_h in results:
            click.echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>10.0f} {cost_h:>10.0f}")
    else:
        click.echo(f"TOP {num_top_bottom}:")
        for name, _, p30, cost_usd, cost_h in results[:num_top_bottom]:
            click.echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>10.0f} {cost_h:>10.0f}")

        click.echo()
        click.echo(f"BOTTOM {num_top_bottom}:")
        for name, _, p30, cost_usd, cost_h in results[-num_top_bottom:]:
            click.echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>10.0f} {cost_h:>10.0f}")

    click.echo()


@main.command()
@click.argument("name")
def describe(name: str) -> None:
    """Display detailed information about a choice."""
    choice = find_choice_by_name(name)
    spec = choice.specification

    click.echo()
    click.secho(f"  {choice.name}", fg="bright_white", bold=True)
    click.secho(f"  {choice.domain}", fg="cyan")
    click.echo()

    if choice.summary:
        wrapped = textwrap.fill(choice.summary, width=76, initial_indent="  ", subsequent_indent="  ")
        click.echo(wrapped)
        click.echo()

    # Specification
    click.secho("  Specification", fg="yellow", bold=True)
    click.echo(f"    Duration:     {spec.duration_h:.2f} h/session")
    click.echo(f"    Frequency:    {spec.weekly_freq:.1f}x/week")
    click.echo(f"    Annual cost:  ${spec.annual_cost_usd:,.0f} | {spec.annual_cost_h:.0f} hours")
    if spec.description:
        click.echo()
        wrapped = textwrap.fill(spec.description, width=72, initial_indent="    ", subsequent_indent="    ")
        click.echo(wrapped)
    click.echo()

    # Effects
    click.secho("  Effects", fg="yellow", bold=True)
    for effect in choice.effects:
        click.echo()
        click.secho(f"    {effect.outcome.value}", fg="bright_white")
        click.echo(f"      Mean: {effect.mean:.3f}  Std: {effect.std:.3f}")
        click.echo(f"      95% CI: [{effect.ci_lower:.3f}, {effect.ci_upper:.3f}]")

        if effect.outcome == Outcome.DELAYED_AGING:
            p30 = percentile_30(effect)
            click.echo(f"      P30: {p30:+.2f} years")

        if effect.evidence:
            click.echo()
            wrapped = textwrap.fill(
                effect.evidence.strip(),
                width=70,
                initial_indent="      ",
                subsequent_indent="      ",
            )
            click.echo(click.style("      Evidence:", fg="bright_black"))
            click.echo(click.style(wrapped, fg="bright_black"))

    click.echo()


if __name__ == "__main__":
    main()
