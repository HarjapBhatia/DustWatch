import os
from pathlib import Path
from dotenv import load_dotenv


#PROJECT PATHS
PIPELINE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PIPELINE_DIR.parent

load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "scripts" / "apps" / "backend" / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))
RAW_DIR = Path(os.getenv("RAW_DIR", DATA_DIR / "raw"))
PATCHES_DIR = Path(os.getenv("PATCHES_DIR", DATA_DIR / "patches"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", DATA_DIR / "models"))
OUTPUTS_DIR = Path(os.getenv("OUTPUTS_DIR", DATA_DIR / "outputs"))

CHANGE_DETECTION_TIF = Path(
    os.getenv(
        "CHANGE_DETECTION_TIF",
        RAW_DIR / "vadodara_change_detection.tif",
    )
)

LABELS_JSON = Path(os.getenv("LABELS_JSON", DATA_DIR / "labels.json"))
PATCHES_INDEX_JSON = Path(os.getenv("PATCHES_INDEX_JSON", PATCHES_DIR / "patches_index.json"))
MODEL_PATH = Path(os.getenv("MODEL_PATH", MODELS_DIR / "rf_construction_model.pkl"))
FEATURE_IMPORTANCE_JSON = Path(
    os.getenv("FEATURE_IMPORTANCE_JSON", OUTPUTS_DIR / "feature_importance.json")
)
CONSTRUCTION_GEOJSON = Path(
    os.getenv("CONSTRUCTION_GEOJSON", OUTPUTS_DIR / "construction_sites.geojson")
)


# EARTH ENGINE CONFIG
GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")

if not GEE_PROJECT_ID:
    raise ValueError(
        "Missing GEE_PROJECT_ID. Add it to .env"
    )

CITY_NAME = "Vadodara"
AOI_BBOX = [73.10, 22.25, 73.45, 22.55]
GEE_DRIVE_FOLDER = "GEE_Vadodara"
CHANGE_EXPORT_DESCRIPTION = "vadodara_change_detection_export"
CHANGE_EXPORT_PREFIX = "vadodara_change_detection"


#IMAGERY CONFIG
T1_START = "2025-01-01"
T1_END = "2025-04-01"

T2_START = "2025-10-01"
T2_END = "2026-01-01"

CLOUD_COVER_MAX = 20
EXPORT_SCALE = 10
EXPORT_CRS = "EPSG:4326"


#PATCH / MODEL CONFIG

PATCH_SIZE = 256
PATCH_STRIDE = 128

BAND_NAMES = [
    "NDVI_T1",
    "NDVI_T2",
    "BSI_T1",
    "BSI_T2",
    "DELTA_NDVI",
    "DELTA_BSI",
    "VV",
    "VH",
]


#Create local output directories used by the pipeline
def ensure_dirs() -> None:
    for path in [DATA_DIR, RAW_DIR, PATCHES_DIR, MODELS_DIR, OUTPUTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
