# ================================
# backup_manager.py
# Backup save lokal "export/import" ke folder publik Download.
#
# KENAPA ADA
# ----------
# Android Auto Backup (Google Drive) sudah terpasang, tapi:
#   - butuh akun Google + internet,
#   - kuotanya 25 MB dan jadwalnya tidak bisa dikontrol,
#   - tidak bisa dipakai pindah save antar-akun / via kabel USB.
# Modul ini menambah TULANG PUNGGUNG lokal tanpa internet: satu file
# JSON di Download/MysticArena/mystic_arena_backup.json yang selamat
# dari uninstall dan bisa disalin manual oleh pemain.
#
# TIGA JALUR TULIS/BACA
# ---------------------
#   Android 10+ (API >= 29)
#       MediaStore.Downloads via pyjnius. TANPA permission untuk file
#       yang dikontribusikan aplikasi sendiri (scoped storage).
#       CATATAN JUJUR: setelah UNINSTALL, kepemilikan file hilang;
#       install baru tidak selalu boleh membaca file itu lagi. Di
#       kasus itu Auto Backup Google Drive-lah jalur restore utama —
#       fitur ini tetap berguna sebagai arsip yang bisa dipindah
#       manual (file manager / kabel data).
#   Android 7-9 (API 24-28, minapi 24)
#       Environment.getExternalStoragePublicDirectory(DIRECTORY_DOWNLOADS)
#       + permission WRITE_EXTERNAL_STORAGE (dideklarasikan dengan
#       maxSdkVersion=28 sehingga TIDAK diminta di Android 10+).
#       Auto-export TIDAK PERNAH memunculkan dialog permission —
#       kalau izin belum ada, export dilewati diam-diam. Dialog izin
#       hanya boleh muncul dari tombol EXPORT/IMPORT manual.
#   Desktop (Windows/Linux/macOS)
#       Folder Download user (~/Downloads dst). Fitur tetap jalan
#       persis sama di PC, memudahkan pengujian.
#
# FORMAT FILE (versi 1)
# ---------------------
# {
#   "magic": "MYSTIC_ARENA_BACKUP",
#   "version": 1,
#   "exported_at": <epoch float>,
#   "slots": {"1": {...}, "2": {...}, "3": {...}},   # hanya slot terisi
#   "settings": {...},                                # settings.json
#   "checksum": "<sha256 hex>"
# }
# checksum = sha256 dari JSON kanonis (sort_keys, tanpa spasi) atas
# seluruh payload TANPA field "checksum". Import menolak file yang
# magic/checksum-nya tidak cocok, dengan pesan yang jelas.
#
# ATURAN ANTI-KECELAKAAN
# ----------------------
#   - Export/import gagal TIDAK BOLEH membuat game crash: semua jalur
#     dibungkus try/except dan hanya mencetak log.
#   - Auto-export tidak menimpa file backup yang datanya LEBIH BARU
#     daripada save lokal (misal: habis install ulang, Auto Backup
#     Google Drive belum turun, tapi file Download berisi progres
#     terakhir). Menimpa hanya boleh lewat tombol EXPORT manual
#     setelah konfirmasi.
# ================================

import hashlib
import json
import os
import sys
import threading
import time

import storage_paths

BACKUP_MAGIC = "MYSTIC_ARENA_BACKUP"
BACKUP_VERSION = 1
BACKUP_DIRNAME = "MysticArena"
BACKUP_FILENAME = "mystic_arena_backup.json"

# Path relatif MediaStore (Android 10+). Trailing slash mengikuti
# cara MediaStore menyimpan kolom relative_path.
_MEDIASTORE_REL_PATH = "Download/" + BACKUP_DIRNAME + "/"

NUM_SLOTS = 3  # sinkron dengan _system.SaveManager.NUM_SLOTS

# Toleransi pembanding timestamp (jam HP vs jam file bisa meleset dikit)
_NEWER_EPSILON = 2.0


# ═══════════════════════════════════════════════════════
# DETEKSI PLATFORM (mandiri — modul ini tidak boleh menyeret
# pygame/_core supaya bisa diuji di CI tanpa display)
# ═══════════════════════════════════════════════════════

def _is_android():
    if "ANDROID_ARGUMENT" in os.environ:
        return True
    if "ANDROID_PRIVATE" in os.environ:
        return True
    return hasattr(sys, "getandroidapilevel")


