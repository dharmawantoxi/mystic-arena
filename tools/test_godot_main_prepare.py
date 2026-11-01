#!/usr/bin/env python3
"""Offline tests for the native entry-point asset preparation tool."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare", ROOT / "tools/prepare_godot_main.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class PrepareTests(unittest.TestCase):
    def test_catalog(self):
        rows = prepare.level_catalog()
        self.assertEqual([row["level_number"] for row in rows], list(range(1, 55)))
        self.assertEqual(rows[0]["name"], "The Fallen Realm")
        self.assertEqual(set(rows[0]), set(prepare.FIELDS))

    def test_container_not_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            for content, expected in [
                (b"OggS" + bytes(60), "ogg"),
                (b"ID3" + bytes(60), "mp3"),
                (b"\xff\xfb" + bytes(60), "mp3"),
                (b"RIFF" + bytes(4) + b"WAVE" + bytes(48), "wav"),
            ]:
                path = Path(directory) / "misleading.wav"
                path.write_bytes(content)
                self.assertEqual(prepare.audio_extension(path), expected)
            path.write_bytes(b"not audio")
            with self.assertRaises(ValueError):
                prepare.audio_extension(path)


if __name__ == "__main__":
    unittest.main()
