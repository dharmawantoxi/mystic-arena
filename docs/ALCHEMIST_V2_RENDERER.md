# ALCHEMIST — Renderer V2 + Live FX (Masterwork)

Dokumen desain teknis untuk rewrite visual + gameplay-feel karakter
`CHARACTER_NAME = "ALCHEMIST"`. Semua render 100 % prosedural via
`pygame.Surface` / `pygame.draw` / `pygame.transform` / `pygame.mask` /
`math` — tanpa PNG/JPG/sprite-sheet. Konvensi mengikuti
`docs/GORATH_V2_RENDERER.md` (siluet kuat, outline hitam 1 px terakhir,
pass cahaya sebelum outline).

## Peta file

| File | Isi |
|---|---|
| `bosses/level2.py` | `_NS_alchemist` — rig statis + animation controller + arc swing + FX tanah + budget guard. Entri publik `draw_alchemist`. |
| `heroes/alchemist_fx.py` | Modul live FX independen (section 0–12): particle system, projectile, skill FX lifecycle, swing trail, impact + game-feel bus, director, overlay debug. |
| `bosses/base_boss.py` | Hook melee → `alchemist_fx.notify_melee_impact`; label offset `"alchemist": 100` (puncak botol W ~−77 px). |
| `_entity.py` | Hook melee hero-side (setelah hook razak). |
| `heroes/__init__.py` | `"alchemist"` terdaftar di `_LIVE_FX_HEROES` + `_LIVE_FX_PATHS` → `heroes.alchemist_fx`. |
| `tools/test_alchemist_masterwork.py` | Suite 12 test (lihat bawah). |
| `tools/_shot_alchemist_masterwork.py` | Sheet before/after OLD (main) vs NEW (v2+live) → `tools/alchemist_masterwork_before_after.png`. |

## Rig v2 (`_NS_alchemist`)

- **Layer (belakang → depan):** bayangan reaktif → anggota belakang →
  torso → armor (pelat dada, sabuk, bahu) → kepala ogre + goblin penumpang
  + topi → ransum kaca punggung → cleaver/bedil → outline hitam 1 px
  (4 arah) → rim-light. Urutan wajib: draw → crop bbox inflate(2,2) →
  `lighting.apply_to_rig(sub, rim_add=(26,40,14), shade_mul=168)` →
  outline TERAKHIR (kebalikan urutan lama menghasilkan hitamtertimpa).
- **Geometri (GROUND_DY=62):** rig 180×166 di (90,86); goblin offset
  (−13,−44); tangan botol (−11,−74); bedil anchor (−13,−44)+f·8, moncong
  13 px; kepala (4,−50); lutut ca·15/sa·20, ankle +12/16; rok 22–27.
- **Siluet bbox (SRCALPHA):** 133×130 — terbesar di keluarga level 2
  (razak 96×107, khalros 120×129, gorath 112×98).

## Animation controller

- State: IDLE/WALK/RUN/ATTACK/SWING/CAST/SKILL/HIT/HURT/DEATH/CHARGE/
  SPECIAL dengan delta-time dan tabel prioritas
  `ANIM_PRIORITY` (DEATH > HURT > SPECIAL > SKILL > CAST > SWING >
  ATTACK > CHARGE > RUN > WALK > IDLE). Transisi hanya jika prioritas
  baru ≥ prioritas lama ATAU state lama sudah > 0.05 s; DEATH mengunci.
- Attack timeline 6 fase: ANTICIPATION (0–0.05) → WINDUP (0.20) →
  SWING (0.40) → IMPACT (0.55) → FOLLOW (0.70) → RECOVERY (0.90);
  hit window frame 8–22 (`_alch_hit_active`).
- Walk cycle: `pulse` 0.8 Hz + `_alch_moving` (deteksi delta posisi);
  kaki menukar beban (XOR band kaki 562/2330 px antar fase berlawanan).

## Swing berbasis arc + trail

