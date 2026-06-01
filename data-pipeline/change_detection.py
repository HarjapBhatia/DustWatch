import ee

import config


# -----------------------------
# Earth Engine Setup
# -----------------------------

print("Initializing Earth Engine...")
ee.Initialize(project=config.GEE_PROJECT_ID)
print("Earth Engine initialized.")


# -----------------------------
# Config
# -----------------------------

aoi = ee.Geometry.Rectangle(config.AOI_BBOX)

drive_folder = getattr(config, "GEE_DRIVE_FOLDER", "GEE_Vadodara")
export_description = getattr(
    config,
    "CHANGE_EXPORT_DESCRIPTION",
    "vadodara_change_detection_export",
)
export_prefix = getattr(config, "CHANGE_EXPORT_PREFIX", "vadodara_change_detection")

print(f"City: {config.CITY_NAME}")
print(f"AOI bbox: {config.AOI_BBOX}")
print(f"T1: {config.T1_START} to {config.T1_END}")
print(f"T2: {config.T2_START} to {config.T2_END}")


# -----------------------------
# Sentinel-2 Helpers
# -----------------------------

def get_sentinel2_composite(start_date: str, end_date: str) -> ee.Image:
    print(f"Building Sentinel-2 composite: {start_date} to {end_date}")

    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", config.CLOUD_COVER_MAX))
        .median()
        .clip(aoi)
    )


def compute_ndvi(image: ee.Image, name: str) -> ee.Image:
    return image.normalizedDifference(["B8", "B4"]).rename(name)


def compute_bsi(image: ee.Image, name: str) -> ee.Image:
    return image.expression(
        "((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))",
        {
            "SWIR": image.select("B11"),
            "RED": image.select("B4"),
            "NIR": image.select("B8"),
            "BLUE": image.select("B2"),
        },
    ).rename(name)


# -----------------------------
# Sentinel-1 Helper
# -----------------------------

def get_sentinel1_composite(start_date: str, end_date: str) -> ee.Image:
    print(f"Building Sentinel-1 composite: {start_date} to {end_date}")

    return (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .select(["VV", "VH"])
        .mean()
        .clip(aoi)
    )


# -----------------------------
# Build Change Detection Stack
# -----------------------------

print("Fetching Sentinel-2 T1...")
s2_t1 = get_sentinel2_composite(config.T1_START, config.T1_END)

print("Fetching Sentinel-2 T2...")
s2_t2 = get_sentinel2_composite(config.T2_START, config.T2_END)

print("Computing NDVI and BSI...")
ndvi_t1 = compute_ndvi(s2_t1, "NDVI_T1")
ndvi_t2 = compute_ndvi(s2_t2, "NDVI_T2")
bsi_t1 = compute_bsi(s2_t1, "BSI_T1")
bsi_t2 = compute_bsi(s2_t2, "BSI_T2")

print("Computing change bands...")
delta_ndvi = ndvi_t2.subtract(ndvi_t1).rename("DELTA_NDVI")
delta_bsi = bsi_t2.subtract(bsi_t1).rename("DELTA_BSI")

print("Fetching Sentinel-1 VV/VH...")
s1 = get_sentinel1_composite(config.T2_START, config.T2_END)

print("Stacking bands...")
change_stack = ee.Image.cat(
    [
        ndvi_t1,
        ndvi_t2,
        bsi_t1,
        bsi_t2,
        delta_ndvi,
        delta_bsi,
        s1.select(["VV", "VH"]),
    ]
).toFloat()


# -----------------------------
# Export to Google Drive
# -----------------------------

print("Starting Google Drive export...")

task = ee.batch.Export.image.toDrive(
    image=change_stack,
    description=export_description,
    folder=drive_folder,
    fileNamePrefix=export_prefix,
    region=aoi,
    scale=config.EXPORT_SCALE,
    crs=config.EXPORT_CRS,
    fileFormat="GeoTIFF",
    maxPixels=1e13,
)

task.start()

print("Export task started.")
print(f"Task ID: {task.id}")
print("Monitor here: https://code.earthengine.google.com/tasks")
