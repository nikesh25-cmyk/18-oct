import json
import pathlib
import tempfile
import unittest

from tools.export_harr_content import ContentError, export_content


class HarrContentExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.files = {}
        for name, key, ids in [
            ("veloren-villagers.json", "residents", ["a", "b"]),
            ("veloren-missions.json", "missions", ["meet"]),
            ("veloren-story-missions.json", "missions", ["story"]),
            ("harr-research.json", "techs", ["first", "second"]),
        ]:
            p = self.root / name
            rows = [{"id": item} for item in ids]
            if key == "techs":
                rows[1]["needs"] = ["first"]
            p.write_text(json.dumps({key: rows}))
            self.files[name] = p

    def test_preserves_raw_content_and_provenance(self):
        package = export_content(self.files, expected=(2, 1, 1, 2))
        self.assertEqual(len(package["residents"]), 2)
        self.assertEqual(len(package["missions"]), 2)
        self.assertEqual(len(package["techs"]), 2)
        self.assertEqual(len(package["source_sha256"]), 4)

    def test_duplicate_id_rejected(self):
        self.files["veloren-villagers.json"].write_text(json.dumps({"residents": [{"id": "a"}, {"id": "a"}]}))
        with self.assertRaisesRegex(ContentError, "duplicate"):
            export_content(self.files, expected=(2, 1, 1, 2))

    def test_missing_tech_prerequisite_rejected(self):
        self.files["harr-research.json"].write_text(json.dumps({"techs": [{"id": "first", "needs": ["absent"]}, {"id": "second"}]}))
        with self.assertRaisesRegex(ContentError, "prerequisite"):
            export_content(self.files, expected=(2, 1, 1, 2))


if __name__ == "__main__":
    unittest.main()
