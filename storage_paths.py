# ================================
# storage_paths.py
# Lokasi folder working copy save (slot & settings)
#
# MASALAH YANG DISELESAIKAN
# -------------------------
# Di Android, working-directory game adalah:
#     /data/data/<applicationId>/files/app
# yaitu folder hasil ekstrak kode game oleh python-for-android.
# Folder itu DIHAPUS TOTAL lalu diekstrak ulang setiap kali aplikasi
# di-update ke versi baru (lihat PythonUtil.unpackAsset ->
# recursiveDelete di bootstrap p4a). Kalau save disimpan dengan path
# relatif "saves/", progres pemain ikut lenyap tiap update.
#
# SOLUSI
# ------
# Simpan di $ANDROID_PRIVATE (= Context.getFilesDir(), .../files)
# yang berada DI LUAR folder "app", sehingga:
#   1. Selamat dari update aplikasi (p4a tidak menyentuhnya).
#   2. Jadi working copy untuk Cloud Save Google Play Games
#      (mobile/cloud_save.py): isi folder ini diunggah ke snapshot
#      Play Games tiap save, dan dipulihkan dari sana saat ganti
#      HP/install ulang. Android Auto Backup sengaja DIMATIKAN
#      (buildozer.spec: android.allow_backup = False) supaya
#      Google Play Games menjadi satu-satunya mekanisme save.
#
# Di desktop (Windows/Linux/macOS) perilaku lama dipertahankan:
# folder "saves/" relatif terhadap folder game.
# ================================

import os
import shutil
import sys

# Root folder game (folder tempat storage_paths.py berada / tempat
# main.py & _system.py). Di desktop, save DIKUNCI ke root ini, bukan
# ke "current working directory" (cwd), supaya save tetap ketemu walau
# game dijalankan dari folder lain (shortcut, IDE, terminal dari `/tmp`,
# dll.)
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def _is_android():
    if "ANDROID_ARGUMENT" in os.environ:
        return True
    if "ANDROID_PRIVATE" in os.environ:
        return True
    if hasattr(sys, "getandroidapilevel"):
        return True
    return False


def _android_writable_dir():
    """
    Folder write-android yang benar (DI LUAR folder 'app' hasil ekstrak
    p4a, sehingga selamat dari update aplikasi).

    Urutan:
      1. env ANDROID_PRIVATE   (dipasang python-for-android)
      2. env ANDROID_APP_PATH  (fallback beberapa bootstrap lama)
      3. PythonActivity.getFilesDir() via pyjnius
      4. home user (terakhir, kalau semuanya gagal)
    """
    for var in ("ANDROID_PRIVATE", "ANDROID_APP_PATH"):
        path = os.environ.get(var, "").strip()
        if path:
            return os.path.abspath(path)
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        files_dir = activity.getFilesDir()
        return files_dir.getAbsolutePath()
    except Exception as exc:
        print("[STORAGE] getFilesDir gagal: %s" % exc)
    return os.path.expanduser("~")


def get_save_dir():
    """
    Folder penyimpanan permanen untuk slot_*.json & settings.json.

    Android : <writable_dir>/saves
              (writable_dir = Context.getFilesDir(), DI LUAR folder
              'app' hasil ekstrak p4a, jadi selamat dari update;
              isinya hanya working copy yang disinkronkan ke Google
              Play Games — Auto Backup Android dimatikan)
    Desktop : <project_root>/saves
              (TIDAK lagi relatif ke cwd — inilah penyebab save
              "hilang" saat game dibuka dari folder/directory berbeda)
    """
    if _is_android():
        return os.path.join(_android_writable_dir(), "saves")
    # Override eksplisit (dipakai test/CI agar tidak menulis ke repo).
    override = os.environ.get("MYSTIC_SAVE_DIR", "").strip()
    if override:
        return os.path.abspath(override)
    return os.path.join(_PROJECT_ROOT, "saves")


SAVE_DIR = get_save_dir()
# Log ke stderr supaya tidak mengganggu program yang membaca stdout.
print("[STORAGE] save dir: %s" % SAVE_DIR, file=sys.stderr)

# Lokasi lama (relatif cwd). Di Android = .../files/app/saves —
# folder yang di-wipe p4a saat update aplikasi.
_OLD_SAVE_DIR = "saves"


def _migrate_from_wiped_location():
    """
    Migrasi SEKALI dari lokasi lama (files/app/saves) ke lokasi
    permanen (files/saves). Berjalan hanya di Android — di desktop
    kedua path identik sehingga fungsi ini tidak melakukan apa-apa.

    File lama TIDAK dihapus (biar aman); toh folder app/ akan
    dibersihkan sendiri oleh p4a pada update berikutnya.
    """
    try:
        old_dir = os.path.abspath(_OLD_SAVE_DIR)
        new_dir = os.path.abspath(SAVE_DIR)
        if old_dir == new_dir:
            return  # Desktop: tidak ada yang perlu dimigrasi

        if not os.path.isdir(old_dir):
            return

        os.makedirs(new_dir, exist_ok=True)

        for name in os.listdir(old_dir):
            src = os.path.join(old_dir, name)
            dst = os.path.join(new_dir, name)
            # Jangan timpa file di lokasi baru dengan file lama.
            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f"[STORAGE] Migrated {name} -> {new_dir}")
    except Exception as e:
        # Migrasi gagal tidak boleh bikin game crash.
        print(f"[STORAGE] Migration skipped: {e}")


_migrate_from_wiped_location()
