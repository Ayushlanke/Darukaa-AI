import json
import sqlite3
from dataclasses import dataclass
from typing import Optional

from darukaa.measurements.profile import EnvironmentalProfile

EVIDENCE_RANK = {"established_evidence": 2, "reasonable_inference": 1, "non_quantifiable": 0}


@dataclass(frozen=True)
class InterventionEntry:
    id: str
    domains: tuple
    what: str
    why: str
    conditions: dict
    effect_size: str
    impacted_metrics: tuple
    time_horizon: str
    evidence_type: str
    source_name: str
    source_url: str
    limitations: str


# Seed content — every claim here must trace to research.md §1.6 / §1.8 exactly (D24).
INTERVENTIONS = (
    InterventionEntry(
        id="agroforestry",
        domains=("land_use", "soil", "biodiversity"),
        what="Convert monoculture cropland to an agroforestry system (integrate trees/shrubs with crops)",
        why="Raises soil organic carbon and supports pollinator/species richness relative to monoculture, with the largest relative SOC gains in arid/semi-arid zones",
        conditions={"land_use_type": ("monoculture", "pasture")},
        effect_size="SOC stock +10-20% vs. comparison land uses on average, largest relative gains in arid/semi-arid zones; solitary bee species richness up to 10.5x higher vs. adjacent monoculture in one 6-site, 3-year UK study",
        impacted_metrics=("soil_organic_carbon_pct", "pollinator_activity_observed", "species_richness_estimate"),
        time_horizon="long",
        evidence_type="established_evidence",
        source_name="Chatterjee et al. (2018), Agriculture, Ecosystems & Environment 266:55-67; Varah, Jones, Smith & Potts (2020), Agriculture, Ecosystems and Environment 301:107031",
        source_url="https://www.sciencedirect.com/science/article/abs/pii/S0167880918302913",
        limitations="SOC gain is a multi-year-to-decadal effect, not achievable in 2-3 years; the species-richness comparison drew on a smaller sub-sample of data than the yield/soil figures (research.md §1.2 row 7).",
    ),
    InterventionEntry(
        id="wheat_vetch_intercropping",
        domains=("soil", "land_use"),
        what="Introduce temporary wheat-vetch intercropping in place of wheat monoculture",
        why="Raises soil microbial biomass carbon and labile carbon fractions within a single season in dryland semi-arid conditions, alongside improved grain yield",
        conditions={"land_use_type": ("monoculture",), "rainfall_category": ("low",)},
        effect_size="Soil microbial biomass carbon +37%, hot-water-extractable carbon +15%, water-soluble carbon +7% over a 9-week trial vs. wheat monoculture",
        impacted_metrics=("soil_microbial_biomass_carbon", "soil_organic_carbon_pct"),
        time_horizon="short",
        evidence_type="established_evidence",
        source_name="Plant and Soil (2023), wheat-vetch temporary intercropping trial",
        source_url="https://link.springer.com/article/10.1007/s11104-023-05914-x",
        limitations="Single trial; a short-term soil-biology response, not yet shown to translate into long-term SOC stock change.",
    ),
    InterventionEntry(
        id="rotation_reduced_tillage",
        domains=("soil", "land_use"),
        what="Adopt crop rotation combined with reduced or no-tillage in place of continuous monoculture with conventional tillage",
        why="Significantly raises SOC stock, microbial biomass carbon, and microbial respiration vs. conventional tillage, consistent across independent semi-arid studies",
        conditions={"land_use_type": ("monoculture", "pasture")},
        effect_size="Significantly higher SOC stock, microbial biomass carbon, AMF root colonization, and microbial respiration vs. conventional tillage (Mediterranean and Northwest India semi-arid studies)",
        impacted_metrics=("soil_organic_carbon_pct", "soil_microbial_biomass_carbon"),
        time_horizon="medium",
        evidence_type="established_evidence",
        source_name="Agronomy (MDPI) 12(4):953 (2022); ICAR-CSSRI Karnal study",
        source_url="https://www.mdpi.com/2073-4395/12/4/953",
        limitations="Effect size is not given as a single universal percentage; direction is consistent but magnitude is site-specific.",
    ),
    InterventionEntry(
        id="cover_cropping",
        domains=("soil",),
        what="Introduce cover crops (legume or non-legume) between or alongside main crop cycles",
        why="Raises SOC on average across a large global evidence base; legume cover crops also raise total soil nitrogen",
        conditions={"land_use_type": ("monoculture", "pasture")},
        effect_size="SOC +15.5% on average (95% CI 13.8-17.3%) in a 131-study global meta-analysis; legume-specific integration raises SOC ~4.6% and total N ~7.9% in a separate 173-experiment meta-analysis",
        impacted_metrics=("soil_organic_carbon_pct",),
        time_horizon="medium",
        evidence_type="reasonable_inference",
        source_name="Jian et al. (2020), Soil Biology and Biochemistry",
        source_url="https://www.sciencedirect.com/science/article/abs/pii/S0038071720300328",
        limitations="Medium-to-long-term average effect; the legume-specific upper bound (8.7%) is not independently confirmed.",
    ),
    InterventionEntry(
        id="buffer_strips",
        domains=("soil", "biodiversity"),
        what="Establish tree or grass buffer strips along field margins or waterways",
        why="Raises SOC strongly at the local strip scale; watershed-scale gain is much smaller unless buffer coverage is substantial",
        conditions={"land_use_type": ("monoculture", "pasture")},
        effect_size="Local/strip-scale SOC ~106 vs. ~91 Mg C/ha (top 50cm) in a 26-year-old system; watershed-scale gain only +1.3-1.8% when buffers cover ~10% of the watershed",
        impacted_metrics=("soil_organic_carbon_pct",),
        time_horizon="long",
        evidence_type="established_evidence",
        source_name="Agroforestry Systems (2024), Missouri alley-cropping watershed study",
        source_url="https://link.springer.com/article/10.1007/s10457-024-01043-1",
        limitations="Effect is strongly scale-dependent: large at the strip/local scale, small at the whole-watershed scale unless buffer coverage is substantial.",
    ),
    InterventionEntry(
        id="rainwater_harvesting_tillage",
        domains=("water",),
        what="Adopt in-field rainwater harvesting (IRWH) tillage (runoff strips and basins) instead of conventional tillage",
        why="Concentrates scarce rainfall into the root zone, raising crop biomass under water-limited conditions",
        conditions={"water_availability": ("low",)},
        effect_size="Above-ground dry matter +29% for sole maize, +27% for intercropped maize vs. conventional tillage, in a semi-arid smallholder trial",
        impacted_metrics=("soil_moisture_pct", "crop_yield"),
        time_horizon="short",
        evidence_type="reasonable_inference",
        source_name="Plants (MDPI) 12(17):3027 (2023), In-Field Rainwater Harvesting Tillage in Semi-Arid Ecosystems",
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC10490175/",
        limitations="Single season, single semi-arid site, 7-farm sample — not a robust generalizable percentage.",
    ),
    InterventionEntry(
        id="drought_tolerant_cultivars",
        domains=("water", "land_use"),
        what="Switch to drought-tolerant crop cultivars",
        why="Raises mean yield and substantially reduces yield variance and downside crop-failure risk under water-limited conditions",
        conditions={"water_availability": ("low",)},
        effect_size="Mean yield +15%, yield variance -38%, downside/crop-failure-risk exposure -36%, per a nationally representative smallholder survey (Zambia)",
        impacted_metrics=("crop_yield",),
        time_horizon="medium",
        evidence_type="established_evidence",
        source_name="Amondo, Simtowe, Rahut & Erenstein (2019), International Journal of Climate Change Strategies and Management",
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7774807/",
        limitations="Single-country survey (Zambia); do not generalize the exact percentages to other regions without re-checking.",
    ),
    InterventionEntry(
        id="drip_irrigation",
        domains=("water",),
        what="Convert from surface/furrow irrigation to drip irrigation",
        why="Delivers water to the root zone far more efficiently per unit applied than surface or sprinkler irrigation",
        conditions={"irrigation_dependent": (True,)},
        effect_size="Field-level application efficiency ~90% for drip vs. ~60% for surface/furrow and ~75% for sprinkler (FAO indicative table)",
        impacted_metrics=("irrigation_efficiency",),
        time_horizon="medium",
        evidence_type="established_evidence",
        source_name="FAO, Irrigation Water Management Training Manual, Annex I",
        source_url="https://www.fao.org/4/t7202e/t7202e08.htm",
        limitations="A field-level efficiency gain, not a guaranteed basin-scale water saving — FAO's own review (Perry & Steduto 2017) warns farmers often reallocate saved water to expand irrigated area, so this must never be framed as 'saves X% water' at farm/basin scale.",
    ),
    InterventionEntry(
        id="mulching",
        domains=("water", "soil"),
        what="Apply plastic-film or organic mulching to retain soil moisture",
        why="Raises topsoil moisture and crop yield in water-limited dryland systems",
        conditions={"water_availability": ("low",)},
        effect_size="Grain yield +43.1% on average (19.8-79.4% by crop), topsoil (0-20cm) soil water content +12.9%, in an 83-study meta-analysis of Northwestern China dryland systems",
        impacted_metrics=("soil_moisture_pct", "crop_yield"),
        time_horizon="short",
        evidence_type="established_evidence",
        source_name="Ma, Chen, Qu, Wang, Misselbrook & Jiang (2018), Agricultural Water Management",
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5890387/",
        limitations="China-dryland evidence base; not necessarily transferable at this exact magnitude to other regions.",
    ),
    InterventionEntry(
        id="integrated_pest_management",
        domains=("human_impact", "biodiversity"),
        what="Adopt Integrated Pest Management (IPM) in place of routine broad-spectrum pesticide use",
        why="Cuts pesticide use while typically raising yield, reducing collateral harm to pollinators and soil life",
        conditions={"pesticide_use": ("high", "medium")},
        effect_size="Mean yield +40.9% (SD 72.3) while pesticide use fell to 30.7% of baseline (SD 34.9), across 85 IPM projects in 24 countries",
        impacted_metrics=("pollinator_activity_observed", "crop_yield"),
        time_horizon="medium",
        evidence_type="established_evidence",
        source_name="Pretty & Bharucha (2015), Insects (MDPI) 6(1):152-182",
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC4553536/",
        limitations="Authors' own caveat: the project sample is biased toward published/successful projects, so the population-wide average is likely more modest.",
    ),
    InterventionEntry(
        id="precision_pesticide_application",
        domains=("human_impact",),
        what="Adopt real-time sensor-based ('precision') pesticide spraying in place of blanket application",
        why="Cuts pesticide volume substantially with no measured yield cost",
        conditions={"pesticide_use": ("high", "medium")},
        effect_size="Pesticide volume reduced 12-96% depending on crop/growth stage, spraying cost -56.16%, no measurable yield difference vs. blanket spraying, across 22 commercial fields (Brazilian Cerrado)",
        impacted_metrics=("pollinator_activity_observed",),
        time_horizon="short",
        evidence_type="established_evidence",
        source_name="Zanin, Neves, Teodoro et al. (2022), Scientific Reports 12:6522",
        source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8980047/",
        limitations="Requires sensor-based spraying equipment; regional/crop transferability of the exact percentages is not established.",
    ),
    InterventionEntry(
        id="riparian_buffer_pollution",
        domains=("human_impact", "water", "biodiversity"),
        what="Establish vegetated riparian buffer strips between treated fields and waterways",
        why="Intercepts agrochemical runoff before it reaches surface water",
        conditions={"pesticide_use": ("high", "medium")},
        effect_size="Reported effectiveness 10-100% for pesticide movement and 12-100% for nutrient movement into surface water, strongly dependent on buffer width, slope, soil, and transport pathway",
        impacted_metrics=("pollinator_activity_observed",),
        time_horizon="medium",
        evidence_type="established_evidence",
        source_name="Prosser, Hoekstra, Gene, Truman, White & Hanson (2020), Journal of Environmental Management 261:110210",
        source_url="https://pubmed.ncbi.nlm.nih.gov/32148280/",
        limitations="Effectiveness range is very wide and buffer width alone is a poor predictor — must state slope/soil/flow-path conditions, not a single number.",
    ),
)