def _android_api_level():
    """API level runtime, 0 kalau bukan Android / jnius gagal."""
    try:
        from jnius import autoclass
        return autoclass("android.os.Build$VERSION").SDK_INT
    except Exception:
        return 0


def _jnius_detach():
    """Thread non-utama yang memakai jnius WAJIB detach sebelum mati."""
    try:
        import jnius
        jnius.detach()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════
# LOKASI SAVE LOKAL (dibaca dinamis supaya tes bisa mengganti
# storage_paths.SAVE_DIR tanpa reload modul ini)
# ═══════════════════════════════════════════════════════

def _save_dir():
    return storage_paths.SAVE_DIR


def _slot_file(slot_num):
    return os.path.join(_save_dir(), "slot_%d.json" % slot_num)


def _settings_file():
    return os.path.join(_save_dir(), "settings.json")


def all_slots_empty():
    """True kalau TIDAK ADA satu pun slot save lokal."""
    for i in range(1, NUM_SLOTS + 1):
        if os.path.exists(_slot_file(i)):
            return False
    return True


def _read_json(path):
    with open(path, "r") as f:
        return json.load(f)


def _local_newest_timestamp():
    """slot_last_played terbaru dari semua slot lokal (0 kalau kosong)."""
    newest = 0.0
    for i in range(1, NUM_SLOTS + 1):
        try:
            data = _read_json(_slot_file(i))
            ts = float(data.get("slot_last_played", 0) or 0)
            newest = max(newest, ts)
        except Exception:
            continue
    return newest


# ═══════════════════════════════════════════════════════
# PAYLOAD + CHECKSUM
# ═══════════════════════════════════════════════════════

