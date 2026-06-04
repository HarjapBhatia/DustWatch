import json

import ee

from . import gee_client


def _s2_composite(date_start: str, date_end: str) -> ee.Image:
    """Sentinel-2 median composite, relaxing cloud filter progressively if needed."""
    collection = None
    for threshold in [30, 50, 80]:
        candidate = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(gee_client.VADODARA_AOI)
            .filterDate(date_start, date_end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", threshold))
        )
        if candidate.size().getInfo() > 0:
            collection = candidate
            if threshold > 30:
                print(f"  Warning: used {threshold}% cloud threshold for {date_start}–{date_end}")
            break
    if collection is None:
        raise ValueError(
            f"No Sentinel-2 images found for {date_start}–{date_end} in the AOI "
            "even at 80% cloud cover. Use a different date range."
        )
    median = collection.median()
    ndvi = median.normalizedDifference(["B8", "B4"]).rename("NDVI")
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
    return median.addBands([ndvi, bsi])


def detect_construction_candidates(
    before_start: str,
    before_end: str,
    after_start: str,
    after_end: str,
) -> ee.FeatureCollection:
    before_s2 = _s2_composite(before_start, before_end)
    after_s2 = _s2_composite(after_start, after_end)
    after_s1 = gee_client.get_sentinel1_composite(after_start, after_end)

    bsi_diff = after_s2.select("BSI").subtract(before_s2.select("BSI"))
    ndvi_diff = after_s2.select("NDVI").subtract(before_s2.select("NDVI"))

    construction_mask = (
        bsi_diff.gt(0.08)                     # BSI increased — soil more exposed
        .And(ndvi_diff.lt(-0.05))              # NDVI decreased — vegetation removed
        .And(after_s2.select("BSI").gt(0.02)) # after period is actually bare
        .And(after_s2.select("NDVI").lt(0.25)) # not vegetated in after period
        .And(after_s1.select("VV").gt(-16))   # SAR confirms surface disturbance
    )

    cleaned = (
        construction_mask
        .clip(gee_client.VADODARA_AOI)
        .focal_min(radius=1, kernelType="square", units="pixels")
        .focal_max(radius=2, kernelType="square", units="pixels")
        .selfMask()
    )

    vectors = cleaned.reduceToVectors(
        geometry=gee_client.VADODARA_AOI,
        scale=20,
        maxPixels=1e9,
        geometryType="polygon",
        eightConnected=False,
        bestEffort=True,
    )

    vectors = vectors.map(lambda f: f.set("area", f.geometry().area(maxError=1)))
    return vectors.filter(
        ee.Filter.And(
            ee.Filter.gt("area", 2000),
            ee.Filter.lt("area", 30000),
        )
    )


