import json

import joblib
import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.windows import Window
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

import config


# -----------------------------
# Setup
# -----------------------------

config.ensure_dirs()

patch_size = config.PATCH_SIZE
stride = config.PATCH_STRIDE

print("Starting construction GeoJSON generation...")
print(f"Input GeoTIFF: {config.CHANGE_DETECTION_TIF}")
print(f"Model path: {config.MODEL_PATH}")
print(f"Output GeoJSON: {config.CONSTRUCTION_GEOJSON}")

if not config.CHANGE_DETECTION_TIF.exists():
    raise FileNotFoundError(f"Missing GeoTIFF: {config.CHANGE_DETECTION_TIF}")

if not config.MODEL_PATH.exists():
    raise FileNotFoundError(f"Missing trained model: {config.MODEL_PATH}")



# Load Model
print("Loading Random Forest model...")
model = joblib.load(config.MODEL_PATH)



# Sliding Window Prediction
with rasterio.open(config.CHANGE_DETECTION_TIF) as src:
    print(f"Raster size: {src.width} x {src.height}")
    print(f"Band count: {src.count}")
    print(f"CRS: {src.crs}")

    if src.count != len(config.BAND_NAMES):
        raise ValueError(
            f"Expected {len(config.BAND_NAMES)} bands, found {src.count} bands."
        )

    prediction_map = np.zeros((src.height, src.width), dtype=np.uint8)
    windows_scanned = 0
    windows_positive = 0

    for row in range(0, src.height - patch_size + 1, stride):
        for col in range(0, src.width - patch_size + 1, stride):
            window = Window(col, row, patch_size, patch_size)
            patch = src.read(window=window).astype(np.float32)
            patch = np.nan_to_num(patch, nan=0.0, posinf=0.0, neginf=0.0)

            feature_vector = patch.mean(axis=(1, 2)).reshape(1, -1)
            prediction = int(model.predict(feature_vector)[0])
            windows_scanned += 1

            if prediction == 1:
                prediction_map[
                    row : row + patch_size,
                    col : col + patch_size,
                ] = 1
                windows_positive += 1

    print(f"Windows scanned: {windows_scanned}")
    print(f"Windows predicted construction: {windows_positive}")

    print("Converting prediction map to polygons...")
    raw_polygons = []

    for geom, value in shapes(prediction_map, mask=prediction_map == 1, transform=src.transform):
        if int(value) == 1:
            raw_polygons.append(shape(geom))

    if raw_polygons:
        merged = unary_union(raw_polygons)
        polygons = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
    else:
        polygons = []


# Build GeoJSON

features = []

for idx, polygon in enumerate(polygons, start=1):
    features.append(
        {
            "type": "Feature",
            "id": f"vadodara-construction-{idx:04d}",
            "geometry": mapping(polygon),
            "properties": {
                "label": "construction",
                "detection_method": "random_forest",
                "city": config.CITY_NAME,
            },
        }
    )

feature_collection = {
    "type": "FeatureCollection",
    "features": features,
}

with open(config.CONSTRUCTION_GEOJSON, "w", encoding="utf-8") as f:
    json.dump(feature_collection, f, indent=2)

print(f"Saved GeoJSON: {config.CONSTRUCTION_GEOJSON}")
print(f"Total construction zones detected: {len(features)}")
