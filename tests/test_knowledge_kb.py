import sqlite3

from darukaa.knowledge.kb import (
    INTERVENTIONS,
    find_matches,
    init_db,
    load_interventions,
    matching_score,
)
from darukaa.measurements.profile import (
    Category,
    ClimateMetrics,
    EnvironmentalProfile,
    LandUseMetrics,
    LandUseType,
    SoilMetrics,
)

PDF_EXAMPLE_PROFILE = EnvironmentalProfile(
    soil=SoilMetrics(organic_carbon_pct=0.3),
    climate=ClimateMetrics(rainfall_category=Category.LOW),
    land_use=LandUseMetrics(land_use_type=LandUseType.MONOCULTURE),
)


def test_every_domain_has_at_least_one_entry_or_is_documented_as_fallback():
    covered = set()
    for entry in INTERVENTIONS:
        covered.update(entry.domains)
    # climate has no direct interventions in the KB by design (D20 no-match fallback applies).
    assert covered == {"soil", "land_use", "water", "human_impact", "biodiversity"}


def test_specificity_prefers_wheat_vetch_over_generic_agroforestry():
    matches = find_matches({"soil", "land_use"}, PDF_EXAMPLE_PROFILE)
    assert matches[0].id == "wheat_vetch_intercropping"


def test_conflicting_condition_excludes_entry():
    agroforestry_profile = EnvironmentalProfile(
        land_use=LandUseMetrics(land_use_type=LandUseType.AGROFORESTRY)
    )
    entry = next(e for e in INTERVENTIONS if e.id == "wheat_vetch_intercropping")
    assert matching_score(entry, agroforestry_profile) is None


def test_no_match_for_domain_with_no_kb_entry():
    matches = find_matches({"climate"}, PDF_EXAMPLE_PROFILE)
    assert matches == []


def test_sqlite_round_trip():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    loaded = load_interventions(conn)
    assert len(loaded) == len(INTERVENTIONS)
    ids = {e.id for e in loaded}
    assert ids == {e.id for e in INTERVENTIONS}
