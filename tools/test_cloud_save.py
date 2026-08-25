"""
tools/test_cloud_save.py

Uji Cloud Save (backend HTTP/REST) secara end-to-end TANPA Android dan
TANPA pygame. Test ini menyalakan contoh server
(`tools/cloud_server/server.py`) di localhost, lalu:
  1. memakai CloudSaveManager untuk upload payload,
  2. menghapus save lokal (simulasi ganti HP),
  3. mendownload + apply untuk memulihkan save.

Yang diperiksa
──────────────
  1. Tanpa MYSTIC_CLOUD_URL, cloud NONAKTIF (available=False).
  2. Upload ke server berhasil (callback OK).
  3. Download + apply memulihkan slot + settings (ganti HP).
  4. Download rusak (magic salah) ditolak, save lokal tetap aman.
  5. Auto-upload dipicu jalur SaveManager (non-blocking, no crash).
  6. Server menolak API key salah (kalau key diset).
  7. Identitas lokal stabil (cloud_player_id.txt dibuat sekali).

Jalankan:
    python3 tools/test_cloud_save.py
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time

# ─── Sandbox: cwd + folder temp, SEBELUM import modul game ───
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX = tempfile.mkdtemp(prefix="mystic_cloud_http_test_")
WORK_DIR = os.path.join(SANDBOX, "game")
CLOUD_DATA = os.path.join(SANDBOX, "cloud_data")
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(CLOUD_DATA, exist_ok=True)

# Pastikan tidak dikira Android
os.environ.pop("ANDROID_ARGUMENT", None)
os.environ.pop("ANDROID_PRIVATE", None)
os.environ.setdefault("MYSTIC_CLOUD_PLAYER_ID", "test-player@example.com")

os.chdir(WORK_DIR)  # storage_paths -> SAVE_DIR = "saves" relatif sini
sys.path.insert(0, REPO_ROOT)

import backup_manager as bm  # noqa: E402
import mobile.cloud_save as cs  # noqa: E402

SAVE_DIR = os.path.join(WORK_DIR, "saves")
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


def make_slot(num, level=5, gold=1200):
    os.makedirs(SAVE_DIR, exist_ok=True)
    data = {
        "unlocked_bosses": ["level%d" % i for i in range(1, level)],
        "purchased_heroes": ["knight", "archer"],
        "meta_gold": gold,
        "completed_levels": list(range(1, level + 1)),
        "last_played_level": level,
        "slot_created": time.time() - 86400,
        "slot_last_played": time.time(),
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


SERVER = None
SERVER_THREAD = None


def start_server():
    """Jalankan contoh cloud server di localhost (port bebas)."""
    global SERVER, SERVER_THREAD
    import sys as _sys
    _sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "cloud_server"))
    import server as srv

    srv.DATA_DIR = CLOUD_DATA
    srv.HOST = "127.0.0.1"
    srv.API_KEY = os.environ.get("MYSTIC_CLOUD_API_KEY", "")
    srv.ensure_data_dir()

    SERVER = srv.ThreadingHTTPServer((srv.HOST, 0), srv.Handler)
    port = SERVER.server_address[1]
    SERVER_THREAD = threading.Thread(target=SERVER.serve_forever,
                                     daemon=True)
    SERVER_THREAD.start()
    print("  [server] http://127.0.0.1:%d" % port)
    return "http://127.0.0.1:%d" % port


def stop_server():
    global SERVER, SERVER_THREAD
    if SERVER is not None:
        SERVER.shutdown()
        SERVER.server_close()
        SERVER = None


def fresh_manager(url=None, api_key="", player_id=None):
    """Buat manager baru (state bersih)."""
    if url is None:
        os.environ.pop("MYSTIC_CLOUD_URL", None)
    else:
        os.environ["MYSTIC_CLOUD_URL"] = url
    if api_key:
        os.environ["MYSTIC_CLOUD_API_KEY"] = api_key
    else:
        os.environ.pop("MYSTIC_CLOUD_API_KEY", None)
    if player_id:
        os.environ["MYSTIC_CLOUD_PLAYER_ID"] = player_id
    else:
        os.environ.pop("MYSTIC_CLOUD_PLAYER_ID", None)
    m = cs.CloudSaveManager(enabled=True)
    return m


def wait_result(manager, holder, timeout=10.0):
    """Poll sampai callback (holder) diisi, lalu kembalikan hasil."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        manager.poll()
        if holder:
            return holder[-1]
        time.sleep(0.05)
    return None


