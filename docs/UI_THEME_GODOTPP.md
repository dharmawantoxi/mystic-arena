# Migrasi ui_theme.py → Godot++ (GDScript)

> **Status:** DONE (2026-09-11, FASE 31) — design system pygame (palet, cache
> gradasi/glow/bayangan, teks, 29 ikon vektor, dan 13 komponen siap pakai)
> diport 1:1 ke `godot/scripts/utils/UiTheme.gd` + 6 widget Control baru dan 3
> widget yang dialihkan ke jalur yang sama. Dikunci oracle dua lapis:
> `tools/test_godot_ui_theme_parity.py` (statik + menjalankan pygame ASLI) dan
> `godot/tests/UiThemeParityTest.tscn` (replay fixture di engine).

## Ringkasan ui_theme.py (Python)

`ui_theme.py` (1011 baris) adalah **satu sumber kebenaran tampilan menu**:
semua fungsi gambar menerima `screen` (permukaan tujuan) dan, untuk komponen
interaktif, `btns` (dict id → Rect) supaya hit-test `Menu.handle_click` tetap
satu jalur. Modul ini sengaja tidak mengimpor `_core`/`_render` di level modul
(circular import) — font selalu diterima sebagai parameter.

| Blok | Baris | Isi |
|---|---|---|
| Palet | `:30-69` | **32 konstanta** RGB: dasar (`BG_DEEP`, `PANEL_TOP/BOTTOM/FILL`), emas (`GOLD`, `GOLD_BRIGHT`, `GOLD_DEEP`, `GOLD_TEXT`, `EDGE_GOLD`, `EDGE_GOLD_DIM`), aksen tim (`CYAN`, `CYAN_SOFT`, `VIOLET`, `ORANGE`, `GREEN`, `GREEN_DEEP`, `RED`, `RED_DEEP`, `SLATE`), teks (`TEXT_WHITE`, `TEXT_BODY`, `TEXT_DIM`, `TEXT_FAINT`), dan 9 warna status kartu (`LOCKED_*`, `DONE_*`, `OPEN_*`) |
| Cache + kualitas | `:72-95` | `cheap_alpha()` (dibaca dari `mobile.perf.Quality` — **properti perangkat hasil pengukuran**, bukan preset kualitas), `clear_caches()`, dan 4 dict modul: `_GRAD_CACHE`, `_SHADOW_CACHE`, `_GLOW_CACHE`, `_GRAD_TEXT_CACHE` (kunci = ukuran + warna + radius/alpha) |
| Primitif | `:96-158` | `_vgrad(w,h,top,bottom,radius)` gradasi per baris `t = y/max(1,h-1)` + `int()` (truncation) + mask radius lewat `BLEND_RGBA_MULT`; `_shadow(w,h,radius,alpha,spread)` = sel 1/8 ukuran lalu `smoothscale`; `_radial(w,h,color,alpha)` glow elips **langkah 2px** dengan alpha `int(a·(1-d)²)` dan kunci alpha dibulatkan kelipatan 8 (`max(4, min(120, a//8*8))`); `math_hyp` |
| Teks | `:171-267` | `letter(text, gap=" ")` (letter-spacing manual — pygame tidak punya tracking), `fit_ellipsis` + `_has_glyph` (elipsis `…` kalau font punya glifnya, selain itu `...`), `draw_text(center=/topleft=, shadow, offset=(2,2))` dengan bayangan `(5,6,12)`, `gradient_text(font,text,top,bottom)` (gradasi di-mask ke glif lewat `BLEND_RGBA_MULT`, cache 400 entri), `outline_text(...)` outline 8 arah (4 arah di mode hemat) + isi gradasi `GOLD_BRIGHT → (196,138,40)` |
| Ikon vektor | `:269-508` | `draw_icon(surf, name, cx, cy, color, s)` — **29 nama** (pengganti emoji yang tidak ada di font Barlow), semuanya polygon/garis/lingkaran dengan pusat `(cx,cy)` dan skala `s` |
| Komponen | `:509-1011` | `corner_ticks` `:509`, `panel` `:524`, `panel_solid` `:545`, `button` `:553`, `pill` `:647`, `chip` `:693`, `section_header` `:736`, `_dim` `:750`, `toggle` `:754`, `slider` `:793`, `option_cycler` `:821`, `tab_width` `:868`, `tab` `:873`, `screen_title` `:907`, `back_button` `:950`, `scroll_indicator` `:962`, `hp_bar` `:982`, `progress_bar` `:998` |

