"""
tools/test_cloud_server_storage.py
Uji logika pemilihan storage server cloud (lokal vs Cloudflare R2).
Tidak perlu boto3 terpasang; pengujian fokus pada deteksi konfigurasi.
Jalankan: python3 tools/test_cloud_server_storage.py
"""

import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "cloud_server"))

import server as srv

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


# ── Bersihkan R2 env ──
for k in ("MYSTIC_CLOUD_R2_ENDPOINT", "MYSTIC_CLOUD_R2_BUCKET",
          "MYSTIC_CLOUD_R2_ACCESS_KEY_ID", "MYSTIC_CLOUD_R2_SECRET_ACCESS_KEY",
          "MYSTIC_CLOUD_R2_PREFIX"):
    os.environ.pop(k, None)


print("== 1. Tanpa R2 -> storage lokal ==")
check("r2_configured False", srv.r2_configured() is False)
check("r2_status local", srv.r2_status() == "local")
# read/write memakai path lokal
tmp = tempfile.mkdtemp()
srv.DATA_DIR = tmp
srv.write_save("a@example.com", '{"magic":"x"}')
check("write lokal membuat file", len(
    [f for f in os.listdir(tmp) if f.endswith(".json")]) == 1)
check("read lokal mengembalikan isi",
      srv.read_save("a@example.com") == '{"magic":"x"}')
check("read lokal miss -> None", srv.read_save("missing@example.com") is None)

print("== 2. Konfigurasi R2 -> status r2 (atau r2-missing-boto3) ==")
os.environ["MYSTIC_CLOUD_R2_ENDPOINT"] = "https://abc.r2.cloudflarestorage.com"
os.environ["MYSTIC_CLOUD_R2_BUCKET"] = "mystic-arena"
os.environ["MYSTIC_CLOUD_R2_ACCESS_KEY_ID"] = "AK0001"
os.environ["MYSTIC_CLOUD_R2_SECRET_ACCESS_KEY"] = "SECRET"
os.environ["MYSTIC_CLOUD_R2_PREFIX"] = "mystic_arena"
# Server membaca env saat import; untuk uji, sinkronkan ke konstanta modul.
srv.R2_ENDPOINT = os.environ["MYSTIC_CLOUD_R2_ENDPOINT"]
srv.R2_BUCKET = os.environ["MYSTIC_CLOUD_R2_BUCKET"]
srv.R2_ACCESS_KEY_ID = os.environ["MYSTIC_CLOUD_R2_ACCESS_KEY_ID"]
srv.R2_SECRET_ACCESS_KEY = os.environ["MYSTIC_CLOUD_R2_SECRET_ACCESS_KEY"]
srv.R2_PREFIX = os.environ["MYSTIC_CLOUD_R2_PREFIX"]
check("r2_configured True", srv.r2_configured() is True)
status = srv.r2_status()
check("status r2 / r2-missing-boto3",
      status in ("r2", "r2-missing-boto3"), status)
key = srv.r2_key("abc@example.com")
check("key R2 berformat json di prefix",
      key.startswith("mystic_arena/") and key.endswith(".json"))

print()
print("HASIL: %d lulus, %d gagal" % (_pass, _fail))
sys.exit(1 if _fail else 0)
