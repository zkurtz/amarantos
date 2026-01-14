#!/usr/bin/env python3
"""User Profile Management CLI.

Simple commands to manage user profiles for personalized wellness recommendations.

Usage:
    python -m amarantos.profiles.cli create <name>
    python -m amarantos.profiles.cli list
    python -m amarantos.profiles.cli show <name>
"""

import json
import sys
from pathlib import Path

import dummio.yaml

from amarantos.core.schemas import UserProfile
from amarantos.profiles.manager import ProfileManager

# Path to default profile template
DEFAULT_PROFILE_PATH = Path(__file__).parent.parent.parent / "data" / "defaults" / "generic_human.yaml"


def create_profile(name: str) -> None:
    """Create a new user profile."""
    manager = ProfileManager()

    try:
        if DEFAULT_PROFILE_PATH.exists():
            template_data = dummio.yaml.load(filepath=DEFAULT_PROFILE_PATH)
            profile = UserProfile(**template_data)
        else:
            profile = UserProfile()

        manager.create(name, profile)
        print(f"Created profile: {name}")
        print(f"Profile saved to: {manager.get_profile_path(name)}")
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def list_profiles() -> None:
    """List all user profiles."""
    manager = ProfileManager()
    profiles = manager.list()

    if not profiles:
        print("No profiles found.")
        return

    print(f"\nFound {len(profiles)} profile(s):")
    for profile_name in profiles:
        print(f"  • {profile_name}")


def show_profile(name: str) -> None:
    """Display a user profile."""
    manager = ProfileManager()

    try:
        profile = manager.read(name)
        print(f"\nProfile: {name}")
        print("=" * 60)
        print(json.dumps(profile.model_dump(), indent=2))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: python -m amarantos.profiles.cli <command> [args]")
        print("\nCommands:")
        print("  create <name>  - Create a new profile")
        print("  list          - List all profiles")
        print("  show <name>   - Display a profile")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 3:
            print("Error: create requires a profile name", file=sys.stderr)
            sys.exit(1)
        create_profile(sys.argv[2])
    elif command == "list":
        list_profiles()
    elif command == "show":
        if len(sys.argv) < 3:
            print("Error: show requires a profile name", file=sys.stderr)
            sys.exit(1)
        show_profile(sys.argv[2])
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
