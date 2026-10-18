"""Package authored Harr residents, missions and research without private state."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


class ContentError(Exception):
    pass


SOURCES = (
    ("veloren-villagers.json", "residents"),
    ("veloren-missions.json", "missions"),
    ("veloren-story-missions.json", "missions"),
    ("harr-research.json", "techs"),
)


def export_content(files, expected=(52, 16, 12, 30)):
    sections = []
    hashes = {}
    for index, (name, key) in enumerate(SOURCES):
        path = Path(files[name])
        try:
            raw = path.read_bytes()
            document = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ContentError(f"cannot read {name}") from error
        rows = document.get(key)
        if not isinstance(rows, list) or len(rows) != expected[index]:
            raise ContentError(f"unexpected count: {name}")
        ids = [row.get("id") if isinstance(row, dict) else None for row in rows]
        if any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != len(ids):
            raise ContentError(f"invalid or duplicate ID: {name}")
        sections.append(rows)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    residents, core, story, techs = sections
    mission_ids = [row["id"] for row in core + story]
    if len(set(mission_ids)) != len(mission_ids):
        raise ContentError("duplicate mission ID across manifests")
    tech_ids = {row["id"] for row in techs}
    for tech in techs:
        needs = tech.get("needs", [])
        if not isinstance(needs, list) or any(need not in tech_ids for need in needs):
            raise ContentError(f"unresolved research prerequisite: {tech['id']}")
    return {
        "format": "harr-authored-content-v1",
        "source_sha256": hashes,
        "counts": {"residents": len(residents), "core_missions": len(core),
                   "story_missions": len(story), "techs": len(techs)},
        "residents": residents,
        "missions": [{"source": "core", "content": row} for row in core] +
                    [{"source": "story", "content": row} for row in story],
        "techs": techs,
    }


def write_atomic(package, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent,
                                         prefix=".harr-content-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(package, stream, separators=(",", ":"))
            stream.write("\n")
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        package = export_content({name: args.source_dir / name for name, _ in SOURCES})
        write_atomic(package, args.output)
    except ContentError as error:
        parser.exit(1, f"content export failed: {error}\n")
    print("Exported 52 residents, 28 missions and 30 technologies")


if __name__ == "__main__":
    main()
