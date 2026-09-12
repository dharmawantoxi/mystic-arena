#!/usr/bin/env python3
"""godot_log_gate — gagalkan CI kalau log Godot headless memuat error.

KENAPA PERLU: `godot --headless` sering tetap keluar dengan exit code 0
walaupun ada `SCRIPT ERROR` / `Parse Error` / assignment properti yang salah.
Error seperti

    Invalid assignment of property or key 'process_material' with value of
    type 'ParticleProcessMaterial' on a base object of type 'CPUParticles2D'.

hanya muncul sebagai baris log saat FX-nya dipakai — kalau CI cuma melihat
exit code, bug seperti ini lolos. Gate ini yang membacanya.

Dipakai .github/workflows/godot-check.yml:

    python3 godot/tools/godot_log_gate.py import.log --require ""
    python3 godot/tools/godot_log_gate.py smoke.log --require "[BattleSmokeTest] PASS"

Exit 0 = bersih, 1 = ada error / baris wajib tidak ditemukan.
"""
import argparse
import re
import sys

## Pola yang SELALU berarti gagal (case sensitive seperti keluaran Godot).
FATAL_PATTERNS = [
    # Assertion harness tidak selalu SCRIPT ERROR. Bahkan jika ada PASS
    # (mis. log gabungan / callback terlambat), satu FAIL tetap fatal.
    r"\[[A-Za-z0-9_]+Test\] FAIL\b",
    r"SCRIPT ERROR",
    r"Parse Error",
    r"Compile Error",
    r"Invalid assignment of property",
    r"Invalid call\. Nonexistent function",
    r"Invalid get index",
    r"Invalid set index",
    r"Attempt to call function .* on a null instance",
    r"Cannot open file",
    r"Failed loading resource",
    r"Condition \".*\" is true\. Returning",  # ERR_FAIL_COND dari engine
    r"Resource file not found",
    r"Cyclic resource inclusion",
    r"Invalid type in function",
    r"Nonexistent signal",
    r"There is no animation with name",
    r'Parameter "body->get_space\(\)" is null',
    r"Node not found",
]

## Baris yang cocok pola di atas TAPI memang wajar di CI headless.
## Sengaja sempit: lebih baik CI cerewet daripada melewatkan bug FX.
ALLOWED_PATTERNS = [
    # Headless tidak punya audio/video device; Godot mengeluh sekali di awal.
    r"Condition \"!driver\" is true",
    r"No audio driver",
    r"Unable to initialize .* driver",
    # GDExtension mystic_lighting / mystic_skills opsional — lib .so/.dll tidak ikut repo
    # (build lokal via SConstruct). Godot log \"Failed loading resource\" /
    # \"Cannot open file\" / \"Condition !FileAccess::exists\" untuk lib yang
    # belum dibuild adalah wajar di CI headless; runtime fallback ke
    # Lighting.gd + shader GPU / HeroSkillKitLoader.gd tetap jalan.
    r"mystic_lighting",
    r"libmystic_lighting",
    r"mystic_skills",
    r"libmystic_skills",
    r"FileAccess::exists",
    r"open_dynamic_library",
    r"open_library",
    r"GDExtension dynamic library not found",
    r"Failed loading resource.*mystic_lighting",
    r"Failed loading resource.*mystic_skills",
    r"addons/mystic_lighting",
    r"addons/mystic_skills",
]


def scan(text):
    fatal = [re.compile(p) for p in FATAL_PATTERNS]
    allowed = [re.compile(p) for p in ALLOWED_PATTERNS]
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if any(a.search(line) for a in allowed):
            continue
        if any(f.search(line) for f in fatal):
            hits.append((i, line.strip()))
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", help="berkas log keluaran godot --headless")
    ap.add_argument("--require", action="append", default=[],
                    help="teks yang WAJIB ada di log (boleh diulang)")
    ap.add_argument("--label", default="", help="nama langkah untuk pesan")
    args = ap.parse_args(argv)

    try:
        with open(args.log, encoding="utf-8", errors="replace") as log:
            text = log.read()
    except OSError as exc:
        print("FAIL tidak bisa membaca %s: %s" % (args.log, exc))
        return 1

    label = (args.label + ": ") if args.label else ""
    problems = 0

    hits = scan(text)
    if hits:
        problems += len(hits)
        print("FAIL %s%d baris error di %s" % (label, len(hits), args.log))
        for line_no, line in hits[:40]:
            print("  %5d | %s" % (line_no, line))
        if len(hits) > 40:
            print("  ... %d baris lagi" % (len(hits) - 40))

    for needle in args.require:
        if needle and needle not in text:
            problems += 1
            print("FAIL %stidak menemukan baris wajib: %r" % (label, needle))

    if problems:
        return 1
    print("OK   %slog bersih (%d baris)" % (label, len(text.splitlines())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