def compute_temporal_features(
    monthly_s2_composites: list,
    monthly_s1_composites: list,
    aoi,
) -> ee.Image:
    """Compute 21-band temporal feature image from 3 monthly S2+S1 composites."""

    def _bsi(img: ee.Image) -> ee.Image:
        return img.expression(
            "((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE))",
            {
                "SWIR": img.select("B11"),
                "RED":  img.select("B4"),
                "NIR":  img.select("B8"),
                "BLUE": img.select("B2"),
            },
        )

    def _ndvi(img: ee.Image) -> ee.Image:
        return img.normalizedDifference(["B8", "B4"])

    def _mndwi(img: ee.Image) -> ee.Image:
        # Negative for dry land/construction, positive for water/riverbeds
        return img.normalizedDifference(["B3", "B11"])

    s2_m1, s2_m2, s2_m3 = monthly_s2_composites
    s1_m1, s1_m2, s1_m3 = monthly_s1_composites

    # --- BSI ---
    bsi_m1 = _bsi(s2_m1).rename("BSI_month1")
    bsi_m2 = _bsi(s2_m2).rename("BSI_month2")
    bsi_m3 = _bsi(s2_m3).rename("BSI_month3")

    bsi_trend       = bsi_m3.subtract(bsi_m1).rename("BSI_trend")
    bsi_consistency = bsi_m1.min(bsi_m2).min(bsi_m3).rename("BSI_consistency")
    bsi_avg_ends    = bsi_m1.add(bsi_m3).divide(2)
    bsi_variance    = bsi_m2.subtract(bsi_avg_ends).rename("BSI_variance")

    # --- NDVI ---
    ndvi_m1    = _ndvi(s2_m1)
    ndvi_m3    = _ndvi(s2_m3)
    ndvi_trend = ndvi_m1.subtract(ndvi_m3).rename("NDVI_trend")

    # --- NDBI: already computed in gee_client, just select the band ---
    # Rises as concrete, asphalt, and foundations appear.
    # Riverbeds score strongly negative; construction sites rise toward +0.3.
    ndbi_m1    = s2_m1.select("NDBI").rename("NDBI_month1")
    ndbi_m2    = s2_m2.select("NDBI").rename("NDBI_month2")
    ndbi_m3    = s2_m3.select("NDBI").rename("NDBI_month3")
    ndbi_trend = ndbi_m3.subtract(ndbi_m1).rename("NDBI_trend")

    # --- MNDWI minimum across 3 months ---
    # Riverbed sand scores +0.1 to +0.4; dry construction ground scores -0.3 to -0.1.
    # The minimum (most-water-like month) is taken so seasonal dryness doesn't mask rivers.
    mndwi_min = (
        _mndwi(s2_m1).min(_mndwi(s2_m2)).min(_mndwi(s2_m3))
        .rename("MNDWI_min")
    )

    # --- SAR VV ---
    vv_m1 = s1_m1.select("VV").rename("VV_month1")
    vv_m2 = s1_m2.select("VV").rename("VV_month2")
    vv_m3 = s1_m3.select("VV").rename("VV_month3")

    vv_trend       = vv_m3.subtract(vv_m1).rename("VV_trend")
    vv_consistency = vv_m1.max(vv_m2).max(vv_m3).rename("VV_consistency")

    vh_vv_m1           = s1_m1.select("VH").divide(s1_m1.select("VV"))
    vh_vv_m3           = s1_m3.select("VH").divide(s1_m3.select("VV"))
    vh_vv_ratio_change = vh_vv_m3.subtract(vh_vv_m1).rename("VH_VV_ratio_change")

    # --- VV−VH absolute difference (double-bounce proxy) ---
    # Metal structures and rough excavated terrain drive VV up relative to VH.
    # High VV−VH = double-bounce = construction materials / structures.
    vv_vh_diff_m1    = s1_m1.select("VV").subtract(s1_m1.select("VH")).rename("VV_VH_diff_month1")
    vv_vh_diff_m3    = s1_m3.select("VV").subtract(s1_m3.select("VH")).rename("VV_VH_diff_month3")
    vv_vh_diff_trend = vv_vh_diff_m3.subtract(vv_vh_diff_m1).rename("VV_VH_diff_trend")

    return ee.Image.cat([
        bsi_m1, bsi_m2, bsi_m3,
        bsi_trend, bsi_consistency, bsi_variance,
        ndvi_trend,
        ndbi_m1, ndbi_m2, ndbi_m3,
        ndbi_trend,
        mndwi_min,
        vv_m1, vv_m2, vv_m3,
        vv_trend, vv_consistency,
        vh_vv_ratio_change,
        vv_vh_diff_m1, vv_vh_diff_m3,
        vv_vh_diff_trend,
    ]).clip(aoi)


def export_candidates_to_geojson(
	candidates: ee.FeatureCollection,
	output_path: str,
) -> dict:
	data = candidates.getInfo()
	with open(output_path, "w", encoding="utf-8") as geojson_file:
		json.dump(data, geojson_file)

	feature_count = len(data.get("features", []))
	print(f"Found {feature_count} candidate zones")
	return data


def run_change_detection(
	before_start: str,
	before_end: str,
	after_start: str,
	after_end: str,
	output_path: str,
) -> dict:
	candidates = detect_construction_candidates(
		before_start,
		before_end,
		after_start,
		after_end,
	)
	return export_candidates_to_geojson(candidates, output_path)