def compute_checksum(payload):
    """sha256 dari JSON kanonis payload TANPA field 'checksum'."""
    body = {k: v for k, v in payload.items() if k != "checksum"}
    canonical = json.dumps(body, sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_backup_payload():
    """
    Kumpulkan semua slot + settings jadi satu payload backup.
    Return None kalau tidak ada satu pun slot terisi (tidak ada yang
    layak di-backup).
    """
    slots = {}
    for i in range(1, NUM_SLOTS + 1):
        path = _slot_file(i)
        if not os.path.exists(path):
            continue
        try:
            slots[str(i)] = _read_json(path)
        except Exception as e:
            # Slot korup dilewati; jangan gagalkan seluruh backup.
            print("[BACKUP] Slot %d unreadable, skipped: %s" % (i, e))

    if not slots:
        return None

    settings = {}
    try:
        if os.path.exists(_settings_file()):
            settings = _read_json(_settings_file())
    except Exception as e:
        print("[BACKUP] Settings unreadable, skipped: %s" % e)

    payload = {
        "magic": BACKUP_MAGIC,
        "version": BACKUP_VERSION,
        "exported_at": time.time(),
        "slots": slots,
        "settings": settings,
    }
    payload["checksum"] = compute_checksum(payload)
    return payload


def parse_backup_text(text):
    """
    Parse + validasi teks backup.
    Return (payload, None) kalau sah, (None, pesan_error) kalau tidak.
    Pesan error singkat & jelas — dipakai langsung di UI.
    """
    try:
        payload = json.loads(text)
    except Exception:
        return None, "File corrupt (not valid JSON)"

    if not isinstance(payload, dict):
        return None, "File corrupt (unexpected structure)"
    if payload.get("magic") != BACKUP_MAGIC:
        return None, "Not a Mystic Arena backup file"
    try:
        version = int(payload.get("version", 0))
    except Exception:
        return None, "File corrupt (bad version)"
    if version < 1 or version > BACKUP_VERSION:
        return None, "Backup version %s not supported" % version
    if not isinstance(payload.get("slots"), dict) or \
            not payload["slots"]:
        return None, "Backup contains no save data"
    if payload.get("checksum") != compute_checksum(payload):
        return None, "File corrupt (checksum mismatch)"
    return payload, None


def get_backup_summary(payload):
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


def backup_is_newer_than_local(payload):
    """
    True kalau DATA di dalam backup lebih baru daripada save lokal.
    Dipakai supaya auto-export tidak menimpa backup hasil sesi yang
    lebih baru (mis. sesudah install ulang) tanpa konfirmasi.
    """
    try:
        backup_newest = get_backup_summary(payload)["newest_played"]
        return backup_newest > _local_newest_timestamp() + _NEWER_EPSILON
    except Exception:
        return False


# ═══════════════════════════════════════════════════════
# BACKEND DESKTOP: folder Download user
# ═══════════════════════════════════════════════════════

def _desktop_download_dir():
    """
    Folder Download user di PC.
      1. Override MYSTIC_BACKUP_DIR (untuk tes / server headless)
      2. XDG user-dirs (Linux)
      3. ~/Downloads  (Windows/macOS/kebanyakan Linux)
    """
    override = os.environ.get("MYSTIC_BACKUP_DIR")
    if override:
        return override

    home = os.path.expanduser("~")

    # Linux: hormati XDG_DOWNLOAD_DIR kalau dikonfigurasi
    try:
        cfg = os.path.join(home, ".config", "user-dirs.dirs")
        if os.path.exists(cfg):
            with open(cfg, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("XDG_DOWNLOAD_DIR"):
                        value = line.split("=", 1)[1].strip().strip('"')
                        value = value.replace("$HOME", home)
                        if value:
                            return value
    except Exception:
        pass

    return os.path.join(home, "Downloads")


def _desktop_backup_path():
    return os.path.join(_desktop_download_dir(),
                        BACKUP_DIRNAME, BACKUP_FILENAME)


def _desktop_write(text):
    path = _desktop_backup_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Tulis atomik: temp lalu rename, supaya crash di tengah tulis
    # tidak meninggalkan backup setengah jadi.
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def _desktop_read():
    path = _desktop_backup_path()
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read()


# ═══════════════════════════════════════════════════════
# BACKEND ANDROID 7-9 (API < 29): file publik langsung
# ═══════════════════════════════════════════════════════

def _legacy_download_dir():
    from jnius import autoclass
    Environment = autoclass("android.os.Environment")
    base = Environment.getExternalStoragePublicDirectory(
        Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
    return os.path.join(base, BACKUP_DIRNAME)


def has_storage_permission():
    """
    Cek izin WRITE_EXTERNAL_STORAGE (hanya relevan di Android < 10).
    Android 10+ dan desktop selalu True.
    """
    if not _is_android():
        return True
    if _android_api_level() >= 29:
        return True
    try:
        from android.permissions import check_permission, Permission
        return check_permission(Permission.WRITE_EXTERNAL_STORAGE)
    except Exception:
        return False


def request_storage_permission():
    """
    Minta izin storage (dialog sistem). HANYA dipanggil dari tombol
    EXPORT/IMPORT manual — auto-export tidak boleh memunculkan dialog.
    """
    if not _is_android() or _android_api_level() >= 29:
        return
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                             Permission.READ_EXTERNAL_STORAGE])
    except Exception as e:
        print("[BACKUP] Permission request failed: %s" % e)


def _legacy_write(text):
    target_dir = _legacy_download_dir()
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, BACKUP_FILENAME)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)
    # Beritahu media scanner supaya file terlihat via MTP/file manager
    try:
        from jnius import autoclass
        MediaScannerConnection = autoclass(
            "android.media.MediaScannerConnection")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        MediaScannerConnection.scanFile(
            PythonActivity.mActivity, [path], None, None)
    except Exception:
        pass
    return path


def _legacy_read():
    path = os.path.join(_legacy_download_dir(), BACKUP_FILENAME)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read()


# ═══════════════════════════════════════════════════════
# BACKEND ANDROID 10+ (API >= 29): MediaStore.Downloads
# ═══════════════════════════════════════════════════════

def _mediastore_find_entry(resolver):
    """
    Cari row backup milik kita di MediaStore.Downloads.
    Return (uri, data_path) — dua-duanya bisa None.
    """
    from jnius import autoclass
    Downloads = autoclass("android.provider.MediaStore$Downloads")
    ContentUris = autoclass("android.content.ContentUris")
    collection = Downloads.EXTERNAL_CONTENT_URI

    uri = None
    data_path = None
    cursor = resolver.query(
        collection,
        ["_id", "_data"],
        "_display_name = ? AND relative_path = ?",
        [BACKUP_FILENAME, _MEDIASTORE_REL_PATH],
        None)
    if cursor is not None:
        try:
            if cursor.moveToFirst():
                uri = ContentUris.withAppendedId(
                    collection, cursor.getLong(0))
                data_path = cursor.getString(1)
        finally:
            cursor.close()
    return uri, data_path


