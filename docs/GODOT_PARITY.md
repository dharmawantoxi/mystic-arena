# Status paritas Godot ↔ Pygame

**Acuan perilaku adalah versi Pygame di repository ini. Godot belum setara
sepenuhnya.** Data catalog yang sama, sprite hasil bake, dan build Android yang
berhasil tidak membuktikan bahwa alur permainan, UI, atau efeknya sudah sama.

Dokumen ini membedakan koreksi yang diuji dari bagian port yang masih parsial.
Roadmap lama di `GODOT_MIGRATION.md` mencatat implementasi komponen, bukan
sertifikasi paritas seluruh game.

## Lapisan Android `mobile/` — jalur native C++ (godot++) — 13 September 2026 (FASE 37) — **DALAM PROSES**

`mobile/` (8 submodul: `touch`, `hud`, `perf`, `platform_utils`, `debug`,
`combat_audio`, `cloud_save`, `buildinfo`) adalah lapisan keputusan Android:
ambang gesture, geometri + visibilitas tombol HUD, preset/gubernur kualitas,
safe area + posisi panel, overlay debug, konfigurasi suara tempur, validasi
payload Cloud Save, dan label build. Fase ini membangkitkan lapisan itu
sebagai C++ (`tools/gen_mobile_cpp.py` →
`godot/gdext/mystic_mobile/src/mobile_processor.{h,cpp}`,
`MysticMobile : RefCounted`, **66 method static**) plus tabel perintah
self-test — **belum ada** saklar backend, jadi tidak ada perilaku pemain
yang berubah. Rincian teknis: [MOBILE_GODOTPP.md](MOBILE_GODOTPP.md).

| Bagian | Sesudah (FASE 37, sejauh ini) |
|---|---|
| Sumber | Satu: AST `mobile/*.py` (8 submodul). Generator MENOLAK (bukan menebak) kalau literal/ekspresi hilang atau berubah bentuk; setiap fungsi menyebut baris sumber Python-nya; `--check` byte-identik |
| Cakupan | Ambang gesture (TAP_SLOP/LONG_PRESS/DOUBLE_TAP/SCROLL_STEP/FLING — `scroll_notch` kontrak satu-langkah-loop), geometri 7 tombol HUD + hit rect semantik `pygame.Rect.inflate` ASLI + visibilitas `sync()` 7 primitif, 3 preset kualitas + properti perangkat + gubernur FX (smooth 0.40/min 0.10/exp 1.5, token 140/18/10→56/10/5) + `AdaptiveQuality` (26/52, window 90, cd 180/300), safe area + zona panel (430/120) + popup/bawah + konversi koordinat, mode overlay debug + warna FPS + baris `[PERF]`, 7 jenis suara + `_KONFIG`/`POLA` + gerbang play + `ringkas()`, konstanta cloud + urutan `parse_payload` lengkap (termasuk "bad version") + `payload_summary` try/except per slot dgn `max()` atomik, label build |
| Sengaja TIDAK diport | Semua yang menyentuh SDL/pygame/JNI: `fastblit`, `blitwatch`, `spritecache`, `_bench_core`, `bootcheck`, `diagnostics` (sidepanel sudah jalur UI), mixer + pemilihan berkas fnmatch, sha256/canonical-JSON, strftime (`exported_at` double), draw, `apply_device_profile`, `PhaseTimer`/`FrameTimer` |
| Verifikasi | (1) `gen_mobile_cpp.py --check` di **kedua** workflow; (2) `test_mobile_cpp_selftest.py` — MENG-EXECUTE `mobile_processor.cpp` apa adanya lewat stub Variant tanpa engine (g++ saja, **tanpa pygame**): oracle = `mobile/*.py` ASLI dieksekusi sebagai AST tanpa node import (stub `pygame.Rect` semantik SDL + stub modul tetangga), **1.564 cek** dengan perilaku nyata (gesture lewat `TouchManager`, preset lewat `Quality.apply`, `AdaptiveQuality` diberi makan FPS, `parse_payload`/`get_payload_summary` asli), closed-world (tabel perintah == bind == deklarasi `.h`) + audit wiring (entry symbol, `.gdextension`, allowlist log gate SEMPIT, path filter kedua workflow, `.gitignore`, `mobile/` bersih); (3) build lib ke-5 di `godot-gdext.yml`: symlink `godot-cpp` bersama, scons, `nm -D` entry `mystic_mobile_library_init`, string tahan-strip `mobile_v1:8mod:66fn:` + `MysticMobile` |
| Belum | Scene paritas engine + saklar backend (`mystic/mobile/use_gdext_mobile`) — sengaja belum, pola FASE 36; jalur produksi tetap pygame |

## Komponen UI `ui_components/` — jalur native C++ (godot++) — 12 September 2026 (FASE 36) — **DALAM PROSES**

`ui_components/_bundle.py` (11 submodul: base UI, portrait hero, popup build,
slot build, panel hero, hero shop, indikator hover, notifikasi, overlay,
popup renderer, hint toko) berisi **lapisan layout + state + label** dari UI
in-match. Fase ini membangkitkan lapisan itu sebagai C++
(`tools/gen_ui_cpp.py` → `godot/gdext/mystic_ui/src/ui_processor.{h,cpp}`,
`MysticUI : RefCounted`, **80 method static**) plus tabel perintah self-test
(`selftest/ui_dispatch.inc`) — **belum ada** saklar backend, jadi tidak ada
perilaku pemain yang berubah.

| Bagian | Sesudah (FASE 36, sejauh ini) |
|---|---|
| Sumber | Satu: AST `ui_components/_bundle.py` + `_core.py` (settings) + `ui_theme.py` (palet). Generator MENOLAK (bukan menebak) kalau literal/ekspresi hilang atau berubah bentuk; setiap fungsi menyebut baris sumber Python-nya |
| Cakupan | Geometri (popup build 400x300 + clamp 4 posisi, panel hero 280x276, kartu toko 340x120 + grid/scroll, slot build 40x38), state tombol (`shop_card_state`, `castle_shield_section`, `regen_shield_section`, `build_button_style`), label (`ITEM FORGE  (n/6)`, `M A X   L E V E L`, `Lv4: DMG 55 HP 700`, `2/5 Heroes`, `x1.5`), predikat hover, kurva slide popup unlock |
| Sengaja TIDAK diport | Piksel (`pygame.draw`, `Surface`, cache tekstur, RNG partikel) dan **metrik font** — lebar/tinggi teks dikirim sebagai parameter supaya kedua backend memakai angka identik tanpa bergantung font engine |
| Verifikasi | (1) `gen_ui_cpp.py --check` di **kedua** workflow (3 berkas byte-identik); (2) `test_ui_cpp_selftest.py` — MENG-EXECUTE `ui_processor.cpp` apa adanya lewat stub Variant tanpa engine: **213 cek** (208 tanpa checkout godot-cpp) vs fixture `ui_hud` (angka direkam dari draw pygame ASLI) + `_core.py`/`ui_theme.py` + built-in Python (`round()` half-to-even, `f"{v:,}"`), **closed-world** (tabel perintah == `bind_static_method` == deklarasi `.h`; setiap fungsi ter-bind wajib diuji), **audit wiring** (entry symbol, `.gdextension`, allowlist SEMPIT `godot_log_gate`, rujukan kedua workflow, `.gitignore`), dan **opsional cek sintaks vs header godot-cpp asli + compile/link/strip .so probe** (`GODOT_CPP_DIR`; `-fvisibility=hidden` + `-s` seperti CI) — penangkap kelas bug yang lolos dari stub: `color.r8()` vs `color.get_r8()`, `nm -D` untuk symbol kelas (padahal visibility hidden), dan cek symbol statis (padahal `.so` di-strip) — ketiganya kejadian nyata CI PR #234, kini ketahuan lokal dalam ±10 detik alih-alih menunggu siklus CI ±30 menit; (3) build scons + cek isi `.so` di `godot-gdext.yml`: `nm -D` untuk entry `mystic_ui_library_init`, lalu string khas yang TAHAN STRIP — `ui_v1:11mod:80fn:` (`api_signature()`) + `MysticUI`. Symbol table tidak bisa dipakai untuk kelas: `symbols_visibility=hidden` (kelas tak ada di `nm -D`) dan `debug_symbols=no` → `-s` (symbol statis di-strip, `nm`: "no symbols"); dua-duanya sudah bikin langkah build gagal palsu di PR #234 |
| Belum | Oracle statis spy-pygame, backend GDScript + saklar (`mystic/ui/use_gdext_ui` default **false**), scene paritas engine, `docs/UI_COMPONENTS_GODOTPP.md`. Sampai itu ada, jalur produksi **hanya** pygame |

## Peta `map_components/` — jalur native C++ (godot++) — 12 September 2026 (FASE 35)

`map_components/_bundle.py` (palet + 54 tema + `PathGenerator` +
`DecorationGenerator`) sebelumnya punya dua port GDScript yang ditulis tangan
dan tidak teruji paritasnya: `ArenaMap._curved_path` (lane) dan
`res://data/themes.json` + merge const (palet). Fase ini menambahkan
**lapisan data + generator yang dibangkitkan dari AST** — backend GDScript
(`MapDB.gd` + `data/themes_raw.json`), **lapisan C++** (`MysticMaps`,
GDExtension `mystic_maps`), saklar backend, rewrite `ArenaMap`, dan lima lapis
verifikasi — sekaligus menutup dua deviasi lane yang sudah ada di produksi.
Renderer pygame (`static/decoration/shop/dynamic_renderer`) SENGAJA tidak
dimigrasi: Fase 3 meng-cover render statik lewat bake tekstur, dan
`DynamicRenderer` non-deterministik. Rincian teknis + semantik Python↔Godot:
[MAPS_GODOTPP.md](MAPS_GODOTPP.md).

| Bagian | Sebelum (FASE 35) | Sesudah |
|---|---|---|
| Sumber tema + generator | Dua port tangan: `ArenaMap._curved_path` (waypoint + Catmull-Rom_inline) dan `themes.json` (format TURUNAN converter: hex, key diganti, fog dipecah — lossy, tidak bisa dinormalkan balik) | Tiga lapisan dari satu sumber: Python (oracle) → GDScript (`scripts/core/MapDB.gd`, 975 baris: `KEY_KINDS` 77 kunci + `_normalize_row` + `make_curved_path` + replika MT19937 `PyMt` + `generate_decorations` + `derive_palette`, data `themes_raw.json` yang SETIA 1:1) → **C++** (`gdext/mystic_maps/src/maps_processor.h` 66 baris + `.cpp` 4.197 baris, entri POD per tema + tabel waypoint + 13 method static). `ArenaMap` kini memanggil `MapDBLoader`; `themes.json` tinggal sebagai pembanding independen |
| Titik lane + smoothness | **Deviasi produksi**: `_curved_path` menyimpan float (Python `int()` trunc) dan memakai smoothness 10 untuk mid (Python: 8 → 65 titik, bukan 81) — minion berjalan di jalur yang sedikit beda | Kedua backend me-`trunc` + smoothness per lane dari AST (top 10, mid 8, bot 10, river 10); waypoint GDScript dibandingkan EKSPRESI-per-ekpresi dengan AST. Engine test mengunci titik PERSIS di 1280×720 + ganjil 1025×769 |
| RNG dekor | `ArenaMap._build_decor` scatter PCG sendiri (sistem kurasi Godot, tetap dipertahankan — lihat bawah); `DecorationGenerator.generate_all` (`random.seed(42)`) tidak ada portnya | Replika MT19937 `init_by_array` di C++ (generated) + GDScript (`PyMt`) + cermin Python — semuanya dibuktikan se-stream dengan `random.Random(42)` (draw pertama 2746317213; 500 getrandbits + 500 randint + 200 choice). Oracle menangkap bug preseden `^` vs `+` di transkripsi pertama (stream salah total) sebelum engine. Bug `_too_close_to_base` lingkaran-1 direplika verbatim + dikunci |
| `round()` bankir Python | `round()` GDScript = half-away (converter = half-even) — palet meleset 1 LSB di 3 kasus aktual | `MapDB.round_half_even` + `_round_nd` EKSAK via dekomposisi IEEE-754 (dua limb int64) — cara naif `round(x·m)/m` TERBUKTI salah untuk `royal.energy` (1.1685000000000001 → 1.169, bukan 1.168; bahkan repr terpendek `"1.1685"` ikut salah). Cermin dibuktikan == `round()` pada 32.500 nilai; engine mengunci 1.169 ujung-ke-ujung. Alpha dihitung dari `.a8` (int), bukan `.a` float32 |
| Pemilihan backend | Tidak ada | `scripts/core/MapDBLoader.gd` (311 baris): `mystic/maps/use_gdext_maps` + `ClassDB.class_exists("MysticMaps")`, instance + katalog di-cache, `force_backend()`, `theme_palette()` = `derive(get_theme())`. Tidak pernah menyebut class GDExt sebagai identifier. `derive_palette`/`theme_palette`/`reload` GDScript-only (dikunci oracle); 13 method lain mencoba C++ dulu |
| Verifikasi | Tidak ada: lane + palet tidak pernah dibandingkan dengan pygame | (1) `gen_maps_cpp.py --check` di **kedua** workflow; (2) `test_godot_map_data_parity.py` — **9.844 cek** tanpa pygame/engine/compiler (JSON setia, `KEY_KINDS`, keymap/flag, waypoint, struktur dekor dua-sisi, stream MT, bankir, derive == converter 54 tema, API tiga sisi, kesegaran `themes.json` + fixture, wiring closed-world); (3) `test_maps_cpp_selftest.py` — eksekusi `maps_processor.cpp` apa adanya (200 perintah, **19.834 cek**); (4) compile+link nyata (`nm -D` symbol); (5) `MapDataParityTest` (±10 ribu cek) + `MapDataGdextParityTest` (paksa C++ + A/B seluruh API) memutar ulang `map_data.json` (428 KB) dari `_bundle.py` ASLI: 54 tema, 5 kurva, lane/river 2 ukuran, dekor 2 varian (101 + 105 entri), derive 54 palet vs `themes.json`, wiring `ArenaMap` scene asli |
| CI GDExt | Dua lib (`mystic_skills`, `mystic_levels`) | Tiga lib: symlink + build + `nm` `mystic_maps`, langkah paritas maps (statis + self-test SEBELUM build ±10 menit), scene GDExt + regresi GDScript |

**Yang TIDAK berubah (sengaja):** `mystic/maps/use_gdext_maps` tetap `false` —
jalur produksi masih GDScript, CI hanya membuild linux x86_64,
`build-android-godot.yml` belum memanggil scons. `_build_decor` ArenaMap tetap
scatter kurasi Godot (keputusan tercatat: 14 kategori pygame tidak dipetakan
1:1 ke 6 jenis `DECOR_*`; posisi pygame tersedia via loader). Kurasi
`modulate`/`light`/`energy` 4 tema pertama dipertahankan bit-identik (dikunci
baterai 14). Python mengembalikan dict tema live; kedua backend Godot
mengembalikan Dictionary SEGAR — deviasi terdokumentasi, dikunci isolasi
mutasi. `_bundle.py` **tidak disunting** (`docs/MIGRASI_1_1.md`).

## Katalog level `levels/` — jalur native C++ (godot++) — 12 September 2026 (FASE 34)

`levels/level_data.py` (2.347 baris: 54 literal dict `LEVEL_N` + `ALL_LEVELS` +
`get_level_config` / `get_level_count` / `is_level_unlocked` / `get_next_level`)
sebelumnya hanya punya satu port: `godot/data/levels.json` yang di-parse
`BossDB.load_levels()`. Fase ini menambahkan **lapisan C++** (`MysticLevels`,
GDExtension `mystic_levels`) yang dibangkitkan dari AST Python yang sama,
saklar backend, dan tiga lapis verifikasi — sekaligus menutup bug kunci level
yang sudah ada di produksi. Rincian teknis + semantik Python↔Godot:
[LEVELS_GODOTPP.md](LEVELS_GODOTPP.md).

| Bagian | Sebelum (FASE 34) | Sesudah |
|---|---|---|
| Sumber katalog | Satu jalur: `BossDB.load_levels()` membaca `res://data/levels.json` dengan `JSON.parse_string` | Tiga lapisan dari satu sumber: Python (oracle) → GDScript (`scripts/core/LevelDB.gd`, 257 baris: `FIELD_KINDS` + `_normalize_row` + cache statis) → **C++** (`gdext/mystic_levels/src/levels_processor.h` 55 baris + `.cpp` 682 baris, tabel POD 54 baris × 19 kolom + 54 array mini boss, 9 method static). `BossDB.load_levels()` kini mengambil katalog dari `LevelDBLoader.all_levels()`; 20+ pemakai `BossDB.levels` / `get_level` tidak berubah |
| Tipe nilai field | **Semua angka float** — `JSON.parse_string` Godot 4.3 tidak punya cabang bilangan bulat (`core/io/json.cpp:341`), jadi `starting_gold = 1000.0`, `castle_start_level = 1.0`, `unlock_after_level = null` hanya di level 1 | Tipe Python dipulihkan: `FIELD_KINDS` (17 field: 11 `int`, 3 `float`, 4 `str` — dibaca dari berkas `.gd` oleh oracle statis, closed-world dua arah) menormalkan jalur GDScript; jalur C++ mengembalikan `int64`/`double` asli dari tabel. `unlock_after_level` nullable (`int?`) di kedua backend, dan kuncinya **selalu ada** (NIL untuk level 1) supaya `Dictionary.keys()` == `dict.keys()` Python |
| Kunci level & progres save | `GameManager.is_level_unlocked()` memanggil `SaveManager.is_level_completed(int(required))` yang memakai `lv in completed` → `Array.has()` → `Variant::hash_compare` **strict tipe** (`core/variant/variant.cpp:3309`), padahal save hasil `JSON.parse_string` berisi float. Akibatnya `3 in [3.0]` **false**: setelah game dimuat ulang, level yang sudah tamat tampak terkunci lagi, badge "MAIN LAGI" hilang, deteksi replay `_grant_meta_reward` salah, tombol NEXT `GameOverOverlay` salah baca progres | Satu implementasi pembanding semantik `==` Python: `LevelDB.py_contains()` (GDScript) dan `MysticLevels::py_contains()` (C++, `Variant::evaluate(OP_EQUAL)`). `SaveManager.is_level_completed()` dan `is_level_unlocked()` (20 kasus fixture, termasuk `completed_levels` berisi float dan string) lewat itu. Deviasi yang **disengaja** dicatat + dikunci: `bool` vs `int` tidak punya evaluator `OP_EQUAL` (`variant_op.cpp:522-528`), jadi `1 in [True]` false di kedua backend Godot padahal Python true — `deviation_battery` mengunci keduanya sepakat |
| Helper level | Tiga implementasi terpisah: `GameManager.next_level_number()` memakai `BossDB.get_level(nxt).is_empty()`, `level_count()` memakai `BossDB.levels.size()`, `is_level_unlocked()` menulis ulang logika `level_data.py:2318-2337` | Ketiganya delegasi ke `LevelDBLoader` (`get_next_level` / `get_level_count` / `is_level_unlocked`) yang menerjemahkan `None` Python → `null` → `0` untuk pemakai Godot lama. Batas helper dikunci fixture: `not config → False` (level 55 tetap terkunci walau 54 tamat), `required None → True`, `next > len(ALL_LEVELS) → None`, dan **tipe nilai balik** `get_next_level(3.0) → 4.0` (float, karena Python mengembalikan `current_level + 1` apa adanya) |
| Pemilihan backend | Tidak ada | `scripts/core/LevelDBLoader.gd` (266 baris): `mystic/levels/use_gdext_levels` + `ClassDB.class_exists("MysticLevels")`, instance + katalog **di-cache** per backend, `force_backend()` untuk harness, `backend_name()`/`catalog_signature()` untuk debug, `_announce()` sekali per perubahan backend. **Tidak pernah** menyebut class GDExt sebagai identifier (di CI headless lib tidak ikut repo → Parse Error mematikan seluruh project). Perutean tipe: `_int_key()` mengembalikan `null` untuk float tak bulat / non-angka → turun ke `LevelDB.gd`, karena argumen C++ `int64_t` memangkas `3.5` jadi `3` padahal Python menjawab `None` |
| Verifikasi C++ | Tidak ada: katalog hanya diperiksa `BossDataParityTest` dari sisi data boss | (1) `tools/gen_levels_cpp.py --check` di **kedua** workflow (`.h`/`.cpp` ter-commit harus byte-identik hasil transpile AST); (2) `tools/test_godot_level_data_parity.py` — **5.162 cek** tanpa pygame/engine/compiler: `levels.json` ↔ `ALL_LEVELS` (nilai+tipe+urutan kunci), `FIELD_KINDS` ↔ tipe Python, literal tabel C++ ↔ katalog Python bit-per-bit, kesegaran fixture, wiring closed-world (loader/3 autoload/`project.godot`/`.gdextension`/`.gitignore`/kedua workflow/harness self-test/allowlist log gate), dan arity helper kedua scene tes — GDScript memeriksa arity lintas berkas saat scene dimuat sedangkan gdparse tidak, jadi `_fail("a", "b")` baru ketahuan sebagai Parse Error di engine; (3) `tools/test_levels_cpp_selftest.py` — **mengeksekusi** `levels_processor.cpp` apa adanya lewat stub `Variant` (`gdext/mystic_levels/selftest/`, bukan bagian lib), 253 cek dalam ±2 detik dengan g++ saja, ditempatkan SEBELUM build godot-cpp yang ±10 menit; (4) compile+link nyata (`scons` + godot-cpp 4.3, symbol `mystic_levels_library_init` diverifikasi `nm -D`); (5) `LevelDataParityTest` (backend GDScript, **2.057 cek**) + `LevelDataGdextParityTest` (backend DIPAKSA C++, gagal keras kalau `MysticLevels` tidak terdaftar, plus A/B `str(Dictionary)` seluruh permukaan API — ikut mengunci urutan kunci) memutar ulang `godot/tests/fixtures/level_data.json` (117 KB) yang direkam `level_data.py` ASLI: 54 baris, 22 kasus `get_level_config`, 20 `is_level_unlocked`, 15 `py_contains`, 17 `get_next_level`, 2 deviasi. Lapis engine ini yang menangkap bug `LevelDB.py_equal` draf pertama: cabang terakhir `return false` membuat `None in [1, None]` false padahal Python true (jalur C++ sudah benar — `OP_EQUAL(NIL, NIL)` = `OperatorEvaluatorAlwaysTrue`, `variant_op.cpp:522`); sekarang sisa tipe diserahkan ke `==` Godot dan bentuk fungsinya dikunci oracle statis. `godot_log_gate.py` ikut diberi allowlist `addons/mystic_levels` (lib tidak ikut repo → "Failed loading resource" itu wajar), sengaja lebih sempit dari entri `mystic_skills` supaya baris FAIL harness tetap fatal |
| CI GDExt | Satu lib (`mystic_skills`), satu cache godot-cpp di `gdext/mystic_skills/godot-cpp` | Dua lib: `godot-cpp` di-clone SEKALI ke `godot/gdext/godot-cpp` lalu di-symlink ke tiap ekstensi (objek compile ±950 berkas dipakai bersama → satu compile godot-cpp untuk dua lib), cache key `-shared-v1`, langkah build + `nm` sendiri untuk `mystic_levels`, dan regresi "lib terpasang tapi flag false → tetap GDScript" |

**Yang TIDAK berubah (sengaja):** `mystic/levels/use_gdext_levels` tetap
`false` — jalur produksi masih GDScript (`LevelDB.gd` + `levels.json`), sama
seperti FASE 33 untuk skill: C++ paritas-teruji di CI, tapi menyalakannya untuk
pemain berarti mewajibkan lib per platform (dua arch Android + wasm) di setiap
rilis. `build-android-godot.yml` belum memanggil scons. CI hanya membuild linux
x86_64. `BossDB.get_level()` sengaja tetap scan `BossDB.levels` (bukan delegasi
ke loader) supaya katalog yang dipegang `BossDB` konsisten untuk 20+
pemakainya, termasuk harness yang menyuntik backend berbeda.
`levels/level_data.py` **tidak disunting** — deviasi Godot dicatat dan dikunci
fixture, bukan "diperbaiki" di sumber (`docs/MIGRASI_1_1.md`). Tidak ada RNG di
`levels/`, jadi paritasnya deterministik penuh.

## Skill hero `hero_skills/` — jalur native C++ (godot++) — 12 September 2026 (FASE 33)

`hero_skills/_bundle.py` (5.221 baris: `BaseSkill` 28 method, 6 kelas starter,
`BossHeroSkills` 273 method / 270 `_cast_*`, `_SKILL_REGISTRY` 66 boss-hero)
sudah punya port GDScript yang paritas-terkunci (`HeroSkillKit.gd`, dijaga
`HeroSkillParityTest`). Fase ini menambahkan **lapisan ketiga**: GDExtension C++
(`MysticHeroSkills`) yang dibangkitkan dari AST Python yang sama, plus saklar
backend, build yang benar-benar berjalan, dan harness yang memaksa oracle
Pygame dilewatkan ke C++. Rincian teknis + daftar bug yang diperbaiki:
[HERO_SKILLS_GODOTPP.md](HERO_SKILLS_GODOTPP.md).

| Bagian | Sebelum (FASE 33) | Sesudah |
|---|---|---|
| Implementasi skill | Satu jalur: `HeroSkillKit.gd` (5.807 baris GDScript hasil transpile) | Tiga lapisan dari satu sumber: Python (oracle) → GDScript → **C++** (`hero_skills_processor.h` 459 baris + `.cpp` 6.802 baris, 432 definisi: helper `BaseSkill`, 6 starter, 66 resep boss, `boss_generic` + `fallback_cast`) |
| Pemilihan backend | Tidak ada — `Hero.gd` preload `HeroSkillKit.gd` | `HeroSkillKitLoader.gd`: `mystic/skills/use_gdext_skills` + `ClassDB.class_exists("MysticHeroSkills")`, instance GDExt **di-cache** (sebelumnya `ClassDB.instantiate()` tiap panggilan, termasuk tiap pembanding `sort_custom`), `force_backend()` untuk harness, `backend_name()` untuk debug |
| Lib GDExt termuat engine | **Tidak pernah**: `mystic_skills.gdextension` menunjuk `libmystic_skills.linux.debug.x86_64.so`, sedangkan scons menghasilkan `...linux.template_debug.x86_64.so` (kunci target Godot ≠ nama berkas godot-cpp); arch Android juga salah (`arm64v8`/`armeabi-v7a` bukan `arm64`/`arm32`) | Nama `[libraries]` diperbaiki (linux/windows/macos/android/web, kunci `debug`/`release` → berkas `template_debug`/`template_release`), `compatibility_minimum = "4.3"`. Bug identik di `mystic_lighting.gdextension` ikut dikoreksi |
| Verifikasi C++ | Tidak ada: `.cpp` 6.758 baris belum pernah dikompilasi, belum pernah dijalankan, tidak ada CI yang menyentuhnya | (1) compile+link nyata (`scons` + godot-cpp 4.3, symbol `mystic_skills_library_init` diverifikasi `nm`); (2) `tools/gen_hero_skills_cpp.py --check` di **kedua** workflow (berkas ter-commit harus byte-identik hasil transpile); (3) `HeroSkillGdextParityTest` memaksa backend `gdext` lalu memutar ulang fixture oracle `match_parity.json["hero_skills"]` (222 hero × 4 skenario, jejak event per frame + state final) **plus** A/B C++ vs GDScript untuk `hero_kind()`/`visual_duration()` seluruh `hero_type` katalog dan tie-break `__by_pair0`; (4) workflow baru `.github/workflows/godot-gdext.yml` (cache godot-cpp per commit SHA + cache binary Godot) |
| Bug paritas C++ yang ditemukan audit | `by_pair0` tanpa tie-break indeks; `boss_generic` mengurutkan musuh dengan bubble-sort **tidak stabil**; `fallback_cast` mengirim `src = nil` ke `kit_hit` (atribusi damage/reflect kehilangan sumber); `trigger_q/w/e/r` membuang `kind` sehingga durasi visual dihitung dari `hero_type` (tabel boss & starter tercampur) dan tabelnya **hardcode**; `has_target` di-bind tanpa `DEFVAL`; `get_attack_cooldown_frames` tidak membulatkan (GDScript `int(roundf(ac * 60))`) sehingga `_original_attack_cd` menyimpan 49.99998; assign langsung `X.attack_timer = 30` (Sylara shackle) dipetakan ke `kit_lock` yang memakai `maxf`; index berantai `kit_catalog_all(h)[type]["damage"]` memakai `Dictionary::operator[]` non-const di atas temporary (buff damage 7 boss jadi `int(100 × mult)`, 33 kegagalan CI); `(double)(Variant)` atas NIL menghasilkan garbage stack; loader fallback `visual_duration` mengembalikan 40 hardcoded | Semuanya diperbaiki **di generator** (`tools/gen_hero_skills_cpp.py`) lalu dibangkitkan ulang, jadi tidak ada patch tangan di `.cpp`: pembanding (dist, idx), insertion sort kunci (dist, idx), `src = h`, `visual_duration_kind(kind, hero_type, key)` + `set_active_skill(h, kind, key, duration)` dengan tabel **dibangkitkan dari data Python**, `DEFVAL(Variant())`, pembulatan frame di `get_attack_cooldown_frames`, helper baru `set_atk_timer_frames` (tulis detik apa adanya, `kit_lock` tetap untuk 74 situs `max(...)`), `dict_at()` untuk baca Dictionary const-safe, `var_num()`/`var_int()` untuk konversi numerik deterministik (NIL → 0, sama dengan GDScript), fallback loader membaca konstanta `HeroSkillKit.gd`. Audit tambahan: literal numerik/string **312 fungsi** GDScript vs C++ dibandingkan statis → 0 selisih semantik |

