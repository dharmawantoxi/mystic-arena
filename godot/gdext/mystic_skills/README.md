# Mystic Skills GDExtension (godot++)

Port dari `hero_skills/_bundle.py` (Python, 5220 baris, 6 starter + 66 boss hero, 264+ cast methods) ke Godot C++ GDExtension.

## Tujuan

- **Paritas 1:1** dengan logic Python via transpiled `HeroSkillKit.gd` (5807 baris).
- **Performa native**: skill tick (`update_timers`) dan cast (`cast_q/w/e/r`) yang hot-path di `Hero.gd` berjalan di C++ (60 FPS, banyak unit).
- **Drop-in replacement**: `Hero.gd` tetap panggil `HeroSkillKit.xxx`, tapi via `HeroSkillKitLoader.gd` yang pilih GDExt kalau `mystic/skills/use_gdext_skills=true` dan `ClassDB.class_exists("MysticHeroSkills")`.

## Struktur

```
godot/gdext/mystic_skills/
  SConstruct                      # copy dari mystic_lighting, output ke ../../addons/mystic_skills/bin/
  src/
    register_types.h/cpp          # entry mystic_skills_library_init, MODULE_INITIALIZATION_LEVEL_SCENE
    hero_skills_processor.h/cpp   # class MysticHeroSkills : RefCounted, 7000+ baris, semua skill
godot/addons/mystic_skills/
  mystic_skills.gdextension       # entry_symbol = mystic_skills_library_init, reloadable=true
  bin/
    libmystic_skills.*.so/dll     # hasil build
godot/scenes/hero/
  HeroSkillKit.gd                 # generated 5807 baris (fallback GDScript, tetap ada)
  HeroSkillKitLoader.gd           # wrapper pilih GDExt vs GDScript
  Hero.gd                         # const HeroSkillKit = preload("...Loader.gd")
tools/
  gen_hero_skill_kit.py           # Python AST -> GDScript (existing)
  gen_hero_skills_cpp.py          # Python AST -> C++ GDExt (baru, 1500+ baris generator)
```

## API C++ (paritas dengan GDScript)

```cpp
class MysticHeroSkills : public RefCounted {
  static void init_state(Object* hero);
  static void update_timers(Object* hero, const Array& all_units, const Array& all_towers, const Array& all_bases);
  static bool cast_q/w/e/r(Object* hero, const Array& all_units, const Array& all_towers, const Array& all_bases);
  static String hero_kind(Object* hero);
  static int visual_duration(const String& hero_type, const String& key);
  static bool boss_generic(...);
  static bool by_pair0(Variant a, Variant b);
  static bool __by_pair0(Variant a, Variant b); // untuk Callable di Hero.gd
  // 200+ skill individu: grimjaw_cast_q, kaizen_cast_q, ... bosshero_cast_q_mana_break, ...
};
```

Helpers `get_*`/`set_*` mirror `Hero.gd` properties:
- `global_position` (Vector2) <-> `x`/`y` frame
- `move_speed` px/s <-> `speed` px/frame (`/60`, `*60`)
- `attack_cooldown` detik <-> frame (`*60`, `/60`)
- `kit` Dictionary untuk state non-inti (`rage_timer`, `vortex_x`, dll.)
- `kit_*` bridges: `kit_enemies`, `kit_skill_damage`, `kit_catalog_all`, `kit_hit`, `kit_slow`, `kit_lock`, `kit_atk_timer`, `kit_unit_alive`, `kit_has_*`, `kit_shake`, `kit_sound`, `kit_popup`, `kit_skill_proj`, `kit_fx_cast`, `kit_fx_impact`

## Build

```bash
cd godot/gdext/mystic_skills
git clone -b godot-4.3-stable https://github.com/godotengine/godot-cpp godot-cpp --depth 1
scons target=template_release -j4
scons target=template_debug -j4
# Output: godot/addons/mystic_skills/bin/libmystic_skills.<platform>.<target>.x86_64.so
```

Aktifkan di `project.godot`:

```ini
[mystic]
skills/use_gdext_skills=true
```

## Paritas Logic

