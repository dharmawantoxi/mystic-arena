# Migrasi `bosses/` → Godot (GDScript)

> **Status:** DONE (2026-09-12, FASE 32) — dua bagian `bosses/` yang realistis
> diport diport penuh: **(A)** lapisan overlay `Boss.draw()`
> (`bosses/base_boss.py:6124-6430`) → `godot/scripts/render/BossOverlay.gd`
> (+ `godot/scenes/boss/BossPlate.gd`), dan **(B)** pipeline data saat-import
> `bosses/boss_data.py` → `godot/scripts/core/BossData.gd` (+ jalur pemulihan
> `BossDB.rebuild_from_pristine()`). Dikunci empat oracle Python dan dua scene
> replay engine.
>
> **Sengaja TIDAK diport:** 54 renderer prosedural per boss
> (`bosses/level1.py`…`level54.py`, ±350 ribu baris). Keputusan repo sejak
> Fase 2b→Fase 5: badan boss tampil lewat **strip bake** PNG
> (`assets/units/<type>.png`, 445 berkas ter-commit) yang di-render dari
> renderer pygame ASLI oleh `tools/convert_to_godot.py --units-png`. Port
> 1:1-nya tidak bisa diverifikasi dan tidak mengubah satu piksel pun bagi
> pemain. Yang diambil dari berkas-berkas itu hanya **pemetaan dispatch**-nya
> (`RendererRegistry` / `has_renderer`), yang menentukan apakah overlay
> menggambar badan generik fallback.

## Bagian A — lapisan overlay `Boss.draw()`

### Ringkasan pygame

`Boss.draw(screen)` (immediate-mode, dipanggil tiap frame) menggambar, dalam
urutan ini:

| # | Blok pygame | Isi |
|---|---|---|
| 1 | `_draw_entrance` (`:6376-6430`) | **eksklusif**: selama `entrance_timer > 0` hanya ini yang digambar — cincin ekspansi + teks entrance berdenyut di tengah layar (bayangan teks +2/+2, baris 34 px, `start_y = 84 − (n−1)·18`) |
| 2 | aura ability (`:6139-6159`) | `ability_active`: 3 cakram konsentris alpha 26/40/60 radius `ability_range` |
| 3 | `_draw_enrage_aura` (`:6277-6300`) | `is_enraged`: dua cincin stroke 2 px radius `radius + 14·pulse`, merah `(255,50,40)` true / oranye `(255,142,30)` mini |
| 4 | `_draw_true_boss_aura` (`:6351-6375`) | true boss saja: 8 lingkaran `range(aura_r, aura_r−15, −2)`, alpha `(aura_r − r_off)·5·pulse`, `pulse = sin(self.pulse)·0,3 + 0,7` |
| 5 | bayangan (`:6166`) | ellipse hitam `(0,0,0,120)` rect `(x − rx, y + ry·0,35, 2rx, ry·0,7)` |
| 6 | indikator debuff menara (`_core.py:1037-1085`) | `TowerDebuffMixin`: label SLOW/ATK SLOW/SKILL DOWN/ANTI HEAL/BURN di atas kepala, timer > 0 |
| 7 | `_draw_generic_body` (`:6301-6350`) | **hanya bila tidak ada renderer** (`has_renderer` false): bulatan `color`/`color_dark` + mahkota + mata menyala |
| 8 | HP bar (`:6225-6245`) | **digambar duluan** (jadi jangkar papan nama): `bar_w` 70 true / 60 mini, `bar_h` 10/8, `bx = x − bar_w//2`, `by = y − head_top − 6 − bar_h`; bg `(40,0,0)`, isi `int(bar_w·ratio)` berwarna `(100,220,100)` >0,5 / `(240,220,60)` >0,25 / `(240,60,60)`, border 1 px `(255,60,60)` enrage / `(255,100,100)` true / `(255,200,50)` mini |
| 9 | papan nama (`:6246-6276`) | `"TRUE BOSS: nama [ENRAGED]"` / `"BOSS: nama [FRENZY]"`, font `body_bold` 20/18, warna `(255,60,60)` enrage / `(255,100,100)` true / `(255,220,100)` mini; `midbottom = (x, by − 5)`, kotak bg hitam `inflate(8,4)` radius 3 + border `border_c` 1 px, lalu **di-clamp** margin 2 px ke lebar layar (`SCREEN_W = 1280`) |