Total **31 def** (termasuk helper privat) — semuanya harus punya padanan Godot
(daftar closed-world di `PEMETAAN`, lihat "Verifikasi").

Perilaku komponen yang paling mudah menyimpang (dan karena itu direkam oracle
dari pygame ASLI, bukan disalin tangan):

- `button()` — rect interaktif **melebar** `inflate(18, 8)` saat hover (quirk
  lama yang dipertahankan supaya hit-test tidak berubah); glow hover
  `_radial(w+44, h+36, accent, 74)` di `(x-22, y-18)`; bayangan di `(x-2, y-2)`
  (beda 2px dari `panel()` yang memakai `(x-4, y-4)`); badge ikon `r=17` di
  `x+34`; pusat label digeser `+14px` lalu **di-clamp tiga langkah** (dorong
  kanan bila menimpa badge → jepit tepi kanan → baru dipusatkan di antaranya).
- `pill()` — 8 kind (`gold/success/danger/locked/owned/neutral/violet/cyan`),
  hover = `top+18`/`bottom+14`, glow `_radial(w+30, h+24, edge, 66)`, dan
  **`enabled=False` tidak mendaftar rect hit** (tombol mati tidak bisa diklik).
- `chip()` — lebar otomatis `26 + (22 bila ikon) + lebar(letter(text)) +
  (10 + lebar(value))`, tinggi 30, `align="right"` berarti `pos` = sudut
  KANAN-atas.
- `section_header()` — `tw = font.size(title)[0] + 28` diukur dari judul
  **TANPA** letter-spacing padahal teksnya digambar letter-spaced (garis aksen
  karena itu partly menutup ekor teks — quirk yang dipertahankan); blok 34px.
- `toggle()` — knob 18px: pusat `right-24` saat ON, `x+6` saat OFF (OFF
  sengaja menonjol 3px keluar track), plus label ON/OFF di sisi berlawanan.
- `slider()` — knob di `x + int(w·value)` (bukan dikompensasi lebar knob);
  gradasi isi hanya bila `fill_w > 4`.
- `option_cycler()` — lebar kotak nilai `max(110, lebar+26)` lalu **dibatasi
  `width-66`**; chevron 24px dengan jarak 6px; hover chevron mana pun membuat
  border kotak jadi `EDGE_GOLD`; mengembalikan `y+37`.
- `screen_title()` — glow `_radial(620,150,(255,205,90),46)` di `(cx-310,y-62)`,
  ornamen di `y+52` (garis ±220/±18, wajik ±8/±7, dot ±230), plate subtitle
  `x = cx - (lebar+56)//2` (**pembagian bulat**), tinggi 44, sudut emas
  `length=8, width=1, inset=3`.
- `scroll_indicator()` — `ratio = h/(h+max)`, `thumb_h = max(18, int(h·ratio))`,
  `thumb_y = y + int((h-thumb_h)·pos/max)`; tidak mendaftar `btns`.
- `hp_bar()`/`progress_bar()` — isi `+50`/`+40` per kanal (ruang 8-bit),
  hanya bila `fw > 3`, radius `h//2`.

## Hasil migrasi

```
godot/scripts/utils/UiTheme.gd            — 1654 baris: palet 32 konstanta, cache tekstur,
                                            fungsi murni geometri/warna, 29 ikon, jalur
                                            immediate-mode draw_* (btns: Dictionary), font
godot/scenes/ui/widgets/PygameChip.gd     — BARU: chip status auto-size (semua
                                            properti ber-setter: assignment
                                            langsung menghitung ulang ukuran)
godot/scenes/ui/widgets/SectionHeader.gd  — BARU: ikon + judul letter-spaced + hairline
godot/scenes/ui/widgets/PygameSlider.gd   — BARU: HSlider dengan visual pygame (visual native dikosongkan)
godot/scenes/ui/widgets/OptionCycler.gd   — BARU: label + kotak nilai + chevron < > (signal value_changed)
godot/scenes/ui/widgets/ScrollIndicator.gd— BARU: thumb ramping 6px + follow(ScrollContainer)
godot/scenes/ui/widgets/GradientText.gd   — BARU: teks gradasi vertikal N pita
godot/scenes/ui/widgets/PygameButton.gd   — DIARAHKAN ulang: 3 mode (MENU/PILL/TAB) mendelegasikan ke UiTheme.*_visual + back_button()
godot/scenes/ui/widgets/PygameToggle.gd   — DIARAHKAN ulang: draw_toggle_visual
godot/scenes/ui/widgets/ScreenTitle.gd    — DIARAHKAN ulang: badan gradasi (GradientText) + sub/ornamen opsional
godot/tests/UiThemeParityTest.gd/.tscn    — replay fixture di engine (1472 baris)
godot/tests/fixtures/ui_theme.json        — 67 KB, 18 seksi, direkam dari pygame ASLI
tools/test_godot_ui_theme_parity.py       — oracle: 4 cek statik + 17 seksi oracle runtime (1141 baris)
```

