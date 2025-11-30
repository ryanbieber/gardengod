from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import date, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from gardengod.models import Plant, Garden
from gardengod.optimizer import optimize_garden, calculate_garden_score
import json
from pathlib import Path

# Mock database for now
PLANTS_DB: list[Plant] = []
PLANTS_DICT: dict[str, Plant] = {}

# USDA Zone frost dates (approximate averages)
# Format: zone -> (last_frost_month, last_frost_day, first_frost_month, first_frost_day)
ZONE_FROST_DATES: dict[str, tuple[int, int, int, int]] = {
    "3a": (5, 15, 9, 15),   # May 15 - Sep 15
    "3b": (5, 10, 9, 20),   # May 10 - Sep 20
    "4a": (5, 10, 9, 25),   # May 10 - Sep 25
    "4b": (5, 5, 10, 1),    # May 5 - Oct 1
    "5a": (5, 1, 10, 5),    # May 1 - Oct 5
    "5b": (4, 25, 10, 10),  # Apr 25 - Oct 10
    "6a": (4, 20, 10, 15),  # Apr 20 - Oct 15
    "6b": (4, 15, 10, 20),  # Apr 15 - Oct 20
    "7a": (4, 10, 10, 25),  # Apr 10 - Oct 25
    "7b": (4, 5, 10, 30),   # Apr 5 - Oct 30
    "8a": (3, 25, 11, 5),   # Mar 25 - Nov 5
    "8b": (3, 15, 11, 10),  # Mar 15 - Nov 10
    "9a": (3, 1, 11, 20),   # Mar 1 - Nov 20
    "9b": (2, 15, 12, 1),   # Feb 15 - Dec 1
    "10a": (2, 1, 12, 15),  # Feb 1 - Dec 15
    "10b": (1, 15, 12, 31), # Jan 15 - Dec 31
}


def load_plants() -> None:
    # Use the project root to find data files
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / "data" / "plants.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Plants data file not found at {data_path}")
    with open(data_path) as f:
        data = json.load(f)
        global PLANTS_DB, PLANTS_DICT
        PLANTS_DB = [Plant(**item) for item in data]
        PLANTS_DICT = {p.id: p for p in PLANTS_DB}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    load_plants()
    yield

app = FastAPI(title="Garden God API", lifespan=lifespan)

# Serve static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")


class OptimizeRequest(BaseModel):
    garden: Garden
    plants_to_place: list[str]


class ScoreResponse(BaseModel):
    score: int


class PlantingDate(BaseModel):
    plant_id: str
    plant_name: str
    action: str  # "start_indoors", "direct_sow", "transplant"
    date: str
    week_of_year: int
    notes: str | None = None


class PlantingScheduleResponse(BaseModel):
    zone: str
    last_frost_date: str
    first_frost_date: str
    schedule: list[PlantingDate]


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(static_path / "index.html")


@app.get("/plants", response_model=list[Plant])
async def get_plants() -> list[Plant]:
    return PLANTS_DB


@app.get("/zones")
async def get_zones() -> list[str]:
    return list(ZONE_FROST_DATES.keys())


@app.get("/schedule/{zone}", response_model=PlantingScheduleResponse)
async def get_planting_schedule(zone: str, year: int | None = None) -> PlantingScheduleResponse:
    zone_lower = zone.lower()
    if zone_lower not in ZONE_FROST_DATES:
        raise HTTPException(status_code=400, detail=f"Unknown zone: {zone}. Valid zones: {list(ZONE_FROST_DATES.keys())}")
    
    if year is None:
        year = date.today().year
    
    last_frost_m, last_frost_d, first_frost_m, first_frost_d = ZONE_FROST_DATES[zone_lower]
    last_frost = date(year, last_frost_m, last_frost_d)
    first_frost = date(year, first_frost_m, first_frost_d)
    
    schedule: list[PlantingDate] = []
    
    for plant in PLANTS_DB:
        if not plant.planting:
            continue
        
        p = plant.planting
        
        # Start indoors
        if p.start_indoors_weeks_before_last_frost:
            start_date = last_frost - timedelta(weeks=p.start_indoors_weeks_before_last_frost)
            schedule.append(PlantingDate(
                plant_id=plant.id,
                plant_name=plant.name,
                action="start_indoors",
                date=start_date.isoformat(),
                week_of_year=start_date.isocalendar()[1],
                notes=p.notes,
            ))
        
        # Transplant before last frost
        if p.transplant_weeks_before_last_frost:
            transplant_date = last_frost - timedelta(weeks=p.transplant_weeks_before_last_frost)
            schedule.append(PlantingDate(
                plant_id=plant.id,
                plant_name=plant.name,
                action="transplant",
                date=transplant_date.isoformat(),
                week_of_year=transplant_date.isocalendar()[1],
                notes=p.notes,
            ))
        
        # Transplant after last frost
        if p.transplant_weeks_after_last_frost:
            transplant_date = last_frost + timedelta(weeks=p.transplant_weeks_after_last_frost)
            schedule.append(PlantingDate(
                plant_id=plant.id,
                plant_name=plant.name,
                action="transplant",
                date=transplant_date.isoformat(),
                week_of_year=transplant_date.isocalendar()[1],
                notes=p.notes,
            ))
        
        # Direct sow before last frost
        if p.direct_sow_weeks_before_last_frost:
            sow_date = last_frost - timedelta(weeks=p.direct_sow_weeks_before_last_frost)
            schedule.append(PlantingDate(
                plant_id=plant.id,
                plant_name=plant.name,
                action="direct_sow",
                date=sow_date.isoformat(),
                week_of_year=sow_date.isocalendar()[1],
                notes=p.notes,
            ))
        
        # Direct sow after last frost
        if p.direct_sow_weeks_after_last_frost:
            sow_date = last_frost + timedelta(weeks=p.direct_sow_weeks_after_last_frost)
            schedule.append(PlantingDate(
                plant_id=plant.id,
                plant_name=plant.name,
                action="direct_sow",
                date=sow_date.isoformat(),
                week_of_year=sow_date.isocalendar()[1],
                notes=p.notes,
            ))
        
        # Fall planting
        if p.fall_planting_weeks_before_first_frost:
            fall_date = first_frost - timedelta(weeks=p.fall_planting_weeks_before_first_frost)
            action = "direct_sow" if p.type == "direct_sow" else "transplant"
            schedule.append(PlantingDate(
                plant_id=plant.id,
                plant_name=plant.name,
                action=f"fall_{action}",
                date=fall_date.isoformat(),
                week_of_year=fall_date.isocalendar()[1],
                notes=f"Fall planting. {p.notes}" if p.notes else "Fall planting.",
            ))
    
    # Sort by date
    schedule.sort(key=lambda x: x.date)
    
    return PlantingScheduleResponse(
        zone=zone_lower,
        last_frost_date=last_frost.isoformat(),
        first_frost_date=first_frost.isoformat(),
        schedule=schedule,
    )


@app.post("/garden", response_model=Garden)
async def create_garden(width: int, height: int) -> Garden:
    garden = Garden(width=width, height=height)
    garden.initialize_grid()
    return garden


@app.post("/optimize", response_model=Garden)
async def optimize(request: OptimizeRequest) -> Garden:
    try:
        optimized = optimize_garden(
            garden=request.garden,
            plants_to_place=request.plants_to_place,
            plants_db=PLANTS_DICT,
        )
        return optimized
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/score", response_model=ScoreResponse)
async def get_score(garden: Garden) -> ScoreResponse:
    score = calculate_garden_score(garden, PLANTS_DICT)
    return ScoreResponse(score=score)
