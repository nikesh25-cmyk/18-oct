# Sudurpashchim ARR Phase 1 Design

**Status:** Implemented (v1.1 accuracy)  
**Date:** 2026-11-20 (Asia/Katmandu)

## Goal

Province-wide primary ARR carbon feasibility screen for Sudurpashchim: map + hectare tables by district and land class, with multi-standard tags. Reporting grain ~100 m / 1 ha.

## Approach

Open-data hybrid desk screen (Approach A from brainstorm), accuracy upgrade:

1. Use **OCHA COD-AB** province/district/local boundaries (exact nesting).
2. Warp ESA WorldCover + ESRI/IO LULC ensemble, Hansen GFC, and Copernicus DEM into a shared 100 m UTM 44N grid.
3. Score distinguishable feasibility tiers (high / medium / high-mountain / low) plus alpine filter.
4. Export GeoTIFF layers, district + palika CSV rollups, methods JSON, overview PNG.

## Eligibility rules (Phase 1 v1.1)

- **Biophysical ARR:** shrubland, grassland, bare/sparse below 3800 m.
- **High:** biophysical + 10y non-forest + slope &lt;15° + elev &lt;3000 m.
- **Medium:** biophysical + 10y non-forest + slope 15–25° + elev &lt;3000 m.
- **High-mountain:** biophysical + 10y non-forest + elev 3000–3800 m + slope ≤25°.
- **Verra / Gold screen:** high + medium + high-mountain.
- **Cropland:** categorized for review; not auto-passed.
- **Existing forest:** ANR watch for VM0047 v1.1 Phase 2.
- **Alpine unsuitable:** snow/ice/moss or elev ≥3800 m.
- **Hard exclude:** built-up, water, wetland, mangroves.

## Non-goals

Credit issuance claims, tenure, FPIC, field validation, WDPA legal clearance (flagged for Phase 2).