Arsitektur port-nya **tiga lapis** supaya geometri/warna hanya punya satu sumber:

1. **Fungsi murni** (`static func ... -> Rect2/Dictionary/Color/Array`):
   `button_hit_rect`, `button_label_cx`, `menu_button_colors`, `pill_colors`,
   `chip_rect`/`chip_size`/`chip_colors`, `section_header_geom`/`_size`,
   `toggle_colors`/`toggle_knob_size`, `slider_geom`, `cycler_geom`,
   `tab_colors`/`tab_width_for`/`tab_width`, `screen_title_geom`,
   `back_button_rect`, `scroll_thumb_rect`, `bar_fill_w`, `dim`, `add_rgb`,
   `vgrad_row_color`, `gradient_bands`, `radial_alpha_key`, `glow_alpha_at`,
   `shadow_surface_size`/`shadow_small_size`, `hyp`, `letter`, `fit_ellipsis`,
   `has_glyph`, `pyrect`. Tidak menggambar apa pun → bisa dibandingkan dengan
   angka oracle tanpa GPU.
2. **Jalur immediate-mode** (`draw_*(cv: CanvasItem, ...)`): port 1:1 badan
   fungsi pygame, dipanggil dari `_draw()`. Komponen interaktif menerima
   `btns: Dictionary` (id → Rect2) — padanan `btns` pygame, jadi hit-test tetap
   satu jalur seperti `Menu.handle_click`. Versi `*_visual()` menggambar tanpa
   mendaftar rect (dipakai widget).
3. **Widget Control** di `scenes/ui/widgets/`: memanggil lapis 2, jadi tidak ada
   angka kedua yang bisa menyimpang.

Cache pygame dipetakan ke cache tekstur Godot dengan **kunci yang sama**:
`radial_texture(w,h,color,alpha)` (langkah 2px + kuantisasi alpha persis
`_radial`) dan `shadow_texture(w,h,radius,alpha,spread)` (sel 1/8 ukuran →
`resize` Lanczos = padanan `smoothscale`); `clear_caches()` mengosongkan
semuanya. `_GRAD_CACHE` tidak perlu tekstur: `draw_vgrad()` menggambar per baris
memakai `vgrad_row_color()` yang rumusnya identik.

## Deviasi (semuanya disengaja + dikunci tes)

