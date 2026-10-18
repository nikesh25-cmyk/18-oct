import json
import pathlib
import tempfile
import unittest

from tools.export_harr_city import ExportError, export_city, write_city


class ExportCityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.manifest = self.root / "manifest.json"
        self.record = self.root / "record.json"
        self.manifest.write_text(json.dumps({"site": "Harr", "groups": [
            {"id": "tower", "anchor": {"plot": "Plaza", "nth": 0}, "ground_at": [0, 0], "ops": [
                {"op": "fill", "from": [0, 0, 0], "to": [1, 1, 2], "kind": "Rock", "rgb": [10, 20, 30]}
            ]}
        ]}))
        self.record.write_text(json.dumps({"site": "Harr", "origin": [100, 200], "groups": {
            "tower": {"anchor": [110, 220], "ground": 400, "digest": "abc"},
            "old-road": {"anchor": [115, 205], "ground": 399, "digest": "old"}
        }}))

    def test_converts_saved_anchor_and_reports_orphan(self):
        package, report = export_city(self.manifest, self.record)
        self.assertEqual(package["groups"][0]["anchor"], [10, 20])
        self.assertEqual(package["groups"][0]["ground"], 400)
        self.assertEqual(report["unresolved_saved_groups"], ["old-road"])
        self.assertEqual(report["missing_application_groups"], [])

    def test_recovers_saved_orphan_from_pinned_legacy_manifest(self):
        legacy = self.root / "legacy.json"
        legacy.write_text(json.dumps({"site": "Harr", "groups": [
            {"id": "old-road", "ops": [{"op": "fill", "from": [0, 0, 0],
                "to": [0, 0, 0], "kind": "Rock", "rgb": [1, 2, 3]}]}
        ]}))
        package, report = export_city(self.manifest, self.record, legacy)
        self.assertEqual(len(package["groups"]), 2)
        self.assertEqual(package["groups"][1]["anchor"], [15, 5])
        self.assertEqual(package["groups"][1]["provenance"], "legacy-saved")
        self.assertEqual(report["recovered_legacy_groups"], ["old-road"])
        self.assertEqual(report["unresolved_saved_groups"], [])

    def test_duplicate_id_refused(self):
        data = json.loads(self.manifest.read_text())
        data["groups"].append(data["groups"][0])
        self.manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ExportError, "duplicate group"):
            export_city(self.manifest, self.record)

    def test_missing_application_refused(self):
        data = json.loads(self.record.read_text())
        del data["groups"]["tower"]
        self.record.write_text(json.dumps(data))
        with self.assertRaisesRegex(ExportError, "missing application"):
            export_city(self.manifest, self.record)

    def test_oversize_fill_refused(self):
        data = json.loads(self.manifest.read_text())
        data["groups"][0]["ops"][0]["to"] = [100, 100, 100]
        self.manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ExportError, "oversize"):
            export_city(self.manifest, self.record)

    def test_invalid_op_refused_without_output(self):
        data = json.loads(self.manifest.read_text())
        data["groups"][0]["ops"][0]["op"] = "teleport"
        self.manifest.write_text(json.dumps(data))
        out = self.root / "city.json"
        report = self.root / "report.json"
        with self.assertRaisesRegex(ExportError, "unsupported op"):
            write_city(self.manifest, self.record, out, report)
        self.assertFalse(out.exists())
        self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
