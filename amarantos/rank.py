"""CLI to rank wellness choices by conservative lifespan impact estimate."""

import textwrap

import click
from click import echo, secho, style

from amarantos.core.bib import EvidenceType, Reference
from amarantos.core.loaders import find_choice_by_name, load_all_choices, load_reference_index
from amarantos.core.schemas import Choice, Effect, Outcome
from amarantos.core.validation import get_evidence_type_distribution

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
@click.option(
    "--show-evidence",
    is_flag=True,
    default=False,
    help="Show evidence type summary for each choice",
)
@click.pass_context
def main(
    ctx: click.Context,
    num_top_bottom: int | None,
    domain: str | None,
    maxd: int | None,
    show_evidence: bool,
) -> None:
    """Amarantos: Rank and explore wellness choices."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(rank, num_top_bottom=num_top_bottom, domain=domain, maxd=maxd, show_evidence=show_evidence)


def _format_evidence_summary(choice: Choice, ref_index: dict[str, Reference]) -> str:
    """Format evidence type summary for a choice (e.g., '2 Meta, 1 RCT')."""
    dist = get_evidence_type_distribution(choice, ref_index)
    if not dist:
        return "-"
    # Short names for evidence types
    short_names = {
        EvidenceType.META_ANALYSIS: "Meta",
        EvidenceType.RCT: "RCT",
        EvidenceType.COHORT: "Cohort",
        EvidenceType.CASE_CONTROL: "Case",
        EvidenceType.CROSS_SECTIONAL: "Cross",
        EvidenceType.NATURAL_EXPERIMENT: "NatExp",
        EvidenceType.MENDELIAN_RANDOMIZATION: "MR",
        EvidenceType.MECHANISTIC: "Mech",
        EvidenceType.EXPERT_OPINION: "Expert",
    }
    parts = [f"{count} {short_names.get(et, str(et)[:6])}" for et, count in dist.most_common()]
    return ", ".join(parts)


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
@click.option(
    "--show-evidence",
    is_flag=True,
    default=False,
    help="Show evidence type summary for each choice",
)
def rank(num_top_bottom: int | None, domain: str | None, maxd: int | None, show_evidence: bool) -> None:
    """Rank wellness choices by 30th percentile lifespan impact."""
    choices = load_all_choices(domain)
    ref_index: dict[str, Reference] = {}
    if show_evidence:
        ref_index = load_reference_index()

    # Build choice lookup for evidence display
    choice_lookup: dict[str, Choice] = {c.name: c for c in choices}

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
    if show_evidence:
        echo(f"{'Choice':<30} {'P30 (years)':>12} {'$/year':>10} {'h/year':>8}  {'Evidence':<20}")
        echo("-" * 84)
    else:
        echo(f"{'Choice':<40} {'P30 (years)':>12} {'$/year':>12} {'hours/year':>12}")
        echo("-" * 78)

    def format_row(name: str, p30: float, cost_usd: float, cost_h: float) -> str:
        if show_evidence:
            evidence = _format_evidence_summary(choice_lookup[name], ref_index)
            return f"{name:<30} {p30:>+12.2f} {cost_usd:>10.0f} {cost_h:>8.0f}  {evidence:<20}"
        return f"{name:<40} {p30:>+12.2f} {cost_usd:>12.0f} {cost_h:>12.0f}"

    if num_top_bottom is None:
        for name, _, p30, cost_usd, cost_h in results:
            echo(format_row(name, p30, cost_usd, cost_h))
    else:
        echo(f"TOP {num_top_bottom}:")
        for name, _, p30, cost_usd, cost_h in results[:num_top_bottom]:
            echo(format_row(name, p30, cost_usd, cost_h))

        echo()
        echo(f"BOTTOM {num_top_bottom}:")
        for name, _, p30, cost_usd, cost_h in results[-num_top_bottom:]:
            echo(format_row(name, p30, cost_usd, cost_h))

    echo()
    echo("P30: conservative (30th percentile) estimate of the *average* years of life extension")
    echo("$/year, hours/year: annual cost of the intervention")


@main.command()
@click.argument("name")
@click.option(
    "--show-sources",
    is_flag=True,
    default=False,
    help="Show linked reference sources for each effect",
)
def describe(name: str, show_sources: bool) -> None:
    """Display detailed information about a choice."""
    choice = find_choice_by_name(name)
    spec = choice.specification

    # Load references if needed
    ref_index: dict[str, Reference] = {}
    if show_sources:
        ref_index = load_reference_index()

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

        # Show linked sources if requested
        if show_sources and effect.ref_ids:
            echo()
            echo(style("      Sources:", fg="cyan"))
            for ref_id in effect.ref_ids:
                ref = ref_index.get(ref_id)
                if ref:
                    # Format: [id] Authors (year). Title...
                    authors_short = ref.authors[0] if ref.authors else "Unknown"
                    title_short = ref.title[:60] + "..." if len(ref.title) > 60 else ref.title
                    echo(style(f"        [{ref_id}] {authors_short} ({ref.year}). {title_short}", fg="cyan"))
                    if ref.url:
                        echo(style(f"          URL: {ref.url}", fg="bright_black"))
                else:
                    echo(style(f"        [{ref_id}] (reference not found)", fg="red"))

    echo()


if __name__ == "__main__":
    main()
