"""
tools/test_backup_manager.py

Uji simulasi sistem backup lokal export/import (backup_manager.py)
TANPA perangkat Android dan TANPA pygame — sama seperti pengujian
storage_paths.py sebelumnya: semua jalur platform disimulasikan
lewat folder sementara + variabel lingkungan.

Yang diperiksa
──────────────
  1.  export tanpa save  -> 'no_data', tidak ada file ditulis
  2.  export normal      -> file di <Download>/MysticArena/, format
      sesuai spek: magic, version, exported_at, slots, settings,
      checksum sha256 yang cocok
  3.  validasi import: tolak JSON rusak, magic salah, checksum salah,
      versi tak dikenal — dengan pesan yang jelas
  4.  roundtrip install-ulang: hapus semua save -> find_backup ->
      apply_backup -> semua slot + settings kembali persis
  5.  slot yang tidak ada di backup ikut dikosongkan saat restore
  6.  proteksi: auto-export TIDAK menimpa backup yang datanya lebih
      baru ('conflict'); export manual force=True boleh
  7.  auto_export() (jalur SaveManager.save) menulis file di
      background tanpa melempar exception
  8.  check_restore_on_startup() memanggil callback saat semua slot
      kosong dan ada backup sah; tidak jalan dua kali
  9.  MYSTIC_BACKUP_DIR override dihormati (desktop/CI)

Jalankan:
    python3 tools/test_backup_manager.py
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import time

# ─── Sandbox: cwd + folder Download palsu, SEBELUM import modul game ───
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX = tempfile.mkdtemp(prefix="mystic_backup_test_")
WORK_DIR = os.path.join(SANDBOX, "game")          # cwd game (desktop)
DOWNLOAD_DIR = os.path.join(SANDBOX, "downloads")  # "folder Download"
os.makedirs(WORK_DIR, exist_ok=True)

# Pastikan tidak dikira Android
os.environ.pop("ANDROID_ARGUMENT", None)
os.environ.pop("ANDROID_PRIVATE", None)
os.environ["MYSTIC_BACKUP_DIR"] = DOWNLOAD_DIR
# Save lokal diarahkan ke sandbox (bukan ke repo) walau cwd berubah.
os.environ["MYSTIC_SAVE_DIR"] = os.path.join(WORK_DIR, "saves")

os.chdir(WORK_DIR)  # storage_paths -> SAVE_DIR mengikuti MYSTIC_SAVE_DIR
sys.path.insert(0, REPO_ROOT)

import backup_manager as bm  # noqa: E402

SAVE_DIR = os.path.join(WORK_DIR, "saves")
BACKUP_FILE = os.path.join(DOWNLOAD_DIR, "MysticArena",
                           "mystic_arena_backup.json")

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


def make_slot(num, level=5, gold=1200, played_at=None):
    os.makedirs(SAVE_DIR, exist_ok=True)
    data = {
        "unlocked_bosses": ["level%d" % i for i in range(1, level)],
        "purchased_heroes": ["knight", "archer"],
        "meta_gold": gold,
        "completed_levels": list(range(1, level + 1)),
        "last_played_level": level,
        "slot_created": time.time() - 86400,
        "slot_last_played": played_at or time.time(),
        "slot_playtime_seconds": 3600,
        "level_stats": {"1": {"best_score": 999}},
    }
    with open(os.path.join(SAVE_DIR, "slot_%d.json" % num), "w") as f:
        json.dump(data, f)
    return data


def make_settings():
    os.makedirs(SAVE_DIR, exist_ok=True)
    data = {"master_volume": 0.9, "difficulty": "hard",
            "game_speed": 1.5, "fps_limit": 120}
    with open(os.path.join(SAVE_DIR, "settings.json"), "w") as f:
        json.dump(data, f)
    return data


def wipe_saves():
    shutil.rmtree(SAVE_DIR, ignore_errors=True)


def wipe_backup():
    shutil.rmtree(os.path.dirname(BACKUP_FILE), ignore_errors=True)


def read_backup_file():
    with open(BACKUP_FILE, "r") as f:
        return json.load(f)


def wait_for(cond_fn, timeout=3.0):
    """Tunggu kondisi thread background (auto_export dkk)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cond_fn():
            return True
        time.sleep(0.05)
    return cond_fn()


