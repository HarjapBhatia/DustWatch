import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import ee
from dotenv import load_dotenv
load_dotenv()

ee.Initialize(project=os.getenv('GEE_PROJECT_ID'))

AOI = ee.Geometry.Rectangle([73.10, 22.25, 73.30, 22.45])

# Check how many Sentinel-2 images are available
s2_before = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(AOI)
    .filterDate('2025-10-01', '2025-12-31')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

s2_after = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(AOI)
    .filterDate('2026-03-01', '2026-05-31')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

print('S2 images before period:', s2_before.size().getInfo())
print('S2 images after period:', s2_after.size().getInfo())

# Check BSI values in the after composite
composite_after = s2_after.median()
bsi_stats = composite_after.expression(
    '((SWIR+RED)-(NIR+BLUE))/((SWIR+RED)+(NIR+BLUE))',
    {
        'SWIR': composite_after.select('B11'),
        'RED':  composite_after.select('B4'),
        'NIR':  composite_after.select('B8'),
        'BLUE': composite_after.select('B2')
    }
).rename('BSI').reduceRegion(
    reducer=ee.Reducer.minMax().combine(ee.Reducer.mean(), '', True),
    geometry=AOI,
    scale=100,
    maxPixels=1e9
)

print('BSI stats in after period:', bsi_stats.getInfo())

# Check BSI values in the before composite
composite_before = s2_before.median()
bsi_before_stats = composite_before.expression(
    '((SWIR+RED)-(NIR+BLUE))/((SWIR+RED)+(NIR+BLUE))',
    {
        'SWIR': composite_before.select('B11'),
        'RED':  composite_before.select('B4'),
        'NIR':  composite_before.select('B8'),
        'BLUE': composite_before.select('B2')
    }
).rename('BSI').reduceRegion(
    reducer=ee.Reducer.minMax().combine(ee.Reducer.mean(), '', True),
    geometry=AOI,
    scale=100,
    maxPixels=1e9
)

print('BSI stats in before period:', bsi_before_stats.getInfo())
