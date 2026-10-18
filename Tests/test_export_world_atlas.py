import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "tools" / "export_world_atlas.mjs"


class WorldAtlasExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.source = self.root / "map.mjs"
        self.output = self.root / "atlas.json"

    def export(self, regions):
        self.source.write_text("export const MAP_COLUMNS=288; export const MAP_ROWS=208; export const MAP_LAYOUT=" + json.dumps(regions) + ";")
        return subprocess.run(["node", str(EXPORTER), "--source", str(self.source), "--output", str(self.output)], capture_output=True, text=True)

    def test_preserves_ids_rectangles_and_source_hash(self):
        result = self.export([{"world": "commons", "x": 0, "y": 0, "width": 96, "height": 64},
                              {"world": "orchard", "x": 96, "y": 0, "width": 40, "height": 28}])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.output.read_text())
        self.assertEqual(data["bounds"], [288, 208])
        self.assertEqual(data["regions"][1]["world"], "orchard")
        self.assertEqual(len(data["source_sha256"]), 64)

    def test_overlap_refused_without_output(self):
        result = self.export([{"world": "one", "x": 0, "y": 0, "width": 20, "height": 20},
                              {"world": "two", "x": 19, "y": 0, "width": 20, "height": 20}])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_duplicate_and_out_of_bounds_refused(self):
        regions = [{"world": "one", "x": 0, "y": 0, "width": 20, "height": 20},
                   {"world": "one", "x": 280, "y": 0, "width": 20, "height": 20}]
        result = self.export(regions)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
