import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter

from models.site import CityStats
from services.risk_scorer import compute_city_stats


router = APIRouter()


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
