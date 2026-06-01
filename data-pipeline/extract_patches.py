import json

import numpy as np
import rasterio
from rasterio.windows import Window

import config


# -----------------------------
# Setup
# -----------------------------

config.ensure_dirs()

patch_size = config.PATCH_SIZE
stride = config.PATCH_STRIDE

print("Starting patch extraction...")
print(f"Input GeoTIFF: {config.CHANGE_DETECTION_TIF}")
print(f"Output folder: {config.PATCHES_DIR}")
print(f"Patch size: {patch_size}x{patch_size}")
print(f"Stride: {stride}")

if not config.CHANGE_DETECTION_TIF.exists():
    raise FileNotFoundError(
        f"Missing change detection GeoTIFF: {config.CHANGE_DETECTION_TIF}"
    )


# -----------------------------
# Patch Extraction
# -----------------------------

patches_index = []

with rasterio.open(config.CHANGE_DETECTION_TIF) as src:
    print(f"Raster size: {src.width} x {src.height}")
    print(f"Band count: {src.count}")
    print(f"CRS: {src.crs}")

    if src.count != len(config.BAND_NAMES):
        raise ValueError(
            f"Expected {len(config.BAND_NAMES)} bands, found {src.count} bands."
        )

    for row in range(0, src.height - patch_size + 1, stride):
        for col in range(0, src.width - patch_size + 1, stride):
            window = Window(col, row, patch_size, patch_size)
            patch = src.read(window=window).astype(np.float32)

            if not np.isfinite(patch).any():
                continue

            patch = np.nan_to_num(patch, nan=0.0, posinf=0.0, neginf=0.0)

            filename = f"patch_row{row}_col{col}.npy"
            patch_path = config.PATCHES_DIR / filename
            np.save(patch_path, patch)

            delta_ndvi = patch[4]
            delta_bsi = patch[5]

            mean_delta_ndvi = float(np.mean(delta_ndvi))
            mean_delta_bsi = float(np.mean(delta_bsi))

            patches_index.append(
                {
                    "patch": filename,
                    "row": row,
                    "col": col,
                    "mean_delta_ndvi": mean_delta_ndvi,
                    "mean_delta_bsi": mean_delta_bsi,
                    "priority_score": mean_delta_bsi - mean_delta_ndvi,
                }
            )


# -----------------------------
# Sort and Save Index
# -----------------------------

print("Sorting patches by construction-likelihood priority...")
patches_index.sort(key=lambda item: item["priority_score"], reverse=True)

with open(config.PATCHES_INDEX_JSON, "w", encoding="utf-8") as f:
    json.dump(patches_index, f, indent=2)

print(f"Saved patch index: {config.PATCHES_INDEX_JSON}")
print(f"Total patches saved: {len(patches_index)}")
