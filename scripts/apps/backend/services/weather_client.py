import json
from pathlib import Path

import numpy as np
import requests

CACHE_DIR = Path(__file__).parent.parent / "data" / "weather"

PERIODS = {
    "oct_dec_2025": ("2025-10-01", "2025-12-31"),
    "jan_mar_2026": ("2026-01-01", "2026-03-31"),
    "apr_may_2026": ("2026-04-01", "2026-05-31"),
}

_BASE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=22.31&longitude=73.18"
    "&hourly=wind_speed_10m,wind_direction_10m"
    "&start_date={start}&end_date={end}"
)


def _summarize_wind(speeds: list, directions_deg: list) -> dict:
    s = np.array(speeds, dtype=float)
    d = np.radians(np.array(directions_deg, dtype=float))
    u = -s * np.sin(d)
    v = -s * np.cos(d)
    u_mean, v_mean = np.nanmean(u), np.nanmean(v)
    speed_mean = float(np.sqrt(u_mean**2 + v_mean**2))
    dir_mean_deg = float((np.degrees(np.arctan2(-u_mean, -v_mean)) + 360) % 360)
    return {"speed_m_s": speed_mean, "direction_deg": dir_mean_deg}


def get_wind_summary(period: str = "oct_dec_2025") -> dict:
    if period not in PERIODS:
        raise ValueError(f"Unknown period '{period}'. Valid: {list(PERIODS)}")

    cache_path = CACHE_DIR / f"vadodara_wind_{period}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    start, end = PERIODS[period]
    url = _BASE_URL.format(start=start, end=end)
    print(f"  Fetching wind data for {period} ({start} → {end})...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    hourly = resp.json()["hourly"]

    summary = _summarize_wind(hourly["wind_speed_10m"], hourly["wind_direction_10m"])

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Cached: {summary['speed_m_s']:.2f} m/s @ {summary['direction_deg']:.1f}°")
    return summary
