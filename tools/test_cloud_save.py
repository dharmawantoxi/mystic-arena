"""
tools/test_cloud_save.py

Uji modul mobile/cloud_save.py TANPA perangkat Android dan TANPA
pygame — memakai bridge palsu (FakeBridge) supaya alur upload/download
yang asinkron lewat status file bisa diverifikasi di desktop/CI.

Yang diperiksa
──────────────
  1. Di desktop, CloudSaveManager disabled dengan aman (available=False,
     auto_upload tidak crash).
  2. upload_payload: mengirim file temp ke bridge, status selesai
     diproses oleh poll(), callback dapat hasil OK, file temp dihapus.
  3. download_payload(apply=True): file yang diunduh dibungkus ulang,
     divalidasi magic/checksum, lalu apply_payload() memulihkan slot +
     settings lokal.
  4. download dengan envelope rusak (magic salah) ditolak, callback
     error, save lokal tidak terhapus.
  5. Dua operasi bersamaan: operasi kedua ditolak (busy) tanpa crash.

Jalankan:
    python3 tools/test_cloud_save.py
"""

import json
import os
import shutil
import sys
import tempfile
import time

# ─── Sandbox: cwd + folder temp, SEBELUM import modul game ───
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX = tempfile.mkdtemp(prefix="mystic_cloud_test_")
WORK_DIR = os.path.join(SANDBOX, "game")
CLOUD_DIR = os.path.join(SANDBOX, "cloud")
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(CLOUD_DIR, exist_ok=True)

# Pastikan tidak dikira Android
os.environ.pop("ANDROID_ARGUMENT", None)
os.environ.pop("ANDROID_PRIVATE", None)
# Save lokal diarahkan ke sandbox (bukan ke repo) walau cwd berubah.
os.environ["MYSTIC_SAVE_DIR"] = os.path.join(WORK_DIR, "saves")

os.chdir(WORK_DIR)  # storage_paths -> SAVE_DIR mengikuti MYSTIC_SAVE_DIR
sys.path.insert(0, REPO_ROOT)

import mobile.cloud_save as cs  # noqa: E402

SAVE_DIR = os.path.join(WORK_DIR, "saves")
m = cs.manager

# Arahkan semua file sementara cloud ke sandbox (bukan /tmp).
cs.work_dir = lambda: CLOUD_DIR

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


def wipe_cloud():
    shutil.rmtree(CLOUD_DIR, ignore_errors=True)
    os.makedirs(CLOUD_DIR, exist_ok=True)


class FakeBridge:
    """Meniru _AndroidBridge (pyjnius) untuk pengujian."""

    def __init__(self):
        self._status = None
        self._signed = True
        self._available = True
        self.upload_calls = []
        self.download_calls = []
        self._last_op = None

    def init(self):
        return self._available

    def is_signed_in(self):
        return self._signed

    def upload(self, src, op_id):
        self.upload_calls.append((src, op_id))
        self._last_op = op_id

    def download(self, dst, op_id):
        self.download_calls.append((dst, op_id))
        self._last_op = op_id

    def check_auth(self, op_id):
        self._last_op = op_id

    def sign_in(self, op_id):
        self._last_op = op_id

    def read_status(self):
        return self._status

    def complete(self, ok=True, code=0, message="ok", file_path=""):
        self._status = {
            "op_id": self._last_op,
            "kind": "op",
            "ok": ok,
            "code": code,
            "message": message,
            "file_path": file_path or "",
            "signed_in": self._signed,
            "ts": time.time(),
        }


def fresh_ready():
    wipe_saves()
    wipe_cloud()
    cs.manager._seen_ops = set()
    fake = FakeBridge()
    cs.manager._bridge = fake
    cs.manager._inited = True
    cs.manager._available = True
    cs.manager._signed_in = True
    cs.manager._busy = False
    cs.manager._op_id = None
    cs.manager._op_kind = None
    cs.manager._op_callback = None
    cs.manager._op_aux = None
    return fake


print("== 1. Desktop: cloud nonaktif, tidak crash ==")
wipe_saves()
wipe_cloud()
cs.manager._bridge = None
cs.manager._inited = False
cs.manager._available = False
cs.manager._signed_in = False
cs.manager.enabled = True
started = cs.manager.start()
check("start() di desktop tidak aktif", started is False)
check("available() False", cs.manager.available() is False)
check("auto_upload() aman (return False)",
      cs.manager.auto_upload() is False)

