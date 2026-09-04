# THALGRYN v4 — "The Shape of Water"

Rewrite total (dari nol) untuk karakter **THALGRYN**, mini boss level 6 yang
juga dipakai sebagai kartu hero: renderer pixel-art prosedural, animasi
delta-time, skill FX 4-fase, combat feedback, dan gameplay feel.

Tidak ada aset eksternal: **0 file gambar, 0 `pygame.image.load`, 0 sprite
sheet**. Semua piksel dihasilkan kode pada buffer `SRCALPHA` kecil lalu
di-upscale nearest-neighbour.

| Preview | Isi |
|---|---|
| `docs/thalgryn_v4_strip.png` | 11 pose: idle, walk, run, charge, swing, impact, follow, hurt, spawn, victory, death |
| `docs/thalgryn_v4_skill_sequence.png` | Q/W/E/R: anticipation → cast → impact → recovery (telegraph + impact FX) |
| `docs/thalgryn_v4_combat.png` | Melee (trail + impact ring/flash) dan ranged Water Spear (proyektil + trail) |
| `docs/thalgryn_v4_ingame.png` | Mock arena: 4 unit hero-lane + 1 mini boss bertarung |
| `docs/thalgryn_v4_hero_lane.png` | Paritas ukuran hero-lane vs gravefang/nyxara/khalros |

Regenerasi preview + audit performa:

```
SDL_VIDEODRIVER=dummy python tools/_shot_thalgryn_v4.py
```

---

## 1. Arsitektur (4 pilar terpisah)

```
bosses/level6.py            entry point & namespace lama (_NS_thalgryn) -> re-export
bosses/thalgryn_v4.py       CHARACTER state/anim + RENDERER prosedural
heroes/thalgryn_fx.py       FX: particles/impacts/projectiles/skills (pooled)
heroes/combat_feel.py       bus FEEL bersama: hit_stop / shake / freeze frame
```

- **CHARACTER** (`_update_thalgryn_attack_anim`, `solve_pose`): state machine
  IDLE/WALK/RUN/CHARGE/SWING/IMPACT/FOLLOW/HURT/SPAWN/DEATH/VICTORY dengan
  timer berbasis **delta-time** (`pygame.time.get_ticks()`, clamp 0.05 s),
  bukan frame counter. Semua squash/stretch/anticipation/follow-through
  dihasilkan `solve_pose()` sebagai kurva kontinu.
- **RENDERER**: buffer pixel-art `109×98` (PX=2 saat blit). Layer modular:
  `render_shadow → mantle → tail → body → equipment → armor → head → face →
  crown → arms → weapon → fist → highlight → outline → hit_flash → status →
  dissolve → orbit`. Buffer hasil di-cache per pose terkuantisasi
  (`_compose_art` + cache key pose) sehingga frame berulang tidak menggambar
  ulang piksel.
- **FX** (`heroes/thalgryn_fx.py`): pool tetap — `Particle(170)`,
  `Impact(8)`, `Projectile(16)`, `Skill(4)`, `SwingTrail(14)`; tidak ada
  alokasi per-frame. Skill memakai **TIMELINE 4 fase**
  (anticipation, cast, impact, recovery) per skill Q/W/E/R.
- **GAMEPLAY FEEL** (`heroes/combat_feel.py`): `FEEL.hit_stop()`,
  `FEEL.shake()`, `FEEL.should_freeze_frame()`, `FEEL.fx_dt()` dipakai bersama
  oleh loop game; chain INPUT→ACTION→VISUAL→AUDIO→IMPACT→FEEDBACK dipatuhi
  (impact memicu hit-stop 60-90 ms + shake teredam + damage number dari sistem
  existing).

## 2. Renderer: detail yang dijamin

- Silhouette: jubah air bertingkat + mahkota 3 puncak + glaive bilah lengkung
  (disc-chain fill, bukan satu `px_poly` degeneratif).
- Material separation: air (dither 2-tone + ramp horizontal), emas mahkota/
  trim (highlight spekular 1 px), baja haft, inti energi (`core_hot`).
- Depth: contact shadow 2-tone + splash ring busa, rim light sisi facing,
  shadow offset, weapon shine berkilau mengikuti fase ayun.
- Hit flash: tint silhouette alpha ≤165 + outline gelap ditarik ulang supaya
  detail & silhouette tetap terbaca (bukan blob putih).
- Status overlay: rim atribut (str/agi/int) saat buff morph aktif.
- Death: collapse squash + erosi alpha baris-demi-baris (slice PixelArray,
  C-level) + puddle + burst droplet. Spawn: kebalikannya (rise dari puddle).
- Bounds-safe: `px_set`/`px_dither` clip ke permukaan (glaive terangkat boleh
  keluar buffer tanpa crash).

## 3. Skill & combat feel

| Skill | Anticipation | Cast | Impact | Recovery |
|---|---|---|---|---|
| Q Tide Surge | condense droplet | teleport-surge streak | geyser + ring + shake | drip |
| W Water Spear | tarik glaive | proyektil spear + trail | burst directional + hit-stop | follow-through |
| E AttributeShift | pulse inti | kolom air + rune ring atribut | flash ring morf | settle |
| R Thousand Drops | puddle clone | 3 clone air (tint `last_art`) muncul berjenjang | slam serentak + shockwave | clone luruh |

- `notify_skill_impact()` menerapkan impact **sinkron** (test mengunci
  `FEEL.SHAKE.amount > 0` tanpa tick), kecuali W yang menunggu spear mendarat.
- Basic attack: whoosh partikel + trail saja — **tanpa ImpactFX** sesuai
  aturan repo (`tools/test_basic_attack_no_impact_fx.py`).
- Knockback, damage number, hit flash, weapon recoil, attack trail, death
  burst semuanya terhubung ke sistem existing tanpa mengubah perhitungan
  damage/targeting/AI/tower.

## 4. Kompatibilitas

- Nama & antarmuka lama dipertahankan: `bosses.level6._NS_thalgryn`,
  `draw_thalgryn(surface, boss, x, y)`, `PALETTE`, `ATTACK_PHASES`,
  `_update_thalgryn_attack_anim`, pose map di `heroes/__init__.py`.
- Hero-lane: badan digambar pada resolusi **native** (PX=2); pipeline
  `heroes.render_hero` yang men-scale sprite terukur (sama seperti boss lain)
  — menghindari double-scale yang membuat sprite mungil.
- Portrait HD (`_portrait_hd`) dan beam-pass pipeline tidak disentuh.

## 5. Performa (diukur, `tools/_shot_thalgryn_v4.py`)

| Skenario | Waktu |
|---|---|
| Full combat frame (ground + sprite + live FX, impact aktif) | **1.44 ms** |
| `draw_thalgryn` lane boss | **1.61 ms** |
| Partikel aktif simultan | 170 (pool penuh, tanpa alokasi) |

Budget frame pertarungan 8 ms → margin ~5×. Cache buffer pose + pool FX +
slice PixelArray menjaga FPS stabil meski banyak unit.

## 6. Test

- `tools/test_thalgryn_rewrite.py` — 36 test (renderer layer, pose solver,
  timeline 4 fase, pool cap, compat API, larangan aset eksternal).
- Regresi silang: `test_basic_attack_no_impact_fx`, `test_kunkka_rewrite`,
  `test_syrentha_rewrite`, `test_gravewake_rewrite` — **153 passed**.
- Full-suite: paritas dengan baseline (52 failure pre-existing order-dependent
  di baseline, tidak bertambah; lihat catatan `/home/user/prev/fail_base.txt`).
