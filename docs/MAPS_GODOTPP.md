# Migrasi `map_components` → godot++ (GDExtension C++)

Port `map_components/_bundle.py` — palet + 54 tema + `PathGenerator` +
`DecorationGenerator` — ke tiga lapisan dari satu sumber: Python (oracle),
GDScript (`MapDB.gd` + `data/themes_raw.json`), dan C++ (`MysticMaps`,
GDExtension `mystic_maps`). Status paritas menyeluruh:
[`docs/GODOT_PARITY.md`](GODOT_PARITY.md) (FASE 35).

Cakupan yang SENGAJA keluar: renderer pygame (`static_renderer`,
`decoration_renderer`, `shop_renderer`, `dynamic_renderer` — `pygame.draw`
dan partikel non-deterministik). Fase 3 sudah meng-cover render statik lewat
bake tekstur; yang dimigrasi di sini adalah **data + generator deterministik**.

## Kenapa C++ untuk data peta?

Alasan yang sama dengan levels (FASE 34) plus satu alasan baru:

1. **Satu sumber, nol drift.** Waypoint lane, ambang validator dekor, dan
   stream RNG pernah ditulis tangan TIGA kali (pygame, `ArenaMap._curved_path`,
   scatter `_build_decor`) — dan dua di antaranya diam-diam menyimpang
   (lihat §3). Tabel C++ dibangkitkan dari AST `_bundle.py`, jadi angkanya
   tidak bisa basi tanpa CI merah.
2. **Tipe asli.** `JSON.parse_string` Godot 4.3 mengubah semua angka jadi
   float (`core/io/json.cpp:341`); jalur C++ mengembalikan `Color`/`int64`
   yang benar tanpa normalisasi.
3. **Drop-in.** `ArenaMap` memanggil `MapDBLoader` — backend C++ atau GDScript
   tidak mengubah satu baris pun pemakainya.

## Arsitektur

```
map_components/_bundle.py            (sumber kebenaran, TIDAK disunting)
  │ AST (tools/gen_maps_cpp.py)       │ AST (convert --map-raw)
  ▼                                   ▼
gdext/mystic_maps/src/               godot/data/themes_raw.json
  maps_processor.h  (66 baris)         (54 tema + 52 palet, skema SETIA:
  maps_processor.cpp (4.197 baris)      kunci + urutan + tuple asli)
  13 method static bound              │
        │                             ▼
        │                    scripts/core/MapDB.gd (975 baris)
        │                      KEY_KINDS + PyMt + derive_palette
        ▼                             │
scripts/core/MapDBLoader.gd (311 baris: saklar + force_backend + cache)
        │
        ▼
scenes/map/ArenaMap.gd (themes + lane/river via loader; kurasi 4 tema tetap)
```

### Peta berkas

| Berkas | Peran |
|---|---|
| `tools/gen_maps_cpp.py` (1.199 baris) | AST `_bundle.py` → `maps_processor.h/.cpp` (+ `--check` byte-identik) |
| `tools/convert_to_godot.py` `--map-raw` | AST `_bundle.py` → `themes_raw.json` (tanpa pygame/SDL) |
| `godot/scripts/core/MapDB.gd` | Backend GDScript: normalisasi tipe, Catmull-Rom, PyMt, dekor, derive |
| `godot/scripts/core/MapDBLoader.gd` | Saklar backend (`mystic/maps/use_gdext_maps` + `ClassDB`) |
| `godot/gdext/mystic_maps/selftest/` | Stub Variant + harness TAB (BUKAN bagian lib) |
| `tools/test_godot_map_data_parity.py` (1.387 baris) | Oracle statis 9.844 cek (+ `--write-fixture`) |
| `tools/test_maps_cpp_selftest.py` | Eksekusi C++ tanpa engine: 200 perintah, 19.834 cek |
| `godot/tests/fixtures/map_data.json` (428 KB) | Oracle Python terekam: katalog + kurva + lane + dekor |
| `godot/tests/MapDataParityTest.{gd,tscn}` | Replay fixture, backend GDScript (±10 ribu cek) |
| `godot/tests/MapDataGdextParityTest.{gd,tscn}` | Backend DIPAKSA gdext + A/B C++ vs GDScript |

## Bentuk data di C++: entri POD + kind per entri

Berbeda dengan levels (skema SERAGAM 17 kolom → struct POD kolom), 54 tema map
TIDAK seragam: `forest` 55 kunci, `haunted` 69 kunci (22 ekstra, 8 `has_*`
hilang). Union-nya 77 kunci — struct 77 kolom akan boros dan salah secara
semantik (`theme.get(k, default)` di konsumen Python bergantung pada kunci
yang HILANG memang tidak ada). C++ menyimpan **entri per tema**
`{kunci, kind, v0..v3, string, list_idx}` + tabel colorlist terpisah, persis
urutan literal dict Python. `get_theme`/`build_theme` merakit `Dictionary`
ordered dari entri — urutan kunci == `dict.keys()` Python.

