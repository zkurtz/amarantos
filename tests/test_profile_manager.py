import json
import tempfile
from pathlib import Path

import pytest

from amarantos.core.schemas import Demographics, UserProfile
from amarantos.profiles.manager import ProfileManager


@pytest.fixture
def temp_profiles_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def manager(temp_profiles_dir):
    return ProfileManager(profiles_dir=temp_profiles_dir)


def test_create_profile(manager):
    profile = UserProfile(demographics=Demographics(age=42))
    manager.create("test_user", profile)

    assert "test_user" in manager.list()


def test_create_duplicate_profile(manager):
    profile = UserProfile()
    manager.create("test_user", profile)

    with pytest.raises(FileExistsError):
        manager.create("test_user", profile)


def test_read_profile(manager):
    profile = UserProfile(demographics=Demographics(age=42, biological_sex="male"))
    manager.create("test_user", profile)

    loaded_profile = manager.read("test_user")
    assert loaded_profile.demographics.age == 42
    assert loaded_profile.demographics.biological_sex == "male"


def test_read_nonexistent_profile(manager):
    with pytest.raises(FileNotFoundError):
        manager.read("nonexistent")


def test_update_profile(manager):
    profile = UserProfile(demographics=Demographics(age=42))
    manager.create("test_user", profile)

    updated_profile = UserProfile(demographics=Demographics(age=43))
    manager.update("test_user", updated_profile)

    loaded_profile = manager.read("test_user")
    assert loaded_profile.demographics.age == 43


def test_update_nonexistent_profile(manager):
    profile = UserProfile()
    with pytest.raises(FileNotFoundError):
        manager.update("nonexistent", profile)


def test_delete_profile(manager):
    profile = UserProfile()
    manager.create("test_user", profile)

    assert "test_user" in manager.list()

    manager.delete("test_user")

    assert "test_user" not in manager.list()


def test_delete_nonexistent_profile(manager):
    with pytest.raises(FileNotFoundError):
        manager.delete("nonexistent")


def test_list_profiles(manager):
    profile = UserProfile()
    manager.create("user1", profile)
    manager.create("user2", profile)
    manager.create("user3", profile)

    profiles = manager.list()
    assert len(profiles) == 3
    assert profiles == ["user1", "user2", "user3"]


def test_list_empty(manager):
    profiles = manager.list()
    assert profiles == []


def test_profile_persistence(temp_profiles_dir):
    # Create profile with first manager
    manager1 = ProfileManager(profiles_dir=temp_profiles_dir)
    profile = UserProfile(demographics=Demographics(age=42))
    manager1.create("test_user", profile)

    # Read with second manager (simulating app restart)
    manager2 = ProfileManager(profiles_dir=temp_profiles_dir)
    loaded_profile = manager2.read("test_user")

    assert loaded_profile.demographics.age == 42


def test_profile_json_format(manager, temp_profiles_dir):
    profile = UserProfile(demographics=Demographics(age=42, biological_sex="male"))
    manager.create("test_user", profile)

    # Verify JSON file format
    profile_path = temp_profiles_dir / "test_user.json"
    assert profile_path.exists()

    with open(profile_path) as f:
        data = json.load(f)

    assert data["demographics"]["age"] == 42
    assert data["demographics"]["biological_sex"] == "male"