- `_draw_cleaver_swing_arc(s, x, y, facing, progress)` — sudut blade
  interpolasi anticipation → follow (bukan teleport); `_swing_hitbox`
  = segmen grip→tip; `_grip_screen/_tip_screen` diubah ke layar untuk
  trail & hitbox.
- Trail ribbon `SwingTrail` di `heroes/alchemist_fx.py`: histori posisi
  (max age 0.16 s, 14 sampel) → pita memudar dari histori — bukan
  lingkaran.

## Live FX (`heroes/alchemist_fx.py`)

- **Budget:** MAX_PARTICLES 170, MAX_PROJECTILES 14, TRAIL_SAMPLES 14,
  MAX_IMPACTS 8, MAX_SKILLS 4; primitives LRU 96; preset `mobile.perf`
  menurunkan cap. Measured: canvas 0.79 ms; canvas + live 1.34 ms
  (limit 2.2 / 6.0 ms).
- **Particle:** 10 bentuk, kolam + `burst/stream`; `rotation_speed`
  harus SKALAR (tuple → TypeError).
- **Projectile:** busur parametrik botol mendarat TEPAT di target
  (`spawn_bottle(src, dst_world)`); lifecycle SPAWN→TRAVEL→HIT→
  IMPACT FX→DESTROY; droplet/coin balistik.
- **SkillFX TIMELINE** {cast, charge, release, area, impact, fade} —
  Q (0.14/0.10/0.30/0.12/0.34), W (0.20/0.12/0.34/0.16/0.44),
  E (0.16/0.12/0.34/0.14/0.36), R (0.34/0.20/0.56/0.26/0.66);
  tiap skill punya bentuk berbeda (semburan cone, botol + genangan,
  aura rage, badai koin + gelombang kejut) — bukan lingkaran generik.
- **Game feel:** hit-stop via `combat_feel` (`_feel_hit_stop` clamp
  0.03–0.08 s), shake bertahap dengan peluruhan, flash impact
  (`_draw_hit_flash`) — mengikuti razak FX, satu arah (director hanya
  MEMBACA state engine; engine tidak tahu director).
- **API:** `attach/owns/tick/_advance/reset_all/total_particles/
  total_projectiles/projectiles_for/draw_ground_layer/draw_live_layer/
  notify_melee_impact/notify_projectile_impact/notify_skill_impact/
  notify_skill_cast/notify_hurt/spawn_bottle/director_for`;
  `DEBUG_CHARACTER = False` → overlay hurtbox/hitbox/state saat True.

## Integrasi

- Boss path: `draw_alchemist` memanggil `draw_ground_layer` +
  `draw_live_layer` tiap frame; `tick()` memakai `combat_feel.fx_dt()`.
- Hero path: `render_hero` (`heroes/__init__.py`) `_live_fx_pre` →
  blit → `_live_fx_post`; hanya `attach`.
- Hook melee: boss (`bosses/base_boss.py`) dan hero (`_entity.py`)
  memanggil `notify_melee_impact(...)` dalam try/except — aman bila
  modul live FX dimatikan (`ALCHEMIST_FX_ENABLED`).
- Import note: modul game membutuhkan `import _core` lebih dulu
  (alias `settings` via `sys.modules`).

## Testing

```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  python3 tools/test_alchemist_masterwork.py     # 12/12 PASS
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  python3 tools/test_level2_masterwork.py        # regresi keluarga PASS
```

Hasil: `ALL ALCHEMIST MASTERWORK TESTS PASSED` — prosedural+API,
family size, animation controller (7 fase, hitwin 16), swing arc+trail+
hitbox, walk cycle, projectile lifecycle, particle system, skill
lifecycle Q/W/E/R, impact+game-feel (hit-stop 0.050 s, dedupe),
lapisan hidup, integrasi, budget. Regresi level 2 tetap
ALL PASSED (0.41 ms/frame).