Waypoint lane/river disimpan sebagai tabel koordinat; spline Catmull-Rom
dihitung saat runtime dengan urutan operasi double yang sama persis dengan
Python (`t3 = t*t*t`, lalu `int()` = trunc). `generate_decorations`
menjalankan replika MT19937 + 14 loop + validator yang sama — bukan tabel
bake — supaya ukuran map berapa pun tetap paritas.

## API

13 method static ter-bind (urutan `_bind_methods`): `tile_size`, `palettes`,
`theme_names`, `theme_count`, `get_theme`, `all_themes`, `catalog_signature`,
`make_curved_path`, `generate_lanes`, `generate_river`,
`generate_decorations`, `build_theme`, `theme_index`.

Dua API SENGAJA tidak di-bind (implementasi GDScript tunggal di `MapDB.gd`,
backend-agnostik karena inputnya sudah setipe dari kedua backend):
`derive_palette` (dict mentah → palet turunan 45 kunci skema ArenaMap) dan
`round_half_even` (helper internal). `MapDBLoader.theme_palette(nama)` =
`derive(get_theme(nama))` — satu-satunya yang dipakai `ArenaMap`.

## Semantik yang dikunci (Python vs Godot)

### 1. Union 77 kunci non-seragam + `ambient_tint` nullable

Kind per kunci: `bool` 25, `color3` 41, `color4` 2, `colorlist3` 2, `int` 2,
`str` 5. Satu-satunya campuran antar tema yang diizinkan generator:
`ambient_tint` (`None` hanya di forest, RGBA di 53 lainnya). C++ melebur kind
kolomnya jadi `COLOR4` + flag NIL per entri; GDScript menandainya `color4?`
di `KEY_KINDS` supaya `null` tetap legal. Kunci baru yang belum terdaftar =
oracle merah (closed-world dua arah).

### 2. Semua angka JSON jadi `float`

`themes_raw.json` menyimpan tuple `(28, 55, 32)` sebagai `[28.0, 55.0, 32.0]`.
`MapDB._normalize_row` memulihkan `Color`/`PackedColorArray`/`int` per
`KEY_KINDS`, per panggilan (bukan cache) supaya tiap `get_theme()` SEGAR
(lihat §11). Urutan kunci = urutan dokumen = urutan literal Python
(`json.dump` + `JSON.parse_string` sama-sama ordered — diaser per tema).

### 3. Trunc `int()` titik spline + smoothness mid 8 — **deviasi yang ditutup**

Port lama `ArenaMap._curved_path` menyimpan titik float (`Vector2(x, y)`)
padahal Python me-`trunc` tiap titik (`int(x), int(y)`), dan memakai
smoothness 10 untuk mid padahal Python memakai 8 (65 titik, bukan 81).
Minion berjalan di jalur yang sedikit beda + waypoint 2× lebih banyak.
Kedua backend baru me-`trunc` dan memakai smoothness per lane dari AST
(top 10, mid 8, bot 10, river 10); `ArenaMap` lama dihapus total dan
diganti panggilan loader. Baterai 9–10 engine test mengunci titik PERSIS
di 1280×720 dan 1025×769 (dimensi ganjil menangkap semantik `//` vs `/`).

### 4. `generate_lanes` tuple → Dictionary

Python mengembalikan tuple `(top, mid, bot)`; kedua backend Godot
mengembalikan Dictionary `{top, mid, bot}` (urutan insert sama). Normalisasi
ini dikunci fixture + self-test C++ + A/B engine.

### 5. MT19937: `init_by_array`, bukan `init_genrand`

`DecorationGenerator.generate_all` deterministik via `random.seed(42)`, dan
`RandomNumberGenerator` Godot (PCG) tidak se-stream dengan Mersenne Twister
Python — apalagi CPython me-seed int lewat `init_by_array`, bukan
`init_genrand` (draw pertama seed 42: **2746317213**, bukan 1608637542).
Ketiga sisi membawa replika MT19937 sendiri (C++/generated, GDScript/`PyMt`,
cermin Python di oracle) yang semuanya dibuktikan se-stream dengan
`random.Random(42)`: 500 `getrandbits` + 500 `randint` + 200 `choice`.

Dua jebakan yang ditangkap oracle saat FASE 35 (bukan teori):

