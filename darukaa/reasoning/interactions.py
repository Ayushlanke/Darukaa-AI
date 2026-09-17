from dataclasses import dataclass, replace

from darukaa.measurements.profile import Category, EnvironmentalProfile, LandUseType, PollinatorActivity, Trend
from darukaa.reasoning.assessor import LOW_MOISTURE_THRESHOLD_PCT


@dataclass(frozen=True)
class InteractionRule:
    id: int
    description: str
    condition: callable
    linked_domains: tuple = ()
    deviation_delta: dict = None
    confidence_delta: dict = None


def _soil_severe(a):
    return "soil" in a and a["soil"].deviation > 0.5


# architecture.md §5.2 — each row traces to a specific coupling in research.md.
RULES = (
    InteractionRule(
        1, "aridity compounds soil degradation (research.md §1.3, Berdugo et al.)",
        lambda p, a: _soil_severe(a) and p.climate.rainfall_category == Category.LOW,
        linked_domains=("soil", "climate"), deviation_delta={"soil": 0.15},
    ),
    InteractionRule(
        2, "monoculture + high fragmentation favors multi-benefit interventions (research.md §1.2)",
        lambda p, a: p.land_use.land_use_type == LandUseType.MONOCULTURE and p.land_use.fragmentation == Category.HIGH,
        linked_domains=("land_use", "biodiversity"),
    ),
    InteractionRule(
        3, "low water availability + irrigation dependence flags drought-driven risk (research.md §1.4)",
        lambda p, a: p.water.availability_category == Category.LOW and p.water.irrigation_dependent is True,
        linked_domains=("water",),
    ),
    InteractionRule(
        4, "high pesticide use + low pollinator activity implicates human impact (research.md §1.5, §1.1)",
        lambda p, a: p.human_impact.pesticide_use == Category.HIGH
        and p.biodiversity.pollinator_activity_observed in (PollinatorActivity.NONE, PollinatorActivity.RARE),
        linked_domains=("human_impact", "biodiversity"), confidence_delta={"human_impact": 0.1},
    ),
    InteractionRule(
        5, "soil pH deviation + declining biodiversity raises soil as primary driver (research.md §1.1)",
        lambda p, a: _soil_severe(a) and p.biodiversity.trend == Trend.DECLINING,
        linked_domains=("soil", "biodiversity"), confidence_delta={"soil": 0.1},
    ),
    InteractionRule(
        6, "high aridity + low habitat diversity flags a discontinuous threshold risk (research.md §1.3)",
        lambda p, a: (p.climate.aridity_index or 0) > 0.7 and p.biodiversity.habitat_diversity_index == Category.LOW,
        linked_domains=("climate", "biodiversity"),
    ),
    InteractionRule(
        7, "land use already favorable; low water availability shifts priority to water (research.md §1.2)",
        lambda p, a: p.land_use.land_use_type in (LandUseType.AGROFORESTRY, LandUseType.NATURAL_HABITAT)
        and p.water.availability_category == Category.LOW,
        linked_domains=("water",), deviation_delta={"land_use": -0.3},
    ),
    InteractionRule(
        8, "nearby deforestation + high fragmentation favors edge/corridor interventions (research.md §1.2)",
        lambda p, a: p.human_impact.deforestation_nearby is True and p.land_use.fragmentation == Category.HIGH,
        linked_domains=("land_use", "human_impact"),
    ),
    InteractionRule(
        9, "low soil moisture compounds soil organic carbon deviation (research.md §1.1, Bogati et al.)",
        lambda p, a: _soil_severe(a) and (p.soil.moisture_pct or 100) < LOW_MOISTURE_THRESHOLD_PCT,
        linked_domains=("soil",), deviation_delta={"soil": 0.15},
    ),
    InteractionRule(
        10, "declining groundwater + irrigation dependence favors recharge/efficiency interventions (research.md §1.4)",
        lambda p, a: p.water.groundwater_trend == Trend.DECLINING and p.water.irrigation_dependent is True,
        linked_domains=("water",),
    ),
    InteractionRule(
        11, "low water availability + declining/low biodiversity links water scarcity to species survival (research.md §1.4)",
        lambda p, a: p.water.availability_category == Category.LOW
        and (p.biodiversity.trend == Trend.DECLINING or p.biodiversity.species_richness_estimate == Category.LOW),
        linked_domains=("water", "biodiversity"),
    ),
)


def apply_interactions(profile: EnvironmentalProfile, assessments: dict):
    fired = [rule for rule in RULES if rule.condition(profile, assessments)]
    adjusted = dict(assessments)
    for rule in fired:
        for domain, delta in (rule.deviation_delta or {}).items():
            if domain in adjusted:
                new_dev = min(1.0, max(0.0, adjusted[domain].deviation + delta))
                adjusted[domain] = replace(adjusted[domain], deviation=new_dev)
        for domain, delta in (rule.confidence_delta or {}).items():
            if domain in adjusted:
                new_conf = min(0.95, max(0.0, adjusted[domain].confidence + delta))
                adjusted[domain] = replace(adjusted[domain], confidence=new_conf)
    return adjusted, fired
