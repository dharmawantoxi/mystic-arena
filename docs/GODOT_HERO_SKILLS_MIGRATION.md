# Migrasi `hero_skills/` → Godot (`godot_rebuild/`)

Status: **native GDScript + kontrak data tertutup, tanpa Python saat runtime**.
Melanjutkan pola `hero_items.py`, `hero_balance.py`, dan `bosses/`: Python tetap
menjadi oracle, sementara port ini **tidak** menambah skill, angka, cooldown,
atau efek baru. Tanggal migrasi: **2026-11-03**, branch
`arena/aba17c41-mystic-arena`.

## Cakupan

| Sumber Python / generator | Native Godot | Catatan |
|---|---|---|
| `hero_skills/__init__.py` (8 alias modul lama, 6 starter, auto-register boss) | `data/hero_skills.json` (`legacy_aliases`, `starters`, `auto_register`, `handler_map`) | 222 hero = 6 starter + 216 boss, tepat sama dengan `core_data.json`/`bosses.json`. |
| `hero_skills/_bundle.py` (8 kelas, 340 metode) | Kontrak `methods`, `registry`, `recipe_methods` | 66 resep boss-hero / 264 slot `q/w/e/r`, tanpa rebalance. |
| `BaseSkill.REQUIRE_TARGET`, `TARGET_RANGE_SLACK`, `_DEFAULT_VISUAL_DURATION` | `scripts/core/HeroSkills.gd` | Helper murni: `skill_range`, `target_reach`, `enemies_in_range`, `aoe_damage`, `cooldown_ready`, `trigger_plan`. |
| `_check_*_cooldown`, `_trigger_*_cooldown`, `_skill_range`, `_get_enemies_in_range`, `_deal_aoe_damage` | `tests/fixtures/hero_skills_parity.json` | Oracle dijalankan dari modul `_bundle.py` asli dengan stub `sound_manager`/`settings`. |
| `SKILL_VISUAL_DURATION` 6 starter + override `nyzrak`/`vhalzun` | Kontrak `visual_duration`, `boss_hero_visual_duration`, `default_visual_duration` | Timer visual tetap dalam frame, bukan detik. |
| `tools/gen_hero_skill_kit.py` + `tools/prepare_godot_entities.py` | `scripts/entities/generated/HeroSkillKit.gd` | 330 fungsi statis, 91 state key `h.kit`, SHA-256 `ddc43b0f7356…`; file tetap generated, tidak diedit manual. |
| `BattleUnit.kit_*` bridge | `BattleUnit.gd` + `HeroSkills.gd` | Combat/FX bridge tetap di `BattleUnit`; façade yang memanggil kit. |
| `cast_skill`, `init_state`, `update_timers` | `CoreData.skills`, `BattleUnit`, `EntityMovement` | Ketiganya kini lewat `HeroSkills.shared()`, bukan preload langsung ke generated kit. |

## Arsitektur runtime

```
hero_skills/ (oracle Python)
  ├── __init__.py  ─┐
  └── _bundle.py   ─┼─> tools/prepare_godot_hero_skills.py
                    │      ├── godot_rebuild/data/hero_skills.json
                    │      └── godot_rebuild/tests/fixtures/hero_skills_parity.json
                    │
tools/gen_hero_skill_kit.py + tools/prepare_godot_entities.py
  └── godot_rebuild/scripts/entities/generated/HeroSkillKit.gd

CoreData
  ├── ... (archetypes, balance, items, localization, bosses)
  └── skills: HeroSkills  ── validasi kontrak fail-closed

HeroSkills.shared()
  ├── kontrak/hash/registry/helper BaseSkill
  └── KIT.init_state / update_timers / cast_q|w|e|r

BattleUnit.setup_hero   -> HeroSkills.shared().init_state(self)
BattleUnit.cast_skill   -> HeroSkills.shared().cast(...)
EntityMovement._update_hero -> HeroSkills.shared().update_timers(...)
run_all.gd              -> SkillsParity.run(self)
```

`CoreData.new(...)` mendapat parameter opsional ketujuh `skills_path` **setelah**
`boss_path`; pemanggil 0/2/3/4/6 argumen lama tetap valid. `CoreData.valid()`
menolak kontrak skill yang hilang/rusak, sehingga game tidak diam-diam
berjalan tanpa registri skill.

## Kontrak data & tooling

```bash
# Setelah mengubah hero_skills/ atau generator kit:
python3 tools/prepare_godot_entities.py          # regenerasi HeroSkillKit.gd bila perlu
python3 tools/prepare_godot_entities.py --check
python3 tools/prepare_godot_hero_skills.py       # tulis kontrak + fixture oracle
python3 tools/prepare_godot_hero_skills.py --check
python3 tools/test_godot_hero_skills_prepare.py
python3 godot_rebuild/tests/validate_project.py
```

