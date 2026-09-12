# Migrasi `levels` → godot++ (GDExtension C++)

`levels/level_data.py` (2.347 baris: 54 literal dict `LEVEL_N` + `ALL_LEVELS` +
empat helper) sekarang punya **tiga** wajah dari satu sumber:

| Lapisan | Berkas | Peran |
|---|---|---|
| Python | `levels/level_data.py` | **oracle** — tidak pernah disesuaikan mengikuti Godot (`docs/MIGRASI_1_1.md`) |
| GDScript | `godot/scripts/core/LevelDB.gd` + `godot/data/levels.json` | jalur produksi default (tanpa compiler) |
| C++ (godot++) | `godot/gdext/mystic_levels/src/levels_processor.{h,cpp}` → `MysticLevels` | opt-in lewat `mystic/levels/use_gdext_levels` |

Fase ini (FASE 34) melanjutkan pola FASE 33 (`hero_skills` →
[HERO_SKILLS_GODOTPP.md](HERO_SKILLS_GODOTPP.md)): kode C++ **dibangkitkan dari
AST Python**, bukan diterjemahkan tangan; saklar backend di loader; harness yang
memaksa oracle dilewatkan ke C++; dan CI yang membuild lib sungguhan.

Status paritas menyeluruh: [GODOT_PARITY.md](GODOT_PARITY.md) (FASE 34).

## Kenapa C++ untuk data yang cuma 54 baris?

Jujur: katalog level **bukan** hot path sebesar `update_timers` skill (yang
dipanggil tiap frame × tiap hero). Nilai migrasi ini ada di empat hal lain:

1. **Satu sumber kebenaran.** `tools/gen_levels_cpp.py` membaca AST
   `level_data.py` — skema field, urutan kunci, tipe, sampai urutan insert
   `mini_bosses` — lalu memancarkan tabel C++. Menambah level ke-55 atau field
   ke-18 di Python otomatis mengubah C++; `--check` di CI menangkap kalau ada
   yang lupa regenerasi.
2. **Tipe asli.** `JSON.parse_string` Godot 4.3 mengubah **semua** angka jadi
   double (`core/io/json.cpp:341`), jadi `levels.json` memberi `starting_gold =
   1000.0`, bukan `1000`. Jalur C++ mengembalikan `int64` asli; jalur GDScript
   memulihkannya lewat `FIELD_KINDS` + `_normalize_row()`. Keduanya dikunci
   fixture yang merekam **tipe Python** tiap field.
3. **Menutup bug semantik yang sudah ada di produksi** — `x in list` Python
   memakai `==`, `Array.has()` Godot memakai `hash_compare` yang strict tipe
   (lihat §4). Bug ini nyata (level terkunci lagi setelah restart) dan baru
   ketahuan karena migrasi ini memaksa `is_level_unlocked` dibaca dari sumbernya.
4. **Pola yang sudah dibayar.** Loader, `.gdextension`, harness A/B, log gate,
   dan workflow GDExt sudah ada dari FASE 33; menambah lib ketiga (dua yang
   dibuild CI) jauh lebih murah daripada membangun polanya.

## Arsitektur

```
levels/level_data.py  (oracle Python — 54 level × 17 field + 4 helper)
  │
  ├─ tools/convert_to_godot.py --levels ─> godot/data/levels.json
  │                                              │
  │                                    scripts/core/LevelDB.gd  (GDScript,
  │                                              │   FIELD_KINDS + normalisasi tipe)
  ├─ tools/gen_levels_cpp.py ─> gdext/mystic_levels/src/levels_processor.{h,cpp}
  │       (--check di CI)              │ scons + godot-cpp
  │                                    ▼
  │             addons/mystic_levels/bin/libmystic_levels.<platform>.<target>.<arch>.so
  │                                    │  addons/mystic_levels/mystic_levels.gdextension
  │                                    ▼
  └────────────────────> scripts/core/LevelDBLoader.gd   (saklar backend)
                                     ▲   ▲   ▲
              BossDB.load_levels() ──┘   │   └── SaveManager.is_level_completed()
        GameManager.level_count() /       │            (LevelDB.py_contains)
        next_level_number() /             │
        is_level_unlocked() ──────────────┘
                       (20+ pemakai lain tetap lewat BossDB.levels / get_level)
```

