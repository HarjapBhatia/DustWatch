# DustWatch

DustWatch is a geospatial machine learning and web platform designed to detect, monitor, and analyze urban construction activity. By leveraging public satellite imagery and automated change detection algorithms, the platform generates transparent and reproducible evidence of active construction zones. This enables municipal compliance tracking, public accountability, and dust pollution risk analysis.

The project was originally developed as a prototype for the Parul University Environment Hackathon (SDG Olympiad 2026), focusing on construction dust accountability in Vadodara, Gujarat, India.

---

## Technical Overview

Particulate pollution contributes significantly to air quality degradation in developing cities. Urban construction activity accounts for a substantial fraction of particulate matter loading, yet compliance oversight is frequently constrained by manual reporting methods and unregistered sites.

DustWatch addresses this gap using satellite imagery and machine learning to construct a dynamic inventory of active construction projects. The platform consists of three core layers:

1. **Data Ingestion and Processing Layer**: Integrates with Google Earth Engine to retrieve, cloud-mask, and composite optical and radar satellite imagery.
2. **Analysis and Inference Layer**: Combines multi-spectral temporal change detection with a Random Forest machine learning classifier to identify construction zones and assess their particulate exposure risk.
3. **Visualization and API Layer**: Serves site metrics, geographical boundaries, and simulated dust dispersion models through a FastAPI backend to an interactive React and Leaflet mapping client.

---

## System Architecture

The pipeline processes geospatial and optical data through a series of stages:

```
[Satellite Data Ingestion]
  - Sentinel-1 SAR (Radar)
  - Sentinel-2 MSI (Optical)
       |
       v
[Google Earth Engine Compositing]
  - Cloud filtering and median stacking
  - Spectral index calculation (BSI, NDVI, NDBI)
       |
       v
[Stage 1: Change Detection Candidates]
  - Spatial thresholding on BSI increase and NDVI drop
  - Extraction of candidate polygon boundaries
       |
       v
[Stage 2: Precision Classification]
  - Extraction of 21 temporal feature bands across a 3-month composite
  - Random Forest inference (predicting confidence score)
  - Confidence threshold filtering (cutoff at 0.45)
       |
       v
[Geospatial Enrichment & Modeling]
  - Proximity calculations for schools and hospitals (OpenStreetMap)
  - Cross-referencing municipal permit databases
  - Gaussian plume dispersion modeling (Open-Meteo wind data)
       |
       v
[API & UI Serving]
  - FastAPI endpoint serialization
  - React, Tailwind, and Leaflet dashboard rendering
```

---

## Technology Stack

### Backend
* **Language**: Python 3.10 or higher
* **Framework**: FastAPI and Uvicorn for the REST API
* **Geospatial Processing**: Google Earth Engine (earthengine-api, geemap), rasterio, geopandas, shapely, pyproj
* **Machine Learning**: scikit-learn (Random Forest classifier), joblib
* **Data Processing**: numpy, pandas, Pydantic
* **External APIs**: OpenStreetMap (Overpass API) for school and hospital features, Open-Meteo Archive API for wind vectors

### Frontend
* **Framework**: React 19 with TypeScript
* **Build Tooling**: Vite 8
* **Mapping Library**: Leaflet.js with react-leaflet
* **Basemaps**: Esri World Imagery and OpenStreetMap
* **Styling**: Tailwind CSS

---

## Repository Structure

