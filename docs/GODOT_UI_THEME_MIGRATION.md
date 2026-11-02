# Migrasi `ui_theme.py` ke Godot

Dokumen ini menjelaskan port native design system menu/dialog dari
`ui_theme.py` (pygame) ke proyek aktif `godot_rebuild/`. Python tetap menjadi
sumber kebenaran dan oracle; Godot tidak memanggil Python saat runtime.
Hasil gate dan batas verifikasi dirangkum di
[`GODOT_UI_THEME_VERIFICATION.md`](GODOT_UI_THEME_VERIFICATION.md).

## Berkas utama

- `tools/prepare_godot_ui_theme.py` — exporter fail-closed. Kontrak diambil
  dari AST/anchor teks `ui_theme.py`; oracle menjalankan fungsi pygame asli
  secara headless dengan font metrics deterministik dan spy primitif.
- `godot_rebuild/data/ui_theme.json` — kontrak runtime: 32 warna palet,
  29 ikon, default komponen, formula cache/teks/layout, anchor sumber, dan
  hash sumber.
- `godot_rebuild/tests/fixtures/ui_theme_parity.json` — oracle 188 kasus
  komponen, 90 kasus ikon, gradient/radial/shadow, letter-spacing, ellipsis,
  corner ticks, dan lebar tab.
- `godot_rebuild/scripts/ui/UiTheme.gd` — pemuat kontrak, palet, kualitas
  `cheap_alpha`, helper Rect/ warna, dan akses angka konfigurasi.
- `UiThemeSurfaces.gd` — formula gradient vertikal, glow radial, bayangan,
  dan cache teks gradasi.
- `UiThemeText.gd` — letter-spacing, ellipsis, layout teks/shadow, outline
  offset, dan injeksi pengukuran font.
- `UiThemeIcons.gd` — geometri vektor 29 ikon dalam ruang koordinat sumber.
- `UiThemeComponents.gd` / `UiThemeComponentsExtra.gd` — layout dan
  draw-command panel, button, pill, chip, header, toggle, slider, cycler,
  tab, judul layar, back button, scroll indicator, HP/progress bar.
- `UiThemeTextures.gd` / `UiThemeDraw.gd` — cache tekstur native dan renderer
  draw-command ke `CanvasItem`.
- `UiThemeButton.gd` / `UiThemePanel.gd` — wrapper `Button`/`PanelContainer`
  yang memakai renderer sumber tanpa mengambil alih layout Godot.
- `Ui.gd` — facade UI aktif sekarang mengambil palet/kontrol dari `UiTheme`.
- `godot_rebuild/tests/UiThemeParityTest.gd` — replay oracle pada helper dan
  komponen, termasuk mode `cheap_alpha` hidup/mati dan fail-closed.
- `tools/test_godot_ui_theme_prepare.py` dan
  `tools/test_godot_ui_theme_parity.py` — gate Python exporter/oracle.

## Semantik yang dipertahankan

- Palet dark-fantasy: midnight, gold, aksen team, teks, dan status
  locked/done/open diambil dari kontrak, bukan konstanta UI lama.
- `cheap_alpha()` sumber berarti “efek alpha aman dijalankan”. Di Godot,
  `RenderQuality.cheap_alpha` adalah flag anggaran terbalik; port memetakannya
  sebagai `not RenderQuality.preset(level).cheap_alpha`. Override kualitas
  tersedia untuk parity dan perubahan setting/adaptive quality dari `Main`.
- Cache surface: gradient vertical dengan truncation `int()` per baris,
  radial ellips blok 2×2 dengan alpha `int(a * (1-d)^2)` dan kuantisasi
  alpha kelipatan 8, shadow dari permukaan kecil `max(4, size//8)`, serta
  batas cache teks gradasi 400 entri.
- Teks: `letter()` menyisipkan gap per karakter; `fit_ellipsis()` mempertahankan
  fallback `…`/`...` dan batas truncate sumber; shadow/outline memakai warna
  dan offset kontrak. Pengukuran font disuntikkan agar oracle dan Font Godot
  dapat memakai jalur layout yang sama.
- Komponen mempertahankan angka sumber: hover button.inflate 18×8, clamp
  label terhadap badge ikon, pill 8 kind + fallback neutral, disabled pill
  tidak mendaftar hit-rect, chip auto-size left/right, header rule memakai
  lebar judul tanpa spacing, toggle knob 18 px, slider fill clamp 0..1,
  cycler value-box min 110 px dan reserve 66/56 px, tab auto-width, judul
  layar glow/ornament/subtitle plate, scroll thumb min 18 px, serta HP/progress
  fill threshold dan lighten 50/40.
- Ikon vektor direkam sebagai primitif polygon/circle/rect/line/arc dengan
  urutan dan warna yang sama seperti `draw_icon` pygame.

## Integrasi native

- `Ui.panel()` mengembalikan `UiThemePanel` yang menggambar panel sumber di
  belakang child container; margin konten lama dipertahankan agar layout menu
  tidak bergeser.
- `Ui.button()` mengembalikan `UiThemeButton` dengan gradasi, border, aksen,
  corner ticks, badge/ikon, dan label dari renderer sumber. Label wrapper tidak
  dipaksa letter-spaced agar teks lokal/HUD yang sudah ada tidak meluap;
  komponen murni tetap mendukung `letter_gap=True` sesuai sumber.
- Rect interaktif wrapper tetap dimiliki Godot. Komponen murni mempertahankan
  hover inflation 18×8 untuk parity; wrapper container tidak mengubah ukuran
  hit-test saat hover supaya fokus keyboard/touch dan VBox tidak melompat.
- `MenuView` memakai `BG_DEEP` sumber. Judul memakai shader gradasi emas native
  sebagai pendekatan `gradient_text`; outline/shadow mengikuti kontrak.
- `Main._settings_changed()` dan jalur adaptive quality meneruskan level
  kualitas ke `UiTheme`, sehingga mode low/medium mematikan efek alpha mahal
  seperti fallback solid pada sumber.

## Perintah

```bash
python3 -m pip install pygame==2.6.1 gdtoolkit==4.5.0
python3 tools/prepare_godot_ui_theme.py
python3 tools/prepare_godot_ui_theme.py --check
python3 tools/test_godot_ui_theme_prepare.py
python3 tools/test_godot_ui_theme_parity.py
python3 godot_rebuild/tests/validate_project.py
```

`--check` membandingkan byte JSON secara eksak dan tidak menulis apa pun.
CI menjalankan gate ini di `godot-check.yml` dan `godot-rebuild.yml`.

## Batas yang jujur

- Renderer native memakai primitif/tekstur Godot. Mask rounded, smoothscale
  shadow, arc ellips, dan raster font bukan replika piksel pygame; parity
  menguji formula, geometri, warna, urutan draw, dan hit-rect, bukan screenshot.
- Gradasi teks pada `Label` memakai shader native; draw-command outline segera
  memakai pendekatan warna badan native. Metrik font Godot tidak diklaim identik
  dengan pygame/SDL_ttf.
- Wrapper `Button`/`PanelContainer` mempertahankan layout dan hit-test Godot;
  hover inflation sumber hanya dijamin pada komponen murni yang diuji parity.
- Tidak ada verifikasi visual GPU layar nyata, perangkat Android, atau output
  audio. Tema ini tidak mengubah layanan top-up/voucher/cloud save.
