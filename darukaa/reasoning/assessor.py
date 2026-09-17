from dataclasses import dataclass

from darukaa.knowledge.store import EvidenceStore
from darukaa.measurements.profile import Category, EnvironmentalProfile, LandUseType, Trend

EVIDENCE_CEILING = {
    "established_evidence": 0.9,
    "reasonable_inference": 0.6,
    "non_quantifiable": 0.35,
    "engineering_assumption": 0.35,
}

# research.md §1.3, Berdugo et al. — the highest of three empirically-grounded aridity
# thresholds, used only as the "maximally deviant" anchor for a 0-1 internal ranking score.
# It is never shown to the user as a claim in itself.
ARIDITY_DEVIATION_ANCHOR = 0.8

# The numeric bands below are engineering_assumption reference points (research.md's own
# fourth evidence tier — "our own design choice, not a scientific claim"), used only to rank
# internal severity for recommendation ordering. They are never surfaced to the user as a
# cited fact; every fact shown to the user comes from retrieved evidence or the intervention KB.
SOIL_OC_HEALTHY_RANGE = (1.5, 4.0)
SOIL_PH_HEALTHY_RANGE = (6.0, 7.5)
LOW_MOISTURE_THRESHOLD_PCT = 15.0

LAND_USE_DEVIATION = {
    LandUseType.MONOCULTURE: 0.8,
    LandUseType.PASTURE: 0.6,
    LandUseType.INTERCROPPED: 0.4,
    LandUseType.AGROFORESTRY: 0.15,
    LandUseType.NATURAL_HABITAT: 0.05,
}
_HIGH_IS_BAD = {Category.LOW: 0.1, Category.MEDIUM: 0.4, Category.HIGH: 0.8}
_LOW_IS_BAD = {Category.LOW: 0.8, Category.MEDIUM: 0.4, Category.HIGH: 0.1}
_TREND_DEVIATION = {Trend.IMPROVING: 0.1, Trend.STABLE: 0.3, Trend.DECLINING: 0.8}

DOMAIN_QUERIES = {
    "soil": "soil organic carbon pH moisture biodiversity",
    "climate": "rainfall temperature aridity biodiversity",
    "land_use": "land use type fragmentation habitat biodiversity",
    "water": "water availability groundwater species survival",
    "human_impact": "pesticide pollution deforestation biodiversity",
    "biodiversity": "species richness habitat diversity pollinator",
}


@dataclass(frozen=True)
class SubAssessment:
    domain: str
    deviation: float
    confidence: float
    evidence: tuple
    notes: str


def _numeric_deviation(value: float, healthy_low: float, healthy_high: float) -> float:
    if value < healthy_low:
        return min(1.0, (healthy_low - value) / healthy_low) if healthy_low else 1.0
    if value > healthy_high:
        return min(1.0, (value - healthy_high) / healthy_high)
    return 0.0


def _soil_deviation(m):
    if m.organic_carbon_pct is not None:
        return _numeric_deviation(m.organic_carbon_pct, *SOIL_OC_HEALTHY_RANGE)
    if m.ph is not None:
        return _numeric_deviation(m.ph, *SOIL_PH_HEALTHY_RANGE)
    return None


def _climate_deviation(m):
    if m.aridity_index is not None:
        return min(1.0, m.aridity_index / ARIDITY_DEVIATION_ANCHOR)
    if m.rainfall_category is not None:
        return _LOW_IS_BAD[m.rainfall_category]
    return None


def _land_use_deviation(m):
    if m.land_use_type is not None:
        return LAND_USE_DEVIATION[m.land_use_type]
    if m.fragmentation is not None:
        return _HIGH_IS_BAD[m.fragmentation]
    return None


def _water_deviation(m):
    if m.availability_category is not None:
        return _LOW_IS_BAD[m.availability_category]
    return None


def _human_impact_deviation(m):
    if m.pesticide_use is not None:
        return _HIGH_IS_BAD[m.pesticide_use]
    return None


def _biodiversity_deviation(m):
    if m.trend is not None:
        return _TREND_DEVIATION[m.trend]
    if m.species_richness_estimate is not None:
        return _LOW_IS_BAD[m.species_richness_estimate]
    if m.habitat_diversity_index is not None:
        return _LOW_IS_BAD[m.habitat_diversity_index]
    return None


_DEVIATION_FNS = {
    "soil": _soil_deviation,
    "climate": _climate_deviation,
    "land_use": _land_use_deviation,
    "water": _water_deviation,
    "human_impact": _human_impact_deviation,
    "biodiversity": _biodiversity_deviation,
}


def assess(domain: str, profile: EnvironmentalProfile, store: EvidenceStore) -> SubAssessment:
    metrics = getattr(profile, domain)
    deviation = _DEVIATION_FNS[domain](metrics)
    if deviation is None:
        deviation = 0.5  # domain populated but no field maps to a deviation rule: neutral

    query = DOMAIN_QUERIES[domain]
    if profile.region.free_text_region:
        # architecture.md §8 — region is used only as retrieval context/a text signal, never
        # as invented geospatial modeling. Several corpus chunks name a specific region
        # (e.g. "Northwest China", "Zambia"), so this lets BM25 actually respond to it.
        query = f"{query} {profile.region.free_text_region}"
    evidence = tuple(store.retrieve(query, topic=domain))
    if evidence:
        best_type = max(evidence, key=lambda c: EVIDENCE_CEILING.get(c.evidence_type, 0)).evidence_type
        ceiling = EVIDENCE_CEILING.get(best_type, 0.35)
        context_match = 1.0 if len(evidence) >= 2 else 0.8
    else:
        best_type, ceiling, context_match = "non_quantifiable", EVIDENCE_CEILING["non_quantifiable"], 0.6

    confidence = ceiling * context_match
    notes = f"{best_type} evidence, {len(evidence)} chunk(s) retrieved"
    return SubAssessment(domain=domain, deviation=deviation, confidence=confidence, evidence=evidence, notes=notes)


def assess_all(profile: EnvironmentalProfile, store: EvidenceStore) -> dict:
    return {domain: assess(domain, profile, store) for domain in profile.populated_domains()}


def severity(a: SubAssessment) -> float:
    """architecture.md §5.3 — replaces the rejected "AHP-style" combination (D18). No
    cross-domain weights: each domain is ranked independently by deviation x confidence."""
    return a.deviation * a.confidence


def rank_domains(assessments: dict) -> list:
    return sorted(assessments, key=lambda d: severity(assessments[d]), reverse=True)