```
DustWatch/
├── data-pipeline/                 Original standalone pipeline for local raster processing
│   ├── change_detection.py        GEE script to export multi-band TIFFs to Google Drive
│   ├── extract_patches.py         Slices GeoTIFF rasters into numpy array patches
│   ├── create_starter_labels.py   Generates weak labels based on index heuristics
│   ├── suggest_patches.py         Active learning patch recommendation script
│   ├── train_model.py             Placeholder Random Forest trainer on local patches
│   ├── generate_geojson.py        Local classifier inference and polygon generation
│   └── requirements.txt           Standalone pipeline Python dependencies
│
├── scripts/
│   └── apps/
│       ├── backend/               FastAPI backend and pipeline scripts
│       │   ├── main.py            REST API entry point and router definitions
│       │   ├── config.py          Path resolving logic and Earth Engine settings
│       │   ├── requirements.txt   Backend Python dependencies
│       │   ├── models/            Pydantic validation schemas
│       │   ├── routers/           API route handlers (sites, stats, layers)
│       │   ├── services/          Domain services (change detection, ML, scoring, plume model)
│       │   ├── scripts/           Updated operational scripts (gee_pipeline, retrain_with_labels)
│       │   ├── data/              Local copies of inputs, models, and processed outputs
│       │   └── static/            Generated dust dispersion overlays
│       │
│       └── frontend/              React frontend application
│           ├── src/
│           │   ├── App.tsx        Root component managing layout and active state
│           │   ├── components/    UI components (Map, Sidebar, SiteCard, StatsBar)
│           │   ├── hooks/         Custom hooks for API ingestion
│           │   └── types/         TypeScript interfaces matching Pydantic backend models
│           └── vite.config.ts     Vite build config with backend reverse-proxy
```

---

## Getting Started

### Prerequisites
* Python 3.10 or higher
* Node.js 18 or higher
* A Google Cloud Project with the Earth Engine API enabled

### Backend Installation

1. Navigate to the root directory and create a virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate the virtual environment:
   * **Windows**:
     ```powershell
     .\.venv\Scripts\activate
     ```
   * **macOS / Linux**:
     ```bash
     source .venv/bin/activate
     ```
3. Install the Python dependencies:
   ```bash
   pip install -r scripts/apps/backend/requirements.txt
   ```
4. Create a `.env` file inside `scripts/apps/backend/` and configure your Google Earth Engine project:
   ```env
   GEE_PROJECT_ID=your-google-cloud-project-id
   ```
5. Authenticate with Google Earth Engine:
   ```bash
   python -c "import ee; ee.Authenticate()"
   ```

### Frontend Installation

1. Navigate to the frontend directory:
   ```bash
   cd scripts/apps/frontend
   ```
2. Install the Node packages:
   ```bash
   npm install
   ```

---

## Pipeline Execution and Operations

To run the data collection, machine learning classification, and enrichment processes, run the operational scripts in sequence from the `scripts/apps/backend/` directory with the virtual environment active.

### Step 1: Model Training
Train the Random Forest classifier using pre-labeled real training data:
```bash
python scripts/retrain_with_labels.py
```
This evaluates a 21-band feature set over the sample coordinates, performs cross-validation, and writes the serialized classifier to `data/models/rf_construction_model.pkl`.

### Step 2: Running Earth Engine Ingestion
Orchestrate the remote collection and candidate detection:
```bash
python scripts/gee_pipeline.py
```
This contacts Google Earth Engine, pulls the Sentinel-1 and Sentinel-2 stack for the Vadodara area of interest, performs baseline change detection, runs inference on candidate patches, and filters them using a confidence score threshold of 0.45. It outputs candidate polygons to `data/processed/candidates.geojson` and sites to `data/samples/vadodara_sites.geojson`.

### Step 3: Geographic Proximity Enrichment
Query OpenStreetMap for sensitive infrastructure:
```bash
python scripts/enrich_proximity.py
```
This queries live schools and hospitals within the bounding box, counts features within a 500-meter radius of each detected site, updates the risk score, and writes the output back to `data/samples/vadodara_sites.geojson`.

### Step 4: Dust Dispersion Rendering
Generate spatial particulate overlays:
```bash
python scripts/build_dust_dispersion.py
```
This evaluates the physical footprint of active sites, extracts wind speed and direction data for historical intervals via Open-Meteo, computes concentrations using a Gaussian plume model, and generates transparent heatmaps inside `static/`.

---

## Starting the Application Servers

With the backend data pre-computed, start the services:

### Start the FastAPI Backend
From `scripts/apps/backend/`:
```bash
uvicorn main:app --reload --port 8000
```
The REST API is served at `http://localhost:8000`. Interactive documentation is available at `http://localhost:8000/docs`.