| # | Deviasi | Alasan | Kunci |
|---|---|---|---|
| 1 | `cheap_alpha()` Godot **selalu true** (auto), dengan `static var cheap_alpha_override: int` (-1 auto / 0 paksa hemat / 1 paksa penuh) | Di pygame ini properti perangkat hasil pengukuran biaya blit (`mobile/perf.py:796`), bukan preset kualitas. Di Godot komposisi alpha terjadi di GPU → jalur "mahal" selalu terjangkau | Kedua cabang (`if cheap_alpha()` / `else`) TETAP diport 1:1 dan dijalankan tes: `DrawProbe._draw()` menggambar semua komponen dua kali (auto + `override = 0`) |
| 2 | Strip aksen 8px di `button()` digambar **opaque**, bukan alpha 70/255 | pygame menulis `(*accent, 70)` ke permukaan display **tanpa SRCALPHA**, jadi komponen alpha-nya DIABAIKAN dan hasilnya opaque (terverifikasi: port lama yang memakai alpha 70/255 adalah deviasi, dikoreksi di FASE 31) | Komentar di `draw_button_visual` + smoke test jalur opaque |
| 3 | `gradient_text()` → `GradientText` memakai **N pita `clip_contents`** (default 12), warna dievaluasi di tengah pita | pygame me-mask gradasi ke glif lewat `BLEND_RGBA_MULT` per baris piksel; Godot tidak bisa masking glif tanpa render target, dan pita clip adalah pendekatan yang tetap tajam di semua resolusi | Rumus per baris pygame (`t = y/max(1,h-1)` + truncation) dikunci persis: fixture merekam 20 baris warna `gradient_text()` ASLI dan tes membandingkannya dengan `vgrad_row_color()`; ujung pita + monotonitas diuji terpisah |
| 4 | Font: `UiTheme._load_font()` + `title_font()`/`body_bold()`/`body_semibold()`/`body_medium()`/`body_regular()` + `font_for_weight()` | pygame menerima font sebagai parameter dan pemanggilnya memakai `_core.get_font(size, weight)`/`title_font(size)`; Godot butuh font + ukuran eksplisit di setiap `draw_string` | `fit_ellipsis`/`tab_width`/`chip_size`/`section_header_size` menerima `(font, font_size, ...)`; oracle memakai **font palsu 7px/karakter** sehingga geometri terkunci tanpa bergantung metrik font engine mana pun |
| 5 | Nama API: `math_hyp` → `hyp`, `_dim` → `dim`, `_vgrad` → `draw_vgrad` + `vgrad_row_color`, `_shadow` → `draw_shadow` + `shadow_texture`/`shadow_surface_size`/`shadow_small_size`, `_radial` → `draw_glow` + `radial_texture`/`radial_alpha_key`/`glow_alpha_at`, `draw_text(center=)` → `draw_text_centered()`, `draw_text(topleft=)` → `draw_text()` | `_`-prefix Python = privat; GDScript memakai nama publik karena dipakai lintas berkas. `center=`/`topleft=` keyword-args Python tidak ada di GDScript | `PEMETAAN` di oracle: 31 def → 618 simbol Godot, **closed-world dua arah** (def pygame tanpa padanan = gagal; simbol Godot yatim = gagal) |
| 6 | `*_visual()` punya parameter tambahan `pressed`, `enabled`, `icon_scale`, `max_width` | `Button` Godot punya state pressed; pemanggil Godot butuh mematikan ikon/skala tanpa cabang baru | Default-nya mereproduksi pygame persis (`pressed=false`, `enabled=true`, `icon_scale` = skala ikon pygame 0.9/0.8); tes membandingkan kunci gradasi/glow pada keadaan default |
| 7 | `pyrect()` dipakai semua komponen | `pygame.Rect` **memotong** (bukan membulatkan) koordinat float ke int | `UiTheme.pyrect(Rect2(10.7,-2.3,30.9,4.1)) == Rect2(10,-2,30,4)` diuji; semua rect fixture bulat dan dibandingkan dengan toleransi 0,51px |
| 8 | `ScrollIndicator.follow(ScrollContainer)` + `set_scroll()`, `OptionCycler.press()`, `PygameButton.back_button()` | Kenyamanan Godot: pygame tidak punya ScrollContainer, dan harness butuh memicu klik tanpa event mouse | Perhitungannya tetap lewat fungsi murni (`scroll_thumb_rect`, `cycler_geom`, `back_button_rect`) yang dibandingkan dengan fixture |
| 9 | **6 widget baru belum punya pemakai UI** (kecuali `GradientText` yang dipakai `ScreenTitle`) | `MainMenu.gd` masih merakit sendiri `_shop_chip`/`_mini_chip`/`_settings_header`/`_volume_slider`/`_screen_header`. Rewiring sengaja TIDAK dilakukan: `MetaShopTxnParityTest` mengiterasi `PanelContainer` (filter meta `hero_type`) dan `LocalizationParityTest` mengumpulkan semua `Label` di layar SETTINGS — mengganti rakitan itu mengubah struktur node yang dikunci kedua tes | Widget-nya diuji `UiThemeParityTest` (min-size, hit-rect, signal, thumb, pita gradasi) terhadap angka oracle; pemakainya ditambahkan bertahap tanpa mengubah struktur node yang sudah dikunci |
| 10 | Dua konstanta Godot ekstra: `TEXT_SHADOW` = `(5,6,12)` dan `OUTLINE_DARK` = `(8,9,18)` | Di pygame keduanya literal di dalam `draw_text()` / pemanggil `gradient_text()`; memberi nama mencegah literal yang sama ditulis ulang di `GradientText.gd`/`ScreenTitle.gd` | Oracle menerima konstanta Godot ekstra (hanya melaporkan, tidak gagal) dan membandingkannya dengan literal pygame; `visual_parity_audit.py --section hardcode` turun dari 3 ke 1 literal (sisanya `TopupDialog.gd`, sudah ada sebelum fase ini) |

