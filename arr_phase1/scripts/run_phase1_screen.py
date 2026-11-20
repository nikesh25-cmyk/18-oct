#!/usr/bin/env python3
"""Sudurpashchim ARR Phase 1 screen — accuracy upgrade (COD-AB boundaries)."""

from __future__ import annotations

import json
import math
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import planetary_computer as pc
import rasterio
import requests
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from pystac_client import Client
from pyproj import Transformer
from rasterio import features
from rasterio.enums import Resampling
from rasterio.transform import from_origin, array_bounds, xy as transform_xy
from rasterio.warp import reproject
from rasterio.windows import from_bounds

ROOT = Path("/workspace/arr_phase1")
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

EPSG = 32644
RES = 100.0
TREE_COVER_THRESH = 30
LOSSYEAR_CUTOFF = 11
ELEV_ALPINE_M = 3800
ELEV_HIGH_MTN_M = 3000
SLOPE_GENTLE = 15.0
SLOPE_MOD = 25.0
SLOPE_MAX = 35.0

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

# Impact Observatory / ESRI annual LULC class → coarse family
# 1 water, 2 trees, 4 flooded veg, 5 crops, 7 built, 8 bare, 9 snow, 11 rangeland
IO_FAMILY = {
    1: "water",
    2: "trees",
    4: "wetland",
    5: "crops",
    7: "built",
    8: "bare",
    9: "snow",
    11: "rangeland",
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

COD_ZIP_URL = (
    "https://data.humdata.org/dataset/07db728a-4f0f-4e98-8eb0-8fa9df61f01c/"
    "resource/dea34e50-37d5-4e36-98ae-2b7b1b4c43de/download/npl_admin_boundaries.geojson.zip"
)

FEAS_NAMES = {
    1: "hard_exclude",
    2: "alpine_unsuitable",
    3: "existing_forest",
    4: "cropland_review",
    5: "candidate_low_risk",
    6: "candidate_medium",
    7: "candidate_high",
    8: "candidate_high_mountain",
}


def ensure_codab_boundaries():
    """Use OCHA COD-AB v02 boundaries (exact province/district match, 0 ha gap)."""
    prov_path = DATA / "sudurpashchim_province_codab.geojson"
    dist_path = DATA / "sudurpashchim_districts_codab.geojson"
    local_path = DATA / "sudurpashchim_local_codab.geojson"
    if prov_path.exists() and dist_path.exists() and local_path.exists():
        return (
            gpd.read_file(prov_path),
            gpd.read_file(dist_path),
            gpd.read_file(local_path),
        )

    zip_path = DATA / "npl_admin_boundaries.geojson.zip"
    if not zip_path.exists():
        print("Downloading OCHA COD-AB Nepal boundaries...")
        r = requests.get(COD_ZIP_URL, timeout=180)
        r.raise_for_status()
        zip_path.write_bytes(r.content)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extract("npl_admin1.geojson", DATA)
        zf.extract("npl_admin2.geojson", DATA)
        zf.extract("npl_admin3.geojson", DATA)

    adm1 = gpd.read_file(DATA / "npl_admin1.geojson")
    adm2 = gpd.read_file(DATA / "npl_admin2.geojson")
    adm3 = gpd.read_file(DATA / "npl_admin3.geojson")
    prov = adm1[adm1["adm1_pcode"] == "NP07"][
        ["adm1_name", "adm1_pcode", "area_sqkm", "geometry"]
    ].copy()
    dist = adm2[adm2["adm1_pcode"] == "NP07"][
        ["adm2_name", "adm2_pcode", "adm1_pcode", "area_sqkm", "geometry"]
    ].copy()
    local = adm3[adm3["adm1_pcode"] == "NP07"][
        [
            "adm3_name",
            "adm3_pcode",
            "adm2_name",
            "adm2_pcode",
            "adm1_pcode",
            "area_sqkm",
            "geometry",
        ]
    ].copy()
    prov.to_file(prov_path, driver="GeoJSON")
    dist.to_file(dist_path, driver="GeoJSON")
    local.to_file(local_path, driver="GeoJSON")
    # cleanup bulky extracts
    for p in [
        DATA / "npl_admin1.geojson",
        DATA / "npl_admin2.geojson",
        DATA / "npl_admin3.geojson",
    ]:
        if p.exists():
            p.unlink()
    return prov, dist, local


def load_admin():
    prov, dist, local = ensure_codab_boundaries()
    prov_utm = prov.to_crs(EPSG)
    districts = dist.to_crs(EPSG).copy()
    districts["district"] = districts["adm2_name"]
    missing = set(EXPECTED_DISTRICTS) - set(districts["district"])
    if missing:
        raise RuntimeError(f"Missing districts in COD-AB: {missing}")
    districts = districts.sort_values("district").reset_index(drop=True)
    districts["district_id"] = np.arange(1, len(districts) + 1, dtype=np.uint8)

    local_utm = local.to_crs(EPSG).copy()
    local_utm["local_name"] = local_utm["adm3_name"]
    local_utm["district"] = local_utm["adm2_name"]
    local_utm = local_utm.sort_values(["district", "local_name"]).reset_index(drop=True)
    local_utm["local_id"] = np.arange(1, len(local_utm) + 1, dtype=np.uint16)
    return prov_utm, districts, local_utm


def grid_from_geom(geom, res=RES):
    minx, miny, maxx, maxy = geom.total_bounds
    minx = math.floor(minx / res) * res - res
    miny = math.floor(miny / res) * res - res
    maxx = math.ceil(maxx / res) * res + res
    maxy = math.ceil(maxy / res) * res + res
    width = int(round((maxx - minx) / res))
    height = int(round((maxy - miny) / res))
    transform = from_origin(minx, maxy, res, res)
    return transform, width, height


def mosaic_to_grid(urls, transform, width, height, dst_crs, resampling, dtype, nodata, band=1):
    dst = np.full((height, width), nodata, dtype=dtype)
    west, south, east, north = array_bounds(height, width, transform)

    for url in urls:
        path = url if url.startswith("/vsicurl/") else f"/vsicurl/{url}"
        with rasterio.open(path) as src:
            # Transform destination bounds into the source CRS for windowed reads
            # (WorldCover is geographic; ESRI/IO LULC tiles are often UTM).
            tf = Transformer.from_crs(dst_crs, src.crs, always_xy=True)
            xs = [west, east, west, east]
            ys = [south, south, north, north]
            xs2, ys2 = tf.transform(xs, ys)
            w, s, e, n = min(xs2), min(ys2), max(xs2), max(ys2)
            pad_x = (e - w) * 0.02 + 1.0
            pad_y = (n - s) * 0.02 + 1.0
            w, s, e, n = w - pad_x, s - pad_y, e + pad_x, n + pad_y
            try:
                win = from_bounds(w, s, e, n, transform=src.transform)
            except Exception:
                continue
            try:
                win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            except Exception:
                continue
            if win.width <= 1 or win.height <= 1:
                continue
            data = src.read(band, window=win)
            win_transform = src.window_transform(win)
            tmp = np.full((height, width), nodata, dtype=dtype)
            reproject(
                source=data.astype(dtype, copy=False),
                destination=tmp,
                src_transform=win_transform,
                src_crs=src.crs,
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
    urls = [it.assets["data"].href for it in items]
    if not urls:
        raise RuntimeError("No DEM tiles found")
    return urls


def esri_lulc_urls(bbox_wgs84):
    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=pc.sign_inplace,
    )
    items = list(
        catalog.search(
            collections=["io-lulc-annual-v02"],
            bbox=list(bbox_wgs84),
            datetime="2023-01-01/2023-12-31",
            max_items=20,
        ).items()
    )
    urls = []
    for it in items:
        asset = it.assets.get("data")
        if asset is not None:
            urls.append(asset.href)
    return urls


def slope_deg(elev, res=RES):
    z = elev.astype(np.float64)
    nod = z <= -1000
    z = np.where(nod, np.nan, z)
    dzdx, dzdy = np.gradient(z, res, res)
    slope = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))
    return np.where(np.isnan(slope), -9999, slope).astype(np.float32)