def _mediastore_write(text):
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    resolver = PythonActivity.mActivity.getContentResolver()

    uri, _ = _mediastore_find_entry(resolver)

    if uri is None:
        Downloads = autoclass("android.provider.MediaStore$Downloads")
        ContentValues = autoclass("android.content.ContentValues")
        values = ContentValues()
        values.put("_display_name", BACKUP_FILENAME)
        values.put("mime_type", "application/json")
        values.put("relative_path", _MEDIASTORE_REL_PATH)
        uri = resolver.insert(Downloads.EXTERNAL_CONTENT_URI, values)
        if uri is None:
            raise RuntimeError("MediaStore insert returned null")

    # "wt" = truncate-then-write (tanpa ini sisa file lama bisa nempel)
    stream = resolver.openOutputStream(uri, "wt")
    try:
        stream.write(bytearray(text.encode("utf-8")))
        stream.flush()
    finally:
        stream.close()
    return _MEDIASTORE_REL_PATH + BACKUP_FILENAME


def _mediastore_read():
    """
    Baca backup di Android 10+.
    Jalur 1: path _data dari MediaStore (file milik sendiri boleh
             dibaca langsung lewat FUSE).
    Jalur 2: path publik konvensional — berhasil kalau kita masih
             pemilik file. Kalau dua-duanya gagal (install baru,
             scoped storage), kembalikan None: restore lokal tidak
             tersedia, Auto Backup Google Drive jadi jalur utama.
    """
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    resolver = PythonActivity.mActivity.getContentResolver()

    try:
        _, data_path = _mediastore_find_entry(resolver)
        if data_path and os.path.exists(data_path):
            with open(data_path, "r") as f:
                return f.read()
    except Exception as e:
        print("[BACKUP] MediaStore path read failed: %s" % e)

    # Fallback: path publik standar
    try:
        Environment = autoclass("android.os.Environment")
        base = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
        path = os.path.join(base, BACKUP_DIRNAME, BACKUP_FILENAME)
        if os.path.exists(path):
            with open(path, "r") as f:
                return f.read()
    except Exception as e:
        print("[BACKUP] Public path read failed: %s" % e)

    return None


# ═══════════════════════════════════════════════════════
# API UTAMA: EXPORT
# ═══════════════════════════════════════════════════════

def _write_backup_text(text):
    """Tulis teks backup lewat backend yang sesuai. Return path/label."""
    if _is_android():
        if _android_api_level() >= 29:
            return _mediastore_write(text)
        return _legacy_write(text)
    return _desktop_write(text)


def _read_backup_text():
    """Baca teks backup dari backend yang sesuai (None kalau tak ada)."""
    if _is_android():
        if _android_api_level() >= 29:
            return _mediastore_read()
        if not has_storage_permission():
            return None
        return _legacy_read()
    return _desktop_read()


def export_backup(force=False):
    """
    Tulis backup ke Download/MysticArena/mystic_arena_backup.json.

    Return (status, detail):
      'ok'            -> detail = path/label tujuan
      'no_data'       -> tidak ada slot terisi, tidak ada yang ditulis
      'no_permission' -> Android < 10 tanpa izin storage
      'conflict'      -> backup yang ada berisi data LEBIH BARU;
                         detail = summary backup itu. Hanya tombol
                         EXPORT manual (force=True setelah konfirmasi)
                         yang boleh menimpanya.
      'error'         -> detail = pesan error
    Tidak pernah melempar exception dan tidak memunculkan dialog.
    """
    try:
        payload = build_backup_payload()
        if payload is None:
            return "no_data", "No save data to export"

        if _is_android() and _android_api_level() < 29 \
                and not has_storage_permission():
            return "no_permission", "Storage permission not granted"

        if not force:
            # Jangan timpa backup yang datanya lebih baru dari lokal.
            try:
                existing_text = _read_backup_text()
                if existing_text:
                    existing, err = parse_backup_text(existing_text)
                    if existing is not None and \
                            backup_is_newer_than_local(existing):
                        print("[BACKUP] Export skipped: existing "
                              "backup is newer than local saves")
                        return "conflict", get_backup_summary(existing)
            except Exception as e:
                # Gagal MEMBACA backup lama tidak boleh memblokir export
                print("[BACKUP] Pre-export check failed: %s" % e)

        text = json.dumps(payload, indent=2)
        dest = _write_backup_text(text)
        print("[BACKUP] Exported to %s" % dest)
        return "ok", dest
    except Exception as e:
        print("[BACKUP] Export failed: %s" % e)
        return "error", str(e)


