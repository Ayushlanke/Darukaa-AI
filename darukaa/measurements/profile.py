from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

# research.md §1.3, Berdugo et al. — lowest of three empirically-grounded aridity thresholds.
ARID_THRESHOLD = 0.54


class Contradiction(Exception):
    """Raised by a structural, field-only contradiction (architecture.md §3, D15).

    Deliberately not a ValueError: pydantic only folds ValueError/AssertionError into its
    own ValidationError, so this propagates distinctly and the conversation layer can catch
    it separately from an ordinary out-of-range field error.
    """


class Category(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LandUseType(str, Enum):
    MONOCULTURE = "monoculture"
    INTERCROPPED = "intercropped"
    AGROFORESTRY = "agroforestry"
    NATURAL_HABITAT = "natural_habitat"
    PASTURE = "pasture"


class Trend(str, Enum):
    DECLINING = "declining"
    STABLE = "stable"
    IMPROVING = "improving"


class PollinatorActivity(str, Enum):
    NONE = "none"
    RARE = "rare"
    MODERATE = "moderate"
    ABUNDANT = "abundant"


class SoilMetrics(BaseModel):
    organic_carbon_pct: Optional[float] = Field(default=None, ge=0, le=100)
    ph: Optional[float] = Field(default=None, ge=0, le=14)
    moisture_pct: Optional[float] = Field(default=None, ge=0, le=100)


class ClimateMetrics(BaseModel):
    rainfall_category: Optional[Category] = None
    rainfall_mm_annual: Optional[float] = Field(default=None, ge=0)
    temperature_c: Optional[float] = None
    aridity_index: Optional[float] = Field(default=None, ge=0, le=3)


class LandUseMetrics(BaseModel):
    land_use_type: Optional[LandUseType] = None
    fragmentation: Optional[Category] = None
    fragmentation_notes: Optional[str] = None


class WaterMetrics(BaseModel):
    availability_category: Optional[Category] = None
    groundwater_trend: Optional[Trend] = None
    irrigation_dependent: Optional[bool] = None


class HumanImpactMetrics(BaseModel):
    pesticide_use: Optional[Category] = None
    deforestation_nearby: Optional[bool] = None
    pollution_notes: Optional[str] = None


class BiodiversityMetrics(BaseModel):
    species_richness_estimate: Optional[Category] = None
    habitat_diversity_index: Optional[Category] = None
    pollinator_activity_observed: Optional[PollinatorActivity] = None
    trend: Optional[Trend] = None


class RegionContext(BaseModel):
    free_text_region: Optional[str] = None
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lon: Optional[float] = Field(default=None, ge=-180, le=180)


DOMAIN_NAMES = ("soil", "climate", "land_use", "water", "human_impact", "biodiversity")


class EnvironmentalProfile(BaseModel):
    soil: SoilMetrics = Field(default_factory=SoilMetrics)
    climate: ClimateMetrics = Field(default_factory=ClimateMetrics)
    land_use: LandUseMetrics = Field(default_factory=LandUseMetrics)
    water: WaterMetrics = Field(default_factory=WaterMetrics)
    human_impact: HumanImpactMetrics = Field(default_factory=HumanImpactMetrics)
    biodiversity: BiodiversityMetrics = Field(default_factory=BiodiversityMetrics)
    region: RegionContext = Field(default_factory=RegionContext)

    @model_validator(mode="after")
    def _check_contradictions(self) -> "EnvironmentalProfile":
        if (
            self.climate.rainfall_category == Category.HIGH
            and self.climate.aridity_index is not None
            and self.climate.aridity_index > ARID_THRESHOLD
        ):
            raise Contradiction(
                "High rainfall was reported together with an aridity index "
                f"({self.climate.aridity_index}) in the arid range (>{ARID_THRESHOLD}); "
                "these are inconsistent."
            )
        return self

    def populated_domains(self) -> list[str]:
        return [name for name in DOMAIN_NAMES if _has_any_field(getattr(self, name))]


def _has_any_field(domain: BaseModel) -> bool:
    return any(value is not None for value in domain.model_dump().values())
