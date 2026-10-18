import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tarfile
import tempfile
import unittest

from tools.rehearse_private_save import RehearsalError, rehearse, table_fingerprints


DATABASES = ("data/world.sqlite", "data/veloren-link.sqlite", "userdata/server/saves/db.sqlite")


class PrivateSaveRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        for name in DATABASES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE records (id TEXT PRIMARY KEY, secret TEXT)")
                db.execute("INSERT INTO records VALUES ('stable-id', 'private-example')")
        self.archive = self.root / "source.tgz"
        with tarfile.open(self.archive, "w:gz") as bundle:
            for name in DATABASES:
                bundle.add(self.source / name, arcname=name)
        self.digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.output = self.root / "staged"

    def test_copies_all_tables_without_exposing_rows_in_report(self):
        report = rehearse(self.archive, self.digest, self.output)
        self.assertEqual(set(report["databases"]), set(DATABASES))
        self.assertEqual([report["databases"][name]["rows"]["records"] for name in DATABASES], [1, 1, 1])
        self.assertNotIn("private-example", json.dumps(report))
        for name in DATABASES:
            with sqlite3.connect(self.output / name) as db:
                self.assertEqual(db.execute("SELECT secret FROM records").fetchone()[0], "private-example")
        self.assertEqual(os.stat(self.output).st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(self.output / DATABASES[0]).st_mode & 0o777, 0o600)
        self.assertEqual(rehearse(self.archive, self.digest, self.output), report)

    def test_rejects_wrong_archive_digest_before_writing(self):
        with self.assertRaisesRegex(RehearsalError, "digest"):
            rehearse(self.archive, "0" * 64, self.output)
        self.assertFalse(self.output.exists())

    def test_missing_database_does_not_leave_partial_output(self):
        with tarfile.open(self.archive, "w:gz") as bundle:
            bundle.add(self.source / DATABASES[0], arcname=DATABASES[0])
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RehearsalError, "missing"):
            rehearse(self.archive, digest, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_unrelated_destination_is_not_overwritten(self):
        self.output.mkdir()
        marker = self.output / "keep"
        marker.write_text("untouched")
        with self.assertRaisesRegex(RehearsalError, "already exists"):
            rehearse(self.archive, self.digest, self.output)
        self.assertEqual(marker.read_text(), "untouched")

    def test_fingerprint_detects_changed_field_with_same_row_count(self):
        database = self.source / DATABASES[0]
        with sqlite3.connect(database) as connection:
            before = table_fingerprints(connection)
            connection.execute("UPDATE records SET secret='changed' WHERE id='stable-id'")
            after = table_fingerprints(connection)
        self.assertNotEqual(before["records"], after["records"])


if __name__ == "__main__":
    unittest.main()
