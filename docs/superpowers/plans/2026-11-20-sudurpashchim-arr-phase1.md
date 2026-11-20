# Sudurpashchim ARR Phase 1 Primary Screen — Implementation Plan

> **For agentic workers:** Execute task-by-task. Phase 1 only (map + hectare tables).

**Goal:** Wall-to-wall primary ARR carbon feasibility screen for 100% of Sudurpashchim Province at ~100 m / 1 ha reporting grain, with all land classes categorized and multi-standard eligibility tags.

**Architecture:** Open-data desk screen. Read ESA WorldCover 2021, Hansen GFC, and Copernicus DEM COGs via HTTP; warp to a province 100 m grid in UTM 44N; rasterize districts; score cells; export GeoTIFF, CSV rollups, methods JSON, and overview map.

**Tech Stack:** Python 3, geopandas, rasterio, numpy, pandas, matplotlib, planetary-computer (DEM signing only).

## Global Constraints

- Reporting grain: ~100 m / 1 ha cells (not credit claims)
- Coverage: full Sudurpashchim ADM1
- Land: all classes retained and categorized
- Standards: Verra VM0047-like screen, Gold Standard-like screen, biophysical-only tag
- No field validation in Phase 1

---

### Task 1: Data ingest + 100 m mosaic

- [ ] Load geoBoundaries NPL ADM1/ADM2; fix district name aliases
- [ ] Warp WorldCover / Hansen / DEM to shared 100 m grid; compute slope
- [ ] Rasterize district IDs

### Task 2: Score + export

- [ ] Apply land-class + forest-history + slope rules; multi-standard tags
- [ ] Write GeoTIFF, district×class tables, summary JSON, overview PNG
- [ ] Document accuracy/reliability limits

### Task 3: Deliver

- [ ] Canvas summary for Nikesh
- [ ] Commit, push, PR
