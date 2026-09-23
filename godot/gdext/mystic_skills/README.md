# Mystic Skills GDExtension (godot++)

Port `hero_skills/_bundle.py` (Python, 5.221 baris: `BaseSkill` + 6 starter +
`BossHeroSkills` 270 `_cast_*` + `_SKILL_REGISTRY` 66 boss) ke Godot C++
GDExtension.

Dokumen desain + daftar bug paritas yang diperbaiki:
[`docs/AUDIT_ULANG_DARI_AWAL.md`](../../../docs/AUDIT_ULANG_DARI_AWAL.md).
Status paritas menyeluruh: [`docs/AUDIT_ULANG_DARI_AWAL.md`](../../../docs/AUDIT_ULANG_DARI_AWAL.md)
(FASE 33).

## Tujuan

- **Paritas 1:1** dengan Python — C++ dibangkitkan dari AST `_bundle.py` yang
  sama dengan `HeroSkillKit.gd` (GDScript), bukan ditulis/diterjemahkan tangan.
- **Performa native** untuk hot-path: `update_timers` (tiap frame × tiap hero)
  dan `cast_q/w/e/r` (menelusuri unit/tower/base lawan).
- **Drop-in**: `Hero.gd` tetap memanggil `HeroSkillKit.*`; yang berganti hanya
  backend di balik `HeroSkillKitLoader.gd`.

## Struktur

```
godot/gdext/mystic_skills/
  SConstruct                        # output -> ../../addons/mystic_skills/bin/
  src/register_types.{h,cpp}        # entry mystic_skills_library_init (level SCENE)
  src/hero_skills_processor.h       # GENERATED — class MysticHeroSkills : RefCounted
  src/hero_skills_processor.cpp     # GENERATED — 432 definisi (helper + 6 starter + 66 boss)
godot/addons/mystic_skills/
  mystic_skills.gdextension         # kunci debug/release -> berkas template_debug/template_release
  bin/libmystic_skills.*            # hasil build (di-gitignore kecuali .gitkeep)
godot/scenes/hero/
  HeroSkillKit.gd                   # GENERATED — fallback GDScript (tetap ada, jalur default)
  HeroSkillKitLoader.gd             # saklar backend (+ force_backend untuk harness)
  Hero.gd                           # const HeroSkillKit = preload("...Loader.gd")
godot/tests/HeroSkillGdextParityTest.{gd,tscn}   # oracle Pygame dilewatkan ke C++
tools/gen_hero_skill_kit.py         # Python AST -> GDScript (+ --check)
tools/gen_hero_skills_cpp.py        # Python AST -> C++ (+ --check)
.github/workflows/godot-gdext.yml   # build lib + uji paritas C++
```

`src/*.h` dan `src/*.cpp` adalah **hasil generate** — jangan disunting tangan.
Ubah `tools/gen_hero_skills_cpp.py`, lalu:

```bash
python3 tools/gen_hero_skills_cpp.py          # regenerasi
python3 tools/gen_hero_skills_cpp.py --check  # CI: berkas ter-commit harus identik
```

## Build

```bash
cd godot/gdext/mystic_skills
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot-cpp   # di-gitignore
scons platform=linux   target=template_debug   -j4     # dev / editor
scons platform=linux   target=template_release -j4     # export release
scons platform=android target=template_release android_arch=arm64v8 -j4
```

Versi godot-cpp **harus** se-minor dengan engine (`compatibility_minimum = 4.3`
↔ branch `godot-4.3-stable`) — ABI GDExtension berubah antar minor.

Hasil (linux x86_64):

```
godot/addons/mystic_skills/bin/libmystic_skills.linux.template_debug.x86_64.so
```

### Nama berkas ≠ kunci target

`.gdextension` memakai **kunci target Godot** (`debug`/`release`/`editor`) tapi
**nilai**nya nama berkas hasil scons yang memakai **target godot-cpp**
(`template_debug`/`template_release`):

```ini
linux.debug.x86_64   = "res://addons/mystic_skills/bin/libmystic_skills.linux.template_debug.x86_64.so"
linux.release.x86_64 = "res://addons/mystic_skills/bin/libmystic_skills.linux.template_release.x86_64.so"
```

`libmystic_skills.linux.debug.x86_64.so` tidak pernah dihasilkan scons — kalau
itu yang ditulis, engine tidak pernah memuat lib dan diam-diam jatuh ke
GDScript (persis kondisi repo sebelum FASE 33). Arch Android di kunci juga
`arm64`/`arm32`/`x86_64` (nama arch Godot), bukan `arm64v8`/`armeabi-v7a` (nama
`android_arch` scons).

