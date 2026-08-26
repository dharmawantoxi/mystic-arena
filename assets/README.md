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
├── castles/                    sprite kastil HD (blue/red L1-L5, PNG transparan)
├── items/                      ikon item ITEM FORGE (25 PNG)
└── heroes/
    └── thorne_<pose>.png       sprite HD hero Thorne (idle/walk/attack)
```

Sprite HD (castles & heroes) adalah render digital transparan gaya
icon item. Kalau berkasnya tidak ada, game otomatis fallback ke
render prosedural lama - build tanpa aset tidak rusak. Sprite hero
diproses dari render mentah lewat `tools/make_thorne_hd_sprites.py`.

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