_PROFILE_FIELD_MAP = {
    "land_use_type": lambda p: p.land_use.land_use_type,
    "rainfall_category": lambda p: p.climate.rainfall_category,
    "pesticide_use": lambda p: p.human_impact.pesticide_use,
    "water_availability": lambda p: p.water.availability_category,
    "irrigation_dependent": lambda p: p.water.irrigation_dependent,
    "deforestation_nearby": lambda p: p.human_impact.deforestation_nearby,
}


def matching_score(entry: InterventionEntry, profile: EnvironmentalProfile) -> Optional[float]:
    """None if a stated condition conflicts with the profile (entry does not apply).
    Otherwise a specificity score: each matching condition contributes 1/len(allowed values),
    so a narrowly-targeted entry outranks a broadly-applicable one (architecture.md §5.4, D20)."""
    score = 0.0
    for field_name, allowed in entry.conditions.items():
        getter = _PROFILE_FIELD_MAP.get(field_name)
        if getter is None:
            continue
        actual = getter(profile)
        if actual is None:
            continue
        actual_value = actual.value if hasattr(actual, "value") else actual
        if actual_value not in allowed:
            return None
        score += 1 / len(allowed)
    return score


def find_matches(top_domains: set, profile: EnvironmentalProfile, entries=INTERVENTIONS) -> list:
    """Entries that target at least one of top_domains and don't conflict with the profile,
    ranked by (domain overlap, specificity, evidence_type), most-preferred first. Empty means
    no KB entry targets these domains at all — the caller falls back per architecture.md
    §5.4/D20, it must not silently substitute an unrelated entry."""
    candidates = []
    for entry in entries:
        overlap = len(set(entry.domains) & top_domains)
        if overlap == 0:
            continue
        score = matching_score(entry, profile)
        if score is None:
            continue
        candidates.append((entry, overlap, score, EVIDENCE_RANK.get(entry.evidence_type, 0)))
    candidates.sort(key=lambda c: (c[1], c[2], c[3]), reverse=True)
    return [c[0] for c in candidates]


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS interventions ("
        "id TEXT PRIMARY KEY, domains TEXT, what TEXT, why TEXT, conditions TEXT, "
        "effect_size TEXT, impacted_metrics TEXT, time_horizon TEXT, evidence_type TEXT, "
        "source_name TEXT, source_url TEXT, limitations TEXT)"
    )
    existing = conn.execute("SELECT COUNT(*) FROM interventions").fetchone()[0]
    if existing:
        return
    for entry in INTERVENTIONS:
        conn.execute(
            "INSERT INTO interventions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                entry.id,
                json.dumps(entry.domains),
                entry.what,
                entry.why,
                json.dumps(entry.conditions),
                entry.effect_size,
                json.dumps(entry.impacted_metrics),
                entry.time_horizon,
                entry.evidence_type,
                entry.source_name,
                entry.source_url,
                entry.limitations,
            ),
        )
    conn.commit()


def load_interventions(conn: sqlite3.Connection) -> list:
    rows = conn.execute("SELECT * FROM interventions").fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM interventions").description]
    entries = []
    for row in rows:
        record = dict(zip(cols, row))
        entries.append(
            InterventionEntry(
                id=record["id"],
                domains=tuple(json.loads(record["domains"])),
                what=record["what"],
                why=record["why"],
                conditions={k: tuple(v) for k, v in json.loads(record["conditions"]).items()},
                effect_size=record["effect_size"],
                impacted_metrics=tuple(json.loads(record["impacted_metrics"])),
                time_horizon=record["time_horizon"],
                evidence_type=record["evidence_type"],
                source_name=record["source_name"],
                source_url=record["source_url"],
                limitations=record["limitations"],
            )
        )
    return entries