**Yang TIDAK berubah (sengaja):** `mystic/skills/use_gdext_skills` tetap
`false` — jalur produksi masih GDScript. C++ sudah paritas-teruji di CI, tapi
menyalakannya untuk pemain berarti mewajibkan lib per platform (termasuk dua
arch Android) di setiap rilis; urutannya paritas hijau → benchmark HP low-end →
default. `build-android-godot.yml` belum memanggil scons, jadi export AAB tetap
memakai fallback GDScript (loader tidak error kalau lib tidak ada). Tidak ada
RNG di `hero_skills` (`grep random` kosong), jadi paritasnya deterministik penuh.

## Paket `bosses/` — lapisan overlay `Boss.draw()` + pipeline data `boss_data.py` — 12 September 2026 (FASE 32)

Dua bagian `bosses/` yang realistis diport diport penuh: **(A)** seluruh lapisan
overlay `Boss.draw()` (`base_boss.py:6124-6430` — entrance, aura
ability/enrage/true boss, bayangan, indikator debuff menara, badan generik, HP
bar, papan nama) → `scripts/render/BossOverlay.gd` + `scenes/boss/BossPlate.gd`,
dan **(B)** pipeline data saat-import `boss_data.py` (lima fungsi yang menimpa
tabelnya sendiri) → `scripts/core/BossData.gd` + `BossDB.rebuild_from_pristine()`.
Rincian, kosakata op kanonik, dan daftar deviasi:
[BOSS_OVERLAY_GODOTPP.md](BOSS_OVERLAY_GODOTPP.md).

**Tetap di luar cakupan (keputusan Fase 2b→5, bukan gap baru):** 54 renderer
prosedural per boss (`bosses/level1.py`…`level54.py`, ±350 ribu baris). Badan
boss tampil lewat **strip bake** yang di-render dari renderer pygame ASLI
(`assets/units/`, 445 PNG ter-commit); yang diambil dari berkas-berkas itu hanya
pemetaan dispatch-nya (`has_renderer`), yang menentukan apakah overlay menggambar
badan generik fallback.

| Bagian pygame | Sebelum (Godot) | Sesudah (FASE 32) |
|---|---|---|
| Entrance `_draw_entrance` (`:6376-6430`) | Tidak ada: selama `entrance_timer` boss hanya diam (freeze perilaku sudah ada), layar tidak menampilkan cincin ekspansi + teks entrance berdenyut | `entrance_ops()` **eksklusif** (kalau `entrance_timer > 0`, hanya ini yang digambar — paritas `return` dini pygame): cakram alpha 200, cincin ekspansi, teks `entrance_text` dari `boss_data` (font 28 true / 24 mini, baris 34 px, `start_y = 84 − (n−1)·18`, `cx = SCREEN_W//2`) + bayangan +2/+2 alpha 200; clamp lebar 1000 px |
| Aura true boss `_draw_true_boss_aura` (`:6351-6375`) | Ada, tetapi ditulis inline di `Boss._draw()` dengan resep pita yang hanya dikunci satu tes alpha | `true_aura_ops()` di BossOverlay (8 pita `range(aura_r, aura_r−15, −2)`, alpha `(aura_r − r_off)·5·pulse`, `pulse = sin(pulse)·0,3 + 0,7`); `Boss.gd` tidak lagi punya `draw_arc`/`draw_circle` — seluruh geometri lewat op kanonik yang dibandingkan fixture |
| Aura ability (`:6139-6159`) + enrage `_draw_enrage_aura` (`:6277-6300`) | Aura ability **tidak diport**; enrage digambar dua `draw_arc` 2 px dengan warna hardcode dan catatan "profil alpha/pixel belum diverifikasi" | `ability_aura_ops()` (3 cakram alpha 26/40/60 radius `ability_range`) + `enrage_aura_ops()` (dua cincin stroke 2 px radius `radius + 14·pulse`, `(255,50,40)` true / `(255,142,30)` mini) — keduanya bagian dari 647 op fixture |
| Bayangan (`:6166`) | `Polygon2D` "Shadow" di `Boss.tscn` — **dimatikan** di `_ready`, jadi boss tidak punya bayangan sama sekali | `shadow_ops()`: ellipse hitam `(0,0,0,120)` rect `(x − rx, y + ry·0,35, 2rx, ry·0,7)` (+10 px untuk true), digambar di node Boss supaya tetap di bawah badan |
| Indikator debuff menara (`_core.py:1037-1085`) | Tidak ada: SLOW/ATK SLOW/SKILL DOWN/ANTI HEAL/BURN dari menara tidak terlihat pada boss | `debuff_ops()` dari `StatusEffects` timer > 0: cincin slow `(150,220,255)`, burn dua lapis `(255,140,40)`/`(255,220,90)`, pip 4 px urutan `DEBUFF_PIP_ORDER` di `y − radius − 12` |
| Badan generik `_draw_generic_body` (`:6301-6350`) | Tanpa strip bake, Godot memasang **siluet** `UnitSilhouette` (bentuk yang tidak pernah digambar pygame untuk boss) | `generic_body_ops()` (bulatan `color`/`color_dark` + mahkota + mata) hanya bila `has_renderer` false; `setup_visual()` tidak lagi membuat siluet — `color_dark` kini dibaca dari data (`bosses.json`, field baru hasil converter), bukan `darkened(0,4)` |
| HP bar + papan nama (`:6225-6276`) | Node statis `UI` (`CanvasGroup` + `ProgressBar` + `Label`): tinggi/lebar bar tetap, tanpa warna border enrage, tanpa prefix `TRUE BOSS:`, teks `nama [ENRAGED] 1234/5678`, tidak di-clamp ke tepi layar | `BossPlate.gd` (anak **sesudah** `Visual`, jadi di atas badan) meraster `hp_bar_ops()` + `name_plate_ops()`: geometri persis pygame (`bar_w` 70/60, `bar_h` 10/8, jangkar `y − head_top − 6 − bar_h` dengan `head_top` dari `BOSS_LABEL_TOP`/radius, tiga warna isi per rasio HP, border enrage/kelas, kotak bg `inflate(8,4)` radius 3, clamp margin 2 px ke `SCREEN_W`); `update_ui()` tinggal memicu gambar ulang |
| Urutan lapisan | `queue_redraw()` dipanggil hanya untuk true boss + enrage, jadi aura ability/entrance/debuff bisa tertinggal satu frame | `_queue_overlay()` (node + `Plate`) tiap frame di `_physics_process`; `underlay_ops()` (langkah 1-7) digambar node Boss, `over_ops()` (langkah 8-9) oleh `Plate` — urutan pygame aura → bayangan → debuff → badan → bar → nama dijaga struktur node, bukan `z_index` |
| Pipeline data `boss_data.py` (`:11452-11841`) | Tidak ada: Godot hanya membaca **hasil** bake. Fallback `BossDB` bila `bosses.json` hilang = 3 baris hardcode dengan angka **pre-pipeline** (salah) | `BossData.gd` mem-port kelima langkah (rebalance piecewise → smoothing monoton per slot wave/level → curve override → normalisasi stat hero_unlock least-squares + clamp + running-max 15% → normalisasi range melee/ranged) atas `data/boss_pristine.json` (tabel mentah hasil ekstraksi **AST** converter); `BossDB.rebuild_from_pristine()` memulihkan 216 baris, `load_levels()` kini jalan lebih dulu karena smoothing butuh jadwal |
| Verifikasi | `test_boss_true_aura_parity.py` (46 cek, hanya aura true boss, tanpa fixture engine) | 4 oracle + 2 scene replay: `test_boss_draw_parity.py` **menjalankan `Boss.draw` pygame ASLI** untuk 50 skenario, merekam primitif → op kanonik, lalu memverifikasi konversinya dengan piksel (byte-per-byte) + profil alpha terukur (245 cek, fixture 185 KB/647 op wajib segar); `test_boss_overlay_model_parity.py` = kembaran Python `BossOverlay.gd` (104 cek, konstanta dibaca dari `.gd`); `test_boss_true_aura_parity.py` ditulis ulang (53 cek, pendekatan naif 8×`draw_circle` **wajib gagal**); `test_boss_data_parity.py` (2515 cek: model vs modul asli 3024 field, vs baker 3024 field, invariant, probe fit nyata). Replay engine: `BossDrawParityTest` (op + semantik lapisan + plumbing `overlay_state()` node asli + raster `exec()`) dan `BossDataParityTest` (216 boss field demi field + purity + katalog + jalur pemulihan) — CI `godot-check` langkah **4z** dan **4z2** |

**Yang belum (jujur):** raster overlay belum diaudit **piksel-per-piksel**
terhadap screenshot pygame — fixture mengunci geometri/warna/urutan op dan
oracle mengunci semantik alpha pita, tetapi bentuk glif teks mengikuti font
engine (metrik `wh`/`asc` yang direkam oracle hanya menjamin **posisi blit**
identik). Bayangan ellipse digambar poligon 32 titik (Godot tidak punya
`draw_ellipse`) sehingga tepinya beda sub-piksel. Visual skill smart-AI per boss
(`heroes/<boss>_fx`) tetap aproksimasi `KitShockRing.gd` seperti sebelum fase
ini — itu ranah `_entity.py`/`heroes/`, bukan `bosses/`.

## Design system UI `ui_theme.py` (palet, teks, ikon, komponen menu) — 11 September 2026 (FASE 31)

`ui_theme.py` (1011 baris, **31 def**) adalah satu sumber kebenaran tampilan
menu pygame: 32 warna palet, 4 cache permukaan (`_GRAD_CACHE`, `_SHADOW_CACHE`,
`_GLOW_CACHE`, `_GRAD_TEXT_CACHE`), primitif gradasi/glow/bayangan, teks
(letter-spacing, elipsis, gradasi glif, outline 8 arah), 29 ikon vektor, dan 13
komponen siap pakai yang mengisi `btns` (dict id → Rect) supaya hit-test
`Menu.handle_click` satu jalur. Port-nya tiga lapis — fungsi murni →
`draw_*`( immediate-mode, `btns: Dictionary`) → widget Control — sehingga angka
geometri/warna hanya punya satu sumber. Rincian + daftar deviasi:
[UI_THEME_GODOTPP.md](UI_THEME_GODOTPP.md).

| Bagian pygame | Sebelum (Godot) | Sesudah (FASE 31) |
|---|---|---|
| Primitif cache `_vgrad`/`_shadow`/`_radial` (`:96-158`) | `draw_vgrad` memakai `top.lerp(bottom, t)` (float, tanpa kuantisasi 8-bit pygame); `draw_glow` = **pendekatan** 14 lingkaran konsentris (poligon 28 titik, alpha `(1-f)²`); `draw_shadow` = `StyleBoxFlat` (`shadow_size = spread*3`, offset (2,3)) | `vgrad_row_color()` port persis loop `int(top + (bottom-top)·y/(h-1))`; `radial_texture()` mereproduksi `_radial` **langkah 2px** + `int(a·(1-d)²)` + kunci alpha `max(4,min(120,a//8*8))`, di-cache seperti `_GLOW_CACHE`; `shadow_texture()` = sel `max(4, w//8)` → `resize` Lanczos (padanan `smoothscale`) + `shadow_surface_size`/`shadow_small_size`; `draw_shadow(offset)` membedakan blit `panel()` (-4,-4) dan `button()` (-2,-2) |
| `cheap_alpha()` + `clear_caches()` (`:72-95`) | Tidak ada padanan: semua efek selalu digambar "penuh", cabang hemat pygame tidak terport dan tidak bisa diuji | `cheap_alpha()` (auto = true, karena komposisi alpha Godot di GPU) + `static var cheap_alpha_override` (-1/0/1) + `clear_caches()`. **Kedua cabang** tiap komponen diport 1:1 dan dijalankan tes (probe menggambar semua komponen dua kali) |
| Teks `letter`/`fit_ellipsis`/`_has_glyph`/`draw_text`/`gradient_text`/`outline_text` (`:171-267`) | `letter()` ada; `fit_ellipsis` **selalu** memakai `…` (font tanpa glif U+2026 menggambar kotak); tidak ada padanan `gradient_text` — judul layar digambar satu warna solid | `has_glyph()` + fallback `"..."` persis pygame; `draw_text`/`draw_text_centered` (bayangan (5,6,12) offset (2,2)); `gradient_bands()` + widget **GradientText** (N pita `clip_contents`); `draw_outline_text` outline 8 arah (4 arah di mode hemat) + isi gradasi `GOLD_BRIGHT → (196,138,40)`; literal pygame `(8,9,18)` diberi nama `OUTLINE_DARK` (dan `(5,6,12)` = `TEXT_SHADOW`) supaya `GradientText`/`ScreenTitle` tidak menulis ulang hex yang sama — `visual_parity_audit.py --section hardcode` turun 3 → 1 (sisanya `TopupDialog.gd`, sudah ada sebelum fase ini) |
| Ikon `draw_icon` (`:269-508`) | 29 lengan sudah ada (+ `VectorIcon.gd`), tetapi **daftar namanya tidak dikunci** — ikon baru di pygame bisa lolos tanpa port | `const ICON_NAMES` + `icon_names()` + `has_icon()`; oracle memparse nama dari `draw_icon` pygame, membandingkan dua arah, dan memverifikasi setiap nama punya lengan `match` di Godot |
| `corner_ticks`/`panel`/`panel_solid` (`:509-552`) | Hanya `PygamePanel` (StyleBox) + `panel_style()`; tidak ada jalur immediate-mode | `draw_panel`/`draw_panel_solid`/`draw_corner_ticks` port 1:1: bayangan → gradasi r12 → border → ticks emas, cabang hemat `PANEL_FILL` / bayangan solid `(6,7,14)` di `r.move(3,4)` |
| `button` (`:553-646`) | `PygameButton` Mode.MENU menulis ±155 baris sendiri: tanpa clamp label 3 langkah, tanpa glow eksak, strip aksen memakai **alpha 70/255** | `button_hit_rect` (`inflate(18,8)` saat hover), `menu_button_colors`, `button_label_cx` (clamp **3 langkah**: dorong kanan → jepit kanan → pusatkan), `draw_button_visual`/`draw_button` (glow `_radial(w+44,h+36,accent,74)` di (-22,-18), badge `r=17` di `x+34`, sorot tepi atas, ticks). **Koreksi deviasi:** pygame menulis `(*accent,70)` ke permukaan display tanpa SRCALPHA → alpha diabaikan → strip aksen **opaque**, bukan 70/255. Factory `PygameButton.menu_button()`/`pill_button()`/`tab_button()`/`back_button()` menyalakan letter-spacing sesuai default pygame (`letter_gap=True`, dan `tab()` selalu `letter()`) |
| `pill` + `back_button` (`:647-692`, `:950-961`) | `pill_colors()` + Mode.PILL; hover/glow/`enabled` tidak terport | `draw_pill_visual`/`draw_pill`: hover `top+18`/`bottom+14`, glow `_radial(w+30,h+24,edge,66)`, ikon `s=0.8` di `x+22` + `cx = x+22+(w-22)//2`, border 2px/1px, dan **`enabled=false` tidak mendaftar `btns`** (rect inputnya tetap dikembalikan); warna teks kind `owned` `(190,250,200)` ikut dikunci statik sebagai `LITERAL_PENTING` setelah run engine menemukan hex yang salah (`#befaca`); `back_button_rect` + `draw_back_button` + `PygameButton.back_button()` (200×42, netral, ikon `back`) |
| `chip`/`section_header`/`_dim` (`:693-753`) | `MainMenu._shop_chip`/`_mini_chip`/`_settings_header` merakit sendiri (angka kedua yang bisa menyimpang) | `chip_rect`/`chip_size`/`chip_colors`/`draw_chip` (lebar `26 + 22·ikon + teks + 10 + nilai`, tinggi 30, `align="right"` = pos sudut kanan) + `section_header_geom`/`_size`/`draw_section_header` (`tw = lebar judul TANPA letter-spacing + 28`, blok 34px) + `dim()` + widget **PygameChip**/**SectionHeader** |
| `toggle` (`:754-792`) | `PygameToggle._draw()` menduplikasi warna/knob/label dengan pendekatan (`Color(0.05,0.06,0.09)`, `Color(0.96,0.97,1.0)`, `Color(0.82,1.0,0.86)`, `size*0.5` bukan floor) | `toggle_colors`/`toggle_knob_size`/`draw_toggle_visual`/`draw_toggle` (knob 18px: pusat `right-24` ON / `x+6` OFF, bayangan (12,14,24) di +1,+2, muka (245,248,255), cincin edge; label ON/OFF (210,255,220)/`TEXT_BODY` di sisi berlawanan); widget sekarang **mendelegasikan** |
| `slider` (`:793-820`) | `style_volume_slider()` (HSlider native + StyleBox) — visualnya bukan visual pygame | `slider_geom` + `draw_slider`: track (34,38,58) r4, isi hanya bila `fill_w > 4`, border (120,110,86), **knob di `x + int(w·value)`** (tanpa kompensasi lebar knob), glow 36×36 alpha 80, lingkaran 11/8 + cincin emas 2px; widget **PygameSlider** mengosongkan visual native lalu mendelegasikan |
| `option_cycler` (`:821-867`) | `MainMenu` merakit cycler bahasa/kecepatan sendiri | `cycler_geom` (kotak `max(110, nilai+26)` **dibatasi `width-66`**, chevron 24px jarak 6px, `next_y = y+37`) + `draw_option_cycler` (label di `y+10`, hover `id_base+"_prev"/"_next"` → border kotak `EDGE_GOLD` + chevron (64,74,110), ikon `s=0.6` (200,210,240)) + widget **OptionCycler** (`value_changed`, `hit_rects`, `press`) |
| `tab_width`/`tab` (`:868-906`) | Mode.TAB menulis sendiri | `tab_colors`/`tab_width_for`/`tab_width`/`draw_tab_visual`/`draw_tab`: aktif = border accent 2px + underline `(x+8, bottom-4, w-16, 3)` r1 + teks accent; non-aktif = border 1px (72,80,106)/(120,130,160) + teks `TEXT_DIM`/`TEXT_BODY`; label letter-spaced |
| `screen_title` (`:907-949`) | `ScreenTitle` menggambar judul solid; ornamen ditangani `Flourish` terpisah | `screen_title_geom` (glow 620×150 di `(cx-310, y-62)`, ornamen `y+52`: garis ±220/±18, wajik ±8/±7, dot ±230, plate `cx - (lebar+56)//2` **pembagian bulat** tinggi 44) + `draw_screen_title`/`draw_title_ornament`/`draw_title_sub` (ticks `length=8,width=1,inset=3`); `ScreenTitle` kini berbadan gradasi lewat GradientText |
| `scroll_indicator` (`:962-981`) | Tidak ada padanan (memakai scrollbar native) | `scroll_thumb_rect` (`ratio = h/(h+max)`, `thumb_h = max(18, int(h·ratio))`, `thumb_y = y + int((h-thumb_h)·pos/max)`) + `draw_scroll_indicator` + widget **ScrollIndicator** (`follow(ScrollContainer)`, `set_scroll`) |
| `hp_bar`/`progress_bar` (`:982-1011`) | Ada, tetapi `light = minf(1.0, c + n/255)` (float) dan radius `h*0.5` | `add_rgb()` (ruang 8-bit `min(255, c+50)` / `+40`) + `bar_fill_w()` + `pyrect()` + radius `floor(h/2)` + gerbang `fw > 3` — koreksi exactness terhadap fixture |
| Verifikasi | Hanya bagian **PALET** di `tools/visual_parity_audit.py` (konstanta warna) | `tools/test_godot_ui_theme_parity.py`: 4 cek statik (PALET 32/32 dua arah, COVERAGE 31 def → 618 simbol closed-world, IKON 29 + lengan `match`, LITERAL 30 warna, WIRING 17 seksi) **plus** menjalankan `ui_theme.py` ASLI (SDL dummy + font palsu 7px/karakter) untuk merekam fixture 18 seksi/67 KB; `godot/tests/UiThemeParityTest.tscn` memutar ulangnya di engine; CI `godot-check` langkah **4y** + `ui_theme.py` masuk filter `paths`. **Run engine pertama (CI) = 1463 cek hijau**; run itu menemukan 3 bug port yang lolos cek statik (hex `owned`, letter-spacing factory, setter `PygameChip`) + 1 bug oracle (`center` label tombol dihitung dari blok piksel yang terpotong permukaan 700px → kini menyadap argumen `center=` `draw_text` + flag `clipped`) |

**Yang belum (jujur):** 6 widget baru (`PygameChip`, `SectionHeader`,
`PygameSlider`, `OptionCycler`, `ScrollIndicator`, dan `GradientText` di luar
`ScreenTitle`) **belum punya pemakai** — `MainMenu.gd` masih merakit
`_shop_chip`/`_mini_chip`/`_settings_header`/`_volume_slider`/`_screen_header`
sendiri. Rewiring sengaja tidak dilakukan di fase ini karena
`MetaShopTxnParityTest` mengiterasi `PanelContainer` (filter meta `hero_type`)
dan `LocalizationParityTest` mengumpulkan semua `Label` di layar SETTINGS, jadi
mengganti rakitan itu mengubah struktur node yang dikunci kedua tes. Widget-nya
sendiri dikunci `UiThemeParityTest` terhadap angka oracle.

## Lokalisasi UI `localization.py` (teks id/en + pilihan bahasa) — 11 September 2026 (FASE 30)

`localization.py` (100 baris) adalah satu-satunya kamus teks UI dwibahasa
pygame: **24 kunci × 2 bahasa**, bahasa aktif `_LANGUAGE`, dan
`tr(key, **values)` dengan fallback berlapis (bahasa aktif → tabel `id` →
kunci mentah; nilai placeholder hilang → **template mentah**, bukan crash dan
bukan string kosong). Bahasa aktif disinkronkan `GameSettings` dan disimpan di
`settings.json` GLOBAL. Rincian migrasi + peta pemanggil pygame:
[LOCALIZATION_GODOTPP.md](LOCALIZATION_GODOTPP.md).

| Bagian pygame | Sebelum (Godot) | Sesudah (FASE 30) |
|---|---|---|
| Modul `localization.py`: `_TEXT`, `LANGUAGES`, `LANGUAGE_LABELS`, `set_language`/`get_language`/`get_language_label`/`tr` (`:7-100`) | Tidak ada padanan sama sekali — setiap Control menulis teks Indonesia-nya sendiri, dan dokumen ini mencatat "UI Godot memang Indonesia" sebagai deviasi yang diterima | `scripts/utils/Localization.gd` (`class_name MysticLocalization`, semua `static`, `static var _language`): tabel 24 kunci × 2 bahasa disalin **persis** (tanda baca, spasi ganda, `—`, `•`), fallback identik, plus `_py_format`/`_py_str` yang menjaga semantik `str.format` + `str()` Python (float bulat `3.0` → `"3.0"`, `0.0` → `"0.0"`, `True`/`False`, `None`) — selisih `str()` Godot yang sama sudah ditangani `HeroItems._py_str` |
| `tr(key, **values)` (`:92-100`) | — | `MysticLocalization.tr_text(key, values: Dictionary)`. **Deviasi nama yang dikunci oracle:** `Object.tr()` adalah method NATIVE engine (pintu masuk `TranslationServer`), jadi nama `tr` dihindari — oracle GAGAL kalau `static func tr(` muncul di port. `**values` Python menjadi Dictionary karena GDScript tidak punya keyword args |
| Baris "Interface language" di PENGATURAN (`_core.py:6321-6329`) + tombol `language_prev`/`language_next` (`:7295-7303`) | Tidak ada; baris FASE 22 di bawah malah mencatat language sebagai "opsi pygame tanpa padanan kerja yang sengaja tidak dipalsukan" | `MainMenu._language_row()` + `_cycle_language()` — label barisnya SENDIRI terlokalisasi (`tr("language")` = "Bahasa"/"Language"), nilainya `get_language_label` ("Bahasa Indonesia"/"English"), posisi persis pygame (setelah Game Speed, sebelum seksi GRAPHICS), cycler membungkus ke dua arah seperti `(idx + delta) % len(languages)` Python, dan layar dibangun ulang setelah berubah (pygame menggambar ulang tiap frame) |
| Sinkron bahasa aktif saat boot/load (`GameSettings.__new__` `:9116`, `_load` `:9170`) | Tidak ada — tidak ada yang membaca setelan bahasa | `AppShell._apply_interface_language()` di `_ready` autoload PALING AKHIR (jadi `SaveManager.load_save()` sudah selesai; `GameManager._ready` jalan lebih awal dan hanya melihat default), `GameManager.apply_language()` + sinkron ulang di `_load_gameplay_settings()` (boot + tiap `start_level`), kolom `bahasa` di banner boot, dan `lang=` di baris `SESSION START` `crash_log.txt` (bug laporan pemain bisa direproduksi bahasanya) |
| `GameSettings.set_language` (`_core.py:9272-9278`): hanya `("id","en")`, lalu simpan + terapkan | Tidak ada | `GameManager.set_language()` (validasi → `Localization` → simpan → `signal language_changed`) + `var language` sebagai cermin; bahasa invalid **diabaikan** tanpa menyimpan dan tanpa sinyal. `language_changed` adalah pengganti "gambar ulang tiap frame" pygame |
| Penyimpanan `language` di `settings.json` GLOBAL (`_core.py:9193`, `storage_paths.SAVE_DIR`) | `SaveManager.get_setting`/`set_setting` hanya float | `SaveManager.get_setting_str()`/`set_setting_str()` untuk kunci `settings.language`. **Deviasi tercatat:** port Godot menyimpan semua setting per slot (precedent `game_speed`/`fps_limit`), jadi bahasa ikut per slot — pygame global |
| `en = get_language() == "en"` untuk mekanik/flavor item (`hero_items.py:1632`, `:3894`) | `HeroItems.build_item_mechanics(data, en, ...)` menerima flag dari pemanggil; tidak ada yang memberinya bahasa aktif (`ItemDB.item_mechanics` default `false`) | `MysticLocalization.is_english()` + `ItemDB.item_mechanics_localized(item_id)`. Signature `build_item_mechanics`/`item_mechanics` TIDAK diubah karena dikunci `HeroItemsParityTest` (33 item × id + en) |
| Konsumen teks lain: notifikasi `ui.add_notification` (beli/antre/kirim/lepas item, `_core.py:2185`/`:8005`, `hero_items.py:4052-4097`), `ItemShopUI` (chip hero "MATI" + antrean, banner tanpa hero, label halaman), popup detail item Forge (7 kunci `item_detail_*`/hint) | — | **23 kunci diport sebagai DATA tanpa pemakai**, dan oracle mencetak daftarnya tiap run supaya tidak diam-diam diklaim "sudah": kanal notifikasi UI belum ada di port, `_update_hero_respawns` belum memanggil `deliver_pending_forge_items` (celah runtime yang sudah tercatat di baris FASE 29), `ShopPanel` tab ITEM adalah Control satu-scroll tanpa halaman/chip hero mati, dan popup detail item belum dibangun. Alasan per kelompok + syarat memakainya: `LOCALIZATION_GODOTPP.md` |

**Validasi:** dua lapis. (1) `python3 tools/test_godot_localization_parity.py`
— oracle TANPA pygame dan TANPA Godot: membaca tabel `Localization.gd` dari
berkasnya (parser sadar-string + continuasi `\`), membandingkan **isi dan
urutan** 24 kunci × 2 bahasa dengan `localization._TEXT`, `LANGUAGES`,
`LANGUAGE_LABELS`, dan bahasa bawaan; mengaudit setiap template supaya hanya
memakai `{nama}` polos (kontrak subset `_py_format`); memeriksa closed-world
kunci `tr_text()` di `godot/**/*.gd`; dan menjaga `localization.json` tetap
segar. (2) `godot --headless --path godot
res://tests/LocalizationParityTest.tscn --quit-after 120` — replay fixture di
engine: 48 kasus `tr` (setiap kunci × bahasa), 8 kasus tepi, 21 kasus
`str.format`, 13 kasus `str()`, 7 `set_language`, 7 label, placeholder 48
template, plus plumbing (`GameManager.set_language`/`apply_language` + sinyal,
`SaveManager` setting string, `ItemDB.item_mechanics_localized`, baris BAHASA
+ cycler di layar PENGATURAN yang dibangun `MainMenu` produksi). Harness
men-snapshot `SaveManager.data` + berkas slot dan memulihkannya; CI
menjalankannya dengan `XDG_DATA_HOME` sementara. Kedua lapis masuk
`godot-check.yml` (oracle di langkah **Linter statis**, scene sebagai langkah
headless sendiri), dan `localization.py` + oracle-nya masuk filter `paths`.

