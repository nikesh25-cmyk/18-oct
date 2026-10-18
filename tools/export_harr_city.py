"""Export authored Harr geometry against a saved Veloren placement record."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


class ExportError(Exception):
    pass


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ExportError(f"cannot read {Path(path).name}") from error


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def point(value, length, label):
    if not isinstance(value, list) or len(value) != length or any(type(n) is not int for n in value):
        raise ExportError(f"invalid {label}")
    return value


def validate_op(op):
    if not isinstance(op, dict):
        raise ExportError("invalid op")
    kind = op.get("op")
    if kind not in ("fill", "clear", "foundation", "sprite"):
        raise ExportError(f"unsupported op: {kind}")
    if kind == "sprite":
        point(op.get("at"), 3, "sprite at")
        if not isinstance(op.get("sprite"), str) or not op["sprite"]:
            raise ExportError("invalid sprite")
    else:
        dimensions = 2 if kind == "foundation" else 3
        start = point(op.get("from"), dimensions, "op from")
        end = point(op.get("to"), dimensions, "op to")
        if any(hi < lo for lo, hi in zip(start, end)):
            raise ExportError("reversed op range")
        volume = 1
        for lo, hi in zip(start, end):
            volume *= hi - lo + 1
        if kind == "foundation":
            depth = op.get("depth")
            if type(depth) is not int or not 1 <= depth <= 64:
                raise ExportError("invalid foundation depth")
            volume *= depth
        if volume > 5000:
            raise ExportError("oversize op")
        if kind != "clear":
            rgb = point(op.get("rgb"), 3, "op rgb")
            if any(not 0 <= channel <= 255 for channel in rgb):
                raise ExportError("invalid op rgb")
    return op


def export_city(manifest_path, record_path, legacy_path=None):
    manifest = load(manifest_path)
    record = load(record_path)
    if manifest.get("site") != "Harr" or record.get("site") != "Harr":
        raise ExportError("site must be Harr")
    origin = point(record.get("origin"), 2, "world origin")
    source_groups = manifest.get("groups")
    applied = record.get("groups")
    if not isinstance(source_groups, list) or not isinstance(applied, dict):
        raise ExportError("missing groups")
    seen = set()
    groups = []
    for group in source_groups:
        if not isinstance(group, dict) or not isinstance(group.get("id"), str) or not group["id"]:
            raise ExportError("invalid group id")
        name = group["id"]
        if name in seen:
            raise ExportError(f"duplicate group: {name}")
        seen.add(name)
        placement = applied.get(name)
        if not isinstance(placement, dict):
            raise ExportError(f"missing application: {name}")
        anchor = point(placement.get("anchor"), 2, f"anchor of {name}")
        ground = placement.get("ground")
        if type(ground) is not int:
            raise ExportError(f"invalid ground: {name}")
        ops = group.get("ops")
        if not isinstance(ops, list) or len(ops) > 1000:
            raise ExportError(f"invalid ops: {name}")
        groups.append({
            "id": name,
            "anchor": [anchor[0] - origin[0], anchor[1] - origin[1]],
            "ground": ground,
            "digest": placement.get("digest", ""),
            "ops": [validate_op(op) for op in ops],
        })
    recovered = []
    if legacy_path is not None:
        legacy = load(legacy_path)
        if legacy.get("site") != "Harr" or not isinstance(legacy.get("groups"), list):
            raise ExportError("invalid legacy manifest")
        legacy_seen = set()
        for group in legacy["groups"]:
            name = group.get("id") if isinstance(group, dict) else None
            if not isinstance(name, str) or not name or name in legacy_seen:
                raise ExportError("invalid or duplicate legacy group")
            legacy_seen.add(name)
            if name in seen or name not in applied:
                continue
            placement = applied[name]
            anchor = point(placement.get("anchor"), 2, f"legacy anchor of {name}")
            ground = placement.get("ground")
            ops = group.get("ops")
            if type(ground) is not int or not isinstance(ops, list) or len(ops) > 1000:
                raise ExportError(f"invalid legacy group: {name}")
            groups.append({"id": name, "anchor": [anchor[0] - origin[0], anchor[1] - origin[1]],
                           "ground": ground, "digest": placement.get("digest", ""),
                           "provenance": "legacy-saved", "ops": [validate_op(op) for op in ops]})
            recovered.append(name)
            seen.add(name)
    unresolved = sorted(set(applied) - seen)
    package = {
        "format": "harr-unity-city-v1",
        "site": "Harr",
        "origin": origin,
        "ground_reference": min(group["ground"] for group in groups) if groups else 0,
        "source_manifest_sha256": sha(manifest_path),
        "saved_record_sha256": sha(record_path),
        "legacy_manifest_sha256": sha(legacy_path) if legacy_path is not None else None,
        "groups": groups,
    }
    report = {
        "format": "harr-unity-city-export-report-v1",
        "authored_groups": len(groups),
        "authored_ops": sum(len(group["ops"]) for group in groups),
        "saved_groups": len(applied),
        "unresolved_saved_groups": unresolved,
        "recovered_legacy_groups": sorted(recovered),
        "missing_application_groups": [],
        "source_manifest_sha256": package["source_manifest_sha256"],
        "saved_record_sha256": package["saved_record_sha256"],
    }
    return package, report


def write_json_atomic(value, path):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent, prefix=".harr-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, separators=(",", ":") if destination.name.endswith("city-v1.json") else None, indent=None if destination.name.endswith("city-v1.json") else 2)
            stream.write("\n")
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def write_city(manifest, record, output, report_path, legacy=None):
    package, report = export_city(manifest, record, legacy)
    write_json_atomic(package, output)
    write_json_atomic(report, report_path)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--world-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--legacy-manifest", type=Path)
    args = parser.parse_args()
    try:
        report = write_city(args.manifest, args.world_record, args.output, args.report, args.legacy_manifest)
    except ExportError as error:
        parser.exit(1, f"city export failed: {error}\n")
    print(f"Exported {report['authored_groups']} groups; {len(report['unresolved_saved_groups'])} saved groups unresolved")


if __name__ == "__main__":
    main()
