from amarantos.core.schemas import (
    Biomarkers,
    CurrentBehaviors,
    Demographics,
    Diet,
    Exercise,
    Goals,
    RiskFactors,
    RiskLevel,
    UserProfile,
)


def test_user_profile_empty():
    profile = UserProfile()
    assert profile.demographics is None
    assert profile.goals is None
    assert profile.completeness() == 0.0


def test_user_profile_with_demographics():
    profile = UserProfile(demographics=Demographics(age=42, biological_sex="male"))
    assert profile.demographics.age == 42
    assert profile.demographics.biological_sex == "male"
    # Demographics has 2 out of 12 total fields
    assert profile.completeness() > 0.0


def test_user_profile_completeness_full():
    profile = UserProfile(
        demographics=Demographics(age=42, biological_sex="male"),
        goals=Goals(primary=["longevity"], secondary=["cognitive_function"]),
        risk_factors=RiskFactors(
            cardiovascular=RiskLevel(level="moderate"),
            metabolic=RiskLevel(level="low"),
            cognitive=RiskLevel(level="low"),
        ),
        current_behaviors=CurrentBehaviors(
            diet=Diet(fatty_fish_servings_per_week=2),
            exercise=Exercise(cardio_minutes_per_week=150),
            sleep_hours_per_night=8.0,
        ),
        biomarkers=Biomarkers(vitamin_d_ng_ml=35.0, triglycerides_mg_dl=120.0),
    )

    completeness = profile.completeness()
    assert completeness == 100.0


def test_user_profile_completeness_partial():
    profile = UserProfile(
        demographics=Demographics(age=42),
        goals=Goals(primary=["longevity"]),
    )

    completeness = profile.completeness()
    # 3 out of 12 fields filled (age + primary goals + secondary goals (empty but counted))
    assert 0.0 < completeness < 100.0


def test_user_profile_serialization():
    profile = UserProfile(
        demographics=Demographics(age=42, biological_sex="male"),
        goals=Goals(primary=["longevity"]),
    )

    data = profile.model_dump()
    assert data["demographics"]["age"] == 42
    assert data["demographics"]["biological_sex"] == "male"
    assert data["goals"]["primary"] == ["longevity"]

    # Test deserialization
    new_profile = UserProfile(**data)
    assert new_profile.demographics.age == 42
    assert new_profile.completeness() == profile.completeness()


def test_user_profile_nested_none():
    profile = UserProfile(
        demographics=Demographics(),
        goals=Goals(),
    )

    # Demographics and goals exist but have no values
    assert profile.demographics is not None
    assert profile.demographics.age is None
    assert profile.goals is not None
    assert len(profile.goals.primary) == 0


def test_biomarkers():
    biomarkers = Biomarkers(vitamin_d_ng_ml=28.0, triglycerides_mg_dl=150.0)
    assert biomarkers.vitamin_d_ng_ml == 28.0
    assert biomarkers.triglycerides_mg_dl == 150.0


def test_current_behaviors():
    behaviors = CurrentBehaviors(
        diet=Diet(fatty_fish_servings_per_week=1),
        exercise=Exercise(cardio_minutes_per_week=90),
        sleep_hours_per_night=7.5,
    )
    assert behaviors.diet.fatty_fish_servings_per_week == 1
    assert behaviors.exercise.cardio_minutes_per_week == 90
    assert behaviors.sleep_hours_per_night == 7.5
