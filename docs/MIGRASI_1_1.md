# Migrasi Godot ↔ Pygame 1:1 — Tanpa Ubah Pygame, Tanpa Cek Manual

> **Pygame adalah sumber kebenaran tunggal. Godot HANYA membaca, tidak pernah menulis Pygame.**

Dokumen ini menjelaskan bagaimana migrasi Godot dibuat **sama persis** dengan Pygame, sehingga Anda **tidak perlu memeriksa satu-satu secara manual** lagi.

## Masalah Lama

Sebelumnya migrasi Godot berbeda dari Pygame:
- Data hero/boss/level di-hardcode manual di Godot, bukan dari Pygame
- Visual unit masih prosedural, bukan bake dari renderer Pygame asli
- FX skill boss smart-AI hanya aproksimasi
- HUD pixel belum di-test
- Harus cek manual satu-satu, memakan waktu

## Solusi Baru: Single-Command Validator

Sekarang cukup **satu perintah** untuk memastikan semuanya 1:1:

```bash
python tools/migrate_parity_check.py
```

Atau yang lebih lengkap:

```bash
python tools/godot_pygame_sync.py
```

Output jika PASS:

```
🎉 SEMUA CEK LULUS — Migrasi Godot SAMA PERSIS dengan Pygame!
   Tidak perlu cek satu-satu manual lagi.
   Pygame tetap murni, Godot 1:1 dari Pygame.
```

### 7 Kategori Cek (1000+ Skenario)

