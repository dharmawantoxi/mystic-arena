# Mystic Maps GDExtension (godot++)

Port `map_components/_bundle.py` (palet + 54 tema + `PathGenerator` +
`DecorationGenerator`) ke Godot C++ GDExtension.

Dokumen desain + semantik Python↔Godot yang dikunci:
[`docs/MAPS_GODOTPP.md`](../../../docs/MAPS_GODOTPP.md). Status paritas
menyeluruh: [`docs/GODOT_PARITY.md`](../../../docs/GODOT_PARITY.md) (FASE 35).

## Tujuan

- **Paritas 1:1** dengan Python — `.h`/`.cpp` dibangkitkan dari AST
  `_bundle.py` (skema union 77 kunci, urutan kunci per tema, tipe, waypoint +
  smoothness, struktur loop dekor, replika MT19937), bukan ditulis tangan.
- **Tipe asli** — `Color`/`int64` dari tabel C++, bukan `float` semua seperti
  hasil `JSON.parse_string` Godot (`core/io/json.cpp:341`).
- **Drop-in** — `ArenaMap` memanggil `MapDBLoader`, tidak tahu backend mana
  yang jalan. Rewrite ini sekaligus menutup DUA deviasi port lama: titik lane
  float (Python me-`trunc` ke int) dan smoothness mid 10 (Python: 8).

## Struktur

```
godot/gdext/mystic_maps/
  SConstruct                        # output -> ../../addons/mystic_maps/bin/
  src/register_types.{h,cpp}        # entry mystic_maps_library_init (level SCENE)
  src/maps_processor.h              # GENERATED — class MysticMaps : RefCounted (66 baris)
  src/maps_processor.cpp            # GENERATED — tabel tema + generator (4.197 baris, 13 bind)
  selftest/godot_stub.hpp           # stub Variant/Color/Vector2/Packed (BUKAN bagian lib)
  selftest/maps_selftest.cpp        # harness stdin TAB — menjalankan .cpp di luar engine
  selftest/shim/godot_cpp/**        # header kosong: include godot-cpp jadi no-op
godot/addons/mystic_maps/
  mystic_maps.gdextension           # kunci debug/release -> berkas template_debug/template_release
  bin/libmystic_maps.*              # hasil build (di-gitignore kecuali .gitkeep)
godot/scripts/core/
  MapDB.gd                          # backend GDScript (975 baris: KEY_KINDS + PyMt + derive)
  MapDBLoader.gd                    # saklar backend (+ force_backend untuk harness)
godot/data/themes_raw.json          # skema SETIA 1:1 THEMES (convert --map-raw, AST-only)
godot/tests/
  MapDataParityTest.{gd,tscn}       # replay fixture oracle, backend GDScript (±10 ribu cek)
  MapDataGdextParityTest.{gd,tscn}  # backend DIPAKSA gdext + A/B C++ vs GDScript
  fixtures/map_data.json            # direkam _bundle.py ASLI (428 KB: katalog + lane + dekor)
tools/gen_maps_cpp.py               # Python AST -> C++ (+ --check)
tools/test_godot_map_data_parity.py # oracle statis 9.844 cek (+ --write-fixture)
tools/test_maps_cpp_selftest.py     # compile + jalankan C++ tanpa engine (19.834 cek)
.github/workflows/godot-gdext.yml   # self-test + build lib + uji paritas C++
```

`src/maps_processor.{h,cpp}` adalah **hasil generate** — jangan disunting tangan.
Ubah `tools/gen_maps_cpp.py`, lalu:

```bash
python3 tools/gen_maps_cpp.py          # regenerasi
python3 tools/gen_maps_cpp.py --check  # CI: berkas ter-commit harus identik
```

Generator **menolak** (bukan menebak): kunci tema ber-kind campuran antar tema
(selain `ambient_tint` None↔RGBA), waypoint bukan tuple-2 int, smoothness bukan
literal, struktur `generate_all` yang tidak dikenali, atau seed ≠ 42. Pesan
menyebut tema + fungsinya.

## Build

```bash
cd godot/gdext/mystic_maps
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot-cpp   # di-gitignore
scons platform=linux   target=template_debug   -j4     # dev / editor
scons platform=linux   target=template_release -j4     # export release
scons platform=android target=template_release android_arch=arm64v8 -j4
```

