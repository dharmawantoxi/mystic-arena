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
└── items/                      ikon item ITEM FORGE (33 PNG)
```

Castle dan Hero menggunakan rendering prosedural murni berbasis kode (code base)
sehingga ringan, konsisten, dan tidak bergantung pada sprite gambar eksternal.

## Folder ini juga sumber aset project Godot

Port Godot (`godot/`) tidak bisa membaca `res://` di luar root project-nya,
jadi `sounds/`, `items/`, dan `presplash.png` **diduplikasi** ke `godot/assets/`
oleh converter (hasilnya di-gitignore — sumber kebenaran tetap di sini):

```bash
python3 tools/convert_to_godot.py --assets   # tanpa pygame/numpy
```

| Di sini | Salinan Godot | Pembaca |
|---|---|---|
| `sounds/*.wav` (24) | `godot/assets/sounds/` | `AudioManager.gd` |
| `items/*.png` (33) | `godot/assets/items/` | `ItemIcons.gd` (port `hero_items.get_icon`) |
| `presplash.png` | `godot/assets/presplash.png` | `application/boot_splash/image` |
| `fonts/*.ttf`, `icon.png`, `logo.png` | `godot/assets/…` (**ikut repo**) | `UiTheme.gd`, `SplashScreen.gd`, ikon launcher |

Tambah ikon item baru? Taruh PNG-nya di `items/`, daftarkan field `"icon"` di
`hero_items.ITEM_CATALOG`, jalankan converter, lalu `python3
tools/test_godot_asset_pipeline.py` (closed-world 33 ikon ↔ `items.json`).

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
