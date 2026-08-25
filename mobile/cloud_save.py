# ================================================================
# mobile/cloud_save.py
# Cloud Save Mystic Arena → Google Play Games Saved Games (Snapshots).
#
# ARSITEKTUR
# ----------
#   Python (modul ini)  <-- file-->  Java CloudSaveBridge  →  Play Games v2
#
#   * Python tidak perlu meng-implementasikan interface Java.
#   * Java menulis hasil setiap operasi ke:
#         <workdir>/cloud_status.json
#     Python mem-poll file itu saat frame game (murah, <1 KB).
#   * File save sementara (upload/download) juga ditaruh di <workdir>.
#
# PERILAKU
# --------
#   Modul ini ADALAH satu-satunya fitur save/restore pemain. Slot save
#   lokal (slot_*.json) hanya dipakai sebagai working copy sementara —
#   sumber kebenaran progres ada di Google Play Games Saved Games.
#   1. start()  : init bridge Android. Kalau Play Games / APP_ID belum
#      siap, fitur dianggap NONAKTIF (game tetap jalan dengan working
#      copy lokal; tidak ada save cloud baru).
#   2. check_auth(): cek apakah pemain sudah masuk Play Games
#      (v2 melakukan sign-in otomatis saat game diluncurkan).
#   3. auto_upload(): dipanggil setiap SaveManager.save() (dipicu dari
#      _system.py) — non-blocking, hanya jalan kalau sudah masuk.
#   4. download_payload()/upload_payload(): tombol manual di Settings.
#   5. poll(): baca status dari bridge; harus dipanggil dari frame
#      game (Menu.update) supaya callback/percobaan cloud jalan.
#
# TANPA ANDROID / TANPA GOOGLE PLAY GAMES -> semua metode jadi no-op
# yang aman dan tidak pernah melempar exception. Working copy lokal
# tidak akan pernah dirusak oleh fitur ini.
# ================================================================

import hashlib
import json
import os
import sys
import tempfile
import threading
import time
import uuid

import storage_paths

CLOUD_MAGIC = "MYSTIC_ARENA_CLOUD"
CLOUD_VERSION = 1

SNAPSHOT_NAME = "mystic_arena_main"
STATUS_FILENAME = "cloud_status.json"
BRIDGE_CLASS = "io.github.dharmawantoxi.mysticarena.CloudSaveBridge"

# Bisa dimatikan total: MYSTIC_CLOUD_SAVE=0
_DEFAULT_ENABLED = os.environ.get("MYSTIC_CLOUD_SAVE", "1") != "0"


def is_android():
    if "ANDROID_ARGUMENT" in os.environ:
        return True
    if "ANDROID_PRIVATE" in os.environ:
        return True
    return hasattr(sys, "getandroidapilevel")


def work_dir():
    """Folder boleh-tulis untuk status file + file sementara cloud.

    Di Android: <ANDROID_PRIVATE>/cloud_save (di luar folder 'app'
    hasil ekstrak p4a, jadi selamat dari update).
    Di desktop: folder temp — hanya dipakai untuk uji.
    """
    base = os.environ.get("ANDROID_PRIVATE") or tempfile.gettempdir()
    d = os.path.join(base, "mystic_cloud")
    try:
        os.makedirs(d, exist_ok=True)
        return d
    except Exception:
        return base


def status_file():
    return os.path.join(work_dir(), STATUS_FILENAME)


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


# ================================================================
# BRIDGE ANDROID (pyjnius)
# ================================================================

class _AndroidBridge:
    """Pembungkus tipis di atas CloudSaveBridge.java (pyjnius)."""

    def __init__(self):
        self._bridge = None
        self._activity = None
        self._workdir = None

    def init(self):
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        self._activity = PythonActivity.mActivity
        bridge = autoclass(BRIDGE_CLASS)
        self._bridge = bridge
        self._workdir = work_dir()
        bridge.init(self._activity, self._workdir)
        # Tersedia hanya kalau kelas ada DAN Play Games benar-benar
        # berhasil diinisialisasi (APP_ID & Play Services tersedia).
        available = bool(bridge.isAvailable())
        initialized = False
        try:
            initialized = bool(bridge.isInitialized())
        except Exception:
            pass
        return bool(available and initialized)

    def is_signed_in(self):
        try:
            return bool(self._bridge.isSignedIn())
        except Exception:
            return False

    def check_auth(self, op_id):
        self._bridge.checkAuthAsync(op_id)

    def sign_in(self, op_id):
        self._bridge.signInAsync(op_id)

    def upload(self, src_path, op_id):
        self._bridge.uploadAsync(src_path, op_id)

    def download(self, dst_path, op_id):
        self._bridge.downloadAsync(dst_path, op_id)

    def read_status(self):
        return _read_json(status_file())


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
# PAYLOAD SAVE (working copy lokal <-> cloud)
#
# Payload berisi SEMUA slot save + settings dalam satu dict, dengan
# checksum sha256. Magic-nya sengaja dipertahankan sebagai
# "MYSTIC_ARENA_BACKUP" (bukan diganti) supaya snapshot cloud yang
# sudah pernah diunggah oleh versi lama tetap bisa dipulihkan.
# ================================================================

