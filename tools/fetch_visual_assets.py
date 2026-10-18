"""Fetch the exact CC0 Poly Haven source maps used by the Unity preview.

This is an offline, build-time import. The game never calls the Poly Haven API.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "Assets" / "Resources" / "Visual"
USER_AGENT = "NemoWorldAssetImport/0.1 (Unity source-asset verification)"
ASSETS = {
    "worn_asphalt": (("Diffuse", "jpg"), ("nor_gl", "jpg")),
    "concrete_wall_004": (("Diffuse", "jpg"), ("nor_gl", "jpg")),
    "blue_metal_plate": (("Diffuse", "jpg"), ("nor_gl", "jpg")),
    "leafy_grass": (("Diffuse", "jpg"), ("nor_gl", "jpg")),
    "forrest_sand_01": (("Diffuse", "jpg"), ("nor_gl", "jpg")),
    "rooftop_night": (("hdri", "hdr"),),
}


def get(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as response:
        return response.read()


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = {"license": "CC0", "source": "https://polyhaven.com/license", "files": []}
    for asset, maps in ASSETS.items():
        metadata = json.loads(get(f"https://api.polyhaven.com/files/{asset}"))
        for map_name, extension in maps:
            info = metadata[map_name]["1k"][extension]
            url = info["url"]
            if not url.startswith("https://dl.polyhaven.org/file/ph-assets/"):
                raise ValueError(f"Unexpected source URL: {url}")
            name = f"{asset}_{map_name}.{extension}"
            path = DEST / name
            data = path.read_bytes() if path.exists() else get(url)
            if len(data) != info["size"] or hashlib.md5(data).hexdigest() != info["md5"]:
                raise ValueError(f"Source verification failed: {name}")
            path.write_bytes(data)
            manifest["files"].append({
                "file": name, "url": url, "md5": info["md5"],
                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            })
            print(f"Verified {name} ({len(data)} bytes)")
    model = json.loads(get("https://api.polyhaven.com/files/street_lamp_01"))["fbx"]["1k"]["fbx"]
    for relative, info in [("street_lamp_01_1k.fbx", model), *model["include"].items()]:
        url = info["url"]
        if not url.startswith("https://dl.polyhaven.org/file/ph-assets/"):
            raise ValueError(f"Unexpected model URL: {url}")
        path = DEST / "Models" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = path.read_bytes() if path.exists() else get(url)
        if len(data) != info["size"] or hashlib.md5(data).hexdigest() != info["md5"]:
            raise ValueError(f"Source verification failed: {relative}")
        path.write_bytes(data)
        manifest["files"].append({
            "file": "Models/" + relative, "url": url, "md5": info["md5"],
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
        })
        print(f"Verified {relative} ({len(data)} bytes)")
    (DEST / "SOURCES.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
