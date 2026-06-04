import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json

import ee
import pandas as pd
from dotenv import load_dotenv
from shapely.geometry import shape

# GEE is initialised as a side-effect of this import
from services import gee_client, change_detection
from services.classifier import TEMPORAL_FEATURE_NAMES

load_dotenv()

_BACKEND = os.path.join(os.path.dirname(__file__), "..")
POSITIVES_CSV    = os.path.join(_BACKEND, "data/labels/construction_positives.csv")
NEGATIVES_GEOJSON = os.path.join(_BACKEND, "data/samples/vadodara_sites.geojson")
OUTPUT_CSV       = os.path.join(_BACKEND, "data/labels/vadodara_real_training_data.csv")

MONTHLY_PERIODS = [
    ("2025-10-01", "2025-10-31"),
    ("2025-11-01", "2025-11-30"),
    ("2025-12-01", "2025-12-31"),
]

# ---------------------------------------------------------------------------
# Step 2 — Positives
# ---------------------------------------------------------------------------

print(f"Loading positives from {POSITIVES_CSV}...")
pos_df = pd.read_csv(POSITIVES_CSV)
pos_df["label"] = 1
pos_df["class"] = "construction"
print(f"  Positives loaded: {len(pos_df)}")

# ---------------------------------------------------------------------------
# Step 3 — Negatives (pipeline-detected sites treated as false positives)
# ---------------------------------------------------------------------------

print(f"Loading negatives from {NEGATIVES_GEOJSON}...")
if not os.path.exists(NEGATIVES_GEOJSON):
    raise FileNotFoundError(
        f"Pipeline output not found at {NEGATIVES_GEOJSON}. "
        "Run gee_pipeline.py first."
    )

with open(NEGATIVES_GEOJSON, "r", encoding="utf-8") as fh:
    geojson = json.load(fh)

neg_rows = []
for feature in geojson.get("features", []):
    centroid = shape(feature["geometry"]).centroid
    neg_rows.append({"lat": centroid.y, "lon": centroid.x})

neg_df = pd.DataFrame(neg_rows)
neg_df["label"] = 0
neg_df["class"] = "false_positive"
print(f"  Negatives loaded: {len(neg_df)}")

# ---------------------------------------------------------------------------
# Step 4 — Combine
# ---------------------------------------------------------------------------

combined = pd.concat([pos_df[["lat", "lon", "label", "class"]], neg_df],
                     ignore_index=True)
print(f"  Total labelled points: {len(combined)}  "
      f"(pos={len(pos_df)}, neg={len(neg_df)})")

# ---------------------------------------------------------------------------
# Step 5 — Build 13-band temporal feature stack
#
# Nine positive coordinates fall east of the default VADODARA_AOI clip
# boundary (lon > 73.30).  We compute an expanded AOI from all input
# coordinates so every point is covered by the clipped image.
# The S2/S1 ImageCollection filterBounds uses the original VADODARA_AOI,
# which is fine — Sentinel-2 tiles covering Vadodara extend well past 73.30.
# ---------------------------------------------------------------------------

buffer_deg = 0.02
expanded_aoi = ee.Geometry.Rectangle([
    float(combined["lon"].min()) - buffer_deg,
    float(combined["lat"].min()) - buffer_deg,
    float(combined["lon"].max()) + buffer_deg,
    float(combined["lat"].max()) + buffer_deg,
])

print("Building monthly Sentinel-2 composites (Oct/Nov/Dec 2025)...")
monthly_s2 = gee_client.get_monthly_composites(MONTHLY_PERIODS)

print("Building monthly Sentinel-1 composites (Oct/Nov/Dec 2025)...")
monthly_s1 = gee_client.get_monthly_sar_composites(MONTHLY_PERIODS)

print("Computing 13-band temporal feature stack...")
feature_stack = change_detection.compute_temporal_features(
    monthly_s2, monthly_s1, expanded_aoi
)

# ---------------------------------------------------------------------------
# Step 6 — Build GEE FeatureCollection from labelled points
# ---------------------------------------------------------------------------

print("Building GEE FeatureCollection...")
ee_features = []
for _, row in combined.iterrows():
    feat = ee.Feature(
        ee.Geometry.Point([float(row["lon"]), float(row["lat"])]),
        {"label": int(row["label"]), "class": str(row["class"])},
    )
    ee_features.append(feat)

fc = ee.FeatureCollection(ee_features)

# ---------------------------------------------------------------------------
# Step 7 — Sample feature stack at every labelled point
# ---------------------------------------------------------------------------

print("Sampling feature stack at labelled points (may take 1–2 min)...")
sampled = feature_stack.sampleRegions(
    collection=fc,
    scale=10,
    geometries=False,
)

# ---------------------------------------------------------------------------
# Step 8 — Convert sampled FeatureCollection to DataFrame
# ---------------------------------------------------------------------------

print("Fetching results from GEE...")
data = sampled.getInfo()
raw_features = data.get("features", [])
print(f"  GEE returned {len(raw_features)} sampled features")

rows = []
for feat in raw_features:
    props = feat.get("properties", {})
    row = {
        "label": props.get("label"),
        "class": props.get("class"),
    }
    for name in TEMPORAL_FEATURE_NAMES:
        row[name] = props.get(name)
    rows.append(row)

df = pd.DataFrame(rows)
before_drop = len(df)
df = df.dropna()
dropped = before_drop - len(df)

if dropped:
    print(f"  Dropped {dropped} rows with NaN values "
          f"(points outside imagery coverage)")

pos_kept = (df["label"] == 1).sum()
neg_kept = (df["label"] == 0).sum()
print(f"  Final: {len(df)} samples  "
      f"(construction={pos_kept}, false_positive={neg_kept})")

# ---------------------------------------------------------------------------
# Step 9 — Save
# ---------------------------------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved {len(df)} samples → {OUTPUT_CSV}")
print(f"Columns: {list(df.columns)}")
print("\nClass distribution:")
print(df.groupby("class")["label"].count().to_string())
