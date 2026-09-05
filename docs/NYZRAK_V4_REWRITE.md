# NYZRAK v4 — "The Hollow Blizzard"

Rewrite total (dari nol) untuk karakter **NYZRAK**, mini boss level 3 yang
juga dipakai sebagai kartu hero: ice wyvern rider (teal / frost / spear).
Renderer pixel-art prosedural, animasi delta-time, skill FX 4-fase, combat
feedback, dan gameplay feel.

Tidak ada aset eksternal: **0 file gambar, 0 `pygame.image.load`, 0 sprite
sheet**. Semua piksel badan dihasilkan kode pada buffer `SRCALPHA` 110×110
lalu di-upscale nearest-neighbour ×2.

| Preview | Isi |
|---|---|
| `docs/nyzrak_v4_closeup.png` | Idle / thrust / sweep, nearest ×4 (review siluet) |
| `docs/nyzrak_v4_strip.png` | 12 pose grid nearest ×3: idle, walk, run, thrust, sweep, hit, Q/W/E/R, spawn, death |

Regenerasi regresi:

```
SDL_VIDEODRIVER=dummy python tools/test_nyzrak_rewrite.py
SDL_VIDEODRIVER=dummy python tools/test_level3_masterwork.py
```

---

## 1. Arsitektur (4 pilar terpisah)

```
bosses/level3.py            entry point & namespace lama (_NS_nyzrak) -> re-export
bosses/nyzrak_v4.py         CHARACTER state/anim + RENDERER prosedural
heroes/nyzrak_fx.py         FX: particles/impacts/projectiles/skills (pooled)
heroes/combat_feel.py       bus FEEL bersama: hit_stop / shake / freeze frame
```

- **CHARACTER** (`_NyzAnimController`, `_update_attack_anim`, `_rig_pose`):
  state machine IDLE/WALK/RUN/ATTACK/SWING/SKILL/HIT/SPAWN/VICTORY/DEATH
  dengan timer serangan dari simulasi 60 fps **plus** jam delta-time
  (`pygame.time.get_ticks()`, clamp 0.05 s) untuk spawn/victory/squash.
  Anticipation (squash mundur), swing (stretch maju), impact hold, recoil,
  follow-through, dan gerak sekunder (sayap/ekor/napas) dari `_rig_pose`.
- **RENDERER**: buffer pixel-art `110×110` (PX=2 saat blit). Layer modular:
  `render_shadow → back_wing → tail → legs → body → head → face →
  rider_cloak → rider_armor → rider_head → rider_arms → weapon →
  front_wing → highlight → outline → hit_flash → status → dissolve`.
- **FX** (`heroes/nyzrak_fx.py`): pool tetap — `Particle(170)`,
  `Impact(8)`, `Projectile(18)`, `Skill(4)`, `SwingTrail(14)`. Skill memakai
  timeline **cast → charge → release → area → after** (Q/W/E/R).
- **GAMEPLAY FEEL** (`heroes/combat_feel.py`): `hit_stop` 0.03–0.08 s,
  `shake` teredam, freeze-frame. Basic attack: trail + whoosh **tanpa
  ImpactFX** (aturan repo).

## 2. Renderer: detail yang dijamin

- Silhouette: wyvern teal + rider berhood + tombak kristal (sayap 4-jari
  scallop, duri punggung bertip es, spatade ekor).
- Material: wyvern 5-band ramp, membrane sayap 4-nada, jubah ungu, fur
  putih, pauldron es, poros baja + cincin emas + mata tombak 4 faset.
- Depth: contact shadow 2-tone + cincin beku, rim light punggung, napas
  dingin, kilau pauldron.
- Hit flash: tint silhouette alpha ≤150 + outline gelap ditarik ulang
  (bukan blob putih).
- Status overlay: rim frost saat cast Q, rim es saat W/E/R.
- Death: collapse + erosi alpha baris-demi-baris (PixelArray). Spawn:
  kebalikannya (rise dari dissolve).
- Bounds-safe: `px_set` clip ke permukaan.

## 3. Skill & combat feel

| Skill | Anticipation | Cast | Impact | Recovery |
|---|---|---|---|---|
| Q Arctic Burn | tombak bidik + orb ungu | beam frost gerigi | burst di ujung | recoil |
| W Splinter Blast | tarik tombak | kerucut shard | 6 splinter + trail | follow |
| E Winter's Curse | angkat tinggi | telegraph dash | penjara kristal | settle |
| R Cold Embrace | gather nova | shockwave ganda | kubah faset + salju | fade |

Durasi visual **50 / 50 / 70 / 90** frame @60 fps — sinkron
`bosses/base_boss._nyzrak_*` dan `hero_skills/_bundle.py`.

## 4. Kompatibilitas

Nama & antarmuka lama dipertahankan:

- `bosses.level3._NS_nyzrak` (re-export dari `nyzrak_v4`)
- `draw_nyzrak(surface, boss, x, y)` / `draw_boss`
- `PALETTE`, `PIXEL=2`, `RIG_SIZE=110`, `GROUND_DY=55`, `LIFT=4`
- `_NyzAnimController`, `ATTACK_PHASES`, `ATTACK_ACTIVE=(0.40, 0.64)`,
  `ATTACK_RELEASE=0.46`, `SKILL_DUR`
- `_spear_pose_geom` / `_spear_state` / `_draw_swing_arc`
- atribut `_nyz_*`

Varkul, Xerathis, dan Ancient Apparition **tidak disentuh**.

Hero-lane: badan pada resolusi native (PX=2); pipeline `heroes.render_hero`
yang men-scale. Portrait HD (`_portrait_hd`) dan canvas-pass
(`_skip_renderer_projectiles`) tetap didukung.

## 5. Performa (diukur, `tools/test_nyzrak_rewrite.py`)

| Skenario | Waktu | Budget |
|---|---|---|
| Renderer idle | **1.33 ms/frame** | 2.35 |
| FX penuh (swing + R) | **1.94 ms/frame** | 5.5 |

## 6. Test

- `tools/test_nyzrak_rewrite.py` — 16 test (render semua state, controller,
  arc sweep/thrust, projectile lifecycle, skill FX, feel, integrasi boss &
  hero, palette, perf, prosedural).
- `tools/test_level3_masterwork.py` — regresi keluarga level 3 (bbox, hurt
  flash, shadow, durasi FX=AI, outline).
- `tools/test_basic_attack_no_impact_fx.py` — Nyzrak tetap di daftar
  "basic attack tanpa ImpactFX".
