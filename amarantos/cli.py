"""Main CLI entry point for amarantos."""

import click

from amarantos.list import main as list_cmd
from amarantos.rank import main as rank_cmd


@click.group()
def cli() -> None:
    """Amarantos: Tips and tools for personal wellness and longevity."""


cli.add_command(list_cmd, name="list")
cli.add_command(rank_cmd, name="rank")

if __name__ == "__main__":
    cli()