**Deviasi terdokumentasi:** (1) `tr` → `tr_text` (native `Object.tr()`),
(2) `**values` → `Dictionary`, (3) `get_language_label(None)` → argumen `""`
(string kosong juga jatuh ke bahasa aktif, sama seperti `language or
_LANGUAGE` Python), (4) subset `str.format` — format spec/konversi/posisional
tidak diimplementasi dan **diaudit agar tidak pernah dipakai** tabel ini,
(5) setting bahasa per slot, bukan `settings.json` global, (6) tanpa
`TranslationServer`/`.po`/`.csv` dan locale engine tidak disentuh — tabel
inline supaya diff terhadap `localization.py` tetap terbaca mesin,
(7) `signal language_changed` sebagai pengganti redraw-per-frame pygame.
Binary Godot tidak tersedia di sandbox saat migrasi dibuat, jadi scene
dijalankan CI; sebagai ganti, algoritma `_py_format`/`_py_str`/`tr_text`
diterjemahkan 1:1 ke Python dan dijalankan terhadap SELURUH kasus fixture
oracle (159 cek, 0 selisih) — sisa risikonya hal spesifik engine, bukan logika.

**Yang tetap terbuka:** 23 kunci tanpa pemakai (butuh kanal notifikasi UI,
pengiriman pesanan forge saat respawn, chip hero mati/antrean + halaman di
toko item, dan popup detail item). Selama permukaan itu belum ada, teksnya
sengaja TIDAK dipasang di UI mana pun supaya tidak ada string yang mengambang
tanpa perilaku.

## Entry point `main.py` (boot, loop, siklus hidup) — 11 September 2026 (FASE 27)

`main.py` (652 baris) adalah satu-satunya berkas pygame yang belum punya
padanan di Godot: **bukan** gameplay, melainkan lapisan aplikasi — boot,
kebijakan loop, preset kualitas, dan siklus hidup Android. Audit
blok-per-bloknya ada di [MAIN_PY_COVERAGE.md](MAIN_PY_COVERAGE.md).

> **Temuan audit:** `main.py` **tidak bisa dijalankan** di repo ini. Impor
> `settings`, `game`, `menu`, `game_settings`, `sound_manager` (`:61-67`,
> `:253-268`) mengarah ke modul yang sudah melebur ke `_core.py`/`_system.py`.
> Karena itu port mengambil perilaku dari TEKS SUMBER (konstanta loop, urutan
> boot, cabang siklus hidup), bukan dari menjalankannya, dan berkas pygame
> tidak disentuh — sesuai aturan `MIGRASI_1_1.md`. README (`python main.py`)
> usang.

| Bagian pygame | Sebelum (Godot) | Sesudah (FASE 27) |
|---|---|---|
| BGM + ambient sejak boot (`main.py:160-164`: `play_bgm(..., fade_ms=3000)` + `play_ambient(..., 0.8)` **sebelum** menu dibuat) | Tidak ada — `AudioManager.play_bgm/play_ambient` hanya dipanggil `GameManager.start_level`, jadi menu utama dan layar pilih level diam | `AppShell._start_boot_audio()` di `_ready` autoload; panggilan `start_level` berikutnya no-op karena track sama |
| Banner boot device/save/input/quality (`main.py:279-291`) + `crash_log.txt` (`mobile/debug.py:427-450`) | Tidak ada | `AppShell._print_boot_banner()` + `_write_session_log()` (`user://crash_log.txt`, rotasi ekor 256 KB) |
| `MAX_CATCHUP = 4` — diturunkan dari 8 untuk mencegah "spiral kematian" (`main.py:332`) | Nilai bawaan engine **8** (`physics/common/max_physics_steps_per_frame` tidak pernah disetel) | `project.godot`: `max_physics_steps_per_frame=4`; `AppShell._check_loop_policy()` memperingatkan kalau diubah; dikunci tes |
| Preset kualitas `auto_detect_quality` (Android/iOS = LOW → 30 FPS, desktop = HIGH → 60 FPS, `mobile/perf.py:861-871`) | Tidak ada; `settings.quality` hanya dipakai untuk `max_damage_numbers` | `AppShell._detect_quality()` + `target_fps()`; `touch_mode()` juga menghormati `MYSTIC_FORCE_TOUCH=1` (paritas `platform_utils.py:60`) |
| Adaptive quality — jendela 90 frame, turun < 26 FPS, naik > 52 FPS, cooldown 180/300 frame (`mobile/perf.py:877-911`) | Tidak ada (dicatat sebagai celah di FASE 25/26) | `AppShell._update_adaptive_quality()` + tangga high↔medium↔low + cooldown; konsumen = batas FPS |
| `clock.tick(limit)`: setting pemain hanya boleh MENURUNKAN di perangkat sentuh, selain itu `Quality.target_fps` (`main.py:620-641`) | `GameManager.apply_fps_limit` menulis `Engine.max_fps` mentah — slider SETTINGS bisa melangkahi pembatas 30 FPS preset LOW | `AppShell.resolve_fps_limit()`; `GameManager.apply_fps_limit` mendelegasikan (aman saat autoload belum terpasang) |
| `_handle_background()` — app ke latar: `mixer.pause()` + `music.pause()`, lalu lanjut saat `APP_FG` (`main.py:128-155`) | Tidak ada padanan: musik terus berbunyi saat app di-minimize (hold taktis sudah dilepas `Main._notification`, FASE 18) | `AppShell._notification` PAUSED/RESUMED → `AudioManager.pause_bgm/pause_ambient` (statusnya disimpan di flag `bgm_paused`/`ambient_paused` karena `stream_paused` engine diabaikan saat tidak ada playback aktif); **tidak** dihidupkan kembali kalau pemain sedang di menu PAUSE |
| Splash boot → menu (`main.py:492-501`) | `SplashScreen.gd` **node yatim** — tidak ada di `main.tscn` dan tidak pernah di-`preload`, jadi Godot melompat langsung ke menu (layar splash tidak pernah terlihat) | `Main._maybe_show_splash()` memasangnya di atas menu sampai signal `finished`; klik/tombol apa pun hanya melewatinya (`ControllerRouter._splash_active()` yang sudah ada dari FASE 24 kini benar-benar punya splash untuk dideteksi). View splash dibuat `MOUSE_FILTER_STOP` + `_gui_input` supaya klik tidak **tembus** ke tombol menu di baliknya — kalau tidak, klik "lewatkan splash" justru menekan MULAI GAME karena jalur GUI Control berjalan sebelum `_unhandled_input`. |

**Validasi:** `godot --headless --path godot res://tests/MainEntryParityTest.tscn
--quit-after 240` (langkah CI baru di `godot-check.yml`, gerbang log yang
sama) — 40+ cek: kebijakan loop, `crash_log.txt` + `SESSION START`, track BGM
boot, matriks batas FPS (desktop vs mode sentuh, setting 0/20/30/45/120),
tangga adaptive quality + cooldown + jendela 90, idempotensi PAUSED, cabang
"menu PAUSE menahan audio", dan boot yang mendarat di menu tanpa splash.
`gdparse` + `tscn_lint` + `check_refs` + `particles_lint` + 5 self-test
log-gate lulus lokal; binary Godot tidak tersedia di sandbox.

**Deviasi terdokumentasi:** (1) **headless** (`godot --headless`, termasuk CI)
mematikan adaptive quality dan membiarkan `Engine.max_fps = 0` — tanpa layar
dan vsync, "FPS" tidak bermakna dan pembatas hanya memperlambat run yang
waktunya dihitung dalam FRAME; splash juga dilewati karena ia akan menelan
input sintetis tes. (2) Konsumen adaptive quality **hanya** batas FPS: rasio
partikel/kabut preset pygame belum punya padanan, jadi
`SparkField.particle_ratio` tetap 1.0 (dikunci `RenderFxParityTest`, dicatat
sebagai deviasi FASE 26). (3) `sys.excepthook` tidak diport: Godot tidak punya
exception hook global, dan satu error di `_process`/`_physics_process` memang
hanya mencetak `SCRIPT ERROR` lalu engine melanjutkan frame berikutnya — jadi
maksud `try/except` main.py sudah dipenuhi mesin; yang diport adalah arsip
lognya. (4) Tidak dibuat aksesor state kanonik baru: mesin state
SPLASH/MENU/GAME/PAUSE sudah hidup di `ControllerRouter.current_state()`
(FASE 24) dan `TouchHUD.sync_from_match()`, dan menduplikasinya di `AppShell`
hanya membuka peluang drift.

**Yang tetap terbuka** (rinci di `MAIN_PY_COVERAGE.md`): layar bootcheck/
diagnostics (mengukur jalur blit SDL yang tidak ada di Godot), getar haptik
(`plat.vibrate`), 4 mode overlay debug `mobile/debug.py`, tahan-tombol-jeda →
overlay debug, multi-sentuh penuh (`claimed`/gestur per id sentuhan), dan cloud
save poll (plugin Play Games).

## Blok FX `_render.py` (percikan, ledakan, panah lane) — 11 September 2026 (FASE 26)

`_render.py` adalah modul gabungan 7 berkas lama (docstring `:1-11`); audit
blok-per-bloknya kini tertulis di
[RENDER_PY_COVERAGE.md](RENDER_PY_COVERAGE.md). Layar cinematic (intro level,
banner boss, kematian boss), wave announcer, combo, achievement, floating text,
dan screen shake sudah diport di fase-fase sebelumnya. Yang **belum punya
padanan sama sekali** adalah tiga blok `effects.py`: `HitParticle`
(`_render.py:418-493`), `DeathExplosion` (`:494-571`), dan `PathPreview`
(`:1275-1370`) — yang terakhir adalah fitur yang benar-benar hilang dari layar
(`PARITY_AUDIT.md` butir 4: "Di Godot tidak ada satu pun berkas `PathPreview`").