### Peta berkas

```
godot/gdext/mystic_levels/
  SConstruct                        # output -> ../../addons/mystic_levels/bin/
  src/register_types.{h,cpp}        # entry mystic_levels_library_init (level SCENE)
  src/levels_processor.h            # GENERATED  —   55 baris, class MysticLevels
  src/levels_processor.cpp          # GENERATED  —  682 baris, tabel POD + 9 method
  selftest/godot_stub.hpp           # stub Variant/Array/Dictionary/String (BUKAN lib)
  selftest/levels_selftest.cpp      # harness stdin: menjalankan .cpp di luar engine
  selftest/shim/godot_cpp/**        # header kosong supaya include godot-cpp no-op
godot/addons/mystic_levels/
  mystic_levels.gdextension         # kunci debug/release -> berkas template_*
  bin/.gitkeep                      # lib hasil build di-gitignore
godot/scripts/core/
  LevelDB.gd                        # 257 baris — backend GDScript (levels.json)
  LevelDBLoader.gd                  # 266 baris — saklar backend + perutean tipe
godot/tests/
  LevelDataParityTest.{gd,tscn}     # 541 baris — replay fixture, backend GDScript
  LevelDataGdextParityTest.{gd,tscn}# 149 baris — memaksa backend C++ + A/B
  fixtures/level_data.json          # 117 KB — direkam dari level_data.py ASLI
tools/
  gen_levels_cpp.py                 # 707 baris — AST Python -> C++ (+ --check)
  test_godot_level_data_parity.py   # 1.178 baris — oracle statis (+ --write-fixture)
  test_levels_cpp_selftest.py       # 396 baris — compile + jalankan C++ tanpa engine
.github/workflows/
  godot-check.yml                   # statis + LevelDataParityTest (tanpa compiler)
  godot-gdext.yml                   # self-test C++ + build lib + uji jalur C++
```

## Bentuk data di C++: POD, bukan `Variant` statis

```cpp
struct MiniBossSlot { const char *wave; const char *boss; };
struct LevelRow {
    int64_t level_number;  const char *name;  const char *description;
    double enemy_hp_mult;  double enemy_damage_mult;  double enemy_speed_mult;
    int64_t castle_start_level;  int64_t starting_gold;  int64_t starting_castle_level;
    const char *map_theme;  const char *bgm_track;
    const MiniBossSlot *mini_bosses;  int64_t mini_bosses_count;
    const char *true_boss;
    int64_t meta_gold_reward_win, meta_gold_reward_replay, meta_gold_reward_lose;
    int64_t unlock_after_level;  bool has_unlock_after_level;   // nullable
};
const MiniBossSlot kMini3[] = { {"25","varkul"}, {"10","xerathis"}, {"17","nyzrak"} };
const LevelRow kLevels[] = { /* 54 baris */ };
const int64_t kLevelCount = 54;
```

Kenapa bukan `static const Dictionary kLevels[]`:

- `Variant`/`Dictionary` statis di dalam lib GDExtension hidup di luar kendali
  urutan init/teardown engine — constructed saat `dlopen`, destroyed saat
  `dlclose`, dan destructor `Variant` memanggil balik ke engine yang mungkin
  sudah mati. Tabel POD (`const char *`, `int64_t`, `double`) tidak punya
  masalah itu dan bisa di-`nm`/di-inspeksi.
- `build_row(index)` membangun `Dictionary` **segar** tiap panggilan dengan
  urutan kunci persis literal dict Python. Tidak ada state bersama yang bisa
  dimutasi pemanggil (Python `ALL_LEVELS[i]` memang bisa dimutasi, tapi tidak
  ada satu pun pemakai Godot yang melakukannya — diaudit saat migrasi).