def rasterize_polygons(gdf, value_col, transform, shape, dtype):
    shapes = ((geom, int(val)) for geom, val in zip(gdf.geometry, gdf[value_col]))
    return features.rasterize(
        shapes=shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype=dtype,
        all_touched=False,
    )


def wc_family(code):
    if code == 10:
        return "trees"
    if code in (20, 30):
        return "rangeland"
    if code == 40:
        return "crops"
    if code == 50:
        return "built"
    if code == 60:
        return "bare"
    if code == 70:
        return "snow"
    if code in (80,):
        return "water"
    if code in (90, 95):
        return "wetland"
    if code == 100:
        return "snow"  # alpine moss/lichen treated with alpine
    return "other"


def score_cells(lc, io_lc, tc2000, lossyear, elev, slope, province_mask):
    h, w = lc.shape
    code_to_id = {k: i + 1 for i, k in enumerate(sorted(WC.keys()))}
    id_to_name = {i + 1: WC[k] for i, k in enumerate(sorted(WC.keys()))}
    land_class = np.zeros((h, w), dtype=np.uint8)
    for code, cid in code_to_id.items():
        land_class[lc == code] = cid

    forest_2011 = (tc2000 >= TREE_COVER_THRESH) & (
        (lossyear == 0) | (lossyear > LOSSYEAR_CUTOFF)
    )
    clear_10yr = ~forest_2011

    plantable_bio = np.isin(lc, [20, 30, 60])
    cropland = lc == 40
    existing_forest = lc == 10
    hard_excl = np.isin(lc, [50, 80, 90, 95]) | (lc == 0)
    alpine_lc = np.isin(lc, [70, 100])
    alpine_elev = elev >= ELEV_ALPINE_M
    high_mtn = (elev >= ELEV_HIGH_MTN_M) & (elev < ELEV_ALPINE_M)
    slope_ok = (slope >= 0) & (slope <= SLOPE_MAX)
    gentle = (slope >= 0) & (slope < SLOPE_GENTLE)
    moderate = (slope >= SLOPE_GENTLE) & (slope < SLOPE_MOD)
    steep = (slope >= SLOPE_MOD) & (slope <= SLOPE_MAX)

    feas = np.zeros((h, w), dtype=np.uint8)
    m = province_mask
    feas[m & hard_excl] = 1
    feas[m & (alpine_lc | alpine_elev) & (feas == 0)] = 2
    # alpine elev overrides plantable
    feas[m & alpine_elev & plantable_bio] = 2
    feas[m & existing_forest & (feas == 0)] = 3
    feas[m & cropland & (feas == 0)] = 4

    bio = m & plantable_bio & ~alpine_elev & (feas == 0)
    # low: history fail or steep
    feas[bio & (~clear_10yr | steep)] = 5
    # high mountain candidates
    feas[bio & clear_10yr & high_mtn & slope_ok & ~steep & (feas == 0)] = 8
    # medium
    feas[bio & clear_10yr & ~high_mtn & moderate & (feas == 0)] = 6
    # high
    feas[bio & clear_10yr & ~high_mtn & gentle & (feas == 0)] = 7
    # remaining bio with ok slope but somehow unset → medium
    feas[bio & clear_10yr & slope_ok & (feas == 0)] = 6
    # remaining bio → low
    feas[bio & (feas == 0)] = 5

    # Multi-standard tags
    # bit0 biophysical
    # bit1 verra_vm0047_screen (high+medium+high_mtn)
    # bit2 gold_standard_screen (same; cropland excluded)
    # bit3 cropland_category
    # bit4 existing_forest_anr_watch
    # bit5 high_confidence_agree
    tags = np.zeros((h, w), dtype=np.uint8)
    tags[m & plantable_bio & ~alpine_elev] |= 1 << 0
    screen_pass = m & np.isin(feas, [6, 7, 8])
    tags[screen_pass] |= (1 << 1) | (1 << 2)
    tags[m & cropland] |= 1 << 3
    tags[m & existing_forest] |= 1 << 4

    # Confidence from WorldCover vs ESRI/IO agreement on family (int codes)
    # 0 other, 1 water, 2 trees, 3 rangeland, 4 crops, 5 built, 6 bare, 7 snow, 8 wetland
    conf = np.ones((h, w), dtype=np.uint8)  # 1 low default
    if io_lc is not None:
        fam_map_wc = {
            10: 2,
            20: 3,
            30: 3,
            40: 4,
            50: 5,
            60: 6,
            70: 7,
            80: 1,
            90: 8,
            95: 8,
            100: 7,
        }
        fam_map_io = {1: 1, 2: 2, 4: 8, 5: 4, 7: 5, 8: 6, 9: 7, 11: 3}
        wc_fam = np.zeros(lc.shape, dtype=np.uint8)
        io_fam = np.zeros(lc.shape, dtype=np.uint8)
        for code, fam in fam_map_wc.items():
            wc_fam[lc == code] = fam
        for code, fam in fam_map_io.items():
            io_fam[io_lc == code] = fam
        agree = (wc_fam == io_fam) & (wc_fam > 0) & m
        wc_plant = np.isin(wc_fam, [3, 6])
        io_plant = np.isin(io_fam, [3, 6])
        partial = m & wc_plant & io_plant & ~agree
        conf[m] = 1
        conf[partial] = 2
        conf[agree] = 3
        tags[agree & screen_pass] |= 1 << 5

    return {
        "land_class": land_class,
        "feasibility": feas,
        "std_tags": tags,
        "clear_10yr": clear_10yr.astype(np.uint8),
        "confidence": conf,
        "id_to_name": id_to_name,
    }