| Bagian pygame | Port Godot | Catatan |
|---|---|---|
| `HitParticle` (`:418-493`) — gravitasi 0.15, gesekan 0.95, sprite pra-render 3·base px di-scale per frame, alpha `int(255·sisa)`, ukuran `max(1, int(size·sisa))` | `scripts/render/HitSpark.gd` | Gerak + aturan alpha/ukuran apa adanya. Pusat lingkaran = `posisi_blit + pusat_kanvas × faktor_skala` (pygame mem-blit di `int(x) − ukuran*3//2`; base genap + ukuran gasal = offset 0,5 px) — jejak fixture yang mengunci, bukan `int(x)` polos |
| `DeathExplosion` (`:494-571`) — 8/15/25 partikel per preset, palet 3 warna per tim, kilat pusat 8 frame (`int(20·intensity)` + `//2`) | `scripts/render/DeathBurst.gd` | Urutan konsumsi RNG direkam oracle: angle → speed → `choice(warna)` → `randint(spark)` → `randint(20,35)`. Replay Godot memakai nilai yang sama lewat `rng` ter-script, jadi jumlah/urutan/rentang roll ikut terkunci |
| `EffectManager.particles`/`explosions` + `MAX_PARTICLES 500` / `MAX_EXPLOSIONS 80` + `add_hit_particles` + `add_death_explosion` + bagian keduanya di `update()`/`draw()` (`:601-800`) | `scripts/render/SparkField.gd` (data, dimiliki `GameManager.spark_fx`) + `scenes/fx/SparkLayer.gd` (draw, z 800) | Satu lapangan global seperti satu `EffectManager` pygame. Trim membuang yang TERTUA (`del [0:…]` / `del [0]`); di-tick `GameManager._process` dengan akumulator 60 Hz |
| Situs pemanggil pygame: `Minion.take_damage` count 4 (`_entity.py:5842`), `Boss.take_damage` count 6 (`base_boss.py:6057`), `Castle.take_damage` count 10 (`_entity.py:1816`), kematian minion `'medium'` (`:5863`) / boss `'large'` (`base_boss.py:6076`), taktik GATHER + PROTECT CASTLE `'small'` (`tactical_commands.py:389/537`, hanya cabang `not silent`) | `CombatSystem._hit_spark_count` + `Minion.die` + `Boss.die` + `TacticalCommands` | Pygame memanggilnya di `take_damage` tiap unit; Godot memusatkan damage di `CombatSystem.apply_damage`, jadi percikannya ditaruh tepat di samping `_spawn_damage_number`. **Hero & menara = 0** (tidak ada call site pygame) sehingga kontrak "serangan dasar tanpa impact FX" tidak tersentuh |
| `PathPreview` (`:1275-1370`) + `EffectManager.path_preview`/`show_path_preview` (`:623/784/789/797`) + pemicu `_core.py:1756-1762` | `scenes/fx/PathPreview.gd` + `Main._show_path_preview()` dari `_on_wave_started` | 120 frame, fade in 20 / out 40, `alpha = int(200·ratio)`, `offset = int(t·2) % 20`, satu panah tiap 8 titik, arah dari titik `i+4`, pulse `(i//8 + offset//5) % 4`, panah 8 px (pulse) / 5 px (redup, alpha//2). Lane dibaca dari `ArenaMap.get_lane_path` dengan urutan `top, mid, bot` persis `_core.py:1757` |
| `KillFeed` (`:1103-1201`), `PopupAnimation` (`:1202-1239`) | — (**sengaja tidak diport**) | Dead code di pygame: `kill_feed.add_kill/draw` nol call site; `popup_anim.get_scale/get_offset_y` nol call site (yang dipanggil `_core.py` hanya `show/hide/update`). `build_dead_claims()` di tool oracle mengunci `sites == []` supaya klaim ini tidak diam-diam basi |

**Deviasi terdokumentasi (mesin/lapisan lain, bukan pilihan gaya):** (1)
`add_hit_particles` pygame dikalikan `mobile.perf.Quality.particle_ratio`
yang di preset HIGH desktop = **0.70**, jadi pygame sebenarnya memunculkan
3/4/7 percikan untuk minion/boss/castle; Godot memakai **1.0** karena lapisan
adaptive quality belum diport (SYSTEM_PY_COVERAGE §3). Knob
`SparkField.particle_ratio`/`particles_enabled` tersedia, faktanya direkam
fixture (`py_quality`) dan dikunci `_test_wiring`; (2) pygame memakai `random`
global, Godot memakai RNG ter-script di harness dan RNG global di produksi —
yang dikunci adalah NILAI dan URUTAN roll, bukan algoritmanya; (3) raster
tidak dibandingkan (`draw_circle`/`draw_colored_polygon` Godot vs sprite hasil
`transform.scale` pygame) — yang dikunci geometri, warna, alpha, dan urutan
perintah gambar; headless Godot tidak bisa screenshot; (4) `_fx_chain`
(`hero_items.py:2728-2745`, 8 call site) belum ikut — rantai damage item sudah
diport, FX kilatnya belum; (5) z-index: effects Godot di z 790/800 (di atas
unit yang bersistem `z = y` ≤ 720) karena pygame menggambar effects SETELAH
semua entitas (`_core.py:2917`), dengan urutan internal path preview → ledakan
→ percikan → floating text.

**Oracle-nya menjalankan kode pygame asli, bukan salinan:**
`tools/test_render_parity.py` mengganti `pygame.Surface` dengan subclass
perekam, lalu merekam `pygame.draw.circle`/`polygon` + `transform.scale` +
`Surface.blit` + `set_alpha` yang benar-benar terjadi, dan MENURUNKAN op dari
jejak itu (pusat = posisi blit + pusat sprite × faktor skala; radius ikut
skala; alpha = alpha lingkaran × alpha sprite). Jalur lane yang dipakai adalah
keluaran `map_components.generators.PathGenerator` sungguhan (111/65/101
titik), dan jumlah percikan per situs (4/6/10) serta ukuran ledakan
(`small`/`medium`/`large`) di-PIN dari teks sumber `_entity.py`,
`bosses/base_boss.py`, `tactical_commands.py`.

**Validasi:** `tools/test_render_parity.py` (211 pemeriksaan: fixture
determinis 2× run, drift vs `godot/tests/fixtures/render_fx.json`, dan kunci
statis konstanta + ekspresi `.gd`) lulus lokal; `gdparse` seluruh `.gd` +
`tscn_lint` 39 scene + `check_refs` + `particles_lint` + 5 self-test log-gate +
`test_system_perf_parity.py` (158) + `test_godot_match_parity.py` +
`test_basic_attack_no_impact_fx.py` lulus lokal. `RenderFxParityTest`
(73 frame percikan, 32 frame/792 op ledakan, 4 skenario `add_hit_particles` +
batas 500/80, 130 frame + 490 polygon panah lane, wiring `GameManager.spark_fx`)
dijalankan CI `godot-check.yml` langkah **4v** — **binary Godot tidak tersedia
di sandbox**, jadi replay headless-nya hanya bisa dibuktikan di sana, dan memang
baru di sanalah tiga bug ketangkap (run `34559683506` → `34560081693` →
`34560657146`, langkah 4v akhirnya **success**):

1. `PathPreview.gd` memakai `sqrtf()` — **tidak ada di Godot 4** (hanya
   `sqrt()`), dan karena RHS jadi tanpa tipe, `var dist := ...` ikut
   "Cannot infer the type". `gdparse` tidak menangkapnya (itu pemeriksaan
   semantik, bukan sintaks) dan efeknya berantai: `Main.gd` gagal load karena
   me-`preload` PathPreview. Sekarang `check_refs.py` punya aturan 7 yang
   memflag `sqrtf/hypotf/expf/logf/sinf/cosf/tanf/atanf/atan2f/acosf/asinf`.
2. Fixture `burst[*].particles` kosong — oracle memfoto baris partikel SETELAH
   loop 40 frame, padahal pygame membuang partikel mati di
   `DeathExplosion.update`. Godot benar (8/15/15/25); fixture yang bilang 0,
   dan 63 × 5 assertion per-partikel membandingkan array kosong.
3. Assertion "alpha penuh 200 di tengah durasi" membaca `ops[0]`, padahal panah
   non-pulse memang digambar redup (`200 // 2 = 100`) dan panah pertama sebuah
   frame bisa yang redup — perilaku pygame yang benar (alpha unik di step 60:
   `{100, 200}`). Dikunci lewat alpha terbesar + terkecil.

Aritmetika port juga dihitung silang terhadap jejak pygame di fixture
(73 + 32 + 16 frame, 0 selisih; 63 partikel burst, 0 selisih, 315 roll terpakai
semua) sebelum CI dijalankan. Yang TETAP TERBUKA di jalur ini: **piksel** (raster
lingkaran/segitiga), `_fx_chain`, dan label prompt/skip yang belum ikut mode
input (`_begin_prompt_text`/`_skip_button_label`).

## Blok performa & overlay FPS `_system.py` — 11 September 2026 (FASE 25)

`_system.py` adalah modul gabungan 5 berkas lama (docstring `:1-9`); audit
blok-per-bloknya kini tertulis di
[SYSTEM_PY_COVERAGE.md](SYSTEM_PY_COVERAGE.md). Yang **belum punya padanan sama
sekali** adalah blok `performance.py` (`:29-185`) dan `fps_counter.py`
(`:189-387`): grid spasial, culling layar, dan panel FPS. `SoundManager`
(`:450-731`) dan `SaveManager` (`:732-1125`) sudah selesai di Fase 4e/21 — di
sini hanya diaudit ulang (hasil: tidak ada metode berperilaku lain yang hilang,
`play_positional` dan cloud save Play Games tetap tercatat sebagai yang tidak
diport).

| Bagian pygame | Port Godot | Catatan |
|---|---|---|
| `FrustumCuller` (`_system.py:40-50`, `MARGIN 80`, `is_visible(x, y, radius=30)`) | `scripts/systems/FrustumCuller.gd` | Batas inklusif `−m ≤ x ≤ W+m` dengan `m = 80 + radius` diambil apa adanya; layar dibaca dari viewport (`is_visible_world` memproyeksi titik dunia lewat transform canvas). fixture `culler` = 17 kasus, termasuk `x == −margin − radius` |
| Konsumen culler pygame: skip blit unit/partikel (`_core.py:2875-2910`) | `scenes/fx/WorldPopups.gd._draw` (`POPUP_RADIUS 24`) | Di Godot CanvasItem di-cull GPU, jadi padanan yang setia bukan "jangan gambar unit" (sudah gratis) tapi "jangan bangun `draw_string` per frame" — antrean 300 teks rusak |
| `SpatialGrid` (`:52-142`): `cell_size=60`, `query_range` bbox→jarak², loop cy luar / cx dalam, satu bucket per sel | `scripts/systems/SpatialGrid.gd` | `insert`/`clear`/`update_from`/`query_range`/`query_enemies`. `int(x/cell)` Godot memotong ke nol → `_cell()` memakai `floor` (koordinat negatif!). `query_range` = cabang `team=None` pygame yang **tidak memfilter apa pun**; `query_enemies` = cabang `team` yang buang sekutu **dan** bangkai |
| `_grid` global + `update_spatial_grid` + `query_enemies_in_range` (`:144-185`), dijadwalkan `_core.py:2007-2013` (frame GENAP saja) | `CombatSystem._spatial_grid` + `update_spatial_grid(_from_tree)` + `Main._process` (`_grid_tick % GRID_REBUILD_EVERY == 0`, `GRID_REBUILD_EVERY := 2`) + `query_enemies_in_range` | Urutan kandidat = urutan bucket (minion → hero+boss), lalu menara/nexus **appended** (memang tidak diindeks grid pygame). Kesegaran grid 2 frame (`GRID_STALE_FRAMES`); grid basi → fallback `enemies_in_radius`, jadi menu/pause/harness lama tidak pernah melihat hasil kosong |
| Konsumen grid pygame: `Minion._get_enemies` (`_entity.py:5635-5680`) | `Minion._find_target_smart` (`CombatSystem.query_enemies_in_range(team, global_position, attack_range + 30.0)`) | HANYA jalur targeting minion yang dialihkan. Mage-chain, archer-volley, splash, AoE, aura, item tetap scan grup — urutan kandidatnya sudah dikunci tes lain dan pygame juga tidak lewat grid di sana |
| `FPSCounter` (`:202-386`): `deque(maxlen=120)`, refresh angka tiap 10 frame, jendela statistik 30, panel 200×95 @(10,45) | `scenes/ui/FpsCounter.gd` | `update(current_fps)` murni aturan riwayat; `_draw()` mengeksekusi `build_ops(state, measurer)` — daftar perintah gambar sebagai fungsi murni supaya bisa dibandingkan dengan jejak `pygame.draw.rect/line` + `font.render` sungguhan (32 op) tanpa GPU |
| F8 (`main_desktop_legacy.py:98-100`) | `Main._on_key` → `toggle_fps_counter()` | Ditangani SEBELUM dispatch state splash/menu/game/pause dan tombolnya tidak ditelan — persis legacy. `DebugLayer` memakai `PROCESS_MODE_ALWAYS` karena pygame men-update counter di luar dispatch state |
| `AdaptiveQuality` / `fps_limiter.py` (`:400-448`) | — (cap FPS tetap `Engine.max_fps` via `GameManager.apply_fps_limit`) | **Sengaja tidak diport**: `tools/test_system_perf_parity.py` membuktikan nol call site di luar `_system.py` (fixture `dead.adaptive_quality.sites == []`); tool gagal kalau suatu hari ada call site muncul, supaya "tidak diport" tidak diam-diam basi |

**Deviasi terdokumentasi (mesin, bukan pilihan gaya):** (1) pygame membekukan
`death_anim` unit di luar layar (`_entity.py:5871-5878`) — Godot mengurangi
`death_anim` di `_process`, jadi animasi kematian di luar kamera tetap selesai;
memindahkan penurunan itu ke sisi-draw akan MENAMBAH perilaku (unit membeku
selamanya kalau kamera tidak pernah lewat), jadi culling Godot murni draw-side;
(2) `main_desktop_legacy.py` memanggil `fps_counter.update/draw` DUA kali per
frame (`:455-456` dan `:461-462`, sisa penggabungan berkas) — Godot menyampel
sekali per frame; (3) `FPSCounter.draw()` pygame ternyata mati (`NameError: get_font`,
`from _core import *` dieksekusi saat `_core` parsial karena import melingkar):
panel itu tidak pernah tampil di legacy build. Tool oracle menambal
`_system.get_font` untuk bisa mengambil jejak render-nya dan menyimpan faktanya
di fixture (`fps.py_draw_needs_shim`); port justru memperbaiki jalur render itu;
(4) lebar teks yang dipakai untuk meratakan label `FPS`, status, dan petunjuk
`[F8] toggle` mengikuti metrik font Godot (TTF pygame + `font.render` tidak bisa
direproduksi) — yang identik adalah ATURAN letaknya (semua konstanta posisi
di-pin), bukan raster-nya; headless Godot juga tidak bisa screenshot, jadi yang
dikunci adalah daftar perintah gambar, bukan piksel; (5) bucket grid boleh basi
satu frame — unit yang baru MELANGKAH MASUK radius baru terlihat setelah rebuild
(persis pygame), sedangkan jarak yang dibandingkan selalu posisi HIDUP karena
bucket menyimpan referensi node.

**Validasi:** `tools/test_system_perf_parity.py` (158 pemeriksaan: fixture
determinis 2× run, drift vs `godot/tests/fixtures/system_perf.json`, dan kunci
statis `CELL_SIZE/MARGIN/HISTORY_SIZE/GRID_REBUILD_EVERY` + geometri/warna
overlay + `for group in ["towers", "nexus"]` + fallback dibaca langsung dari `.gd`)
lulus lokal; `gdparse` `.gd` yang disentuh + `tscn_lint` + `check_refs` +
`particles_lint` + `tools/test_godot_match_parity.py` lulus.
`SystemPerfParityTest` (9 skenario grid / 19 kueri berurutan, 17 kasus culler,
150 sampel FPS + 32 op render + 8 band tangga warna + wiring grid di scene
sungguhan) dijalankan CI `godot-check.yml` langkah 4u — **binary Godot tidak
tersedia di sandbox**, jadi replay headless-nya diverifikasi di sana. Yang TETAP
TERBUKA di jalur ini: **piksel** panel FPS (raster/alpha blend `SRCRECT`-nya
pygame), dan tie-break target menara yang beda di KEDUA sisi (lihat
"Belum setara").

## Lapisan gamepad — 11 September 2026 (FASE 24)

`_core.py` punya delapan modul gabungan; audit blok-per-blok-nya kini tertulis
di [CORE_PY_COVERAGE.md](CORE_PY_COVERAGE.md). Blok terbesar yang **belum punya
padanan sama sekali** adalah `controller_manager.py` (`_core.py:9299-10234`,
±935 baris) — satu-satunya konsumennya `main_desktop_legacy.py` (build Android
pygame memasang `menu.controller_mgr = None`, `main.py:250`). Karena lapisan
ini tidak ada, hint bar pygame tidak mungkin diport (komentar lama
`HUD._build_hint_bar`: "Godot belum punya lapisan input gamepad"). Kini diport:

| Bagian pygame | Port Godot | Catatan |
|---|---|---|
| `ControllerManager` (deteksi tipe, kursor virtual, aksi, rumble, label/hint, snap UI) | `scripts/systems/ControllerManager.gd` | Nilai/urutan/aturan sama: kursor 12→25 kurva `magnitude^1.5` deadzone 0.25; D-PAD fresh + repeat delay 22/rate 5; trigger `> 0.5` strict; scroll accum 0.55/deadzone 0.18/step 1.0 guard 8 tick; `rumble` = `int(frames × 16.67)` ms + stop otomatis; tabel label xbox/ps/generic + 7 konteks hint |
| Blok routing aksi (`main_desktop_legacy.py:146-320`) | `scripts/systems/ControllerRouter.gd` | Menerjemahkan aksi pad ke JALUR PRODUKSI keyboard/mouse: `Main._on_key/_on_click/_on_right_click`, `_cinematic_click`, `_toggle_pause`, `_tactical_release_all`, `MainMenu._handle_escape/_do_resume`, `GameManager.next_level`, `HUD.toggle_debug_overlay` |
| `draw_cursor` (`:9837-9934`) | `scenes/ui/VirtualCursor.gd` | Geometri/warna 1:1 (pulse `sin(t·0.1)·0.3+0.7`, glow r12, crosshair ±3..±8, bracket 12 px offset 5); kotak beradius via StyleBoxFlat |
| `Menu._toggle_input_mode` + tombol `input_select` (`:4774`, `:7025-7037`) | `MainMenu._toggle_input_mode` + tombol **INPUT** di menu utama + label `INPUT: …` kiri-bawah | Termasuk `rescan()` + `debug_print()` saat controller belum terdeteksi |
| `Game._draw_input_hints`/`_input_label` (`:2701-2756`) | `HUD._hint_rows` + `ControllerManager.get_hints` | Bar kini **tampil hanya di mode controller** (persis `_core.py:2709-2714`) dan memakai tabel label pygame; keyboard/sentuh tetap tanpa bar (assertion lama `UiHudParityTest` tidak berubah) |
| STATE_SPLASH (`main_desktop_legacy.py:154-157`) | `Main._splash_active/_skip_splash` + `SplashScreen` masuk grup `splash` | Node splash-nya sendiri masih belum dipasang di `main.tscn` (tercatat di CORE_PY_COVERAGE) |

**Deviasi terdokumentasi (mesin, bukan perilaku):** (1) pygame membaca
tombol/axis MENTAH per vendor (`XBOX_MAP`/`PS_MAP`/`GENERIC_MAP`), Godot
menormalkan lewat SDL sehingga cukup satu `BUTTON_MAP` — ketiga tipe tetap ada
karena LABEL-nya beda; (2) D-PAD pygame = `get_hat(0)`, Godot = 4 tombol
`JOY_BUTTON_DPAD_*` yang disintesis jadi vektor hat; (3) pygame punya
`get_numbuttons/get_numaxes`, Godot tidak — `_device_button_count/_axis_count`
memakai `Input.is_joy_known()` (21/6 vs 0/0) sehingga aturan fallback
"≥ 11 tombol & ≥ 4 axis → xbox" tetap dieksekusi apa adanya; (4) `rumble(low,
high, ms)` → `start_joy_vibration(weak=high, strong=low, detik)`; (5) snap
kursor membaca rect `BaseButton` hidup (pygame: dict `ui_buttons`/`buttons`);
(6) cabang `popup_target` TANPA `shop_open` tidak punya padanan karena toko
Godot terpadu.

**Oracle-nya menjalankan kode pygame asli, bukan salinan:**
`tools/test_godot_match_parity.py` menambal `pygame.joystick` dengan perangkat
ter-script lalu menjalankan `ControllerManager` pygame sungguhan, dan
**memotong + meng-`exec` blok routing `main_desktop_legacy.py` apa adanya**
(dengan `game`/`menu`/`fps_counter`/`splash` palsu yang merekam panggilan) —
jadi kalau routing legacy berubah, fixture ikut berubah dan CI menolaknya.
`main_desktop_legacy.py` kini ikut filter `paths` di `godot-check.yml`.

**Validasi:** `gdparse` seluruh `.gd` + `tscn_lint` 36 scene + `check_refs` +
`particles_lint` + 5 self-test log-gate + `test_godot_match_parity.py`
(freshness, dua run identik) lulus lokal. `ControllerInputParityTest` baru
(9 deteksi perangkat, 7 skenario kursor, 12 skenario aksi/138 frame, 5 rumble,
6 snap/find, 136 label, 28 konteks hint, 60 skenario routing + 1 kasus
`tick_frame` jalur produksi penuh) dijalankan CI — **binary Godot tidak
tersedia di sandbox**, jadi replay headless-nya diverifikasi di
`godot-check.yml`. **Piksel** kursor (glow/bracket) dan **audio** belum teruji;
perangkat fisik tidak diuji (hanya perangkat ter-script).

## Integrasi TouchHUD — 10 September 2026 (FASE 23)

Temuan audit: `TouchHUD.gd` sudah ditulis lengkap tetapi **tidak dipakai di
scene mana pun** — tombol pause/skip/replay/next/menu tidak muncul di game,
sehingga versi Godot praktis tidak bisa dimainkan di HP. Kini dipasang penuh
tanpa menyentuh kode pygame:

| Bagian | Sebelum | Sesudah (paritas pygame) |
|---|---|---|
| Pemasangan | Node yatim, tanpa signal | Anak HUD paling atas (pygame `hud.draw` terakhir di `STATE_GAME`), `hud_action` tersambung ke `Main._apply_touch_action` |
| Geometri | Rect hard-code duplikat | Dibangun dari kanon `HudLayout.TOUCH_BUTTONS` (sumber tunggal, anti-drift dari fixture `touchhud`) |
| Gambar | Skala manual `size/1280` | Gambar 1:1 logis — skala manual menggelembung di aspect expand (size logis 1624x720 ikut diskala); stretch `canvas_items` yang memetakan ke fisik |
| Input | Mouse + touch (aksi ganda) | Mouse SAJA — sentuhan tiba sebagai mouse via `emulate_mouse_from_touch` (kini eksplisit di `project.godot`); dua cabang = toggle debug 2x / back 2x ESC |
| Sync | Kunci state manual | `sync_from_match()` tiap frame (paritas `hud.sync`): node hanya di match (pygame tak menggambar hud di menu/pause/splash), matriks 7 kunci + `next_level` dari `next_level_number()` |
| Panel kanan | Diabaikan | Override `_panel_ada`: pause + FPS sembunyi saat rail ada (pause pindah ke `RailPause`, FPS dihapus dari rail pygame — `sidepanel.py:125-128`) |
| Tombol FPS | Default nyala | Default mati + env `MYSTIC_DEBUG=1` (paritas `main.py:180`); targetnya overlay FPS minimal (esensi `DebugOverlay`, bukan port penuh 450 baris/4 mode) |
| Router aksi | Tidak ada | `_apply_touch_action` = port `apply_hud_action`: pause (gate `STATE_GAME` + abaikan saat menu terbuka), debug, skip (rantai `_cinematic_click`), replay/next/menu (guard usai-match), back (`menu.handle_key(ESCAPE)` — tombolnya tetap tak-tampil seperti pygame) |

**Validasi:** `gdparse` seluruh `.gd` + `tscn_lint` + `check_refs` +
`particles_lint` + 5 self-test log-gate + `gen_* --check` + scope-check
lulus lokal; `TouchHudParityTest` baru (z-order, geometri=kanon + hit
MIN_TAP 80, matriks 7 kunci, sembunyi-di-menu/pause, tap→signal, guard +
jalur positif replay/next/menu/pause/skip/debug/back, override panel) +
langkah CI **4s** — replay headless diverifikasi CI, binary Godot tak
tersedia di sandbox. Yang TETAP TERBUKA di jalur sentuh: long-press jeda
→ overlay debug (`main.py` — butuh deteksi tahan), safe-area poni
(geometri kanon = inset nol), dan 4 mode + grafik `DebugOverlay` penuh.

## Koreksi panel kanan — 10 September 2026

Laporan lapangan: "di Pygame ingame ada panel kanan, di Godot tidak ada".
Audit kode + render panel pygame asli (`mobile/sidepanel.py` pada 1624x720)
menemukan rail Godot sudah ada (`SidePanel.gd` + `TacticalBar.gd`) tetapi
menyimpang dari pygame pada 6 titik — semuanya diperbaiki tanpa menyentuh
kode pygame:

| Bagian | Simpangan Godot | Perbaikan (paritas pygame) |
|---|---|---|
| Kapan rail ada | Rail MUNCUL di 1280x720 persis (`viewport.x >= 960`), menutupi + memblokir klik 300 px kanan arena (base Dire tak terlihat/tak bisa diklik — `_on_click` lewat `_unhandled_input` dimakan rail `MOUSE_FILTER_STOP`) | `has_side_panel()` = landscape DAN sisa layar `>= 120` (`sisa >= 120` `platform_utils`): 16:9 = TANPA rail, arena penuh; HP 18:9+ = rail selebar sisa layar |
| Posisi/lebar rail | Lebar 300 px ditempel di TEPI VIEWPORT (kanan) | `Rect(1280, 0, sisa, 720)` menempel di TEPI ARENA; 344 px pada 1624x720, cap 920 (paritas batas total 2200) |
| Tombol tactical tak memenuhi syarat | DISEMBUNYIKAN (`btn.visible = enabled`) | Tampil ABU tak-bisa-ditekan (`disabled` + `mouse_filter IGNORE`) — pygame SELALU menggambar kelima kotak (bg 45,45,50) dan `btn.visible` hanya mematikan hit-test. `panel_available()` kini `visible and not disabled` (nilai oracle tak berubah) |
| Sorot HOLD | Tidak ada indikator perintah ditahan | Tombol yang ditahan menyala + chip "HOLD" (paritas `di_hold` + chip pygame) |
| Baris hero | Tanpa titik skill | Titik q/w/e/r (ungu siap / gelap belum, pitch 14 px) via `Hero.is_skill_ready` |
| Latar rail | Gradien datar | Bata batu port `_gambar_panel_samping` (bata 34 px selang-seling, gradasi kiri, garis emas) sebagai `StoneBG` |
| STATUS + gate gameplay | Teks shield beda; isi hanya saat `playing` | `LV n [SHIELDED]` / `Wave n (Shield)` persis pygame; isi tampil saat playing/victory/defeat (paritas `dalam_gp`) |

Tanpa rail (16:9/potret): TacticalBar dilipat jadi chip TACTICAL kecil di
kanan-bawah arena (revisi 10 September — lihat seksi di bawah; dulu kotak
220x210-nya mengambang menutupi map) dan SEMUA tab toko memakai modal tengah
(paritas "posisi lama" popup pygame saat `panel_popup_pos` None).

Bonus bug yang ditemukan asersi baru: `_panel` ShopPanel adalah
PanelContainer sehingga minimum size-nya mengikuti tinggi KONTEN
(isi tab menara >2000 px) — offset `_layout_panel` di-clamp engine dan
popup/modal meluber jauh ke bawah frame (tertangkap: 900x2294, bukan
900x560). Diperbaiki dengan wrapper `ShopClip` (Control polos memutus
rantai minimum-size) sehingga panel pas rect dan ScrollContainer
benar-benar menggulir.

**Validasi:** `gdparse` + `tscn_lint` + `check_refs` + `particles_lint` +
5 self-test log-gate + `gen_* --check` + scope-check lulus lokal;
`MobileSidePanelParityTest` ditulis ulang (rail dikunci pada viewport lebar
1624x720, TANPA rail di 16:9, fallback tactical + modal di 16:9, 5 tombol abu
saat roster kosong). Replay headless (termasuk `TacticalInputParityTest` yang
membaca `panel_available()`) diverifikasi CI — binary Godot tak tersedia di
sandbox. Piksel rail (bata/font/komposit) tetap milik bucket piksel.

## Koreksi panel HUD menutupi map + panel hero hilang — 10 September 2026

Laporan lapangan: "tactical command pada Godot menghalangi map, dan popup
upgrade hero juga tidak ada". Dua-duanya panel HUD yang salah tempat saat
layar TIDAK punya rail kanan (project default 1280x720 = 16:9 persis):

| Bagian | Simpangan Godot | Perbaikan (paritas pygame) |
|---|---|---|
| Kotak TACTICAL COMMANDS tanpa rail | Kotak 220x210 mengambang di kanan-bawah ARENA: map tertutup dan ketukan di sana dimakan `MOUSE_FILTER_STOP` (tak sampai ke unit) | Di pygame tanpa panel kanan tombol command memang **tidak digambar sama sekali** (pemain memakai hotkey G/F/T/C/B/D; `SidePanel.draw` early-return). Godot menyediakan chip **TACTICAL** kecil (148x32, di atas tombol SKIP) untuk HP tanpa keyboard; kotak command terlipat default, dibuka dengan ketukan chip, dan **menutup sendiri** begitu perintah dilepas atau klik di luar panel. Ada rail = perilaku lama (kotak di dasar rail) tak berubah |
| Panel hero (popup upgrade) | Panel 280x276 SELALU tampil — dengan teks "tidak ada hero dipilih" + tombol upgrade kosong — di atas map kiri-bawah (base Radiant), dan menelan ketukan hero di sana; tinggi panel dipatok 276 sehingga konten yang lebih tinggi mendorong tombol UPGRADE keluar layar | Panel hanya tampil saat ada hero terpilih & hidup (`HeroPanel.draw` pygame `if not h or not h.alive: return`). Dengan rail, panelnya pindah KE DALAM rail di jalur popup pygame (`panel_pos_bawah`, `ZONA_POPUP_Y` = 430 pada 720 = dasar kotak tactical di rail Godot) sehingga arena tak tertutup; tanpa rail jatuh ke fallback pygame (20, H-296). Tinggi = `max(276, minimum konten)` lewat `MobileLayout.hero_panel_rect()` |

Revisi ini TIDAK menyentuh kode pygame: nilai oracle (`panel_available()`,
jejak `hold_start`/`hold_end`, teks/label panel hero) tetap sama — yang
berubah hanya kapan & di mana panel digambar. Asersi yang ikut diperbarui:
`MobileSidePanelParityTest` (16:9: chip tampil, kotak terlipat default,
kotak terbuka di kanan-bawah arena saat chip ditekan; panel hero
tersembunyi tanpa pilihan, kiri-bawah di 16:9, di dalam rail pada 1624x720,
tombol UPGRADE tetap di dalam layar).

## Koreksi hint bar + teks kontrol — 10 September 2026

Audit lanjutan seksi panel kanan menemukan teks kontrol Godot yang masih
mengklaim perilaku pra-FASE 18: hint bar bawah HUD memuat daftar statis
salah ("B toko / D difficulty / SPASI beli hero"), padahal B/D kini hotkey
perintah taktis (FASE 18), toko = H, dan SPASI hanya melewati intro.
Semuanya diperbaiki tanpa menyentuh kode pygame:

| Lokasi | Teks lama (salah) | Perbaikan (port pygame) |
|---|---|---|
| HUD hint bar | 8 item statis campur konteks — "B/toko", "D/difficulty", "SPASI/beli hero", dan "ENTER/lanjut" tampil bahkan saat masih bermain | Port `InputManager.get_hints` (`_core.py:10102`) per konteks, bahasa Indonesia: game = klik/pilih · QWER/skill · H/toko · klik kanan/tutup · P/jeda; victory = ENTER/lanjut · R/ulangi · ESC/menu; defeat = R/ulangi · ESC/menu; shop = klik/beli · H/tutup. Konteks berpindah lewat sinyal `game_over` / `level_started` / `shop_changed`, prioritas persis `_draw_input_hints` (`_core.py:2721-2731`): victory > defeat > shop > game |
| `HUD._layout_hud` | `HintLabel` ikut daftar geser tengah-arena | Dikeluarkan dari daftar: host-nya left-anchored di HUD.tscn (offset 18..1262, bukan anchor 0.5) sehingga shift tengah justru menggesernya keluar pusat arena di layar lebar |
| MainMenu HOW_TO_PLAY + SkillBar | "B → HERO" | "H → HERO" (judul seksi HOW_TO_PLAY "TOKO (B)" ikut menjadi "TOKO (H)") |
| ShopPanel footer | "… · D ganti difficulty" | Klaim dihapus — D = hotkey taktis ATTACK TOP DEALER sejak FASE 18 (paritas HOW TO PLAY pygame: "D = ATTACK TOP DEALER (all)") |

**Perfeksionis — kebijakan tampil (masih 10 September):** render pygame asli
membuktikan hint bar HANYA digambar di mode controller legacy desktop
(`_draw_input_hints` `_core.py:2709-2714`; build Android `main.py:250` tak
memasang `controller_mgr`, dan pemain keyboard tidak pernah melihatnya).
Karena Godot belum punya lapisan input gamepad, paritas yang jujur adalah
TIDAK PERNAH menampilkan bar — `HintLabel` kini disembunyikan (node tetap
ada untuk fixture struktur), mesin konteks `get_hints` tetap terpasang dan
diaktifkan kembali begitu gamepad diport. Dikunci asersi baru di
`UiHudParityTest` (`hint bar disembunyikan`).

**Ditambahkan 10 September 2026 — dekorasi banner wave:** panel 400×80
WaveAnnouncer pygame (`_render.py:1022-1103`) kini diport utuh sebagai
`WavePlate.gd` (gradasi latar alpha lengkung 0.3, border emas 3px, garis
dalam terang, diagonal tiap 10px, corner ticks 12/2/inset-5) + bayangan teks
(8,8,14) offset +2/+2, urutan gambar plate → shadow → teks, semuanya ikut
kurva slide/alpha tween yang terkunci fixture. Warna teks banner memakai
puncak gradien pygame (255,242,175); gradien per-glyph sendiri tetap milik
bucket piksel (kebijakan `gradasi-pendekatan` yang sama dengan ScreenTitle).

**Validasi (hint bar + settings + banner):** `gdparse` + `tscn_lint` +
`check_refs` lulus lokal — replay headless diverifikasi CI, binary Godot tak
tersedia di sandbox.

## Koreksi permukaan UI — 9 September 2026 (FASE 22)

Koreksi laporan visual/lapangan (bukan perilaku match yang sudah terkunci):

| Bagian | Masalah | Perbaikan |
|---|---|---|
| Layar menu | Menu hanya menutupi sebagian layar sehingga arena + HUD (bar nexus fallback `Lv0 · 0/1 HP`, footer hotkey) kelihatan di sampingnya — "tampilan berantakan" | `MainMenu` sekarang LAYAR PENUH eksplisit (anchors + offsets, bukan `set_anchors_preset` saja), backdrop **opak** (alpha 1.0) untuk semua state non-PAUSE, dan `menu_coverage_changed` membuat `Main` MENYEMBUNYIKAN `ArenaMap`/`Containers`/`FX`/slot layer/HUD selama menu non-PAUSE — arena tak mungkin lagi terlihat di belakang/sebelah menu. PAUSE = arena BEKU tetap kelihatan di belakang backdrop dim (0.62) — paritas pygame pause (frame terakhir + overlay). Sinkronisasi awal dipanggil `Main._ready` karena emit pertama `MainMenu._ready` mendahului koneksi. |
| Bangunan toko di map | Gedung ITEM FORGE/HERO SHOP (gambar bake) tidak bisa diklik — toko hanya via H | `Main._on_click` prioritas #1 (paritas `_handle_left_click` item 1 `_core.py:7814-7826`): `ArenaMap.get_clicked_shop` (radius 60 = `shop_size` `_render.py:109`) — Radiant → tab ITEM, Dire → tab HERO, SFX `ui_click` 0.5. Beda disengaja yang tetap: pygame membuka item shop full-screen (`item_shop_open`), Godot memakai tab ITEM panel terpadu (sudah tercatat sebagai deviasi desain). |
| Bar nexus HUD | Fallback `DIRE NEXUS Lv0 · 0/1 HP` menyesatkan saat nexus belum ada (menu/sebelum match) | Bar DISEMBUYIKAN sampai nexus eksis (`_refresh_bars`); nilai label kini dibaca dari node nexus (Lv1+ saat match mulai). |
| PENGATURAN | Hanya 2 slider + hapus save — "tidak lengkap" | Dua kolom paritas struktur `_draw_settings` pygame: AUDIO (Master/SFX/BGM — master kini `var` + settings key `master` di `AudioManager.apply_settings`), GAMEPLAY (info difficulty [dipilih di PILIH LEVEL], **Screen Shake** [hidup: `Camera2D` kini masuk grup `camera` yang dibaca `Boss._shake` + guard `GameManager.screen_shake_enabled`], **Damage Numbers** [live ke `world_popups`]), PROGRESI (hapus slot aktif + dialog), catatan jujur CLOUD SAVE belum di-port. Opsi pygame tanpa padanan kerja (voice, game speed, language, FPS limit) sengaja tidak dipalsukan — game speed/FPS limit menyusul di FASE 25 dan **language di FASE 30** (`Localization.gd` + `MainMenu._language_row`), menyisakan voice playback. |
| Hero shop / level select "kosong" | Katalog gagal muat tidak terlihat (layar hening) | Guard eksplisit: jika `HeroDB.heroes`/`BossDB.levels` kosong, layar menampilkan pesan merah + perintah `python tools/convert_to_godot.py`, bukan "tidak ada hero" generik. |
| Dialog hapus slot | ESC membatalkan dialog tapi kartu slot tidak disegarkan | (dijaga) flag `_slot_delete_confirm` di-reset sebelum dialog disembunyikan. |
| Screen shake | `Boss._shake` memanggil `call_group("camera", ...)` padahal Camera2D tidak terdaftar di grup `camera` → semua guncangan pygame (enrage, frenzy, ability) no-op | `Main._ready` mendaftarkan `Camera2D` ke grup `camera`. |

**Validasi:** `gdparse` seluruh `.gd` + `tscn_lint` 29 scene + `check_refs` +
`particles_lint` lulus. Regenerasi fixture TIDAK diperlukan (kode pygame tidak
disentuh; perilaku match tidak diubah). Replay scene paritas lama dijalankan CI
(`godot-check.yml`) — layout UI baru di luar fixture headless (piksel tetap
milik bucket piksel).

## Koreksi alur pertandingan — 8 September 2026

| Bagian | Godot sebelumnya | Perilaku sekarang / acuan Pygame |
|---|---|---|
| Roster awal | 6 hero gratis per tim | Kedua tim mulai kosong. Pemain dan AI membeli hero dengan gold (`Game.reset`, `AIPlayer.__init__`). |
| Unlock awal | Keenam starter langsung terbuka | Save baru mendapat Kaizen. Unlock pada save lama **tidak dicabut**. Unlock permanen hanya izin membeli, bukan summon gratis. |
| Pembelian hero | API menerima hero terkunci, duplikat, dan roster tanpa batas | Catalog valid, unlocked, gold cukup, satu hero per tipe, maksimal 5 hero **termasuk yang mati**. Spawn pemain di depan toko Radiant (`Game.try_buy_hero`). |
| Kematian hero | Node dihapus; satu tim habis memulai ulang seluruh arena setelah 3 detik | Hero yang sama respawn setelah 10 detik di base sendiri. Level, item biasa, dan statistik tetap. Holy Rapier rontok. Debuff dibersihkan; cooldown W/E/R dan state kit (mis. charge Sylara) **membeku** lalu berjalan lagi setelah respawn, dan respawn menyetel HANYA Q siap — persis `Hero.respawn` (`Game.update`, `Hero.respawn`). |
| Waktu respawn | Callback timer bisa bertahan melewati restart/pause | Timer milik match, membeku ketika pause/intro, dibuang saat restart/menu. |
| Wave pertama | Langsung, termasuk selama intro | Persiapan 5 detik **setelah** intro dilewati; mulai pada wave 0 (`Game.reset`). |
| Wave berikutnya | Otomatis setiap 25 detik walau wave sebelumnya hidup | Interval 25 detik adalah minimum. Antrean kedua tim dan semua minion hidup harus sudah habis (`Game.update_waves`). |
| Spawn minion | Satu komposisi dibagi ke tiga lane, spawn serentak, cap 24/tim | Satu komposisi penuh **per lane**, urutan top → mid → bot, interval 20 frame/60 FPS per tim. Tidak memotong wave elite yang berisi 33 minion/tim. |
| Komposisi wave | Tabel diindeks nomor wave | Tabel diindeks **level nexus tim sendiri**, lalu tambahan elite pada wave 4/7/10/13 (`Game._get_wave_composition`). |
| Stat minion | Skala dari nexus terkuat kedua tim + bonus 8%/wave | HP/damage, kecepatan, cooldown, gold reward, regen dan prioritas target mengikuti level nexus sendiri. Hard scaling diterapkan hanya pada minion merah ketika spawn (`Minion.__init__`, `Game.update_waves`). |
| Jalur minion | Lane hanya label; berjalan diagonal ke base lawan | Mulai dari ujung lane yang benar dan mengikuti waypoint maju/mundur sesuai tim (`Minion._move_forward`). |
| Ekonomi AI | Gold awal dan income sama dengan pemain | Mulai dengan `STARTING_GOLD` (350), income `GOLD_PER_SECOND + wave_number`. AI membangun/draft memakai saldo ini (`AIPlayer.__init__`, `Game.update`). |
| Nexus AI | Tidak ada eskalasi wave otomatis | Naik ke level 2/3/4/5 pada wave 4/7/10/13, sebelum menghitung komposisi baru (`Game._auto_scale_ai_castle`). |
| Mini boss | Wave tetap dari JSON | Wave unik diacak tiap match: easy 20–40, normal/hard 11–30, urutan dan tipe boss tetap (`Game._roll_mini_boss_schedule`). |
| Data boss | BossDB hanya hp/damage/speed/range/cooldown/radius | `bosses.json` diekspor converter dari `boss_data.py` + `hero_archetypes`: armor/MR tematik, ability/ability2 (cooldown, damage, range, heal), jarak kiting, dan bendera `uses_smart_ai` hasil AST `Boss.update` — 216 baris cocok dengan oracle Pygame (`BossCoreParityTest`). Modul `hero_archetypes.py` itu sendiri diport utuh 1:1 ke `HeroArchetypes.gd`: const `ARCHETYPES` (222 hero: dmg_type/playstyle/tier/power) + `BOSS_RESISTANCES` (216 boss), `get_archetype` (termasuk override manual `dmg_type` ala `boss_data['hero_unlock']` dan entri default `derived`), `school_of`, `physical_mitigation`, `_resist_from_profile` (pembulatan banker ala `round()` Python + clamp `ARMOR_MAX`/`MR_MAX`), dan `get_boss_resistances` (fallback profil balanced per kelas untuk boss yang belum terdaftar). `Boss.gd` memakai fungsi itu sebagai default sebelum override + clamp persis `base_boss.py:447-457`, dan `HeroDB.get_balanced_stats` mengambil `dmg_school` dari modul yang sama. Dikunci `HeroArchetypesParityTest` (oracle konstanta py + fixture `boss_core` + sinkron data JSON). **FASE 32 menambah tiga field** (`color_dark` badan generik, `label_top` jangkar HP bar dari AST `BOSS_LABEL_TOP`, `entrance_text` dari tabel `ENTRANCE_TEXT`) plus ekspor tabel MENTAH `boss_pristine.json` dan port pipeline saat-import `boss_data.py` ke `BossData.gd` — lihat [BOSS_OVERLAY_GODOTPP.md](BOSS_OVERLAY_GODOTPP.md). |
| Resilience boss | Tidak ada; hit besar menembus | `damage_reduction` 30% (true) / 20% (mini), anti-burst cap 8% / 12% max HP, tenacity slow/atk_slow (×0.5, cap 0.35) dan resist stun 55% (`Boss.__init__`, `Boss.take_damage`, `Boss.apply_slow/apply_debuff`). |
| Enrage / Frenzy | Tidak ada | True boss enrage di HP ≤50% (×1.25/×1.25/cd ×0.75 min 18), mini frenzy di HP ≤40% (×1.15/×1.20/cd ×0.80 min 20) + callout + shake; nilai dibandingkan dengan hasil `Boss.update()` Pygame sungguhan di fixture. |
| Entrance boss | Langsung bergerak/menyerang | Freeze entrance 3 s (true) / 2 s (mini); cooldown serangan tidak jalan selama entrance. |
| True boss ability2 | Tidak ada | Heal `max_hp × ability2_heal_pct` saat HP < 30% dengan cooldown ability2. |
| Cleave & ability generik | Serangan dasar hanya kena target | Cleave 40% radius 80 ke musuh lain (netral sekolah); boss tanpa smart-AI memakai `_use_ability` (damage/range/cooldown dari data, lock serangan 60 frame, shake) persis `base_boss.py`. |
| Smart-AI boss musuh (79 tipe) | Rantai `elif boss_type` di `Boss.update` pygame tidak diport; semua boss memakai ability generik | `BossKit.gd` dihasilkan `tools/gen_boss_smart_ai.py` dari AST `bosses/base_boss.py`: dispatch 79 boss + 116 helper Q/W/E/R — koefisien, target, timing, dan urutan kondisi persis sumber (summon, dash, transform, dot/debuff area, buff, heal, knockback, combo angka). State kit per instans; jembatan frame↔detik satu tempat di `Boss.gd` (`kit_enemies`/`kit_get_stats`/`kit_skill_hit`/`kit_apply_slow`/`kit_lock_attack`/…). `gen_boss_smart_ai.py --check` di CI menjaga hasil generate tidak drift diam-diam. Boss tanpa smart-AI tetap ability generik. |
| Facing boss | Arah hadap di-update tiap frame walau boss diam di luar jangkauan | `_face()` dipanggil hanya di cabang dalam-jangkauan `update` pygame (kiter yang hold tidak berbalik); facing awal -1 (`Boss.__init__`); kunci arah hadap selama ayunan serangan dasar 6–15 frame (`_attack_lock_timer`). |
| Skill hero (222) | `SkillBook.gd` tabel efek generik per-detik; 6 starter hand-written belum diaudit koefisien/target/timing; SEMUA boss-hero memakai substitusi generik | `HeroSkillKit.gd` di-transpile 1:1 dari `hero_skills/_bundle.py` oleh `tools/gen_hero_skill_kit.py`: dispatch registry 66 resep `_cast_*` + `_generic_cast`/`_fallback_cast` untuk sisanya — koefisien, guard jangkauan (slack 1.15 hanya di acquire), prioritas auto-cast R→E(2+)→W(hp<0.4%)→Q, CDR+spell-vamp, dan urutan timer frame persis `Hero.update`. `SkillBook.gd` jadi facade UI tipis (tanpa state sendiri). Fixture oracle `hero_skills` = 222 hero × 4 skenario (118.293 event) diputar ulang `HeroSkillParityTest`; `gen_hero_skill_kit.py --check` + scope-check dijaga CI. |
| Catch-up stat hero | Buff melee normalisasi hp/damage di `get_balanced_stats` + koreksi starter saja | `HeroDB.catchup_base` mirror `hero_balance.starter_catchup_stats`: MENIMPA stat dasar SEMUA hero dari katalog MENTAH, `k = 1 + 0.32 × (1 − min(1, unlocks/12)) × sisa-hp`; hpK=1+(k−1)·1,25, dmgK=1+(k−1)·0,85; level-1/no-save → ×1,40/×1,272. `get_balanced_stats` tidak lagi mem-buff hp/damage melee (speed/cd tetap dinormalisasi ke px/s dan detik). |
| Kalkulator balance hero (FASE 28) | Godot hanya membaca ANGKA bake `heroes.json` tanpa logika kalibrasinya: rumus catch-up/hitung unlock hidup sebagai mirror terpisah di `HeroDB`/`GameManager`, dan tidak ada yang membuktikan bake bisa dihitung ulang | `hero_balance.py` diport utuh 1:1 ke `HeroBalance.gd` (semua static, satu dependensi `HeroArchetypes`): `metrics`, re-budget (`hero_target`/`stat_multipliers`), paritas sel IPF 18 iterasi + paritas sekolah per kelas boss, jangkar rata-rata pool, fixpoint akhir, `starter_catchup(_stats)`, `boss_unlocks_for_purchases`, `calibrate_boss_resistances`, `apply_to_catalog`. Adaptasi yang dikunci: tuple→Array/kunci `"A|B"`, `round()` banker's + `round(x,n)` koreksi TwoProd (killer double rounding 1.46475/1.32975), `statistics.fmean` via penjumlahan exact gaya `math.fsum` (bit-identik di 157 set pipeline nyata + fuzz 400rb), `median` polos, data mentah boss disuntik (`pristine`/`boss_tables`) supaya murni, dan `__main__.game_instance` menjadi parameter `boss_unlocks`/`level` eksplisit. `HeroDB.starter_catchup_mults`/`catchup_base` + `GameManager.boss_unlocks_for_purchases` kini mendelegasikan ke modul ini (perilaku tak berubah). Dikunci seksi fixture `hero_balance` (katalog mentah replika `_core` yang kesetiaannya di-assert `apply(replika)==inner`, tabel + stat final + `LAST`, grid catch-up 512 mult, kalibrasi 216 baris, baterai numerik, varian resolve/fallback/fix-sel) + `HeroBalanceParityTest`: hitung-ulang Godot == oracle DAN == bake `heroes.json` untuk 216 hero (beda `unlock_cost` inner-vs-wrapper dikunci eksplisit). |
| Logika murni item (FASE 29) | `get_item_class` (badge/tab kelas ITEM FORGE), `SHOP_PAGES`/`SHOP_PAGE_META`/`ITEM_SHOP_ORDER`, popup detail mekanik `_build_item_mechanics`, pesanan forge tertunda (`pending_forge_items`/`deliver_pending_forge_items`), target toko `_resolve_shop_target`, dan `_hero_level_mult` hanya hidup di pygame; sisi Godot hanya membaca `items.json` | `hero_items.py` (bagian logika murni yang belum punya pembaca) diport 1:1 ke `HeroItems.gd` (semua static, data disuntik): `get_item_class` (+ `ITEM_CLASS_INFO`/`_ITEM_CLASS_OVERRIDES`/`_MAP_CATEGORY_TO_CLASS`), `build_shop_pages` (+ `CLASS_ITEM_ORDER`/`ITEMS_PER_PAGE`), `fmt_mech_value`/`build_item_mechanics` (+ label/group/pct/frame keys), `pending_forge_items`/`deliver_pending_forge_items`, `resolve_shop_target`, `hero_level_mult`. Adaptasi yang dikunci: `f"{x:g}"` Python → `_py_g` (eksponen via loop + `String.num` + buang nol — termasuk float "kotor" 0.022×100 → "2.2%"), `str(float)` Python yang mempertahankan ".0" (3.0 → "3.0") → `_py_str` (asal int-vs-float dipulihkan lewat `_FLOAT_MECH_FIELDS` + flag `float` fixture, sebab `JSON.parse_string` Godot mengubah semua angka jadi float), dan `hero.alive` → fallback `not is_dead` (Godot Hero.gd memakai is_dead). `ItemDB` mendelegasikan `item_class`/`item_class_label`/`item_mechanics`/`shop_pages` (badge kelas kartu toko kini tampil di ShopPanel). Dikunci seksi fixture `hero_items` (33 item: kelas, 6 halaman, mekanik id+en, baterai format 116 nilai, 13 target toko, 6 kirim forge, 18 pengali level) + `HeroItemsParityTest`. Catatan: logika `pending_forge_items`/`deliver_pending_forge_items`/`resolve_shop_target` sudah di-port & dikunci, tapi antrian BELI-UNTUK-HERO-MATI belum di-wire ke `GameManager.try_buy_item` (yang kini masih menolak hero mati) + pengiriman saat respawn di `_update_hero_respawns` — celah runtime ini ditutup terpisah setelah shop-target state (strip BUY FOR) di-ShopPanel ikut diport. |
| Sumber unlock catch-up (progresi) | `_catchup_unlocks()` Godot hard-code **0**: GameManager tidak menyimpan daftar hero yang dibeli/di-unlock lintas-save, jadi tiap save memakai bonus starter PENUH (×1,40 HP / ×1,272 dmg) — identik save BARU pygame walau roster pemain sudah penuh | Rantai sumber pygame diport utuh: save `purchased_heroes` (`_system.SaveManager.load`/`get_empty_save`) → `Game.reset` (_core.py:1596-1604, termasuk AUTO-GRANT `kaizen` untuk save kosong) → `__main__.game_instance` → `Hero.__init__` (`hero_balance.boss_unlocks_for_purchases` = `len()` hero BUKAN starter). Di Godot: `SaveManager.data["unlocked_heroes"]` (kunci lama Godot = padanan `purchased_heroes`) → `GameManager.purchased_heroes` (REFERENSI ke array save; diikat `bind_purchased_heroes()` di `start_level`, **dilepas dengan mengganti binding — bukan `clear()`** di `return_to_menu`, paritas `game_instance = None` main.py:587) → `GameManager.catchup_unlocks()` → `Hero._catchup_unlocks()`. Berlaku untuk hero KEDUA tim (pygame membaca daftar yang sama untuk hero AI). Unlock yang masuk di tengah match (boss dikalahkan) langsung terhitung karena array-nya dibagi referensi; hero yang SUDAH berdiri tidak dihitung ulang (sama seperti pygame). Save pemain tidak dimigrasi/dihapus: unlock lama dipakai apa adanya, penulisan hanya saat starter benar-benar baru di-grant. Dikunci fixture `hero_catchup_unlocks` + `HeroCatchupUnlockParityTest`. |
| Kaizen | Rig buatan ulang selalu mengalahkan sprite Pygame | Arena normal memakai bake renderer Pygame. Rig alternatif tetap ada di `KaizenDemo.tscn`, atau opt-in `mystic/rendering/experimental_hero_rigs`. |
| Kontrol demo | D/F1/T/SPACE mengubah match normal | Dinonaktifkan default; hanya aktif dengan `Main.enable_debug_controls`. Pilih difficulty di menu sebelum bermain. |
| Jalur damage basic hero | Pipeline school-aware satu-untuk-semua: physical→armor node, magic→MR, netral→tanpa mitigasi; armor hero = snapshot node; amp setelah mitigasi; block sebelum armor floor 1; blind dibaca dari status TARGET; crit buff tidak pernah aktif; lifesteal/cleave memakai damage post-mitigasi; reflect thornmail bertipe 'normal' | `CombatSystem.apply_damage` kini dispatch per jenis target, mirror `take_damage` pygame masing-masing: HERO = amp `int(round)` → armor ITEM (live dari inventory + aura, dikikis shred, negatif = bonus) utk SEMUA damage non-`fire`, TANPA magic_resist → block SETELAH armor (amount milik defender, aura guard menimpa tanpa roll, floor 0) → Bristleback; MINION = amp → shred bonus (double-dip) → armor−shred/MR; BOSS = amp → shred bonus → reduction−shred×0.06 (cap 0.60)/MR → resilience+cap, blind hanya `normal` bersource; TOWER = armor/MR sekolah; NEXUS = shield `int(x×(1−0.88))` truncation. Kalkulasi penyerang `calc_damage` = `_do_attack` pygame (bonus item → crit buff kit `int(×2)` → rend Soul Rend `int(×1.5)` TANPA roll ke target bertanda → crit item `int(×mult)`; pembulatan `py_round` banker ala Python). Lifesteal float pra-mitigasi (ranged `int()` saat spawn), cleave netral tanpa source, Morgath serang instan 'normal', peluru menara/minion netral, boss ranged 'normal'. Dikunci `HeroBasicAttackParityTest` (29 skenario + probe get_block). |
| Level-select stats + transaksi Hero Shop meta (FASE 20) | Kartu level tidak menampilkan BEST SCORE/BEST TIME/ATTEMPTS/WIN RATE padahal `level_stats` sudah ditulis ke save sejak FASE 13; `format_time` tidak ada. Transaksi Hero Shop meta hidup di `MainMenu.gd` tanpa satu pun oracle: audit menemukan katalog EFEKTIF pygame adalah def `get_all_hero_types` KEDUA (`_core.py:1255`) yang MENIMPA semua `unlock_cost` dengan konstanta flat — starter **0** (FREE), mini/true **4500** — di atas harga rumus def pertama (1200/2200/1.8×) | `SaveManager.format_time` (M:SS, `--:--` untuk 0) mirror `_system.py:1118`; kartu level (`MainMenu._level_card`) kini menampilkan blok stat untuk kartu TERBUKA saja: skor (ribuan koma < 10000, `%.1fK` setelahnya, truncasi `[:8]` bila lebar terukur > ambang 120px = `w//2−20` pygame 280px — konstanta pygame di-pin, metrik font tetap milik Godot), waktu, `xW/y` attempts, win rate `int((wins/attempts)×100)` dengan band warna 3 tingkat (≥75 hijau / ≥50 emas / else oranye — RGB ui_theme pygame disalin sebagai data), "No stats yet" → "Belum ada statistik" (beda bahasa terkunci). Transaksi `_try_unlock_hero` + meta keputusan kartu (`owned/boss_ready/affordable`) dikunci oracle `meta_shop_txn`: katalog closed-world 222 hero (pygame = heroes.json: 6×0 + 216×4500, `unlock_require_boss` = boss sendiri), 10 kasus transaksi (katalog→duplikat→gate boss→saldo 4499/4500/9000, sfx ui_error/ui_buy, sinkron in-memory↔save, persist disk), matriks 5 state save × 4 hero wakil (OWNED / boss-locked / pill FREE-UNLOCK + kind gold-neutral). Dikunci oracle `level_select_stats` (9 kasus kartu draw pygame ASLI + 12 format_time + 13 format skor dengan lebar piksel pygame + 12 win-rate) + replay `LevelSelectStatsParityTest`/`MetaShopTxnParityTest` lewat jalur produksi. |
| Roll RNG guard & item | Roll combat tidak pernah teruji: damage uji bertipe `fire` (netral deterministik) sehingga windrun tidak pernah me-roll dan shadow realm hanya tampak sebagai bhp flat di harness skill | Dikunci fixture `hero_rng_guards` (14 skenario, 47 roll ter-script) + replay `HeroRngGuardParityTest`. Oracle menjalankan `take_damage`/`_do_attack` pygame ASLI dengan `random.random` DI-MONKEYPATCH per situs roll (`_entity.py::take_damage`, `hero_items.py::roll_crit` — pemanggil lain jatuh ke RNG asli, double-run seed beda tetap dijalankan); Godot memutar ulang lewat hook `ParityRng` di `CombatSystem.apply_damage` + `ItemInventory.roll_crit` (tanpa begin() = `randf()` global — perilaku produksi tak berubah) dan membandingkan HP + JUMLAH/nilai/URUTAN roll yang terkonsumsi. Windrun (Sylara W): fisik = `normal`/`projectile` dengan sekolah bukan magic — termasuk netral TANPA source; `0.75` persis TIDAK meleset (strict); sihir/fire tidak me-roll; flag mati tanpa roll. Shadow realm (Zephyr W): kebal total SEMUA damage tanpa roll, dipotong sebelum windrun/wall/veil. Urutan guard shadow → windrun (roll) → wind wall → veil → evasion terkunci lewat jumlah roll per tahap. Crit Dead Edge me-roll di `calc_damage` SEBELUM mitigasi target (crit buff men-diskip roll; ranged: roll crit saat spawn lalu roll block saat mendarat), block Scarlet Bulwark me-roll setelah armor utk semua non-fire (floor 0), miss = SATU roll `max(evasion, blind)`, True Strike tanpa roll, windrun penyerang ikut me-roll pada reflect Bristleback (nested take_damage). |
| Skor match (klaster skor: combo, NEW BEST, kill hero, popup achievement) | Tidak ada sistem combo (`Max Combo` tidak dihitung), save tanpa best per level (badge `NEW BEST!` mustahil), kill hero tidak membayar +150 dan tanpa atribusi killer, popup achievement `NEW HERO UNLOCKED!` tidak ada (hanya baris teks Fase 12) | Klaster skor diport 1:1 + dikunci oracle `match_scoring`/`MatchScoringParityTest` (oracle menjalankan `Game.update` pygame SUNGGUHAN headless — unit betulan mati via `take_damage`, dua run seed beda harus identik): (1) **combo** — mesin state `ComboCounter.gd` frame @60fps (max_timer 120 = 2 dtk, target scale 1.3, color flash 20, expiry `last_combo`) diputar `GameManager._tick_combo` (akumulator 60Hz; membeku saat pause/menu/intro paritas `EffectManager.update`); `max_combo` dibaca **sebelum** `add_kill` (quirk pygame: rantai N kill berurutan → max_combo N−1) dan hanya menyala untuk kill minion RED oleh damage apa pun termasuk netral tanpa sumber; (2) **NEW BEST!** — `SaveManager.get/update_level_stats` (kunci save `level_stats` per level: attempts/playtime/total_kills/max_combo all-time bahkan saat kalah; best_score/best_time/wins hanya saat menang, time 0 diabaikan, sama-rata tidak beri flag) dipanggil `_grant_meta_reward` lalu flag `GameManager.new_best_score/new_best_time` membuntuti baris Final Score/Match Time panel game-over; (3) **kill hero +150** — `GameManager.register_hero_death` membayar FLAT 150 ke tim lawan KORBAN (hero merah mati → gold+skor pemain, hero biru → saldo AI, siapa pun pembunuhnya) + atribusi `killer.kills` hanya untuk hero pembunuh tim lawan (tower/minion/self/netral tidak); kematian minion kini dinilai dari tim korban (`register_minion_death`) sehingga kill netral pun membayar seperti pygame; `_rewarded` direset saat hero hidup lagi — respawn (600 frame) tidak membayar dua kali; (4) **popup achievement** — `AchievementPopup.gd` (antrean, tampil 180 frame, pengganti muncul di frame yang sama, slide 300px ease-out-back, panel 280×60 @(W−300,180), header `A C H I E V E M E N T`) dipicu `GameManager.unlock_achievement` (signal → FX HUD, pola `EffectManager.unlock_achievement`); trigger `NEW HERO UNLOCKED!` + deskripsi `… now FREE in Hero Shop!` dari `_auto_unlock_defeated_boss_heroes` (sudah-own → tanpa popup). Belum teruji/sengaja terbuka: komposit piksel badge combo + popup (font/shadow/ikon/truncation ellipsis judul), notifikasi tier sidepanel pygame (tidak ada sidepanel Godot), ~~popup gold `+nG` kematian minion~~ (data/antrean/posisi kini terkunci FASE 15 — baris reward minion+menara), tampilan BEST SCORE/best time di level-select (data `level_stats` sudah tertulis — ranah menu). Reward gold/skor kematian boss + atribusi/popup SLAYER mini/true kini terkunci FASE 14 (baris berikutnya); reward kematian minion + menara + popup gold `+nG` kini terkunci FASE 15 (baris reward minion+menara). |
| Reward kematian boss (FASE 14) | Boss mati hanya dicatat tipenya dan memainkan cinematic; tidak membayar gold/skor, unlock boss baru tersimpan saat menang, tidak ada SLAYER maupun popup `+nG` | `Boss.take_damage → die(source) → GameManager.register_boss_death` mengikuti blok `Game.update` pygame `_core.py:2113–2163`: bayar **nilai runtime `boss.gold_reward`** ke gold+skor PEMAIN, tanpa memandang killer/tim boss, tanpa meta gold/combo/total_kills; `bosses_defeated_this_run` menghitung setiap instans, `bosses_defeated_this_match` dan `unlocked_bosses` unik berurutan. Boss unlock langsung dipersist dan bertahan saat kalah; hero gratis tetap menunggu menang. Guard per instans mencegah callback/tween/tick ganda. `_process_boss_kill` menambah `killer.kills` hanya hero lawan (hero yang sudah mati tetap valid); hanya hero **blue** menambah counter mini/true dan ID dedup in-match + popup `MINI BOSS SLAYER!` / `TRUE BOSS SLAYER!`, deskripsi dan ikon skull persis pygame. **HERO SLAYER tetap DIHAPUS**. Popup pertama-kali `BOSS/TRUE BOSS: … Defeated!` (owned vs tuntutan menghancurkan castle) tetap sesudah SLAYER. `FloatingTextQueue` + `WorldPopups`: gold `+{amount}G` di `(boss.x,boss.y−10)`, RGB `(255,220,50)`, font 18, velocity `(0,−1.5)`, 50 frame; map SLAYER di `(boss.x,boss.y−40)` via cabang critical (pygame menambah `!` lagi), jitter/drift, FIFO/cap 300 (berbagi dengan `DamageNumber` legacy lewat WeakRef), scale dan expiry frame diport. Ekor frame efek selesai sebelum pause cinematic; Main melepas active boss dan mengonsumsi satu pending mini pada frame kematian. Dikunci `boss_death_rewards` / `BossDeathRewardParityTest`; **piksel** font/shadow/glow/komposit cinematic dan audio SFX belum diuji. |
| Reward kematian minion + menara (FASE 15) | Minion merah mati tanpa popup gold `+nG`; reward menara lewat `award_kill` TIM PEMBUNUH (menara merah dihancurkan sumber netral/tanpa killer malah membayar AI — pygame memakai TIM KORBAN), tanpa guard anti bayar ganda, `red_towers_destroyed` belum diaudit sekali-per-menara | Klaster reward minion+menara mengikuti blok `Game.update` pygame `_core.py:2196–2227` lewat `Minion.die()/Tower.die() → GameManager.register_minion_death/register_tower_death` (menggantikan `award_kill` killer): (1) **minion** — dinilai TIM KORBAN: minion RED oleh damage apa pun (hero biru/merah/mati, tower, minion, nexus, boss, self, netral tanpa sumber) membayar gold+skor pemain + `total_kills` + combo, minion biru membayar AI **tanpa** popup; (2) **popup gold `+nG`** — `add_gold_popup(x, y−10, reward)` hanya minion RED (menara & minion biru tanpa popup — pygame tidak memanggilnya), via `FloatingTextQueue`/`WorldPopups` FASE 14: velocity `(0,−1.5)` decay 0.95, lifetime 50, scale 0.3→1.0 spring, x_drift RNG per situs; (3) **menara** — TIM KORBAN: menara RED hancur oleh apa pun membayar gold+skor pemain (nilai runtime `gold_reward` = 100/150), menara biru membayar AI, `total_kills` tidak naik, `red_towers_destroyed` naik TEPAT SEKALI per menara merah (syarat true boss ≥6); (4) **guard** — flag `reward_processed` per instans = `_rewarded` pygame (die() ulang/pukul mayat/callback ganda tidak membayar dua kali; flag hero dibuka lagi saat respawn); (5) urutan operasi persis pygame: gold → score → popup → total_kills → max_combo **dibaca SEBELUM add_kill** (quirk: rantai N kill berurutan → max_combo N−1). Nilai reward runtime diuji (goblin 8/orc 18/troll 45/dark_rider 65, skala nexus, override, tower outer 100/inner 150). Dikunci `minion_tower_rewards` / `MinionTowerRewardParityTest` (20 skenario oracle `Game.update` dua seed); **piksel** font/shadow popup tetap milik bucket piksel FX. |
| Dispatch kematian terpusat (FASE 16) | Sebagian jalur damage menulis HP ≤0 TANPA memanggil `die()`, jadi reward tidak pernah dibayar: peluru menara (`Tower._spawn_bullet`) dan nexus (`Nexus._shoot`), kit boss, kit skill hero (`Hero.kit_hit`), item on-hit, cleave, reflect Bristleback/Thornmail, dan serangan ranged. Hanya `take_damage()` per node yang memanggil `die()` sendiri, sehingga pemanggil yang menulis `hp`/`apply_damage` langsung melewati pembayaran. Sumber peluru juga belum diputus, sehingga peluru menara bisa memberi kill credit dan memantulkan Bristleback — padahal pygame `Bullet._on_hit` memanggil `take_damage` TANPA `source` (`_entity.py:246–248`) | Semua jalur damage Godot lewat `CombatSystem.apply_damage`, jadi keputusan “unit ini mati” ditaruh DI SINI sebagai satu pintu: `death_dispatch_enabled` (default true) + langkah 10 — sesudah mitigasi/shield/reflect/thornmail/on-hit penyerang, persis pygame yang masih mengeksekusi reflect saat korban “baru mati” — jika `dmg > 0` dan `hp <= 0`, `_dispatch_death` memanggil `die()` unit yang benar menurut jenisnya: Hero/Boss `die(source)` (atribusi kill memakai OBJEK source), Tower `die(from_team, source)`, Minion/Nexus `die(from_team)`. Reward/popup/counter tetap lewat `register_*` FASE 13–15 dan tidak membayar dua kali (guard `reward_processed` + guard `is_dead` di tiap `die()`); `Minion.die()` dijadikan idempoten seperti Tower/Hero/Boss. **Source diputus (null)** di peluru menara, peluru nexus, dan serangan minion — paritas `Bullet._on_hit` (`_entity.py:246–248`) dan `Minion.update` (`_entity.py:5580–5581`): peluru/pukulan minion tidak pernah memberi kill credit, reflect Bristleback/Thornmail, maupun blind (semua syarat `source is not None`). `Hero.kit_hit` meneruskan `src` dengan `trigger_on_hit=false`: damage SKILL tetap dispatch kematian + atribusi kill/reflect, tetapi tidak memicu jaket on-hit serangan dasar — persis pygame yang memanggil `take_damage(source=hero, school=…)` tanpa `on_basic_attack_hit`. Dikunci `death_dispatch` / `DeathDispatchParityTest` (21 skenario **jalur serangan nyata**: peluru normal/cannon/ice, melee, proyektil ranged, minion, skill/kit, + guard tanpa kematian dan mayat dipukul ulang). Snapshot per unit HANYA `dead/hp/rewarded/team` — identitas pembunuh sengaja tidak direkam karena `Tower.die(killer_team, _killer)` MEMBUANG killer; atribusi dibaca dari hasil akhirnya (`hero.kills`). **Piksel** damage number/ledakan cannon dan **audio** (menara hancur, minion mati, hentakan proyektil) BELUM TERUJI. |
| Perintah taktis (FASE 17) | `tactical_commands.py` (1051 baris, 28 fungsi) belum ada padanannya di Godot: tidak ada GATHER/PROTECT/ATTACK, tidak ada mode HOLD, tidak ada auto-protect, dan `Hero` tanpa `follow_target` (klik musuh hanya move-to + aggro) | `TacticalCommands.gd` (anak `Main`, dibuat di `_ready` seperti `_ai`, self-managed 60 Hz) mem-port seluruh manager 1:1 — 5 issuer + HOLD + push gather + 4 helper target + auto-protect + warna/status — membaca state live produksi (`GameManager`: state/wave/selected/owned_heroes/nexus; grup towers/minions; `Main.active_boss`). `Hero.move_to` + `follow_target` (validasi + state follow di `_physics_process` persis prioritas pygame destination → follow → serang) dan nama target produksi (`target_name`: menara = nama tipe dasar tanpa `Lv`, castle = `Castle`, sisanya `display_name`). Roll 20% auto-boss lewat `ParityRng` (satu-satunya situs RNG modul). Dikunci `tactical_commands` / `TacticalCommandsParityTest` (37 skenario, 112 langkah: gate cooldown/state, TAP-vs-HOLD 20f/ekor-30, push gather, seleksi threat/nearest/dealer, decay timer, auto castle/tower/boss+roll, status/warna — dua seed identik). Jalur mati ikut dikunci: push one-shot tidak pernah picu (visual 150f < timer 300), push hanya via HOLD ≥240f. Overlay world (lingkaran gather-point + garis hero) kini digambar produksi oleh `TacticalCommands.gd` (Node2D), sedangkan feedback top-banner dibaca `TacticalBar.gd` dari state manajer — tanpa state taktik kedua. **Raster piksel** dan **audio** ui_click/hero_skill BELUM TERUJI; pemicu UI-nya (tombol panel + hotkey G/F/T/C/B/D) diikat **FASE 18** (baris berikutnya). |
| Pemicu UI perintah taktis (FASE 18) | Manajer taktis FASE 17 callable tapi TANPA pemicu: hotkey G/F/T/C/B/D tidak melakukan apa pun (B malah toggle toko — "ekstensi Godot" FASE 12 yang menyimpang dari oracle pygame), tidak ada panel perintah, KEYUP tidak dirutekan, hold "nyangkut" saat pause | Dua permukaan pemicu diikat ke `TacticalCommands.gd` yang sama (tanpa logika ganda): (1) **HOTKEY** — `Main._on_key` blok taktis (paritas `InputHandler.handle_key` `_core.py:8343-8396`): G/F = gather di posisi mouse bila kursor di dalam layar (`follow_mouse=True`), T = protect_tower dengan `selected_tower` BIRU bila ada, C/B/D polos, digate `state == "playing"`, dikonsumsi SEBELUM skill QWER; `Main._on_key_release` (paritas `handle_key_up`: TANPA gate state, peta G/F→gather) dirutekan dari `_unhandled_input` untuk event `pressed=false`; B dihapus dari action `toggle_shop` (H satu-satunya, paritas oracle `ui_hud.hotkeys.b` = hold attack_boss). (2) **PANEL** — `TacticalBar.gd` (HUD, dibangun dari kode pola SkillBar): 5 tombol GATHER [G]/PROTECT TOWER [T]/PROTECT CASTLE [C]/ATTACK BOSS [B]/ATTACK DMG DEALER [D] dengan visibilitas = syarat `_gambar_tactical` pygame (state playing; hero hidup >0/≥1; boss aktif; hero merah hidup — hidden saat tak memenuhi, bukan abu-abu), tekan = `button_down` → `Main._tactical_panel_press` (paritas `apply_hud_action`: gather TANPA posisi mouse ≠ hotkey, protect_tower pakai selected_tower), lepas dirutekan per-sentuhan (`button_up` + `TacticalBar._input` klik-kiri lepas — paritas `held_tac` claimed-touch main.py: release tetap sampai walau kursor sudah pindah), gate popup (paritas `ada_popup_game`: hero terpilih hidup / popup tower-nexus-slot menutupi tombol → tekan tidak tembus). **PAUSE / aplikasi ke latar** = `Main._tactical_release_all()` (paritas `main.py:479-486` `hold_end()` tanpa nama + `held_tac.clear()`; release belakangan diam total) dipanggil `_toggle_pause` + `NOTIFICATION_APPLICATION_PAUSED`. Dikunci `tactical_input` / `TacticalInputParityTest` (17 skenario, 73 langkah, dua seed identik): oracle menjalankan jalur INPUT pygame ASLI (`Game.handle_key`/`handle_key_up`, `SidePanel._gambar_tactical`+`hit_test` dengan rect panel dipaksa, `apply_hud_action`, cabang release/pause main.py), Godot mereplay lewat `Main._unhandled_input` + tombol HUD produksi — jejak `hold_start`/`hold_end` (nama/args/follow_mouse/hasil) direkam hook `hold_trace` produksi + visibilitas tombol + snapshot closed-world manajer. Audit terkunci: KEYUP tanpa gate state (victory: KEYDOWN diam, KEYUP tetap `hold_end`), release nama-salah = no-op (hold B tetap saat KEYUP G), pergantian perintah di tengah cooldown mengganti `held_command` walau terbit gagal (ret False, hold "dipersenjatai"), panel gather mengabaikan mouse, pause memotong timer ke 30. **Piksel** panel (chip HOLD, warna/font sidepanel) dan **audio** BELUM TERUJI; sentuh multi-jari dua tombol panel serentak tidak diuji (manajer memang satu hold). |
| UI/HUD in-match (toko/panel/banner/klik/hotkey) | Panel/label/tombol dibangun manual tanpa oracle: income memakai `"%.1f"` engine yang tak terverifikasi, angka cooldown `ceil(detiks)` (60f tampil "1"), gate equip melee `< 110` + magic via `dmg_school` (46 hero role-magic salah), klik tanah kosong = deselect (bukan perintah gerak), tanpa klik kanan, tanpa tombol N, tanpa catatan skor/kill/timer/unlock match, pause tanpa panel, game-over tanpa stat | Seksi fixture `ui_hud` menjalankan draw pygame ASLI headless (82 skenario draw, 31 kasus klik, 28 hotkey, 222 hero predikat, kurva banner 121 titik, baterai touch-rect) dan diputar ulang `UiHudParityTest`. Kanon tunggal `HudLayout.gd`: `format_gold_rate` bit-eksak IEEE-754 (terbukti identik Python: baterai oracle + fuzz 200.000 nilai, 0 beda — `GameManager`/`HUD` delegasi), ribuan/match-time/mode/cooldown (`frames//60+1`), easing banner (slide-in 0.4 BACK OUT → tahan 1.0 → slide-out 0.6 BACK IN + subtitle letterspaced), nama castle (Lv6+ CITADEL), touch-rect 48px (center integer pygame), dan semesta TERTUTUP `ui_key` tombol toko yang diaudit tiap layar. Perilaku yang disamakan: panel hero (`Lv.n`, `hp/max`, `UPGRADE HERO (300G)`/`M A X   L E V E L`, `AUTO-CAST ON` no-op, `ITEM FORGE  (n/6)` → tab item, chip slot → forge, X = deselect), toko (suffix `MAX`/`DIMILIKI`, alasan disabled `MELEE ONLY`/`MAGIC ONLY`/`POOR`/`FULL`/`OWNED` di `ui_data`+tooltip, tanpa tombol jual di Lv1 + fallback +50G via handler, tutup seusai beli hero/bangun menara), gate equip (`range > 80` tolak melee_only; magic via `ItemDB.is_magic_hero` berbasis ROLE), prioritas klik (slot → nexus → hero biru → perintah → menara biru → deselect; tanah kosong + hero hidup = MOVE tetap dipilih; klik kanan = tutup + MOVE), hotkey H (toggle toko, paritas) + B (kini paritas oracle: hotkey taktis attack_boss — FASE 18; "B = toko" ekstensi Godot lama dihapus) + N (victory → next; defeat/last diam) + R/ESC, pause (panel 400×400 @(440,160), 4 tombol 300×48 seurutan, mode line), game-over (`VICTORY! LV.n`/`DEFEAT LV.n`, 5 baris stat termasuk `Max Combo` + penanda `NEW BEST!` — dikunci `match_scoring`/`MatchScoringParityTest`, `NEW LEVEL UNLOCKED!`, `NEW HERO: …`, tombol next hanya victory+ada-lanjut). Beda disengaja yang dikunci eksplisit: UI Godot berbahasa Indonesia, toko satu-scroll tanpa halaman (himpunan 33 id direplay), klik musuh = move-to + aggro otomatis (klik belum memakai `follow_target` FASE 17), baris NEW HERO ditampilkan (pygame menghitung tapi tidak me-render), klik-kanan di atas panel tertelan. Belum teruji/sengaja terbuka: piksel (lebar chip metrik-font, gradien/shadow/dekorasi banner, ikon, kartu item, komposit badge combo + popup achievement), popup unlock geser (350×230), notifikasi tier combo sidepanel pygame, ~~popup gold `+nG` kill minion~~ (terkunci FASE 15 — baris reward minion+menara), ~~bangunan toko di map~~ (DITUTUP FASE 22 — klik gedung Radiant/Dire membuka tab ITEM/HERO, lihat seksi koreksi 2026-09-09), sistem taktis TERKUNCI di baris perintah taktis + `tactical_commands`/`TacticalCommandsParityTest` (state perintah/hold/auto) DAN `tactical_input`/`TacticalInputParityTest` (pemicu UI tombol panel + hotkey G/F/T/C/B/D — FASE 18), kontrol sentuh di layar, dan teks intro level (perilaku/skip-nya milik `CinematicTest`) — combo/`Max Combo`, badge `NEW BEST!`, skor kill-hero +150 + atribusi killer, dan popup achievement `NEW HERO UNLOCKED!` kini TERKUNCI di baris klaster skor + `match_scoring`/`MatchScoringParityTest`. |

| **Multi-slot save + migrasi legacy (FASE 21)** | Satu berkas `user://mystic_save.json`; tanpa konsep slot, tanpa `get_slot_info`/`delete_slot`/`format_playtime`/`format_last_played`, dan layar `SLOT_SELECT` pygame dilewati | `NUM_SLOTS = 3` + `slot_1.json`..`slot_3.json`, slot aktif (`set_current_slot`; nomor di luar 1..3 diabaikan), metadata `slot_created`/`slot_last_played`/`slot_playtime_seconds`, `migrate_legacy_save()` (jalan hanya kalau berkas legacy ada **dan** slot 1 kosong; legacy di-rename ke backup, TIDAK dihapus; berkas rusak → gagal tanpa efek; idempoten), `save`/`load_slot` (backfill `setdefault` persis `SaveManager.load`), `get_empty_save`, `delete_slot`, `get_slot_info`/`get_all_slot_info` (slot korup → `null`), `format_playtime`/`format_last_played` (UTC) — dikunci oracle `save_slots` + replay `SaveSlotParityTest`. Layar `SLOT_SELECT` Godot (`MainMenu._slot_card`: level tertinggi + nama level, gold ber-grouping, jumlah hero/boss, string terakhir dimainkan, tombol LANJUTKAN/MULAI BARU/HAPUS SAVE + dialog konfirmasi) dipakai produksi; MULAI GAME kini lewat layar slot (paritas `btn_id == "play"`), LANJUTKAN tetap mem-bypass. Tombol HAPUS SAVE di pengaturan menghapus slot aktif (paritas `reset_save`). `SAVE_PATH` menjadi **var** yang mengikuti slot aktif (10 harness lama membacanya untuk snapshot/restore). **Cloud save tidak diport** (luar scope, tercatat terbuka di bawah). |

## Belum setara — jangan ditandai selesai

- **Performa (`_system.py:29-185` + `:189-387`, FASE 25):** grid spasial,
  culling draw-side, dan panel FPS sudah diport + dikunci fixture. Yang belum:
  (1) **piksel** panel FPS — headless Godot tidak bisa screenshot, jadi yang
  direplay adalah daftar perintah gambar (`build_ops`) + konstanta letak/warna,
  bukan raster-nya; posisi yang bergantung lebar teks ikut metrik font Godot;
  (2) `AdaptiveQuality` (`_system.py:400-448`) sengaja TIDAK diport karena
  dead code di pygame — kalau nanti diaktifkan di sisi pygame, fixture harus
  diregenerasi dan port-nya ditinjau ulang; (3) `mobile/perf.py`
  `auto_detect_quality` (preset Android) belum punya padanan Godot — preset
  kualitas Godot hanya membaca `settings.quality` untuk anggaran popup
  (`GameManager`), belum untuk jumlah partikel/kabut seperti pygame Android;
  (4) **tie-break target menara**: pygame `Tower._find_target` memakai
  `dist <= best_dist` (musuh TERAKHIR pada jarak sama menang,
  `_entity.py:808-860`) sementara `CombatSystem.nearest_enemy` memakai `<`
  (yang pertama). Selisih ini ada SEBELUM FASE 25 dan tidak disentuh (jalur
  menara tidak dialihkan ke grid), tapi nyata dan belum diputuskan;
  (5) tombol FPS 4-mode `mobile/debug.py` (entry `main.py`) belum diport —
  yang diport adalah `_system.FPSCounter` jalur desktop legacy.

- ~~**Reward kematian boss belum membayar gold/skor, tracking unlock langsung,
  popup SLAYER mini/true, dan data/antrean `+nG` belum diport.**~~
  **Ditutup FASE 14** oleh oracle `boss_death_rewards` + replay seluruh
  daftar headless `BossDeathRewardParityTest` (lihat tabel dan seksi tes).
  Yang **murni piksel tetap BELUM teruji**: raster/font, anti-alias,
  shadow/glow, ikon skull/ellipsis judul, penumpukan popup terhadap
  flash/dissolve/perayaan boss dan camera shake. SFX dipanggil tetapi
  bunyi/mix tidak diverifikasi headless. Ini bukan sertifikasi visual
  atau audio seluruh efek kematian boss.

- ~~**Popup gold `+nG` kematian minion belum diport, reward menara masih
  membayar tim pembunuh (bukan tim korban), dan kematian minion/menara
  tanpa guard anti bayar ganda.**~~
  **Ditutup FASE 15** oleh oracle `minion_tower_rewards` + replay seluruh
  daftar headless `MinionTowerRewardParityTest` (lihat baris tabel reward
  minion+menara dan seksi tes). Yang TETAP TERBUKA di jalur ini,
  eksplisit: (1) **piksel** popup gold (raster font, shadow, anti-alias,
  penumpukan vs FX lain) — data/antrean/gerak/scale/lifetime sudah
  terkunci; (2) ~~**dispatch kematian pre-existing**~~ — **DITUTUP
  FASE 16**: `CombatSystem.apply_damage` langkah 10 `_dispatch_death`
  kini memanggil `die()` untuk SEMUA jalur damage lethal (peluru
  menara/nexus, kit boss/hero, item on-hit, cleave, reflect, ranged),
  dikunci oracle `death_dispatch` + `DeathDispatchParityTest`;
  (3) **jual menara** tidak menghasilkan refund
  reward di KEDUA engine (paritas, bukan gap); (4) regen/aura nexus
  menghidupkan unit tanpa reset flag `reward_processed` (pariter dengan
  pygame `_rewarded` yang juga tidak direset oleh mekanik itu).

- **UI/HUD/toko/menu:** perilaku in-match kini diuji oracle (`ui_hud` +
  `UiHudParityTest` — lihat tabel di atas: format, banner, biaya, gate,
  klik, hotkey, pause, game-over, audit `ui_key`). Klaster SKOR match
  (combo/`Max Combo`, badge `NEW BEST!`, kill hero +150 + atribusi
  killer, popup achievement `NEW HERO UNLOCKED!`) juga sudah terkunci
  (`match_scoring`/`MatchScoringParityTest` — lihat baris tabel klaster
  skor). Yang TETAP TERBUKA, eksplisit: (1) **piksel** — lebar chip
  (metrik font), gradien/shadow/dekorasi banner, ikon skill, kartu item,
  komposit visual badge combo + popup achievement (termasuk truncation
  ellipsis judul yang bergantung metrik font), dan seluruh komposit
  lain belum lolos perbandingan screenshot; (2) **popup unlock geser**
  (geometri 350×230 tercatat di fixture tapi Godot hanya menampilkan
  baris teks) — popup achievement SUDAH diport (`AchievementPopup.gd`);
  (3) ~~**bangunan toko di map**~~ (**DITUTUP FASE 22**: klik gedung
  Radiant/Dire membuka tab ITEM/HERO — `ArenaMap.get_clicked_shop` radius 60
  paritas `_render.py:246-260`; deviasi desain yang tersisa: pygame item
  shop full-screen vs tab panel Godot); (4) ~~**pemicu UI taktis**~~ (**DITUTUP
  FASE 18**: sistem `tactical_commands.py` ditutup FASE 17 —
  `TacticalCommands.gd` + `Hero.follow_target` + oracle
  `tactical_commands` + replay `TacticalCommandsParityTest`; pemicunya
  kini ikut terikat — hotkey hold G/F/T/C/B/D di
  `Main._on_key`/`_on_key_release` + panel `TacticalBar.gd` di HUD,
  dikunci oracle `tactical_input` + replay `TacticalInputParityTest`;
  B kini hotkey attack_boss, bukan toggle toko — paritas oracle pygame)
  + notifikasi tier combo sidepanel pygame
  (`beri_tahu_global` — Godot tanpa sidepanel); (5) ~~**kontrol sentuh
  di layar** (data tombol+visibilitas diport di `HudLayout`, UI-nya
  belum ada)~~ (**DITUTUP FASE 23**: `TouchHUD` dipasang di HUD paling
  atas + `Main._apply_touch_action` port `apply_hud_action`, dikunci
  `TouchHudParityTest` — tersisa long-press jeda, safe-area poni, dan
  `DebugOverlay` penuh); (6) **teks intro level** (sudah diport visual, replay
  teks belum ada — `CinematicTest` mengunci perilaku/skip);
  (7) **transaksi Hero Shop meta** di `MainMenu.gd` belum punya oracle
  sendiri; (8) beda kecil yang didokumentasikan di kode: hero mati +
  klik kosong menutup juga tokonya di Godot (pygame membiarkan
  `shop_open`), klik kanan di atas panel toko tertelan (pygame menutup
  popup dari mana saja), baris stat + `MUNDUR` di panel hero adalah
  tambahan Godot.
- **Visual unit:** bake menyamakan sumber pose hero/boss, bukan seluruh komposit
  live FX. Overlay live dari `_entity.py` kini diport: armor crest shield
  (Tower/Nexus), bintang level di papan nama hero, slash 7-titik + death dust
  minion, torch L4+/aura L6 + `SHIELD n%` nexus, peluru HD archer, dan kind
  SkillProjectile zephyr/morgath/ancient_apparition. Badan minion/tower/nexus
  tetap bake+prosedural. Kuantisasi pose, lighting, cuaca dan efek skill juga
  belum lolos perbandingan screenshot menyeluruh. Perilaku non-piksel
  (`credit_hero_damage` int, archer L5=2/L6=3, kit_hit tanpa double-count,
  tanpa hit-stop di `try_attack`) dikunci `EntityPyParityTest`.
- **Skill hero:** koefisien/target/timing kini 1:1 dengan `hero_skills/_bundle.py`
  dan dikunci `HeroSkillParityTest` (222 hero × 4 skenario). Guard
  **windrun** (roll RNG 75% evade fisik) dan **shadow realm** (kebal total)
  kini TERUJI PENUH di harness terpisah `hero_rng_guards`/`HeroRngGuardParityTest`
  (oracle dengan roll ter-script, urutan guard + jumlah konsumsi roll
  dibandingkan — dulu keduanya mirror manual `_entity.py:4537-4585` yang
  hanya tampak sebagai bhp flat karena damage uji bertipe `fire`).
  Yang masih terbuka: proyektil skill (`_spawn_skill_projectile`) tetap
  VISUAL-only di kedua sisi (damage instan), jadi 520 px/s travel-time
  tidak memengaruhi state — dan tidak diuji. `_try_auto_cast` Godot
  memakai ulang list `_kit_lists()` (bukan list argumen yang dilempar
  Game.update) — sama isinya saat run normal.
`Hero.auto_cast_enabled` default True seperti pygame v27 (auto-cast juga
untuk hero terpilih; gate False hanya dipakai harness replay).
  `_catchup_unlocks()` kini membaca daftar unlock lintas-save
  (`SaveManager.unlocked_heroes` -> `GameManager.purchased_heroes`) dan
  dikunci `HeroCatchupUnlockParityTest` — lihat tabel di atas.
- **Visual skill smart-AI boss:** blok `heroes/<boss>_fx` pygame
  (notify_skill_cast/impact: flash, shockwave, serpihan, beam per boss)
  diganti aproksimasi Godot — callout nama skill + cincin ekspansi
  `KitShockRing.gd` pada posisi/radius panggilan yang sama. **Perilaku**
  (koefisien, target, timing, frame) diverifikasi `BossSmartAIParityTest`;
  tampilan visualnya belum diaudit piksel-per-piksel dan dibiarkan terbuka.
  ~~Aura ability/enrage juga belum (test `test_boss_true_aura_parity` baru
  mencakup aura true boss)~~ — **DITUTUP FASE 32**: seluruh lapisan overlay
  `Boss.draw()` (entrance, aura ability/enrage/true boss, bayangan, indikator
  debuff menara, badan generik, HP bar, papan nama) diport ke
  `BossOverlay.gd`/`BossPlate.gd` dan dikunci fixture 50 skenario/647 op yang
  direkam dari `Boss.draw` pygame ASLI (`tools/test_boss_draw_parity.py` +
  `BossDrawParityTest`); `test_boss_true_aura_parity.py` kini menguji model
  pita dan **mewajibkan** pendekatan naif 8×`draw_circle` gagal.
- **Mitigasi damage hero — TERUTUP audit basic attack (7 September 2026):**
  blok armor `Hero.take_damage` pygame (armor ITEM utk SEMUA damage non-
  `fire`, tanpa MR) kini di-mirror persis oleh `CombatSystem` per jenis
  target dan dikunci `HeroBasicAttackParityTest` — detail di tabel di atas.
  ~~(1) **rend crit Sanguine Thorn belum ada sama sekali** di item Godot
  (item aktif Soul Rend — silence/amp/target — belum diport; pygame
  `_do_attack` crit pasti 150% ke target bertanda)~~ — **DITUTUP FASE 19**:
  `ItemInventory` kini menyimpan penandaan `rend_target` (trigger otomatis
  via `tick`, silence + amp + tanda), `CombatSystem.calc_damage` memberi
  crit PASTI 1.5x ke target bertanda TANPA roll dan MEN-DISKIP roll crit
  item (urutan crit buff → rend → roll, persis `_do_attack` 4244-4270);
  (2) **roll block Scarlet Bulwark 55%, roll crit Dead Edge, evasion item,
  dan blind < 1.0 DIREPLAY** penuh lewat `hero_rng_guards`/
  `HeroRngGuardParityTest` (roll ter-script, urutan+jumlah konsumsi
  dibandingkan) — ~~yang masih tanpa oracle: roll blind BOSS (pygame-nya
  di `bosses/base_boss.py`, Godot tetap `randf()` langsung) dan proc item
  on-attack/on-damage (bash/chain/frostbite/miasma/empower/entangle/
  static charge)~~ — **DITUTUP FASE 19**: roll blind BOSS kini lewat pintu
  `ParityRng` dan seluruh proc dikunci oracle `item_procs`/
  `ItemProcParityTest` (detail di baris tabel item tempur di atas);
  masih TERBUKA di jalur ini (eksplisit, tidak disembunyikan):
  (3) **context hero aktif**
  pygame boss) tidak diuji.
