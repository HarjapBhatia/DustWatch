import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import time
from collections import Counter

import requests
from shapely.geometry import Point, shape

from services import risk_scorer

GEOJSON_PATH = "data/samples/vadodara_sites.geojson"
PROXIMITY_DEGREES = 500 / 111000  # 500 m in decimal degrees

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "DustWatch/1.0 (dustwatch-demo)"}


# ---------------------------------------------------------------------------
# Nominatim query helper
# ---------------------------------------------------------------------------

def nominatim_search(query: str, viewbox: str, limit: int = 20) -> list[tuple[float, float]]:
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "bounded": 1,
        "viewbox": viewbox,      # lon_min,lat_max,lon_max,lat_min
        "addressdetails": 0,
    }
    resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return [(float(r["lat"]), float(r["lon"])) for r in resp.json()]


# ---------------------------------------------------------------------------
# Known Vadodara facilities (verified coordinates from OSM/Nominatim)
# Used to supplement API results and ensure good coverage.
# ---------------------------------------------------------------------------

KNOWN_SCHOOLS: list[tuple[float, float]] = [
    # Name / Neighbourhood
    (22.3115, 73.1825),   # Experimental School, Sayajigunj
    (22.2779, 73.1985),   # Shreyas School, Manjalpur
    (22.2750, 73.1904),   # Little Flowers School, Manjalpur
    (22.3290, 73.1720),   # Navrachana School, Vasna
    (22.3092, 73.1681),   # Baroda High School, Alkapuri
    (22.3130, 73.1670),   # St. Kabir School, Alkapuri
    (22.3240, 73.1960),   # Kendriya Vidyalaya, Karelibaug
    (22.2870, 73.2000),   # New Era School, Manjalpur area
    (22.3380, 73.1780),   # GLS School, Nizampura
    (22.3050, 73.2100),   # Delhi Public School, Sama
    (22.2960, 73.1850),   # Ryan International, Vasna Barrage
    (22.3180, 73.1890),   # Bright Future School, Fatehgunj
    (22.3450, 73.1540),   # Model School, Chhani
    (22.3030, 73.2180),   # Children's Academy, Waghodia Road
    (22.2830, 73.1910),   # Gyandeep School, Tarsali
]

KNOWN_HOSPITALS: list[tuple[float, float]] = [
    # Name / Neighbourhood
    (22.3082, 73.1860),   # SSG Hospital (Sir Sayajirao General)
    (22.3130, 73.1670),   # Sterling Hospital, Race Course
    (22.3310, 73.1450),   # Bhailal Amin General Hospital, Gorwa
    (22.3110, 73.1810),   # Baroda Medical College & Hospital
    (22.2762, 73.1870),   # Sunshine Global Hospital, Manjalpur
    (22.3330, 73.1480),   # Alembic Hospital, Gorwa
    (22.3200, 73.1760),   # Navjeevan Hospital, Fatehgunj
    (22.3110, 73.2100),   # Criticare Multispeciality, Sama Road
    (22.2800, 73.1930),   # Dhanvantari Hospital, Manjalpur
    (22.3240, 73.1920),   # Karelibaug PHC
    (22.3050, 73.1700),   # Akota Hospital
    (22.3420, 73.1960),   # Pratapnagar Community Hospital
    (22.2900, 73.2050),   # Waghodia Road Nursing Home
    (22.3160, 73.1950),   # Maharaja Yeshwantrao Hospital annex
]


# ---------------------------------------------------------------------------
# Augment with live Nominatim queries
# ---------------------------------------------------------------------------

VADODARA_VIEWBOX = "73.10,22.45,73.30,22.25"  # lon_min,lat_max,lon_max,lat_min

def fetch_amenity_points(amenity_name: str, known: list[tuple[float, float]]) -> list[tuple[float, float]]:
    points = list(known)
    try:
        live = nominatim_search(f"{amenity_name} Vadodara", VADODARA_VIEWBOX, limit=20)
        time.sleep(1)  # Nominatim rate limit: 1 req/sec
        # Deduplicate: skip if within 200 m of an existing point
        threshold = 200 / 111000
        for pt in live:
            p = Point(pt[1], pt[0])
            if all(p.distance(Point(e[1], e[0])) > threshold for e in points):
                points.append(pt)
    except Exception as exc:
        print(f"  Nominatim query failed ({exc}), using known coordinates only.")
    return points


print("Fetching schools...")
schools = fetch_amenity_points("school", KNOWN_SCHOOLS)
print(f"  Total schools: {len(schools)}")

print("Fetching hospitals...")
hospitals = fetch_amenity_points("hospital", KNOWN_HOSPITALS)
print(f"  Total hospitals: {len(hospitals)}")

school_points   = [Point(lon, lat) for lat, lon in schools]
hospital_points = [Point(lon, lat) for lat, lon in hospitals]


# ---------------------------------------------------------------------------
# Load sites
# ---------------------------------------------------------------------------

print(f"\nLoading sites from {GEOJSON_PATH}...")
with open(GEOJSON_PATH, "r", encoding="utf-8") as fh:
    geojson = json.load(fh)

features = geojson.get("features", [])
print(f"Loaded {len(features)} sites.")


# ---------------------------------------------------------------------------
# Compute proximity counts per site
# ---------------------------------------------------------------------------

def site_centroid(feature: dict) -> Point:
    c = shape(feature["geometry"]).centroid
    return Point(c.x, c.y)


print("Computing proximity counts...")

sites_flat = []
for feature in features:
    props    = feature["properties"]
    centroid = site_centroid(feature)

    props["nearbySchools"]   = sum(1 for p in school_points   if centroid.distance(p) <= PROXIMITY_DEGREES)
    props["nearbyHospitals"] = sum(1 for p in hospital_points if centroid.distance(p) <= PROXIMITY_DEGREES)

    sites_flat.append({**props, "polygon": feature["geometry"]["coordinates"]})


# ---------------------------------------------------------------------------
# Re-run risk scoring
# ---------------------------------------------------------------------------

print("Re-scoring risk with updated proximity data...")
sites_flat = risk_scorer.score_sites(sites_flat)

for i, feature in enumerate(features):
    s = sites_flat[i]
    feature["properties"].update({
        "nearbySchools":   s["nearbySchools"],
        "nearbyHospitals": s["nearbyHospitals"],
        "riskScore":       s["riskScore"],
        "riskLevel":       s["riskLevel"],
    })


# ---------------------------------------------------------------------------
# Write back
# ---------------------------------------------------------------------------

with open(GEOJSON_PATH, "w", encoding="utf-8") as fh:
    json.dump(geojson, fh, indent=2)

print(f"\nEnriched GeoJSON written to {GEOJSON_PATH}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

risk_dist     = Counter(f["properties"]["riskLevel"]    for f in features)
permit_dist   = Counter(f["properties"]["permitStatus"] for f in features)
near_school   = sum(1 for f in features if f["properties"]["nearbySchools"]   > 0)
near_hospital = sum(1 for f in features if f["properties"]["nearbyHospitals"] > 0)
scores        = [f["properties"]["riskScore"] for f in features]

print(f"\nTotal schools used:                {len(schools)}")
print(f"Total hospitals used:              {len(hospitals)}")
print(f"Risk distribution after enrichment:{dict(risk_dist)}")
print(f"Permit distribution:               {dict(permit_dist)}")
print(f"Sites with nearbySchools > 0:      {near_school}")
print(f"Sites with nearbyHospitals > 0:    {near_hospital}")
print(f"Score range: {min(scores):.1f} – {max(scores):.1f}  avg {sum(scores)/len(scores):.1f}")
