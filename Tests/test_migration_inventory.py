import json
import pathlib
import subprocess
import tarfile
import tempfile
import unittest

from tools.migration_inventory import InventoryError, build_report, write_report


MANIFESTS = {
    "veloren-world-harr.json": ("groups", 2),
    "veloren-ai-city.json": ("groups", 1),
    "veloren-villagers.json": ("residents", 1),
    "veloren-missions.json": ("missions", 1),
    "veloren-story-missions.json": ("missions", 1),
    "harr-research.json": ("techs", 1),
}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.nemo = self.root / "nemo"
        self.veloren = self.root / "veloren"
        (self.nemo / "content").mkdir(parents=True)
        self.veloren.mkdir()
        for repo in (self.nemo, self.veloren):
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "--allow-empty", "-qm", "baseline"], check=True)
        for name, (key, count) in MANIFESTS.items():
            (self.nemo / "content" / name).write_text(json.dumps({key: [{"id": f"{name}-{i}"} for i in range(count)]}))
        self.archive = self.root / "save.tgz"
        for name in ("data/world.sqlite", "data/veloren-link.sqlite", "userdata/server/saves/db.sqlite"):
            path = self.root / "old" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture")
        with tarfile.open(self.archive, "w:gz") as tar:
            tar.add(self.root / "old" / "data", arcname="data")
            tar.add(self.root / "old" / "userdata", arcname="userdata")

    def test_reports_revisions_counts_and_archive_hash_without_private_bytes(self):
        report = build_report(self.nemo, self.veloren, self.archive)
        self.assertEqual(report["manifests"]["veloren-world-harr.json"]["count"], 2)
        self.assertEqual(len(report["nemoworld_commit"]), 40)
        self.assertEqual(len(report["archive_sha256"]), 64)
        self.assertNotIn("fixture", json.dumps(report))

    def test_duplicate_ids_refused(self):
        path = self.nemo / "content" / "veloren-missions.json"
        path.write_text(json.dumps({"missions": [{"id": "same"}, {"id": "same"}]}))
        with self.assertRaisesRegex(InventoryError, "duplicate id"):
            build_report(self.nemo, self.veloren, self.archive)

    def test_missing_manifest_refused(self):
        (self.nemo / "content" / "harr-research.json").unlink()
        with self.assertRaisesRegex(InventoryError, "harr-research.json"):
            build_report(self.nemo, self.veloren, self.archive)

    def test_unsafe_archive_member_refused(self):
        with tarfile.open(self.archive, "w:gz") as tar:
            path = self.root / "old" / "data" / "world.sqlite"
            tar.add(path, arcname="../escape")
        with self.assertRaisesRegex(InventoryError, "unsafe archive member"):
            build_report(self.nemo, self.veloren, self.archive)

    def test_missing_save_refused(self):
        with tarfile.open(self.archive, "w:gz") as tar:
            tar.add(self.root / "old" / "data" / "world.sqlite", arcname="data/world.sqlite")
        with self.assertRaisesRegex(InventoryError, "veloren-link.sqlite"):
            build_report(self.nemo, self.veloren, self.archive)

    def test_failure_leaves_no_partial_report(self):
        output = self.root / "report.json"
        (self.nemo / "content" / "harr-research.json").unlink()
        with self.assertRaises(InventoryError):
            write_report(self.nemo, self.veloren, self.archive, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