- **Perintah taktis dan kontrol pemain:** ~~`tactical_commands.py` belum diport~~
  (**DITUTUP FASE 17 + 18** — manajernya `TacticalCommandsParityTest`,
  pemicu hotkey/panel-nya `TacticalInputParityTest`); yang tetap terbuka:
  overlay sentuh Android (kontrol sentuh di layar — data di `HudLayout`,
  UI-nya belum ada).
- **Progresi/settings:** kunci difficulty sepanjang run, reset progresi karena
  ganti mode, statistik/achievement, migrasi/cloud save belum setara. Tidak
  menghapus save pengguna untuk menyamarkan selisih. Pilihan settings yang
  kini ADA + berfungsi (FASE 22): volume master/sfx/bgm (persist per slot,
  live ke `AudioManager`), Screen Shake (camera trauma, guard live), Damage
  Numbers (live ke `world_popups`), hapus slot aktif + dialog. **Ditambahkan
  10 September 2026 (port `GameSettings`):** slider **Volume Voice** (persist
  `voice`; kategori `voice` pygame `_system.py:599-604` juga tanpa file voice
  — di kedua engine slider tidak mengubah bunyi, hanya persist),
  cycler **Game Speed** 0.5/1.0/1.5/2.0 (`game_speed`, berlaku boot + live ke
  `Engine.time_scale` dengan quirk pygame `int(mult)-1` dipertahankan:
  1.5x memang tidak berpengaruh di pygame — `_core.py:1966`; hit-stop kini
  kembali ke basis speed, bukan 1.0), cycler **FPS Limit** 30/60/120/0
  (`fps_limit` → `Engine.max_fps`, 0 = tanpa batas seperti `main.py:637`),
  dan seksi **CLOUD SAVE** gaya PC pygame (`_draw_cloud_buttons`
  `_core.py:6395-6455`: status `CLOUD: OFF (PC / belum diset)` + tombol
  upload/download inert + baris status — plugin Play Games tetap BELUM
  diport, di pygame PC pun tombolnya tanpa akses). ~~language~~ **sudah
  diport FASE 30** (`localization.py` → `Localization.gd` + baris BAHASA di
  PENGATURAN, lihat seksi "Lokalisasi UI" di atas). Yang TERBUKA eksplisit:
  voice playback (tanpa aset di kedua
  engine), cloud save fungsional (Play Games), difficulty-lock pygame
  ("terkunci sampai semua level selesai" — Godot memilih difficulty
  bebas di PILIH LEVEL, deviasi terdokumentasi).
  Yang SUDAH setara + teruji dari blok ini termasuk **sumber jumlah unlock
  catch-up** (`hero_catchup_unlocks`/`HeroCatchupUnlockParityTest`: kunci
  save, auto-grant starter, hitungan `boss_unlocks_for_purchases`, stat hero
  hasilnya, dan jaminan unlock save lama tidak hilang). Reward/atribusi/unlock kematian boss juga
  sudah teruji di FASE 14 (`boss_death_rewards`); rincian di bawah. Yang TETAP TERBUKA
  di jalur progresi ini, eksplisit:
  (1) **penempatan auto-grant starter beda**: Godot memberi `kaizen` saat
  save di-backfill (load), pygame saat `Game.reset`. Jumlah unlock
  catch-up sama-sama 0, tetapi status OWNED `kaizen` di Hero Shop untuk
  save yang benar-benar baru muncul lebih awal di Godot — belum
  disamakan karena mengubahnya menyentuh alur save;
  (2) ~~**multi-slot save + migrasi legacy + cloud save** (`_system.py`
  NUM_SLOTS/`migrate_legacy_save`, `mobile/cloud_save.py`) belum ada di
  Godot: satu berkas `user://mystic_save.json`, jadi `get_slot_info`,
  playtime, dan `level_stats` belum diport~~ — **DITUTUP FASE 21** untuk
  multi-slot + migrasi legacy (`save_slots`/`SaveSlotParityTest`: jalur
  berkas, 8 kasus migrasi, 9 skenario save/load per-slot, 3 kasus hapus,
  6 kasus `get_slot_info`, 32 baterai format, 5 layar × 3 kartu slot —
  lihat baris tabel di atas). **CLOUD SAVE (`mobile/cloud_save.py`)
  MASIH TERBUKA** dan sengaja dikeluarkan dari scope FASE 21: Godot tidak
  mengunggah snapshot Play Games, jadi auto-upload di `SaveManager.save()`
  pygame belum punya padanan. Yang juga tetap terbuka di jalur ini:
  **`slot_playtime_seconds` tidak pernah bertambah di pygame** — tidak ada
  satu pun pemanggil yang menambahnya (selalu 0) dan kartu slot tidak
  menampilkannya, jadi port Godot setia menyimpan 0 alih-alih mengarang
  akumulasi. Peta nama legacy berbeda dan terdokumentasi: Godot tidak
  pernah punya `progress.json`, jadi berkas tunggal lamanya
  (`user://mystic_save.json`) yang dimigrasi ke slot 1 lalu dipindahkan ke
  `mystic_save_backup.json.old`;
  (3) ~~**alur pembelian hero di Hero Shop meta** (`_unlock_hero_in_meta_shop`:
  syarat `unlock_require_boss`, potong `meta_gold`, harga 4500) ada di
  `MainMenu.gd` tetapi belum punya oracle sendiri — yang diuji harness ini
  hanya AKIBAT daftar unlock terhadap catch-up, bukan validasi transaksinya~~ —
  **DITUTUP FASE 20**: oracle `meta_shop_txn` mengunci katalog EFEKTIF
  pygame (def `get_all_hero_types` kedua menimpa semua harga: starter 0,
  mini/true 4500 — 222 baris closed-world vs `heroes.json`), 10 kasus
  transaksi (urutan guard katalog→duplikat→gate boss→saldo, sfx
  ui_error/ui_buy, sinkron in-memory↔save_data, persist disk), dan matriks
  keputusan kartu 5 state × 4 hero; replay `MetaShopTxnParityTest` lewat
  jalur produksi `MainMenu._try_unlock_hero` + meta kartu
  (pemetaan `purchased_heroes` = `unlocked_heroes` FASE 13);
  (4) `heroes_unlocked_this_match` kini DIPORT (`GameManager` +
  baris `NEW HERO: …` di panel game-over, dikunci `UiHudParityTest` —
  pygame menghitung subtitle ini tapi tidak me-render-nya) DAN popup
  achievement `NEW HERO UNLOCKED!` kini ikut diport + dikunci
  (`GameManager.unlock_achievement` → signal → `AchievementPopup.gd`,
  fixture `match_scoring` — lihat baris tabel klaster skor).
  ~~Yang tetap terbuka di jalur ini: tampilan **BEST SCORE/best time per
  level di LEVEL SELECT** pygame (`_core.py:4257-4271` +
  `SaveManager.format_time`) belum diport — data `level_stats` sudah
  ditulis ke save, UI menu-nya belum~~ — **DITUTUP FASE 20**: kartu level
  Godot kini menampilkan blok stat lengkap (skor `9,999`/`12.3K` +
  truncasi `[:8]` ambang 120px, waktu `M:SS` via `SaveManager.format_time`,
  attempts `xW/y`, win rate 3-band) — dikunci oracle `level_select_stats`
  (draw pygame ASLI `Menu._draw_level_card` kartu 280px + baterai format)
  + replay `LevelSelectStatsParityTest` lewat kartu produksi. Yang tetap
  terbuka di jalur ini: **piksel** blok stat (lebar chip metrik font —
  batas tepat truncasi bergantung raster font; konstanta ambang pygame
  120px dipertahankan) dan label bahasa Indonesia yang memang beda
  disengaja; (5) ~~slot save tunggal~~ — **DITUTUP FASE 21**: 3 slot +
  migrasi legacy Godot (`mystic_save.json` → `slot_1.json`; save
  pengguna tidak pernah dihapus — lihat baris tabel di atas). Yang TETAP
  TERBUKA di jalur ini: **piksel** kartu slot (gradasi/ikon vektor dan
  truncasi nama level `ui_theme.fit_ellipsis` yang bergantung metrik font
  — yang dikunci hanya nama level MENTAHNYA), label kartu bahasa
  Indonesia (beda disengaja, dipetakan eksplisit di harness), dan isi
  `level_stats` lama tetap tidak diimpor — backfill `level_stats: {}`,
  statistik mulai terkumpul dari sekarang.