- Kolom nullable pakai pasangan nilai + `bool has_` (hanya
  `unlock_after_level`, yang `None` hanya untuk level 1). Generator **menolak**
  (bukan menebak) kalau menemukan float nullable atau `mini_bosses` nullable.

Generator juga menolak, dengan pesan yang menyebut level + field-nya:

- tipe campuran per kunci di seluruh katalog (`1.05` di satu level, `1` di level
  lain) — di Python itu sah, di C++ satu kolom punya satu tipe. Solusinya di
  sumber: tulis `1.05` di semua level.
- urutan kunci yang tidak seragam antar level (17 field harus urutan sama).

## API

Semua method `static`, di-bind lewat `ClassDB::bind_static_method("MysticLevels", …)`:

| `MysticLevels` (C++) | `levels/__init__.py` | Catatan |
|---|---|---|
| `all_levels() -> Array` | `ALL_LEVELS` | 54 `Dictionary` segar, tipe Python, urutan kunci Python |
| `get_level_config(n) -> Variant` | `get_level_config` | `Dictionary` atau **NIL** (Python `None`) |
| `get_level_count() -> int` | `get_level_count` | `len(ALL_LEVELS)` = 54 |
| `is_level_unlocked(n, completed) -> bool` | `is_level_unlocked` | lihat §4 + §7 |
| `get_next_level(n) -> Variant` | `get_next_level` | `int` atau **NIL** |
| `build_row(i) -> Dictionary` | — (helper) | baris katalog ke-`i`; di luar jangkauan → Dictionary kosong |
| `row_index(n) -> int` | — (helper) | scan linear = paritas `for lvl in ALL_LEVELS`; `-1` kalau tak ada |
| `py_contains(haystack, needle) -> bool` | `x in list` | semantik `==` Python, **bukan** `Array.has()` |
| `catalog_signature() -> String` | — (helper) | `"54:1-54:162"` = jumlah:level pertama-terakhir:total mini boss |

`catalog_signature()` bukan hash kriptografis; gunanya membuktikan lib yang
termuat engine membawa tabel generasi yang sama dengan data repo (dicetak loader
saat mengumumkan backend, dan dibandingkan harness A/B).

## Semantik yang dikunci (Python vs Godot)

### 1. Kunci `mini_bosses`: `int` → `String`

Python: `{25: "varkul", 10: "xerathis"}`. Godot: `{"25": "varkul", "10":
"xerathis"}` — sama seperti `levels.json` (kunci objek JSON selalu string).
Ini **satu-satunya** beda yang diizinkan antara katalog Python dan kedua
backend, dan dicatat eksplisit di fixture. Semua pemakai sudah key-agnostic
(`Main._roll_mini_boss_schedule` memakai `source.values()`,
`BossData.schedule_from_levels` memakai `mb[int(wave)]`).

### 2. Urutan insert `mini_bosses` tidak selalu naik

`LEVEL_3` memang `25, 10, 17` di `level_data.py`. `Dictionary` Godot ordered
(`core/variant/dictionary.h` = vector pasangan + map indeks), jadi urutan itu
bisa — dan harus — dipertahankan: `Main._roll_mini_boss_schedule` mengacak
jadwal dari `values()`, dan urutan yang berbeda mengubah jadwal mini boss.
Dikunci dua kali: `str(Dictionary)` di A/B backend, dan `got.keys() ==
field_order` di engine test.

### 3. Semua angka JSON jadi `float`

`JSON.parse_string` Godot 4.3 tidak punya cabang bilangan bulat
(`core/io/json.cpp:341` → `_parse_number` selalu `double`). Karena itu
`LevelDB.gd` punya `FIELD_KINDS` (tipe Python tiap field, **dibaca dari
berkasnya** oleh oracle statis, bukan disalin) dan `_normalize_row()` yang
mengembalikan `int` untuk field int, `float` untuk multiplier, `null` untuk
`unlock_after_level` level 1. Jalur C++ tidak perlu normalisasi: tabelnya
memang `int64_t`/`double`.

