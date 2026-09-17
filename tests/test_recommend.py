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
)
from darukaa.reasoning.assessor import assess_all, rank_domains
from darukaa.reasoning.interactions import apply_interactions
from darukaa.reasoning.recommend import (
    build_recommendation,
    contains_generic_phrase,
    faithfulness_check,
    select_top_domains,
)

RESEARCH_MD = Path(__file__).resolve().parent.parent / "docs" / "research.md"


@pytest.fixture(scope="module")
def store():
    return EvidenceStore(parse_research_md(RESEARCH_MD), persist=False)


PDF_EXAMPLE_PROFILE = EnvironmentalProfile(
    soil=SoilMetrics(organic_carbon_pct=0.3),
    climate=ClimateMetrics(rainfall_category=Category.LOW),
    land_use=LandUseMetrics(land_use_type=LandUseType.MONOCULTURE),
)


def _recommend_for(profile, store):
    assessments = assess_all(profile, store)
    adjusted, fired = apply_interactions(profile, assessments)
    ranking = rank_domains(adjusted)
    top_domains = select_top_domains(ranking, fired)
    return build_recommendation(top_domains, adjusted, profile)


def test_pdf_example_selects_wheat_vetch_not_generic_agroforestry(store):
    rec = _recommend_for(PDF_EXAMPLE_PROFILE, store)
    assert rec is not None
    assert "wheat" in rec.what.lower() or "vetch" in rec.what.lower()
    assert rec.confidence in ("low", "medium", "high")
    assert rec.time_horizon in ("short", "medium", "long")


def test_all_required_fields_populated(store):
    rec = _recommend_for(PDF_EXAMPLE_PROFILE, store)
    assert rec.what and rec.why and rec.supporting_variables and rec.impacted_metrics
    assert rec.evidence and rec.limitations


def test_no_match_fallback_returns_none(store):
    profile = EnvironmentalProfile(climate=ClimateMetrics(rainfall_category=Category.LOW))
    assessments = assess_all(profile, store)
    rec = build_recommendation(["climate"], assessments, profile)
    assert rec is None


def test_top_ranked_domain_with_no_kb_entry_is_not_masked_by_other_populated_domains(store):
    # Regression test: climate (deviation 1.0, no linking interaction, no KB entry) must
    # rank above and be selected over water (deviation 0.5, has KB entries) — passing the
    # full ranking to build_recommendation instead of just the top domain(s) previously
    # let water's KB entries match even though climate was the actual top concern.
    from darukaa.measurements.profile import Trend, WaterMetrics

    profile = EnvironmentalProfile(
        climate=ClimateMetrics(aridity_index=0.9),
        water=WaterMetrics(groundwater_trend=Trend.DECLINING),
    )
    assessments = assess_all(profile, store)
    adjusted, fired = apply_interactions(profile, assessments)
    ranking = rank_domains(adjusted)
    assert ranking[0] == "climate"
    top_domains = select_top_domains(ranking, fired)
    assert top_domains == {"climate"}
    rec = build_recommendation(top_domains, adjusted, profile)
    assert rec is None


def test_faithfulness_check_drops_unsupported_number(store):
    rec = _recommend_for(PDF_EXAMPLE_PROFILE, store)
    fabricated = f"{rec.why} This also raises yield by 999% within a week."
    safe_text, dropped = faithfulness_check(fabricated, rec)
    assert dropped is True
    assert "999" not in safe_text


def test_faithfulness_check_keeps_supported_text(store):
    rec = _recommend_for(PDF_EXAMPLE_PROFILE, store)
    safe_text, dropped = faithfulness_check(rec.why, rec)
    assert dropped is False
    assert safe_text


def test_generic_phrase_blocklist():
    assert contains_generic_phrase("Use sustainable practices", "it helps") is True
    assert contains_generic_phrase("Introduce wheat-vetch intercropping", "raises SOC") is False
