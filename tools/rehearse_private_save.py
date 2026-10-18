"""Rehearse a read-only, complete SQLite snapshot from the protected Harr archive.

Output is private staging data, not a migrated C# game database. Never place it in Git.
"""

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import struct
import tarfile
import tempfile


DATABASES = ("data/world.sqlite", "data/veloren-link.sqlite", "userdata/server/saves/db.sqlite")
SIDECARS = tuple(name + suffix for name in DATABASES for suffix in ("-wal", "-shm"))
MAX_MEMBER_BYTES = 2_000_000_000


class RehearsalError(Exception):
    pass


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def table_counts(connection):
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    counts = {}
    for (name,) in rows:
        escaped = name.replace('"', '""')
        counts[name] = connection.execute('SELECT COUNT(*) FROM "' + escaped + '"').fetchone()[0]
    return counts


def table_fingerprints(connection):
    """Hash typed row values as a multiset, independent of SQLite row ordering."""
    names = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    result = {}
    for (name,) in names:
        escaped = name.replace('"', '""')
        row_hashes = []
        for row in connection.execute('SELECT * FROM "' + escaped + '"'):
            row_digest = hashlib.sha256()
            for value in row:
                if value is None:
                    tag, data = b"n", b""
                elif isinstance(value, int):
                    tag, data = b"i", str(value).encode("ascii")
                elif isinstance(value, float):
                    tag, data = b"f", struct.pack(">d", value)
                elif isinstance(value, str):
                    tag, data = b"t", value.encode("utf-8")
                else:
                    tag, data = b"b", bytes(value)
                row_digest.update(tag)
                row_digest.update(len(data).to_bytes(8, "big"))
                row_digest.update(data)
            row_hashes.append(row_digest.digest())
        table_digest = hashlib.sha256()
        for row_hash in sorted(row_hashes):
            table_digest.update(row_hash)
        result[name] = table_digest.hexdigest()
    return result


def snapshot_database(raw, output):
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output.parent, 0o700)
    with closing(sqlite3.connect(raw)) as source:
        source.execute("PRAGMA query_only=ON")
        if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RehearsalError("source database integrity failed")
        before = table_counts(source)
        before_fingerprints = table_fingerprints(source)
        with closing(sqlite3.connect(output)) as destination:
            source.backup(destination)
            if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RehearsalError("staged database integrity failed")
            after = table_counts(destination)
            after_fingerprints = table_fingerprints(destination)
    if before != after or before_fingerprints != after_fingerprints:
        raise RehearsalError("staged table rows differ")
    os.chmod(output, 0o600)
    return {"tables": len(after), "rows": after, "row_fingerprints": after_fingerprints, "sha256": sha256(output)}


def extract_saves(archive, raw_root):
    needed = set(DATABASES)
    selected = set(DATABASES + SIDECARS)
    with tarfile.open(archive, "r:gz") as bundle:
        members = {member.name: member for member in bundle if member.name in selected}
        if not needed.issubset(members):
            raise RehearsalError("missing required SQLite database")
        for name, member in members.items():
            if not member.isfile() or member.size > MAX_MEMBER_BYTES:
                raise RehearsalError("invalid SQLite archive member")
            destination = raw_root / name
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with bundle.extractfile(member) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
            os.chmod(destination, 0o600)


def verify_existing(output, expected_digest):
    report_path = output / "rehearsal-report.json"
    if not report_path.is_file():
        raise RehearsalError("destination already exists")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RehearsalError("destination already exists") from error
    if (report.get("format") != "harr-private-save-rehearsal-v1" or
            report.get("archive_sha256") != expected_digest or
            set(report.get("databases", {})) != set(DATABASES)):
        raise RehearsalError("destination already exists with different source")
    for name in DATABASES:
        destination = output / name
        entry = report["databases"][name]
        if (not destination.is_file() or
                len(entry.get("row_fingerprints", {})) != entry.get("tables") or
                sha256(destination) != entry["sha256"]):
            raise RehearsalError("staged database changed since rehearsal")
    return report


def rehearse(archive, expected_digest, output):
    archive = Path(archive)
    output = Path(output)
    if not archive.is_file() or len(expected_digest) != 64 or sha256(archive) != expected_digest:
        raise RehearsalError("archive digest mismatch")
    if output.exists():
        return verify_existing(output, expected_digest)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".harr-rehearsal-", dir=output.parent))
    os.chmod(temporary, 0o700)
    try:
        raw_root = temporary / "raw"
        raw_root.mkdir(mode=0o700)
        extract_saves(archive, raw_root)
        report = {"format": "harr-private-save-rehearsal-v1", "archive_sha256": expected_digest, "databases": {}}
        for name in DATABASES:
            report["databases"][name] = snapshot_database(raw_root / name, temporary / name)
        shutil.rmtree(raw_root)
        report_path = temporary / "rehearsal-report.json"
        with report_path.open("w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.chmod(report_path, 0o600)
        if output.exists():
            raise RehearsalError("destination already exists")
        os.rename(temporary, output)
        return report
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = rehearse(args.archive, args.expected_sha256, args.output_dir)
    except (OSError, sqlite3.Error, tarfile.TarError, RehearsalError) as error:
        parser.exit(1, "rehearsal failed: " + str(error) + "\n")
    print("Private save rehearsal complete: " + str(len(report["databases"])) + " databases; report kept in private output")


if __name__ == "__main__":
    main()