- **Android/performa:** lolos tes headless bukan pengujian visual, sentuh,
  performa perangkat, ataupun verifikasi APK/AAB.

## Tes yang menjaga koreksi ini

Dari root repository, dengan `pygame-ce` dan Godot 4.3+ terpasang:

```bash
# Fixture dievaluasi dari fungsi Pygame asli, bukan salinan rumus Godot:
python tools/test_godot_match_parity.py

# BossKit.gd adalah hasil generate — tidak boleh drift dari base_boss.py:
python3 tools/gen_boss_smart_ai.py --check

# HeroSkillKit.gd adalah hasil generate — tidak boleh drift dari hero_skills/:
python3 tools/gen_hero_skill_kit.py --check

# hero_skills_processor.h/.cpp (GDExtension C++) JUGA hasil generate dari
# _bundle.py yang sama — cek ini tanpa compiler:
python3 tools/gen_hero_skills_cpp.py --check

# Seluruh runtime di bawah memakai user:// sementara, BUKAN save pengguna:
export XDG_DATA_HOME="$(mktemp -d)"
trap 'rm -rf "$XDG_DATA_HOME"' EXIT

# Import resource lalu jalankan scene regresi:
godot --headless --path godot --editor --import
godot --headless --path godot res://tests/GameplayParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/BattleSmokeTest.tscn --quit-after 180
godot --headless --path godot res://tests/AIPlayerTest.tscn --quit-after 120
godot --headless --path godot res://tests/CinematicTest.tscn --quit-after 960
godot --headless --path godot res://tests/BossCoreParityTest.tscn --quit-after 420
godot --headless --path godot res://tests/BossSmartAIParityTest.tscn --quit-after 2400
godot --headless --path godot res://tests/HeroSkillParityTest.tscn --quit-after 900
# Jalur C++ (butuh lib GDExt terbuild: cd godot/gdext/mystic_skills && scons ...):
godot --headless --path godot res://tests/HeroSkillGdextParityTest.tscn --quit-after 900
godot --headless --path godot res://tests/HeroBasicAttackParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/EntityPyParityTest.tscn --quit-after 60
godot --headless --path godot res://tests/HeroRngGuardParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/ItemProcParityTest.tscn --quit-after 600
godot --headless --path godot res://tests/HeroItemsParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/HeroCatchupUnlockParityTest.tscn --quit-after 120
godot --headless --path godot res://tests/UiHudParityTest.tscn --quit-after 400
godot --headless --path godot res://tests/MatchScoringParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/LevelSelectStatsParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/MetaShopTxnParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/BossDeathRewardParityTest.tscn --quit-after 600
godot --headless --path godot res://tests/MinionTowerRewardParityTest.tscn --quit-after 600
godot --headless --path godot res://tests/DeathDispatchParityTest.tscn --quit-after 600
godot --headless --path godot res://tests/SaveSlotParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/TouchHudParityTest.tscn --quit-after 300
godot --headless --path godot res://tests/SystemPerfParityTest.tscn --quit-after 300
# Blok `performance.py` + `fps_counter.py` _system.py (oracle pygame + fixture):
python3 tools/test_system_perf_parity.py
# Lokalisasi `localization.py` -> Localization.gd (oracle TANPA pygame/Godot):
python3 tools/test_godot_localization_parity.py
godot --headless --path godot res://tests/LocalizationParityTest.tscn --quit-after 120
python3 godot/tools/test_godot_log_gate.py
```