Verifikasi cepat tanpa engine:

```bash
nm -D --defined-only godot/addons/mystic_skills/bin/libmystic_skills.linux.template_debug.x86_64.so \
  | grep mystic_skills_library_init
```

Compile-check tanpa build godot-cpp penuh (butuh `gen/include` hasil generator):

```bash
g++ -fsyntax-only -std=c++17 -DGDEXTENSION \
  -I godot-cpp/gdextension -I godot-cpp/include -I godot-cpp/gen/include \
  -I src src/hero_skills_processor.cpp
```

## Mengaktifkan

`godot/project.godot` (default **false** — produksi masih GDScript):

```ini
[mystic]
skills/use_gdext_skills=true
```

Atau paksa dari kode (dipakai harness paritas):

```gdscript
HeroSkillKitLoader.force_backend("gdext")   # "gdscript" | "" = ikut setting
print(HeroSkillKitLoader.backend_name())    # "gdext" / "gdscript"
```

## API C++

Semua method di-bind `ClassDB::bind_static_method` pada `MysticHeroSkills`
(`RefCounted`). Yang dipakai `Hero.gd` / loader:

```cpp
static void   init_state(Object* hero);
static void   update_timers(Object* hero, const Array& all_units, const Array& all_towers, const Array& all_bases);
static bool   cast_q/cast_w/cast_e/cast_r(Object* hero, const Array&, const Array&, const Array&);
static String hero_kind(Object* hero);                 // 6 starter | "boss"
static bool   __by_pair0(Variant a, Variant b);        // Callable sort: (dist, idx)
static int    visual_duration(const String& hero_type, const String& key);
```

Sisanya (helper `BaseSkill`, 270 `_cast_*`, `boss_generic`, `fallback_cast`,
`registry_dispatch`, jembatan `kit_*`) internal — dipanggil dari dalam lib.

Helper `get_*`/`set_*` memetakan properti `Hero.gd`:

- `global_position` (Vector2) ↔ `x`/`y` pygame
- `move_speed` px/detik ↔ `speed` px/frame (`/60`, `*60`)
- `attack_cooldown` detik ↔ frame (`/60`; arah baca **dibulatkan** — GDScript `int(roundf(ac * 60))`)
- `kit` Dictionary untuk state non-inti (`rage_timer`, `vortex_x`, `_q_stack`, …)
- jembatan `kit_*`: `kit_enemies`, `kit_skill_damage`, `kit_catalog_all`,
  `kit_hit`, `kit_slow`, `kit_lock`, `kit_atk_timer`, `kit_unit_alive`,
  `kit_has_*`, `kit_shake`, `kit_sound`, `kit_popup`, `kit_skill_proj`,
  `kit_fx_cast`, `kit_fx_impact`

Objek yang sudah `free()` aman: `Variant::operator Object*()` me-resolve
ObjectID dan memberi `nullptr`, jadi `if (tgt && ...)` setara
`is_instance_valid(tgt)` di GDScript.

## Pemetaan transpiler (Python → C++)

| Python | C++ |
|---|---|
| `h.x` / `h.y` | `get_global_pos_x/y(h)`, `set_global_pos_x/y` |
| `h.speed` (px/frame) | `get_speed_frames` / `set_speed_frames` (↔ `move_speed` px/detik) |
| `h.attack_cooldown` (frame) | `get/set_attack_cooldown_frames` (↔ detik, baca dibulatkan `round`) |
| `h.skill_damage` | `kit_skill_damage(h)` |
| `h.<state>` non-inti / `getattr(h, k, d)` | `get_kit_value(h, "k"[, d])` / `set_kit_value` |
| `e.take_damage(d, team, …)` | `kit_hit(h, e, d, team, src, school)` |
| `e.apply_slow(a, f)` / `_apply_stun` | `kit_slow` / `kit_lock` |
| `e.attack_timer` baca | `kit_atk_timer` / `kit_has_atk_timer` |
| `e.attack_timer = max(e.attack_timer, N)` (74 situs) | `kit_lock(h, e, frames)` — `Hero.kit_lock` memakai `maxf` |
| `e.attack_timer = N` assign langsung (1 situs: Sylara shackle) | `set_atk_timer_frames(h, e, frames)` — tulis `frames / 60.0` apa adanya |
| `math.hypot/cos/sin/atan2/pi` | `Vector2(..).length()`, `Math::cos/sin/atan2`, `Math_PI` |
| `for e in enemies` | loop indeks atas `Array` + `Object::cast_to<Object>` |
| `a or b`, truthiness | `py_or`, `truthy` (semantik Python per tipe Variant) |
| tuple unpack `tx, ty = …` | `Array` + `((Array)v)[0]` |
| `nearby.sort(key=lambda t: t[0])` | insertion sort kunci `(dist, idx)` — **stabil** |
| `catalog[type]["damage"]` (index berantai) | `dict_at(dict_at(catalog, type), "damage")` — `.get()` const; `Dictionary::operator[]` non-const memanggil `ptrw()` (detach COW) dan menyisipkan NIL kalau key tidak ada |
| `int(x)` / `float(x)` / arithmetic atas Variant | `var_int(x)` / `var_num(x)` — deterministik untuk NIL (0), bukan `(double)(Variant)` yang membiarkan buffer tak terinisialisasi kalau `to_type_constructor` gagal |
| `self._get_visual_duration(k)` | `visual_duration_kind("{kind}", get_hero_type(h), k)` |
| aritmetika Variant | cast `(double)` eksplisit (hindari overload ambigu) |