| # | Kategori | Apa yang dicek | Skenario |
|---|----------|----------------|----------|
| 1 | **Pygame untouched** | Pygame tidak mengandung hack Godot | File inti _core.py, _entity.py, dll |
| 2 | **Data JSON fresh** | godot/data/*.json hasil converter, bukan manual | 14 file JSON |
| 3 | **Baked assets** | PNG dari renderer Pygame asli | 445 unit + 54 map |
| 4 | **Parity oracle** | Logic game Pygame vs fixture | 237 skenario + 222 hero×4 skill + 15 oracle tambahan |
| 5 | **Static Godot** | gdparse, tscn_lint, check_refs, dll | Semua .gd dan .tscn |
| 6 | **Constants parity** | Konstanta Godot = Pygame | FIRST_WAVE, RESPAWN, HUNT, AGGRO, RETREAT, dll |
| 7 | **Data from Pygame** | JSON valid dan jumlah benar | 222 hero, 216 boss, 54 level |

### Oracle Parity Detail (dari `tools/test_godot_match_parity.py`)

Oracle ini membaca **AST langsung dari Pygame** (`_core.py`, `_entity.py`, `bosses/base_boss.py`, `hero_skills/_bundle.py`) dan menghasilkan `godot/tests/fixtures/match_parity.json`:

- **Economy**: 54 level × 3 difficulty (STARTING_GOLD 350+100×level, GOLD_PER_SECOND 3+0.3×level, WAVE_INTERVAL 1500, SPAWN_DELAY 20)
- **Wave composition**: 50 komposisi dari NEXUS_WAVE_COMPOSITION (L1: goblin×3 ... L5: orc×2 undead troll goblin×2)
- **Minion/Nexus**: 25 kombinasi MINION_TYPES (goblin/orc/troll/undead/dark_rider hp/dmg/speed/range/cooldown/gold/radius/color)
- **Boss core**: 216 boss (MINI_BOSS_TYPES + TRUE_BOSS_TYPES, armor/magic_resist dari hero_archetypes.get_boss_resistances)
- **Boss smart-AI**: 79 boss dengan rantai `elif boss_type ==` di Boss.update
- **Hero skill**: 222 hero × 4 skill traces (118293 events)
- **Basic attack**: 29 skenario, 58 HP events
- **RNG guard**: 14 skenario, 58 HP, 47 roll ter-script
- **Item proc**: 18 skenario, 53 events, 24 roll
- **UI HUD**: 82 draw, 31 klik, 28 hotkey, 222 hero predikat
- **Catchup**: 10 save, 315 multiplier, 24 stat hero
- **Match scoring**: 5 combo, 9 reward, 9 level-stats, 181 slide
- **Boss death**: 216 boss, 37 Game.update, 5 antrean
- **Minion tower**: 20 skenario, 67 kematian, 134 gold popup
- **Death dispatch**: 21 skenario, 22 serangan, 16 kematian terbayar
- **Tactical commands**: 37 skenario, 112 langkah
- **Tactical input**: 17 pemicu UI, 73 langkah
- **Level select**: 9 kartu, 12 format_time, 13 format skor
- **Meta shop**: 222 katalog, 10 transaksi, 20 keputusan kartu
- **Save slots**: 8 migrasi, 9 save/load, 6 info slot, 17 format_playtime + 15 format_last_played

Semua ini **tanpa mengubah Pygame** — hanya membaca.

## Alur Data: Pygame → Godot (Read-Only)

```
Pygame (sumber kebenaran)
   │
   ├── _core.py (HERO_TYPES, MINION_TYPES, NEXUS_LEVELS, economy)
   ├── _entity.py (Hero, Minion, Tower, Nexus, RETREAT 0.20/0.80, HUNT 900, AGGRO 250)
   ├── bosses/boss_data.py (MINI_BOSS_TYPES, TRUE_BOSS_TYPES)
   ├── bosses/base_boss.py (smart-AI, ability cooldown)
   ├── hero_skills/_bundle.py (Q/W/E/R per hero, 222 hero)
   ├── heroes/_bundle.py (renderer prosedural 16k baris)
   ├── map_components/themes.py (54 tema map)
   │
   ▼
tools/convert_to_godot.py (READ-ONLY, tidak ada os.remove/shutil.move)
   │
   ├── godot/data/heroes.json (222)
   ├── godot/data/bosses.json (216)
   ├── godot/data/boss_stats_full.json (stat mentah untuk kit smart-AI)
   ├── godot/data/levels.json (54)
   ├── godot/data/hero_archetypes.json (222)
   ├── godot/data/items.json (33) + items_meta.json
   ├── godot/data/hero_levels.json (kurva level)
   ├── godot/data/towers.json (ARCHER/CANNON/ICE/MAGE + regen shield)
   ├── godot/data/nexus.json (NEXUS_LEVELS + castle shield)
   ├── godot/data/economy.json (gold/s, wave, minion_types)
   ├── godot/data/themes.json (54 palet)
   ├── godot/assets/units/*.png (445 PNG bake dari renderer asli)
   │    └── godot/data/baked_units.json (manifest: frame, anchor, fps, skill, rage)
   ├── godot/assets/maps/*.png (54 PNG bake dari MapRenderer)
   │    └── godot/data/map_bakes.json
   └── godot/assets/sounds/*.wav (copy dari assets/sounds/)
   │
   ▼
Godot (hanya membaca JSON/PNG, tidak pernah import Pygame)
   ├── scripts/autoload/GameManager.gd (economy, wave, respawn — paritas _core.py)
   ├── scenes/hero/Hero.gd (HUNT 900, AGGRO 250, RETREAT 0.20/0.80, heal 3.0*FPS)
   ├── scenes/boss/Boss.gd (armor/MR dari hero_archetypes, smart-AI dari BossKit.gd)
   ├── scenes/hero/HeroSkillKit.gd (generated dari hero_skills/_bundle.py)
   ├── scenes/boss/BossKit.gd (generated dari bosses/base_boss.py)
   ├── scripts/render/UnitSilhouette.gd (fallback kalau bake belum ada)
   └── tests/*.gd (21 parity test vs fixture)
```

**Prinsip:**
- `tools/convert_to_godot.py` cuma **MEMBACA** `import _core, bosses.boss_data`, lalu **MENULIS** `godot/data/*.json`. Tidak ada `os.remove`, tidak ada `shutil.move`.
- Pygame tidak pernah di-import oleh Godot.
- Semua visual bake memakai **renderer Pygame asli** sebagai sumber kebenaran (bukan port manual).

## Cara Pakai Harian

### Cek Parity (tanpa ubah apa pun)

```bash
python tools/migrate_parity_check.py
# atau
python tools/godot_pygame_sync.py
```

### Auto-Fix Data JSON dari Pygame (tanpa ubah Pygame)

Kalau data JSON drift (misal habis edit balance di Pygame):

```bash
python tools/migrate_parity_check.py --fix
# sama dengan:
# python tools/convert_to_godot.py
```

### Full Bake (kalau visual berubah)

```bash
# Data JSON saja (cepat, 2 detik)
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py

# Units PNG (lambat, 2-3 menit, 222 unit × 24 frame)
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py --units-png

# Maps PNG (sedang, 30 detik, 54 tema)
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py --maps-png

# Semua sekaligus
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py && \
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py --units-png && \
SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py --maps-png
```

### Generate Laporan

```bash
python tools/migrate_parity_check.py --report md
# → docs/MIGRASI_1_1_REPORT.md (laporan otomatis, bukan dokumen utama)
```

### Workflow Balance Baru

Setiap kali edit balance di Pygame:

```bash
# 1. Edit seperti biasa di Pygame
nano _core.py
# atau
nano hero_balance.py

# 2. Test Pygame dulu (wajib)
python main.py

# 3. Copy ulang ke Godot (1 perintah, tidak hapus apa pun)
python tools/convert_to_godot.py

# 4. Cek parity otomatis (tidak perlu cek manual satu-satu)
python tools/migrate_parity_check.py

# 5. Test Godot
godot godot/project.godot

# 6. Commit
git add _core.py godot/data/*.json
git commit -m "balance Kaizen hp 850→900 + sync godot data"
```

**Jangan edit `godot/data/*.json` manual** — nanti ketimpa pas convert. Sumber kebenaran tetap `*_core.py` + `heroes/` + `bosses/`.

## Apa yang Sudah Parity 1:1

### ✅ Data & Logic (100% parity, auto-tested)

- **Economy**: STARTING_GOLD 350, GOLD_PER_SECOND 3+0.3×level, DIFFICULTY_MULT, WAVE_INTERVAL 1500, SPAWN_DELAY 20, MAX_HEROES_OWNED 5
- **Minion**: 5 jenis (goblin/orc/troll/undead/dark_rider) hp/dmg/speed/range/cooldown/gold/radius/color + NEXUS_WAVE_COMPOSITION L1-L5
- **Tower**: 4 jalur (ARCHER/CANNON/ICE/MAGE) + regen shield (delay 120, rate 3.5) + HP regen
- **Nexus/Castle**: 5 level (4000-15000 HP, 35-95 dmg, 150-250 range, 45-35 cd) + shield (88% reduction, HP 100%, regen delay 120, rate 3.5)
- **Hero**: 222 hero, HUNT 900, AGGRO 250, RETREAT_BELOW 0.20/RETREAT_UNTIL 0.80, BASE_HEAL 3.0×FPS (180 HP/s di base) vs PASSIVE 0.15×FPS (9 HP/s luar), skill timers frame-based, auto-cast R>E(2+)>W(<40%)>Q
- **Boss**: 216 boss, armor/magic_resist dari hero_archetypes.get_boss_resistances (clamp armor 0..40, MR 0..0.45), ability cooldown/damage/range, gold_reward, smart-AI 79 boss
- **Skill**: 222 hero × 4 skill (Q/W/E/R) dari hero_skills/_bundle.py, skill_damage via property (amp item + skill_down tower), kit_hit/kit_slow/kit_lock parity
- **Items**: 33 items, 6 slot, flat cost, shop order, categories, skill amp, crit, lifesteal, cleave
- **Save**: NUM_SLOTS 3, LEGACY file mapping (user://mystic_save.json → backup .old), format_playtime/format_last_played UTC via _civil_from_days, backfill purchased_heroes
- **Tactical**: GATHER, PROTECT TOWER, PROTECT CASTLE, ATTACK BOSS, ATTACK DAMAGE DEALER — paritas _core.py
- **Match scoring**: combo, reward, level-stats, popup, NEW HERO trigger

### ✅ Visual (bake dari renderer Pygame asli, bukan port manual)

- **Hero/Boss**: 222 unit × 24 frame (idle 8 + walk 8 + attack 8) + skill q/w/e/r (6 frame/skill) + rage varian (drakar) — PNG strip dari HERO_RENDERERS/BOSS_RENDERERS via _call_renderer_on_canvas
- **Map**: 54 tema dari map_components/themes.py THEMES (forest/desert/ice/abyss + 50 lainnya) + bake MapRenderer._render_static_map (terrain+river+lane+decor+shop+wall) → 1280×720 PNG
- **Fallback**: UnitSilhouette.gd untuk unit yang belum ke-bake (prosedural sederhana, tapi logic tetap parity)

### ⚠️ Yang Masih Prosedural (acceptable, logic tetap parity)

- **Minion/Tower/Nexus visual**: masih UnitSilhouette/prosedural, belum bake PNG (tapi stat dan logic 100% parity, hanya visual yang beda)
- **FX boss smart-AI**: callout + ring, aproksimasi (logic damage/heal/slow parity, visual FX tidak 1:1 pixel)
- **HUD pixel**: belum screenshot-test (logic dan layout parity, pixel belum)
- **Cloud save**: sengaja tidak diport (Pygame pakai cloud, Godot pakai local slot — fitur berbeda, bukan bug)

## Cara Kerja Bake Visual (Kenapa 1:1)

### Hero/Boss Bake

Bake memakai **renderer Pygame asli** sebagai sumber kebenaran:

1. Probe entity dibuat (`_ProbeEntity`) dengan stat asli dari boss_data
2. Renderer dipanggil via choke point yang sama dengan game: `_call_renderer_on_canvas` (heroes/__init__.py:1729)
3. Pose:
   - idle/walk: `pulse = (k+0.5)/2.0` → `fase = int(pulse*2.0) % 8` (HERO_ANIM_PHASES = 8, heroes/__init__.py:1483)
   - walk: probe digeser 1.4 px/frame (> ambang 0.3 px, bosses/level1.py:947-962)
   - attack: mode manual preview (`_gnk_attack_active=True + _gnk_attack_progress=p`, bosses/level1.py:873-880)
4. Crop bbox alpha>=8, anchor kaki di tengah kanvas 512
5. Strip: grid 8 frame per baris (bukan 1 baris panjang, aman untuk GPU mobile 4096 px)
6. PNG: palet 256 warna + alpha fix (<16 → 0, untuk hindari halo kotak)

Hasil: **geometri/warna/pose identik** karena melewati renderer yang sama dengan game.

### Map Bake

Bake memakai **MapRenderer pygame asli**:

1. `MapRenderer(surface, theme_name=name)._render_static_map()` — 6 layer (terrain+details, river, 3 lane, dekor seed(42), shop, border wall) dalam urutan yang persis sama dengan game
2. Determinisme: `random.seed()` tanpa argumen di map_components/_bundle.py:4889/5074 dibekukan ke seed tetap (MAP_BAKE_SEED=20260907)
3. PNG: 1280×720 opaque, palet 256 warna

Hasil: **map identik** dengan game Pygame.

## Testing

### Pygame Oracle (tanpa Godot binary)

```bash
# Install pygame-ce sementara
python3 -m venv /tmp/venv-test
/tmp/venv-test/bin/pip install 'pygame-ce==2.5.*' -q

# Jalankan oracle (hasil: godot/tests/fixtures/match_parity.json)
SDL_VIDEODRIVER=dummy /tmp/venv-test/bin/python tools/test_godot_match_parity.py
# Output: PygameMatchParity PASS: 54 levels, 50 wave compositions, 25 minion/nexus, 216 boss-core, 79 smart-AI, 222 hero×4 skill, dll
```

### Godot Parity Tests (butuh Godot 4.3+)

Godot membaca fixture JSON dan membandingkan logic-nya:

```bash
godot --headless --path godot --script res://tests/GameplayParityTest.gd
# 21 test: GameplayParityTest, BossCoreParityTest, BossSmartAIParityTest, HeroSkillParityTest, dll
```

### Full Pipeline (tanpa Godot binary, cuma Python)

```bash
python tools/godot_pygame_sync.py
# 7 kategori, 1000+ skenario, 0 drift = PASS
```

## FAQ

**Q: Apakah `godot/data/heroes.json` duplikat `hero_archetypes.json`?**
A: Duplikat sengaja (snapshot). Godot butuh JSON statis tanpa import Python. Converter menggabungkan HERO_TYPES + archetypes jadi satu.

**Q: Kaizen di Godot kok 25 tulang, di pygame tidak ada tulang?**
A: Pygame gambar pakai `pygame.draw.polygon` procedural, tidak ada konsep tulang. Godot mengubahnya jadi BakedSprite (PNG strip) — pose busur `ATTACK_ARC_START=-2.30 sweep -3.05` diambil 1:1 dari kode pygame, jadi animasi tetap identik tapi sekarang GPU-interpolasi.

**Q: Bagaimana kalau saya hapus `godot/` apakah pygame rusak?**
A: Tidak. `godot/` tidak pernah di-import oleh `main.py`, `_core.py`, atau `buildozer.spec`. Hapus folder `godot/` → `python main.py` tetap jalan.

**Q: Data 222 hero → 216 boss → 54 level, kok bisa beda?**
A: 222 hero = semua playable (termasuk boss-hero). 216 boss = mini+boss sejati (filter `boss_class`). 54 level = `levels.level_data.ALL_LEVELS`.

**Q: Kenapa visual minion/tower/nexus masih prosedural, bukan bake?**
A: Prioritas bake adalah hero/boss (222 unit) yang punya renderer kompleks 16k baris. Minion/tower/nexus visual-nya sederhana (kotak/lingkaran), jadi UnitSilhouette fallback sudah cukup parity untuk logic. Bake mereka bisa ditambah nanti kalau mau 100% pixel parity, tapi logic sudah 100% parity.

**Q: Saya edit balance di Pygame, Godot kok tidak berubah?**
A: Jalankan `python tools/convert_to_godot.py` untuk copy ulang, lalu `python tools/migrate_parity_check.py` untuk verifikasi.

**Q: Tool bilang FAIL, apa yang harus dilakukan?**
A: Lihat kategori mana yang FAIL:
- Data JSON fresh FAIL → `python tools/convert_to_godot.py`
- Baked assets FAIL → `SDL_VIDEODRIVER=dummy python tools/convert_to_godot.py --units-png --maps-png`
- Parity oracle FAIL → cek apakah Pygame diubah? Harusnya tidak. Laporkan bug.
- Static Godot FAIL → `gdparse`, `tscn_lint`, `check_refs`, `gen_* --check` — fix file .gd/.tscn yang error.

## Checklist 1 Halaman (tempel di dinding)

- [ ] `python tools/migrate_parity_check.py` → 7 PASS
- [ ] `python main.py` → pygame jalan
- [ ] `godot godot/project.godot` → F5 main → hero/boss pakai bake PNG
- [ ] `git status` → hanya `?? godot/` dan `?? tools/`, tidak ada `D heroes/`
- [ ] Edit balance → re-run converter → `migrate_parity_check.py` PASS → commit

Selesai — Anda punya **dua engine hidup berdampingan**, migrasi **1:1 tanpa cek manual satu-satu**, Pygame tetap murni.