# ── Auto-export di background (dipanggil tiap SaveManager.save) ──
# Satu worker + flag "pending": save beruntun digabung jadi satu
# export, tidak pernah ada dua worker jalan bersamaan.
_export_lock = threading.Lock()
_export_pending = False


def _auto_export_worker():
    global _export_pending
    try:
        while True:
            _export_pending = False
            export_backup(force=False)
            if not _export_pending:
                break
    finally:
        _export_lock.release()
        if _is_android():
            _jnius_detach()


def auto_export():
    """
    Export otomatis, non-blocking, tanpa dialog. Aman dipanggil dari
    mana saja — kegagalan hanya tercatat di log.
    """
    global _export_pending
    try:
        _export_pending = True
        if _export_lock.acquire(blocking=False):
            threading.Thread(target=_auto_export_worker,
                             name="mystic-backup-export",
                             daemon=True).start()
    except Exception as e:
        print("[BACKUP] Auto-export scheduling failed: %s" % e)


# ═══════════════════════════════════════════════════════
# API UTAMA: IMPORT / RESTORE
# ═══════════════════════════════════════════════════════

def find_backup():
    """
    Cari & validasi file backup.
    Return (payload, summary, error_msg):
      - ada & sah   -> (payload, summary, None)
      - tidak ada   -> (None, None, None)
      - ada tapi rusak -> (None, None, pesan error yang jelas)
    """
    try:
        text = _read_backup_text()
    except Exception as e:
        print("[BACKUP] Read failed: %s" % e)
        return None, None, "Could not read backup file"

    if text is None:
        return None, None, None

    payload, err = parse_backup_text(text)
    if payload is None:
        print("[BACKUP] Invalid backup rejected: %s" % err)
        return None, None, err
    return payload, get_backup_summary(payload), None


def apply_backup(payload):
    """
    Pulihkan SEMUA slot + settings dari payload (payload diasumsikan
    sudah lolos parse_backup_text). Menimpa file lokal.
    Return (ok, error_msg).
    """
    try:
        save_dir = _save_dir()
        os.makedirs(save_dir, exist_ok=True)

        for i in range(1, NUM_SLOTS + 1):
            slot_data = payload.get("slots", {}).get(str(i))
            path = _slot_file(i)
            if slot_data is None:
                # Slot kosong di backup -> kosongkan juga di lokal
                # supaya hasil restore = kondisi saat export.
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
        print("[BACKUP] Restore complete (%d slot(s))"
              % len(payload.get("slots", {})))
        return True, None
    except Exception as e:
        print("[BACKUP] Restore failed: %s" % e)
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


# ═══════════════════════════════════════════════════════
# DETEKSI RESTORE SAAT INSTALL ULANG
# ═══════════════════════════════════════════════════════

# Sekali per proses: dialog restore tidak boleh nongol berulang kali.
_restore_check_done = False


def check_restore_on_startup(callback):
    """
    Kalau SEMUA slot kosong (indikasi install ulang / device baru),
    cari file backup di background. Kalau ketemu & sah, panggil
    callback(payload, summary) — dari thread worker, jadi callback
    hanya boleh menyetel state (bukan menggambar).

    Dipanggil dari Menu.__init__; no-op kalau sudah pernah jalan
    atau ada save lokal.
    """
    global _restore_check_done
    if _restore_check_done:
        return
    _restore_check_done = True

    try:
        if not all_slots_empty():
            return
    except Exception:
        return

    def _worker():
        try:
            payload, summary, err = find_backup()
            if payload is not None:
                print("[BACKUP] Backup found on startup "
                      "(level %s, gold %s, %s)"
                      % (summary["highest_level"],
                         summary["meta_gold"],
                         summary["exported_at_str"]))
                callback(payload, summary)
            elif err:
                print("[BACKUP] Startup restore check: %s" % err)
        except Exception as e:
            print("[BACKUP] Startup restore check failed: %s" % e)
        finally:
            if _is_android():
                _jnius_detach()

    try:
        threading.Thread(target=_worker,
                         name="mystic-backup-scan",
                         daemon=True).start()
    except Exception as e:
        print("[BACKUP] Restore scan failed to start: %s" % e)


def backup_location_label():
    """Label lokasi backup untuk ditampilkan di UI."""
    if _is_android():
        return "Download/%s/%s" % (BACKUP_DIRNAME, BACKUP_FILENAME)
    return os.path.join(_desktop_download_dir(),
                        BACKUP_DIRNAME, BACKUP_FILENAME)
