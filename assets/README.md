# Folder assets

Berkas biner (font, suara, gambar) **tidak ikut** dalam bundel kode.
Salin milik Anda ke sini sebelum build APK.

```
assets/
├── fonts/
│   ├── Cinzel.ttf              judul / nama level / nama boss
│   ├── Barlow-Regular.ttf      teks HUD
│   ├── Barlow-Medium.ttf
│   ├── Barlow-SemiBold.ttf
│   └── Barlow-Bold.ttf
├── sounds/
│   ├── bgm_battle.wav|ogg      musik pertarungan
│   ├── ui_click.wav|ogg        ...dan seluruh efek suara lain
│   └── (lihat daftar lengkap di _system.py -> SoundManager.load_all)
├── icon.png                    512x512  ikon aplikasi (WAJIB untuk rilis)
├── presplash.png               1280x720 layar pembuka saat Python dimuat
├── logo.png                    (opsional) logo di splash screen game
└── items/                      ikon item ITEM FORGE (25 PNG)
```

Castle dan Hero menggunakan rendering prosedural murni berbasis kode (code base)
sehingga ringan, konsisten, dan tidak bergantung pada sprite gambar eksternal.

## Catatan penting

**Game tetap jalan tanpa berkas ini** — font otomatis mundur ke SysFont,
suara yang hilang hanya memunculkan `[WARNING] Sound ... tidak ditemukan!`.
Jadi Anda bisa langsung menguji kode dulu, aset menyusul.

**Untuk Play Store**: konversi musik `.wav` → `.ogg` agar ukuran AAB
jauh lebih kecil (batas Google 200 MB):

```bash
ffmpeg -i assets/sounds/bgm_battle.wav -c:a libvorbis -q:a 4 \
       assets/sounds/bgm_battle.ogg
```

Kalau nama berkasnya berubah, sesuaikan juga pemanggilan di
`_system.py` (kelas `SoundManager`).
