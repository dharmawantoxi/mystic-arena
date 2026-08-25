# ================================================================
# mobile/cloud_save.py
# Cloud Save Mystic Arena → backend HTTP/REST yang kamu kontrol.
#
# KENAPA SERVER REST, BUKAN GOOGLE PLAY GAMES?
# --------------------------------------------
# Google Play Games Saved Games WAJIB punya Google Play Console.
# Karena tidak memakai Play Console, cloud save memakai server REST
# sederhana yang dijalankan sendiri:
#     tools/cloud_server/server.py   (Python stdlib, tanpa dependency)
#
# ALUR
# ----
#   1. Game membaca:
#        MYSTIC_CLOUD_URL        -> mis. https://myserver.example.com
#        MYSTIC_CLOUD_API_KEY    -> (opsional) kunci bersama server
#        MYSTIC_CLOUD_PLAYER_ID  -> (opsional) identitas pemain
#   2. Kalau MYSTIC_CLOUD_URL belum diisi, cloud NONAKTIF (ame tetap
#      jalan; save lokal + Android Auto Backup tetap dipakai).
#   3. Identitas pemain:
#        - Android: akun Google utama di HP (via AccountManager).
#        - Desktop/CI: MYSTIC_CLOUD_PLAYER_ID, atau ID stabil yang
#          dibuat otomatis di folder save.
#   4. auto_upload() dipanggil tiap SaveManager.save(); upload dijalankan
#      di thread background supaya game tidak berhenti.
#   5. upload_payload/download_payload dipanggil tombol manual di UI.
#   6. poll() dipanggil tiap frame untuk menyampaikan hasil operasi ke
#      callback UI.
#
# GARANSI KEAMANAN SAVE LOKAL
# ---------------------------
#   - Semua operasi cloud NON-BLOCKING di thread, dan selalu try/except.
#   - Gagal upload/download TIDAK pernah menghapus save lokal.
#   - Payload hanya berisi data save; magic + checksum divalidasi
#     (reuse backup_manager) supaya file rusak ditolak.
# ================================================================

import hashlib
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

CLOUD_MAGIC = "MYSTIC_ARENA_CLOUD"
CLOUD_VERSION = 1

# Bisa dimatikan total: MYSTIC_CLOUD_SAVE=0
_DEFAULT_ENABLED = os.environ.get("MYSTIC_CLOUD_SAVE", "1") != "0"

# Untuk jalur Google (hanya identitas; bukan Play Console)
GOOGLE_ACCOUNT_TYPE = "com.google"


def is_android():
    if "ANDROID_ARGUMENT" in os.environ:
        return True
    if "ANDROID_PRIVATE" in os.environ:
        return True
    return hasattr(sys, "getandroidapilevel")


def _env(name, default=""):
    return (os.environ.get(name, default) or "").strip()


def server_url():
    """Base URL server cloud. Tanpa ini cloud tidak aktif."""
    return _env("MYSTIC_CLOUD_URL").rstrip("/")


def api_key():
    return _env("MYSTIC_CLOUD_API_KEY")


def is_configured():
    return bool(server_url())


def _stable_dir():
    """Folder tempat menyimpan cloud_player_id.txt (stabil antar update)."""
    base = os.environ.get("ANDROID_PRIVATE") or os.getcwd()
    d = os.path.join(base, "saves")
    try:
        os.makedirs(d, exist_ok=True)
        return d
    except Exception:
        return base


def _google_account_email():
    """Akun Google utama di HP (Android) — tanpa Play Console."""
    if not is_android():
        return ""
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        AccountManager = autoclass("android.accounts.AccountManager")
        activity = PythonActivity.mActivity
        mgr = AccountManager.get(activity)
        accounts = mgr.getAccountsByType(GOOGLE_ACCOUNT_TYPE)
        if accounts is not None and len(accounts) > 0:
            email = getattr(accounts[0], "name", None)
            if email:
                return str(email)
    except Exception as exc:
        print("[CLOUD] baca akun Google gagal: %s" % exc)
    return ""