- **Preseden `^` vs `+`.** Transkripsi pertama menulis
  `mt[i] ^ suku + key + j` — karena `^` LEBIH RENDAH dari `+` (GDScript
  seperti C/Python), artinya menjadi `mt[i] ^ (suku + key + j)` dan stream
  salah total. Bentuk benar `mt19937ar.c`: `(mt[i] ^ suku) + key + j`.
  Kurung luarnya dikomentari WAJIB di kedua replika.
- **State global.** Python me-`re-seed()` di akhir `generate_all` (no-op
  sistem); C++/GDScript memakai instance RNG lokal per panggilan — tidak ada
  state yang bisa bocor antar `generate_decorations()`.

### 6. Bug base lingkaran-1 direplika

`_too_close_to_base` Python punya bug: lingkaran pertama berpusat di
`(120, 120)`, bukan base Radiant —
`hypot(x - 120, map_h - 120 - (map_h - y))`. Ketiga sisi mereplika bug ini
verbatim (dikomentari JANGAN DIPERBAIKI + dikunci oracle E3); "memperbaiki"
akan menggeser penempatan dekor vs pygame.

### 7. `hypot` float32 vs float64 selalu sepakat — dengan bukti

Validator memakai `Vector2.length()` (sqrt float32) vs `math.hypot` (double).
Keduanya SELALU sepakat di sini, dan alasannya ditulis di kode: dx²+dy² <
2²⁴ (eksak di kedua presisi), sqrt correctly-rounded di keduanya, dan semua
ambang adalah int — jarak dua titik integer-koordinat tidak pernah mendarat
dalam setengah ulp dari bilangan bulat (|sqrt(S) − T| ≥ ~1/2T untuk S ≠ T²).

### 8. § bankir: `round()` Python di GDScript

Converter memakai `round()` Python = half-even; `round()` GDScript =
half-away. Tiga kasus di domain aktual memang mendarat di batas dan
dibulatkan berbeda — tanpa `round_half_even`, palet Godot meleset 1 LSB.

Yang lebih dalam: `round(x, nd)` untuk `fog_alpha`/`energy` TIDAK bisa
ditulis naif `round_half_even(x * 10^nd) / 10^nd`. `royal.energy` membuktikannya:
x = 1.1685000000000001 (tepat DI ATAS batas) → `round(x,3)` = **1.169**, tapi
x*1000 dibulatkan dulu ke double menjadi 1168.5 tepat → 1.168. Bahkan
pembulatan repr terpendek pun salah (`repr(x)` = `"1.1685"` tepat di batas →
1.168). Satu-satunya jalan benar: bulatkan nilai BINER eksak.

`MapDB._round_nd` melakukannya tanpa string: dekomposisi IEEE-754
(`encode_double` → mantissa 53 bit + eksponen), P = m × 10^nd dalam dua limb
int64 (hi×S < 2³⁶, lo×S < 2⁴⁶ — muat, diaser cermin), pembandingan sisa
eksak dengan aturan half-even, lalu SATU divisi correctly-rounded (= double
terdekat ke desimal yang benar = yang dikembalikan CPython). Cermin Python-nya
dibuktikan == `round()` pada 32.500 nilai (sapuan acak seed-tetap + tetangga
batas desimal), dan engine test mengunci `royal.energy = 1.169` ujung-ke-ujung.

### 9. `.a8`, bukan `.a`

Kanal alpha `Color` disimpan float32 — `tc.a` meleset ~1e-9 dari `a/255.0`
double Python dan bisa membalikkan pembulatan desimal di kasus batas.
Derivasi memakai `.a8` (int) lalu `/255.0` dalam double, urutan op sama
dengan converter. Konsumsi warna (termasuk `Color(html)` di engine test)
dibandingkan via `r8`/`to_html`, bukan float32.

### 10. Fallback `forest`, OOB → `{}`

`get_theme` tak dikenal → baris forest (paritas `THEMES.get(nama,
FOREST_THEME)`); `build_theme` di luar jangkauan → Dictionary kosong (C++
mengembalikan dict kosong; GDScript sama). `theme_index` tak dikenal → −1.

### 11. Deviasi yang **disengaja**: dict SEGAR vs objek live

Python mengembalikan objek tema live (bisa dimutasi konsumen); kedua backend
Godot mengembalikan Dictionary SEGAR tiap panggilan (termasuk
`PackedColorArray` baru — tidak ada aliasing). Tidak ada konsumen Godot yang
memutasi, dan baterai 12 engine test mengunci isolasi ini (mutasi + append
lalu baca ulang).

### 12. Struktur `generate_all`: while landmark, obor, re-seed

