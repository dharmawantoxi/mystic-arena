# Migrasi `_entity.py` ke Godot 4

Tanggal: 2026-11-01. Branch: `arena/597c5816-mystic-arena`.

## Ruang lingkup

Permintaan pengguna adalah **semuanya**: gameplay entity, projectile, AI, dan
visual entity. Port ini memindahkan aturan `_entity.py` ke GDScript native di
`godot_rebuild/`, bukan menjalankan Python di dalam Godot. Sumber Python tetap
disimpan sebagai referensi parity dan generator.

## Arsitektur native

| Modul | Tanggung jawab |
|---|---|
| `scripts/core/BattleUnit.gd` | State unit, stat hero/minion/tower/castle/boss, damage school, shield, debuff, respawn, jembatan kit Q/W/E/R dan boss. |
| `scripts/core/MatchModel.gd` | Loop 60 Hz, reward, wave, projectile/effect/popup, AI match, tactical command. |
| `scripts/entities/EntityCombat.gd` | Resolusi school damage, armor/MR, evasion/blind/true-strike, block, Bristleback, boss resilience/per-hit cap. |
| `scripts/entities/EntityProjectiles.gd` | Peluru tower homing (normal/cannon/ice/mage) dan projectile hero ranged/skill, splash/burn/slow/anti-heal/skill-down. |
| `scripts/entities/EntityMovement.gd` | Prioritas hero (retreat/heal, tactical, destination, follow, attack, hunt, push), minion tier 1–5, pathing, boss entrance/enrage/cleave. |
| `scripts/entities/EntityAI.gd` | Port `AIPlayer`: draft hero, reserve gold, build/upgrade tower, item, shield, nexus, lane assignment, scaling level 1–54. |
| `scripts/entities/EntityItems.gd` | Timer/auto-trigger item dan on_attack chain/cleave/proc dari katalog `hero_items`. |
| `scripts/entities/EntityVisuals.gd` | Renderer sprite-strip hasil bake: hero/boss idle/walk/attack/skill, minion, tower per level, nexus per level, projectile, effect, popup. |
| `scripts/entities/generated/HeroSkillKit.gd` | Hasil transpile `hero_skills/_bundle.py` oleh `tools/gen_hero_skill_kit.py`. |
| `scripts/entities/generated/BossKit.gd` | Hasil transpile smart-AI `bosses/base_boss.py` oleh `tools/gen_boss_smart_ai.py`. |

### Data dan aset

- `tools/prepare_godot_entities.py` menghasilkan/memverifikasi kit GDScript dan
  manifest sprite. `--check` gagal bila kit stale; `--bake` menjalankan exporter
  pygame-ce/Pillow/numpy dengan `MYSTIC_GODOT_ROOT` menunjuk ke `godot_rebuild/`.
- `data/baked_units.json`: 222 strip hero/boss, 8 frame idle/walk/attack, skill
  pose, anchor, skala, FPS, dan rage strip. SHA-256 kit: `9cba05ebd821`.
- `data/baked_props.json`: 10 minion, 8 tower bertingkat, 2 nexus; 538 frame.
- `assets/units/` dan `assets/props/` berisi PNG hasil bake (~17.3 MB total).
- `tools/convert_to_godot.py` sekarang menghormati `MYSTIC_GODOT_ROOT` sehingga
  bake dapat menulis ke proyek native tanpa mengubah folder legacy `godot/`.

### Kontrak jembatan kit

`BattleUnit` sengaja memakai satuan frame seperti Pygame. Properti kompatibilitas
(`hero_type`, `range`, `move_speed`, `attack_cooldown_seconds`, `skill_timer`,
`w/e/r_cooldown`, `skill_data`) memetakan API generator ke state native. Method
`kit_*` meneruskan damage, slow, lock, projectile, popup, shake, dan FX ke
`MatchModel`/`EntityProjectiles`/`EntityVisuals`. Boss memakai `kit_get_stats()`
untuk skill-down/enrage scaling dan `kit_stats_full()` untuk data mentah.

## Yang sudah diuji native

- Normalisasi hero melee/ranged dan inisialisasi kit.
- Projectile hero bergerak dan mengenai target; bullet tower memberi slow.
- Boss per-hit cap, tenacity slow, enrage, dan dispatch smart-AI.
- AI menghabiskan gold untuk hero/tower/item dan memiliki draft pool.
- Auto-trigger item saat HP kritis dan saran item dari katalog.
- Manifest sprite unit/tower/nexus termuat.
- Suite core/shell sebelumnya tetap lulus.

## Batas parity yang belum diklaim

1. **Bake sprite**: `sasori/e` gagal di renderer Python (`NameError: random`) dan
   jatuh ke pose attack; `ursath/w` dibuang sebagai static. Ini cacat sumber
   Python yang belum diperbaiki dalam port ini.
2. **Item**: stats, slot, saran, auto-trigger utama, dan on_attack chain/cleave
   sudah native. Seluruh passive/aura/active spesifik 33 item belum diklaim 1:1
   dengan `hero_items.py`; beberapa efek lanjutan masih memerlukan port manual.
3. **Boss smart-AI**: kit memuat 79 rantai smart-AI yang dihasilkan generator.
   Boss di luar rantai tersebut memakai ability generik + stat boss; belum semua
   216 boss memiliki perilaku bespoke yang diverifikasi terhadap oracle Pygame.
4. **Visual**: sprite-strip, tier tower/nexus, projectile, popup, dan screen shake
   sudah native. Rig Pygame prosedural, cinematic intro/death, partikel kompleks,
   dan side-panel lebar belum diklaim parity piksel-per-piksel.
5. **Performa**: spatial-grid optimisasi Pygame belum diport; pencarian target
   masih linear. Benchmark perangkat nyata belum dilakukan.
6. **Layanan/ekspor**: Play Games, top-up nyata, Android/keystore, GPU/audio perangkat
   tetap tidak diverifikasi lokal dan tidak boleh diklaim sukses palsu.

## Regenerasi

```bash
python tools/prepare_godot_entities.py          # tulis kit + validasi manifest
python tools/prepare_godot_entities.py --check  # CI: gagal bila stale
python tools/prepare_godot_entities.py --bake   # butuh pygame-ce, Pillow, numpy
python tools/test_godot_entity_prepare.py
```

Kit generated dikecualikan dari `gdlint`/`gdformat` karena melebihi batas gaya
file transpile, tetapi tetap wajib lulus `gdparse` dan `--check` staleness.
