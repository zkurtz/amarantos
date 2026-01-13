#!/usr/bin/env python3
"""User Profile Management CLI.

This module provides commands to manage user profiles for personalized
wellness recommendations.

Usage:
    python -m amarantos.profiles.cli create <name>
    python -m amarantos.profiles.cli list
    python -m amarantos.profiles.cli show <name>
    python -m amarantos.profiles.cli delete <name>
"""

import json
from pathlib import Path

import click
import dummio.yaml

from amarantos.core.schemas import UserProfile
from amarantos.profiles.manager import ProfileManager

# Path to default profile template
DEFAULT_PROFILE_PATH = Path(__file__).parent.parent.parent / "data" / "defaults" / "generic_human.yaml"


@click.group()
def cli() -> None:
    """User Profile Management Tool."""
    pass


@cli.command()
@click.argument("name")
@click.option("--from-template", is_flag=True, help="Create from default template")
def create(name: str, from_template: bool) -> None:
    """Create a new user profile.

    NAME: Name for the new profile
    """
    manager = ProfileManager()

    try:
        if from_template and DEFAULT_PROFILE_PATH.exists():
            # Load from template
            template_data = dummio.yaml.load(filepath=DEFAULT_PROFILE_PATH)
            profile = UserProfile(**template_data)
        else:
            # Create empty profile
            profile = UserProfile()

        manager.create(name, profile)
        click.echo(f"Created profile: {name}")
        click.echo(f"Completeness: {profile.completeness()}%")
        click.echo(f"\nProfile saved to: {manager._get_profile_path(name)}")
        click.echo("\nTip: Edit the JSON file directly or use 'update' command to add information.")
    except FileExistsError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def list() -> None:
    """List all user profiles."""
    manager = ProfileManager()
    profiles = manager.list()

    if not profiles:
        click.echo("No profiles found.")
        click.echo("\nTip: Create a profile with 'create <name>'")
        return

    click.echo(f"\nFound {len(profiles)} profile(s):\n")
    for profile_name in profiles:
        try:
            profile = manager.read(profile_name)
            completeness = profile.completeness()
            click.echo(f"  • {profile_name:<20} Completeness: {completeness:>5.1f}%")
        except Exception:
            click.echo(f"  • {profile_name:<20} (error reading)")


@cli.command()
@click.argument("name")
def show(name: str) -> None:
    """Display a user profile.

    NAME: Name of the profile to display
    """
    manager = ProfileManager()

    try:
        profile = manager.read(name)
        click.echo(f"\nProfile: {name}")
        click.echo("=" * 60)
        click.echo(f"Completeness: {profile.completeness()}%")
        click.echo("\nProfile Data:")
        click.echo(json.dumps(profile.model_dump(), indent=2))
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def delete(name: str) -> None:
    """Delete a user profile.

    NAME: Name of the profile to delete
    """
    manager = ProfileManager()

    try:
        manager.delete(name)
        click.echo(f"Deleted profile: {name}")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("name")
@click.argument("profile_file", type=click.Path(exists=True))
def update(name: str, profile_file: str) -> None:
    """Update a profile from a JSON file.

    NAME: Name of the profile to update
    PROFILE_FILE: Path to JSON file with profile data
    """
    manager = ProfileManager()

    try:
        with open(profile_file) as f:
            data = json.load(f)

        profile = UserProfile(**data)
        manager.update(name, profile)

        click.echo(f"Updated profile: {name}")
        click.echo(f"Completeness: {profile.completeness()}%")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {profile_file}: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("name")
def completeness(name: str) -> None:
    """Show profile completeness indicator.

    NAME: Name of the profile
    """
    manager = ProfileManager()

    try:
        profile = manager.read(name)
        completeness_pct = profile.completeness()

        click.echo(f"\nProfile: {name}")
        click.echo("=" * 60)
        click.echo(f"Completeness: {completeness_pct}%")

        # Visual progress bar
        bar_width = 40
        filled = int(bar_width * completeness_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        click.echo(f"[{bar}] {completeness_pct}%")

        # Breakdown by section
        click.echo("\nBreakdown:")
        sections = {
            "Demographics": profile.demographics is not None,
            "Goals": profile.goals is not None,
            "Risk Factors": profile.risk_factors is not None,
            "Current Behaviors": profile.current_behaviors is not None,
            "Biomarkers": profile.biomarkers is not None,
        }

        for section, has_data in sections.items():
            status = "✓" if has_data else "✗"
            click.echo(f"  {status} {section}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
