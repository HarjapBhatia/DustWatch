import os
from pathlib import Path
import ee 
from dotenv import load_dotenv
from datetime import date
from dateutil.relativedelta import relativedelta


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")

if not GEE_PROJECT_ID:
    raise ValueError("Missing GEE_PROJECT_ID in scripts/apps/backend/.env")

ee.Initialize(project=GEE_PROJECT_ID)

print("Earth Engine initialized successfully.")

END_DATE = date.today()
START_DATE = END_DATE - relativedelta(months=6)

START_DATE_STR = START_DATE.isoformat()
END_DATE_STR = END_DATE.isoformat()

# this is area of interest, the area we're look currently (for eg. vadodara)
AOI = ee.Geometry.Rectangle([73.05, 22.20, 73.35, 22.40])

# on those with cloud coverage less than 20% and computing the median pixel values across the image collection
s2 = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(AOI)
    .filterDate(START_DATE_STR, END_DATE_STR)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)) 
    .median()
)

# NDVI = (B8 - B4) / (B8 + B4)
ndvi = s2.normalizedDifference(["B8", "B4"]).rename("NDVI")

# BSI = ((B11+B4) - (B8+B2)) / ((B11+B4) + (B8+B2))
bsi = s2.expression(
    "((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))",
    {
        "SWIR": s2.select("B11"),
        "RED": s2.select("B4"),
        "NIR": s2.select("B8"),
        "BLUE": s2.select("B2"),
    },
).rename("BSI")

s1 = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(AOI)
    .filterDate(START_DATE_STR, END_DATE_STR)
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .select(["VV", "VH"])
    .mean()
)

composite = ee.Image.cat(
    [
        s2.select(["B2", "B3", "B4", "B8", "B11"]),
        s1.select(["VV", "VH"]),
        ndvi, 
        bsi,
    ]
).toFloat()

task = ee.batch.Export.image.toDrive(
    image=composite,
    description="vadodara_sentinel_stack_export",
    folder="GEE_Vadodara",
    fileNamePrefix=f"vadodara_sentinel_stack_{START_DATE_STR}_to_{END_DATE_STR}",
    region=AOI,
    scale=10,
    crs="EPSG:4326",
    fileFormat="GeoTIFF",
    maxPixels=1e13,
)

task.start()

print("Export task started.")
print(f"Task ID : {task.id}")
print("Check status: https://code.earthengine.google.com/tasks")