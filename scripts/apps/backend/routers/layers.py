import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

_BACKEND_ROOT = Path(__file__).parent.parent
_WEATHER_DIR  = _BACKEND_ROOT / "data" / "weather"
_STATIC_DIR   = _BACKEND_ROOT / "static"

VALID_PERIODS = {"oct_dec_2025", "jan_mar_2026", "apr_may_2026"}
VALID_POLLUTANTS = {"pm10", "pm25"}

_PERIOD_LABELS = {
    "oct_dec_2025": "Oct–Dec 2025",
    "jan_mar_2026": "Jan–Mar 2026",
    "apr_may_2026": "Apr–May 2026",
}
_POLLUTANT_LABEL = {
    "pm10": "Modeled PM10 contribution (µg/m³)",
    "pm25": "Modeled PM2.5 contribution (µg/m³)",
}
_POLLUTANT_VMAX = {"pm10": 10.0, "pm25": 2.5}
_POLLUTANT_VMIN = {"pm10": 0.1,  "pm25": 0.025}


@router.get("/api/layers/modeled_dust")
def get_modeled_dust_layer(
    period: str = Query("oct_dec_2025"),
    pollutant: str = Query("pm10"),
):
    if period not in VALID_PERIODS:
        raise HTTPException(400, detail=f"Invalid period. Choose from {sorted(VALID_PERIODS)}")
    if pollutant not in VALID_POLLUTANTS:
        raise HTTPException(400, detail=f"Invalid pollutant. Choose from {sorted(VALID_POLLUTANTS)}")

    png_path = _STATIC_DIR / f"dust_{period}_{pollutant}.png"
    if not png_path.exists():
        raise HTTPException(404, detail="PNG not found — run scripts/build_dust_dispersion.py first")

    wind_cache = _WEATHER_DIR / f"vadodara_wind_{period}.json"
    wind = None
    if wind_cache.exists():
        with open(wind_cache) as f:
            wind = json.load(f)

    return {
        "url": f"/static/dust_{period}_{pollutant}.png",
        "bounds": [[22.25, 73.10], [22.45, 73.30]],
        "wind": wind,
        "period": period,
        "pollutant": pollutant,
        "available_periods": sorted(VALID_PERIODS),
        "legend": {
            "min_ug_m3": _POLLUTANT_VMIN[pollutant],
            "max_ug_m3": _POLLUTANT_VMAX[pollutant],
            "label": _POLLUTANT_LABEL[pollutant],
            "citation": "Gaussian plume · EPA AP-42 · Briggs urban σ",
            "scale": "log",
        },
    }


@router.get("/api/layers/available_periods")
def get_available_periods():
    return {
        p: _PERIOD_LABELS[p]
        for p in sorted(VALID_PERIODS)
    }