print("=" * 62)
print(" TEST backup_manager.py  (simulasi desktop, tanpa Android)")
print(" sandbox : %s" % SANDBOX)
print("=" * 62)

# ── 1. Export tanpa save ──────────────────────────────────────────
print("\n[1] Export tanpa save data")
wipe_saves()
wipe_backup()
status, detail = bm.export_backup()
check("status 'no_data'", status == "no_data", repr((status, detail)))
check("tidak ada file ditulis", not os.path.exists(BACKUP_FILE))

# ── 2. Export normal + format file ────────────────────────────────
print("\n[2] Export normal & format file backup")
slot1 = make_slot(1, level=7, gold=2500)
slot3 = make_slot(3, level=3, gold=400)
settings = make_settings()

status, detail = bm.export_backup()
check("status 'ok'", status == "ok", repr((status, detail)))
check("file backup ada", os.path.exists(BACKUP_FILE))
check("path di dalam MYSTIC_BACKUP_DIR",
      os.path.abspath(BACKUP_FILE).startswith(
          os.path.abspath(DOWNLOAD_DIR)))

payload = read_backup_file()
check("magic sesuai", payload.get("magic") == "MYSTIC_ARENA_BACKUP")
check("version = 1", payload.get("version") == 1)
check("exported_at masuk akal",
      abs(payload.get("exported_at", 0) - time.time()) < 60)
check("slot 1 & 3 ikut, slot 2 tidak",
      set(payload.get("slots", {}).keys()) == {"1", "3"})
check("settings ikut",
      payload.get("settings", {}).get("difficulty") == "hard")

# checksum dihitung ulang manual: sha256 dari JSON kanonis tanpa field
# 'checksum'
body = {k: v for k, v in payload.items() if k != "checksum"}
canonical = json.dumps(body, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False)
expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
check("checksum sha256 cocok", payload.get("checksum") == expected)

# ringkasan untuk dialog
p2, err = bm.parse_backup_text(json.dumps(payload))
summary = bm.get_backup_summary(p2)
check("summary: level tertinggi 7", summary["highest_level"] == 7)
check("summary: gold 2500", summary["meta_gold"] == 2500)
check("summary: 2 slot", summary["slot_count"] == 2)
check("summary: ada tanggal", bool(summary["exported_at_str"]))

# ── 3. Validasi import: file rusak ditolak dengan jelas ───────────
print("\n[3] Validasi: tolak file korup / palsu")
p, err = bm.parse_backup_text("{ bukan json }")
check("JSON rusak ditolak", p is None and "JSON" in err, repr(err))

fake = dict(payload)
fake["magic"] = "OTHER_GAME"
p, err = bm.parse_backup_text(json.dumps(fake))
check("magic salah ditolak", p is None and "Mystic Arena" in err,
      repr(err))

tampered = json.loads(json.dumps(payload))
tampered["slots"]["1"]["meta_gold"] = 999999  # cheat!
p, err = bm.parse_backup_text(json.dumps(tampered))
check("checksum salah ditolak", p is None and "checksum" in err,
      repr(err))

future = dict(payload)
future["version"] = 99
p, err = bm.parse_backup_text(json.dumps(future))
check("versi tak dikenal ditolak", p is None and "version" in err,
      repr(err))

p, err = bm.parse_backup_text(json.dumps(payload))
check("file sah diterima", p is not None and err is None, repr(err))

# ── 4. Roundtrip install ulang ────────────────────────────────────
print("\n[4] Simulasi install ulang: wipe -> find -> restore")
wipe_saves()
check("semua slot kosong terdeteksi", bm.all_slots_empty())

found, summary, err = bm.find_backup()
check("backup ditemukan & sah", found is not None and err is None,
      repr(err))

ok, err = bm.apply_backup(found)
check("apply_backup sukses", ok, repr(err))

with open(os.path.join(SAVE_DIR, "slot_1.json")) as f:
    restored1 = json.load(f)
with open(os.path.join(SAVE_DIR, "slot_3.json")) as f:
    restored3 = json.load(f)
with open(os.path.join(SAVE_DIR, "settings.json")) as f:
    restored_settings = json.load(f)

check("slot 1 identik", restored1 == slot1)
check("slot 3 identik", restored3 == slot3)
check("slot 2 tetap kosong",
      not os.path.exists(os.path.join(SAVE_DIR, "slot_2.json")))
