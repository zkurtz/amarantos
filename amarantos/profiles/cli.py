#!/usr/bin/env python3
"""User Profile Management CLI."""

import json
from pathlib import Path

import click
import dummio.yaml

from amarantos.core.schemas import UserProfile
from amarantos.profiles.manager import ProfileManager

DEFAULT_PROFILE_PATH = Path(__file__).parent.parent.parent / "data" / "defaults" / "generic_human.yaml"


@click.group()
def cli() -> None:
    """Manage user profiles for personalized wellness recommendations."""
    pass


@cli.command()
@click.argument("name")
def create(name: str) -> None:
    """Create a new user profile."""
    manager = ProfileManager()

    if DEFAULT_PROFILE_PATH.exists():
        template_data = dummio.yaml.load(filepath=DEFAULT_PROFILE_PATH)
        profile = UserProfile(**template_data)
    else:
        profile = UserProfile()

    try:
        manager.create(name, profile)
        click.echo(f"Created profile: {name}")
        click.echo(f"Profile saved to: {manager.get_profile_path(name)}")
    except FileExistsError as e:
        raise click.ClickException(str(e))


@cli.command("list")
def list_profiles() -> None:
    """List all user profiles."""
    manager = ProfileManager()
    profiles = manager.list()

    if not profiles:
        click.echo("No profiles found.")
        return

    click.echo(f"\nFound {len(profiles)} profile(s):")
    for profile_name in profiles:
        click.echo(f"  - {profile_name}")


@cli.command()
@click.argument("name")
def show(name: str) -> None:
    """Display a user profile."""
    manager = ProfileManager()

    try:
        profile = manager.read(name)
        click.echo(f"\nProfile: {name}")
        click.echo("=" * 60)
        click.echo(json.dumps(profile.model_dump(), indent=2))
    except FileNotFoundError as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    cli()