## Verifikasi

```bash
# 1. Oracle TANPA engine (detik) + menjalankan ui_theme.py ASLI (SDL dummy):
#    PALET   32 konstanta identik dua arah (Godot boleh punya ekstra:
#            TEXT_SHADOW, OUTLINE_DARK)
#    COVERAGE 31 def -> 618 simbol Godot (closed-world; def baru = gagal)
#    IKON    29 nama identik + setiap nama punya lengan `match` di draw_icon
#    LITERAL 30 warna literal komponen (chip/slider/knob/cycler/tab/title/
#            bar/scroll + teks pill "owned")
#    WIRING  17 seksi fixture semuanya dipakai UiThemeParityTest.gd
#    fixture segar (basi = gagal, sertakan daftar seksi yang berubah)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_godot_ui_theme_parity.py
#    regenerasi fixture HANYA kalau ui_theme.py memang berubah:
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_godot_ui_theme_parity.py --write-fixture

# 2. Parser GDScript asli (gdtoolkit) + lint scene/referensi repo
gdparse $(find godot -name '*.gd')
python3 godot/tools/tscn_lint.py $(find godot -name '*.tscn' -o -name '*.tres')
python3 godot/tools/check_refs.py godot
#    warna UiTheme tidak boleh ditulis ulang sebagai literal di .gd lain:
SDL_VIDEODRIVER=dummy python3 tools/visual_parity_audit.py --section palette,hardcode

# 3. Replay fixture di engine (CI godot-check langkah 4y):
XDG_DATA_HOME=$(mktemp -d) godot --headless --path godot \
  res://tests/UiThemeParityTest.tscn --quit-after 200
#    wajib: "[UiThemeParityTest] PASS" tanpa SCRIPT ERROR / Parse Error
```

Isi fixture `godot/tests/fixtures/ui_theme.json` (18 seksi, 67 KB):

| Seksi | Isi |
|---|---|
| `palette_live` | 32 warna dibaca dari modul pygame saat runtime |
| `math.vgrad` | 3 kasus, warna **tiap baris** (9/8/5 baris) |
| `math.radial` | 3 kasus × 40 sampel alpha per blok 2px + kunci alpha terkuantisasi |
| `math.shadow` | 3 kasus: ukuran permukaan + ukuran sel kecil |
| `math.dim/letter/hyp/ellipsis` | 4 + 5 + 3 + 5 kasus |
| `panel` | kunci gradasi, warna jalur hemat, ukuran bayangan |
| `button` | 4 kasus (idle/hover × ikon) + **12 kasus pusat label** (termasuk tombol sempit 120/160px yang memicu clamp "dorong kanan"); `center` direkam dari argumen `center=` yang **diterima** `draw_text` (bukan dari tengah blok piksel) + flag `clipped` untuk teks yang lebih lebar dari permukaan oracle |
| `pill` | tabel 8 kind × 4 warna + 16 kasus (kind × hover) + kasus `enabled=false` (rect kembalian + rect input + `btns` kosong) |
| `chip` | 8 kasus (align × ikon × value) |
| `section_header` | 2 warna: next_y, rentang piksel garis redup, ujung garis aksen |
| `toggle` | 4 kasus (on × hover) + ukuran knob |
| `slider` | 6 kasus (value 0 · 0,25 · 0,5 · 1 · 1,7 · −0,4 → clamp) + warna track/border + glow knob |
| `cycler` | 4 kasus (lebar × value_w) + kasus hover chevron |
| `tab` | 4 kasus (active × hover) + 3 kasus `tab_width` |
| `screen_title` | glow, ornamen (5 ukuran diturunkan dari piksel), plate subtitle, konstanta sumber |
| `back_button` | rect idle + hover (pill tidak inflate) |
| `scroll` | 5 kasus thumb (termasuk `max_scroll=0` dan thumb minimum 18px) |
| `bars` | 9 kasus (5 hp + 4 progres, rasio 0 → 2) |
| `gradient_text` | 20 baris warna gradasi teks ASLI + warna body/outline `outline_text` |
| `icons` | 29 nama |

## Temuan run engine pertama (CI hijau)

Cek statik + oracle di sandbox **tidak** bisa menjalankan Godot (binary tidak
bisa diunduh di lingkungan itu), jadi run CI `godot-check` adalah run engine
pertama untuk fase ini: **1463 cek, 19 gagal**. Ketigabelas sisanya lulus.
Rinciannya berguna karena menunjukkan apa yang hanya bisa ditangkap engine:

