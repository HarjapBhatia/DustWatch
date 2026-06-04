from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_bounds

BBOX = (73.10, 22.25, 73.30, 22.45)   # lon_min, lat_min, lon_max, lat_max
GRID_M = 50                             # 50 m resolution

_lat_center = 22.35
_m_per_deg_lat = 111320
_m_per_deg_lon = 111320 * np.cos(np.radians(_lat_center))

N_LON = int((BBOX[2] - BBOX[0]) * _m_per_deg_lon / GRID_M)
N_LAT = int((BBOX[3] - BBOX[1]) * _m_per_deg_lat / GRID_M)

# EPA AP-42 construction emission factors (kg PM / hectare / hour)
_EMISSION_FACTORS = {
    "pm10": 0.11,
    "pm25": 0.11 * 0.25,   # PM2.5 ≈ 25% of PM10 (AP-42 Table 13.2.2-2)
}


def emission_rate_g_s(area_m2: float, pollutant: str = "pm10") -> float:
    factor = _EMISSION_FACTORS[pollutant]
    kg_per_hour = factor * (area_m2 / 10000)
    return kg_per_hour * 1000 / 3600


def _plume_concentration(Q: float, u: float, x_down: np.ndarray, y_cross: np.ndarray) -> np.ndarray:
    x_safe = np.where(x_down > 1, x_down, np.nan)
    sigma_y = 0.16 * x_safe / np.sqrt(1 + 0.0004 * x_safe)
    sigma_z = 0.14 * x_safe / np.sqrt(1 + 0.0003 * x_safe)
    c = Q / (np.pi * u * sigma_y * sigma_z) * np.exp(-(y_cross**2) / (2 * sigma_y**2))
    return np.nan_to_num(c, nan=0.0)


def build_dust_raster(sites: list, wind: dict, pollutant: str = "pm10") -> np.ndarray:
    theta = np.radians(wind["direction_deg"])
    u = max(wind["speed_m_s"], 1.0)

    xs = (np.arange(N_LON) + 0.5) * GRID_M
    ys = (np.arange(N_LAT) + 0.5) * GRID_M
    gx, gy = np.meshgrid(xs, ys)

    total = np.zeros_like(gx)

    for site in sites:
        lon = site.get("lon") or site.get("coordinates", [None, None])[1]
        lat = site.get("lat") or site.get("coordinates", [None, None])[0]
        area = site.get("area_m2") or site.get("areaM2", 5000.0)
        if lon is None or lat is None:
            continue

        cx = (lon - BBOX[0]) * _m_per_deg_lon
        cy = (lat - BBOX[1]) * _m_per_deg_lat
        dx = gx - cx
        dy = gy - cy
        x_down  =  dx * np.sin(theta) + dy * np.cos(theta)
        y_cross = -dx * np.cos(theta) + dy * np.sin(theta)
        Q = emission_rate_g_s(float(area), pollutant)
        total += _plume_concentration(Q, u, x_down, y_cross)

    return total * 1e6   # g/m³ → µg/m³


def save_geotiff(raster: np.ndarray, path: str | Path) -> None:
    transform = from_bounds(*BBOX, N_LON, N_LAT)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff",
        height=N_LAT, width=N_LON, count=1,
        dtype="float32", crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(np.flipud(raster).astype("float32"), 1)


def save_png_overlay(raster: np.ndarray, path: str | Path,
                     vmin: float = 0.1, vmax: float = 10.0) -> None:
    """Log-scale viridis PNG with transparency below vmin."""
    import matplotlib.cm as cm
    from PIL import Image

    # Log normalization: maps [vmin, vmax] → [0, 1] logarithmically
    # so near-field (high) and far-field (low) cells both get meaningful color
    log_raster = np.log10(np.clip(raster, vmin, vmax * 10))
    log_min = np.log10(vmin)
    log_max = np.log10(vmax)
    norm = np.clip((log_raster - log_min) / (log_max - log_min), 0, 1)

    rgba = (cm.viridis(norm) * 255).astype(np.uint8)

    # Alpha: transparent below vmin, otherwise proportional (min 30 so far-field is visible)
    alpha = np.where(
        raster < vmin, 0,
        np.clip(norm * 200 + 30, 30, 220)
    ).astype(np.uint8)
    rgba[..., 3] = alpha

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.flipud(rgba)).save(path)