PAYLOAD_MAGIC = "MYSTIC_ARENA_BACKUP"  # dijaga untuk kompatibilitas
PAYLOAD_VERSION = 1
NUM_SLOTS = 3  # sinkron dengan _system.SaveManager.NUM_SLOTS


def _save_dir():
    # Dibaca dinamis supaya tes bisa mengganti storage_paths.SAVE_DIR
    # tanpa reload modul ini.
    return storage_paths.SAVE_DIR


def _slot_file(slot_num):
    return os.path.join(_save_dir(), "slot_%d.json" % slot_num)


def _settings_file():
    return os.path.join(_save_dir(), "settings.json")


def _read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def all_slots_empty():
    """True kalau TIDAK ADA satu pun slot save (indikasi install ulang)."""
    for i in range(1, NUM_SLOTS + 1):
        if os.path.exists(_slot_file(i)):
            return False
    return True


def compute_checksum(payload):
    """sha256 dari JSON kanonis payload TANPA field 'checksum'."""
    body = {k: v for k, v in payload.items() if k != "checksum"}
    canonical = json.dumps(body, sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_payload():
    """
    Kumpulkan semua slot + settings jadi satu payload untuk diunggah.
    Return None kalau tidak ada satu pun slot terisi.
    """
    slots = {}
    for i in range(1, NUM_SLOTS + 1):
        path = _slot_file(i)
        if not os.path.exists(path):
            continue
        try:
            slots[str(i)] = _read_json(path)
        except Exception as e:
            # Slot korup dilewati; jangan gagalkan seluruh payload.
            print("[CLOUD] Slot %d unreadable, skipped: %s" % (i, e))

    if not slots:
        return None

    settings = {}
    try:
        if os.path.exists(_settings_file()):
            settings = _read_json(_settings_file())
    except Exception as e:
        print("[CLOUD] Settings unreadable, skipped: %s" % e)

    payload = {
        "magic": PAYLOAD_MAGIC,
        "version": PAYLOAD_VERSION,
        "exported_at": time.time(),
        "slots": slots,
        "settings": settings,
    }
    payload["checksum"] = compute_checksum(payload)
    return payload


def parse_payload(text):
    """
    Parse + validasi payload cloud.
    Return (payload, None) kalau sah, (None, pesan_error) kalau tidak.
    """
    try:
        payload = json.loads(text)
    except Exception:
        return None, "File corrupt (not valid JSON)"

    if not isinstance(payload, dict):
        return None, "File corrupt (unexpected structure)"
    if payload.get("magic") != PAYLOAD_MAGIC:
        return None, "Not a Mystic Arena save file"
    try:
        version = int(payload.get("version", 0))
    except Exception:
        return None, "File corrupt (bad version)"
    if version < 1 or version > PAYLOAD_VERSION:
        return None, "Save version %s not supported" % version
    if not isinstance(payload.get("slots"), dict) or \
            not payload["slots"]:
        return None, "Save contains no data"
    if payload.get("checksum") != compute_checksum(payload):
        return None, "File corrupt (checksum mismatch)"
    return payload, None


def get_payload_summary(payload):
    """
    Ringkasan untuk dialog konfirmasi:
    level tertinggi, gold terbanyak, tanggal export, jumlah slot.
    """
    highest_level = 0
    best_gold = 0
    newest_played = 0.0
    for data in payload.get("slots", {}).values():
        try:
            completed = data.get("completed_levels", []) or []
            if completed:
                highest_level = max(highest_level, max(completed))
            best_gold = max(best_gold, int(data.get("meta_gold", 0)))
            newest_played = max(
                newest_played,
                float(data.get("slot_last_played", 0) or 0))
        except Exception:
            continue

    exported_at = float(payload.get("exported_at", 0) or 0)
    try:
        date_str = time.strftime("%d %b %Y %H:%M",
                                 time.localtime(exported_at))
    except Exception:
        date_str = "?"

    return {
        "highest_level": highest_level,
        "meta_gold": best_gold,
        "slot_count": len(payload.get("slots", {})),
        "exported_at": exported_at,
        "exported_at_str": date_str,
        "newest_played": newest_played,
    }


def apply_payload(payload):
    """
    Pulihkan SEMUA slot + settings dari payload (payload diasumsikan
    sudah lolos parse_payload). Menimpa working copy lokal.
    Return (ok, error_msg).
    """
    try:
        save_dir = _save_dir()
        os.makedirs(save_dir, exist_ok=True)

        for i in range(1, NUM_SLOTS + 1):
            slot_data = payload.get("slots", {}).get(str(i))
            path = _slot_file(i)
            if slot_data is None:
                # Slot kosong di cloud -> kosongkan juga di lokal
                # supaya hasil restore = kondisi saat upload.
                if os.path.exists(path):
                    os.remove(path)
                continue
            tmp = path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(slot_data, f, indent=2)
            os.replace(tmp, path)

        settings = payload.get("settings") or {}
        if settings:
            tmp = _settings_file() + ".tmp"
            with open(tmp, "w") as f:
                json.dump(settings, f, indent=2)
            os.replace(tmp, _settings_file())

        _reload_runtime_settings()
        print("[CLOUD] Restore selesai (%d slot)"
              % len(payload.get("slots", {})))
        return True, None
    except Exception as e:
        print("[CLOUD] Restore gagal: %s" % e)
        return False, str(e)


def _reload_runtime_settings():
    """
    Setelah settings.json ditimpa, muat ulang singleton GameSettings
    dan sinkronkan volume ke SoundManager. Best-effort: kalau game
    belum memuat modul-modul itu (mis. saat tes CLI), lewati saja.
    """
    try:
        from game_settings import GameSettings
        s = GameSettings()
        s._load()
    except Exception:
        return
    try:
        from sound_manager import SoundManager
        sm = SoundManager()
        sm.sfx_volume = s.sfx_volume
        sm.bgm_volume = s.bgm_volume
        sm.voice_volume = s.voice_volume
        sm.set_master_volume(s.master_volume)
        sm.update_bgm_volume()
    except Exception:
        pass


# ================================================================
# CLOUD SAVE MANAGER
# ================================================================

class CloudSaveManager:
    """
    Satu instance global (di-export sebagai `manager` di bawah).

    Semua operasi berjalan asinkron lewat Java (Task Play Games);
    Python hanya mengirim perintah dan menunggu `poll()` menyelesaikan
    operasi yang sedang berjalan.
    """

    def __init__(self, enabled=True):
        self.enabled = bool(enabled)
        self._inited = False
        self._available = False
        self._signed_in = False

        self._bridge = _AndroidBridge() if is_android() else None
        self._lock = threading.Lock()

        # operasi yang sedang berjalan (maksimum 1)
        self._busy = False
        self._op_id = None
        self._op_kind = None
        self._op_callback = None
        self._op_aux = None

        # status ops yang sudah diproses (anti double-poll)
        self._seen_ops = set()

        # pesan terakhir untuk UI
        self._last_message = "Cloud save: siap digunakan di Android"
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

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------

    def start(self):
        """Init bridge Android sekali. Tidak pernah melempar exception."""
        if self._inited:
            return self._available
        self._inited = True
        if not self.enabled:
            self._available = False
            self._set_status(True, "Cloud save dimatikan (MYSTIC_CLOUD_SAVE=0)")
            return False
        if self._bridge is None:
            self._available = False
            self._set_status(True, "Cloud save: hanya aktif di Android")
            return False
        try:
            ok = self._bridge.init()
            self._available = bool(ok)
            self._signed_in = bool(
                self._bridge.is_signed_in()) if ok else False
            if ok:
                self._set_status(
                    True, "Cloud save siap (Google Play Games)")
            else:
                self._set_status(
                    False, "Cloud save belum tersedia — cek Play Games / APP_ID")
        except Exception as e:
            self._available = False
            self._signed_in = False
            self._set_status(False, "Cloud save tidak tersedia: %s" % e)
        return self._available

    # ------------------------------------------------------------
    # AUTH
    # ------------------------------------------------------------

    def check_auth(self, callback=None):
        if not self._ready():
            if callback:
                callback(_err_result("check", 1, self._last_message))
            return
        op_id = self._start_op("check", callback)
        if op_id:
            try:
                self._bridge.check_auth(op_id)
            except Exception as e:
                self._fail_op("check", op_id, 2, str(e))

    def sign_in(self, callback=None):
        if not self._ready():
            if callback:
                callback(_err_result("signin", 1, self._last_message))
            return
        op_id = self._start_op("signin", callback)
        if op_id:
            try:
                self._bridge.sign_in(op_id)
            except Exception as e:
                self._fail_op("signin", op_id, 3, str(e))

    # ------------------------------------------------------------
    # UPLOAD / DOWNLOAD PAYLOAD
    # ------------------------------------------------------------

    def upload_payload(self, payload, callback=None):
        """
        Unggah payload (working copy lokal) sebagai snapshot cloud.
        Payload dibungkus envelope cloud untuk validasi saat download.
        """
        if not self._ready():
            if callback:
                callback(_err_result("upload", 1, self._last_message))
            return
        if not self._signed_in:
            if callback:
                callback(_err_result(
                    "upload", 4, "Masuk ke Google Play Games dulu"))
            return
        if not payload or (not payload.get("slots")
                           and not payload.get("settings")):
            if callback:
                callback(_err_result(
                    "upload", 5, "Tidak ada save untuk diunggah"))
            return

        op_id = self._start_op("upload", callback)
        if not op_id:
            return
        dst = os.path.join(work_dir(), "upload_%s.json" % op_id)
        self._op_aux = {"file": dst, "delete": True}
        try:
            envelope = {
                "magic": CLOUD_MAGIC,
                "version": CLOUD_VERSION,
                "exported_at": time.time(),
                "payload": payload,
            }
            with open(dst, "w", encoding="utf-8") as fh:
                json.dump(envelope, fh, ensure_ascii=False)
            self._bridge.upload(dst, op_id)
        except Exception as e:
            self._fail_op("upload", op_id, 6, str(e))

    def download_payload(self, callback=None, apply=False):
        """
        Unduh snapshot cloud ke file sementara lalu (opsional) terapkan
        ke working copy lokal. Callback selalu menerima dict result.
        """
        if not self._ready():
            if callback:
                callback(_err_result("download", 1, self._last_message))
            return
        if not self._signed_in:
            if callback:
                callback(_err_result(
                    "download", 7, "Masuk ke Google Play Games dulu"))
            return

        op_id = self._start_op("download", callback)
        if not op_id:
            return
        dst = os.path.join(work_dir(), "download_%s.json" % op_id)
        self._op_aux = {"file": dst, "apply": bool(apply), "delete": True}
        try:
            self._bridge.download(dst, op_id)
        except Exception as e:
            self._fail_op("download", op_id, 8, str(e))

    def auto_upload(self, callback=None):
        """
        Dipanggil dari SaveManager.save() tiap kali working copy lokal
        ditulis. Non-blocking, tidak mengganggu alur save.
        """
        try:
            if not self._inited:
                self.start()
            if not self._available or not self._signed_in or self._busy:
                return False
            payload = build_payload()
            if payload is None or (not payload.get("slots")
                                   and not payload.get("settings")):
                return False
            self.upload_payload(payload, callback)
            return True
        except Exception as e:
            print("[CLOUD] auto_upload skipped: %s" % e)
            return False

    # ------------------------------------------------------------
    # POLL (harus dipanggil dari frame game)
    # ------------------------------------------------------------

    def poll(self):
        if not self._inited or self._bridge is None:
            return
        try:
            status = self._bridge.read_status()
        except Exception:
            return
        if not isinstance(status, dict):
            return
        op_id = str(status.get("op_id", "") or "")
        if not op_id or op_id in self._seen_ops:
            return
        self._seen_ops.add(op_id)
        if len(self._seen_ops) > 32:
            # Buang yang paling lama; operasi yang sedang jalan
            # disimpan terakhir karena baru saja ditambah.
            self._seen_ops = set(list(self._seen_ops)[-16:])

        # Selalu ikuti perubahan status masuk.
        if "signed_in" in status:
            signed = bool(status.get("signed_in"))
            if signed != self._signed_in:
                self._signed_in = signed
                if not signed:
                    self._set_status(
                        False, "Belum masuk ke Google Play Games")

        with self._lock:
            matches = (self._busy and op_id == self._op_id)
            kind = self._op_kind
            callback = self._op_callback
            aux = self._op_aux

        if matches:
            with self._lock:
                self._busy = False
                self._op_id = None
                self._op_kind = None
                self._op_callback = None
                self._op_aux = None
            self._dispatch_result(kind, status, callback, aux)

    # ------------------------------------------------------------
    # INTERNALS
    # ------------------------------------------------------------

    def _ready(self):
        if not self._inited:
            self.start()
        return self._available and self._bridge is not None

    def _set_status(self, ok, message):
        self._last_ok = bool(ok)
        self._last_message = message

    def _start_op(self, kind, callback):
        with self._lock:
            if self._busy:
                if callback:
                    callback(_err_result(
                        kind, 9, "Operasi cloud lain sedang berjalan"))
                return None
            op_id = "op-%s-%s-%s" % (
                kind, int(time.time() * 1000), uuid.uuid4().hex[:6])
            self._busy = True
            self._op_id = op_id
            self._op_kind = kind
            self._op_callback = callback
            self._op_aux = None
            return op_id

    def _fail_op(self, kind, op_id, code, message):
        # Panggil saat perintah tidak sampai ke Java (mis. import gagal).
        self._set_status(False, message)
        with self._lock:
            callback = self._op_callback
            aux = self._op_aux
            self._busy = False
            self._op_id = None
            self._op_kind = None
            self._op_callback = None
            self._op_aux = None
        if callback:
            callback(_err_result(kind, code, message))
        if aux:
            self._cleanup_aux(aux)

    def _cleanup_aux(self, aux):
        if not isinstance(aux, dict):
            return
        if aux.get("delete") and aux.get("file"):
            try:
                os.remove(aux["file"])
            except Exception:
                pass

    def _dispatch_result(self, kind, status, callback, aux):
        ok = bool(status.get("ok"))
        code = int(status.get("code", 0) or 0)
        message = status.get("message", "") or ""

        if not ok:
            self._set_status(False, message)
            if callback:
                callback(_err_result(kind, code, message))
            self._cleanup_aux(aux)
            return

        if kind == "download":
            self._handle_download_ok(aux, callback, message)
        else:
            self._set_status(True, message)
            if callback:
                callback(_ok_result(
                    kind, message=message,
                    path=status.get("file_path") or None))
            self._cleanup_aux(aux)

    def _handle_download_ok(self, aux, callback, message):
        dst = (aux or {}).get("file")
        apply_now = bool((aux or {}).get("apply"))
        payload = None
        summary = None
        err = None

        try:
            if not dst or not os.path.exists(dst):
                err = "File cloud tidak ditemukan"
            else:
                with open(dst, "r", encoding="utf-8") as fh:
                    envelope = json.load(fh)
                if envelope.get("magic") != CLOUD_MAGIC:
                    err = "Bukan file cloud Mystic Arena"
                elif envelope.get("version", 0) > CLOUD_VERSION:
                    err = "Versi cloud lebih baru dari game"
                else:
                    payload = envelope.get("payload")
                    if not isinstance(payload, dict):
                        err = "Payload cloud rusak"
                    else:
                        text = json.dumps(payload, ensure_ascii=False)
                        parsed, parse_err = parse_payload(text)
                        if parsed is None:
                            err = parse_err or "Validasi cloud gagal"
                        else:
                            payload = parsed
                            summary = get_payload_summary(parsed)
        except Exception as e:
            err = "Baca cloud gagal: %s" % e

        if err:
            self._set_status(False, err)
            if callback:
                callback(_err_result("download", 10, err))
        else:
            applied = False
            if apply_now:
                try:
                    ok_apply, apply_err = apply_payload(payload)
                    if ok_apply:
                        applied = True
                    else:
                        err = "Terapkan cloud gagal: %s" % apply_err
                except Exception as e:
                    err = "Terapkan cloud gagal: %s" % e

            if err:
                self._set_status(False, err)
                if callback:
                    callback(_err_result("download", 11, err))
            else:
                msg = ("Cloud restored!" if applied
                       else "Cloud save ditemukan")
                self._set_status(True, msg)
                if callback:
                    callback(_ok_result(
                        "download", message=msg,
                        payload=payload, summary=summary,
                        path=dst))
        self._cleanup_aux(aux)


# instance global yang dipakai game
manager = CloudSaveManager(enabled=_DEFAULT_ENABLED)
