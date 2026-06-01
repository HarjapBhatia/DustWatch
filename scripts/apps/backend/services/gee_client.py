import os

from dotenv import load_dotenv
import ee

load_dotenv()

GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")
if GEE_PROJECT_ID:
	ee.Initialize(project=GEE_PROJECT_ID)
else:
	ee.Initialize()

VADODARA_AOI = ee.Geometry.Rectangle([73.10, 22.25, 73.30, 22.45])


def get_sentinel2_composite(date_start: str, date_end: str) -> ee.Image:
	collection = (
		ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
		.filterBounds(VADODARA_AOI)
		.filterDate(date_start, date_end)
		.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
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