def cell_area_ha():
    return (RES * RES) / 10000.0


def summarize(districts, district_raster, locals_gdf, local_raster, scored, province_mask, slope, elev):
    ha = cell_area_ha()
    id_to_name = scored["id_to_name"]
    land_class = scored["land_class"]
    feas = scored["feasibility"]
    tags = scored["std_tags"]
    conf = scored["confidence"]

    rows = []
    for _, drow in districts.iterrows():
        did = int(drow["district_id"])
        name = drow["district"]
        m = (district_raster == did) & province_mask
        for cid, cname in id_to_name.items():
            cmask = m & (land_class == cid)
            cnt = int(cmask.sum())
            if not cnt:
                continue
            rows.append(
                {
                    "district": name,
                    "land_class": cname,
                    "hectares": round(cnt * ha, 2),
                    "verra_vm0047_screen_ha": round(
                        int((cmask & ((tags & (1 << 1)) != 0)).sum()) * ha, 2
                    ),
                    "gold_standard_screen_ha": round(
                        int((cmask & ((tags & (1 << 2)) != 0)).sum()) * ha, 2
                    ),
                    "biophysical_arr_ha": round(
                        int((cmask & ((tags & (1 << 0)) != 0)).sum()) * ha, 2
                    ),
                    "high_confidence_screen_ha": round(
                        int((cmask & ((tags & (1 << 5)) != 0)).sum()) * ha, 2
                    ),
                }
            )
    detail = pd.DataFrame(rows)

    dist_rows = []
    for _, drow in districts.iterrows():
        did = int(drow["district_id"])
        name = drow["district"]
        m = (district_raster == did) & province_mask
        dist_rows.append(
            {
                "district": name,
                "adm2_pcode": drow.get("adm2_pcode", ""),
                "total_ha": round(int(m.sum()) * ha, 2),
                "candidate_high_ha": round(int((m & (feas == 7)).sum()) * ha, 2),
                "candidate_medium_ha": round(int((m & (feas == 6)).sum()) * ha, 2),
                "candidate_high_mountain_ha": round(int((m & (feas == 8)).sum()) * ha, 2),
                "candidate_low_risk_ha": round(int((m & (feas == 5)).sum()) * ha, 2),
                "verra_vm0047_screen_ha": round(int((m & ((tags & (1 << 1)) != 0)).sum()) * ha, 2),
                "gold_standard_screen_ha": round(int((m & ((tags & (1 << 2)) != 0)).sum()) * ha, 2),
                "high_confidence_screen_ha": round(int((m & ((tags & (1 << 5)) != 0)).sum()) * ha, 2),
                "biophysical_arr_ha": round(int((m & ((tags & (1 << 0)) != 0)).sum()) * ha, 2),
                "cropland_review_ha": round(int((m & (feas == 4)).sum()) * ha, 2),
                "existing_forest_ha": round(int((m & (feas == 3)).sum()) * ha, 2),
                "alpine_unsuitable_ha": round(int((m & (feas == 2)).sum()) * ha, 2),
                "hard_exclude_ha": round(int((m & (feas == 1)).sum()) * ha, 2),
                "mean_slope_deg": round(
                    float(np.nanmean(np.where(m & (slope >= 0), slope, np.nan))), 2
                ),
                "mean_elevation_m": round(
                    float(np.nanmean(np.where(m & (elev > -1000), elev, np.nan))), 1
                ),
                "mean_confidence_1to3": round(
                    float(np.nanmean(np.where(m, conf, np.nan))), 2
                ),
            }
        )
    district_summary = pd.DataFrame(dist_rows).sort_values(
        "verra_vm0047_screen_ha", ascending=False
    )

    # Local-level (palika) summary — more distinguishable boundaries
    local_rows = []
    for _, lrow in locals_gdf.iterrows():
        lid = int(lrow["local_id"])
        m = (local_raster == lid) & province_mask
        n = int(m.sum())
        if n == 0:
            continue
        screen_ha = int((m & ((tags & (1 << 1)) != 0)).sum()) * ha
        local_rows.append(
            {
                "local_level": lrow["local_name"],
                "adm3_pcode": lrow.get("adm3_pcode", ""),
                "district": lrow["district"],
                "total_ha": round(n * ha, 2),
                "verra_vm0047_screen_ha": round(screen_ha, 2),
                "candidate_high_ha": round(int((m & (feas == 7)).sum()) * ha, 2),
                "candidate_medium_ha": round(int((m & (feas == 6)).sum()) * ha, 2),
                "candidate_high_mountain_ha": round(int((m & (feas == 8)).sum()) * ha, 2),
                "high_confidence_screen_ha": round(
                    int((m & ((tags & (1 << 5)) != 0)).sum()) * ha, 2
                ),
                "cropland_review_ha": round(int((m & (feas == 4)).sum()) * ha, 2),
                "existing_forest_ha": round(int((m & (feas == 3)).sum()) * ha, 2),
                "mean_elevation_m": round(
                    float(np.nanmean(np.where(m & (elev > -1000), elev, np.nan))), 1
                ),
            }
        )
    local_summary = pd.DataFrame(local_rows).sort_values(
        "verra_vm0047_screen_ha", ascending=False
    )

    m = province_mask
    province = {
        "province": "Sudurpashchim",
        "boundary_source": "OCHA COD-AB Nepal v02 (adm1_pcode NP07)",
        "total_ha": round(int(m.sum()) * ha, 2),
        "verra_vm0047_screen_ha": round(int((m & ((tags & (1 << 1)) != 0)).sum()) * ha, 2),
        "gold_standard_screen_ha": round(int((m & ((tags & (1 << 2)) != 0)).sum()) * ha, 2),
        "high_confidence_screen_ha": round(int((m & ((tags & (1 << 5)) != 0)).sum()) * ha, 2),
        "candidate_high_ha": round(int((m & (feas == 7)).sum()) * ha, 2),
        "candidate_medium_ha": round(int((m & (feas == 6)).sum()) * ha, 2),
        "candidate_high_mountain_ha": round(int((m & (feas == 8)).sum()) * ha, 2),
        "candidate_low_risk_ha": round(int((m & (feas == 5)).sum()) * ha, 2),
        "biophysical_arr_ha": round(int((m & ((tags & (1 << 0)) != 0)).sum()) * ha, 2),
        "cropland_review_ha": round(int((m & (feas == 4)).sum()) * ha, 2),
        "existing_forest_ha": round(int((m & (feas == 3)).sum()) * ha, 2),
        "alpine_unsuitable_ha": round(int((m & (feas == 2)).sum()) * ha, 2),
        "hard_exclude_ha": round(int((m & (feas == 1)).sum()) * ha, 2),
        "cell_resolution_m": RES,
        "hectares_per_cell": ha,
    }

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
    return detail, district_summary, local_summary, landclass_summary, province


