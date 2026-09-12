# Mystic Levels GDExtension (godot++)

Port `levels/level_data.py` (Python, 2.347 baris: 54 literal dict `LEVEL_N` +
`ALL_LEVELS` + `get_level_config` / `get_level_count` / `is_level_unlocked` /
`get_next_level`) ke Godot C++ GDExtension.

Dokumen desain + semantik Python↔Godot yang dikunci:
[`docs/LEVELS_GODOTPP.md`](../../../docs/LEVELS_GODOTPP.md). Status paritas
menyeluruh: [`docs/GODOT_PARITY.md`](../../../docs/GODOT_PARITY.md) (FASE 34).

## Tujuan

- **Paritas 1:1** dengan Python — `.h`/`.cpp` dibangkitkan dari AST
  `level_data.py` (skema field, urutan kunci, tipe, urutan insert
  `mini_bosses`), bukan ditulis/diterjemahkan tangan.
- **Tipe asli** — `int64`/`double` dari tabel C++, bukan `float` semua seperti
  hasil `JSON.parse_string` Godot (`core/io/json.cpp:341`).
- **Drop-in** — `BossDB` / `GameManager` / `SaveManager` memanggil
  `LevelDBLoader`, tidak tahu backend mana yang jalan.

## Struktur

```
godot/gdext/mystic_levels/
  SConstruct                        # output -> ../../addons/mystic_levels/bin/
  src/register_types.{h,cpp}        # entry mystic_levels_library_init (level SCENE)
  src/levels_processor.h            # GENERATED — class MysticLevels : RefCounted
  src/levels_processor.cpp          # GENERATED — tabel POD 54 level + 9 method static
  selftest/godot_stub.hpp           # stub Variant/Array/Dictionary/String (BUKAN bagian lib)
  selftest/levels_selftest.cpp      # harness stdin — menjalankan .cpp di luar engine
  selftest/shim/godot_cpp/**        # header kosong: include godot-cpp jadi no-op
godot/addons/mystic_levels/
  mystic_levels.gdextension         # kunci debug/release -> berkas template_debug/template_release
  bin/libmystic_levels.*            # hasil build (di-gitignore kecuali .gitkeep)
godot/scripts/core/
  LevelDB.gd                        # backend GDScript (data/levels.json) — jalur default
  LevelDBLoader.gd                  # saklar backend (+ force_backend untuk harness)
godot/tests/
  LevelDataParityTest.{gd,tscn}     # replay fixture oracle, backend GDScript
  LevelDataGdextParityTest.{gd,tscn}# backend DIPAKSA gdext + A/B C++ vs GDScript
  fixtures/level_data.json          # direkam dari level_data.py ASLI (nilai + TIPE Python)
tools/gen_levels_cpp.py             # Python AST -> C++ (+ --check)
tools/test_godot_level_data_parity.py   # oracle statis (+ --write-fixture)
tools/test_levels_cpp_selftest.py   # compile + jalankan C++ tanpa engine
.github/workflows/godot-gdext.yml   # self-test + build lib + uji paritas C++
```

`src/*.h` dan `src/*.cpp` adalah **hasil generate** — jangan disunting tangan.
Ubah `tools/gen_levels_cpp.py`, lalu:

```bash
python3 tools/gen_levels_cpp.py          # regenerasi
python3 tools/gen_levels_cpp.py --check  # CI: berkas ter-commit harus identik
```

Generator **menolak** (bukan menebak) kalau data Python-nya tidak seragam:
tipe campuran per kunci antar level (`1.05` vs `1`), urutan kunci berbeda antar
level, atau field nullable selain `unlock_after_level`. Pesannya menyebut level
+ field-nya.

## Build

```bash
cd godot/gdext/mystic_levels
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot-cpp   # di-gitignore
scons platform=linux   target=template_debug   -j4     # dev / editor
scons platform=linux   target=template_release -j4     # export release
scons platform=android target=template_release android_arch=arm64v8 -j4
```

Atau pakai checkout godot-cpp **bersama** dengan ekstensi lain (objek compile
godot-cpp hidup di dalam direktori itu, jadi dua lib memakai ulang hasil yang
sama — inilah yang dilakukan CI: satu clone, satu cache, dua lib):

```bash
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot/gdext/godot-cpp
ln -s ../godot-cpp godot/gdext/mystic_levels/godot-cpp
ln -s ../godot-cpp godot/gdext/mystic_skills/godot-cpp
```

Setelah build, nyalakan jalurnya:

```
mystic/levels/use_gdext_levels=true        ; di godot/project.godot
```

atau dari kode/harness: `LevelDBLoader.force_backend("gdext")`. Loader mencetak
satu baris per perubahan backend — CI me-`--require` baris ini:

```
[LevelDBLoader] GDExtension MysticLevels aktif (godot++ C++) — katalog 54:1-54:162
```

Kalau lib tidak ada (atau symbol-nya salah), loader jatuh ke GDScript **tanpa
error** — F5 di mesin tanpa toolchain tetap normal.

## Self-test: menjalankan C++ tanpa engine

`selftest/` bukan bagian lib (`SConstruct` hanya `Glob("src/*.cpp")`). Ia
meng-include `src/levels_processor.cpp` **apa adanya** dan menyediakan stub
`Variant`/`Array`/`Dictionary`/`String` yang meniru semantik Godot 4.3, jadi
tabel + logika helper bisa dieksekusi di mesin mana pun yang punya compiler —
tanpa godot-cpp (±10 menit) dan tanpa engine:

```bash
python3 tools/test_levels_cpp_selftest.py       # compile + jalankan + bandingkan oracle
```

±2 detik, 253 cek. Yang diuji: 54 baris × 17 field (nilai + tipe + urutan
kunci), `row_index`, `get_level_config`, `get_level_count`, `is_level_unlocked`,
`get_next_level`, `py_contains`, dan dua deviasi bool/int yang terdokumentasi.
Perutean argumennya meniru `LevelDBLoader` (float tak bulat / non-angka tidak
dikirim ke C++ — itu jalur GDScript), jadi self-test tidak diam-diam
"memperbaiki" deviasi yang sudah diputuskan di loader.

## Verifikasi

```bash
python3 tools/gen_levels_cpp.py --check             # 1. kesegaran transpile
python3 tools/test_godot_level_data_parity.py       # 2. oracle statis (5.162 cek)
python3 tools/test_levels_cpp_selftest.py           # 3. eksekusi C++ (253 cek)
godot --headless --path godot res://tests/LevelDataParityTest.tscn      --quit-after 120
godot --headless --path godot res://tests/LevelDataGdextParityTest.tscn --quit-after 120
```

CI: langkah 1–2 + `LevelDataParityTest` di `godot-check.yml` (tanpa compiler);
langkah 1, 3, build lib, `nm -D` symbol check, dan kedua scene level di
`godot-gdext.yml`.

## Batas yang disengaja

- Flag produksi tetap `false` — jalur pemain masih GDScript sampai lib tersedia
  untuk semua platform rilis (`build-android-godot.yml` belum memanggil scons).
- CI hanya membuild linux x86_64; `.gdextension` sudah memetakan
  windows/macos/android/web tapi lib-nya belum pernah dikompilasi di CI.
- `BossDB.get_level()` tetap scan `BossDB.levels` (bukan delegasi ke loader)
  supaya katalog yang dipegang `BossDB` selalu konsisten untuk 20+ pemakainya.
