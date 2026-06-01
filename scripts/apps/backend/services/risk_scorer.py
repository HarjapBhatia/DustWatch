from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


def _cap(value: float, cap: float = 1.0) -> float:
	return min(value, cap)


def compute_risk_score(
	area_m2: float,
	active_days: int,
	nearby_schools: int,
	nearby_hospitals: int,
	permit_status: str,
) -> Dict[str, object]:
	area_score = _cap(area_m2 / 20000)
	duration_score = _cap(active_days / 90)
	proximity_score = _cap(((nearby_schools * 0.6) + (nearby_hospitals * 0.4)) / 5)

	permit_score_map = {
		"registered": 0.0,
		"expired": 0.6,
		"unregistered": 1.0,
	}
	permit_score = permit_score_map.get(permit_status, 0.0)

	raw_score = (
		(area_score * 0.25)
		+ (duration_score * 0.25)
		+ (proximity_score * 0.30)
		+ (permit_score * 0.20)
	)
	score = round(raw_score * 100, 1)

	if score >= 75:
		level = "critical"
	elif score >= 50:
		level = "high"
	elif score >= 25:
		level = "medium"
	else:
		level = "low"

	return {"score": score, "level": level}


def score_sites(sites: List[Dict[str, object]]) -> List[Dict[str, object]]:
	for site in sites:
		result = compute_risk_score(
			area_m2=float(site.get("areaM2", 0.0)),
			active_days=int(site.get("activeDays", 0)),
			nearby_schools=int(site.get("nearbySchools", 0)),
			nearby_hospitals=int(site.get("nearbyHospitals", 0)),
			permit_status=str(site.get("permitStatus", "registered")),
		)
		site["riskScore"] = result["score"]
		site["riskLevel"] = result["level"]

	return sites


def compute_city_stats(sites: List[Dict[str, object]]) -> Dict[str, object]:
	total_sites = len(sites)
	critical = sum(1 for site in sites if site.get("riskLevel") == "critical")
	high = sum(1 for site in sites if site.get("riskLevel") == "high")
	medium = sum(1 for site in sites if site.get("riskLevel") == "medium")
	low = sum(1 for site in sites if site.get("riskLevel") == "low")
	unregistered = sum(
		1 for site in sites if site.get("permitStatus") == "unregistered"
	)

	population_exposed = 0.0
	for site in sites:
		if site.get("riskLevel") in {"critical", "high"}:
			population_exposed += float(site.get("areaM2", 0.0)) * 0.012

	return {
		"totalSites": total_sites,
		"critical": critical,
		"high": high,
		"medium": medium,
		"low": low,
		"unregistered": unregistered,
		"populationExposed": int(round(population_exposed)),
		"lastUpdated": datetime.now(timezone.utc).isoformat(),
	}
