# DustWatch

A satellite-AI platform for urban construction dust accountability in Indian cities.

DustWatch detects active construction zones from satellite imagery, scores them by pollution risk, and makes the underlying evidence publicly accessible so residents, journalists, and environmental organisations can hold builders accountable for dust suppression compliance.

This repository contains the prototype built for the Parul University Environment Hackathon (SDG Olympiad 2026).

---

## Project Background

India's cities experience year-round particulate pollution far above WHO safe limits. Construction activity contributes roughly 30 percent of urban PM10 loading, yet operates with self-reported compliance and minimal independent oversight. A substantial proportion of construction proceeds without permit registration, making it invisible to municipal authorities by definition.

DustWatch addresses this accountability gap. It uses free Sentinel-1 and Sentinel-2 satellite data, machine learning based change detection, and OpenStreetMap proximity analysis to identify active construction zones at city scale. Each detected site is risk-scored based on area, activity duration, proximity to schools and hospitals, and permit status, then made available through a public web platform.

The platform is positioned as an independent verification layer between construction activity and public accountability. It does not claim to measure ambient air quality directly or replace regulatory enforcement. It generates satellite-verified evidence that anyone can independently reproduce.

---

## Architecture

```
Sentinel-1 SAR + Sentinel-2 MSI
            |
Google Earth Engine processing
            |
13-band temporal feature stack
   (3 monthly composites: Mar, Apr, May 2026)
            |
Change detection
   (BSI, NDVI, NDBI, SAR backscatter)
            |
Random Forest classifier
            |
Permit cross-referencing
            |
Composite risk scoring
            |
FastAPI backend
            |
React frontend with Leaflet map
```

---

## Tech Stack

Backend
- Python 3.10+
- FastAPI, Uvicorn
- Google Earth Engine, geemap
- scikit-learn (Random Forest)
- geopandas, shapely, rasterio
- Pydantic for schema validation

Frontend
- React 18 with TypeScript
- Vite build tooling
- Leaflet.js for mapping
- Esri World Imagery as satellite basemap
- Tailwind CSS

Data Sources
- Sentinel-1 GRD (Copernicus, ESA)
- Sentinel-2 SR Harmonized (Copernicus, ESA)
- OpenStreetMap (Overpass API)
- Sample VMC permit data (placeholder pending RTI response)

---

## Repository Structure

```
DustWatch/
├── apps/
│   ├── backend/
│   │   ├── main.py                       FastAPI entry point
│   │   ├── requirements.txt
│   │   ├── config.py                     Pipeline constants
│   │   ├── routers/
│   │   │   ├── sites.py                  GET /api/sites
│   │   │   └── stats.py                  GET /api/stats
│   │   ├── services/
│   │   │   ├── gee_client.py             GEE auth and image fetch
│   │   │   ├── change_detection.py       Temporal feature stack
│   │   │   ├── classifier.py             RF inference
│   │   │   ├── risk_scorer.py            Composite scoring
│   │   │   └── permit_lookup.py          Geospatial permit overlay
│   │   ├── models/
│   │   │   └── site.py                   Pydantic schemas
│   │   └── scripts/
│   │       ├── gee_pipeline.py           Main pipeline orchestrator
│   │       ├── train_model.py            Classifier training
│   │       ├── enrich_proximity.py       OSM schools and hospitals
│   │       └── build_real_training_data.py
│   └── frontend/
│       ├── src/
│       │   ├── App.tsx
│       │   ├── components/
│       │   │   ├── Map.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   ├── SiteCard.tsx
│       │   │   └── StatsBar.tsx
│       │   ├── hooks/useSites.ts
│       │   ├── types/index.ts
│       │   └── utils/riskColors.ts
│       └── vite.config.ts
└── data/
    ├── samples/
    │   ├── vadodara_sites.geojson        Pipeline output
    │   └── vmc_permits.json              Sample permit data
    ├── labels/
    │   └── construction_positives.csv    Manually verified sites
    └── models/
        └── rf_construction_model.pkl     Trained classifier
```

---

## Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- A Google Earth Engine account with an approved Cloud project
- Git

### Backend Setup

```bash
git clone https://github.com/dhairyasharmaa/DustWatch.git
cd DustWatch

python -m venv .venv
source .venv/bin/activate

pip install -r apps/backend/requirements.txt
```

Create a `.env` file in `apps/backend/`:

```
GEE_PROJECT_ID=your-gee-project-id
```

Authenticate with Google Earth Engine:

```bash
python -c "import ee; ee.Authenticate()"
```

### Frontend Setup

```bash
cd apps/frontend
npm install
```

---

## Running the Pipeline

The pipeline is a sequence of three scripts. Run them in order from the `apps/backend` directory.

### Step 1. Train the Classifier

```bash
python scripts/train_model.py
```

This trains a Random Forest classifier on the labelled dataset and saves the model to `data/models/rf_construction_model.pkl`.

### Step 2. Run the GEE Pipeline

```bash
python scripts/gee_pipeline.py
```