Atau pakai checkout godot-cpp **bersama** dengan ekstensi lain (objek compile
godot-cpp hidup di dalam direktori itu, jadi tiga lib memakai ulang hasil yang
sama — inilah yang dilakukan CI: satu clone, satu cache, tiga lib):

```bash
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot/gdext/godot-cpp
ln -s ../godot-cpp godot/gdext/mystic_maps/godot-cpp
ln -s ../godot-cpp godot/gdext/mystic_levels/godot-cpp
ln -s ../godot-cpp godot/gdext/mystic_skills/godot-cpp
```

Setelah build, nyalakan jalurnya:

```
mystic/maps/use_gdext_maps=true        ; di godot/project.godot
```

atau dari kode/harness: `MapDBLoader.force_backend("gdext")`. Loader mencetak
satu baris per perubahan backend — CI me-`--require` baris ini:

```
[MapDBLoader] GDExtension MysticMaps aktif (godot++ C++) — katalog 54:forest-hollowbane:2984
```

Kalau lib tidak ada (atau symbol-nya salah), loader jatuh ke GDScript **tanpa
error** — F5 di mesin tanpa toolchain tetap normal.

## Self-test: menjalankan C++ tanpa engine

`selftest/` bukan bagian lib (`SConstruct` hanya `Glob("src/*.cpp")`). Ia
meng-include `src/maps_processor.cpp` **apa adanya** dan menyediakan stub
`Variant`/`Color`/`Vector2`/`Packed*`/`Dictionary` yang meniru semantik Godot
4.3, jadi tabel + generator bisa dieksekusi di mesin mana pun yang punya
compiler — tanpa godot-cpp (±10 menit) dan tanpa engine:

```bash
python3 tools/test_maps_cpp_selftest.py       # compile + jalankan + bandingkan oracle
```

200 perintah, 19.834 cek: 54 tema × kunci union (nilai + tipe + urutan),
palet, `theme_index`/`build_theme`, `make_curved_path` (kasus tepi + 4 ukuran
map), `generate_lanes`/`generate_river`, dan `generate_decorations` penuh
(14 kategori — replika MT19937 `init_by_array` yang bit-eksak dengan
`random.seed(42)` CPython).

## Verifikasi

```bash
python3 tools/gen_maps_cpp.py --check             # 1. kesegaran transpile
python3 tools/test_godot_map_data_parity.py       # 2. oracle statis (9.844 cek)
python3 tools/test_maps_cpp_selftest.py           # 3. eksekusi C++ (19.834 cek)
godot --headless --path godot res://tests/MapDataParityTest.tscn      --quit-after 120
godot --headless --path godot res://tests/MapDataGdextParityTest.tscn --quit-after 120
```

CI: langkah 1–2 + `MapDataParityTest` di `godot-check.yml` (tanpa compiler);
langkah 1, 3, build lib, `nm -D` symbol check, dan kedua scene maps di
`godot-gdext.yml`.

## Batas yang disengaja

- Flag produksi tetap `false` — jalur pemain masih GDScript sampai lib tersedia
  untuk semua platform rilis (`build-android-godot.yml` belum memanggil scons).
- CI hanya membuild linux x86_64; `.gdextension` sudah memetakan
  windows/macos/android/web tapi lib-nya belum pernah dikompilasi di CI.
- Renderer pygame (`static/decoration/shop/dynamic_renderer`: `pygame.draw`,
  partikel, kabut) TIDAK dimigrasi — Fase 3 sudah meng-cover-nya lewat bake
  tekstur statik; `DynamicRenderer` non-deterministik dan tidak bisa di-oracle.
- `_build_decor` ArenaMap SENGAJA tetap scatter kurasi Godot (bukan posisi
  `generate_decorations`) — tampilannya sudah dikunci; posisi pygame tersedia
  lewat loader untuk dipakai nanti.
- Python mengembalikan dict tema live (bisa dimutasi); kedua backend Godot
  mengembalikan Dictionary SEGAR — deviasi terdokumentasi, dikunci fixture
  (isolasi mutasi).
