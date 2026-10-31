# Migrasi `ui_theme.py` ke Godot

Sistem desain Mystic Arena: palet, teks (gradasi/letter-spacing/elipsis), permukaan cache,
ikon vektor, dan komponen siap pakai (panel, tombol, pill, chip, toggle, slider, tab, header,
judul layar). Berkas ini 1011 baris: 0 kelas, 31 fungsi, 36 assign, 1 import.

Layer **9cp** menutup sisi geometri & teks yang belum pernah diport. Sisi piksel sudah
ditangani lebih dulu oleh layer **9br** (`bake/bake_ui_theme.py` → `assets/art/ui/*.png` →
`scripts/ui/ui_skin.gd`, diuji `tests/ui_skin_checks.gd`).

## 1. Ringkasan

| Aspek | Nilai |
| --- | --- |
| Berkas sumber | `ui_theme.py` (1011 baris) |
| Simbol | **68** = 32 palet + 31 fungsi + 4 cache + `pygame` |
| Klasifikasi | ported 25 · data 32 · baked 4 · folded 7 · deviation 0 · dead 0 |
| Modul native | `scripts/ui/ui_theme.gd` (995 baris, 39 `static func`) |
| Oracle | `tests/ui_theme_source_oracle.py` → `PASS: 31 ui_theme cases (212 ops) + 10 strings + 92 inventory facts` |
| Tes native | `tests/ui_theme_checks.gd` (terdaftar di `tests/run_all.gd` sebagai `UiThemeChecks`) |
| Fixture | `tests/fixtures/ui_theme_source.json`, `tests/fixtures/ui_theme_inventory.json` |

## 2. Klasifikasi simbol

### 2.1 Palet (32 konstanta → `data`)

Nilai dibaca ulang dari manifest 9br; `UiTheme.rgb(nama)` menerjemahkannya ke array RGB
integer dan `tests/ui_theme_checks.gd` membandingkan **32/32** dengan palet yang dijalankan
oracle dari modul Python asli. `tests/ui_skin_checks.gd` tetap memegang pin sembilan warna
utama dan ukuran tabel palet.

