#!/usr/bin/env python3
"""Zephyr geometry export regression tests (no pygame dependency)."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import prepare_godot_zephyr_bolt as prepare


class ZephyrBoltPrepareTest(unittest.TestCase):
    def test_current(self):
        fixture, colors = prepare.build()
        self.assertEqual(json.loads(prepare.OUTPUT.read_text()), fixture)
        self.assertEqual(json.loads(prepare.PALETTE.read_text()), json.loads(json.dumps(colors)))

    def test_coverage_and_command_order(self):
        fixture, _ = prepare.build()
        self.assertEqual(len(fixture["cases"]), 80)
        for case in fixture["cases"]:
            commands = case["commands"]
            self.assertEqual([c[0] for c in commands],
                             ["polygon", "polygon", "glow", "polygon", "polygon", "polygon",
                              "polygon", "line", "line", "rect", "rect", "rect", "rect", "rect", "rect"])
        self.assertEqual({c["params"]["crit"] for c in fixture["cases"]}, {False, True})

    def test_expected_axis_aligned_geometry(self):
        fixture, _ = prepare.build()
        commands = fixture["cases"][0]["commands"]
        self.assertEqual(commands[0][2], [[100, 204], [74, 200], [100, 195]])
        self.assertEqual(commands[2], ["glow", [100, 12, 84, 255], [88, 188], 12, 0.42])
        self.assertEqual(commands[5][2], [[118, 200], [98, 204], [91, 200], [98, 195]])

    def test_records_source_not_a_copied_geometry_formula(self):
        baseline, _ = prepare.build()
        source = prepare.SOURCE.read_text().replace("tail = r * 4.2", "tail = r * 5.2")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.py"
            path.write_text(source)
            with patch.object(prepare, "SOURCE", path):
                changed, _ = prepare.build()
        self.assertNotEqual(baseline["cases"][0]["commands"][0], changed["cases"][0]["commands"][0])

    def test_check_never_rewrites_stale_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stale.json"
            path.write_text("{}\n")
            with patch.object(prepare, "OUTPUT", path), patch("sys.argv", ["prepare", "--check"]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    prepare.main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(path.read_text(), "{}\n")


if __name__ == "__main__":
    unittest.main()