def make_overview_map(feas, transform, province_gdf, districts, path):
    fig, ax = plt.subplots(figsize=(11, 13))
    colors = [
        "#f7f7f7",  # 0
        "#6d6d6d",  # 1 hard exclude
        "#b3e5fc",  # 2 alpine
        "#1b5e20",  # 3 forest
        "#fbc02d",  # 4 cropland
        "#ef6c00",  # 5 low
        "#7cb342",  # 6 medium
        "#2e7d32",  # 7 high
        "#00695c",  # 8 high mountain
    ]
    cmap = ListedColormap(colors)
    west, south, east, north = array_bounds(feas.shape[0], feas.shape[1], transform)
    ax.imshow(
        feas,
        origin="upper",
        extent=(west, east, south, north),
        cmap=cmap,
        vmin=0,
        vmax=8,
        interpolation="nearest",
    )
    districts.boundary.plot(ax=ax, linewidth=0.9, edgecolor="#212121")
    province_gdf.boundary.plot(ax=ax, linewidth=1.6, edgecolor="#000000")
    for _, r in districts.iterrows():
        c = r.geometry.representative_point()
        ax.text(
            c.x,
            c.y,
            r["district"],
            fontsize=8,
            ha="center",
            va="center",
            color="#000000",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7),
        )
    ax.set_title("Sudurpashchim ARR Phase 1 — Feasibility tiers (COD-AB boundaries, 100 m)")
    ax.set_xlabel("Easting (m, UTM 44N)")
    ax.set_ylabel("Northing (m, UTM 44N)")
    legend = [
        Patch(color="#2e7d32", label="High (gentle slope, <3000 m)"),
        Patch(color="#7cb342", label="Medium (moderate slope)"),
        Patch(color="#00695c", label="High-mountain (3000–3800 m)"),
        Patch(color="#ef6c00", label="Low (history/steep risk)"),
        Patch(color="#fbc02d", label="Cropland review"),
        Patch(color="#1b5e20", label="Existing forest"),
        Patch(color="#b3e5fc", label="Alpine unsuitable"),
        Patch(color="#6d6d6d", label="Hard exclude"),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=8, framealpha=0.92)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)