### Jebakan alpha (kenapa port-nya bukan `draw_circle` bertumpuk)

`pygame.draw.circle` pada surface `SRCALPHA` **MENIMPA** piksel (termasuk kanal
alpha), bukan mem-blend. Delapan lingkaran konsentris aura true boss karena itu
menghasilkan **gradien berpita**: setiap piksel memakai alpha lingkaran terkecil
yang menutupinya, dan bagian dalam (`d ≤ aura_r − 14`) rata di `70·pulse`.
`draw_circle()` Godot sebaliknya mem-blend, jadi menyalin loop pygame apa adanya
membuat pusat aura ±3× lebih pekat (terukur 144/255 vs 49/255 pada pulse 0,7).

Model yang dipakai (dan dikunci tes): **pita annulus** —
`band(ri, ro, alpha)` untuk `ri < d ≤ ro`, digambar dengan `draw_arc` selebar
`AURA_STEP` di radius tengah, sehingga pita-pitanya tidak saling menimpa.
Pita terdalam menutup `d = 0` (`ri ≤ 0`), dan profil alpha radialnya diukur dari
render pygame sungguhan — pendekatan naif 8× `draw_circle` **wajib gagal** di
oracle (`tools/test_boss_true_aura_parity.py`).

### Hasil migrasi

| Berkas | Peran |
|---|---|
| `godot/scripts/render/BossOverlay.gd` (852 baris, 78 konstanta) | Sumber geometri overlay: builder murni `entrance_ops` / `ability_aura_ops` / `enrage_aura_ops` / `true_aura_ops` / `shadow_ops` / `debuff_ops` / `generic_body_ops` / `hp_bar_ops` / `name_plate_ops`, pembagi lapisan `underlay_ops()` (langkah 1-7) + `over_ops()` (langkah 8-9), `exec()` (raster op kanonik → `draw_*` Godot), plus helper audit `filled_aura_bands()` / `radial_profile()` |
| `godot/scenes/boss/Boss.gd` | Menyuplai `overlay_state()` (satu-satunya tempat angka permainan bertemu geometri) dan meraster lapisan **bawah** badan di `_draw()` — `CanvasItem` menggambar dirinya dulu, anaknya belakangan, jadi urutannya otomatis benar |
| `godot/scenes/boss/BossPlate.gd` | Node anak **sesudah `Visual`** yang meraster lapisan **atas** badan (HP bar + papan nama) dari `overlay_state()` yang sama |
| `godot/scenes/boss/Boss.tscn` | `Plate` menggantikan node statis `UI` (`CanvasGroup` + `ProgressBar` + `Label`) yang tidak bisa meniru geometri pygame; `Shadow` `Polygon2D` lama dimatikan (bayangan digambar overlay) |

**Kosakata op kanonik** (dipakai fixture, model Python, dan `exec()`):
`disc{k,c,r,col}` · `band{k,c,ri,ro,col}` · `ring{k,c,r,w,col}` ·
`ellipse{k,rect,col,w}` · `rect{k,rect,col,w,radius}` · `poly{k,col,pts}` ·
`text{k,text,size,style,col,anchor,pos,wh,asc}`. Setiap `col` 4 komponen
(alpha diterapkan saat emisi, paritas `with_alpha` pygame); `anchor` selalu
`"topleft"` dengan `pos` = tujuan blit pygame, `wh`/`asc` = metrik font yang
direkam oracle (Godot tidak punya API metrik font pygame).

### Deviasi (semuanya disengaja + dikunci tes)

