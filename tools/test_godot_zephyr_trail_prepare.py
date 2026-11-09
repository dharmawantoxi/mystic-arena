#!/usr/bin/env python3
import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import prepare_godot_zephyr_trail as prepare


class ZephyrTrailPrepareTest(unittest.TestCase):
    def test_current_and_deterministic(self):
        config, fixture = prepare.build()
        self.assertEqual((config, fixture), prepare.build())
        self.assertEqual(config, json.loads(prepare.CONFIG.read_text()))
        self.assertEqual(fixture, json.loads(prepare.FIXTURE.read_text()))

    def test_defaults_and_baked_pose_coverage(self):
        config, fixture = prepare.build()
        self.assertEqual(config["defaults"]["samples"], 7)
        self.assertEqual(config["defaults"]["life"], 0.26)
        self.assertEqual(len(config["attachments"]), 8)
        self.assertEqual([i for i, row in enumerate(config["attachments"]) if row["swinging"]], [3, 4])
        self.assertEqual(len(fixture["world_attachments"]), 32)
        self.assertEqual(len(fixture["cases"]), 4)

    def test_size_guard_and_expiry_boundaries(self):
        _, fixture = prepare.build()
        rows = fixture["cases"][2]["expected"]
        self.assertEqual(len(rows[1]["commands"]), 3)  # exactly 1400 px accepted
        self.assertEqual(rows[2]["commands"], [])      # larger scratch is rejected
        self.assertEqual(rows[-1]["state"]["points"], [])
        rows = fixture["cases"][3]["expected"]
        self.assertEqual(rows[0]["state"]["points"], [])
        self.assertTrue(rows[0]["state"]["active"])  # preserve unusual Python samples=0 behavior
        self.assertFalse(rows[1]["state"]["active"])

    def test_original_rig_formula_drives_attachments(self):
        before, _ = prepare.build()
        text = re.sub(r"(STAFF_R_STRIKE\s*=\s*)68\.0", r"\g<1>75.0", prepare.BUNDLE.read_text())
        self.assertNotEqual(text, prepare.BUNDLE.read_text())
        with tempfile.TemporaryDirectory(dir=prepare.ROOT) as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "BUNDLE", path):
                after, _ = prepare.build()
        self.assertNotEqual(before["attachments"][4], after["attachments"][4])

    def test_original_trail_lifetime_drives_fixture(self):
        _, before = prepare.build()
        text = prepare.SOURCE.read_text().replace("self.life = 0.26", "self.life = 0.36")
        with tempfile.TemporaryDirectory(dir=prepare.ROOT) as directory:
            path = Path(directory) / "changed.py"
            path.write_text(text)
            with patch.object(prepare, "SOURCE", path):
                _, after = prepare.build()
        self.assertNotEqual(before["cases"][0]["expected"], after["cases"][0]["expected"])

    def test_stale_baked_pose_count_fails_closed(self):
        manifest = json.loads(prepare.MANIFEST.read_text())
        manifest["units"]["zephyr"]["anims"]["attack"][1] = 9
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            with patch.object(prepare, "MANIFEST", path), self.assertRaises(ValueError):
                prepare.build()

    def test_check_does_not_rewrite_stale_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stale.json"
            path.write_text("{}\n")
            with patch.object(prepare, "CONFIG", path), patch("sys.argv", ["prepare", "--check"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    prepare.main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(path.read_text(), "{}\n")


if __name__ == "__main__":
    unittest.main()
