#!/usr/bin/env python3
# ================================================================
# tools/cloud_server/server.py
# Contoh server Cloud Save untuk Mystic Arena.
#
# STORAGE
# -------
#   Lokal (default)  : <data_dir>/<sha256(player_id)>.json
#                      Cukup untuk PC/VPS. Di Render Free ini
#                      TIDAK awet (filesystem ephemeral).
#   Cloudflare R2    : (disarankan di Render Free) file disimpan ke
#                      bucket R2 via S3 API. Walau Render restart /
#                      redeploy, save tidak hilang.
#                      Aktifkan dengan env:
#                        MYSTIC_CLOUD_R2_* (lihat bawah).
#                      Butuh: pip install boto3 (optional; tanpa R2
#                      server tetap jalan tanpa dependency).
#
# Endpoint
# --------
#   GET  /health                        -> cek server hidup
#   PUT  /api/v1/save                   -> simpan cloud save (body =
#                                         envelope cloud dari game)
#   GET  /api/v1/save?player_id=<id>    -> ambil cloud save
#
# Header yang dikirim game:
#   X-Mystic-Player-Id: <identitas pemain (mis. akun Google)>
#   X-Mystic-Api-Key:   <kunci bersama — diwajibkan kalau diset>
#
# Konfigurasi via environment:
#   HOST                                default 0.0.0.0
#   PORT                                default 8080 (Render/Railway isi sendiri)
#   MYSTIC_CLOUD_DATA_DIR               default ./cloud_data (storage lokal)
#   MYSTIC_CLOUD_API_KEY                (opsional) kunci bersama
#   MYSTIC_CLOUD_R2_ENDPOINT            mis. https://<accountid>.r2.cloudflarestorage.com
#   MYSTIC_CLOUD_R2_BUCKET              nama bucket R2
#   MYSTIC_CLOUD_R2_ACCESS_KEY_ID       Access Key ID R2 (S3 credentials)
#   MYSTIC_CLOUD_R2_SECRET_ACCESS_KEY   Secret Access Key R2
#   MYSTIC_CLOUD_R2_PREFIX              (opsional) prefix object, default "mystic_arena"
#
# Menjalankan:
#   python3 tools/cloud_server/server.py
#   # lalu dari game/terminal:
#   MYSTIC_CLOUD_URL=http://<host>:8080 python main.py
# ================================================================

import hashlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
DATA_DIR = os.environ.get("MYSTIC_CLOUD_DATA_DIR", "./cloud_data")
API_KEY = (os.environ.get("MYSTIC_CLOUD_API_KEY") or "").strip()

# ── Cloudflare R2 (S3 compatible) ──────────────────────────────
R2_ENDPOINT = (os.environ.get("MYSTIC_CLOUD_R2_ENDPOINT") or "").strip().rstrip("/")
R2_BUCKET = (os.environ.get("MYSTIC_CLOUD_R2_BUCKET") or "").strip()
R2_ACCESS_KEY_ID = (os.environ.get("MYSTIC_CLOUD_R2_ACCESS_KEY_ID") or "").strip()
R2_SECRET_ACCESS_KEY = (os.environ.get("MYSTIC_CLOUD_R2_SECRET_ACCESS_KEY") or "").strip()
R2_PREFIX = (os.environ.get("MYSTIC_CLOUD_R2_PREFIX") or "mystic_arena").strip()


def r2_configured():
    return bool(R2_ENDPOINT and R2_BUCKET and R2_ACCESS_KEY_ID
                and R2_SECRET_ACCESS_KEY)


def r2_status():
    if not r2_configured():
        return "local"
    try:
        import boto3  # noqa: F401
        return "r2"
    except Exception:
        return "r2-missing-boto3"


_r2_client = None


def r2_client():
    """Buat klien boto3 untuk R2 (region_name='auto' wajib)."""
    global _r2_client
    if _r2_client is not None:
        return _r2_client
    import boto3
    _r2_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    return _r2_client


def r2_key(player_id):
    sanitized = player_id.lower().strip()
    digest = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()
    return "%s/%s.json" % (R2_PREFIX, digest)


def r2_read(player_id):
    try:
        obj = r2_client().get_object(
            Bucket=R2_BUCKET, Key=r2_key(player_id))
        return obj["Body"].read().decode("utf-8", "replace")
    except Exception as exc:
        # 404 / NoSuchKey = belum ada save.
        code = str(getattr(exc, "response", {}).get(
            "Error", {}).get("Code", ""))
        if code in ("NoSuchKey", "404", "NotFound"):
            return None
        raise


def r2_write(player_id, body_text):
    try:
        r2_client().put_object(
            Bucket=R2_BUCKET,
            Key=r2_key(player_id),
            Body=body_text.encode("utf-8"),
            ContentType="application/json",
        )
    except Exception as exc:
        raise


# ── helper lokal ───────────────────────────────────────────────

def ensure_data_dir():
    if not r2_configured():
        os.makedirs(DATA_DIR, exist_ok=True)


