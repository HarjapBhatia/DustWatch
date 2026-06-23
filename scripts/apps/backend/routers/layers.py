import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query

load_dotenv()

router = APIRouter()

# Simple in-process cache so we don't hammer WAQI on every page load
_aqi_cache: dict = {"data": None, "ts": 0.0}
_AQI_TTL = 300   # seconds

_AQI_BANDS = [
    (50,  "Good",                     "#00e400"),
    (100, "Moderate",                 "#ffff00"),
    (150, "Unhealthy (Sensitive)",    "#ff7e00"),
    (200, "Unhealthy",                "#ff0000"),
    (300, "Very Unhealthy",           "#8f3f97"),
    (999, "Hazardous",                "#7e0023"),
]

def _aqi_color(aqi: int) -> tuple[str, str]:
    for limit, label, color in _AQI_BANDS:
        if aqi <= limit:
            return color, label
    return "#7e0023", "Hazardous"


@router.get("/api/layers/aqi_stations")
def get_aqi_stations():
    token = os.getenv("WAQI_TOKEN", "")
    if not token or token == "your_token_here":
        raise HTTPException(503, detail="WAQI_TOKEN not configured in .env")

    if time.time() - _aqi_cache["ts"] < _AQI_TTL and _aqi_cache["data"] is not None:
        return _aqi_cache["data"]

    url = (
        f"https://api.waqi.info/map/bounds/"
        f"?latlng=22.10,72.90,22.55,73.50&token={token}"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as exc:
        raise HTTPException(502, detail=f"WAQI request failed: {exc}")

    if raw.get("status") != "ok":
        raise HTTPException(502, detail=f"WAQI error: {raw.get('data', 'unknown')}")

    stations = []
    for s in raw.get("data", []):
        try:
            aqi_val = int(s["aqi"])
        except (ValueError, KeyError):
            continue   # skip stations reporting "-" or missing AQI
        color, band = _aqi_color(aqi_val)
        stations.append({
            "uid":     s.get("uid"),
            "lat":     float(s["lat"]),
            "lon":     float(s["lon"]),
            "aqi":     aqi_val,
            "band":    band,
            "color":   color,
            "name":    s.get("station", {}).get("name", "Unknown station"),
            "time":    s.get("station", {}).get("time", ""),
        })

    result = {"stations": stations, "count": len(stations)}
    _aqi_cache["data"] = result
    _aqi_cache["ts"]   = time.time()
    return result

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