`prepare_godot_hero_skills.py` adalah exporter deterministik:

1. menolak perubahan dunia sumber (harus tepat `__init__.py` + `_bundle.py`);
2. menyimpan SHA-256 gabungan sumber, SHA-256 per file, SHA-256 tiga tool
   (`gen_hero_skill_kit.py`, `prepare_godot_entities.py`, exporter ini), dan
   SHA-256 `HeroSkillKit.gd` aktif;
3. memverifikasi byte generated kit sama persis dengan
   `prepare_godot_entities.kits()["HeroSkillKit.gd"]`;
4. menulis `data/hero_skills.json` dengan `schema=1`, 222 handler, 66 resep,
   264 slot resep, 91 state key, 330 fungsi statis, metode/bridge, dan helper
   `BaseSkill`;
5. menulis `tests/fixtures/hero_skills_parity.json` dari oracle Python:
   223 klasifikasi hero, 892 durasi visual, 868 slot resep, 16 cooldown,
   7 range, 3 geometri, 4 AoE, dan 37 trigger cooldown;
6. `--check` membandingkan byte JSON sort-key tanpa menulis; hash sumber,
   tool, generated kit, atau oracle yang basi membuat gate gagal.

SHA-256 kontrak saat migrasi: `ef42a57b7334…`; SHA-256 fixture oracle:
`cd9c87c13ce1…`. Float fixture dinormalisasi 12 desimal agar stabil lintas
CPython; kontrak sumber tetap exact.

## Integrasi CI

- `godot-check.yml` dan `godot-rebuild.yml` menambah path filter
  `hero_skills/**`, `tools/prepare_godot_hero_skills.py`,
  `tools/test_godot_hero_skills_prepare.py`,
  `godot_rebuild/scripts/core/HeroSkills.gd`, dan
  `godot_rebuild/tests/HeroSkillsParityTest.gd`.
- Kedua workflow menjalankan `python3 tools/prepare_godot_hero_skills.py --check`
  serta `python3 tools/test_godot_hero_skills_prepare.py` di dekat gate entity.
- `validate_project.py` mengunci hash sumber/tool/kit, cakupan 222/66/91/330,
  wiring `CoreData`/`BattleUnit`/`EntityMovement`, fixture oracle, pemanggilan
  `SkillsParity.run(self)`, dan perintah CI.
- `run_all.gd` memanggil `HeroSkillsParityTest.run()`; tes GDScript membandingkan
  kontrak, klasifikasi, durasi visual, resep, cooldown, range, geometri, AoE,
  trigger, wiring runtime, dan perilaku fail-closed loader.

## Rekonsiliasi klaim lama

Sebelumnya `godot_rebuild/README.md` menyatakan "skill/rig bespoke per hero/boss
belum diklaim parity", sementara header generated kit dan
`docs/GODOT_ENTITY_MIGRATION.md` menyebut transpile 1:1 serta regression lama
`godot/tests/HeroSkillParityTest.tscn`. Batasnya sekarang eksplisit:

- **Diklaim parity:** registri/handler, resep, durasi visual, konstanta dan
  helper `BaseSkill`, cooldown/range/geometri/AoE, serta dispatch runtime ke
  generated `HeroSkillKit.gd` melalui kontrak + oracle + `run_all.gd`.
- **Tidak diklaim parity:** rig/sprite/cinematic Pygame, fidelitas piksel FX,
  audio output, perangkat Android, Play Games, dan server top-up produksi.
- Header `HeroSkillKit.gd` masih menyebut scene legacy
  `godot/tests/HeroSkillParityTest.tscn`; itu artefak historis. Cakupan aktif
  adalah `godot_rebuild/tests/HeroSkillsParityTest.gd` dan workflow di atas.

## Batasan yang jujur

- Tidak ada skill, damage, cooldown, atau efek baru; semua berasal dari
  `hero_skills/` dan generated kit yang sudah ada.
- Implementasi Q/W/E/R bespoke tetap ada di `HeroSkillKit.gd`; `HeroSkills.gd`
  adalah façade kontrak/helper, bukan penulisan ulang 5.220 baris skill.
- Visual skill, popup, shake, dan suara diuji nilainya terhadap oracle, bukan
  kesamaan rendering/audio dengan Pygame.
- Headless tidak membuktikan GPU, Android, audio, Play Games, atau top-up
  produksi. Lihat `GODOT_HERO_SKILLS_VERIFICATION.md` untuk hasil uji aktual.
