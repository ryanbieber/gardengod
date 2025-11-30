from pydantic import BaseModel, Field


class PlantingInfo(BaseModel):
    """Planting schedule information for a plant."""
    type: str = Field(..., description="'direct_sow' or 'transplant'")
    frost_tolerance: str = Field(..., description="'tender', 'semi_hardy', 'hardy', 'very_hardy'")
    days_to_maturity: list[int] = Field(..., description="[min_days, max_days]")
    
    # Indoor starting (for transplants)
    start_indoors_weeks_before_last_frost: int | None = None
    transplant_weeks_before_last_frost: int | None = None
    transplant_weeks_after_last_frost: int | None = None
    
    # Direct sowing
    direct_sow: bool | None = None
    direct_sow_weeks_before_last_frost: int | None = None
    direct_sow_weeks_after_last_frost: int | None = None
    
    # Fall planting
    fall_planting: bool | None = None
    fall_planting_weeks_before_first_frost: int | None = None
    transplant_for_fall_weeks_before_first_frost: int | None = None
    spring_planting_weeks_before_last_frost: int | None = None
    
    # Succession planting
    succession_planting_weeks: int | None = None
    
    notes: str | None = None


class CareInfo(BaseModel):
    """Care tips for maintaining a plant."""
    watering: str = Field(..., description="Watering instructions")
    watering_frequency: str = Field(..., description="How often to water (e.g., 'daily', 'every 2-3 days')")
    sunlight: str = Field(..., description="Sunlight requirements")
    fertilizing: str | None = None
    pruning: str | None = None
    pests: str | None = None
    harvesting: str | None = None
    tips: list[str] = Field(default_factory=list, description="Additional care tips")


class Plant(BaseModel):
    id: str
    name: str
    spacing_per_sqft: int = Field(..., description="Number of plants that fit in 1 sqft")
    companions: list[str] = Field(default_factory=list, description="List of plant IDs that are beneficial")
    antagonists: list[str] = Field(default_factory=list, description="List of plant IDs that are harmful")
    planting: PlantingInfo | None = None
    care: CareInfo | None = None


class GridCell(BaseModel):
    x: int
    y: int
    plant_id: str | None = None


class Garden(BaseModel):
    width: int = Field(..., gt=0, description="Width of the garden in feet")
    height: int = Field(..., gt=0, description="Height of the garden in feet")
    grid: list[GridCell] = Field(default_factory=list)

    def initialize_grid(self) -> None:
        self.grid = [
            GridCell(x=x, y=y)
            for x in range(self.width)
            for y in range(self.height)
        ]
