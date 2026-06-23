import os

from dotenv import load_dotenv
import ee

load_dotenv()

try:
	GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")
	if GEE_PROJECT_ID:
		ee.Initialize(project=GEE_PROJECT_ID)
	else:
		ee.Initialize()
except Exception as e:
	print(f"Warning: Google Earth Engine failed to initialize on import: {e}")
	print("GEE-dependent pipeline features will fail unless authenticated later.")

VADODARA_AOI = ee.Geometry.Rectangle([73.10, 22.25, 73.30, 22.45])


def get_sentinel2_composite(date_start: str, date_end: str) -> ee.Image:
	collection = None
	for threshold in [20, 50, 80]:
		candidate = (
			ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
			.filterBounds(VADODARA_AOI)
			.filterDate(date_start, date_end)
			.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", threshold))
		)
		if candidate.size().getInfo() > 0:
			collection = candidate
			if threshold > 20:
				print(f"  Warning: used {threshold}% cloud threshold for {date_start}–{date_end}")
			break
	if collection is None:
		raise ValueError(
			f"No Sentinel-2 images found for {date_start}–{date_end} in the AOI "
			"even at 80% cloud cover. Use a different date range."
		)

	median = collection.median()

	ndvi = median.normalizedDifference(["B8", "B4"]).rename("NDVI")
	ndbi = median.normalizedDifference(["B11", "B8"]).rename("NDBI")

	bsi = (
		median.expression(
			"((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))",
			{
				"SWIR": median.select("B11"),
				"RED": median.select("B4"),
				"NIR": median.select("B8"),
				"BLUE": median.select("B2"),
			},
		)
		.rename("BSI")
	)

	return median.addBands([ndvi, ndbi, bsi])


def get_sentinel1_composite(date_start: str, date_end: str) -> ee.Image:
	collection = (
		ee.ImageCollection("COPERNICUS/S1_GRD")
		.filterBounds(VADODARA_AOI)
		.filterDate(date_start, date_end)
		.filter(ee.Filter.eq("instrumentMode", "IW"))
		.select(["VV", "VH"])
	)

	return collection.mean()


def get_combined_composite(date_start: str, date_end: str) -> ee.Image:
	sentinel2 = get_sentinel2_composite(date_start, date_end)
	sentinel1 = get_sentinel1_composite(date_start, date_end)
	return ee.Image.cat([sentinel2, sentinel1])


def get_monthly_composites(year_month_list: list) -> list:
	"""Return one Sentinel-2 median composite per (start, end) tuple."""
	composites = []
	for date_start, date_end in year_month_list:
		composites.append(get_sentinel2_composite(date_start, date_end))
	return composites


def get_monthly_sar_composites(year_month_list: list) -> list:
	"""Return one Sentinel-1 median composite per (start, end) tuple."""
	composites = []
	for date_start, date_end in year_month_list:
		composites.append(get_sentinel1_composite(date_start, date_end))
	return composites