### 4. `x in list` Python ≠ `Array.has()` Godot — **bug yang diperbaiki**

`Array.has()`/`find()` memakai `Variant::hash_compare`, yang pertama-tama
membandingkan **tipe**:

```cpp
// core/variant/variant.cpp:3309
bool Variant::hash_compare(const Variant &p_variant) const {
    if (type != p_variant.type) return false;
```

Sedangkan `in` Python memakai `==`, dan `3 == 3.0` → `True`. Save Godot dibaca
lewat `JSON.parse_string`, jadi `completed_levels` berisi **float** (`[3.0]`).
Akibatnya sebelum fase ini:

```gdscript
return completed is Array and lv in completed   # 3 in [3.0] -> FALSE
```

Gejalanya: setelah game dimuat ulang, level yang sudah tamat tampak **terkunci
lagi** (`GameManager.is_level_unlocked`), badge "MAIN LAGI" hilang
(`SaveManager.is_level_completed`), deteksi replay di
`GameManager._grant_meta_reward` salah, dan tombol NEXT di `GameOverOverlay`
salah baca progres.

Perbaikannya satu implementasi untuk kedua pemakai: `LevelDB.py_contains()`
(GDScript, meniru `==` Python: numerik lintas tipe, selain itu hanya tipe sama)
dan `MysticLevels::py_contains()` (C++, `Variant::evaluate(OP_EQUAL, …)`).
`SaveManager.is_level_completed()` dan `is_level_unlocked()` sekarang lewat itu.

**Bug kedua di fungsi yang sama, ketahuan hanya di engine.** Draf pertama
`LevelDB.py_equal()` menutup semua tipe non-primitif dengan `return false`,
jadi `None in [1, None]` menjawab `false` padahal Python `true`. Jalur C++
sudah benar sejak awal — engine mendaftarkan
`OperatorEvaluatorAlwaysTrue<OP_EQUAL, NIL, NIL>` (`variant_op.cpp:522`) dan
`OperatorEvaluatorEqual<Array/Dictionary>` (`:555-556`), jadi `Variant::evaluate`
membandingkan NIL/Array/Dictionary berdasarkan nilai, persis `==` Python.
Sekarang GDScript menyerahkan sisa tipe ke `==` Godot sesudah penjaga tipe, dan
oracle statis mengunci bentuk fungsi itu (`if ta != tb` + jatuh ke
`return bool(a == b)`) supaya tidak mundur lagi. Kasusnya tidak mungkin muncul
dari save (isinya int/float), tapi fixture oracle memang menguncinya — dan
`LevelDataParityTest` di CI yang menangkapnya: 1 kegagalan dari 2.057 cek.

### 5. Deviasi yang **disengaja**: `bool` vs `int`

Python: `1 in [True]` → `True` (karena `True == 1`). Godot: tidak ada evaluator
`OP_EQUAL` untuk pasangan `BOOL`/`INT` (`core/variant/variant_op.cpp:522-528`
hanya mendaftarkan pasangan tipe sama, `INT`↔`FLOAT`, dan keluarga string),
jadi `Variant::evaluate` memberi `valid = false` → `py_contains` menjawab
`false`. Tidak error, tidak crash — hanya berbeda.

Deviasi ini **dicatat, bukan disembunyikan**: `deviation_battery` di fixture
(2 kasus, dua arah) mengunci bahwa **kedua backend Godot sepakat** menjawab
`false`. Di produksi tidak terpicu: save Godot hanya menyimpan int/float.

### 6. Konversi argumen `float` → `int64_t`, dan kenapa loader merutekan

Signature C++-nya `get_level_config(int64_t)`. Kalau GDScript mengirim `3.5`,
Godot **memangkas** jadi `3` saat mengonversi argumen — padahal Python
`get_level_config(3.5)` menjawab `None` (tidak ada level 3.5). Karena itu
`LevelDBLoader` merutekan, bukan meneruskan buta:

