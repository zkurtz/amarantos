"""Core CLI for amarantos wellness interventions.

Usage:
    python -m amarantos.core.cli list
    python -m amarantos.core.cli list --domain exercise
    python -m amarantos.core.cli list --domain diet
"""

import click

from amarantos.core.loaders import load_all_choices
from amarantos.core.schemas import Choice


@click.group()
def cli() -> None:
    """Amarantos wellness interventions CLI."""
    pass


@cli.command()
@click.option(
    "--domain",
    "-d",
    type=str,
    help="Filter by domain (e.g., 'diet', 'exercise')",
)
def list(domain: str | None) -> None:
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


if __name__ == "__main__":
    cli()