| # | Deviasi | Alasan |
|---|---|---|
| 1 | Bayangan ellipse digambar **hitam solid** `(0,0,0,120)`, bukan tekstur ber-alpha gradasi | `draw_circle`/poligon Godot tidak punya padanan `pygame.draw.ellipse` pada surface SRCALPHA; rect + warna sumbernya identik, jadi hanya rasterisasi tepinya yang beda sub-piksel |
| 2 | Godot tidak punya primitif `draw_ellipse` → ellipse dipetakan ke poligon 32 titik (`poly`) | Satu-satunya cara menggambar ellipse di `_draw()`; bbox-nya sama persis |
| 3 | Aura true boss/ability/enrage memakai **pita annulus + `draw_arc`**, bukan lingkaran bertumpuk | Meniru semantik TIMPA `pygame.draw.circle` (lihat di atas) |
| 4 | Teks overlay diukur & dirender font Godot (Cinzel/Barlow repo), bukan SDL_ttf pygame | Metrik (`wh`, `asc`) direkam oracle dan **disuntik lewat `state["metrics"]`** supaya posisi blit yang dibandingkan identik; tanpa suntikan `BossOverlay.text_metrics` mengukur dengan font engine (`get_string_size`, tinggi = `ascent + descent` — bukan `Font.get_height()` yang ikut line gap). Lebar hasil shaping HarfBuzz selisih ±0,5% dari SDL_ttf (426 vs 428 px), jadi jalur produksi dikunci sifatnya (op terbentuk, jumlah baris entrance sama, teks ≤ `ENTRANCE_WRAP_W`/`SCREEN_W`), bukan angkanya |
| 5 | Badan generik (langkah 7) hanya jalan bila `has_renderer` false — di produksi semua 216 boss punya strip bake | Jalur fallback untuk tipe baru yang belum di-bake; pygame juga hanya menggambarnya bila renderer tidak ada |
| 6 | `entrance_timer` disimpan detik di Godot, dikonversi `int(round(t·60))` frame di `overlay_state()` | pygame menghitung frame; konversinya diuji fixture |

## Bagian B — pipeline data `boss_data.py`

`boss_data.py` bukan tabel statis: saat import, lima fungsi berjalan berurutan
dan **menimpa tabelnya sendiri in-place**, sehingga input mentahnya tidak
pernah terlihat setelah itu.

| # | Fungsi pygame | Baris | Isi |
|---|---|---|---|
| 1 | `_apply_boss_rebalancing()` | `:11452-11528` | boost piecewise HP/damage/ability + skill Q/W/E/R (mini ×2,2/1,6/1,4/1,3 lantai 7500; true ×2,4/2,0/1,6/1,45 lantai 36000; ability `max(ab, int(ab·1,25/1,35))`) |
| 2 | `_smooth_boss_progression()` | `:11552-11607` | paksa monoton per **slot wave** mini (`_slot_of_mini_wave`: 10-12 → `w10`, 13-21 → `w18`, 22+ → `w25`) dan per **level** true; baca `levels.get_level_config` |
| 3 | `_apply_boss_curve_overrides()` | `:11663-11675` | tiga kurva eksplisit true boss (HP 33 entri, damage 5, ability 5) — menang atas smoothing |
| 4 | `_normalize_hero_unlock_stats()` | `:11703-11802` | least-squares `_hero_unlock_trend` stat~cost per kelas, `clamp()` outlier (di luar 0,70..1,30×prediksi → 0,80/1,20×prediksi), lalu running-max toleransi 15% urut cost |
| 5 | `_normalize_hero_unlock_range()` | `:11815-11832` | `MELEE_ROLE_HINTS` (27 peran, `:11805`) atau `range ≤ 90` → 70; selain itu clamp 120..220; `skill_range` dinaikkan ke `range` |
| — | `get_all_boss_types()` | `:11837-11841` | `mini.update(true)` — true menimpa mini bila nama bentrok |

### Hasil migrasi

| Berkas | Peran |
|---|---|
| `godot/scripts/core/BossData.gd` (514 baris, `class_name BossData`) | Port 1:1 kelima langkah sebagai **static func** dengan data disuntik: `clone_tables`, `apply_boss_rebalancing`, `slot_of_mini_wave`, `smooth_boss_progression`, `apply_boss_curve_overrides`, `hero_unlock_trend`, `normalize_hero_unlock_stats`, `normalize_hero_unlock_range`, `get_all_boss_types`, `build(pristine, schedule)`, `load_pristine()`, `schedule_from_levels(levels)` |
| `godot/data/boss_pristine.json` | Tabel **MENTAH** (sebelum mutasi) diekstrak converter lewat **AST literal** — 162 mini + 54 true × field yang disentuh logika, `curves`, `melee_role_hints`, `mini_boss_waves`, `level_true_boss` |
| `godot/scripts/core/BossDB.gd` | `rebuild_from_pristine()` menggantikan fallback hardcode 3 boss lama (yang memakai angka **pre-pipeline** dan salah): 216 baris dihitung ulang; `load_levels()` kini jalan sebelum `load_bosses()` karena smoothing butuh jadwal |