## Paritas

Dikunci tiga lapis (rincian di `docs/AUDIT_ULANG_DARI_AWAL.md`):

1. **Oracle Pygame** — `HeroSkillGdextParityTest` memaksa backend `gdext` lalu
   memutar ulang `match_parity.json["hero_skills"]` (direkam dari `Hero.update`
   pygame ASLI: 222 hero × 4 skenario, jejak event per frame + state final).
   Kalau lib tidak termuat, test **GAGAL** (bukan skip).
2. **A/B backend** — `hero_kind()` + `visual_duration(q/w/e/r)` C++ vs GDScript
   untuk seluruh `hero_type` katalog, plus tie-break `__by_pair0`.
3. **Kesegaran transpile** — `gen_hero_skills_cpp.py --check` +
   `gen_hero_skill_kit.py --check` di `godot-check.yml` (statis) dan
   `godot-gdext.yml` (sebelum build).

Angka kunci yang harus tetap sama (audit vs `HeroSkillKit.gd`):
guard target `skill_range` fallback 200 + `TARGET_RANGE_SLACK` 1.15;
`cast_range` boss `max(int(skill_range or 100), 140)` **tanpa** slack;
damage `int(skill_damage * mult)` dengan `src = hero`, `school = dmg_school`;
cooldown trigger Q `skill_cooldown_max` + shake 8 + sound 0.7, W 5/0.6,
E 6/0.7, R 15/1.0, boss-generic shake 10/8/8/15;
`DEFAULT_VISUAL_DURATION` q60/w90/e60/r100 + override per kelas
(grimjaw q180/w90/e60/r90, kaizen q60/w90/e60/r100, sylara q180/w180/e150/r60,
thorne q40/w100/e60/r120, vex q40/w100/e60/r80, zephyr q240/w180/e180/r240)
+ `BOSS_HERO_VISUAL_DURATION` (nyzrak q50/w50/e70/r90, vhalzun q60/w80/e60/r100)
— semuanya **dibangkitkan dari tabel Python**, bukan angka yang disalin tangan.

## Testing

```bash
python3 tools/gen_hero_skill_kit.py --check
python3 tools/gen_hero_skills_cpp.py --check
scons platform=linux target=template_debug -j4
godot --headless --path godot res://tests/HeroSkillGdextParityTest.tscn --quit-after 900
godot --headless --path godot res://tests/HeroSkillParityTest.tscn --quit-after 900  # baseline GDScript
```

CI: `.github/workflows/godot-gdext.yml` (build lib + kedua test di atas,
godot-cpp di-cache per commit SHA). `godot-check.yml` tetap menjalankan baseline
GDScript **tanpa** compiler, jadi PR yang tidak menyentuh C++ tidak membayar
biaya build.

## Catatan

- `godot-cpp/` tidak di-commit (`.gitignore`) — di-clone saat build, di-cache CI.
- `addons/mystic_skills/bin/*.so|*.dll|*.framework` tidak di-commit; hanya
  `.gdextension` + `.gitkeep`.
- `reloadable = true`: hot-reload editor tanpa restart. Loader menyimpan
  `Object` instance (bukan pointer C++), jadi unload/reload aman.
- Android: `.gdextension` sudah memuat kunci `arm64`/`arm32`/`x86_64`, tapi
  `build-android-godot.yml` belum memanggil scons — export AAB jalan dengan
  fallback GDScript sampai build native ditambahkan.

## Lisensi

Mengikuti lisensi project utama Mystic Arena.
