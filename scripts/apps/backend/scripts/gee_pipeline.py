import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from datetime import datetime, timezone

import ee
from dotenv import load_dotenv
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

from services import change_detection, classifier, gee_client, permit_lookup, risk_scorer
import config as pipeline_config


BEFORE_START = pipeline_config.T1_START
BEFORE_END = pipeline_config.T1_END
AFTER_START = pipeline_config.T2_START
AFTER_END = pipeline_config.T2_END
OUTPUT_PATH = "data/samples/vadodara_sites.geojson"
CONFIDENCE_THRESHOLD = 0.45
MIN_AREA_M2 = 1000
MAX_AREA_M2 = 50000

MONTHLY_PERIODS = [
    ("2025-10-01", "2025-10-31"),
    ("2025-11-01", "2025-11-30"),
    ("2025-12-01", "2025-12-31"),
]


def build_site_from_feature(feature: dict, index: int) -> dict:
    geom = feature.get("geometry", {})
    if not geom or "type" not in geom:
        geom = {"type": "Polygon", "coordinates": feature.get("polygon", [])}

    polygon = shape(geom)
    centroid = polygon.centroid

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    projected_polygon = transform(transformer.transform, polygon)

    today = datetime.now(timezone.utc)
    after_date = datetime.fromisoformat(AFTER_START).replace(tzinfo=timezone.utc)

    return {
        "id": f"site-{index:03d}",
        "name": f"Construction Site {index}",
        "coordinates": [centroid.y, centroid.x],
        "polygon": geom.get("coordinates"),
        "riskScore": 0.0,
        "riskLevel": "low",
        "permitStatus": "unregistered",
        "areaM2": float(projected_polygon.area),
        "activeDays": (today - after_date).days,
        "nearbySchools": 0,
        "nearbyHospitals": 0,
        "detectedAt": AFTER_START,
        "lastUpdated": today.date().isoformat(),
        "ward": None,
        "address": None,
        "confidenceScore": feature.get("confidenceScore"),
    }


def run_pipeline() -> None:
    load_dotenv()

    print("Initialising GEE...")
    project_id = os.getenv("GEE_PROJECT_ID")
    if project_id:
        ee.Initialize(project=project_id)
    else:
        ee.Initialize()

    print("Running change detection...")
    os.makedirs("data/processed", exist_ok=True)
    candidates_path = "data/processed/candidates.geojson"
    change_detection.run_change_detection(
        BEFORE_START,
        BEFORE_END,
        AFTER_START,
        AFTER_END,
        candidates_path,
    )

    print("Extracting features for classification...")
    if not os.path.exists(candidates_path):
        print(f"Candidates file not found at {candidates_path}")
        sys.exit(1)

    with open(candidates_path, "r", encoding="utf-8") as candidates_file:
        candidates_geojson = json.load(candidates_file)

    if len(candidates_geojson.get("features", [])) == 0:
        print("No candidate zones detected. Try adjusting the")
        print("change detection threshold or date range.")
        print("Exiting pipeline.")
        sys.exit(0)

    print("Building monthly S2/S1 composites...")
    monthly_s2 = gee_client.get_monthly_composites(MONTHLY_PERIODS)
    monthly_s1 = gee_client.get_monthly_sar_composites(MONTHLY_PERIODS)

    print("Computing 21-band temporal feature image...")
    aoi = gee_client.VADODARA_AOI
    temporal_image = change_detection.compute_temporal_features(monthly_s2, monthly_s1, aoi)

    features = classifier.extract_features(candidates_geojson, temporal_image)
    scores = classifier.run_inference(features)

    candidates = candidates_geojson.get("features", [])
    filtered_candidates = classifier.filter_by_confidence(
        candidates,
        scores,
        CONFIDENCE_THRESHOLD,
    )

    print("Building site records...")
    sites = [
        build_site_from_feature(feature, index + 1)
        for index, feature in enumerate(filtered_candidates)
    ]

    print("Tagging permit status...")
    sites = permit_lookup.tag_sites_with_permits(sites)

    print("Computing risk scores...")
    sites = risk_scorer.score_sites(sites)

    sites = [s for s in sites if MIN_AREA_M2 <= s['areaM2'] <= MAX_AREA_M2]
    print(f"After area filter: {len(sites)} sites")

    print("Writing output...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": site["polygon"],
                },
                "properties": {k: v for k, v in site.items() if k != "polygon"},
            }
            for site in sites
        ],
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
        json.dump(output_geojson, output_file, indent=2)

    print(f"Detected {len(sites)} sites")
    print(f"Output written to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_pipeline()
