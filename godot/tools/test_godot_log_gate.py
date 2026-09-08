#!/usr/bin/env python3
"""Regresi gate: PASS bukan alasan mengabaikan error atau assertion FAIL."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from godot_log_gate import main, scan


class GodotLogGateTest(unittest.TestCase):
    def gate(self, text, required="[BossDeathRewardParityTest] PASS"):
        with tempfile.TemporaryDirectory(prefix="godot-gate-") as tmp:
            path = Path(tmp) / "runtime.log"
            path.write_text(text, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                return main([str(path), "--require", required])

    def test_clean_pass(self):
        self.assertEqual(self.gate("[BossDeathRewardParityTest] PASS: 123 checks"), 0)

    def test_exit_without_pass_is_failure(self):
        self.assertEqual(self.gate("Godot Engine v4.3.stable\n"), 1)

    def test_fail_even_with_pass(self):
        self.assertEqual(self.gate(
            "[BossDeathRewardParityTest] PASS\n"
            "[BossDeathRewardParityTest] FAIL: gold dibayar dua kali\n"), 1)
        self.assertTrue(scan("[MatchScoringParityTest] FAIL: regression"))

    def test_runtime_errors_even_with_pass(self):
        for error in ("SCRIPT ERROR", "Parse Error", "Compile Error",
                      "Invalid assignment of property", "Node not found"):
            with self.subTest(error=error):
                self.assertEqual(self.gate(
                    "[BossDeathRewardParityTest] PASS\n" + error), 1)

    def test_headless_allowance_stays_narrow(self):
        self.assertFalse(scan('Condition "!driver" is true'))
        self.assertTrue(scan('Condition "wrong_state" is true. Returning'))


if __name__ == "__main__":
    unittest.main()