`GameplayParityTest` membaca `godot/tests/fixtures/match_parity.json`: ekonomi
54 level × 3 difficulty, 50 komposisi wave, 25 kombinasi minion/nexus, eskalasi
nexus AI dan titik spawn. Tes runtime juga memeriksa pembelian/duplikat/cap,
respawn individu dan team wipe, pause, antrean wave, jalur, restart dan menu.
`BattleSmokeTest` membeli hero melalui API yang sebenarnya, bukan lagi
menganggap roster demo sebagai syarat sukses.

`BossCoreParityTest` membandingkan `godot/data/bosses.json` dengan 216 baris
oracle `boss_core` (stat boss + flag smart-AI dari `Boss.update`, dan nilai
enrage dari pemanggilan `update()` Pygame yang sebenarnya), lalu menguji
perilaku runtime node Boss.gd: resilience/anti-burst, entrance freeze, aggro,
tenacity (slow/atk_slow/stun), heal true boss, cleave, dan ability generik
boss tanpa smart-AI.

`BossSmartAIParityTest` memutar ulang 237 skenario oracle `boss_smart_ai`
(3 skenario × 79 boss: gerombolan dengan HP bertahap, duo HP rendah, target
tunggal di tepi jangkauan) pada node `Boss.gd` asli yang menjalankan
`BossKit.gd`, lalu membandingkan jejak event per frame — cast skill, damage,
heal/shield, slow, kunci serangan, knockback, dash, enrage, facing, buff
speed/damage — plus state kit final (timer Q/W/E/R, buff, posisi clone,
target). Serangan dasar dimatikan di KEDUA sisi supaya jejak murni Q/W/E/R;
oracle dihasilkan dari `Boss.update` Pygame sungguhan lewat
`python tools/test_godot_match_parity.py --write-fixture`.

`HeroSkillParityTest` memutar ulang seksi fixture `hero_skills` (STRING JSON
kompak; 222 hero × skenario cluster/edge/combo/empty) pada node `Hero.gd` +
`HeroSkillKit.gd` yang sebenarnya: cast skrip (force-ready = cooldown dinolkan
di KEDUA sisi), urutan timer persis `Hero.update` (Q-- → active-- → WER-- →
`update_timers`), hit harness `fire` tiap 37 frame dari f30 (menggerakkan
guard konsumsi kit: shadow realm & Bristleback DR+reflect), floor hp 1.0.
Dibandingkan: jejak event per frame (attempt/cast/ask/bhp/bmove/bspd/batk/
bface/dmg/alock/emove/slow) + state final (4 cooldown, active_skill, diff kit
vs instance segar, kondisi probe). Serangan dasar dan gerak TIDAK di-simulasikan
di harness ini (serangan dasar dikunci `HeroBasicAttackParityTest` di bawah).
Regenerasi fixture HANYA bila `hero_skills/_bundle.py` atau `_entity.py`
berubah — pygame tidak pernah disetel mengikuti Godot.

`HeroBasicAttackParityTest` memutar ulang seksi fixture `hero_basic_attack`
(STRING JSON kompak; 29 skenario + 3 probe get_block) pada node
Hero/Minion/Boss/Tower/Nexus ASLI + `CombatSystem.apply_damage` yang
sebenarnya. Oracle pygame menjalankan `Hero._do_attack` betulan (melee &
ranged: bonus item → crit buff `int(×2)` → crit item → lifesteal float /
`int()` saat spawn → cleave netral) DAN memanggil `take_damage` tiap jenis
target dengan matriks damage-type × school × state (armor item, aura live,
shred, amp, block aura, blind penyerang, wind wall, bristleback + reflect,
thornmail, MR minion, rumus shred boss, armor menara, int truncation shield
castle). Skenario bebas RNG dan dijalankan dua kali dengan seed berbeda saat
generate — hasil harus identik. Dibandingkan: `max_hp`/`hp0` tiap unit,
HP semua unit tiap event (fase spawn & hit utk ranged), damage + school
proyektil, dan nilai `get_block()` (amount mengikuti melee/ranged PEMILIK).
Regenerasi fixture HANYA bila `_entity.py`/`hero_items.py`/`bosses/` berubah.

`HeroRngGuardParityTest` memutar ulang seksi fixture `hero_rng_guards`
(STRING JSON kompak; 14 skenario, 58 event HP, 47 roll ter-script) pada
node Hero ASLI + `CombatSystem.apply_damage`/`ItemInventory.roll_crit`
yang sebenarnya. Oracle pygame menjalankan `take_damage`/`_do_attack`
asli dengan `random.random` DI-MONKEYPATCH: hanya panggilan dari
`_entity.py::take_damage` dan `hero_items.py::roll_crit` yang mengonsumsi
urutan nilai skenario — pemanggil lain (audio/FX) jatuh ke RNG asli, dan
tiap skenario tetap dijalankan dua kali dengan seed beda supaya roll
liar yang memengaruhi hasil ditolak saat generate. Sisi Godot memakai
hook `ParityRng` (script kosong = `randf()` global, jadi perilaku
produksi tidak berubah): harness memasang script lewat `begin()`,
melepasnya lewat `end()`, lalu membandingkan HP semua unit tiap event
DAN daftar nilai roll yang benar-benar dikonsumsi — jumlah, nilai, dan
urutan. Roll yang hilang/bertambah/tertukar di salah satu engine gagal
tes. Cakupan: windrun (Sylara W — fisik = normal/projectile non-magic
termasuk netral tanpa source, 0.75 persis tidak meleset, sihir/fire tanpa
roll), shadow realm (Zephyr W — kebal total tanpa roll), urutan prioritas
guard shadow → windrun → wind wall → veil → evasion, roll block Scarlet
Bulwark 55% (setelah armor, non-fire, floor 0), roll crit Dead Edge 25%
(sebelum mitigasi target; crit buff men-diskip; ranged: roll crit saat
spawn lalu roll block saat mendarat), evasion Monarch Wings 28%, blind
< 1.0 penyerang (satu roll `max(ev, blind)`, True Strike tanpa roll),
dan windrun pada reflect Bristleback (nested take_damage). Regenerasi
fixture HANYA bila `_entity.py`/`hero_items.py` berubah.

`ItemProcParityTest` memutar ulang seksi fixture `item_procs` (STRING JSON
kompak; 18 skenario, 53 event, 24 roll ter-script) pada node
Hero/Boss/Minion ASLI + `CombatSystem.apply_damage`/`ItemInventory` yang
sebenarnya — pola `hero_rng_guards` diperluas ke ITEM TEMPUR (FASE 19).
Oracle pygame menjalankan `_do_attack`/`take_damage`/`inv.update` asli
dengan `random.random` DI-MONKEYPATCH per situs roll combat
(`hero_items.py::_on_hit_common/_notify_damage_taken/roll_crit`,
`_entity.py::take_damage`, `base_boss.py::take_damage`) — dua run seed
beda wajib identik. Sisi Godot mereplay frame produksi yang sama
(`status.tick` + `items.tick` per unit, urutan `Hero.update` pygame) dan
membandingkan per event: HP semua unit (fase spawn & hit untuk ranged),
daftar roll terkonsumsi (jumlah+nilai+urutan), dan flag state internal
(`rend_on`/`rend_marked`/`rend_cd_on`/`static_on`/`slow_on`). Cakupan:
Soul Rend Sanguine Thorn (trigger `inv.update`, silence + amp + penandaan,
crit pasti 1.5x TANPA roll + short-circuit roll Dead Edge, cd 1080f,
juga vs boss), bash Abyss Breaker (22%, damage NETRAL kena armor, cd 140f
menahan roll), Arc Chain (dict chain dari SLOT PERTAMA — 0.19/0.21
membedakan fenrir vs thunder), Piercing Bash Sundering Cudgel (28%,
magic, situs SETELAH chain), Frostbite (tanpa roll), Miasma (racun tanpa
roll, tick 30f) + multishot Polycephaly (roll HANYA ranged,
`int(damage×70%)`), Empower Strike (charge 540f penuh sejak init —
serangan pertama TIDAK proc; nol/parsial/penuh via injeksi
`items_state`), Entangle vine_rod (root slow 1.0, cd 540f, expiry slow
korban dikunci), Static Charge Thunder Coil (roll 20% saat pemilik kena
damage, cd 1200f menahan roll, zap berkala dengan quirk pygame
`static_tick` berkurang 2×/frame → zap tiap 15 frame), dan roll blind
BOSS (hanya `normal` bersource, 0.40 persis kena, True Strike tanpa
roll). Regenerasi fixture HANYA bila `_entity.py`/`hero_items.py`/
`bosses/` berubah.

`HeroCatchupUnlockParityTest` memutar ulang seksi fixture
`hero_catchup_unlocks` (objek biasa, bukan string kompak) pada
`SaveManager`/`GameManager`/node `Hero.gd` yang sebenarnya. Oracle
membaca kode pygame ASLI: kunci save + starter yang di-grant diambil dari
**AST `Game.reset`** (rename diam-diam langsung ketahuan),
`SaveManager.load()` pygame dijalankan atas berkas slot lama di direktori
save SEMENTARA, `boss_unlocks_for_purchases`/`starter_catchup` dipanggil
apa adanya, dan 24 baris stat berasal dari `Hero` pygame SUNGGUHAN yang
dibuat dengan `__main__.game_instance.purchased_heroes` terisi (termasuk
sesudah `upgrade()` — catch-up TIDAK dihitung ulang saat naik level).
Dibandingkan di Godot: konstanta kurva + daftar starter, unlock save lama
tidak hilang sesudah backfill, `GameManager.catchup_unlocks()` untuk 10
isi save (kosong, hanya starter, 6 starter, 1/3/6/12/15 hero non-starter,
entri kembar, dan "di luar match" = 0), 315 multiplier
`HeroDB.starter_catchup_mults`, lalu `base_hp`/`base_damage`/`max_hp`/
`damage` node Hero. Harness TIDAK PERNAH menulis berkas save
(`bind_purchased_heroes(false)`, state `SaveManager.data` di-snapshot dan
dipulihkan). Regresi yang dijaga khusus: `return_to_menu()` melepas
binding daftar unlock **tanpa** menghapus isi save. Regenerasi fixture
HANYA bila `_core.py`/`_entity.py`/`_system.py`/`hero_balance.py`
berubah.

`HeroItemsParityTest` memutar ulang seksi fixture `hero_items` (objek
JSON) pada `HeroItems.gd` + `ItemDB`/`HeroDB` yang sebenarnya. Oracle
membaca kode pygame ASLI `hero_items.py` langsung: `get_item_class`
(33 item, termasuk override tempest_vane/abyss_breaker → TANK dan
magic_only → MAGIC, item tak dikenal → PHYSICAL), `_build_shop_pages`
(6 halaman selaras batas kelas + meta + urutan flatten 33 item),
`_build_item_mechanics` bahasa id DAN en (popup detail, urutan field =
urutan katalog), `_fmt_mech_value` (baterai persen/frame/crit_mult/
str(float) termasuk kasus float "kotor" 0.022×100 → "2.2%" dan
`str(3.0)` → "3.0" vs `str(4)` → "4"), `pending_forge_items`/
`deliver_pending_forge_items` (antrian melekat hero, item tak muat/tak
dikenal tetap diantrikan), `_resolve_shop_target` (tersimpan > terseleksi
> hidup pertama > mati pertama, + kasus tanpa hero), dan `_hero_level_mult`
(level 0..20). Sisi Godot memakai `HeroItems.gd` dengan katalog
`items.json` disuntik + `HeroDB.hero_levels_int()` untuk pengali level.
Regenerasi fixture HANYA bila `hero_items.py` berubah.

`LocalizationParityTest` memutar ulang **seluruh** `localization.json` (objek
JSON) pada `Localization.gd` + jalur produksi `GameManager`/`SaveManager`/
`ItemDB`/`MainMenu`. Oracle-nya `localization.py` yang dijalankan apa adanya:
tabel 24 kunci × 2 bahasa, 48 hasil `tr()` (setiap kunci × bahasa dengan nilai
contoh), 8 kasus tepi (kunci tak dikenal → kunci mentah, nilai hilang →
template mentah), 21 kasus `str.format` (escape `{{`, kurung tunggal →
`ValueError` → mentah, float `3.0` → `"3.0"`), 13 kasus `str()`, 7
`set_language` (termasuk `""`/`"ID"`/`"en-US"`/`null` → `id`), 7 label, dan
daftar placeholder per kunci. Yang di sisi Godot juga dikunci: bahasa aktif
setelah boot == setting tersimpan, `set_language` menolak bahasa invalid tanpa
menyimpan/memancarkan sinyal, cycler `<`/`>` membungkus ke dua arah, dan layar
PENGATURAN produksi benar-benar memuat label `Bahasa` + `Bahasa Indonesia`.
Fixture-nya dijaga **dua lapis**: `tools/test_godot_localization_parity.py`
membandingkan tabel di `Localization.gd` dengan `localization.py` baris demi
baris tanpa engine (jalan di langkah Linter statis CI), dan scene ini
menjalankan ulang hasilnya di dalam Godot. Regenerasi fixture HANYA bila
`localization.py` berubah.

`BossDeathRewardParityTest` memutar ulang **seluruh** seksi
`boss_death_rewards` (objek JSON, bukan pembacaan string kode). Oracle
menjalankan `Boss.take_damage`, `Game.update`, `_process_boss_kill`,
`_unlock_achievement`, `EffectManager.add_gold_popup`/`FloatingText.update`
dan write+reload `SaveManager` pygame ASLI; sumber damage tidak ikut
simulasi arena, income/wave dibekukan, FX kontak hit diisolasi dari
klaster reward. Dua seed berbeda wajib menghasilkan jejak identik.
Daftar headless tertutup yang **semuanya direplay**, bukan hanya dicatat:

1. **216 boss**: nama/kelas/nilai reward dari instans asli, reward tidak
   berubah oleh hard scaling, payout runtime gold/skor/AI/counter.
   Set tipe harus sama persis dengan `BossDB` (hilang/asing/ganda gagal).
2. **37 skenario `Game.update`** pada Main/HUD/Boss/Hero/Minion/Tower/Nexus
   Godot nyata: last-hit hero blue/red/netral/hero mati, tower/minion/
   castle/boss/self/tanpa sumber, tim sama vs lawan, source berbeda dari
   `from_team`, nonlethal → last-hit berubah, guard alive/defeated, null
   active boss, callback ganda, boss tipe sama berulang, counter mini/true
   independen, ID achievement dedup, reward runtime 0/17/123456, hard
   scaling, owned vs belum-owned, unlock lama, flag damage numbers off,
   jeda cinematic dan pending mini pada frame yang sama. Snapshot
   gold/skor/ai_gold/total_kills/combo/max_combo/killer.kills, daftar
   tracking, event popup, current/queue/timer achievement, **semua field
   non-piksel** floating text, posisi+nominal event gold, data save +
   jumlah/urutan write sungguhan dibandingkan rekursif (key asing juga
   gagal). Kill hero biasa diuji eksplisit **tanpa HERO SLAYER**.
3. **5 baterai antrean**: formatting (0, negatif, angka besar), posisi
   pecahan/negatif, RGB/font/critical, lifetime 50 frame + gerak/scale,
   drift, FIFO 302 entri → cap 300, buang tertua, expiry tidak menghapus
   popup baru, gold tetap muncul meski damage numbers off/cap kualitas 1,
   campuran teks SLAYER + gold dengan anggaran damage 2. RNG hanya situs
   `FloatingText.__init__`/`add_damage_number` yang di-pin: jenis/range/
   nilai/jumlah/urutan panggilan ikut direplay lewat Callable lokal queue.
   Akumulator diuji dua half-frame per frame, bukan hanya fungsi tick.
   **3 baterai FIFO bersama** juga mempertemukan node `DamageNumber`
   legacy nyata dengan popup gold (damage→gold, gold→damage, flag off),
   termasuk disposal node lama; batas 300 bukan antrean gold terpisah.
   Soft-cap pygame membuang SATU entri tertua, bukan menguras sampai
   cap kualitas. Renderer lama tetap menggambar dirinya sendiri; adapter
   WeakRef hanya menyatukan FIFO/budget, bukan mengklaim pikselnya setara.
4. **Menang dan kalah**: `end_match` sungguhan + reload disk; boss unlock
   sudah persisten sebelum hasil, kalah tidak memberikan hero gratis,
   menang menambah hero + popup `NEW HERO UNLOCKED!` tanpa membayar ulang
   gold/skor boss. Sentinel data lain dan meta gold tetap benar.
5. **Lifecycle**: counter/list/ID dari `Game.reset` pygame vs `start_level`
   Godot; popup match lama dibuang, menu melepas binding `unlocked_bosses`
   tanpa `clear()` milik save; match berikutnya bisa rebind unlock lama.

CI menjalankan scene ini dengan `XDG_DATA_HOME` baru agar save pengguna
bahkan tidak dibaca/ditulis bila harness berhenti di tengah. Harness juga
mem-snapshot/memulihkan data+file seperti `MatchScoringParityTest`.
`SaveManager.saved` diamati setelah file ditutup, bukan mock save yang
selalu sukses. Gate mewajibkan `[BossDeathRewardParityTest] PASS` dan
menolak error runtime **serta baris `[...Test] FAIL` meskipun ada PASS**;
5 regresi Python untuk gate turut dijalankan. Fixture lama tetap identik;
kode pygame tidak diubah untuk menyesuaikan port.

`MatchScoringParityTest` memutar ulang seksi fixture `match_scoring`
(objek biasa, bukan string kompak) atas kode Godot yang sebenarnya.
Oracle pygame menjalankan `Game.update` SUNGGUHAN headless (Game +
Minion/Hero/Tower betulan, kematian lewat `take_damage` asli, dua run
seed beda harus identik, dan guard internal menolak perubahan state di
langkah tanpa kill ter-script). Yang direplay: (1) mesin state
`ComboCounter` murni per frame — count/timer/last_combo/color_flash/
display_scale/target_scale, termasuk quirk `max_combo` yang dibaca
SEBELUM `add_kill` dan expiry 120 frame; (2) data draw combo dari draw
pygame asli — label ambang, warna dasar + pulsa flash (ruang 0..255),
anchor (W−100, 100), label (cx, cy−30), bar 80×4 @(cx−40, cy+40) +
lebar isi per sisa timer; (3) 9 skenario reward `Game.update` —
gold/score/ai_gold/total_kills/max_combo/combo per frame + atribusi
`killer.kills` (kill netral/self/tower/minion tanpa atribusi, +150 tim
korban, respawn 600 frame tanpa bayar ganda) pada node Minion/Hero/
Tower ASLI yang di-step `GameManager._tick_combo`/`_update_hero_
respawns` 1/60 per frame script; (4) `SaveManager.get/update_level_
stats` (9 kasus: flag NEW BEST, best hanya saat menang, max_combo
all-time, time 0 diabaikan) pada dict awam tanpa menyentuh save; (5)
state machine `AchievementPopup` (antrean, 180 frame, pengganti di
frame yang sama) + kurva slide 181 titik + teks/warna panel; (6)
trigger popup `NEW HERO UNLOCKED!` dari `_auto_unlock_defeated_boss_
heroes` via signal `achievement_unlocked` (5 kasus termasuk sudah-
owned → tanpa popup); (7) integrasi `end_match` penuh — `start_level`
+ `end_match` menulis `level_stats` save, menyalakan flag NEW BEST,
baris panel game-over (Max Combo + NEW BEST! + NEW HERO), dan memancarkan
popup; defeat menulis statistik tanpa best. Harness mem-snapshot
`SaveManager.data` DAN berkas `user://mystic_save.json` lalu memulihkan
keduanya. Regenerasi fixture HANYA bila `_core.py`/`_render.py`/
`_system.py`/`_entity.py` berubah.

`UiHudParityTest` memutar ulang seksi fixture `ui_hud` (objek biasa, bukan
string kompak) pada node `Main`/`HUD`/`ShopPanel`/`SkillBar`/`MainMenu`
yang sebenarnya. Oracle menjalankan draw pygame ASLI headless dengan
font/mouse/timer/waktu ter-pin: 82 skenario draw (gold/chip/badge, panel
hero, item forge + 6 halaman, shop hero, popup menara/nexus/build, overlay
menang/kalah, pause, intro), 31 kasus klik penuh yang berurutan dalam SATU
`Game` (state mengalir: beli, upgrade, jual, regen, shield, tab, scroll,
prioritas klik dunia, klik kanan, PLAY NEXT LEVEL), 28 hotkey (termasuk
matriks N/R/H/ESC saat victory-L1/victory-L54/defeat), predikat
range/magic 222 hero, tabel biaya hero/menara/nexus/shield/sell, kurva
slide banner 121 titik, baterai format (gold/income/mode/cooldown/
match-time), baterai touch-rect 48px, matriks tombol+visibilitas touch
HUD, dan urutan draw (dokumentasi — Godot memakai scene tree).
Dibandingkan di Godot: teks label HUD/panel/toko/game-over, daftar+
urutan+enabled/disabled+alasan tombol (`ui_key`/`ui_data` dengan audit
closed-world tiap layar — key asing/ganda gagal tes), geometri panel
pause 400×400 + tombol 300×48, kurva easing, dan perilaku klik/hotkey
lewat node sungguhan. Harness mem-snapshot `SaveManager.data` DAN berkas
`user://mystic_save.json` lalu memulihkan keduanya (tidak menyentuh save
pengguna). Regenerasi fixture HANYA bila `_core.py`/`_render.py`/
`hero_items.py`/`ui_components/` berubah.

Jika aturan Pygame memang berubah, sesuaikan Godot, **kemudian** regenerasi:

```bash
python tools/test_godot_match_parity.py --write-fixture
```

`MinionTowerRewardParityTest` memutar ulang **seluruh** seksi
`minion_tower_rewards` (objek JSON, 20 skenario) pada node
Minion/Hero/Tower Godot ASLI + `GameManager` sungguhan. Oracle
menjalankan `Game.update` pygame ASLI headless (`_core.py:2196–2227`
dipanggil betulan, kematian lewat `take_damage` asli, dua run seed beda
harus identik, FX kontak hit diisolasi dari jejak, guard internal
menolak perubahan state di langkah tanpa kill ter-script). Skenario
mencakup: minion merah oleh hero biru/mati/merah, tower, minion, nexus,
boss, self, netral tanpa sumber, override `team:""`, variasi jenis
minion (goblin/orc/troll/undead/dark_rider + skala nexus), menara
outer/inner kedua tim, kematian beda tim + jenis campur SATU FRAME,
10-kill berurutan (quirk max_combo 9), 6-kill berjeda (max_combo 5),
expiry combo 120 frame, antrean popup FIFO teracak-deklarasi,
flag damage numbers off (popup gold tetap muncul), dan unit
dead-on-spawn (minion + menara). Kunci anti bayar ganda TIGA lapis:
pukul mayat
(`take_damage` ulang pada unit mati), `die()` ulang, dan callback
`register_*_death` langsung — semuanya tak boleh membayar/popup/counter
dua kali; flag hero dibuka lagi saat respawn. Dibandingkan rekursif
closed-world per langkah: gold/score/ai_gold/total_kills/max_combo/combo
(count/timer/last_combo)/red_towers_destroyed/kills
(unit+sources)/rewarded/seluruh field non-piksel floating text/
gold_events posisi+nominal/daftar+urutan konsumsi RNG popup. Dua seed
harus identik. Harness men-step `GameManager._tick_combo`/
`_update_hero_respawns`/`world_popups.advance` 1/60 per frame skrip
(pola `MatchScoringParityTest` — income dibekukan `GOLD_PER_SECOND=0`
di oracle); cinematic di-clear dan SceneTree di-unpause supaya tick
manual berjalan. Regenerasi fixture HANYA bila `_core.py`/`_entity.py`
berubah.

`DeathDispatchParityTest` memutar ulang **seluruh** seksi `death_dispatch`
(objek JSON, 21 skenario) pada node Hero/Minion/Tower Godot ASLI +
`GameManager`/`CombatSystem` sungguhan. Beda penting dari FASE 15: oracle
TIDAK memakai `take_damage(10**9)`, melainkan **jalur serangan pygame
sunnguhan** — `Tower._shoot → Bullet.update → Bullet._on_hit`
(`take_damage(dmg, team, 'projectile')` TANPA source), `Hero._do_attack`
(melee instan `source=hero, school=…`; ranged lewat `_spawn_projectile` +
`Hero.update`), `Minion.update` (`take_damage(dmg, team)` netral), dan
`take_damage(source=hero, school=…)` untuk jalur skill/kit — lalu loop
reward `Game.update` membayar di frame berikutnya. Godot mereplay lewat
jalur produksi yang sama: `Tower._shoot(CombatSystem)` → `TowerBullet`
diterbangkan dengan `_physics_process` manual (deterministik) →
`_on_hit` → `apply_damage`; `Hero.try_attack()`; `Minion.try_attack()`;
dan `CombatSystem.apply_damage` langsung untuk skill/DoT. **Tidak ada**
`register_minion_death`/`register_tower_death`/`register_hero_death`
manual dan **tidak ada** `die()` langsung — reward boleh muncul HANYA
sebagai akibat dispatch, dan `_run_kill` pola FASE 15 sengaja tidak
dipakai karena justru melewati dispatch yang diuji.

