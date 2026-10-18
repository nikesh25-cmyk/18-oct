#!/usr/bin/env python3
"""Fetch a small, pinned set of CC0 Poly Haven models from their official API."""

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "Assets/Resources/Visual/Models"
ASSETS = (
    "modular_urban_apartments_facade",
    "modular_factory_facade",
    "planter_pot_clay",
    "painted_wooden_bench",
    "wooden_crate_01",
)
USER_AGENT = "NemoWorldAssetImporter/1.0 (Poly Haven CC0 game integration)"


def read_url(url):
    host = urlparse(url).hostname
    if host not in {"api.polyhaven.com", "dl.polyhaven.org"}:
        raise ValueError(f"Unexpected asset host: {host}")
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=90) as response:
        return response.read()


def save_file(relative, info):
    target = DEST / relative
    expected = info["md5"]
    if target.exists() and hashlib.md5(target.read_bytes()).hexdigest() == expected:
        data = target.read_bytes()
    else:
        data = read_url(info["url"])
        if len(data) != info["size"] or hashlib.md5(data).hexdigest() != expected:
            raise ValueError(f"Download integrity check failed: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f"{relative}: {len(data):,} bytes")
    return {
        "file": "Models/" + relative.as_posix(),
        "url": info["url"],
        "md5": expected,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def main():
    manifest = ROOT / "Assets/Resources/Visual/SOURCES.json"
    sources = json.loads(manifest.read_text())
    visual_root = ROOT / "Assets/Resources/Visual"
    for entry in sources["files"]:
        path = visual_root / entry["file"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Existing visual asset failed source manifest check: {entry['file']}")
    known = {entry["file"] for entry in sources["files"]}
    for asset in ASSETS:
        metadata = json.loads(read_url(f"https://api.polyhaven.com/files/{asset}"))
        bundle = metadata["fbx"]["1k"]["fbx"]
        downloads = {Path(f"{asset}_1k.fbx"): bundle}
        # Built-in Standard materials use albedo, normal and (where supplied)
        # opacity. Omit source roughness/displacement/metal maps from this
        # bounded 1K runtime import to keep the Unity project manageable.
        downloads.update({
            Path(name): info for name, info in bundle["include"].items()
            if any(token in name for token in ("_diff_", "_nor_gl_", "_alpha_"))
        })
        for relative, info in downloads.items():
            if "Models/" + relative.as_posix() not in known:
                sources["files"].append(save_file(relative, info))
    manifest.write_text(json.dumps(sources, indent=2) + "\n")


if __name__ == "__main__":
    main()
