# DustWatch Data Pipeline

This folder contains the Task 2 geospatial ML pipeline for detecting likely construction activity in Vadodara, India.

## Pipeline Order

Run the scripts from the repository root.

### 1. Export Change Detection GeoTIFF

```powershell
.\.venv\Scripts\python.exe data-pipeline\change_detection.py
```

This starts a Google Earth Engine export task.

Monitor it here:

```text
https://code.earthengine.google.com/tasks
```

When the task completes, download the GeoTIFF from Google Drive and place it at:

```text
data/raw/vadodara_change_detection.tif
```

### 2. Extract Patches

```powershell
.\.venv\Scripts\python.exe data-pipeline\extract_patches.py
```

This creates overlapping 256x256 `.npy` patches in:

```text
data/patches/
```

It also creates:

```text
data/patches/patches_index.json
```

The index is sorted so likely construction-change patches appear first.

### 3. Label Patches

Create:

```text
data/labels.json
```

Use this format:

```json
[
  { "patch": "patch_row0_col256.npy", "label": 1 },
  { "patch": "patch_row128_col512.npy", "label": 0 }
]
```

Labels:

```text
1 = construction
0 = non-construction
```

For a quick pipeline test, label at least 2 patches per class. For a useful model, aim for 50-100 patches per class or more.

For a quick weak-label baseline, you can generate starter labels from the ranked patch index:

```powershell
.\.venv\Scripts\python.exe data-pipeline\create_starter_labels.py
```

This creates 100 weak construction labels from the top-ranked patches and 100 weak non-construction labels from the bottom-ranked patches. Review these labels manually before treating model output as evidence.

### 4. Train Model

```powershell
.\.venv\Scripts\python.exe data-pipeline\train_model.py
```

Outputs:

```text
data/models/rf_construction_model.pkl
data/outputs/feature_importance.json
```

### 5. Generate GeoJSON

```powershell
.\.venv\Scripts\python.exe data-pipeline\generate_geojson.py
```

Output:

```text
data/outputs/construction_sites.geojson
```

## Configuration

Shared configuration lives in:

```text
data-pipeline/config.py
```

The pipeline reads `GEE_PROJECT_ID` from either:

```text
.env
scripts/apps/backend/.env
```

Required environment variable:

```env
GEE_PROJECT_ID=your-google-cloud-project-id
```

## Dependencies

Install dependencies into the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r scripts\apps\backend\requirements.txt
```

## Git Hygiene

Generated rasters, patches, labels, models, and GeoJSON outputs are ignored by Git. Commit the scripts and configuration, not generated data artifacts.