**Angka final tetap di-bake** (`bosses.json` + `boss_stats_full.json`) dan itulah
yang dibaca runtime — sama seperti `HeroBalance.gd` (FASE 28) dan `HeroItems.gd`
(FASE 29). `BossData.gd` adalah jalur **hitung ulang**: membuktikan pipeline-nya
dipahami, dan memulihkan katalog bila berkas bake hilang.

### Adaptasi GDScript (dikunci tes)

| Python | GDScript | Kenapa |
|---|---|---|
| `int(x)` | `_py_int(x)` | pemotongan ke arah nol, bukan `round()`/`floor()` |
| `round(x)` | `_py_round(x)` | **banker's** (half-to-even): `round(2,5) == 2`; `round()` Godot half-up |
| `a / b` (int) | `float(a) / float(b)` | `/` antar int di GDScript membulatkan |
| `(c − mx) ** 2` | `pow(c − mx, 2.0)` | `pow` libm dan `x*x` beda ±1 ulp untuk ±1% nilai nyata (9 dari 864) — menggeser `sxx`, lalu clamp |
| `list.sort(key=…)` | `sort_custom` + tie-break indeks asal | sort Python **stabil**, `Array.sort_custom` tidak dijamin; banyak `cost` hero_unlock seri |
| `if hu:` | `_truthy_hu(bd)` | `None` **dan** dict kosong sama-sama falsy |
| `hu["hp"] < 0.85 * m` | `float(v) < 0.85 * float(m)` | pembanding Python float, bukan int terpangkas |

## Verifikasi

```bash
# A1. ORACLE: menjalankan Boss.draw pygame ASLI (SDL dummy) untuk 50 skenario,
#     merekam setiap primitif, mengonversinya ke op kanonik, lalu MEMVERIFIKASI
#     konversi itu dengan piksel (op digambar ulang == render asli byte-per-byte)
#     dan dengan profil alpha terukur. Fixture wajib segar (basi = gagal +
#     petunjuk regenerasi). 245 cek.
SDL_VIDEODRIVER=dummy python3 tools/test_boss_draw_parity.py
#     regenerasi HANYA kalau base_boss.py/boss_data.py memang berubah:
SDL_VIDEODRIVER=dummy python3 tools/test_boss_draw_parity.py --write-fixture

# A2. KEMBARAN Python BossOverlay.gd: 78 konstanta dibaca dari berkas .gd,
#     setiap builder disalin ulang, 647 op dibandingkan dengan fixture op demi
#     op. Tanpa engine → salah transkripsi ketahuan sebelum Godot diunduh.
python3 tools/test_boss_overlay_model_parity.py           # 104 cek

# A3. Aura true boss: pita vs render pygame SRCALPHA sungguhan; pendekatan naif
#     8×draw_circle WAJIB gagal; cek struktural (Boss.gd mendelegasikan).
SDL_VIDEODRIVER=dummy python3 tools/test_boss_true_aura_parity.py   # 53 cek

# B1. ORACLE pipeline data: model 5 langkah vs modul boss_data ASLI
#     (3024 field) + vs ekspor baker bosses.json/boss_stats_full.json
#     (3024 field) + invariant (monoton, lantai piecewise, pita clamp,
#     skill_range ≥ range) + cek struktural BossData.gd/BossDB.gd + probe
#     fit least-squares nyata. Fixture wajib segar.
SDL_VIDEODRIVER=dummy python3 tools/test_boss_data_parity.py        # 2515 cek

# Replay di engine (CI godot-check langkah 4z dan 4z2):
godot --headless --path godot res://tests/BossDrawParityTest.tscn --quit-after 400
godot --headless --path godot res://tests/BossDataParityTest.tscn --quit-after 120
# wajib "[BossDrawParityTest] PASS" / "[BossDataParityTest] PASS" tanpa
# SCRIPT ERROR / Parse Error (gate: godot/tools/godot_log_gate.py)
```

`BossDrawParityTest.gd` empat seksi: (1) op `BossOverlay` deep-equal vs fixture
647 op; (2) semantik lapisan (entrance eksklusif, bar pertama/teks terakhir,
pita tidak tumpang tindih); (3) plumbing node Boss sungguhan —
`overlay_state()` harus sama dengan state fixture setelah field dinamis diset
(membuktikan `bosses.json` → `label_top`/`entrance_text`/`color_dark`, detik →
frame, `Plate` sesudah `Visual`, tidak ada `Control` statis tersisa);
(4) raster smoke — `exec()` menggambar semua op di `_draw()` tanpa error.

