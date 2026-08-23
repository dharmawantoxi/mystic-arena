# ================================
# storage_paths.py
# Lokasi folder data permanen (save slot & settings)
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
#   2. Ikut Android Auto Backup ke Google Drive, jadi progres
#      otomatis kembali saat install ulang atau pindah HP dengan
#      akun Google yang sama. Aturan backup-nya dibatasi hanya ke
#      folder saves/ — lihat backup_rules.xml (Android <= 11) dan
#      data_extraction_rules.xml (Android 12+) di root repo.
#
# Di desktop (Windows/Linux/macOS) perilaku lama dipertahankan:
# folder "saves/" relatif terhadap folder game.
# ================================

import os
import shutil


def get_save_dir():
    """
    Folder penyimpanan permanen untuk slot_*.json & settings.json.

    Android : $ANDROID_PRIVATE/saves  (persisten antar update,
              ikut Auto Backup ke Google Drive)
    Desktop : ./saves                 (perilaku lama, tidak berubah)
    """
    android_private = os.environ.get("ANDROID_PRIVATE")
    if android_private and os.path.isdir(android_private):
        return os.path.join(android_private, "saves")
    return "saves"


SAVE_DIR = get_save_dir()

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
            # Jangan timpa file di lokasi baru (misal hasil restore
            # Auto Backup) dengan file lama.
            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f"[STORAGE] Migrated {name} -> {new_dir}")
    except Exception as e:
        # Migrasi gagal tidak boleh bikin game crash.
        print(f"[STORAGE] Migration skipped: {e}")


_migrate_from_wiped_location()