print("== 2. upload_payload + poll ==")
fresh = fresh_ready()
make_slot(1)
make_slot(2)
make_slot(3)
make_settings()
payload = cs.build_payload()
results = []
f1 = fresh_ready()
cs.manager.upload_payload(payload, results.append)
check("upload_payload mengirim ke bridge", len(f1.upload_calls) == 1)
check("busy selama operasi", cs.manager.busy() is True)
f1.complete(True, 0, "Save terunggah ke cloud")
cs.manager.poll()
check("callback upload sukses", results and results[-1].get("ok") is True)
check("busy selesai", cs.manager.busy() is False)
upload_file = f1.upload_calls[0][0]
check("file temp upload dihapus", not os.path.exists(upload_file))

print("== 3. download_payload(apply=True) memulihkan save ==")
f2 = fresh_ready()
# Bangun payload cloud DARI save yang ada, lalu hapus save lokal
# untuk simulasi ganti HP.
make_slot(1, level=5, gold=1200)
make_slot(2)
make_slot(3)
make_settings()
cloud_payload = cs.build_payload()
wipe_saves()
make_settings()       # settings lokal masih ada; apply menimpanya
env = {"magic": "MYSTIC_ARENA_CLOUD", "version": 1,
       "exported_at": time.time(), "payload": cloud_payload}
results2 = []
cs.manager.download_payload(results2.append, apply=True)
dst = f2.download_calls[0][0]
with open(dst, "w", encoding="utf-8") as f:
    json.dump(env, f)
f2.complete(True, 0, "Save diunduh dari cloud", file_path=dst)
cs.manager.poll()
check("callback download sukses",
      results2 and results2[-1].get("ok") is True)
check("slot lokal pulih (slot_1 ada)",
      os.path.exists(os.path.join(SAVE_DIR, "slot_1.json")))
with open(os.path.join(SAVE_DIR, "slot_1.json")) as f:
    restored = json.load(f)
check("meta_gold pulih dari cloud", restored.get("meta_gold") == 1200)

print("== 4. Ensop rusak ditolak, save lokal tetap aman ==")
f3 = fresh_ready()
wipe_saves()
make_slot(1, level=3, gold=777)
bad_env = {"magic": "BUKAN_CLOUD", "version": 1, "payload": {}}
results3 = []
cs.manager.download_payload(results3.append, apply=True)
dst3 = f3.download_calls[0][0]
with open(dst3, "w", encoding="utf-8") as f:
    json.dump(bad_env, f)
f3.complete(True, 0, "Save diunduh dari cloud", file_path=dst3)
cs.manager.poll()
check("callback download error (magic salah)",
      results3 and not results3[-1].get("ok"))
with open(os.path.join(SAVE_DIR, "slot_1.json")) as f:
    kept = json.load(f)
check("save lokal TIDAK terhapus oleh cloud rusak",
      kept.get("meta_gold") == 777)

print("== 5. Dua operasi bersamaan ditolak (busy) ==")
fresh_ready()
wipe_saves()
make_slot(1)
p2 = {"slots": {"1": json.load(open(
    os.path.join(SAVE_DIR, "slot_1.json")))}, "settings": {}}
cs.manager._busy = False
results_a = []
results_b = []
cs.manager.upload_payload(p2, results_a.append)
cs.manager.upload_payload(p2, results_b.append)
check("operasi kedua ditolak (busy)",
      results_b and not results_b[-1].get("ok"))


print("== 6. auto_upload() memakai jalur yang sama ==")
f6 = fresh_ready()
wipe_saves()
make_slot(1, level=2, gold=350)
results6 = []
triggered = cs.manager.auto_upload(results6.append)
check("auto_upload mengirim ke bridge", triggered is True
      and len(f6.upload_calls) == 1)
f6.complete(True, 0, "Save terunggah ke cloud")
cs.manager.poll()
check("callback auto_upload sukses",
      results6 and results6[-1].get("ok") is True)

print("== 7. sign_in + poll memperbarui status masuk ==")
f7 = fresh_ready()
cs.manager._signed_in = False
results7 = []
cs.manager.sign_in(results7.append)
f7._signed = True
f7.complete(True, 0, "Berhasil masuk")
cs.manager.poll()
check("callback sign-in sukses", results7 and results7[-1].get("ok") is True)
check("signed_in diperbarui", cs.manager.signed_in() is True)


print()
print("HASIL: %d lulus, %d gagal" % (_pass, _fail))
sys.exit(1 if _fail else 0)