`BossDataParityTest.gd` enam seksi: jadwal level, hasil 216 boss field demi
field, probe helper statis (`_py_round`/`_py_int`/`slot_of_mini_wave`/
`hero_unlock_trend` + fit nyata), purity/determinisme `build()`, kesepakatan
katalog runtime (`BossDB` vs hitung ulang), dan jalur pemulihan
`rebuild_from_pristine()`.

## Temuan run engine pertama (CI PR #229)

Run `godot-check` pertama **gagal di `BossDrawParityTest`** (36 scene lain
hijau) dan menemukan tiga hal yang lolos semua cek statis lokal — persis alasan
langkah replay engine ada:

| # | Temuan | Sebab | Perbaikan |
|---|---|---|---|
| 1 | `aura_ability_*`: Godot menghasilkan **8 op**, pygame 7 (pita ekstra `ri 84..87`) | `ability_aura_ops` di `.gd` memanggil `filled_aura_bands(…, AURA_RINGS, …)` — seharusnya `ABILITY_RINGS` (7 vs 8; pygame `range(aura_r, aura_r − 18, −3)` = 6 lingkaran + inti) | Konstanta diperbaiki, **dan** kembaran Python kini punya seksi *fidelitas transkripsi*: untuk 29 fungsi, himpunan token konstanta dan multiset literal angka di `.gd` harus identik dengan di twin (mutasi `ABILITY_RINGS → AURA_RINGS` kini gagal di langkah statis, tanpa engine) |
| 2 | `pita aura tidak ada yang tumpang tindih (123)` | Cek di scene salah rumus: membandingkan pita **berurutan** (`ro <= prev_outer`), padahal pygame menggambar dari luar ke dalam, dan dua grup aura (ability + true boss) memang saling menimpa | Cek diganti **per grup** (grup berakhir di pita `ri = 0`): dalam satu grup pita tidak boleh bertabrakan dan jumlah lebarnya harus == radius terluar (partisi cakram). Fixture: 142 pita → 21 grup, 0 tabrakan, 0 celah |
| 3 | `entrance_*`: geometri teks dari node beda (`wh [426,48]` vs `[428,29]`, `pos y 62` vs `72`) | `overlay_state()` tidak membawa metrik font pygame, jadi `text_metrics` jatuh ke font engine; tinggi memakai `Font.get_height()` yang menghitung **line gap** (48 px untuk size 24, padahal pygame 29) | Tinggi fallback jadi `ascent + descent` (deviasi 4). Scene kini menyuntik metrik fixture untuk perbandingan geometri (yang diuji plumbing angkanya) **dan** menguji jalur produksi terpisah: metrik terukur, teks ≤ `ENTRANCE_WRAP_W`/`SCREEN_W`, urutan jenis op dicatat sebagai NOTE bila shaping font membuatnya beda |

Setelah ketiganya, simulasi lokal plumbing node (44 skenario yang memenuhi
syarat, memetakan `bosses.json` → `overlay_state()` persis seperti `Boss.gd`)
cocok di semua field, dan model pita fixture tertutup 21 grup tanpa celah.

## Menambah boss / mengubah overlay

1. Ubah `bosses/base_boss.py` (overlay) atau `bosses/boss_data.py` (angka),
   lalu bake ulang: `python3 tools/convert_to_godot.py` (menulis
   `bosses.json`, `boss_stats_full.json`, `boss_pristine.json`).
2. Regenerasi fixture: `--write-fixture` pada `test_boss_draw_parity.py` dan
   `test_boss_data_parity.py`. Keduanya deterministik (byte-identik antar run).
3. Sesuaikan builder di `BossOverlay.gd` / langkah di `BossData.gd`, lalu
   jalankan kembaran Python-nya (`test_boss_overlay_model_parity.py`) — kalau
   hijau, CI engine hampir pasti hijau juga.
4. Konstanta baru harus `const` di `BossOverlay.gd`: kembaran Python
   **membacanya dari berkas .gd**, jadi angka yang ditulis dua kali langsung
   ketahuan.