This fetches Sentinel-1 and Sentinel-2 imagery for Vadodara, computes the 13-band temporal feature stack, runs change detection, applies the classifier, computes risk scores, and writes output to `data/samples/vadodara_sites.geojson`. The pipeline takes 5 to 15 minutes depending on GEE processing load.

### Step 3. Enrich with Proximity Data

```bash
python scripts/enrich_proximity.py
```

This queries OpenStreetMap for schools and hospitals within the Vadodara bounding box, computes proximity for each detected site, and re-scores the risk index with proximity weighting.

### Step 4. Start the API Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Auto-generated documentation is at `http://localhost:8000/docs`.

### Step 5. Start the Frontend

In a separate terminal:

```bash
cd apps/frontend
npm run dev
```

The frontend will be available at `http://localhost:3000` and will fetch live data from the backend API.

---

## API Reference

### GET /api/sites

Returns the full list of detected construction sites for the configured city.

Response shape:

```json
[
  {
    "id": "site-001",
    "name": "Construction Site 1",
    "coordinates": [22.3072, 73.1812],
    "polygon": [[lat, lng]],
    "riskLevel": "high",
    "riskScore": 67.4,
    "permitStatus": "unregistered",
    "areaM2": 4200,
    "activeDays": 92,
    "nearbySchools": 2,
    "nearbyHospitals": 1,
    "detectedAt": "2026-03-01",
    "lastUpdated": "2026-05-20"
  }
]
```

### GET /api/sites/{site_id}

Returns a single construction site by ID.

### GET /api/stats

Returns city-level summary statistics.

```json
{
  "totalSites": 138,
  "critical": 0,
  "high": 131,
  "medium": 7,
  "low": 0,
  "unregistered": 136,
  "populationExposed": 585196,
  "lastUpdated": "2026-05-20T06:00:00Z"
}
```

---

## Pipeline Configuration

Constants in `apps/backend/config.py`:

```python
AOI_BOUNDS = [73.10, 22.25, 73.30, 22.45]
MONTHLY_PERIODS = [
    ('2026-03-01', '2026-03-31'),
    ('2026-04-01', '2026-04-30'),
    ('2026-05-01', '2026-05-31'),
]
CONFIDENCE_THRESHOLD = 0.6
MIN_AREA_M2 = 1000
MAX_AREA_M2 = 50000
```

These can be adjusted for different cities or detection sensitivities.

---

## Risk Scoring

The composite risk score is calculated as a weighted sum:

```
score = (area_factor * 0.25)
      + (duration_factor * 0.25)
      + (proximity_factor * 0.30)
      + (permit_factor * 0.20)
      * 100
```

Risk tiers:

```
critical: score >= 75
high:     score >= 50
medium:   score >= 25
low:      score < 25
```

---

## Known Limitations

This is a research prototype built within a four-day hackathon window. Several components are known to have limitations:

1. The classifier was trained on a limited labelled dataset. Ground truth validation showed substantial false positive rates in the current model. Production accuracy requires significantly more labelled examples from the target city.

2. VMC permit data in `data/samples/vmc_permits.json` is sample data. Real permit cross-referencing requires a data sharing agreement with Vadodara Municipal Corporation or successful RTI filing.

3. The `populationExposed` metric uses a heuristic formula based on site area, not census-derived population density.

4. The current pipeline targets Vadodara only. Extension to other cities requires updating the AOI bounding box, retraining the classifier on local imagery, and obtaining city-specific permit data.

5. Pollution attribution claims are limited to construction-source dust. The platform does not measure ambient air quality directly and is not a substitute for ground-based monitoring.

---

## Validation and Reproducibility

Every detected site is traceable to public satellite imagery. The detection metadata includes the Sentinel-2 image date, spectral values, and confidence score. Any third party can reproduce a detection by accessing the same imagery through Google Earth Engine using the published coordinates and date.

Manual verification is possible by taking site coordinates and viewing them on Google Maps satellite view. We encourage independent ground-truth validation of platform outputs.

---

## Future Development

Near-term priorities for moving from prototype to production:

1. Real labelled training data at scale (target: 1000+ labelled examples from Vadodara and additional Indian cities)
2. Integration with live VMC building permit feeds
3. Sentinel-5P aerosol optical depth integration for ambient air quality context
4. Citizen reporting module for community-submitted dust complaints
5. Geographic expansion to additional Indian cities
6. PIL-ready evidence export with court-formatted documentation
7. Carbon credit verification module linking dust suppression compliance to voluntary carbon markets

---

## Team

Dhairya Sharma (lead developer, ML pipeline)
Harjap Singh Bhatia (data engineering, satellite processing)

Parul University, Parul Institute of Engineering and Technology
Vadodara, Gujarat, India

---

## Acknowledgements

This project was developed for the Parul University Environment Hackathon under the SDG Olympiad 2026 framework. We acknowledge the European Space Agency Copernicus Programme for free access to Sentinel satellite data, the Google Earth Engine team for the geospatial processing platform, and the OpenStreetMap community for proximity reference data.

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

## Contact

For questions, collaboration, or feedback, open an issue on this repository or reach out via the team's institutional email.
