"""Profile CRUD operations."""

import json
from pathlib import Path

from amarantos.core.schemas import UserProfile

# Profile storage directory
PROFILES_DIR = Path.cwd() / "profiles"


class ProfileManager:
    """Manage user profiles with CRUD operations."""

    def __init__(self, profiles_dir: Path | None = None):
        """Initialize the profile manager.

        Args:
            profiles_dir: Directory to store profiles. Defaults to ./profiles
        """
        self.profiles_dir = profiles_dir or PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _get_profile_path(self, profile_name: str) -> Path:
        """Get the path for a profile file.

        Args:
            profile_name: Name of the profile

        Returns:
            Path to the profile JSON file
        """
        return self.profiles_dir / f"{profile_name}.json"

    def create(self, profile_name: str, profile: UserProfile) -> None:
        """Create a new profile.

        Args:
            profile_name: Name for the profile
            profile: UserProfile object to save

        Raises:
            FileExistsError: If profile already exists
        """
        profile_path = self._get_profile_path(profile_name)
        if profile_path.exists():
            raise FileExistsError(f"Profile '{profile_name}' already exists")

        self._save_profile(profile_path, profile)

    def read(self, profile_name: str) -> UserProfile:
        """Read a profile.

        Args:
            profile_name: Name of the profile to read

        Returns:
            UserProfile object

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        profile_path = self._get_profile_path(profile_name)
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{profile_name}' not found")

        with open(profile_path) as f:
            data = json.load(f)

        return UserProfile(**data)

    def update(self, profile_name: str, profile: UserProfile) -> None:
        """Update an existing profile.

        Args:
            profile_name: Name of the profile to update
            profile: UserProfile object with updated data

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        profile_path = self._get_profile_path(profile_name)
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{profile_name}' not found")

        self._save_profile(profile_path, profile)

    def delete(self, profile_name: str) -> None:
        """Delete a profile.

        Args:
            profile_name: Name of the profile to delete

        Raises:
            FileNotFoundError: If profile doesn't exist
        """
        profile_path = self._get_profile_path(profile_name)
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{profile_name}' not found")

        profile_path.unlink()

    def list(self) -> list[str]:
        """List all available profiles.

        Returns:
            List of profile names
        """
        if not self.profiles_dir.exists():
            return []

        return sorted([p.stem for p in self.profiles_dir.glob("*.json")])

    def _save_profile(self, profile_path: Path, profile: UserProfile) -> None:
        """Save a profile to disk.

        Args:
            profile_path: Path to save the profile
            profile: UserProfile object to save
        """
        with open(profile_path, "w") as f:
            json.dump(profile.model_dump(), f, indent=2)