14 kategoriAttempts `[45, 35, 12, 15, 12, 10, 15, 25, 20, 20, 20, 8]`, while
landmark `<30` + `<240` sebaris, obor border deterministik (18 titik di
1280×720 — tanpa RNG), `random.seed()` penutup. Batas randint `-3` vs `-2`
(rocks/bushes) dan sisi R/D per seksi semuanya dikunci dua-sisi (AST ==
tabel == teks GDScript).

## Nama berkas lib: `debug` ≠ `template_debug`

Konvensi yang sama dengan FASE 33/34 (dan bug yang sama dihindari):
kunci `[libraries]` memakai nama target Godot (`linux.debug.x86_64`),
nilainya memakai nama berkas scons/godot-cpp
(`libmystic_maps.linux.template_debug.x86_64.so`). Arch Android memakai nama
godot-cpp (`arm64`/`arm32`/`x86_64`). CI memverifikasi symbol
`mystic_maps_library_init` dengan `nm -D`.

## Build

```bash
cd godot/gdext/mystic_maps
ln -s ../godot-cpp godot-cpp   # atau clone godot-4.3-stable
scons platform=linux target=template_debug -j4
```

Lalu `mystic/maps/use_gdext_maps=true` di `project.godot`, atau
`MapDBLoader.force_backend("gdext")` dari kode. Tanpa lib, loader jatuh ke
GDScript tanpa error (pola yang sama dengan levels/skills — tidak ada
identifier `MysticMaps` di `MapDBLoader.gd`, semua akses via string
`ClassDB`).

## Lima lapis verifikasi

1. `tools/gen_maps_cpp.py --check` di **kedua** workflow (tabel ter-commit
   byte-identik hasil transpile AST).
2. `tools/test_godot_map_data_parity.py` — **9.844 cek** tanpa pygame/engine/
   compiler: JSON setia, `KEY_KINDS` closed-world, keymap/flag converter,
   waypoint + smoothness, struktur dekor dua-sisi, stream MT, bankir +
   sapuan 32.500 nilai, derive == converter 54 tema, `--check`, permukaan
   API tiga sisi, kesegaran `themes.json` + fixture, wiring closed-world.
3. `tools/test_maps_cpp_selftest.py` — **mengeksekusi** `maps_processor.cpp`
   apa adanya lewat stub (200 perintah, **19.834 cek**).
4. Compile+link nyata (`scons` + godot-cpp 4.3, symbol diverifikasi `nm -D`).
5. `MapDataParityTest` (backend GDScript, ±10 ribu cek) +
   `MapDataGdextParityTest` (backend DIPAKSA C++ + A/B seluruh permukaan API)
   memutar ulang `map_data.json` yang direkam `_bundle.py` ASLI: 54 tema,
   5 kurva, lane/river 2 ukuran, dekor 2 varian (101 + 105 entri), derive
   54 palet vs `themes.json`, wiring `ArenaMap` (scene asli).

## Batas yang disengaja

- Flag produksi tetap `false` — jalur pemain masih GDScript sampai lib tersedia
  untuk semua platform rilis. CI hanya membuild linux x86_64.
- Renderer pygame tidak dimigrasi (lihat Cakupan di atas).
- `_build_decor` ArenaMap tetap scatter kurasi Godot (keputusan tercatat di
  kode + README): posisi pygame tersedia via loader untuk dipakai nanti.
- `map_components/_bundle.py` **tidak disunting** — deviasi Godot dicatat dan
  dikunci fixture, bukan "diperbaiki" di sumber (`docs/MIGRASI_1_1.md`).

## Testing

```bash
# 1. kesegaran transpile (tanpa compiler, detik)
python3 tools/gen_maps_cpp.py --check
# 2. oracle statis: data + tipe + tabel C++ + wiring (tanpa engine/pygame)
python3 tools/test_godot_map_data_parity.py
# 2b. regenerasi fixture HANYA bila _bundle.py berubah
python3 tools/test_godot_map_data_parity.py --write-fixture
# 3. jalankan C++ di luar engine (butuh g++; tanpa godot-cpp)
python3 tools/test_maps_cpp_selftest.py
# 4. paritas runtime di engine (butuh lib + Godot 4.3)
godot --headless --path godot res://tests/MapDataParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/MapDataGdextParityTest.tscn --quit-after 120
```

## Referensi

- Sumber: `map_components/_bundle.py` (palet, 54 `*_THEME`, `THEMES`,
  `_NS_generators.PathGenerator/DecorationGenerator`), `_render.py`
  (konsumen kanonis: urutan konkatenasi lane, posisi toko).
- Converter: `tools/convert_to_godot.py` (`export_themes`,
  `_derive_theme_extras`, `_fog_from_theme`, `export_map_raw`).
- Pola FASE 33/34: `docs/HERO_SKILLS_GODOTPP.md`, `docs/LEVELS_GODOTPP.md`.