| Input | `_int_key()` | Jalan | Hasil |
|---|---|---|---|
| `3` (int) | `3` | C++ | config level 3 |
| `3.0` (float bulat) | `3` | C++ | config level 3 (Python `3 == 3.0` → cocok) |
| `3.5` (float tak bulat) | `null` | `LevelDB.gd` | `null` (paritas Python) |
| `"3"`, `true`, `null` | `null` | `LevelDB.gd` | `null` |

`get_next_level` lebih ketat lagi: jalur C++ hanya untuk `typeof(x) ==
TYPE_INT`. Python mengembalikan `current_level + 1` **apa adanya**, jadi
`get_next_level(3.0)` → `4.0` (float). Signature `int64` tidak bisa
mengembalikan itu; `LevelDB.gd` bisa. Semua call site Godot mengirim int, tapi
harness mengunci perilaku float-nya juga.

### 7. Batas helper (dibaca dari `level_data.py`, bukan ditebak)

```python
def is_level_unlocked(level_number, completed_levels):
    config = get_level_config(level_number)
    if not config: return False            # level tak ada -> False (walau syaratnya tamat)
    required = config.get("unlock_after_level")
    if required is None: return True       # level 1 selalu terbuka
    return required in completed_levels    # == Python, lihat §4

def get_next_level(current_level):
    next_level = current_level + 1
    if next_level > len(ALL_LEVELS): return None
    if not get_level_config(next_level): return None
    return next_level
```

Kunci `unlock_after_level` **selalu ada** di tiap baris (NIL untuk level 1) —
bukan dihilangkan — supaya `Dictionary.keys()` Godot cocok dengan
`dict.keys()` Python.

## Nama berkas lib: `debug` ≠ `template_debug`

Bug FASE 33 yang diwarisi dan **tidak** diulang: kunci di `[libraries]`
`.gdextension` memakai nama target **Godot** (`linux.debug.x86_64`), sedangkan
nilainya harus nama berkas hasil **scons/godot-cpp**
(`libmystic_levels.linux.template_debug.x86_64.so`). Kalau tertukar, engine
tidak pernah menemukan lib dan jatuh ke GDScript **tanpa pesan**. Arch Android
juga mengikuti godot-cpp (`arm64`/`arm32`, bukan `arm64v8`/`armeabi-v7a` yang
merupakan nama `android_arch` scons). Oracle statis membandingkan nama berkas di
`.gdextension` dengan pola output `SConstruct`, dan CI memverifikasi
`entry_symbol` benar-benar diekspor (`nm -D | grep " T mystic_levels_library_init"`).

## Build

```bash
cd godot/gdext/mystic_levels
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot-cpp        # di-gitignore
scons platform=linux   target=template_debug   -j4          # dev / editor
scons platform=linux   target=template_release -j4          # export release
scons platform=android target=template_release android_arch=arm64v8 -j4
```

Atau pakai checkout godot-cpp bersama (hemat ±10 menit compile kalau ekstensi
lain sudah pernah dibuild) — inilah yang dilakukan CI:

```bash
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot/gdext/godot-cpp
ln -s ../godot-cpp godot/gdext/mystic_levels/godot-cpp
ln -s ../godot-cpp godot/gdext/mystic_skills/godot-cpp
```

Lalu nyalakan jalurnya: `mystic/levels/use_gdext_levels=true` di
`godot/project.godot`, atau `LevelDBLoader.force_backend("gdext")` dari
kode/harness. Loader mencetak satu baris saat backend berubah:

```
[LevelDBLoader] GDExtension MysticLevels aktif (godot++ C++) — katalog 54:1-54:162
```

Baris itu di-`--require` oleh CI: tanpa lib, tanpa symbol, atau dengan tabel
basi, harness gagal — bukan diam-diam fallback.

