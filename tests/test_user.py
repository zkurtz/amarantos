import attrs

from amarantos.core.schemas import User


def test_user_empty():
    user = User()
    assert user.age is None
    assert user.is_male is None


def test_user_partial():
    user = User(age=42, is_male=True, sleep_hours=7.5)
    assert user.age == 42
    assert user.is_male is True
    assert user.sleep_hours == 7.5
    assert user.body_fat_pct is None


def test_user_full():
    user = User(
        is_male=True,
        age=42,
        height_cm=178.0,
        body_fat_pct=18.0,
        blood_pressure_systolic=120,
        is_vegan=False,
        is_vegetarian=False,
        diet_quality_pctl=65.0,
        exercise_cardio_pctl=70.0,
        exercise_resistance_pctl=50.0,
        sleep_hours=7.5,
    )
    assert user.age == 42
    assert user.height_cm == 178.0
    assert user.exercise_cardio_pctl == 70.0


def test_user_serialization():
    user = User(age=42, is_male=True, body_fat_pct=20.0)
    data = attrs.asdict(user)
    assert data["age"] == 42
    assert data["is_male"] is True
    assert data["body_fat_pct"] == 20.0
