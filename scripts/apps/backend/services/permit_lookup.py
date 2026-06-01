import json
import os
from typing import Any, Dict, List, Optional

from shapely.geometry import shape


def load_permits(file_path: str = "data/samples/vmc_permits.json") -> List[Dict[str, Any]]:
	if not os.path.exists(file_path):
		print(f"Warning: permit file not found at {file_path}")
		return []

	with open(file_path, "r", encoding="utf-8") as permit_file:
		data = json.load(permit_file)

	return data if isinstance(data, list) else []


def get_permit_status(
	site_polygon: Dict[str, Any],
	permits: List[Dict[str, Any]],
) -> str:
	if isinstance(site_polygon, list):
		site_polygon = {
			"type": "Polygon",
			"coordinates": site_polygon,
		}
	site_geom = shape(site_polygon)

	for permit in permits:
		geometry = permit.get("geometry")
		if not geometry:
			continue

		permit_geom = shape(geometry)
		if site_geom.intersects(permit_geom):
			status = str(permit.get("status", "")).lower()
			return "registered" if status == "active" else "expired"

	return "unregistered"


def tag_sites_with_permits(
	sites: List[Dict[str, Any]],
	permits_path: str = "data/samples/vmc_permits.json",
) -> List[Dict[str, Any]]:
	permits = load_permits(permits_path)

	for site in sites:
		polygon = site.get("polygon")
		if polygon:
			site["permitStatus"] = get_permit_status(polygon, permits)
		else:
			site["permitStatus"] = "unregistered"

	return sites
