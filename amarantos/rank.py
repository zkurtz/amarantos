"""CLI to rank wellness choices by conservative lifespan impact estimate."""

import textwrap

import click
from click import echo, secho, style

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


@click.group(invoke_without_command=True)
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
@click.pass_context
def main(
    ctx: click.Context,
    num_top_bottom: int | None,
    domain: str | None,
    maxd: int | None,
) -> None:
    """Amarantos: Rank and explore wellness choices."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(rank, num_top_bottom=num_top_bottom, domain=domain, maxd=maxd)


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
    echo()
    echo(f"{'Choice':<40} {'P30 (years)':>12} {'$/year':>12} {'hours/year':>12}")
    echo("-" * 78)

    if num_top_bottom is None:
        for name, _, p30, cost_usd, cost_h in results:
            echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>12.0f} {cost_h:>12.0f}")
    else:
        echo(f"TOP {num_top_bottom}:")
        for name, _, p30, cost_usd, cost_h in results[:num_top_bottom]:
            echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>12.0f} {cost_h:>12.0f}")

        echo()
        echo(f"BOTTOM {num_top_bottom}:")
        for name, _, p30, cost_usd, cost_h in results[-num_top_bottom:]:
            echo(f"{name:<40} {p30:>+12.2f} {cost_usd:>12.0f} {cost_h:>12.0f}")

    echo()
    echo("P30: conservative (30th percentile) estimate of the *average* years of life extension")
    echo("$/year, hours/year: annual cost of the intervention")


@main.command()
@click.argument("name")
def describe(name: str) -> None:
    """Display detailed information about a choice."""
    choice = find_choice_by_name(name)
    spec = choice.specification

    echo()
    secho(f"  {choice.name}", fg="bright_white", bold=True)
    secho(f"  {choice.domain}", fg="cyan")
    echo()

    if choice.summary:
        wrapped = textwrap.fill(choice.summary, width=76, initial_indent="  ", subsequent_indent="  ")
        echo(wrapped)
        echo()

    # Specification
    secho("  Specification", fg="yellow", bold=True)
    echo(f"    Duration:     {spec.duration_h:.2f} h/session")
    echo(f"    Frequency:    {spec.weekly_freq:.1f}x/week")
    echo(f"    Annual cost:  ${spec.annual_cost_usd:,.0f} | {spec.annual_cost_h:.0f} hours")
    if spec.description:
        echo()
        wrapped = textwrap.fill(spec.description, width=72, initial_indent="    ", subsequent_indent="    ")
        echo(wrapped)
    echo()

    # Effects
    secho("  Effects", fg="yellow", bold=True)
    for effect in choice.effects:
        echo()
        secho(f"    {effect.outcome.value}", fg="bright_white")
        echo(f"      Mean: {effect.mean:.3f}  Std: {effect.std:.3f}")
        echo(f"      95% CI: [{effect.ci_lower:.3f}, {effect.ci_upper:.3f}]")

        if effect.outcome == Outcome.DELAYED_AGING:
            p30 = percentile_30(effect)
            echo(f"      P30: {p30:+.2f} years")

        if effect.evidence:
            echo()
            wrapped = textwrap.fill(
                effect.evidence.strip(),
                width=70,
                initial_indent="      ",
                subsequent_indent="      ",
            )
            echo(style("      Evidence:", fg="bright_black"))
            echo(style(wrapped, fg="bright_black"))

    echo()


if __name__ == "__main__":
    main()
