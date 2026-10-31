# Perbaikan parse/compile Godot 4.7 (layer 9cq–9cr)

Godot **4.7.2** menolak memuat project dengan 40+ error, padahal `gdparse` dan `gdlint`
lulus untuk seluruh berkas. Penyebabnya: 4.7 menaikkan kelas peringatan tertentu menjadi
**error**, dan dua di antaranya (`INFERENCE_ON_VARIANT`, "cannot infer the type") hanya bisa
dilihat oleh *type checker* Godot — bukan oleh parser pihak ketiga.

Aturan yang dipakai untuk memilah setiap laporan user:

| Kelas error | Arti | Perbaikan yang dipakai di repo |
| --- | --- | --- |
| `The variable type is being inferred from a Variant value` | `var x := <ekspresi Variant>` | tulis tipe eksplisit (`var x: Vector2 = ...`) atau bungkus dengan cast (`String(...)`, `float(...)`, `int(...)`) |
| `Cannot infer the type of "x" variable` | ekspresi tidak punya tipe (Variant / fungsi tanpa `->`) | sama: anotasi eksplisit atau cast |
| `Could not find type "X" in the current scope` | skrip memakai namanya sendiri sebagai tipe tanpa `class_name` | tambah `class_name X` (atau hapus preload const yang membayangi kelas global) |
| `Expected loop variable name after "for"` | nama variabel loop adalah keyword GDScript | ganti nama (`class_name` → `suite_name`, `namespace` → `space_name`) |
| `There is already a variable named "x" declared in this scope` | variabel lokal membayangi lokal blok induk di fungsi yang sama | ganti nama variabel dalam (`box` → `measured`, `clamp` → `clamp_rows`) |
| `Invalid argument for "_ops_only()"` | fungsi builder mengembalikan Dictionary, bukan Array | normalisasi lewat helper `_dict_only()` |

## 1. Daftar perbaikan (12 titik, 11 berkas)

| Berkas | Baris | Penyebab | Perbaikan |
| --- | --- | --- | --- |
| `scripts/ui/ui_component_base.gd` | 82 | `measure.call(...)` menghasilkan Variant, memblok `tower_popup_layout.gd` → `prototype_view.gd` | `var metrics: Vector2 = measure.call(...)` (menerima `Vector2i` maupun `Vector2` lewat konversi implisit) |
| `scripts/combat/spatial_grid.gd` | 1 / 20 / 116 / 118 / 128 | memakai `SpatialGrid` sebagai tipe tanpa `class_name` → `shared()` tak teresolusi, ikut mematahkan `system_checks.gd` | tambah `class_name SpatialGrid` |
| `scripts/data/hero_archetypes.gd` | 534–535 | `floor()` bertipe `Variant` di `@GlobalScope` | `var lower: float = floor(value)`, `var fraction: float = value - lower` |
| `scripts/data/hero_balance.gd` | 571, 967 | `key2` adalah key Dictionary (Variant) → `key2.split("|")[0]` | `String(key2).get_slice("|", 0)` (semantik identik) |
| `tests/bosses_folder_checks.gd` | 154 | `parked[key]` indeks Dictionary | `var definition: Variant = parked[key]` |
| `tests/hero_skills_folder_checks.gd` | 181, 368 | `hero_id` Variant; `DEFINITIONS[boss_id]` Variant | `String(hero_id)`; `var definition: Variant = ...` |
| `tests/render_checks.gd` | 189, 302 | `for class_name in ...` (keyword); `clamp` dideklarasikan dua kali | `for suite_name in ...`; variabel kedua → `clamp_rows` |
| `tests/towers_checks.gd` | 211 | `for namespace in ...` (keyword) | `for space_name in ...` |
| `tests/sprite_lighting_checks.gd` | 394 | `var box` membayangi `box: Array` di fungsi yang sama | → `var measured` |
| `tests/system_checks.gd` | 26 | `const SpatialGrid = preload(...)` membayangi kelas global baru | const dihapus, kelas global dipakai langsung |
| `tests/ui_components_checks.gd` | 508 | `build(...)["buttons"]` Variant | `var registered: Dictionary = ...` |
| `tests/ui_theme_checks.gd` | 193, 197 | `screen_title_ops()` mengembalikan Dictionary, dibungkus `_ops_only(Array)` | helper baru `_dict_only(Dictionary)` |

## 2. Guard permanen: `tests/gdscript_type_guard.py`

Validator menjalankan pemindai ini untuk **seluruh** `scripts/`, `scenes/`, `tests/`, `app/`.
Tipe diresolusi **per fungsi** (parameter + lokal + anggota kelas), jadi `var state: Variant`
di satu fungsi tidak meracuni `state: Dictionary` di fungsi lain.

| Aturan | Yang dilaporkan |
| --- | --- |
| `callable-call` / `dictionary-get` | `var x := y.call(...)` / `var x := y.get(...)` |
| `variant-math` | `var x := floor(...)`, `round`, `ceil`, `abs`, `sign`, `min`, `max`, `clamp`, `wrap` |
| `untyped-func` | `var x := nama_helper(...)` di mana helper tidak mendeklarasikan `-> T` |
| `variant-receiver` | `var x := v.method(...)` ketika `v` bertipe Variant |
| `index-from-Array/Dictionary/Variant` | `var x := wadah[key]` untuk wadah tanpa tipe elemen |
| `index-from-call` | `var x := v.split(...)[0]` ketika `v` Variant |
| `keyword-loop-var` | `for class_name in ...` dan keyword lain |
| `duplicate-local` | lokal yang membayangi lokal blok induk dalam satu fungsi (blok *saudara* tetap boleh) |

`--self-test` menembakkan kedelapan aturan ke sampel rusak (8 temuan) dan memastikan sampel
yang sudah diperbaiki bersih (0 temuan). Validator memanggil `--self-test` plus `scan()`,
sehingga guard yang "lulus karena tidak menemukan apa-apa" tidak mungkin lolos diam-diam.

Hasil saat ini: `PASS: 8 rules fire on the broken sample, 0 on the fixed one` dan
`PASS: 0 typed-inference problems`.

## 3. Catatan soal "Unexpected NUL character"

Lima error `Unicode parsing error ... Unexpected NUL character` **bukan** dari berkas repo:

- pemindaian byte seluruh `godot_rebuild/` menemukan NUL hanya di berkas biner
  (`assets/**.png`, `assets/art/**.webp`) — itu wajar untuk format tersebut;
- tidak ada satu pun `.gd`, `.tscn`, `.tres`, `.json`, `.cfg` yang mengandung `\x00`.

Artinya Godot membaca berkas di luar repo (cache impor `.godot/`, atau buffer editor yang
belum disimpan). Langkahnya di PC: tutup editor, hapus `godot_rebuild/.godot/`, buka ulang
project. Kalau masih muncul, jalankan
`grep -rlIP '\x00' godot_rebuild --include=*.gd` untuk memastikan.

## 4. Batas bukti

Validator statis + dua guard + `gdparse`/`gdlint` **bukan** bukti parity dan bukan bukti
project bisa dijalankan: keduanya hanya membuktikan tidak ada lagi pelanggaran aturan yang
terdeteksi. Langkah verifikasi tetap: buka `godot_rebuild/` di Godot 4.7 lalu jalankan
`tests/run_all.gd` di PC/CI user.
