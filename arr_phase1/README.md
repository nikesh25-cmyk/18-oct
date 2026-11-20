# Sudurpashchim ARR Phase 1 — Primary Feasibility Screen

Wall-to-wall ~100 m / 1 ha ARR carbon screening for **100% of Sudurpashchim Province**, Nepal.

## What this is

- **Purpose:** Primary triage for voluntary-market ARR (multi-standard tags).
- **Not:** A credit claim, PDD, or tenure/FPIC determination.
- **Grain:** 100 m cells (1 ha) in UTM Zone 44N (`EPSG:32644`).

## Quick results (province)

| Metric | Hectares |
| --- | ---: |
| Province total (masked grid) | 1,972,900 |
| High-priority ARR candidate (Verra/GS screen) | 276,698 |
| Biophysical ARR (shrub/grass/bare) | 452,170 |
| Candidate with history/slope risk | 175,472 |
| Cropland (review only) | 177,915 |
| Existing forest (ANR watch) | 1,189,561 |
| Hard exclude (built/water/snow/wetland/moss) | 153,254 |

Top districts by high-priority ha: **Bajhang (82,520), Bajura (55,566), Darchula (45,059), Achham (24,720), Baitadi (24,592)**.

## Data sources

- ESA WorldCover 10 m 2021 v200 (land cover)
- Hansen GFC v1.11 tree cover 2000 + loss year (10-year non-forest proxy)
- Copernicus DEM GLO-30 (slope)
- geoBoundaries NPL ADM1/ADM2 (province + districts)

## Reproduce

```bash
pip install geopandas rasterio shapely pyproj pandas numpy matplotlib planetary-computer pystac-client
python3 arr_phase1/scripts/run_phase1_screen.py
```

Outputs land in `arr_phase1/outputs/`.

## Accuracy / reliability

- Spatial precision: **100 m**
- Land-cover OA expected: **~70–87%** (lower on shrub/grass/forest edges in Himalaya)
- Decision reliability for triage: **~70–80%**
- District hectare planning band: **±15–30%** until Phase 2
- Missing in Phase 1: tenure, FPIC, field plots, protected-area legal overlay, VM0047 dynamic benchmark