Sebaliknya, **absennya** lib harus tetap wajar: `.so` tidak ikut repo, jadi
langkah `Import project` di `godot-check.yml` selalu mencetak
`Failed loading resource: res://addons/mystic_levels/mystic_levels.gdextension`
+ `GDExtension dynamic library not found`. Karena itu
`godot/tools/godot_log_gate.py` punya allowlist untuk ekstensi opsional
(`addons/mystic_levels`, `libmystic_levels`, `Failed loading
resource.*mystic_levels`) — tanpa entri itu, gate menganggap import fatal dan
**seluruh** langkah engine di-skip. Entri levels sengaja lebih sempit daripada
`mystic_skills`/`mystic_lighting` (tidak ada pola telanjang `mystic_levels`)
supaya baris kegagalan harness — `[LevelDBLoader] GAGAL instantiate
MysticLevels`, `[LevelDataGdextParityTest] FAIL: …` — tetap terhitung fatal.
Oracle statis mengunci kedua sifat itu (allowlist ada, pola telarang tidak).

## Tiga lapis verifikasi

| # | Alat | Butuh | Mengunci | Cek |
|---|---|---|---|---|
| 1 | `tools/gen_levels_cpp.py --check` | Python saja | `.h`/`.cpp` ter-commit byte-identik hasil transpile AST | — |
| 2 | `tools/test_godot_level_data_parity.py` | Python saja (tanpa pygame, tanpa engine, tanpa compiler) | `levels.json` ↔ `ALL_LEVELS` (nilai+tipe+urutan kunci), `FIELD_KINDS` ↔ tipe Python (closed-world dua arah), literal tabel C++ ↔ katalog Python (54 baris × 19 kolom + 54 array mini boss, bit-per-bit), kesegaran fixture, wiring (loader/3 autoload/`project.godot`/`.gdextension`/`.gitignore`/kedua workflow/ harness self-test/allowlist log gate), bentuk `LevelDB.py_equal`, dan **arity** tiap pemanggilan helper di kedua scene tes | **5.162** |
| 3 | `tools/test_levels_cpp_selftest.py` | g++ saja (±2 detik) | **mengeksekusi** `levels_processor.cpp` apa adanya lewat stub `Variant`: 54 baris × 17 field (nilai+tipe+urutan kunci), `row_index`, 20 kasus `get_level_config`, `get_level_count`, 20 `is_level_unlocked`, 12 `get_next_level`, 15 `py_contains`, 2 deviasi bool/int | **253** |
| 4 | `godot/tests/LevelDataParityTest.tscn` | Godot 4.3 headless | replay fixture di engine, backend GDScript: katalog, 4 helper, `py_contains`, wiring produksi (`BossDB`/`GameManager`/`SaveManager`), snapshot+restore save | **2.057** (9 seksi) |
| 5 | `godot/tests/LevelDataGdextParityTest.tscn` | Godot + lib `.so` | memaksa backend `gdext` (gagal keras kalau `MysticLevels` tidak terdaftar), replay fixture yang sama lewat C++, **plus** A/B backend untuk seluruh permukaan API (`str(Dictionary)` ikut mengunci urutan kunci) | A/B + fixture |

Lapis 2 jalan di `godot-check.yml` (tanpa compiler); lapis 1, 3, 5 + build lib
jalan di `godot-gdext.yml`. Lapis 4–5 bukan formalitas: lapis 4 yang menangkap
bug `py_equal` di §4 (nilai `null` tidak mungkin terlihat oleh parser statis
maupun stub C++, karena yang salah justru cabang fallback GDScript-nya). Lapis 3 sengaja ditempatkan **sebelum** build
godot-cpp: regresi data/logika gagal dalam detik, bukan setelah sepuluh menit.

Kenapa lapis 3 perlu kalau sudah ada lapis 2? Lapis 2 **mem-parse** literal
`.cpp` (statis); lapis 3 **menjalankan** kodenya, jadi logika helper ikut
terkunci (scan `row_index`, `not config → False`, `required None → True`, batas
`get_next_level`, evaluator `OP_EQUAL`). Kenapa perlu kalau sudah ada lapis 5?
Lapis 5 butuh engine + lib; lapis 3 butuh compiler saja, jadi paritas logika
tetap terjaga di mesin tanpa Godot terunduh.

