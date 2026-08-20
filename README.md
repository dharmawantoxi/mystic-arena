# Mystic Arena — MOBA Tower Defense (pygame → Android)

Game tower-defense/MOBA berbasis **pygame-ce**, 54 level, 200+ boss,
6 hero dengan skill Q/W/E/R, dan 20+ tema peta.
Repositori ini berisi versi yang sudah disiapkan untuk **Android /
Google Play**, dengan kontrol **layar sentuh penuh**.

> 📖 Panduan lengkap langkah demi langkah (build APK, GitHub Actions,
> publikasi Play Store): **[docs/PANDUAN_ANDROID.md](docs/PANDUAN_ANDROID.md)**

---

## Struktur proyek

```
main.py                  entry point (sentuh + fallback mouse/keyboard)
main_desktop_legacy.py   entry point lama (keyboard + gamepad) — arsip
_core.py                 settings, game, menu, input, UI, dev tools
_entity.py               tower, castle, hero, minion, ai_player
_render.py               map renderer, efek, cinematic, cache font
_system.py               performance, fps, sound, save
splash_screen.py         splash pembuka

mobile/                  ◀ LAPISAN BARU KHUSUS ANDROID
├── platform_utils.py    deteksi Android, display SCALED, safe area, jnius
├── touch.py             mesin gesture: tap / long-press / drag / fling
├── hud.py               tombol layar: skill QWER, shop, pause, skip
├── debug.py             overlay FPS + crash handler ke file
├── perf.py              cache font/teks, darken/flash, pool, preset kualitas
└── spritecache.py       cache sprite (opsional - lihat catatan hasil ukur)

bosses/                  base_boss, boss_data, level1..level54
heroes/ hero_skills/     renderer & skill hero
levels/                  konfigurasi 54 level
map_components/          palet, tema, generator, renderer peta
minions/ towers/         renderer unit & menara
ui_components/           panel, popup, shop, notifikasi

buildozer.spec           konfigurasi build Android
p4a-recipes/pygame-ce/   resep kompilasi pygame-ce untuk Android
.github/workflows/       CI: APK debug tiap push, AAB release tiap tag
bosses/_boss_index.py    peta boss→modul (dibuat tools/gen_boss_index.py)
tools/                   benchmark, uji cache sprite, generator indeks
```

## Menjalankan di PC

```bash
python -m venv .venv && source .venv/bin/activate
pip install pygame-ce
python main.py                       # mouse + keyboard
MYSTIC_FORCE_TOUCH=1 python main.py  # simulasikan layout HP
```

## Membangun APK

```bash
pip install buildozer "cython<3.0"
buildozer android debug        # APK untuk uji di HP
buildozer android release      # AAB untuk Play Store
```

## Hasil optimasi (terukur, headless di CPU desktop)

| | Sebelum | Sesudah |
|---|---|---|
| Adegan intro boss | 29,4 ms/frame (34 FPS) | **5,4 ms/frame (185 FPS)** |
| Waktu buka aplikasi | 3,50 s | **0,14 s** |
| RAM saat start | 100 MB | **39 MB** |
| Modul boss dimuat saat start | 54 | **0** (impor malas) |

Rinciannya di [docs/PANDUAN_ANDROID.md § 3](docs/PANDUAN_ANDROID.md).

## Perkakas

```bash
python tools/bench_mobile.py       # benchmark adegan intro + uji gesture/HUD
python tools/bench_heavy.py        # benchmark gameplay (--quality low/high)
python tools/bench_minions.py      # skala jumlah minion
python tools/test_spritecache.py   # uji kebenaran cache sprite (piksel)
python tools/gen_boss_index.py     # regenerasi indeks boss setelah tambah boss
```

## Aset yang harus ada

`assets/fonts/` (Cinzel.ttf, Barlow-*.ttf), `assets/sounds/*.wav|ogg`,
`assets/icon.png` (512×512), `assets/presplash.png`.
Tanpa font/suara game tetap jalan (ada fallback), tanpa
`icon.png`/`presplash.png` build tetap jalan dengan gambar bawaan.

## Kontrol sentuh

| Aksi lama (keyboard/mouse) | Aksi baru (sentuh) |
|---|---|
| Klik kiri | Ketuk |
| Klik kanan | Tahan 0,45 detik |
| Scroll wheel | Geser vertikal + inersia |
| Q / W / E / R | 4 tombol skill di kanan bawah |
| H (shop) | Tombol SHOP kiri bawah |
| ESC (pause) | Tombol ⏸ kanan atas |
| SPACE (skip cinematic) | Ketuk layar / tombol LEWATI |
| F8 (FPS) | Tombol FPS kanan atas (4 mode debug) |
| R / N (ulangi / lanjut) | Tombol di layar menang/kalah |
