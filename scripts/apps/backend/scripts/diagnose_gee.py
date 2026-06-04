import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import ee
from dotenv import load_dotenv
load_dotenv()

ee.Initialize(project=os.getenv('GEE_PROJECT_ID'))

AOI = ee.Geometry.Rectangle([73.10, 22.25, 73.30, 22.45])

# T1 (before) = Jan-Apr 2025, T2 (after/active) = Oct-Dec 2025
T1_START, T1_END = '2025-01-01', '2025-04-30'
T2_START, T2_END = '2025-10-01', '2025-12-31'

def s2_count(start, end, cloud=20):
    return (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(AOI)
        .filterDate(start, end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud)))

def bsi_stats(composite):
    return composite.expression(
        '((SWIR+RED)-(NIR+BLUE))/((SWIR+RED)+(NIR+BLUE))',
        {'SWIR': composite.select('B11'), 'RED': composite.select('B4'),
         'NIR':  composite.select('B8'),  'BLUE': composite.select('B2')}
    ).rename('BSI').reduceRegion(
        reducer=ee.Reducer.minMax().combine(ee.Reducer.mean(), '', True),
        geometry=AOI, scale=100, maxPixels=1e9
    )

# --- image counts at various cloud thresholds ---
print(f'=== T1 ({T1_START} → {T1_END}) ===')
for pct in [20, 50, 80]:
    col = s2_count(T1_START, T1_END, pct)
    print(f'  S2 images at <{pct}% cloud: {col.size().getInfo()}')

print(f'\n=== T2 ({T2_START} → {T2_END}) ===')
for pct in [20, 50, 80]:
    col = s2_count(T2_START, T2_END, pct)
    print(f'  S2 images at <{pct}% cloud: {col.size().getInfo()}')

# --- monthly breakdown for Oct / Nov / Dec 2025 ---
print('\n=== Monthly S2 counts (Oct/Nov/Dec 2025) ===')
for start, end in [('2025-10-01','2025-10-31'), ('2025-11-01','2025-11-30'), ('2025-12-01','2025-12-31')]:
    n = s2_count(start, end, 30).size().getInfo()
    print(f'  {start[:7]}: {n} images')

# --- BSI comparison T1 vs T2 ---
print('\n=== BSI stats T1 (before) ===')
c_t1 = s2_count(T1_START, T1_END, 50)
if c_t1.size().getInfo() > 0:
    print(bsi_stats(c_t1.median()).getInfo())
else:
    print('  No images found for T1 — try a different date range.')

print('\n=== BSI stats T2 (after / active construction) ===')
c_t2 = s2_count(T2_START, T2_END, 30)
if c_t2.size().getInfo() > 0:
    print(bsi_stats(c_t2.median()).getInfo())
else:
    print('  No images found for T2 — try a different date range.')