check("settings identik", restored_settings == settings)
check("all_slots_empty sekarang False", not bm.all_slots_empty())

# ── 5. Restore mengosongkan slot yang tak ada di backup ───────────
print("\n[5] Restore membuang slot lokal yang tidak ada di backup")
make_slot(2, level=1, gold=10)  # slot nyasar
ok, err = bm.apply_backup(found)
check("apply sukses", ok, repr(err))
check("slot 2 ikut dikosongkan",
      not os.path.exists(os.path.join(SAVE_DIR, "slot_2.json")))

# ── 6. Proteksi backup lebih baru ─────────────────────────────────
print("\n[6] Auto-export tidak menimpa backup yang lebih baru")
# Save lokal 'tua', backup di Download berisi progres lebih baru
wipe_saves()
make_slot(1, level=2, gold=100, played_at=time.time() - 7200)

newer_slots = {"1": dict(slot1, slot_last_played=time.time() + 60)}
newer = {
    "magic": bm.BACKUP_MAGIC,
    "version": 1,
    "exported_at": time.time(),
    "slots": newer_slots,
    "settings": {},
}
newer["checksum"] = bm.compute_checksum(newer)
os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
with open(BACKUP_FILE, "w") as f:
    json.dump(newer, f)

status, detail = bm.export_backup(force=False)
check("status 'conflict'", status == "conflict", repr(status))
check("detail = summary backup lama",
      isinstance(detail, dict) and detail.get("highest_level") == 7)
still = read_backup_file()
check("file TIDAK tertimpa",
      still["slots"]["1"]["slot_last_played"]
      == newer_slots["1"]["slot_last_played"])

status, detail = bm.export_backup(force=True)
check("force=True menimpa ('ok')", status == "ok", repr(status))
overwritten = read_backup_file()
check("isi sekarang dari save lokal",
      overwritten["slots"]["1"]["meta_gold"] == 100)

# backup korup di disk tidak boleh memblokir export berikutnya
with open(BACKUP_FILE, "w") as f:
    f.write("{corrupt!!")
status, detail = bm.export_backup(force=False)
check("backup korup langsung ditimpa export baru", status == "ok",
      repr((status, detail)))

# ── 7. auto_export (jalur SaveManager.save) ───────────────────────
print("\n[7] auto_export() background")
wipe_backup()
bm.auto_export()
ok = wait_for(lambda: os.path.exists(BACKUP_FILE))
check("file ditulis oleh worker", ok)
p, err = bm.parse_backup_text(open(BACKUP_FILE).read())
check("hasilnya valid", p is not None, repr(err))

# panggilan beruntun tidak melempar & tetap menghasilkan file sah
for _ in range(5):
    bm.auto_export()
ok = wait_for(lambda: not bm._export_lock.locked())
check("worker selesai tanpa deadlock", ok)

# ── 8. check_restore_on_startup ───────────────────────────────────
print("\n[8] Deteksi restore saat startup")
wipe_saves()
hits = []
bm._restore_check_done = False  # reset guard utk tes
bm.check_restore_on_startup(lambda p, s: hits.append((p, s)))
ok = wait_for(lambda: len(hits) == 1)
check("callback dipanggil (slot kosong + backup ada)", ok)
if hits:
    check("summary berisi level", hits[0][1]["highest_level"] >= 1)

# kedua kalinya: guard mencegah scan ulang
bm.check_restore_on_startup(lambda p, s: hits.append((p, s)))
time.sleep(0.3)
check("tidak jalan dua kali", len(hits) == 1)

# ada save lokal -> tidak ada prompt
bm._restore_check_done = False
make_slot(1)
hits2 = []
bm.check_restore_on_startup(lambda p, s: hits2.append(1))
time.sleep(0.3)
check("tidak prompt kalau ada save lokal", len(hits2) == 0)

# ── 9. Lokasi backup ──────────────────────────────────────────────
print("\n[9] Lokasi backup")
label = bm.backup_location_label()
check("label menunjuk MYSTIC_BACKUP_DIR",
      label.startswith(DOWNLOAD_DIR), label)

# ── Ringkasan ─────────────────────────────────────────────────────
print("\n" + "=" * 62)
print(" HASIL: %d OK, %d FAIL" % (_pass, _fail))
print("=" * 62)

shutil.rmtree(SANDBOX, ignore_errors=True)
sys.exit(1 if _fail else 0)