**Bug port sungguhan (3) — semuanya lolos gdparse & oracle statik:**

| Bug | Kenapa cek statik melewatkannya |
|---|---|
| `pill_colors("owned")` teks `#befaca`, seharusnya `#befac8` = `(190,250,200)` | `LITERAL_PENTING` belum memuat warna itu → sekarang ditambah, jadi salah hex begini gagal **tanpa** engine |
| `PygameButton.menu_button()`/`pill_button()` tidak menyalakan `use_letter_spacing` padahal `ui_theme.button()`/`pill()` default `letter_gap=True` | Factory tidak dibandingkan oracle (hanya `draw_*` yang diukur) → tes widget kini menguncinya |
| `PygameChip`: properti polos, jadi `chip.label_text = "X"` tidak menghitung ulang `custom_minimum_size` (lebar tetap 26px) | Tes statik tidak menjalankan setter → semua properti kini ber-setter |

**Jebakan engine yang layak diingat:**

- `Range::emit_value_changed()` **melewati node yang tidak ada di dalam tree**
  (`if (!r->is_inside_tree()) continue;`). Jadi `PygameSlider.value_changed`
  hanya terbit setelah `add_child()`; di luar tree nilainya tetap berubah,
  hanya sinyalnya yang diam. Widget turunan `Range` harus dipasang dulu.
- `floor()`/`ceil()`/`round()`/`min()`/`max()` mengembalikan **Variant** di
  GDScript → `var x := floor(...)` gagal parse ("Cannot infer the type") atau
  jadi warning `INFERENCE_ON_VARIANT` yang diperlakukan CI sebagai error.
  Pakai `floorf`/`ceilf`/`minf`/`maxf`/`mini`/`maxi`.
- Nama enum Godot 4: `Image.INTERPOLATE_LANCZOS` (bukan `INTERPOLATION_*`).
- `_draw()` bisa terpanggil lebih dari sekali per tes headless → probe yang
  mengakumulasi penghitung harus me-reset di awal `_draw()` (dulu 58 = 2 × 29
  ikon).
- `radial_texture()` **sengaja** menyatukan alpha sebucket
  (`max(4, min(120, a // 8 * 8))`, jadi 74 dan 72 → 72) persis `_GLOW_CACHE`
  pygame; tes yang mengharapkan instance berbeda untuk 74 vs 72 salah paham.

**Bug di sisi oracle (1):** `center` label tombol dulu dihitung dari tengah
blok piksel `TEXT_WHITE`. Untuk teks 60/130 karakter (833px/1813px) blit-nya
terpotong permukaan oracle 700px, sehingga "tengahnya" jadi `text_w / 2`
(416.5 dan 906.5) — bukan `text_cx` pygame. Oracle kini menyadap argumen
`center=` yang diterima `draw_text` dan merekam flag `clipped`; port
`button_label_cx` sendiri sudah benar (ke-12 kasus cocok 0.00px).

## Menambah warna / ikon / komponen baru

1. **Warna palet baru** di `ui_theme.py` → tambahkan konstanta di `UiTheme.gd`
   dan (bila dipakai komponen) di daftar `_test_palette_live`. Oracle gagal
   lebih dulu kalau hanya satu sisi yang ditambah.
2. **Ikon baru** → tambahkan lengan `match` di `UiTheme.draw_icon` **dan** nama
   di `const ICON_NAMES`. Oracle membandingkan kedua daftar dengan nama yang
   diparse dari `draw_icon` pygame, dan memverifikasi setiap nama punya lengan.
3. **Komponen/def baru** → tambahkan entri `PEMETAAN` di
   `tools/test_godot_ui_theme_parity.py` (def pygame → daftar simbol Godot).
   Tanpa entri itu oracle gagal dengan "def belum dipetakan" — memang itu
   maksudnya, supaya port tidak pernah diam-diam ketinggalan.
4. **Warna literal baru di dalam fungsi** → tambahkan ke `LITERAL_PENTING`
   (dicek sebagai `#hex` atau `Color8(...)` di `UiTheme.gd`).
5. Regenerasi fixture (`--write-fixture`), lalu tambahkan seksi pemeriksaannya
   di `UiThemeParityTest.gd` — `check_test_wiring` menolak fixture yang punya
   seksi tanpa pemeriksa ("oracle yatim").