def has_account_permission():
    """Cek izin GET_ACCOUNTS di Android (desktop: True)."""
    if not is_android():
        return True
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        granted = activity.checkSelfPermission(
            "android.permission.GET_ACCOUNTS")
        return int(granted) == 0
    except Exception as exc:
        print("[CLOUD] cek izin akun gagal: %s" % exc)
        return False


def request_account_permission():
    """
    Minta izin GET_ACCOUNTS (dialog sistem). Hasilnya dipakai pada
    pengecekan berikutnya (pemain mengetuk lagi setelah memberi izin).
    Di desktop: False (tidak perlu).
    """
    if not is_android():
        return False
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        activity.requestPermissions(
            ["android.permission.GET_ACCOUNTS"], 4123)
        return True
    except Exception as exc:
        print("[CLOUD] minta izin akun gagal: %s" % exc)
        return False


def player_id():
    """
    Identitas pemain untuk server.
    Prioritas: env MYSTIC_CLOUD_PLAYER_ID > akun Google Android >
    ID stabil lokal (dashboard/test).
    """
    override = _env("MYSTIC_CLOUD_PLAYER_ID")
    if override:
        return override
    gmail = _google_account_email()
    if gmail:
        return "g:" + gmail
    return _stable_fallback_id()


def _stable_fallback_id():
    try:
        path = os.path.join(_stable_dir(), "cloud_player_id.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                value = fh.read().strip()
                if value:
                    return value
        value = "local-" + uuid.uuid4().hex[:12]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(value)
        return value
    except Exception:
        return "local-unknown"


# ================================================================
# HTTP INDEPENDENT (stdlib, dipakai di Android & desktop)
# ================================================================

def _http_request(method, url, body=None, headers=None, timeout=15):
    headers = headers or {}
    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = body
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = getattr(resp, "status", 200)
            content_type = resp.headers.get("Content-Type", "")
            try:
                decoded = raw.decode("utf-8")
            except Exception:
                decoded = raw
            if "json" in content_type and decoded:
                try:
                    return status, json.loads(decoded)
                except Exception:
                    return status, decoded
            return status, decoded
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception as exc:
        return -1, str(exc)


def _headers_for(pid):
    headers = {
        "X-Mystic-Player-Id": pid,
        "Accept": "application/json",
    }
    key = api_key()
    if key:
        headers["X-Mystic-Api-Key"] = key
    return headers


def upload_to_server(payload, pid):
    """
    PUT /api/v1/save dengan body = envelope cloud.
    Return (status, message). status 200/201 = sukses.
    """
    if not server_url():
        return 0, "MYSTIC_CLOUD_URL belum diset"
    envelope = {
        "magic": CLOUD_MAGIC,
        "version": CLOUD_VERSION,
        "exported_at": time.time(),
        "payload": payload,
    }
    url = server_url() + "/api/v1/save"
    status, body = _http_request(
        "PUT", url, body=envelope, headers=_headers_for(pid))
    if status in (200, 201):
        return status, "Save terunggah ke cloud"
    return status, ("Upload gagal (%s): %s" % (status, body
                                               if isinstance(body, str)
                                               else str(body)))


def download_from_server(pid):
    """
    GET /api/v1/save?player_id=<pid>. Return (status, json/payload).
    """
    if not server_url():
        return 0, "MYSTIC_CLOUD_URL belum diset"
    url = server_url() + "/api/v1/save?player_id=" + urllib.parse.quote(pid)
    status, body = _http_request("GET", url, headers=_headers_for(pid))
    if status == 200:
        if isinstance(body, dict):
            return status, body
        try:
            return status, json.loads(body)
        except Exception:
            return 400, "Respons server bukan JSON"
    if status == 404:
        return 404, "Tidak ada save cloud untuk akun ini"
    return status, ("Download gagal (%s): %s" % (status, body))


# ================================================================
# RESULT HELPER
# ================================================================

def _ok_result(kind, message="", payload=None, summary=None, path=None):
    return {
        "ok": True,
        "kind": kind,
        "code": 0,
        "message": message,
        "payload": payload,
        "summary": summary,
        "path": path,
    }


def _err_result(kind, code, message):
    return {
        "ok": False,
        "kind": kind,
        "code": code,
        "message": message,
        "payload": None,
        "summary": None,
        "path": None,
    }


# ================================================================
# CLOUD SAVE MANAGER
# ================================================================

class CloudSaveManager:
    """
    Satu instance global (di-export sebagai `manager` di bawah).

    Operasi upload/download berjalan di thread background; hasilnya
    disimpan di antrean kecil dan disampaikan ke callback oleh poll()
    (dipanggil tiap frame dari Menu.update / main.py).
    """

    def __init__(self, enabled=True):
        self.enabled = bool(enabled)
        self._inited = False
        self._available = False
        self._signed_in = False
        self._pid = ""
        self._url = ""

        self._lock = threading.Lock()
        self._busy = False
        self._pending = []          # (callback, result) menunggu poll
        self._last_auto_ts = 0.0
        self._last_message = "Cloud: belum dikonfigurasi"
        self._last_ok = True

    # ------------------------------------------------------------
    # STATE READERS (untuk UI)
    # ------------------------------------------------------------

    def available(self):
        return bool(self._available)

    def signed_in(self):
        return bool(self._signed_in)

    def busy(self):
        return bool(self._busy)

    def last_message(self):
        return self._last_message

    def last_ok(self):
        return bool(self._last_ok)

    def player_id(self):
        return self._pid

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------

    def start(self):
        """Baca konfigurasi cloud sekali. Tidak pernah crash."""
        if self._inited:
            return self._available
        self._inited = True
        if not self.enabled:
            self._available = False
            self._signed_in = False
            self._last_message = "Cloud dimatikan (MYSTIC_CLOUD_SAVE=0)"
            return False

        self._url = server_url()
        self._pid = player_id()

        if not self._url:
            self._available = False
            self._signed_in = False
            self._last_message = "Cloud: MYSTIC_CLOUD_URL belum diset"
            print("[CLOUD] URL server belum diset — cloud NONAKTIF")
            return False

        if not self._pid:
            self._available = False
            self._signed_in = False
            self._last_message = "Cloud: identitas pemain belum tersedia"
            return False

        self._available = True
        self._signed_in = True
        self._last_message = "Cloud server siap"
        print("[CLOUD] URL=%s player=%s" % (self._url, self._pid))
        return True

    # ------------------------------------------------------------
    # AUTH (server REST: tidak ada dialog; identitas sudah siap)
    # ------------------------------------------------------------

    def check_auth(self, callback=None):
        """Cek konfigurasi + identitas. Tidak memanggil server."""
        if callback:
            if not self._ready():
                callback(_err_result("check", 1, self._last_message))
            else:
                callback(_ok_result("check", "Cloud server siap"))

    def sign_in(self, callback=None):
        """Di server REST tidak ada 'sign-in' dialog; panggil check_auth."""
        self.check_auth(callback)

    def has_account_permission(self):
        return has_account_permission()

    def request_account_permission(self):
        return request_account_permission()

    # ------------------------------------------------------------
    # UPLOAD / DOWNLOAD PAYLOAD
    # ------------------------------------------------------------

    def upload_payload(self, payload, callback=None):
        if not self._ready():
            if callback:
                callback(_err_result("upload", 1, self._last_message))
            return
        if not payload or (not payload.get("slots")
                           and not payload.get("settings")):
            if callback:
                callback(_err_result(
                    "upload", 2, "Tidak ada save untuk diunggah"))
            return
        if self._busy:
            if callback:
                callback(_err_result(
                    "upload", 3, "Operasi cloud lain sedang berjalan"))
            return
        self._set_busy(True)
        self._last_message = "Mengunggah save ke cloud…"
        self._start_thread("upload", payload, callback)

    def download_payload(self, callback=None, apply=False):
        if not self._ready():
            if callback:
                callback(_err_result("download", 1, self._last_message))
            return
        if self._busy:
            if callback:
                callback(_err_result(
                    "download", 3, "Operasi cloud lain sedang berjalan"))
            return
        self._set_busy(True)
        self._last_message = "Mengunduh save dari cloud…"
        self._start_thread("download", {"apply": bool(apply)}, callback)

    def auto_upload(self, callback=None, debounce=8.0):
        """
        Dipanggil SaveManager.save(). Upload di background.
        'debounce' mencegah upload lebih dari 1x per N detik (save
        bisa dipanggil beberapa kali dalam sesi). Manual upload tidak
        dibatasi.
        """
        try:
            if not self._inited:
                self.start()
            if not self._available or self._signed_in is False \
                    or self._busy:
                return False
            now = time.time()
            if debounce > 0 and (now - self._last_auto_ts) < debounce:
                return False
            self._last_auto_ts = now
            import backup_manager as bm
            payload = bm.build_backup_payload()
            if payload is None or (not payload.get("slots")
                                   and not payload.get("settings")):
                return False
            self.upload_payload(payload, callback)
            return True
        except Exception as e:
            print("[CLOUD] auto_upload skipped: %s" % e)
            return False

    # ------------------------------------------------------------
    # POLL
    # ------------------------------------------------------------

    def poll(self):
        """Sampaikan hasil operasi thread ke callback (dari frame game)."""
        with self._lock:
            pending = self._pending
            self._pending = []
        for callback, result in pending:
            if callback:
                try:
                    callback(result)
                except Exception as exc:
                    print("[CLOUD] callback gagal: %s" % exc)

    # ------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------

    def _ready(self):
        if not self._inited:
            self.start()
        return self._available and bool(self._pid)

    def _set_busy(self, value):
        with self._lock:
            self._busy = bool(value)

    def _set_status(self, ok, message):
        self._last_ok = bool(ok)
        self._last_message = message

    def _start_thread(self, kind, payload, callback):
        def worker():
            try:
                if kind == "upload":
                    status, msg = upload_to_server(payload, self._pid)
                    result = (_ok_result("upload", msg)
                              if status in (200, 201)
                              else _err_result("upload", status, msg))
                else:
                    status, body = download_from_server(self._pid)
                    if status != 200:
                        result = _err_result("download", status,
                                             str(body))
                    else:
                        result = self._parse_download(body, payload.get(
                            "apply", False) if isinstance(payload, dict)
                            else False)
                self._set_status(result.get("ok", False),
                                 result.get("message", ""))
            except Exception as exc:
                self._set_status(False, "Cloud gagal: %s" % exc)
                result = _err_result(kind, -2, "Cloud gagal: %s" % exc)
            finally:
                self._set_busy(False)
                with self._lock:
                    self._pending.append((callback, result))

        t = threading.Thread(target=worker, name="mystic-cloud-http",
                             daemon=True)
        t.start()

    def _parse_download(self, body, apply):
        try:
            if not isinstance(body, dict):
                return _err_result("download", 10,
                                   "Respons server bukan JSON")
            if body.get("magic") != CLOUD_MAGIC:
                return _err_result("download", 11,
                                   "Bukan data cloud Mystic Arena")
            if body.get("version", 0) > CLOUD_VERSION:
                return _err_result("download", 12,
                                   "Versi cloud lebih baru dari game")
            payload = body.get("payload")
            if not isinstance(payload, dict):
                return _err_result("download", 13, "Payload cloud rusak")

            import backup_manager as bm
            text = json.dumps(payload, ensure_ascii=False)
            parsed, err = bm.parse_backup_text(text)
            if parsed is None:
                return _err_result("download", 14, err or "Validasi gagal")
            summary = bm.get_backup_summary(parsed)

            if apply:
                ok, apply_err = bm.apply_backup(parsed)
                if not ok:
                    return _err_result("download", 15,
                                       "Terapkan cloud gagal: %s" % apply_err)
                return _ok_result("download", "Cloud restored!",
                                  payload=parsed, summary=summary)
            return _ok_result("download", "Cloud save ditemukan",
                              payload=parsed, summary=summary)
        except Exception as exc:
            return _err_result("download", 16, "Baca cloud gagal: %s" % exc)


# instance global yang dipakai game
manager = CloudSaveManager(enabled=_DEFAULT_ENABLED)
