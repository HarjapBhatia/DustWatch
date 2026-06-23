import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from models.site import CityStats
from services.risk_scorer import compute_city_stats
from services.population_exposure import compute_zone_exposure, ZONES


router = APIRouter()


@router.get("/stats/population_exposure")
def get_population_exposure(
    period: str = Query("oct_dec_2025"),
    pollutant: str = Query("pm10"),
    threshold: float = Query(0.1, ge=0.0),
):
    valid_periods = {"oct_dec_2025", "jan_mar_2026", "apr_may_2026"}
    valid_pollutants = {"pm10", "pm25"}
    if period not in valid_periods:
        raise HTTPException(400, detail=f"Invalid period. Choose from {sorted(valid_periods)}")
    if pollutant not in valid_pollutants:
        raise HTTPException(400, detail=f"Invalid pollutant. Choose from {sorted(valid_pollutants)}")
    try:
        return compute_zone_exposure(period, pollutant, threshold)
    except FileNotFoundError as e:
        raise HTTPException(404, detail=str(e))


@router.get("/stats", response_model=CityStats)
def get_stats() -> CityStats:
	output_path = "data/samples/vadodara_sites.geojson"
	if not os.path.exists(output_path):
		return CityStats(
			totalSites=0,
			critical=0,
			high=0,
			medium=0,
			low=0,
			unregistered=0,
			populationExposed=0,
			lastUpdated=datetime.now(timezone.utc).isoformat(),
		)

	with open(output_path, "r", encoding="utf-8") as stats_file:
		data = json.load(stats_file)

	features = data.get("features", [])
	sites = [
		{
			**feature.get("properties", {}),
			"polygon": feature.get("geometry", {}).get("coordinates"),
		}
		for feature in features
	]
	return CityStats(**compute_city_stats(sites))