Skenario: menara membunuh lewat peluru **normal/cannon (+splash 60%)/ice**,
menara membunuh menara, **hero melee** membunuh minion & hero, **hero
ranged** (proyektil) membunuh minion/menara/hero, **minion** membunuh
menara & minion, damage **skill/kit** membunuh minion & hero, **guard
tanpa kematian** (menara/minion/hero + `direct` 99.999 damage dengan HP
sisa > 0 — dispatch wajib diam total), dan **mayat dipukul ulang**
(dibayar tetap sekali). Dua skenario membuktikan klaim source: korban
ber-`_bristleback_active` yang dipukul **peluru** tidak memantulkan apa
pun (HP menara utuh), sedangkan korban yang sama dipukul **melee hero**
memantulkan 25% ke penyerang — tanpa pasangan ini absennya reflect bisa
saja cuma karena Bristleback tidak pernah aktif. Guard internal oracle
menolak: unit mati di skenario guard, reward tanpa kematian, counter
bergerak tanpa kematian, HP unit non-korban bergerak tanpa script, dan
`kills` hero naik di skenario peluru mana pun. Inventory item dibiarkan
kosong sehingga **tidak ada situs RNG sama sekali** (`roll_crit` berhenti
di `chance <= 0`; evasion/blind/block hanya roll saat peluangnya > 0) —
dua seed berbeda wajib identik. Snapshot dibandingkan rekursif
closed-world per langkah: gold/score/ai_gold/total_kills/max_combo/combo
(count/timer/last_combo)/red_towers_destroyed + per unit
`dead/hp/rewarded/team` + `hero_kills`. Snapshot PRA-serangan ikut
dibandingkan supaya kegagalan menunjuk ke setup, bukan ke dispatch.
Regenerasi fixture HANYA bila `_core.py`/`_entity.py`/`hero_items.py`
berubah.

`TacticalCommandsParityTest` memutar ulang **seluruh** seksi
`tactical_commands` (37 skenario, 112 langkah) pada node
Hero/Minion/Tower/Nexus/Boss Godot ASLI + `Main._tactical`
(`TacticalCommands.gd`, dibuat di `Main._ready` seperti `_ai`) +
`GameManager` sungguhan. Oracle TIDAK menjalankan `Game.update` penuh,
melainkan `TacticalCommandManager.update()` pygame yang di-step manual
per frame dengan unit betulan; Godot mereplay lewat jalur produksi yang
sama: `command_*` / `hold_*` / `update()` + `Hero.move_to` /
`follow_target` / `target` + `GameManager` (selected, state, wave,
`owned_heroes`, nexus). **Tidak ada** `register_*` manual dan **tidak
ada** set state taktik langsung — perintah/timer/cooldown/feedback/hold/
push/auto boleh berubah HANYA sebagai akibat produksi. Roll 20%
auto-attack-boss (satu-satunya situs RNG modul) di-script per skenario
lewat `ParityRng.begin/end` dan konsumsinya dibandingkan.

Skenario: gather eksplisit/default/avg-midmix/single-silent/tanpa-hero,
gate cooldown+state, push one-shot (jalur mati: visual 150f kedaluwarsa
sebelum timer 300) vs tanpa-arrival, protect tower (ancaman
rendah/tinggi/roster-kecil/auto-threatened/fallback-HP/hancur-pilih-ulang/
tanpa-target), protect castle (formasi+clamp/hancur), attack boss
(sukses/tanpa-boss), attack dealer (sukses + fokus pindah/tanpa-musuh),
HOLD tap-pendek vs potong-30, mismatch/idempotent/invalid,
follow-mouse + clamp-layar, armed-menunggu-boss (gagal-diam lalu loud
saat boss muncul), push-HOLD + kunci-target, helper count/nearest/
threatened/dealer, kedaluwarsa timer, auto castle/tower/swarm/boss-roll/
gagal-roll/wave-rendah, dan retreat-clear. Guard internal oracle menolak:
gate bocor, TAP-vs-HOLD tertukar, push tanpa arrival 60%, target salah,
timer negatif/tidak decay, auto salah kondisi, status/warna menyimpang,
dan konsumsi random ≠ script. Snapshot dibandingkan rekursif closed-world
per langkah: manager (20 key) + hero biru + semua unit + castle + game,
termasuk snapshot PRA-aksi. Regenerasi fixture HANYA bila
`tactical_commands.py`/`_core.py`/`_entity.py` berubah.

`TacticalInputParityTest` (FASE 18) memutar ulang seluruh seksi
`tactical_input` (17 skenario, 73 langkah) — bukan manajernya lagi,
melainkan **jalur input** yang sampai ke manajer. Oracle menjalankan
pygame ASLI: `Game.handle_key`/`handle_key_up` (hotkey G/F/T/C/B/D
termasuk cabang mouse-dalam-layar dan selected_tower), `SidePanel`
betulan (`_gambar_tactical` + `hit_test` dengan rect panel dipaksa
320 px di kanan arena — panel asli hanya ada di layar > 16:9) untuk
gate visibilitas/popup tombol, `mobile/hud.apply_hud_action` untuk
tekanan panel, dan pernyataan persis cabang release/pause `main.py`
untuk pelepasan. Godot mereplay lewat jalur produksi: InputEventKey →
`Main._unhandled_input` → `_on_key`/`_on_key_release`, tombol
`TacticalBar` HUD (`button_down` + rute pelepasan klik kiri), dan
`Main._tactical_release_all` untuk pause. Jejak `hold_start`/`hold_end`
(nama/args/follow_mouse/nilai balik) direkam lewat hook `hold_trace`
produksi di `TacticalCommands.gd` (pola `mouse_override`), lalu
dibandingkan persis — itulah bukti pemicu memanggil manajer dengan
argumen yang tepat. Regenerasi fixture HANYA bila `_core.py`
(InputHandler), `tactical_commands.py`, `mobile/sidepanel.py`, atau
`mobile/hud.py` berubah.

`TouchHudParityTest` (FASE 23, bukan oracle — data tombolnya sudah dikunci
`UiHudParityTest` vs fixture `touchhud`) menguji integrasi pada scene Main
asli: `hud_action` tersambung ke router, TouchHUD di atas ShopPanel +
AchievementPopup, geometri 7 tombol = kanon + hit ≥ 80 px, matriks 7 kunci
visibilitas, sembunyi di menu/pause, tap → signal (tombol sembunyi dan tanah
kosong diam), guard + jalur positif replay/next/menu/pause/skip/debug/back
lewat `_apply_touch_action`, dan override panel kanan (pause + FPS sembunyi
saat rail ada).

CI `godot-check.yml` memeriksa freshness fixture dan log runtime. Sukses berarti
ada penanda `PASS` **dan** tidak ada `SCRIPT ERROR`, `Parse Error`, atau
`Compile Error`; exit code Godot saja tidak cukup.

### Hasil validasi perubahan ini

- **FASE 18 — pemicu UI perintah taktis (PR ini):** oracle freshness lulus
  lokal dengan `/tmp/parity-venv/bin/python tools/test_godot_match_parity.py`
  (pygame-ce 2.5.8): seksi baru `tactical_input` berisi 17 skenario /
  73 langkah dengan 17 `hold_start` + 19 `hold_end` ter-rekam; dua seed
  berbeda identik dan seluruh guard internal oracle lulus. `--write-fixture`
  menghasilkan **6.359 baris insert-only** — semua seksi fixture lama
  byte-identik (0 delesi), tanpa perubahan kode runtime pygame (pygame
  satu-satunya sumber kebenaran; hanya tools/test_godot_match_parity.py
  yang bertambah), dan save pengguna tidak disentuh
  (`XDG_DATA_HOME=$(mktemp -d)`). Audit input menemukan tiga perilaku
  kunci yang dikunci eksplisit: (1) KEYUP taktis pygame TANPA gate state
  (saat victory KEYDOWN diam, KEYUP G tetap merutekan `hold_end(gather)` —
  no-op tapi terekam); (2) pergantian perintah di tengah cooldown
  MENGGANTI `held_command` walau penerbitan gagal (ret False — hold baru
  "dipersenjatai", ditemukan saat guard oracle pertama menolak asumsi
  ret True); (3) release panel yang datang setelah pause DIAM TOTAL
  (`held_tac` sudah di-clear, pop → None — bukan sekadar no-op
  `hold_end`). Perbaikan paritas sekaligus: B dihapus dari action
  `toggle_shop` Godot (H satu-satunya) karena oracle `ui_hud.hotkeys.b`
  pygame = `hold_start attack_boss` — asersi "B buka toko (ekstensi
  Godot)" di UiHudParityTest diganti paritas. Cek statis CI langkah 1
  lulus lokal: `gdparse` seluruh `.gd` (termasuk `TacticalBar.gd` +
  `TacticalInputParityTest.gd`), `tscn_lint` 29 scene (termasuk
  `TacticalInputParityTest.tscn`), `check_refs`, `particles_lint`
  (97 berkas), 5 self-test `godot_log_gate`, `gen_boss_smart_ai --check`,
  `gen_hero_skill_kit --check`, dan `check_bosskit_scope`. Langkah CI baru
  **4n** menjalankan `TacticalInputParityTest --quit-after 600` di
  user-data terisolasi melalui `godot_log_gate.py`.
  **Yang TIDAK terverifikasi lokal, eksplisit:** binary Godot 4.3 tidak
  bisa diperoleh di sandbox (release-assets.githubusercontent.com diblokir
  — sama seperti FASE 17), jadi `TacticalInputParityTest` sendiri maupun
  regresi seluruh daftar headless tidak dijalankan lokal — semuanya
  diverifikasi CI PR ini (`gh run watch --exit-status`). Tidak mengklaim
  pixel/audio parity (panel TacticalBar adalah aproksimasi visual),
  tidak mengklaim game 100% ekuivalen, dan tidak ada uji Android.

- **FASE 17 — perintah taktis:** oracle freshness lulus lokal
  dengan `/tmp/parity-venv/bin/python tools/test_godot_match_parity.py`
  (pygame-ce 2.5.8): seksi baru `tactical_commands` berisi 37 skenario /
  112 langkah (gather×47, protect_tower×15, protect_castle×6,
  attack_boss×6, attack_damage_dealer×4), 1 skenario push gather (HOLD),
  2 roll boss 20% ter-script; dua seed berbeda identik dan seluruh guard
  internal oracle lulus. `--write-fixture` menghasilkan **20.484 baris
  insert-only fixture + 988 baris oracle** — semua seksi fixture lama
  byte-identik (0 delesi), tidak ada perubahan kode runtime pygame, dan
  save pengguna tidak disentuh (`XDG_DATA_HOME=$(mktemp -d)`). Blok print
  `main()` menambah baris `tactical-commands oracle`. Audit menemukan dua
  perilaku kunci yang dikunci eksplisit: (1) push gather ONE-SHOT adalah
  jalur mati (`gather_point_timer` 150 kedaluwarsa sebelum
  `command_timer` sentuh 300 — push hanya hidup via HOLD
  `hold_elapsed >= 240`); (2) melee `range` pygame SELALU 70
  (normalisasi BALANCE PASS, `_entity.py:3305`) sehingga spread fokus
  attack_boss/dealer = 35+i·8 — cocok dengan `get_balanced_stats`
  Godot. Audit presisi membuktikan NOL flip batas desimal-4 antara
  float64 oracle dan float32 `Vector2` untuk seluruh titik spread.
  Cek statis CI langkah 1 lulus lokal: `gdparse` seluruh `.gd`
  (termasuk `TacticalCommands.gd` + `TacticalCommandsParityTest.gd` +
  `Hero.gd` + `Main.gd`), `tscn_lint` 28 scene (termasuk
  `TacticalCommandsParityTest.tscn`), `check_refs`, `particles_lint`
  (94 berkas), 5 self-test `godot_log_gate`, `gen_boss_smart_ai
  --check`, `gen_hero_skill_kit --check`, dan `check_bosskit_scope`.
  Langkah CI baru **4m** menjalankan
  `TacticalCommandsParityTest --quit-after 600` di user-data terisolasi
  melalui `godot_log_gate.py`.
  **Yang TIDAK terverifikasi lokal, eksplisit:** binary Godot 4.3 tidak
  bisa diperoleh di sandbox (release-assets.githubusercontent.com,
  downloads.godotengine.org, conda/ghcr/nix/nuget semuanya diblokir;
  kompilasi dari sumber tidak layak pada 2 CPU / 3 GB RAM), jadi
  `TacticalCommandsParityTest` sendiri **maupun regresi seluruh daftar
  headless tidak dijalankan lokal** — semuanya diverifikasi oleh CI PR
  ini (`gh run watch --exit-status`) dengan binary Godot 4.3 standar.
  Tidak mengklaim pixel/audio parity, tidak mengklaim game 100%
  ekuivalen, dan tidak ada uji Android.

- **FASE 16 — dispatch kematian terpusat (uji lanjut PR #193):** oracle
  freshness lulus lokal dengan `/tmp/parity-venv/bin/python
  tools/test_godot_match_parity.py` (pygame-ce 2.5.8): seksi baru
  `death_dispatch` berisi 21 skenario serangan nyata + 22 serangan
  (tower_bullet×8, hero_melee×4, hero_ranged×4, minion_attack×2,
  skill×2, direct×2), 16 kematian terbayar, 6 skenario guard tanpa
  kematian; dua seed berbeda identik dan seluruh guard internal oracle
  lulus. `--write-fixture` menghasilkan **3.039 baris insert-only** —
  semua seksi fixture lama byte-identik, tidak ada perubahan kode
  runtime pygame, dan save pengguna tidak disentuh
  (`XDG_DATA_HOME=$(mktemp -d)` + `MYSTIC_SAVE_DIR` sementara). Blok
  print `main()` menambah baris `death-dispatch oracle`. Cek statis CI
  langkah 1 lulus lokal: `gdparse` seluruh `.gd` (termasuk
  `DeathDispatchParityTest.gd`), `tscn_lint` 27 scene (termasuk
  `DeathDispatchParityTest.tscn`), `check_refs`, `particles_lint`
  (91 berkas), 5 self-test `godot_log_gate`, `gen_boss_smart_ai --check`,
  `gen_hero_skill_kit --check`, dan `check_bosskit_scope`. Langkah CI
  baru **4l** menjalankan `DeathDispatchParityTest --quit-after 600` di
  user-data terisolasi melalui `godot_log_gate.py`.
  Ronde CI pertama menemukan **tiga drift harness nyata** yang semuanya
  sudah diperbaiki (bukan dilonggarkan): (1) `Hero.__init__` menskala
  `base_hp`/`base_damage` lewat `hero_balance.starter_catchup_stats`
  dengan input `game_instance.purchased_heroes` (`_entity.py:3355-3360`) —
  `make_match_scoring_fixture` (FASE 13) membeli hero dan **tidak
  memulihkan** `__main__.game_instance`, sehingga di proses yang sama
  grimjaw lahir 1093/dmg 41 alih-alih 1120/42; kini `purchased_heroes`
  di-pin kosong di oracle dan `GameManager.purchased_heroes = []` di
  harness Godot; (2) `Hero._passive_heal` 0.15/frame (`_entity.py:3763-3766`)
  menggeser HP korban yang selamat tiap frame — dibekukan di oracle,
  paritas harness Godot yang men-`set_physics_process(false)` sehingga
  `PASSIVE_HEAL_PER_SEC` tidak jalan; (3) selisih 1 damage pada troll
  (763 vs 762) dan Thorne (1958 vs 1957) ternyata **gejala** dari (1),
  bukan bug mitigasi armor — hilang setelah catch-up di-pin. Setelah
  perbaikan, seluruh nilai yang di-flag CI cocok dengan keluaran Godot
  (h0 1120, m0 762, h0 486, h1 1957, attacker 1113, korban 471) dan
  perubahan fixture tetap **terkurung di seksi `death_dispatch`**
  (47 baris, semua ≥ baris 102801; seksi lain byte-identik).
  **Yang TIDAK terverifikasi lokal, eksplisit:** binary Godot 4.3 tidak
  bisa diperoleh di sandbox (release-assets.githubusercontent.com,
  downloads.godotengine.org, conda/ghcr/nix/nuget semuanya diblokir;
  kompilasi dari sumber tidak layak pada 2 CPU / 3 GB RAM), jadi
  `DeathDispatchParityTest` sendiri **maupun regresi FASE 13/14/15 dan
  seluruh daftar headless lainnya tidak dijalankan lokal** — semuanya
  diverifikasi oleh CI PR ini (`gh run watch --exit-status`) dengan
  binary Godot 4.3 standar. Tidak mengklaim pixel/audio parity, tidak
  mengklaim game 100% ekuivalen, dan tidak ada uji Android.

- **FASE 15 — reward kematian minion + menara:** oracle freshness lulus
  lokal: 20 skenario `Game.update` baru (dua seed berbeda identik),
  **semua seksi fixture lama byte-identik** (diff 6.538 baris
  insert-only); tidak ada perubahan kode runtime pygame atau save
  pengguna. `MinionTowerRewardParityTest` lulus **7.993 pemeriksaan**
  dengan Godot **4.3.stable.custom_build** headless lokal melalui gate
  log (PASS + tanpa script/parse/compile error). Ke-13 scene regresi
  lama juga PASS: Gameplay (1.455 checks), Battle, AIPlayer,
  Cinematic, BossCore (3.717), BossSmartAI, HeroSkill,
  HeroBasicAttack, HeroRngGuard, HeroCatchupUnlock, UiHud (1.159 —
  harness award_kill diganti register_*_death node asli),
  MatchScoring (901), BossDeathReward (39.729). `gdparse`, scene/ref/
  particle lint, dua generator `--check`, scope-check, 5 regresi
  log-gate, serta regresi pygame achievement-command, aura boss (46),
  basic-attack-no-impact, damage-school (36), dan easy-mode AI lulus.
  Engine lokal dibangun tanpa backend renderer karena unduhan binary
  diblokir sandbox. CI PR menjalankan binary Godot 4.3 standar,
  termasuk langkah baru `MinionTowerRewardParityTest --quit-after 600`
  di user-data terisolasi; checks CI wajib hijau sebelum squash-merge.
  Tidak mengklaim pixel/audio parity atau uji Android; gap dispatch
  kematian pre-existing didokumentasikan terbuka (bukan ranah fase ini).

- **FASE 14 — reward kematian boss:** oracle freshness lulus lokal:
  216 boss, 37 skenario `Game.update` (dua seed berbeda), 5 baterai
  antrean floating + 3 baterai FIFO bersama `DamageNumber`, 2 hasil
  akhir match (menang/kalah) dan reset. **Semua seksi fixture lama
  byte-identik**; tidak ada perubahan kode runtime pygame atau save
  pengguna. `BossDeathRewardParityTest` lulus **39.729 pemeriksaan**
  dengan Godot **4.3.stable.custom_build** headless lokal, melalui gate
  log (PASS + tanpa script/parse/compile error atau assertion FAIL).
  Ke-12 scene regresi lama juga PASS: Gameplay (1.455 checks), Battle,
  AIPlayer, Cinematic, BossCore (3.717), BossSmartAI, HeroSkill,
  HeroBasicAttack, HeroRngGuard, HeroCatchupUnlock (836), UiHud (1.159),
  MatchScoring (901). `gdparse`, scene/ref/particle lint, dua generator
  `--check`, scope-check, 5 regresi log-gate, serta regresi pygame
  achievement-command, aura boss (46), basic-attack-no-impact,
  damage-school (36), dan easy-mode AI lulus. Engine lokal dibangun
  tanpa backend renderer karena unduhan binary diblokir sandbox;
  pesan `No renderers available` bukan hasil audit piksel. CI PR
  menjalankan **binary Godot 4.3 standar**, termasuk langkah baru
  `BossDeathRewardParityTest --quit-after 600` di user-data terisolasi;
  checks CI wajib hijau sebelum squash-merge. Detail run ada pada
  checks PR FASE 14. Tidak mengklaim pixel/audio parity atau uji Android.

- Fixture Pygame dan pemeriksaan GDScript, scene/referensi, serta properti
  partikel lulus. Regresi aura boss, serangan dasar tanpa impact FX, dan AI
  easy-mode Pygame juga lulus.
- Godot 4.3: `GameplayParityTest` **1.453 pemeriksaan lulus**;
  `BattleSmokeTest`, `AIPlayerTest`, dan `CinematicTest` juga `PASS`, tanpa
  error script/kompilasi/animasi. `BossCoreParityTest` lulus di CI dengan
  3.717 pemeriksaan (data 216 boss + perilaku inti boss). Gate kini turut
  menolak animasi yang tidak ada dan body fisika yang belum terdaftar di
  space.
- Fase smart-AI: oracle Pygame `boss_smart_ai` lulus lokal
  (`tools/test_godot_match_parity.py` — 79 boss, 237 skenario, 3.867 event),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` lulus, plus scope
  checker lokal `tools/check_bosskit_scope.py` (mencegat kelas Parse Error
  "Identifier not declared" yang lolos gdparse). Replay Godot
  (`BossSmartAIParityTest`) diverifikasi lewat CI `godot-check.yml` pada PR —
  gate lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/
  `Compile Error`.
- Fase hero-skill kit: oracle `--check` lulus lokal (222 hero × 4 skenario,
  118.293 event — fixture = perilaku pygame hari ini, sisi pygame tidak
  disentuh), `gen_hero_skill_kit.py --check` dan `check_bosskit_scope.py`
  lulus, seluruh berkas ter-gate `gdparse` + `tscn_lint`/`check_refs`/
  `particles_lint` bersih. Replay `HeroSkillParityTest` (888 skenario penuh,
  driver `Hero.skill_test_step`) lulus di CI `godot-check.yml` run
  34178217267 — tidak ada Godot headless lokal di lingkungan kerja. Tiga
  beda semantik yang ditemukan CI dan dikunci regression test di harness yang
  sama: (1) compound-op field berunit (`h.speed *= 2.0` kit windrun sylara)
  kini diekspansi generator jadi WRITE(READ op val) sehingga px/frame ↔
  px/second round-trip tanpa faktor 60 ikut ter-skala; (2) buff speed melee
  mengikuti `round(x*1.18, 2)` PERSIS (pembulatan desimal dari nilai biner —
  khalros 1.25 → 1.47, bukan 1.48 ala round(147.5)); (3) key kit
  `_base_attack_cd` (backing attr properti `attack_cooldown` di `_entity.py`,
  satuan frame) dipetakan ke `hero.attack_cooldown×60` — Godot menyimpannya
  sebagai field detik di node, bukan entri kit.
- Engine lokal dibangun dari source untuk **headless saja**, tanpa backend
  Vulkan/OpenGL. Pesan engine `No renderers available` pada lingkungan ini
  adalah batasan build pengujian; hasil di atas **bukan** validasi gambar GPU,
  sentuhan perangkat, atau APK/AAB. CI memakai binary Godot standar.
- Fase audit basic hero: oracle `hero_basic_attack` lulus lokal
  (`tools/test_godot_match_parity.py` — 29 skenario × double-run seed beda,
  58 event HP + 3 probe, sisi pygame tidak disentuh), `gdparse`/`tscn_lint`/
  `check_refs`/`particles_lint` + `gen_*  --check` + scope-check lulus lokal.
  Tidak ada Godot headless lokal di lingkungan kerja — replay
  `HeroBasicAttackParityTest` (dan regresi lama lain) diverifikasi lewat CI
  `godot-check.yml` pada PR; gate lulus = penanda `PASS` dan tanpa
  `SCRIPT ERROR`/`Parse Error`/`Compile Error`.
- Fase catch-up unlocks (progresi, FASE 11): oracle `hero_catchup_unlocks`
  lulus lokal (10 isi save, 4 kasus save lama, 315 multiplier, 24 stat hero
  pygame; seksi lama fixture byte-identik — sisi pygame TIDAK disentuh),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` + `gen_* --check` +
  scope-check lulus lokal. Tidak ada Godot headless lokal di lingkungan
  kerja — replay `HeroCatchupUnlockParityTest` diverifikasi lewat CI
  `godot-check.yml` pada PR (langkah baru setelah `HeroRngGuardParityTest`);
  gate lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/
  `Compile Error`. Efek nyata: save dengan 6 hero non-starter membuat
  Kaizen mulai di 660 HP / 40 damage (bukan 770/45 seperti save baru),
  persis angka `Hero` pygame.
- Fase guard RNG (windrun/shadow realm): oracle `hero_rng_guards` lulus
  lokal (14 skenario × double-run seed beda, 58 event HP, 47 roll
  ter-script; seksi lama fixture byte-identik, sisi pygame tidak
  disentuh), `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` +
  `gen_* --check` + scope-check lulus lokal. Hook `ParityRng` dipasang
  di 4 titik roll (windrun/evasion-blind/block di `CombatSystem`,
  crit di `ItemInventory.roll_crit`) — tanpa begin() tetap `randf()`
  global. Tidak ada Godot headless lokal di lingkungan kerja — replay
  `HeroRngGuardParityTest` diverifikasi lewat CI `godot-check.yml`
  pada PR (langkah baru setelah `HeroBasicAttackParityTest`); gate
  lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/
  `Compile Error`.
- Fase klaster skor (FASE 13): oracle `match_scoring` lulus lokal
  (`tools/test_godot_match_parity.py` — 5 kasus combo, 9 skenario reward
  `Game.update` pygame asli × double-run seed beda, 9 kasus level-stats,
  3 kasus popup + 181 titik slide + 5 trigger NEW HERO; seksi lama
  fixture byte-identik — sisi pygame TIDAK disentuh),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` + `gen_* --check` +
  scope-check lulus lokal. Tidak ada Godot headless lokal di lingkungan
  kerja — replay `MatchScoringParityTest` (termasuk integrasi end_match
  penuh) diverifikasi lewat CI `godot-check.yml` pada PR (langkah baru
  setelah `UiHudParityTest`, `--quit-after 300`); gate lulus = penanda
  `PASS` dan tanpa `SCRIPT ERROR`/`Parse Error`/`Compile Error`.
  Efek nyata: kill hero merah kini +150 gold/skor (hero biru membayar
  AI), rantai kill minion merah menghidupkan combo kanan-atas
  (`x{n}` + label KILLING SPREE! dst + bar 2 detik), panel game-over
  menampilkan `Max Combo: x{n}` dan penanda `NEW BEST!` pada Final
  Score/Match Time saat rekor per level pecah (save `level_stats`), dan
  menang dengan boss baru memunculkan popup `NEW HERO UNLOCKED!`
  (antrean 3 detik, slide dari kanan).
- Fase UI/HUD in-match (FASE 12): oracle `ui_hud` lulus lokal (82 draw
  headless run pygame asli, 31 klik berurutan, 28 hotkey, 222 predikat
  hero, 121 titik banner, baterai format/touch; seksi lama fixture
  byte-identik — sisi pygame TIDAK disentuh),
  `gdparse`/`tscn_lint`/`check_refs`/`particles_lint` +
  `gen_* --check` + scope-check lulus lokal. `format_gold_rate`
  di-fuzz 200.000 nilai acak: 0 beda vs Python. Tidak ada Godot
  headless lokal di lingkungan kerja — replay `UiHudParityTest`
  (termasuk audit closed-world `ui_key` tiap layar toko)
  diverifikasi lewat CI `godot-check.yml` pada PR (langkah baru
  setelah `HeroCatchupUnlockParityTest`, `--quit-after 400`);
  gate lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/
  `Parse Error`/`Compile Error`.
gen_* --check` + scope-check lulus lokal. `format_gold_rate`
  di-fuzz 200.000 nilai acak: 0 beda vs Python. Tidak ada Godot
  headless lokal di lingkungan kerja — replay `UiHudParityTest`
  (termasuk audit closed-world `ui_key` tiap layar toko)
  diverifikasi lewat CI `godot-check.yml` pada PR (langkah baru
  setelah `HeroCatchupUnlockParityTest`, `--quit-after 400`);
  gate lulus = penanda `PASS` dan tanpa `SCRIPT ERROR`/
  `Parse Error`/`Compile Error`.
