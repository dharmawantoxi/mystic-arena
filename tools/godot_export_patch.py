#!/usr/bin/env python3
"""
Tambal godot/export_presets.cfg sesuai versi & jenis build (Fase 6).

Dipakai workflow .github/workflows/build-android-godot.yml SEBELUM
`godot --headless --export-release/debug "Android"`. Bisa juga dijalankan
lokal untuk uji:

    RELEASE_TAG=v1.2.3 BUILD_TYPE=release python3 tools/godot_export_patch.py --dry-run

Aturan versi:
  * tag vX.Y.Z     -> version/name=X.Y.Z, code = major*10000+minor*100+patch, AAB
  * manual release -> 0.0.1-dev / code=tanggal UTC (YYYYMMDD), AAB (verifikasi)
  * manual debug   -> 0.0.0-debug / code=tanggal UTC, APK (sideload)

Output:
  * file `ext` (nama ekstensi hasil export) ditulis ke $GITHUB_OUTPUT kalau
    env itu ada (CI), supaya step export/gerbang tahu nama filenya;
  * baris ringkasan dicetak ke stdout.
"""
import os
import re
import sys
from datetime import datetime, timezone


def resolve(tag: str, btype: str):
    """(version_name, version_code, extensi_file, gradle_export_format)"""
    if tag and re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        t = tag[1:]
        m, n, p = (int(x) for x in t.split(".")[:3])
        return t, m * 10000 + n * 100 + p, "aab", 1
    if btype == "release":
        return "0.0.1-dev", int(datetime.now(timezone.utc).strftime("%Y%m%d")), "aab", 1
    return "0.0.0-debug", int(datetime.now(timezone.utc).strftime("%Y%m%d")), "apk", 0


def patch(cfg_path: str, name: str, code: int, ext: str, fmt: int) -> None:
    lines = open(cfg_path, encoding="utf-8").read().splitlines(keepends=True)

    def repl_first(pattern: str, repl: str) -> None:
        for i, ln in enumerate(lines):
            if re.match(pattern, ln):
                lines[i] = repl + "\n"
                return
        sys.exit(f"::error::baris {pattern!r} tidak ada di {cfg_path}")

    # `export_path=` ada di 2 preset (Android dulu, Linux/X11 kemudian) ->
    # ganti HANYA yang pertama (= preset Android).
    repl_first(r"export_path=", f'export_path="build/MysticArena.{ext}"')
    repl_first(r"version/name=", f'version/name="{name}"')
    repl_first(r"version/code=", f"version/code={code}")
    repl_first(r"gradle_build/export_format=", f"gradle_build/export_format={fmt}")
    open(cfg_path, "w", encoding="utf-8").write("".join(lines))


def main() -> None:
    dry = "--dry-run" in sys.argv
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = os.path.join(root, "godot", "export_presets.cfg")
    tag = os.environ.get("RELEASE_TAG", "")
    btype = os.environ.get("BUILD_TYPE", "debug")
    name, code, ext, fmt = resolve(tag, btype)

    if not dry:
        patch(cfg, name, code, ext, fmt)
        # preset Linux/X11 harus tetap utuh
        check = open(cfg, encoding="utf-8").read()
        if 'export_path="build/MysticArena.x86_64"' not in check:
            sys.exit("::error::preset Linux/X11 ikut terubah — periksa tools/godot_export_patch.py")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"ext={ext}\n")
    suffix = "  [dry-run]" if dry else ""
    print(f"version/name={name}  version/code={code}  "
          f"format={'AAB' if fmt else 'APK'}  file=MysticArena.{ext}{suffix}")


if __name__ == "__main__":
    main()
