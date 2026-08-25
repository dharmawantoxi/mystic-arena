"""
tools/test_storage_paths.py — Uji lokasi save lokal.

Memastikan:
  1. Desktop: save DIKUNCI ke root project (lokasi storage_paths.py),
     bukan ke cwd (supaya tidak hilang kalau game dibuka dari folder
     lain seperti shortcut/IDE).
  2. MYSTIC_SAVE_DIR bisa memaksa folder sandbox (dipakai test/CI).
  3. Android: save tetap di <ANDROID_PRIVATE>/saves.

Jalankan: python3 tools/test_storage_paths.py
"""
import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_pass = 0
_fail = 0


def check(name, cond, detail=""):
    global _pass, _fail
    if cond:
        _pass += 1
        print("  OK   %s" % name)
    else:
        _fail += 1
        print("  FAIL %s %s" % (name, ("- " + detail) if detail else ""))


def run_import(extra_env):
    """Import storage_paths dalam subprocess dan cetak SAVE_DIR."""
    env = dict(os.environ)
    env.pop("ANDROID_ARGUMENT", None)
    env.pop("ANDROID_PRIVATE", None)
    env.pop("MYSTIC_SAVE_DIR", None)
    env["PYTHONPATH"] = REPO_ROOT
    env.update(extra_env)
    code = (
        "import storage_paths;"
        "print(storage_paths.SAVE_DIR)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tempfile.mkdtemp(prefix="other_cwd_"),
        env=env,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout.strip()


# 1. Desktop: anchor ke root project
rc, out = run_import({})
expected = os.path.join(REPO_ROOT, "saves")
check("desktop -> <project>/saves", rc == 0 and out == expected, out)

# 2. Override env dihormati
sandbox = tempfile.mkdtemp(prefix="override_save_")
rc, out = run_import({"MYSTIC_SAVE_DIR": os.path.join(sandbox, "saves")})
check("MYSTIC_SAVE_DIR override", rc == 0 and out == os.path.join(
    sandbox, "saves"), out)

# 3. Android private
android_dir = tempfile.mkdtemp(prefix="android_private_")
rc, out = run_import({"ANDROID_PRIVATE": android_dir})
check("android -> <private>/saves", rc == 0 and out == os.path.join(
    android_dir, "saves"), out)

print()
print("HASIL: %d lulus, %d gagal" % (_pass, _fail))
sys.exit(1 if _fail else 0)
