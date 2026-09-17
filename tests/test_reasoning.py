from pathlib import Path

import pytest

from darukaa.knowledge.ingest import parse_research_md
from darukaa.knowledge.store import EvidenceStore
from darukaa.measurements.profile import (
    Category,
    ClimateMetrics,
    EnvironmentalProfile,
    LandUseMetrics,
    LandUseType,
    SoilMetrics,
    Trend,
)
from darukaa.reasoning.assessor import assess_all, rank_domains, severity
from darukaa.reasoning.interactions import apply_interactions

RESEARCH_MD = Path(__file__).resolve().parent.parent / "docs" / "research.md"


@pytest.fixture(scope="module")
def store():
    return EvidenceStore(parse_research_md(RESEARCH_MD), persist=False)


PDF_EXAMPLE_PROFILE = EnvironmentalProfile(
    soil=SoilMetrics(organic_carbon_pct=0.3),
    climate=ClimateMetrics(rainfall_category=Category.LOW),
    land_use=LandUseMetrics(land_use_type=LandUseType.MONOCULTURE),
)


def test_pdf_example_ranks_soil_first_after_interaction(store):
    assessments = assess_all(PDF_EXAMPLE_PROFILE, store)
    adjusted, fired = apply_interactions(PDF_EXAMPLE_PROFILE, assessments)
    fired_ids = {r.id for r in fired}
    assert 1 in fired_ids  # aridity-compounds-soil rule
    ranking = rank_domains(adjusted)
    assert ranking[0] == "soil"


def test_interaction_amplifies_soil_deviation(store):
    assessments = assess_all(PDF_EXAMPLE_PROFILE, store)
    adjusted, fired = apply_interactions(PDF_EXAMPLE_PROFILE, assessments)
    assert adjusted["soil"].deviation > assessments["soil"].deviation


def test_two_distinct_interaction_rows_can_fire_together(store):
    profile = EnvironmentalProfile(
        soil=SoilMetrics(organic_carbon_pct=0.3, moisture_pct=8),
        climate=ClimateMetrics(rainfall_category=Category.LOW),
    )
    assessments = assess_all(profile, store)
    _, fired = apply_interactions(profile, assessments)
    fired_ids = {r.id for r in fired}
    assert {1, 9}.issubset(fired_ids)


def test_severity_is_zero_when_deviation_is_zero(store):
    from darukaa.reasoning.assessor import SubAssessment

    a = SubAssessment(domain="soil", deviation=0.0, confidence=0.9, evidence=(), notes="")
    assert severity(a) == 0.0


def test_no_interactions_fire_for_a_single_populated_domain(store):
    profile = EnvironmentalProfile(soil=SoilMetrics(organic_carbon_pct=2.0))
    assessments = assess_all(profile, store)
    _, fired = apply_interactions(profile, assessments)
    assert fired == []


def test_water_biodiversity_interaction_rule_fires(store):
    from darukaa.measurements.profile import BiodiversityMetrics, WaterMetrics

    profile = EnvironmentalProfile(
        water=WaterMetrics(availability_category=Category.LOW),
        biodiversity=BiodiversityMetrics(trend=Trend.DECLINING),
    )
    assessments = assess_all(profile, store)
    _, fired = apply_interactions(profile, assessments)
    assert 11 in {r.id for r in fired}


def test_region_context_influences_retrieval(store):
    from darukaa.measurements.profile import RegionContext

    profile = EnvironmentalProfile(
        climate=ClimateMetrics(rainfall_category=Category.LOW),
        region=RegionContext(free_text_region="Northwest China"),
    )
    assessment = assess_all(profile, store)["climate"]
    assert any("Northwest China" in c.source_name for c in assessment.evidence)