print("== 1. Tanpa URL: cloud NONAKTIF ==")
m0 = fresh_manager(url=None)
ok0 = m0.start()
check("start() False tanpa URL", ok0 is False)
check("available() False", m0.available() is False)
check("auto_upload() aman", m0.auto_upload() is False)

print("== 2. Server hidup + upload ==")
stop_server()
base = start_server()
m1 = fresh_manager(url=base, player_id="test-player@example.com")
ok1 = m1.start()
check("start() True setelah URL", ok1 is True)
check("available() True", m1.available() is True)
check("signed_in() True", m1.signed_in() is True)
make_slot(1, level=5, gold=1200)
make_slot(2)
make_slot(3)
make_settings()
payload = bm.build_backup_payload()
results1 = []
m1.upload_payload(payload, results1.append)
res1 = wait_result(m1, results1)
check("upload callback OK", res1 is not None and res1.get("ok") is True)
stored = os.listdir(CLOUD_DATA)
check("file server ada", len([f for f in stored if f.endswith(".json")]) >= 1)

print("== 3. Download + apply (simulasi ganti HP) ==")
m2 = fresh_manager(url=base, player_id="test-player@example.com")
wipe_saves()
make_settings()
m2.start()
results2 = []
m2.download_payload(results2.append, apply=True)
res2 = wait_result(m2, results2)
check("download callback OK", res2 is not None and res2.get("ok") is True)
check("slot_1 pulih", os.path.exists(os.path.join(SAVE_DIR, "slot_1.json")))
with open(os.path.join(SAVE_DIR, "slot_1.json"), "r") as fh:
    restored = json.load(fh)
check("meta_gold pulih", restored.get("meta_gold") == 1200)

print("== 4. Data rusak di server ditolak, save lokal aman ==")
m3 = fresh_manager(url=base, player_id="bad-player@example.com")
make_slot(1, level=3, gold=777)
m3.start()
# Tulis payload rusak langsung ke server (memakai path hash dari server)
import hashlib as _hash
bad_file = os.path.join(
    CLOUD_DATA, "%s.json" % _hash.sha256(
        ("bad-player@example.com" or "").lower().encode()).hexdigest())
with open(bad_file, "w", encoding="utf-8") as fh:
    json.dump({"magic": "BUKAN_CLOUD", "version": 1, "payload": {}}, fh)
results3 = []
m3.download_payload(results3.append, apply=True)
res3 = wait_result(m3, results3)
check("download rusak ditolak",
      res3 is not None and not res3.get("ok"))
with open(os.path.join(SAVE_DIR, "slot_1.json"), "r") as fh:
    kept = json.load(fh)
check("save lokal tetap aman", kept.get("meta_gold") == 777)

print("== 5. Auto-upload via jalur SaveManager ==")
m4 = fresh_manager(url=base, player_id="test-player@example.com")
m4.start()
make_slot(1, level=2, gold=350)
triggered = m4.auto_upload(debounce=0)
check("auto_upload trigger", triggered is True)
# tunggu sampai selesai
for _ in range(200):
    m4.poll()
    if not m4.busy():
        break
    time.sleep(0.05)
# setelah auto-upload selesai, tidak crash; verify status terakhir ok
check("auto-upload status OK", m4.last_ok() is True)

print("== 6. API key salah ditolak server ==")
stop_server()
os.environ["MYSTIC_CLOUD_API_KEY"] = "secret-key-123"
base6 = start_server()
# Server dibuat dengan API_KEY dari env (secret-key-123); kirim tanpa key
m6 = fresh_manager(url=base6, player_id="test-key@example.com")
m6.start()
make_slot(1, level=1, gold=1)
results6 = []
m6.upload_payload(bm.build_backup_payload(), results6.append)
res6 = wait_result(m6, results6)
check("upload tanpa key ditolak",
      res6 is not None and not res6.get("ok"))

print("== 7. Identitas lokal stabil (desktop) ==")
# Tanpa override & tanpa Google account (desktop) -> ID file dibuat.
os.environ.pop("MYSTIC_CLOUD_PLAYER_ID", None)
m7 = cs.CloudSaveManager(enabled=True)
m7._inited = False
# paksa tidak google account pada desktop
m7.start()
pid7 = m7.player_id()
check("player_id terbentuk", bool(pid7))
check("player_id stabil file", os.path.exists(
    os.path.join(SAVE_DIR, "cloud_player_id.txt")))

stop_server()
print()
print("HASIL: %d lulus, %d gagal" % (_pass, _fail))
sys.exit(1 if _fail else 0)
