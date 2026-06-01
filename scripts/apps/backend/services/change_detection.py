import json

import ee

from . import gee_client


def detect_construction_candidates(
	before_start: str,
	before_end: str,
	after_start: str,
	after_end: str,
) -> ee.FeatureCollection:
	after_s2 = gee_client.get_sentinel2_composite(after_start, after_end)
	after_s1 = gee_client.get_sentinel1_composite(after_start, after_end)

	bare_soil = after_s2.select("BSI").gt(0.05)
	low_ndvi = after_s2.select("NDVI").lt(0.25)
	disturbed_surface = after_s2.select("NDBI").gt(-0.1)
	active_backscatter = after_s1.select("VV").gt(-15)

	construction_mask = bare_soil.And(low_ndvi).And(disturbed_surface).And(active_backscatter)

	cleaned = (
		construction_mask
		.focal_min(radius=1, kernelType="square", units="pixels")
		.focal_max(radius=2, kernelType="square", units="pixels")
		.selfMask()
	)

	vectors = cleaned.reduceToVectors(
		geometry=gee_client.VADODARA_AOI,
		scale=20,
		maxPixels=1e9,
		geometryType="polygon",
		eightConnected=False,
		bestEffort=True,
	)

	vectors = vectors.map(lambda f: f.set("area", f.geometry().area(maxError=1)))
	return vectors.filter(ee.Filter.gt("area", 300))


def export_candidates_to_geojson(
	candidates: ee.FeatureCollection,
	output_path: str,
) -> dict:
	data = candidates.getInfo()
	with open(output_path, "w", encoding="utf-8") as geojson_file:
		json.dump(data, geojson_file)

	feature_count = len(data.get("features", []))
	print(f"Found {feature_count} candidate zones")
	return data


def run_change_detection(
	before_start: str,
	before_end: str,
	after_start: str,
	after_end: str,
	output_path: str,
) -> dict:
	candidates = detect_construction_candidates(
		before_start,
		before_end,
		after_start,
		after_end,
	)
	return export_candidates_to_geojson(candidates, output_path)
