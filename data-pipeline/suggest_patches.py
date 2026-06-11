import json
import rasterio
import config

config.ensure_dirs()

print("Starting suggest_patches.py...")
print(f"Reading patches index from: {config.PATCHES_INDEX_JSON}")
print(f"Reading existing labels from: {config.LABELS_JSON}")
print(f"Reading GeoTIFF from: {config.CHANGE_DETECTION_TIF}")

if not config.PATCHES_INDEX_JSON.exists():
    raise FileNotFoundError(
        f"Missing patch index: {config.PATCHES_INDEX_JSON}. Run extract_patches.py first."
    )

if not config.CHANGE_DETECTION_TIF.exists():
    raise FileNotFoundError(
        f"Missing GeoTIFF file: {config.CHANGE_DETECTION_TIF}. Run GEE export and place it in raw/ folder."
    )

# Load existing labels to avoid suggesting them again
labels_set = set()
if config.LABELS_JSON.exists():
    with open(config.LABELS_JSON, "r", encoding="utf-8") as f:
        existing_labels = json.load(f)
        for item in existing_labels:
            labels_set.add(item["patch"])
print(f"Loaded {len(labels_set)} existing labels.")

# Open GeoTIFF to extract spatial coordinates
with rasterio.open(config.CHANGE_DETECTION_TIF) as src:
    transform = src.transform
    crs = src.crs
    print(f"Loaded raster transform. CRS: {crs}")

def get_patch_center_coords(row, col):
    row_center = row + config.PATCH_SIZE // 2
    col_center = col + config.PATCH_SIZE // 2
    lon, lat = rasterio.transform.xy(transform, row_center, col_center)
    return lon, lat

def is_riverbed_or_road(lon, lat):
    # Vishwamitri River winding zone in Vadodara
    is_river = (73.17 <= lon <= 73.21) and (22.26 <= lat <= 22.34)
    # NH 48 highway corridor on the east side of Vadodara
    is_road = (73.22 <= lon <= 73.25) and (22.25 <= lat <= 22.35)
    return is_river or is_road

# Load patches from index
with open(config.PATCHES_INDEX_JSON, "r", encoding="utf-8") as f:
    patches = json.load(f)
print(f"Loaded {len(patches)} patches from index.")

# Group patches by priority
priority_groups = {1: [], 2: [], 3: [], 4: []}

for item in patches:
    patch_name = item["patch"]
    if patch_name in labels_set:
        continue

    row = item["row"]
    col = item["col"]
    mean_delta_ndvi = item["mean_delta_ndvi"]
    mean_delta_bsi = item["mean_delta_bsi"]

    lon, lat = get_patch_center_coords(row, col)
    in_river_or_road = is_riverbed_or_road(lon, lat)

    # Priority 1: High BSI change + NDVI drop, not riverbed/road
    if not in_river_or_road and mean_delta_bsi > 0.2 and mean_delta_ndvi < -0.2:
        priority_groups[1].append({
            "patch": patch_name,
            "suggested_label": 1,
            "priority": 1,
            "mean_delta_ndvi": round(mean_delta_ndvi, 4),
            "mean_delta_bsi": round(mean_delta_bsi, 4),
            "reason": "High BSI change + NDVI drop, likely construction"
        })
    # Priority 2: Moderate BSI change + NDVI drop, not riverbed/road
    elif not in_river_or_road and mean_delta_bsi > 0.15 and mean_delta_ndvi < -0.15:
        priority_groups[2].append({
            "patch": patch_name,
            "suggested_label": 1,
            "priority": 2,
            "mean_delta_ndvi": round(mean_delta_ndvi, 4),
            "mean_delta_bsi": round(mean_delta_bsi, 4),
            "reason": "Moderate BSI change + NDVI drop, medium confidence construction"
        })
    # Priority 3: NDVI increase, likely vegetation
    elif mean_delta_ndvi > 0.1:
        priority_groups[3].append({
            "patch": patch_name,
            "suggested_label": 0,
            "priority": 3,
            "mean_delta_ndvi": round(mean_delta_ndvi, 4),
            "mean_delta_bsi": round(mean_delta_bsi, 4),
            "reason": "NDVI increase, likely vegetation"
        })
    # Priority 4: High BSI but in riverbed/road (hard negatives)
    elif mean_delta_bsi > 0.15 and in_river_or_road:
        priority_groups[4].append({
            "patch": patch_name,
            "suggested_label": 0,
            "priority": 4,
            "mean_delta_ndvi": round(mean_delta_ndvi, 4),
            "mean_delta_bsi": round(mean_delta_bsi, 4),
            "reason": "High BSI change in known riverbed or road, hard negative"
        })

# Select up to 400 total suggestions in priority order
suggestions = []
counts = {1: 0, 2: 0, 3: 0, 4: 0}

for p in [1, 2, 3, 4]:
    for item in priority_groups[p]:
        if len(suggestions) >= 400:
            break
        suggestions.append(item)
        counts[p] += 1
    if len(suggestions) >= 400:
        break

print("Priority breakdown:")
print(f"  Priority 1: {counts[1]}")
print(f"  Priority 2: {counts[2]}")
print(f"  Priority 3: {counts[3]}")
print(f"  Priority 4: {counts[4]}")
print(f"Total suggestions selected: {len(suggestions)}")

# Save to labeling_queue.json
with open(config.LABELING_QUEUE_JSON, "w", encoding="utf-8") as f:
    json.dump(suggestions, f, indent=2)

print(f"Saved labeling queue to: {config.LABELING_QUEUE_JSON}")
print("suggest_patches.py completed.")
