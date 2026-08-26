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
    ├── thorne_<pose>.png        sprite HD hero Thorne (idle/walk/attack)
    ├── thorne_swing_<0..7>.png  frame animasi swing attack Thorne (8 frame)
    ├── thorne_skill_<q/w/e/r>.png  efek skill HD Thorne (icon-item style)
    ├── zephyr_<pose>.png        sprite HD hero Zephyr (idle/walk/attack)
    ├── zephyr_walk_<0..1>.png   cycle jalan Zephyr (stride <-> plant)
    ├── zephyr_swing_<0..7>.png  frame animasi cast staff Zephyr (8 frame)
    ├── zephyr_skill_<q/w/e/r>.png  efek skill HD Zephyr
    ├── kaizen_<pose>.png        sprite HD hero Kaizen (idle/walk/attack)
    ├── kaizen_walk_<0..1>.png   cycle jalan Kaizen (stride <-> plant)
    ├── kaizen_swing_<0..7>.png  frame animasi iai slash Kaizen (8 frame)
    └── kaizen_skill_<q/w/e/r>.png  efek skill HD Kaizen (steel wind/wall/sweep/tornado)
```

Sprite HD (castles & heroes) adalah render digital transparan gaya
icon item. Kalau berkasnya tidak ada, game otomatis fallback ke
render prosedural lama - build tanpa aset tidak rusak. Sprite hero
diproses dari render mentah lewat `tools/make_thorne_hd_sprites.py`.

Frame swing & efek skill Thorne dibake dari renderer prosedural lewat
`tools/make_thorne_skill_sprites.py`:

```
python tools/make_thorne_skill_sprites.py
# -> assets/heroes/thorne_swing_<0..7>.png
# -> assets/heroes/thorne_skill_<q/w/e/r>.png
```

Zephyr dan Kaizen dibake dari render mentah HD (latar hitam) di
`assets/heroes/_raw/` (di-ignore git) lewat:

```
python tools/process_zephyr_anim.py   # -> zephyr_idle/walk/attack, walk_0..1, swing_0..7, skill_qwer
python tools/process_kaizen_anim.py   # -> kaizen_idle/walk/attack, walk_0..1, swing_0..7, skill_qwer
```

Saat runtime, swing memakai `<hero>_swing_<N>.png` per progress serangan
(fallback: `<hero>_attack.png` -> prosedural), dan efek skill Q/W/E/R
memakai `<hero>_<key>.png` sebagai lapisan HD (fallback: prosedural).

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
