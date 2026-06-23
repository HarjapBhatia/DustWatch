from pathlib import Path

import numpy as np
import rasterio

_BACKEND_ROOT = Path(__file__).parent.parent

BBOX = (73.10, 22.25, 73.30, 22.45)   # lon_min, lat_min, lon_max, lat_max

# 2011 Census baseline (VMC 19-ward reorganization)
ZONES = {
    "North Zone": {
        "wards": [1, 2, 3, 7, 13],
        "population": 435_914,
        "area_km2": 45.05,
        "centroid_lat": 22.3412,
        "centroid_lon": 73.1954,
    },
    "East Zone": {
        "wards": [4, 5, 6, 14, 15],
        "population": 456_753,
        "area_km2": 36.69,
        "centroid_lat": 22.3060,
        "centroid_lon": 73.2385,
    },
    "West Zone": {
        "wards": [8, 9, 10, 11, 12],
        "population": 487_117,
        "area_km2": 81.54,
        "centroid_lat": 22.3124,
        "centroid_lon": 73.1492,
    },
    "South Zone": {
        "wards": [16, 17, 18, 19],
        "population": 362_007,
        "area_km2": 52.80,
        "centroid_lat": 22.2587,
        "centroid_lon": 73.1989,
    },
}

_m_per_deg_lat = 111320
_m_per_deg_lon = 111320 * np.cos(np.radians(22.35))


def compute_zone_exposure(
    period: str,
    pollutant: str,
    threshold: float = 0.1,
) -> dict:
    tif_path = _BACKEND_ROOT / f"data/outputs/dust_{period}_{pollutant}.tif"
    if not tif_path.exists():
        raise FileNotFoundError(f"GeoTIFF not found: {tif_path}")

    with rasterio.open(tif_path) as src:
        # Row 0 = north (lat_max), row N-1 = south (lat_min)
        raster = src.read(1).astype(np.float32)
        n_lat, n_lon = raster.shape

    pixel_h = (BBOX[3] - BBOX[1]) / n_lat   # degrees per row
    pixel_w = (BBOX[2] - BBOX[0]) / n_lon   # degrees per col

    # Cell-centre coordinates
    lats_1d = BBOX[3] - (np.arange(n_lat) + 0.5) * pixel_h   # north → south
    lons_1d = BBOX[0] + (np.arange(n_lon) + 0.5) * pixel_w   # west  → east
    LON, LAT = np.meshgrid(lons_1d, lats_1d)                  # (n_lat, n_lon)

    # Assign each cell to nearest zone centroid (Voronoi)
    zone_names = list(ZONES.keys())
    zone_idx = np.zeros((n_lat, n_lon), dtype=np.int8)
    min_dist = np.full((n_lat, n_lon), np.inf)

    for i, zone in enumerate(ZONES.values()):
        dlat = (LAT - zone["centroid_lat"]) * _m_per_deg_lat
        dlon = (LON - zone["centroid_lon"]) * _m_per_deg_lon
        dist = dlat**2 + dlon**2                        # squared distance (no sqrt needed)
        closer = dist < min_dist
        zone_idx[closer] = i
        min_dist[closer] = dist[closer]

    cell_area_km2 = (pixel_h * _m_per_deg_lat / 1000) * (pixel_w * _m_per_deg_lon / 1000)
    exposed_mask = raster > threshold

    results = []
    for i, (name, zone) in enumerate(ZONES.items()):
        in_zone = zone_idx == i
        exposed_cells = int((exposed_mask & in_zone).sum())
        exposed_area_km2 = round(exposed_cells * cell_area_km2, 3)

        pop_density = zone["population"] / zone["area_km2"]
        estimated_exposed = int(exposed_area_km2 * pop_density)
        exposure_pct = round(estimated_exposed / zone["population"] * 100, 2)

        results.append({
            "name": name,
            "wards": zone["wards"],
            "zone_population": zone["population"],
            "pop_density_per_km2": int(pop_density),
            "exposed_area_km2": exposed_area_km2,
            "estimated_exposed": estimated_exposed,
            "exposure_pct": exposure_pct,
        })

    results.sort(key=lambda r: r["estimated_exposed"], reverse=True)

    return {
        "period": period,
        "pollutant": pollutant,
        "threshold_ug_m3": threshold,
        "total_population": sum(z["population"] for z in ZONES.values()),
        "total_exposed": sum(r["estimated_exposed"] for r in results),
        "zones": results,
        "note": "2011 Census baseline · Gaussian plume model · Voronoi zone assignment",
    }
