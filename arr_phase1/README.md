# Sudurpashchim ARR Phase 1 — Primary Feasibility Screen (v1.1 accuracy)

Wall-to-wall ~100 m / 1 ha ARR carbon screening for **100% of Sudurpashchim Province**, Nepal.

## Accuracy upgrades (v1.1)

- **Boundaries:** OCHA **COD-AB Nepal v02** (HDX) — province NP07 + 9 districts nest with **0 ha gap** (replaced geoBoundaries)
- **Local levels:** 93 palika (ADM3) rollups for finer, more distinguishable units
- **Feasibility tiers:** high / medium / high-mountain / low-risk (not a single pass/fail)
- **Alpine filter:** elev ≥ 3800 m → unsuitable
- **Ensemble confidence:** ESA WorldCover 2021 × ESRI/IO LULC 2023 agreement (1–3)

## Quick results (province)

| Metric | Hectares |
| --- | ---: |
| Province total (masked grid) | 1,972,892 |
| Verra / Gold screen (high+medium+high-mtn) | **106,658** |
| High-confidence screen (ensemble agree) | **84,680** |
| Candidate high (gentle, &lt;3000 m) | 37,450 |
| Candidate medium | 54,486 |
| Candidate high-mountain (3000–3800 m) | 14,722 |
| Candidate low (history/steep risk) | 205,605 |
| Cropland review | 177,941 |
| Existing forest (ANR watch) | 1,186,155 |
| Alpine unsuitable | 279,985 |

Top districts by screen ha: **Bajhang, Bajura, Achham, Baitadi**.

Top local levels (examples): Himali, Shuklaphanta*, Saipal, Budhinanda, Apihimal, Bungal.  
\*Shuklaphanta overlaps a national park — exclude/confirm in Phase 2 protected-area overlay.

## Reproduce

```bash
pip install -r arr_phase1/requirements.txt
python3 arr_phase1/scripts/run_phase1_screen.py
```

Downloads COD-AB on first run, warps open COGs, writes outputs under `arr_phase1/outputs/`.

Committed summaries: CSVs, `methods_and_totals.json`, `feasibility_overview.png`. GeoTIFFs/admin downloads are gitignored.

## Accuracy / reliability

- Boundary nesting: **exact** (COD-AB)
- Spatial precision: **100 m**
- Decision reliability: **~75–85%** for triage when confidence = 3
- District ha planning band: **±10–25%** until Phase 2
- Still missing: tenure, FPIC, WDPA legal clearance, field plots, VM0047 dynamic benchmark