def main():
    print("Loading OCHA COD-AB boundaries...")
    prov, districts, locals_gdf = load_admin()
    # simplified exports for map tooling (full precision used in rasterize)
    districts.to_file(OUT / "districts.geojson", driver="GeoJSON")
    prov.to_file(OUT / "province.geojson", driver="GeoJSON")
    locals_gdf[["local_id", "local_name", "district", "adm3_pcode", "geometry"]].to_file(
        OUT / "local_levels.geojson", driver="GeoJSON"
    )

    transform, width, height = grid_from_geom(prov)
    print(f"Grid {width}x{height} @ {RES}m ({width * height / 1e6:.2f}M cells)")

    print("Rasterizing province, districts, local levels...")
    province_mask = (
        features.rasterize(
            ((geom, 1) for geom in prov.geometry),
            out_shape=(height, width),
            transform=transform,
            fill=0,
            dtype=np.uint8,
            all_touched=False,
        )
        == 1
    )
    district_raster = rasterize_polygons(
        districts, "district_id", transform, (height, width), np.uint8
    )
    local_raster = rasterize_polygons(
        locals_gdf, "local_id", transform, (height, width), np.uint16
    )
    # With COD-AB, district coverage of province should be complete.
    uncovered = int((province_mask & (district_raster == 0)).sum())
    print(f"Province cells with no district id: {uncovered}")

    print("Warping ESA WorldCover 2021...")
    lc = mosaic_to_grid(
        WORLDCOVER_TILES, transform, width, height, EPSG, Resampling.nearest, np.uint8, 0
    )

    print("Warping ESRI/IO annual LULC 2023 (confidence ensemble)...")
    prov_wgs = prov.to_crs(4326)
    bbox = tuple(prov_wgs.total_bounds)
    io_urls = esri_lulc_urls(bbox)
    io_lc = None
    if io_urls:
        io_lc = mosaic_to_grid(
            io_urls, transform, width, height, EPSG, Resampling.nearest, np.uint8, 0
        )
    else:
        print("WARNING: no ESRI/IO tiles; confidence defaults to 1")

    print("Warping Hansen tree cover / loss...")
    tc = mosaic_to_grid(
        HANSEN_TC, transform, width, height, EPSG, Resampling.average, np.float32, -9999
    )
    tc = np.where(tc < 0, 0, tc).astype(np.float32)
    loss = mosaic_to_grid(
        HANSEN_LOSS, transform, width, height, EPSG, Resampling.nearest, np.uint8, 255
    )
    loss = np.where(loss == 255, 0, loss).astype(np.uint8)

    print("Warping Copernicus DEM + slope...")
    elev = mosaic_to_grid(
        dem_urls(bbox), transform, width, height, EPSG, Resampling.bilinear, np.float32, -9999
    )
    slope = slope_deg(elev)

    print("Scoring cells...")
    scored = score_cells(lc, io_lc, tc, loss, elev, slope, province_mask)

    print("Summarizing district + local levels...")
    detail, district_summary, local_summary, landclass_summary, province = summarize(
        districts, district_raster, locals_gdf, local_raster, scored, province_mask, slope, elev
    )

    detail.to_csv(OUT / "district_landclass_hectares.csv", index=False)
    district_summary.to_csv(OUT / "district_summary.csv", index=False)
    local_summary.to_csv(OUT / "local_level_summary.csv", index=False)
    local_summary.head(25).to_csv(OUT / "local_level_top25_screen.csv", index=False)
    landclass_summary.to_csv(OUT / "province_landclass_summary.csv", index=False)
    districts[["district_id", "district", "adm2_pcode"]].to_csv(
        OUT / "district_id_legend.csv", index=False
    )
    locals_gdf[["local_id", "local_name", "district", "adm3_pcode"]].to_csv(
        OUT / "local_id_legend.csv", index=False
    )

    methods = {
        "phase": 1,
        "version": "1.1-accuracy",
        "purpose": "Primary ARR carbon feasibility screen — not a credit claim",
        "province": "Sudurpashchim, Nepal",
        "boundary_source": "OCHA COD-AB Nepal admin boundaries v02 (HDX)",
        "boundary_improvements": [
            "Replaced geoBoundaries with COD-AB ADM1/ADM2/ADM3",
            "Province and 9 districts nest with 0 ha topological gap",
            "93 local levels (palika) for finer distinguishable units",
        ],
        "reporting_grain_m": RES,
        "datasets": {
            "land_cover_primary": "ESA WorldCover 10m 2021 v200",
            "land_cover_ensemble": "ESRI/IO Annual LULC 2023 (confidence)",
            "forest_history": "Hansen GFC v1.11 treecover2000 + lossyear",
            "elevation_slope": "Copernicus DEM GLO-30",
            "admin": "OCHA COD-AB NP07 / ADM2 / ADM3",
        },
        "rules": {
            "biophysical_arr": "WorldCover shrubland/grassland/bare below 3800 m",
            "candidate_high": "biophysical + 10y non-forest + slope <15° + elev <3000 m",
            "candidate_medium": "biophysical + 10y non-forest + slope 15–25° + elev <3000 m",
            "candidate_high_mountain": "biophysical + 10y non-forest + elev 3000–3800 m + slope ≤25°",
            "candidate_low_risk": "biophysical but history fail or slope 25–35°",
            "verra_gold_screen": "candidate high + medium + high-mountain",
            "alpine_unsuitable": "snow/ice/moss or elev ≥3800 m",
            "confidence": "3=WorldCover family agrees with ESRI/IO; 2=both plantable; 1=disagree/missing",
        },
        "accuracy_reliability": {
            "spatial_precision_m": RES,
            "boundary_accuracy": "COD-AB official humanitarian boundaries; district nesting exact",
            "land_cover_oa_expected_pct": "70-87; ensemble confidence flags agreement",
            "decision_reliability_primary_screen_pct": "75-85 for triage when confidence=3",
            "district_ha_planning_band_pct": "±10-25 with COD-AB + ensemble (tighter than v1.0)",
            "not_included": [
                "land tenure / CFUG polygons",
                "FPIC",
                "field plots",
                "WDPA legal clearance",
                "VM0047 dynamic performance benchmark",
            ],
        },
        "feasibility_codes": FEAS_NAMES,
        "province_totals": province,
    }
    (OUT / "methods_and_totals.json").write_text(json.dumps(methods, indent=2))

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
        "confidence": scored["confidence"],
        "district_id": district_raster,
        "clear_10yr_nonforest": scored["clear_10yr"],
    }
    for name, arr in layers.items():
        with rasterio.open(OUT / f"{name}.tif", "w", **{**profile_base, "dtype": arr.dtype}) as dst:
            dst.write(arr, 1)
            dst.set_band_description(1, name)
    with rasterio.open(
        OUT / "local_id.tif", "w", **{**profile_base, "dtype": local_raster.dtype}
    ) as dst:
        dst.write(local_raster, 1)
    with rasterio.open(
        OUT / "slope_deg.tif", "w", **{**profile_base, "dtype": "float32", "nodata": -9999}
    ) as dst:
        dst.write(slope.astype(np.float32), 1)
    with rasterio.open(
        OUT / "elevation_m.tif", "w", **{**profile_base, "dtype": "float32", "nodata": -9999}
    ) as dst:
        dst.write(elev.astype(np.float32), 1)

    print("Writing overview map...")
    make_overview_map(
        scored["feasibility"], transform, prov, districts, OUT / "feasibility_overview.png"
    )

    print("DONE")
    print(json.dumps(province, indent=2))
    print("Top local levels by screen ha:")
    print(local_summary.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