| Konstanta | Nilai | Kind | Bukti |
| --- | --- | --- | --- |
| `BG_DEEP` | `(9, 12, 26)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `CYAN` | `(110, 195, 255)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `CYAN_SOFT` | `(165, 220, 255)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `DONE_BG_BOTTOM` | `(17, 30, 24)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `DONE_BG_TOP` | `(26, 44, 36)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `DONE_EDGE` | `(86, 178, 112)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `EDGE_GOLD` | `(176, 144, 82)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `EDGE_GOLD_DIM` | `(104, 92, 66)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `GOLD` | `(255, 205, 85)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `GOLD_BRIGHT` | `(255, 233, 158)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `GOLD_DEEP` | `(158, 116, 40)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `GOLD_TEXT` | `(255, 220, 110)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `GREEN` | `(112, 226, 132)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `GREEN_DEEP` | `(34, 116, 58)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `LOCKED_BG_BOTTOM` | `(20, 19, 29)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `LOCKED_BG_TOP` | `(30, 28, 40)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `LOCKED_EDGE` | `(84, 86, 110)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `OPEN_BG_BOTTOM` | `(18, 24, 44)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `OPEN_BG_TOP` | `(28, 38, 64)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `OPEN_EDGE` | `(96, 152, 214)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `ORANGE` | `(255, 168, 96)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `PANEL_BOTTOM` | `(17, 21, 40)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `PANEL_FILL` | `(21, 26, 48)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `PANEL_TOP` | `(30, 37, 66)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `RED` | `(255, 108, 108)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `RED_DEEP` | `(132, 44, 44)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `SLATE` | `(148, 158, 188)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `TEXT_BODY` | `(198, 207, 230)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `TEXT_DIM` | `(132, 142, 170)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `TEXT_FAINT` | `(96, 106, 136)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `TEXT_WHITE` | `(240, 244, 255)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |
| `VIOLET` | `(176, 138, 255)` | data | `data/art/ui_theme.json` palette + `UiSkin.palette()` |

### 2.2 Fungsi (31)

| Simbol | Kind | Target native / bukti | Catatan |
| --- | --- | --- | --- |
| `letter` | ported | `ui_theme.gd::letter` | `gap.join(list(text))`; dua salinan lama di `level_intro_layout.gd`/`shop_hint_layout.gd` tidak diubah |
| `fit_ellipsis` | ported | `ui_theme.gd::fit_ellipsis` | loop kandidat sama; `_has_glyph` menjadi parameter `ellipsis` |
| `math_hyp` | ported | `ui_theme.gd::math_hyp` | `(x*x + y*y) ** 0.5` |
| `_dim` | ported | `ui_theme.gd::dim` | `int(c * f)` per kanal |
| `tab_width` | ported | `ui_theme.gd::tab_width` | `max(150, width(letter(label)) + 36)` |
| `draw_text` | ported | `ui_theme.gd::draw_text_ops` | body + bayangan `(5, 6, 12)` offset `(2, 2)` |
| `gradient_text` | ported | `ui_theme.gd::_gradtext` | satu op `gradtext`; cache dibatasi 400 |
| `outline_text` | ported | `ui_theme.gd::outline_text_ops` | 8 blit outline saat `cheap_alpha`, 4 saat tidak |
| `corner_ticks` | ported | `ui_theme.gd::corner_ticks_ops` | default length 11, width 2, inset 2 |
| `panel` | ported | `ui_theme.gd::panel_ops` | shadow + gradasi + border + ticks; jalur murah = (6, 7, 14) |
| `panel_solid` | ported | `ui_theme.gd::panel_solid_ops` | `PANEL_FILL` + `EDGE_GOLD` + ticks |
| `button` | ported | `ui_theme.gd::button_ops` | hover inflate (18, 8), glow, bevel, aksen kiri, badge, label ter-clamp |
| `pill` | ported | `ui_theme.gd::pill_ops` | 8 jenis, hover +18/+14, radius 7 |
| `toggle` | ported | `ui_theme.gd::toggle_ops` | knob 18 px di sisi berlawanan label |
| `tab` | ported | `ui_theme.gd::tab_ops` | underline aksen di tepi bawah, radius 8 |
| `slider` | ported | `ui_theme.gd::slider_ops` | track 8 px, knob 11/8; ada juga Control `ui_theme_slider.gd` |
| `chip` | ported | `ui_theme.gd::chip_ops` | lebar `26 + 22 ikon + teks + 10 + nilai`, tinggi 30 |
| `section_header` | ported | `ui_theme.gd::section_header_ops` | ikon + judul letter-spaced + hairline + underline dim |
| `option_cycler` | ported | `ui_theme.gd::option_cycler_ops` | kotak nilai `max(110, teks + 26)` di-clamp `width - 66` |
| `screen_title` | ported | `ui_theme.gd::screen_title_ops` | glow 620x150, ornamen wajik-garis, plate subtitle |
| `back_button` | ported | `ui_theme.gd::back_button_ops` | pill netral 200x42 dengan ikon `back` |
| `scroll_indicator` | ported | `ui_theme.gd::scroll_indicator_ops` | thumb `max(18, int(height * ratio))` |
| `hp_bar` | ported | `ui_theme.gd::hp_bar_ops` | track (16, 18, 30), isi dicerahkan, border (86, 92, 120) |
| `progress_bar` | ported | `ui_theme.gd::progress_bar_ops` | track (30, 34, 54), isi +40, border (96, 96, 126) |
| `clear_caches` | ported | `ui_theme.gd::clear_caches` | mengosongkan cache gradtext + `UiSkin.clear_cache()` |
| `draw_icon` | baked | `bake/bake_ui_theme.py` → `assets/art/ui/icons.png` | 30 glyph vektor; native hanya menaruh frame (`icon` op) |
| `_vgrad` | baked | `panels.png`, `pills.png`, `buttons.png`, `tabs.png` | native memakai `GradientTexture2D` untuk isi slider |
| `_shadow` | baked | `panels.png` + expand margin nine-patch | ring bayangan lembut, bukan rect runtime |
| `_radial` | baked | `assets/art/ui/slider_glow.png` | satu-satunya glow radial runtime |
| `cheap_alpha` | folded | `scripts/ui/shop_hint_layout.gd` dkk | setiap layout menerima flag kualitas dari adaptive quality |
| `_has_glyph` | folded | `ui_theme.gd::fit_ellipsis` | Barlow + Cinzel punya `…`; parameter `ellipsis` menggantikan probe render |

### 2.3 Cache dan import (5)

| Simbol | Kind | Bukti | Catatan |
| --- | --- | --- | --- |
| `_GRAD_CACHE` | folded | `ui_skin.gd::panels_texture` | gradasi sudah di-bake ke sheet |
| `_GLOW_CACHE` | folded | `ui_skin.gd::slider_glow_texture` | glow runtime hanya 36x36 |
| `_SHADOW_CACHE` | folded | `ui_skin.gd::panel_box` | bayangan jadi bagian nine-patch |
| `_GRAD_TEXT_CACHE` | folded | `ui_theme.gd::GRAD_TEXT_CACHE_LIMIT` | cache op `gradtext` dibatasi 400 seperti sumber |
| `pygame` | folded | `shop_hint_layout.gd` | diganti kosakata op; tidak ada Python/pygame saat runtime |

## 3. Yang ditutup di layer ini

| Celah | Perbaikan |
| --- | --- |
| 19 helper teks/geometri tidak punya padanan native | `ui_theme.gd` memport `letter`, `fit_ellipsis`, `tab_width`, `math_hyp`, `_dim`, `corner_ticks`, `panel`, `panel_solid`, `draw_text`, `gradient_text`, `outline_text`, `chip`, `section_header`, `option_cycler`, `screen_title`, `back_button`, `scroll_indicator`, `hp_bar`, `progress_bar` |
| Lima komponen interaktif hanya ada sebagai gambar bake | `button`, `pill`, `toggle`, `tab`, `slider` kini juga punya op builder, jadi geometri (rect, id tombol, hover, label) bisa diuji tanpa membaca piksel |
| `clear_caches()` tidak ada | `ui_theme.gd::clear_caches` + `ui_skin.gd::clear_cache` |
| Palet hanya dipin 9 dari 32 warna | tes native membandingkan **seluruh 32** warna terhadap palet hasil eksekusi modul Python |
| Tidak ada bukti urutan op | 31 kasus (212 op) direkam dari `ui_theme.py` asli dan dibandingkan op-per-op |

## 4. Deviasi terdokumentasi

| # | Sumber | Port | Alasan |
| --- | --- | --- | --- |
| D1 | `cheap_alpha()` membaca `mobile.perf.Quality` | flag parameter di setiap builder | modul mobile tidak ada di Godot; semua layout lain sudah memakai flag yang sama |
| D2 | `_vgrad`/`_shadow`/`_radial`/`draw_icon` menggambar piksel | op `vgrad`/`shadow`/`radial`/`icon` | piksel berasal dari sheet bake 9br; geometri & tanda tangan tetap dipin op |
| D3 | `gradient_text` menggambar satu baris per piksel tinggi | satu op `gradtext` | node judul menggambar gradasi; hasil op identik secara geometri |
| D4 | `_has_glyph` membandingkan dua render font | parameter `ellipsis` (default `…`) | Godot punya `Font.has_char`; sumber hanya butuh tahu apakah `…` ada |
| D5 | empat cache permukaan modul | bake + `UiSkin.clear_cache()` + cache gradtext 400 | permukaan di-cache sebagai resource/texture, bukan `Surface` pygame |
| D6 | `screen_title(sub=..., ornament=False)` → `NameError` (`fy` belum ada) | `fy = y + 52` selalu dihitung | perilaku sumber untuk pemanggil nyata sama; bug laten tidak dibawa |
| D7 | `button(font_size=...)` meng-import `get_font(font_size, "body_bold")` | `size`/`style` dari state dict | ukuran font di sumber selalu datang dari pemanggil; tidak ada kasus yang memakai override |
| D8 | `draw_icon` menggambar vektor pada skala apa pun | atlas 36 px dipakai ulang (`icon` op) | bake hanya menyimpan satu tile 36 px; skala lain memakai frame yang sama |

## 5. Cara menjalankan

```bash
python3 godot_rebuild/tests/ui_theme_source_oracle.py --write   # tulis kedua fixture
python3 godot_rebuild/tests/ui_theme_source_oracle.py           # 31 kasus + 10 string + 92 fakta
python3 godot_rebuild/tests/validate_project.py                 # blok 9br + 9cp
godot --headless --script tests/run_all.gd                      # suite native (PC/CI)
```

`tests/ui_theme_checks.gd` mengukur teks dengan metrik recorder (`int(size * 0.55)` per glyph,
tinggi = size), membandingkan `ops`, `rect` dan `buttons` lewat string kanonik (urutan kunci
tidak berpengaruh), lalu memeriksa inventaris 68 simbol, palet 32 warna, dan konstanta
kebijakan modul.

## 6. Status paritas

Terbukti: 31 rangkaian op (212 op, meliputi 10 jenis op), 10 kasus string/metrik, geometri
tombol (rect + registry id), dan 32/32 warna palet **identik** dengan eksekusi `ui_theme.py`
asli di bawah shim pygame. Piksel komponen tetap berasal dari bake pygame asli (9br).

Belum terbukti: tampilan akhir di layar Godot (spasi huruf, ketebalan font, posisi baseline
nyata) dan perilaku di perangkat Android — keduanya butuh run Godot + screenshot dengan seed/
state yang sama, sesuai kriteria paritas proyek. Validator statis dan fixture **bukan** bukti
paritas visual.
