# Sudurpashchim ARR Phase 1 Design

**Status:** Implemented  
**Date:** 2026-11-20 (Asia/Katmandu)

## Goal

Province-wide primary ARR carbon feasibility screen for Sudurpashchim: map + hectare tables by district and land class, with multi-standard tags. Reporting grain ~100 m / 1 ha.

## Approach

Open-data hybrid desk screen (Approach A from brainstorm):

1. Warp ESA WorldCover, Hansen GFC, and Copernicus DEM into a shared 100 m UTM 44N grid covering the province.
2. Categorize every cell (all land classes retained).
3. Score biophysical ARR, Verra VM0047-like screen, and Gold Standard-like screen.
4. Export GeoTIFF layers, CSV rollups, methods JSON, overview PNG.

## Eligibility rules (Phase 1)

- **Biophysical ARR:** shrubland, grassland, bare/sparse.
- **Verra / Gold screen:** biophysical + ~10-year non-forest proxy (not forest-like in 2011 per Hansen) + slope ≤ 35°.
- **Cropland:** categorized for review; not auto-passed.
- **Existing forest:** ANR watch for VM0047 v1.1 Phase 2.
- **Hard exclude:** built-up, water, snow/ice, wetland, mangroves, moss/lichen.

## Non-goals

Credit issuance claims, tenure, FPIC, field validation, protected-area legal clearance.