def filename_for(player_id):
    sanitized = player_id.lower().strip()
    return os.path.join(DATA_DIR,
                        hashlib.sha256(sanitized.encode("utf-8")).hexdigest()
                        + ".json")


def read_save(player_id):
    if r2_configured():
        return r2_read(player_id)
    path = filename_for(player_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_save(player_id, body_text):
    if r2_configured():
        r2_write(player_id, body_text)
        return r2_key(player_id)
    path = filename_for(player_id)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(body_text)
    if os.path.exists(path):
        os.replace(tmp, path)
    else:
        os.rename(tmp, path)
    return path


class Handler(BaseHTTPRequestHandler):
    server_version = "MysticCloudServer/1.0"

    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        # Endpoint native tidak butuh preflight, tapi biar aman.
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, X-Mystic-Player-Id, X-Mystic-Api-Key")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status, obj):
        self._send(status, json.dumps(obj, ensure_ascii=False))

    def _allowed(self):
        if not API_KEY:
            return True
        return self.headers.get("X-Mystic-Api-Key", "") == API_KEY

    def _player_id(self):
        pid = (self.headers.get("X-Mystic-Player-Id", "")
               or self._get_query_param("player_id") or "").strip()
        if not pid:
            return ""
        return pid

    def _get_query_param(self, name):
        from urllib.parse import parse_qs, urlsplit
        qs = parse_qs(urlsplit(self.path).query)
        vals = qs.get(name, [])
        return vals[0] if vals else ""

    def _parse_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return ""
        return self.rfile.read(length).decode("utf-8", "replace")

    # ------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------

    def do_GET(self):
        if self.path.startswith("/health") or self.path == "/":
            self._send_json(200, {
                "ok": True,
                "service": "mystic-arena-cloud-server",
                "version": 1,
                "storage": r2_status(),
                "data_dir": DATA_DIR,
                "auth": bool(API_KEY),
            })
            return

        if self.path.startswith("/api/v1/save"):
            if not self._allowed():
                self._send_json(403, {"ok": False,
                                      "error": "api key salah"})
                return
            pid = self._player_id()
            if not pid:
                self._send_json(400, {"ok": False,
                                      "error": "player_id kosong"})
                return
            try:
                text = read_save(pid)
            except Exception as exc:
                print("[CLOUD] read R2 gagal: %s" % exc)
                self._send_json(500, {"ok": False,
                                      "error": "baca storage gagal"})
                return
            if text is None:
                self._send_json(404, {"ok": False,
                                      "error": "save tidak ditemukan"})
                return
            self._send(200, text, "application/json")
            return

        self._send_json(404, {"ok": False, "error": "not found"})

    def do_PUT(self):
        if not self.path.startswith("/api/v1/save"):
            self._send_json(404, {"ok": False, "error": "not found"})
            return
        if not self._allowed():
            self._send_json(403, {"ok": False, "error": "api key salah"})
            return
        pid = self._player_id()
        if not pid:
            self._send_json(400, {"ok": False, "error": "player_id kosong"})
            return
        body = self._parse_body()
        if not body:
            self._send_json(400, {"ok": False, "error": "body kosong"})
            return
        # Validasi minimal: harus JSON.
        try:
            payload = json.loads(body)
        except Exception:
            self._send_json(400, {"ok": False,
                                  "error": "body bukan JSON valid"})
            return
        # Ambil tanggal dari envelope supaya mudah diperiksa manual.
        exported = payload.get("exported_at", 0) if isinstance(
            payload, dict) else 0
        try:
            dest = write_save(pid, body)
        except Exception as exc:
            print("[CLOUD] write storage gagal: %s" % exc)
            self._send_json(500, {"ok": False,
                                  "error": "simpan storage gagal"})
            return
        print("[CLOUD] save %s -> %s (%d bytes)" % (
            pid[:40], dest, len(body)))
        self._send_json(200, {"ok": True, "exported_at": exported})

    def log_message(self, fmt, *args):
        # Kurangi spam log ke terminal; tetap tampilkan request penting.
        if "/health" in fmt % args:
            return
        print("[CLOUD] %s" % (fmt % args))


def main():
    ensure_data_dir()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    storage = r2_status()
    print("=" * 60)
    print("  MYSTIC ARENA CLOUD SAVE SERVER")
    if storage == "r2":
        print("  storage  : CLOUDFLARE R2 (%s/%s)" % (R2_ENDPOINT, R2_BUCKET))
    elif storage == "r2-missing-boto3":
        print("  storage  : LOCAL (R2 dikonfigurasi tapi boto3 belum "
              "terpasang — pip install boto3)")
    else:
        print("  storage  : LOCAL (%s)" % os.path.abspath(DATA_DIR))
    print("  auth     : %s" % ("API key" if API_KEY else "TANPA AUTH (uji lokal)"))
    print("  listen   : http://%s:%s" % (HOST, PORT))
    print("  health   : http://%s:%s/health" % (HOST, PORT))
    print("=" * 60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[CLOUD] server berhenti")
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
