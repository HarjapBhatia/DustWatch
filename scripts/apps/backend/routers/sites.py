import json
import os
from typing import List

from fastapi import APIRouter, HTTPException

from models.site import ConstructionSite


router = APIRouter()


@router.get("/sites", response_model=List[ConstructionSite])
def list_sites() -> List[ConstructionSite]:
	output_path = "data/samples/vadodara_sites.geojson"
	if not os.path.exists(output_path):
		raise HTTPException(
			status_code=404,
			detail="Pipeline output not found. Run gee_pipeline.py first.",
		)

	with open(output_path, "r", encoding="utf-8") as sites_file:
		data = json.load(sites_file)

	features = data.get("features", [])
	return [
		{
			**feature.get("properties", {}),
			"polygon": feature.get("geometry", {}).get("coordinates"),
		}
		for feature in features
	]


@router.get("/sites/{site_id}", response_model=ConstructionSite)
def get_site(site_id: str) -> ConstructionSite:
	output_path = "data/samples/vadodara_sites.geojson"
	if not os.path.exists(output_path):
		raise HTTPException(
			status_code=404,
			detail="Pipeline output not found. Run gee_pipeline.py first.",
		)

	with open(output_path, "r", encoding="utf-8") as sites_file:
		data = json.load(sites_file)

	for feature in data.get("features", []):
		properties = feature.get("properties", {})
		if properties.get("id") == site_id:
			return {
				**properties,
				"polygon": feature.get("geometry", {}).get("coordinates"),
			}

	raise HTTPException(status_code=404, detail="Site not found")