### Start the React Frontend
In a separate terminal, from `scripts/apps/frontend/`:
```bash
npm run dev
```
The client opens at `http://localhost:3000` and automatically proxies `/api` calls to the FastAPI backend.

---

## Core Algorithms and Logic

### Feature Space
The classification model evaluates a 21-dimensional feature space derived from Sentinel-1 and Sentinel-2 over a 3-month period:
* **Soil Indices**: Bare Soil Index (BSI) values, trends, variances, and consistencies.
* **Vegetation Indices**: Normalized Difference Vegetation Index (NDVI) temporal trend.
* **Urban Indexes**: Normalized Difference Built-Up Index (NDBI) monthly composites.
* **Water Indexes**: Modified Normalized Difference Water Index (MNDWI) minimums to filter riverbed anomalies.
* **Radar Backscatter**: Sentinel-1 SAR VV/VH monthly averages, ratios, and double-bounce indicators.

### Weighted Risk Score
Risk is evaluated as a composite index from 0 to 100:
* **Area Factor** (25% weight): Normalized surface area relative to a 20,000 square meter baseline.
* **Duration Factor** (25% weight): Cumulative days of detected activity relative to a 90-day baseline.
* **Proximity Factor** (30% weight): Spatial count of schools and hospitals within 500 meters.
* **Permit Factor** (20% weight): Deductions based on permit registration status (0 for registered, 100 for unregistered).

Sites are classified into risk categories based on their score:
* **Critical**: Score greater than or equal to 75
* **High**: Score greater than or equal to 50
* **Medium**: Score greater than or equal to 25
* **Low**: Score less than 25

### Air Dispersion Modeling
Plume dispersion is calculated using the Gaussian Plume equation:
$$C(x,y,z) = \frac{Q}{2\pi u \sigma_y \sigma_z} \exp\left( \frac{-y^2}{2\sigma_y^2} \right) \left[ \exp\left( \frac{-(z-H)^2}{2\sigma_z^2} \right) + \exp\left( \frac{-(z+H)^2}{2\sigma_z^2} \right) \right]$$
* **Q**: Emission rate (derived from site area using EPA AP-42 construction emission factors)
* **u**: Mean wind speed at release height
* **$\sigma_y, \sigma_z$**: Dispersion coefficients parameterizing crosswind and vertical spread (Briggs urban coefficients)
* **H**: Effective emission height

---

## API Reference

### GET /api/sites
Returns a list of all detected construction sites.
* **Response Format**: JSON array of site objects containing boundaries, area, risk scores, permit registration, and geographical ward descriptors.

### GET /api/sites/{site_id}
Returns metrics for a single site by ID.

### GET /api/stats
Returns city-wide statistics.
* **Response Format**: Aggregated statistics including total site count, site counts by risk levels, unregistered counts, and estimated population exposure.

### GET /api/layers/modeled_dust
Returns the path and boundaries of the modeled dust dispersion layer.
* **Query Parameters**:
  * `period`: `oct_dec_2025`, `jan_mar_2026`, or `apr_may_2026`
  * `pollutant`: `pm10` or `pm25`
* **Response Format**: Image URL, bounding coordinates, and averaged wind vectors.

---

## System Scope and Constraints

* **Data Frequency**: The system relies on Sentinel imagery updates, limiting temporal tracking granularity to 5-day intervals.
* **Atmospheric Modeling**: The dispersion model is a physical approximation of source emissions and wind transport. It does not measure ambient air quality values directly or replace ground-based monitoring stations.
* **Permit Cross-Referencing**: Permit lookup is dependent on municipal database availability. In this prototype, a static sample dataset containing representative municipal records is used.
* **Model Validation**: The machine learning model is trained on a localized sample of verified sites. In highly reflective environments (such as dry sandy beds or fallow agricultural soil), manual validation may be required to resolve false-positive classifications.

---

## License

This software is released under the MIT License. See the `LICENSE` file for details.