- **Guard target**: `_has_target` pakai `skill_range` fallback 200 + `TARGET_RANGE_SLACK` 1.15, retarget ke nearest alive dalam reach.
- **Boss generic**: `cast_range = max(int(skill_range or 100), 140)` tanpa slack, sort nearby by distance dengan stable tie-break idx, fallback mult q1.0/w1.2/e1.5/r2.5 kalau tidak ada recipe.
- **Damage**: `_deal_aoe_damage` -> `int(skill_damage * multiplier)`, source=hero, school=dmg_school; single target cek alive; line/cone pakai proj + perp check; slow via `kit_slow` amount/duration frame; stun via `kit_lock` max(attack_timer, duration).
- **Cooldown trigger**: Q `skill_timer = skill_cooldown_max + active_skill q + shake 8 + sound 0.7`; W 5/0.6; E 6/0.7; R 15/1.0; boss generic shake 10/8/8/15.
- **Visual duration**: `DEFAULT_VISUAL_DURATION` q60/w90/e60/r100, override per hero (grimjaw q180/w90/e60/r90, kaizen q60/w90/e60/r100, sylara q180/w180/e150/r60, thorne q40/w100/e60/r120, vex q40/w100/e60/r80, zephyr q240/w180/e180/r240, nyzrak q50/w50/e70/r90, vhalzun q60/w80/e60/r100).

## Integrasi GDScript

`HeroSkillKitLoader.gd` cek `ProjectSettings.get_setting("mystic/skills/use_gdext_skills")` dan `ClassDB.class_exists("MysticHeroSkills")`. Kalau true, delegasikan ke `MysticHeroSkills`, kalau false ke `HeroSkillKit.gd` transpiled.

`Hero.gd`:

```gdscript
const HeroSkillKit = preload("res://scenes/hero/HeroSkillKitLoader.gd")
# ...
HeroSkillKit.init_state(self)
HeroSkillKit.update_timers(self, lists[0], lists[1], lists[2])
HeroSkillKit.cast_q(self, all_units, all_towers, all_bases)
```

`SkillBook.gd` tetap baca `hero.skill_timer`, `w_cooldown`, dll., tidak perlu ubah.

## Generator C++

`tools/gen_hero_skills_cpp.py` baca `hero_skills/_bundle.py` via `ast`, transpiles ke C++ dengan mapping:

- `h.x/y` -> `get_global_pos_x/y(h)` / `set_global_pos_x/y`
- `h.speed` px/frame <-> `move_speed` px/s *60
- `h.attack_cooldown` frame <-> detik /60
- `h.skill_damage` -> `kit_skill_damage(h)`
- `h.<state>` -> `get_kit_value(h, "<state>")` / `set_kit_value`
- `e.take_damage(d, team)` -> `kit_hit(h, e, d, team, src, school)`
- `e.apply_slow(a, f)` -> `kit_slow(h, e, a, f)`
- `e.attack_timer` -> `kit_atk_timer` / `kit_lock`
- `math.hypot`, `cos`, `sin`, `atan2`, `pi` -> `Vector2(...).length()`, `Math::cos`, `Math::sin`, `Math::atan2`, `Math_PI`
- `getattr(h, 'x', d)` -> `get_kit_value(h, "x", d)`
- `h.kit["key"]` -> `get_kit_value(h, "key")` / `set_kit_value`
- Tuple unpack `tx, ty = ...` -> `Array` + indexing `((Array)val)[0]`
- `for e in enemies` -> `for (int __i=0; __i<((Array)enemies).size(); ++__i) { Variant __v_e = ((Array)enemies)[__i]; Object* e = ... }`
- `Variant` arithmetic di-cast ke `(double)` untuk hindari ambiguous overload.

Hasil: `hero_skills_processor.h` 448 baris, `hero_skills_processor.cpp` 6748 baris, 200+ fungsi skill.

## Testing

- `python tools/gen_hero_skill_kit.py --check` — pastikan `HeroSkillKit.gd` tidak basi.
- `python tools/gen_hero_skills_cpp.py` — regenerasi C++ dari `_bundle.py`.
- Build GDExt dan aktifkan flag, lalu jalankan Godot arena, cek skill Q/W/E/R semua hero (6 starter + 66 boss) masih trigger, damage, slow, stun, FX sama.
- `HeroSkillKitLoader.is_using_gdext()` bisa dipakai untuk debug HUD.

## Catatan

- `godot-cpp` tidak di-commit, di-clone saat build (sesuai `.gitignore`).
- `addons/mystic_skills/bin/` berisi `.so`/`.dll` hasil build, di-ignore kecuali `.gitkeep`? Saat ini `.so` ter-build di CI? Kita commit `.gdextension` saja, bin di-build lokal.
- Paritas visual: `BOSS_HERO_VISUAL_DURATION` untuk nyzrak, vhalzun sudah di-hardcode di C++ `visual_duration()`.

## Lisensi

Mengikuti lisensi project utama Mystic Arena.
