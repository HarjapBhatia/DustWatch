import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from pathlib import Path

from services.weather_client import PERIODS, get_wind_summary
from services.dust_dispersion import build_dust_raster, save_geotiff, save_png_overlay

# Run from scripts/apps/backend/
SITES_PATH = Path("data/samples/vadodara_sites.geojson")

POLLUTANT_CONFIG = {
    "pm10": {"vmin": 0.1,   "vmax": 10.0},
    "pm25": {"vmin": 0.025, "vmax": 2.5},
}

print("Loading sites...")
with open(SITES_PATH) as f:
    geojson = json.load(f)

sites = []
for feature in geojson["features"]:
    props = feature["properties"]
    coords = props.get("coordinates", [None, None])
    sites.append({
        "lat": coords[0],
        "lon": coords[1],
        "areaM2": props.get("areaM2", 5000.0),
    })
print(f"  {len(sites)} sites loaded\n")

for period in PERIODS:
    print(f"=== Period: {period} ===")
    wind = get_wind_summary(period)
    print(f"  Wind: {wind['speed_m_s']:.2f} m/s @ {wind['direction_deg']:.1f}°")

    for pollutant, cfg in POLLUTANT_CONFIG.items():
        print(f"  Building {pollutant.upper()} raster...")
        raster = build_dust_raster(sites, wind, pollutant=pollutant)
        print(f"    max: {raster.max():.2f} µg/m³")

        tif_path = Path(f"data/outputs/dust_{period}_{pollutant}.tif")
        png_path = Path(f"static/dust_{period}_{pollutant}.png")

        save_geotiff(raster, tif_path)
        save_png_overlay(raster, png_path, vmin=cfg["vmin"], vmax=cfg["vmax"])

        from PIL import Image
        import numpy as np
        arr = np.array(Image.open(png_path))
        visible = (arr[..., 3] > 0).sum()
        total = arr.shape[0] * arr.shape[1]
        print(f"    PNG saved → {png_path}  ({visible:,}/{total:,} pixels visible, {visible/total*100:.1f}%)")

print("\nAll done.")
