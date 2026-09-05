# RAZAK v4 — "The Fire Rider"

Rewrite total (dari nol) untuk karakter **RAZAK**, mini boss level 2 yang
juga dipakai sebagai kartu hero: goblin penunggang kelelawar api merah
dengan flamethrower kuningan + machete berujung bara.

Tidak ada aset eksternal: **0 file gambar, 0 `pygame.image.load`, 0 sprite
sheet**. Semua piksel badan dihasilkan kode pada buffer `SRCALPHA` 176×152
lalu diturunkan ke `SCALE = 0.62` (satu faktor untuk boss, lane hero, dan
portrait).

| Preview | Isi |
|---|---|
| `docs/razak_v4_closeup.png` | Idle / attack / Q, nearest ×3 (review siluet) |
| `docs/razak_v4_strip.png` | 12 pose grid: idle, walk, attack, dash, hit, Q/W/E/R, mirror |

Regenerasi regresi:

```
SDL_VIDEODRIVER=dummy python tools/test_razak_rewrite.py
SDL_VIDEODRIVER=dummy python tools/test_level2_masterwork.py
SDL_VIDEODRIVER=dummy python tools/test_razak_v3_combat.py
SDL_VIDEODRIVER=dummy python tools/test_razak_no_white_cover.py
```

---

## 1. Arsitektur (4 pilar terpisah)

```
bosses/level2.py            entry point & namespace lama (_NS_razak) -> re-export
bosses/razak_v4.py          CHARACTER state/anim + RENDERER prosedural
heroes/razak_fx.py          FX: particles/impacts/projectiles/skills (pooled)
heroes/combat_feel.py       bus FEEL bersama: hit_stop / shake / freeze frame
```

- **CHARACTER** (`_update_attack_anim`, `_attack_pose`, `_resolve_pose`):
  state IDLE/WALK/ATTACK/DASH/SKILL/HIT dengan timer serangan dari simulasi
  60 fps **plus** jam delta-time (`combat_feel.frame_dt()`, clamp 0.05 s).
  Anticipation (squash mundur), swing (stretch maju), impact hold, follow-
  through, dan gerak sekunder (sayap/ekor/syal/napas) dari `_attack_pose`.
- **RENDERER**: buffer pixel-art `176×152` (PIXEL=2, SCALE=0.62). Layer:
  `shadow → aura → telegraph → back wing → tail → body → head → rider →
  front wing → outline → lighting → live FX`.
- **FX** (`heroes/razak_fx.py`): pool tetap — `Particle(170)`,
  `Impact(8)`, `Projectile(12)`, `Skill(4)`, `SwingTrail(14)`. Skill memakai
  timeline **cast → charge → release → area → impact → fade** (Q/W/E/R).
- **GAMEPLAY FEEL** (`heroes/combat_feel.py`): `hit_stop` 0.03–0.08 s,
  `shake` teredam, freeze-frame. Basic attack: trail + whoosh **tanpa
  ImpactFX** (aturan repo).

Khalros, Gorath, dan Alchemist **tidak disentuh**.

---

## 2. Renderer: detail yang dijamin

- Silhouette: kelelawar api merah + goblin rider (sayap membran 4-band
  scallop, duri punggung ber-flame-mane, ekor berujung panah menyala).
- Material: bat 5-band ramp (bayangan ungu → highlight oranye), kulit
  goblin hijau 4-band, goggles biru signature, tangki brass ganda, bilah
  machete 5-band + fuller, flamethrower brass ber-moncong flare.
- Depth: contact shadow 2-tone + cincin bara, rim light punggung, napas
  / dengus, kilau goggle + brass.
- Hit flash: siluet badan dibanjiri putih-hangat; bayangan tanah **tidak**
  ikut menyala (y≥300).
- Bounds-safe: family bbox ≥ 60×60 dan tinggi alchemist ≥ razak.

---

## 3. Skill & combat feel

| Skill | Anticipation | Cast | Impact | Recovery |
|---|---|---|---|---|
| Q Sticky Napalm | muzzle vortex | molotov parabola | splat + kolam lengket | fade |
| W Flamebreak | charge kerucut | stream 4-band | ring di target | recoil |
| E Firefly | afterimage dash | ring pendaratan 80 | embers + debu | settle |
| R Firestorm | gather (tanpa pilar di badan) | 8 pilar orbit | shockwave + wisp | fade |

Durasi visual **40 / 50 / 35 / 90** frame @60 fps — sinkron
`bosses/base_boss._razak_*`. Radius dunia **75 / 95 / 80 / 180**.

Telegraph world-space: Q/W di **target**, E/R di **caster + GROUND_DY**.
`_fx_scale` cap 2.6. Shockwave aktivasi `age < 12`.

---

## 4. Kompatibilitas

Nama & antarmuka lama dipertahankan:

- `bosses.level2._NS_razak` (re-export dari `razak_v4`)
- `draw_razak(surface, boss, x, y)` / `draw_boss`
- `PALETTE`, `PIXEL=2`, `SCALE=0.62`, `GROUND_DY=52`, `RIG 176×152`
- `ATTACK_PHASES` 6 jendela, `SKILL_DUR`, `SKILL_RADIUS`
- `_machete_grip_local` / `_tip_screen` / `_swing_hitbox`
- `NapalmProjectile` / `NapalmPatch`
- atribut `_razak_*`

Hero-lane: badan pada resolusi native; pipeline `heroes.render_hero`
yang men-scale. Portrait HD (`_portrait_hd`) dan canvas-pass
(`_skip_renderer_projectiles`) tetap didukung.

`heroes/__init__.py` tetap `"razak": ("bosses.level2", "_NS_razak", ...)`.

---

## 5. Performa (diukur, `tools/test_razak_rewrite.py`)

| Skenario | Budget |
|---|---|
| Renderer idle | 3.5 ms/frame |
| FX penuh (swing + R) | 6.0 ms/frame |

---

## 6. Test

- `tools/test_razak_rewrite.py` — render semua state, fase, arc, projectile,
  skill FX, feel, integrasi boss & hero, palette, konstanta, perf.
- `tools/test_level2_masterwork.py` — regresi keluarga level 2 (bbox, hurt
  flash, shadow, durasi FX=AI via `inspect.getsource(razak_v4)`, outline).
- `tools/test_razak_v3_combat.py` — kontrak FX hidup.
- `tools/test_razak_no_white_cover.py` — glow premultiplied, bukan white-out.
- `tools/test_grimjaw_masterwork.py` — nama publik + world-space Q75/W95/E80/R180.
- `tools/test_basic_attack_no_impact_fx.py` — Razak tetap di daftar ranged.
