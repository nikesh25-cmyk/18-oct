"""Read-only public inventory of NemoWorld source and a private Harr backup."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile


class InventoryError(Exception):
    pass


MANIFESTS = {
    "veloren-world-harr.json": "groups",
    "veloren-ai-city.json": "groups",
    "veloren-villagers.json": "residents",
    "veloren-missions.json": "missions",
    "veloren-story-missions.json": "missions",
    "harr-research.json": "techs",
}
REQUIRED_SAVES = (
    "data/world.sqlite",
    "data/veloren-link.sqlite",
    "userdata/server/saves/db.sqlite",
)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def git_state(root):
    try:
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], stderr=subprocess.DEVNULL))
    except subprocess.CalledProcessError as error:
        raise InventoryError("not a readable Git checkout") from error
    return head, dirty


def read_manifest(path, collection):
    if not path.is_file():
        raise InventoryError(f"missing manifest: {path.name}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InventoryError(f"invalid manifest: {path.name}") from error
    records = data.get(collection) if isinstance(data, dict) else None
    if not isinstance(records, list):
        raise InventoryError(f"missing {collection} list: {path.name}")
    ids = [item.get("id") if isinstance(item, dict) else None for item in records]
    if any(not isinstance(value, str) or not value for value in ids):
        raise InventoryError(f"missing id: {path.name}")
    if len(ids) != len(set(ids)):
        raise InventoryError(f"duplicate id: {path.name}")
    return {"count": len(records), "ids": ids, "sha256": digest(path)}


def archive_count(path):
    if not Path(path).is_file():
        raise InventoryError("missing archive")
    names = set()
    try:
        with tarfile.open(path, "r:gz") as archive:
            for member in archive:
                name = PurePosixPath(member.name)
                if name.is_absolute() or ".." in name.parts or not member.name or member.issym() or member.islnk():
                    raise InventoryError("unsafe archive member")
                names.add(str(name))
    except (tarfile.TarError, OSError) as error:
        raise InventoryError("unreadable archive") from error
    for required in REQUIRED_SAVES:
        if required not in names:
            raise InventoryError(f"missing save: {required}")
    return len(names)


def build_report(nemoworld, veloren, archive):
    nemo_head, nemo_dirty = git_state(nemoworld)
    veloren_head, veloren_dirty = git_state(veloren)
    manifests = {
        name: read_manifest(Path(nemoworld) / "content" / name, collection)
        for name, collection in MANIFESTS.items()
    }
    count = archive_count(archive)
    return {
        "format": "nemoworld-unity-migration-inventory-v1",
        "nemoworld_commit": nemo_head,
        "nemoworld_dirty": nemo_dirty,
        "veloren_commit": veloren_head,
        "veloren_dirty": veloren_dirty,
        "archive_sha256": digest(archive),
        "archive_members": count,
        "required_saves_present": list(REQUIRED_SAVES),
        "manifests": manifests,
    }


def write_report(nemoworld, veloren, archive, output):
    report = build_report(nemoworld, veloren, archive)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, prefix=".migration-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nemoworld", type=Path, required=True)
    parser.add_argument("--veloren", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = write_report(args.nemoworld, args.veloren, args.archive, args.output)
    except InventoryError as error:
        parser.exit(1, f"inventory failed: {error}\n")
    print(f"Wrote inventory: {args.output} ({len(report['manifests'])} manifests)")


if __name__ == "__main__":
    main()