## Batas yang disengaja

- **`mystic/levels/use_gdext_levels` tetap `false`.** Produksi masih GDScript.
  C++ sudah paritas-teruji di CI, tapi menyalakannya untuk pemain berarti
  mewajibkan lib per platform (termasuk dua arch Android + wasm) di setiap
  rilis. Urutannya: paritas hijau → default.
- **`build-android-godot.yml` belum memanggil scons**, jadi export AAB tetap
  lewat fallback GDScript. Loader tidak error kalau lib tidak ada.
- **`BossDB.get_level()` sengaja tetap scan `levels`** (tidak delegasi ke
  `LevelDBLoader.get_level_config`): `BossDB.levels` bisa disuntik harness, dan
  pemakai yang menyimpan array itu harus melihat baris yang sama. Isinya tetap
  dari backend aktif karena `load_levels()` mengambilnya dari loader.
- **Hanya linux x86_64 yang dibuild CI** (sama seperti FASE 33). `.gdextension`
  sudah memetakan semua platform/arch, tapi lib-nya belum pernah dikompilasi di
  CI untuk windows/macos/android/web.
- **`level_data.py` tidak disentuh.** Deviasi Godot dicatat + dikunci fixture
  (§5), bukan "diperbaiki" di Python — aturan `docs/MIGRASI_1_1.md`.

## Testing

```bash
# 1. kesegaran transpile (tanpa compiler, detik)
python3 tools/gen_levels_cpp.py --check

# 2. oracle statis: data + tipe + tabel C++ + wiring (tanpa engine/pygame)
python3 tools/test_godot_level_data_parity.py
python3 tools/test_godot_level_data_parity.py --write-fixture   # hanya kalau level_data.py berubah

# 3. jalankan C++ di luar engine (butuh g++; tanpa godot-cpp)
python3 tools/test_levels_cpp_selftest.py

# 4. compile-check cepat tanpa build godot-cpp penuh (butuh gen/include)
g++ -std=c++17 -fsyntax-only -I godot/gdext/mystic_levels/godot-cpp/include \
    -I godot/gdext/mystic_levels/godot-cpp/gen/include \
    godot/gdext/mystic_levels/src/levels_processor.cpp

# 5. paritas runtime di engine (butuh lib + Godot 4.3)
cd godot/gdext/mystic_levels && scons platform=linux target=template_debug -j4
godot --headless --path godot res://tests/LevelDataParityTest.tscn      --quit-after 120
godot --headless --path godot res://tests/LevelDataGdextParityTest.tscn --quit-after 120
```

## Next step (opsional)

- Bangun lib windows/macos/android/web di CI (matriks), lalu pertimbangkan
  menyalakan `use_gdext_levels` default setelah ada bukti di HP low-end.
- Port modul data murni berikutnya dengan pola yang sama (`bosses/boss_data.py`
  sudah punya jalur fixture; kandidat lain `map_components/`).
- `_roll_mini_boss_schedule` masih mengacak di GDScript dari `values()`; kalau
  nanti dipindah ke C++, RNG-nya harus stream `ParityRng` yang sama.

## Referensi

- Sumber engine 4.3 yang dibaca untuk dokumen ini: `core/io/json.cpp`
  (`_parse_number` selalu double), `core/variant/variant.cpp` (`hash_compare`
  strict tipe), `core/variant/variant_op.cpp` (tabel evaluator `OP_EQUAL`),
  `core/variant/dictionary.h` (ordered).
- [HERO_SKILLS_GODOTPP.md](HERO_SKILLS_GODOTPP.md) — pola loader/harness/CI yang
  dipakai ulang fase ini (termasuk pelajaran nama berkas `template_debug`).
- [GODOT_PARITY.md](GODOT_PARITY.md) — status paritas menyeluruh (FASE 34).
- [MIGRASI_1_1.md](MIGRASI_1_1.md) — aturan "Python adalah oracle".
- `godot/gdext/mystic_levels/README.md` — build + struktur ekstensi.
