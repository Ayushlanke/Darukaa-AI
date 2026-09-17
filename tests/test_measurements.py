import pytest
from pydantic import ValidationError

from darukaa.measurements.profile import (
    Category,
    ClimateMetrics,
    Contradiction,
    EnvironmentalProfile,
    LandUseMetrics,
    LandUseType,
    SoilMetrics,
)


def test_valid_full_profile():
    profile = EnvironmentalProfile(
        soil=SoilMetrics(organic_carbon_pct=0.3, ph=7.2, moisture_pct=10),
        climate=ClimateMetrics(rainfall_category=Category.LOW),
        land_use=LandUseMetrics(land_use_type=LandUseType.MONOCULTURE),
    )
    assert profile.soil.organic_carbon_pct == 0.3
    assert set(profile.populated_domains()) == {"soil", "climate", "land_use"}


def test_out_of_range_value_rejected():
    with pytest.raises(ValidationError):
        SoilMetrics(ph=15)


def test_rainfall_aridity_contradiction_flagged():
    with pytest.raises(Contradiction):
        EnvironmentalProfile(
            climate=ClimateMetrics(rainfall_category=Category.HIGH, aridity_index=0.8)
        )


def test_no_contradiction_when_consistent():
    profile = EnvironmentalProfile(
        climate=ClimateMetrics(rainfall_category=Category.HIGH, aridity_index=0.2)
    )
    assert profile.climate.aridity_index == 0.2


def test_empty_profile_has_no_populated_domains():
    assert EnvironmentalProfile().populated_domains() == []
