#!/usr/bin/env python3
"""Sudurpashchim ARR Phase 1 primary screen (~100 m / 1 ha)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import planetary_computer as pc
import rasterio
from matplotlib.colors import ListedColormap
from pystac_client import Client
from rasterio import features
from rasterio.enums import Resampling
from rasterio.transform import from_origin, array_bounds
from rasterio.warp import reproject
from rasterio.windows import from_bounds

ROOT = Path("/workspace/arr_phase1")
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

EPSG = 32644  # UTM 44N
RES = 100.0  # meters ≈ 1 ha
TREE_COVER_THRESH = 30  # Hansen % canopy for "forest-like"
SLOPE_MAX_DEG = 35.0
LOSSYEAR_CUTOFF = 11  # loss by 2011 → clearer 10-yr non-forest vs 2021 map

# ESA WorldCover v200 class codes
WC = {
    10: "tree_cover",
    20: "shrubland",
    30: "grassland",
    40: "cropland",
    50: "built_up",
    60: "bare_sparse",
    70: "snow_ice",
    80: "water",
    90: "wetland",
    95: "mangroves",
    100: "moss_lichen",
}

DISTRICT_ALIASES = {
    "Baijura": "Bajura",
    "Dadeidhura": "Dadeldhura",
}

EXPECTED_DISTRICTS = [
    "Achham",
    "Baitadi",
    "Bajhang",
    "Bajura",
    "Dadeldhura",
    "Darchula",
    "Doti",
    "Kailali",
    "Kanchanpur",
]

WORLDCOVER_TILES = [
    "https://esa-worldcover.s3.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E078_Map.tif",
    "https://esa-worldcover.s3.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E081_Map.tif",
    "https://esa-worldcover.s3.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N30E078_Map.tif",
    "https://esa-worldcover.s3.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N30E081_Map.tif",
]

HANSEN_TC = [
    "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_treecover2000_30N_080E.tif",
    "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_treecover2000_40N_080E.tif",
]
HANSEN_LOSS = [
    "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_lossyear_30N_080E.tif",
    "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_lossyear_40N_080E.tif",
]


def load_admin():
    adm1 = gpd.read_file(DATA / "NPL_ADM1.geojson")
    adm2 = gpd.read_file(DATA / "NPL_ADM2.geojson")
    prov = adm1[adm1["shapeName"] == "Sudurpaschim"].copy()
    if prov.empty:
        raise RuntimeError("Sudurpaschim not found in ADM1")
    prov_utm = prov.to_crs(EPSG)
    adm2_utm = adm2.to_crs(EPSG)
    cents = adm2_utm.copy()
    cents["geometry"] = cents.representative_point()
    inside = gpd.sjoin(cents, prov_utm[["geometry"]], predicate="within", how="inner")
    districts = adm2_utm.loc[inside.index].copy()
    districts["district"] = districts["shapeName"].replace(DISTRICT_ALIASES)
    # Keep only expected nine; drop edge spills if any
    districts = districts[districts["district"].isin(EXPECTED_DISTRICTS)].copy()
    missing = set(EXPECTED_DISTRICTS) - set(districts["district"])
    if missing:
        raise RuntimeError(f"Missing districts: {missing}")
    districts = districts.dissolve(by="district", as_index=False)
    districts["district_id"] = np.arange(1, len(districts) + 1, dtype=np.uint8)
    return prov_utm, districts


def grid_from_geom(geom, res=RES):
    minx, miny, maxx, maxy = geom.total_bounds
    # pad one cell
    minx = math.floor(minx / res) * res - res
    miny = math.floor(miny / res) * res - res
    maxx = math.ceil(maxx / res) * res + res
    maxy = math.ceil(maxy / res) * res + res
    width = int(round((maxx - minx) / res))
    height = int(round((maxy - miny) / res))
    transform = from_origin(minx, maxy, res, res)
    return transform, width, height


def mosaic_to_grid(urls, transform, width, height, dst_crs, resampling, dtype, nodata, band=1):
    """Warp multiple COGs into one destination array (first-valid wins)."""
    dst = np.full((height, width), nodata, dtype=dtype)
    west, south, east, north = array_bounds(height, width, transform)
    for url in urls:
        path = url if url.startswith("/vsicurl/") else f"/vsicurl/{url}"
        with rasterio.open(path) as src:
            src_crs = src.crs
            # read only intersecting window in source CRS (approx via WGS84 bounds)
            # Convert dst bounds to WGS84 for windowing
            from pyproj import Transformer

            tf = Transformer.from_crs(dst_crs, "EPSG:4326", always_xy=True)
            # sample corners
            xs = [west, east, west, east]
            ys = [south, south, north, north]
            lons, lats = tf.transform(xs, ys)
            w, s, e, n = min(lons), min(lats), max(lons), max(lats)
            # expand slightly
            pad = 0.02
            w, s, e, n = w - pad, s - pad, e + pad, n + pad
            try:
                win = from_bounds(w, s, e, n, transform=src.transform)
            except Exception:
                continue
            win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            if win.width <= 0 or win.height <= 0:
                continue
            data = src.read(band, window=win, boundless=False)
            win_transform = src.window_transform(win)
            tmp = np.full((height, width), nodata, dtype=dtype)
            reproject(
                source=data.astype(dtype, copy=False),
                destination=tmp,
                src_transform=win_transform,
                src_crs=src_crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=resampling,
                src_nodata=getattr(src, "nodata", None),
                dst_nodata=nodata,
            )
            mask = dst == nodata
            valid = tmp != nodata
            dst[mask & valid] = tmp[mask & valid]
    return dst


def dem_urls(bbox_wgs84):
    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace,
    )
    items = list(
        catalog.search(collections=["cop-dem-glo-30"], bbox=list(bbox_wgs84), max_items=50).items()
    )
    urls = []
    for it in items:
        href = it.assets["data"].href
        urls.append(href)
    if not urls:
        raise RuntimeError("No DEM tiles found")
    return urls


def slope_deg(elev, res=RES):
    """Horn-like slope from elevation meters; nodata=-9999."""
    z = elev.astype(np.float64)
    nod = z <= -1000
    z = np.where(nod, np.nan, z)
    dzdx, dzdy = np.gradient(z, res, res)
    slope = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))
    slope = np.where(np.isnan(slope), -9999, slope).astype(np.float32)
    return slope


def rasterize_districts(districts, transform, shape, province_mask):
    shapes = (
        (geom, int(did))
        for geom, did in zip(districts.geometry, districts["district_id"])
    )
    dist = features.rasterize(
        shapes=shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype=np.uint8,
        all_touched=False,
    )
    # Fill province cells missed by ADM1/ADM2 topology mismatch with nearest district.
    missing = province_mask & (dist == 0)
    if missing.any():
        from rasterio.transform import xy as transform_xy

        # Candidate centers for each district
        centers = []
        for _, row in districts.iterrows():
            c = row.geometry.representative_point()
            centers.append((int(row["district_id"]), float(c.x), float(c.y)))
        ys, xs = np.where(missing)
        # Batch assign by nearest center in projected meters
        for y, x in zip(ys, xs):
            px, py = transform_xy(transform, y, x, offset="center")
            best_id = centers[0][0]
            best_d = 1e30
            for did, cx, cy in centers:
                d = (px - cx) ** 2 + (py - cy) ** 2
                if d < best_d:
                    best_d = d
                    best_id = did
            dist[y, x] = best_id
    return dist


def score_cells(lc, tc2000, lossyear, slope, province_mask):
    """Return dict of uint8 layers + string category codes."""
    h, w = lc.shape
    land_class = np.zeros((h, w), dtype=np.uint8)
    # map WC codes to compact 1..11
    code_to_id = {k: i + 1 for i, k in enumerate(sorted(WC.keys()))}
    id_to_name = {i + 1: WC[k] for i, k in enumerate(sorted(WC.keys()))}
    for code, cid in code_to_id.items():
        land_class[lc == code] = cid

    # Forest-like in ~2011 (10y before 2021 WorldCover vintage)
    forest_2011 = (tc2000 >= TREE_COVER_THRESH) & (
        (lossyear == 0) | (lossyear > LOSSYEAR_CUTOFF)
    )
    clear_10yr_nonforest = ~forest_2011

    plantable_bio = np.isin(lc, [20, 30, 60])  # shrub, grass, bare
    cropland = lc == 40
    existing_forest = lc == 10
    excluded = np.isin(lc, [50, 70, 80, 90, 95, 100]) | (lc == 0)
    slope_ok = (slope >= 0) & (slope <= SLOPE_MAX_DEG)

    # Feasibility class:
    # 0 outside / nodata
    # 1 excluded hard
    # 2 existing forest (not ARR plant; possible ANR later)
    # 3 cropland review
    # 4 biophysical candidate but forest-history fail
    # 5 biophysical candidate history OK (high)
    # 6 wetland/alpine soft exclude already in 1
    feas = np.zeros((h, w), dtype=np.uint8)
    feas[province_mask & excluded] = 1
    feas[province_mask & existing_forest] = 2
    feas[province_mask & cropland] = 3
    feas[province_mask & plantable_bio & ~clear_10yr_nonforest] = 4
    feas[province_mask & plantable_bio & clear_10yr_nonforest] = 5
    # steep plantable → downgrade to review/exclude for planting practicality
    steep = province_mask & plantable_bio & ~slope_ok
    feas[steep & (feas == 5)] = 4
    feas[steep & (feas == 4)] = 4

    # Multi-standard bitflags in one byte:
    # bit0 biophysical_arr
    # bit1 verra_vm0047_screen
    # bit2 gold_standard_screen (excludes cropland)
    # bit3 cropland_category_keep
    # bit4 existing_forest_anr_watch
    tags = np.zeros((h, w), dtype=np.uint8)
    tags[province_mask & plantable_bio] |= 1 << 0
    tags[province_mask & plantable_bio & clear_10yr_nonforest & slope_ok] |= 1 << 1
    tags[province_mask & plantable_bio & clear_10yr_nonforest & slope_ok] |= 1 << 2
    tags[province_mask & cropland] |= 1 << 3
    # Gold Standard-like: also allow cropland only as separate flag, not pass
    tags[province_mask & existing_forest] |= 1 << 4
    # Verra v1.1 can consider degraded forest ANR — we only flag existing forest for Phase2
    # Optional: Verra pass on cropland if history clear? Keep as review only (no auto pass)

    return {
        "land_class": land_class,
        "feasibility": feas,
        "std_tags": tags,
        "clear_10yr": clear_10yr_nonforest.astype(np.uint8),
        "id_to_name": id_to_name,
    }


def cell_area_ha():
    return (RES * RES) / 10000.0


def summarize(districts, district_raster, scored, province_mask, slope):
    ha = cell_area_ha()
    id_to_name = scored["id_to_name"]
    land_class = scored["land_class"]
    feas = scored["feasibility"]
    tags = scored["std_tags"]

    rows = []
    for _, drow in districts.iterrows():
        did = int(drow["district_id"])
        name = drow["district"]
        m = (district_raster == did) & province_mask
        n = int(m.sum())
        if n == 0:
            continue
        for cid, cname in id_to_name.items():
            cmask = m & (land_class == cid)
            cnt = int(cmask.sum())
            if cnt == 0:
                continue
            rows.append(
                {
                    "district": name,
                    "land_class": cname,
                    "hectares": round(cnt * ha, 2),
                    "cells": cnt,
                    "verra_vm0047_screen_ha": round(
                        int((cmask & ((tags & (1 << 1)) != 0)).sum()) * ha, 2
                    ),
                    "gold_standard_screen_ha": round(
                        int((cmask & ((tags & (1 << 2)) != 0)).sum()) * ha, 2
                    ),
                    "biophysical_arr_ha": round(
                        int((cmask & ((tags & (1 << 0)) != 0)).sum()) * ha, 2
                    ),
                }
            )
    detail = pd.DataFrame(rows)

    # District summary
    dist_rows = []
    feas_names = {
        1: "excluded_hard",
        2: "existing_forest",
        3: "cropland_review",
        4: "candidate_history_or_slope_risk",
        5: "candidate_high_priority",
    }
    for _, drow in districts.iterrows():
        did = int(drow["district_id"])
        name = drow["district"]
        m = (district_raster == did) & province_mask
        rec = {
            "district": name,
            "total_ha": round(int(m.sum()) * ha, 2),
            "verra_vm0047_screen_ha": round(int((m & ((tags & (1 << 1)) != 0)).sum()) * ha, 2),
            "gold_standard_screen_ha": round(int((m & ((tags & (1 << 2)) != 0)).sum()) * ha, 2),
            "biophysical_arr_ha": round(int((m & ((tags & (1 << 0)) != 0)).sum()) * ha, 2),
            "cropland_review_ha": round(int((m & (feas == 3)).sum()) * ha, 2),
            "existing_forest_ha": round(int((m & (feas == 2)).sum()) * ha, 2),
            "excluded_hard_ha": round(int((m & (feas == 1)).sum()) * ha, 2),
            "candidate_high_priority_ha": round(int((m & (feas == 5)).sum()) * ha, 2),
            "candidate_risk_ha": round(int((m & (feas == 4)).sum()) * ha, 2),
            "mean_slope_deg": round(float(np.nanmean(np.where(m & (slope >= 0), slope, np.nan))), 2)
            if m.any()
            else None,
        }
        dist_rows.append(rec)
    district_summary = pd.DataFrame(dist_rows).sort_values("district")

    # Province totals
    m = province_mask
    province = {
        "province": "Sudurpashchim",
        "total_ha": round(int(m.sum()) * ha, 2),
        "verra_vm0047_screen_ha": round(int((m & ((tags & (1 << 1)) != 0)).sum()) * ha, 2),
        "gold_standard_screen_ha": round(int((m & ((tags & (1 << 2)) != 0)).sum()) * ha, 2),
        "biophysical_arr_ha": round(int((m & ((tags & (1 << 0)) != 0)).sum()) * ha, 2),
        "cropland_review_ha": round(int((m & (feas == 3)).sum()) * ha, 2),
        "existing_forest_ha": round(int((m & (feas == 2)).sum()) * ha, 2),
        "excluded_hard_ha": round(int((m & (feas == 1)).sum()) * ha, 2),
        "candidate_high_priority_ha": round(int((m & (feas == 5)).sum()) * ha, 2),
        "candidate_risk_ha": round(int((m & (feas == 4)).sum()) * ha, 2),
        "cell_resolution_m": RES,
        "hectares_per_cell": ha,
    }

    # Land class province rollup
    lc_rows = []
    for cid, cname in id_to_name.items():
        cmask = m & (land_class == cid)
        cnt = int(cmask.sum())
        if not cnt:
            continue
        lc_rows.append(
            {
                "land_class": cname,
                "hectares": round(cnt * ha, 2),
                "pct_of_province": round(100.0 * cnt / max(int(m.sum()), 1), 2),
            }
        )
    landclass_summary = pd.DataFrame(lc_rows).sort_values("hectares", ascending=False)
    return detail, district_summary, landclass_summary, province, feas_names


def write_geotiff(path, arrays, transform, crs, descriptions):
    count = len(arrays)
    profile = {
        "driver": "GTiff",
        "height": arrays[0].shape[0],
        "width": arrays[0].shape[1],
        "count": count,
        "dtype": arrays[0].dtype,
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    # upcast if mixed
    dtypes = {a.dtype for a in arrays}
    if len(dtypes) > 1:
        # write separately as uint8 stack where possible
        pass
    with rasterio.open(path, "w", **profile) as dst:
        for i, (arr, desc) in enumerate(zip(arrays, descriptions), start=1):
            dst.write(arr.astype(profile["dtype"]), i)
            dst.set_band_description(i, desc)


def make_overview_map(feas, transform, province_gdf, districts, path):
    fig, ax = plt.subplots(figsize=(10, 12))
    # show feasibility
    cmap = ListedColormap(
        [
            "#f5f5f5",  # 0
            "#9e9e9e",  # 1 excluded
            "#1b5e20",  # 2 forest
            "#f9a825",  # 3 cropland
            "#ef6c00",  # 4 risk candidate
            "#2e7d32",  # 5 high priority
        ]
    )
    west, south, east, north = array_bounds(feas.shape[0], feas.shape[1], transform)
    ax.imshow(
        feas,
        origin="upper",
        extent=(west, east, south, north),
        cmap=cmap,
        vmin=0,
        vmax=5,
        interpolation="nearest",
    )
    districts.boundary.plot(ax=ax, linewidth=0.6, edgecolor="black")
    province_gdf.boundary.plot(ax=ax, linewidth=1.2, edgecolor="black")
    for _, r in districts.iterrows():
        c = r.geometry.representative_point()
        ax.text(c.x, c.y, r["district"], fontsize=7, ha="center", va="center")
    ax.set_title("Sudurpashchim ARR Phase 1 — Feasibility (100 m)")
    ax.set_xlabel("Easting (m, UTM 44N)")
    ax.set_ylabel("Northing (m, UTM 44N)")
    # legend proxies
    from matplotlib.patches import Patch

    legend = [
        Patch(color="#2e7d32", label="High-priority ARR candidate"),
        Patch(color="#ef6c00", label="Candidate w/ history or slope risk"),
        Patch(color="#f9a825", label="Cropland (review)"),
        Patch(color="#1b5e20", label="Existing forest"),
        Patch(color="#9e9e9e", label="Hard exclude"),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=8)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    print("Loading admin boundaries...")
    prov, districts = load_admin()
    districts.to_file(OUT / "districts.geojson", driver="GeoJSON")
    prov.to_file(OUT / "province.geojson", driver="GeoJSON")

    transform, width, height = grid_from_geom(prov)
    print(f"Grid {width}x{height} @ {RES}m ({width * height / 1e6:.2f}M cells)")

    print("Rasterizing province + districts...")
    province_mask = (
        features.rasterize(
            ((geom, 1) for geom in prov.geometry),
            out_shape=(height, width),
            transform=transform,
            fill=0,
            dtype=np.uint8,
        )
        == 1
    )
    district_raster = rasterize_districts(
        districts, transform, (height, width), province_mask
    )

    print("Warping ESA WorldCover 2021...")
    lc = mosaic_to_grid(
        WORLDCOVER_TILES,
        transform,
        width,
        height,
        EPSG,
        Resampling.nearest,
        np.uint8,
        0,
    )

    print("Warping Hansen tree cover 2000...")
    tc = mosaic_to_grid(
        HANSEN_TC,
        transform,
        width,
        height,
        EPSG,
        Resampling.average,
        np.float32,
        -9999,
    )
    # clamp
    tc = np.where(tc < 0, 0, tc).astype(np.float32)

    print("Warping Hansen loss year...")
    loss = mosaic_to_grid(
        HANSEN_LOSS,
        transform,
        width,
        height,
        EPSG,
        Resampling.nearest,
        np.uint8,
        255,
    )
    loss = np.where(loss == 255, 0, loss).astype(np.uint8)

    print("Warping Copernicus DEM + slope...")
    # province bounds in WGS84
    prov_wgs = prov.to_crs(4326)
    bbox = tuple(prov_wgs.total_bounds)  # minx,miny,maxx,maxy
    dem_list = dem_urls(bbox)
    elev = mosaic_to_grid(
        dem_list,
        transform,
        width,
        height,
        EPSG,
        Resampling.bilinear,
        np.float32,
        -9999,
    )
    slope = slope_deg(elev)

    print("Scoring cells...")
    scored = score_cells(lc, tc, loss, slope, province_mask)

    print("Summarizing...")
    detail, district_summary, landclass_summary, province, feas_names = summarize(
        districts, district_raster, scored, province_mask, slope
    )

    detail.to_csv(OUT / "district_landclass_hectares.csv", index=False)
    district_summary.to_csv(OUT / "district_summary.csv", index=False)
    landclass_summary.to_csv(OUT / "province_landclass_summary.csv", index=False)

    methods = {
        "phase": 1,
        "purpose": "Primary ARR carbon feasibility screen — not a credit claim",
        "province": "Sudurpashchim, Nepal",
        "reporting_grain_m": RES,
        "hectares_per_cell": cell_area_ha(),
        "crs": f"EPSG:{EPSG}",
        "datasets": {
            "land_cover": "ESA WorldCover 10m 2021 v200",
            "forest_history": "Hansen GFC v1.11 treecover2000 + lossyear",
            "elevation": "Copernicus DEM GLO-30 via Microsoft Planetary Computer",
            "admin": "geoBoundaries gbOpen NPL ADM1/ADM2",
        },
        "rules": {
            "biophysical_arr": "WorldCover shrubland(20), grassland(30), bare/sparse(60)",
            "verra_vm0047_screen": "biophysical + ~10y non-forest proxy (not forest-like in 2011) + slope<=35°",
            "gold_standard_screen": "same as Verra screen in Phase 1 (cropland excluded from pass)",
            "cropland": "categorized for review; not auto-passed",
            "existing_forest": "flagged for possible ANR under VM0047 v1.1 in Phase 2",
            "forest_like_2011": f"Hansen TC2000>={TREE_COVER_THRESH}% and (no loss or loss after year code {LOSSYEAR_CUTOFF})",
        },
        "accuracy_reliability": {
            "spatial_precision_m": RES,
            "land_cover_oa_expected_pct": "70-87 depending on product; Himalaya literature lower for shrub/grass/forest edges",
            "decision_reliability_primary_screen_pct": "70-80 for triage only",
            "district_ha_planning_band_pct": "±15-30 until Phase 2",
            "not_included": [
                "land tenure / CFUG boundaries",
                "FPIC",
                "field plots",
                "protected-area legal overlays (recommend Phase 2)",
                "VM0047 dynamic performance benchmark",
            ],
        },
        "feasibility_codes": feas_names,
        "std_tag_bits": {
            "0": "biophysical_arr",
            "1": "verra_vm0047_screen",
            "2": "gold_standard_screen",
            "3": "cropland_category",
            "4": "existing_forest_anr_watch",
        },
        "province_totals": province,
    }
    (OUT / "methods_and_totals.json").write_text(json.dumps(methods, indent=2))

    # Write multi-band categorical geotiff as separate files for dtype simplicity
    profile_base = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "crs": EPSG,
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    layers = {
        "land_class": scored["land_class"],
        "feasibility": scored["feasibility"],
        "std_tags": scored["std_tags"],
        "district_id": district_raster,
        "clear_10yr_nonforest": scored["clear_10yr"],
    }
    for name, arr in layers.items():
        with rasterio.open(
            OUT / f"{name}.tif",
            "w",
            **{**profile_base, "dtype": arr.dtype},
        ) as dst:
            dst.write(arr, 1)
            dst.set_band_description(1, name)

    with rasterio.open(
        OUT / "slope_deg.tif",
        "w",
        **{**profile_base, "dtype": "float32", "nodata": -9999},
    ) as dst:
        dst.write(slope.astype(np.float32), 1)

    print("Writing overview map...")
    make_overview_map(
        scored["feasibility"],
        transform,
        prov,
        districts,
        OUT / "feasibility_overview.png",
    )

    # compact district id legend
    districts[["district_id", "district"]].to_csv(OUT / "district_id_legend.csv", index=False)

    print("DONE")
    print(json.dumps(province, indent=2))


if __name__ == "__main__":
    main()
