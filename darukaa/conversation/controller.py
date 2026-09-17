from typing import Optional

from darukaa.measurements.profile import EnvironmentalProfile

# D23 — matches the brief's own worked example verbatim ("Can you provide soil organic
# carbon %, rainfall pattern, and land use type?").
DEFAULT_FIELD_SET = ("soil.organic_carbon_pct", "climate.rainfall_category", "land_use.land_use_type")

DOMAIN_FIELD_SETS = {
    "soil": ("soil.organic_carbon_pct", "soil.ph", "soil.moisture_pct"),
    "climate": ("climate.rainfall_category", "climate.temperature_c"),
    "land_use": ("land_use.land_use_type", "land_use.fragmentation"),
    "water": ("water.availability_category", "water.irrigation_dependent"),
    "human_impact": ("human_impact.pesticide_use", "human_impact.deforestation_nearby"),
    "biodiversity": ("biodiversity.trend", "biodiversity.species_richness_estimate"),
}

FIELD_LABELS = {
    "soil.organic_carbon_pct": "soil organic carbon %",
    "soil.ph": "soil pH",
    "soil.moisture_pct": "soil moisture %",
    "climate.rainfall_category": "rainfall pattern",
    "climate.temperature_c": "temperature",
    "land_use.land_use_type": "land use type",
    "land_use.fragmentation": "habitat fragmentation level",
    "water.availability_category": "water availability",
    "water.irrigation_dependent": "whether the land is irrigation-dependent",
    "human_impact.pesticide_use": "pesticide use level",
    "human_impact.deforestation_nearby": "whether deforestation is happening nearby",
    "biodiversity.trend": "biodiversity trend",
    "biodiversity.species_richness_estimate": "observed species richness",
}

DOMAIN_KEYWORDS = {
    "soil": ("soil",),
    "climate": ("rainfall", "climate", "temperature", "drought"),
    "land_use": ("land use", "crop", "monoculture", "farm", "field"),
    "water": ("water", "irrigation", "groundwater"),
    "human_impact": ("pesticide", "pollution", "deforestation", "chemical"),
}
# Deliberately no "biodiversity" entry: a general complaint naming only the outcome itself
# ("biodiversity is declining") names no diagnostic input domain — it should trigger the
# default baseline triage (D23), the same as the brief's own worked example, not a narrow
# question about biodiversity's own fields (which wouldn't explain *why* it's declining).

REASONING_THRESHOLD = 2  # D23 — at least 2 of 6 domains populated before attempting reasoning


def detect_named_domain(message: str) -> Optional[str]:
    lowered = message.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return domain
    return None


def missing_fields_for(profile: EnvironmentalProfile, named_domain: Optional[str]) -> tuple:
    candidate_fields = DOMAIN_FIELD_SETS[named_domain] if named_domain else DEFAULT_FIELD_SET
    missing = []
    for field in candidate_fields:
        domain, attr = field.split(".")
        if getattr(getattr(profile, domain), attr) is None:
            missing.append(field)
    return tuple(missing)


def needs_clarification(profile: EnvironmentalProfile) -> bool:
    return len(profile.populated_domains()) < REASONING_THRESHOLD


def clarifying_question(missing_fields: tuple) -> str:
    labels = [FIELD_LABELS.get(field, field) for field in missing_fields]
    return "Can you provide " + ", ".join(labels) + "?"


def merge_profile(existing: EnvironmentalProfile, updates: dict) -> EnvironmentalProfile:
    """Merges structured JSON input or LLM-extracted fields into the session profile.
    Re-validating via the full model re-runs the contradiction check (architecture.md §3),
    so a merge that creates one raises Contradiction here, not later."""
    base = existing.model_dump()
    for domain, fields in (updates or {}).items():
        if domain not in base or not isinstance(fields, dict):
            continue
        for key, value in fields.items():
            if value is not None and key in base[domain]:
                base[domain][key] = value
    return EnvironmentalProfile(**base)
