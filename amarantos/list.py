"""CLI to list wellness interventions.

Usage:
    python -m amarantos.list
    python -m amarantos.list --domain exercise
"""

import click

from amarantos.core.loaders import load_all_choices
from amarantos.core.schemas import Choice


@click.command()
@click.option(
    "--domain",
    "-d",
    type=str,
    default=None,
    help="Filter by domain (e.g., 'diet', 'exercise')",
)
def main(domain: str | None) -> None:
    """List all wellness interventions."""
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


if __name__ == "__main__":
    main()
