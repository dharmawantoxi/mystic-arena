# Vex v2.1 Pixel Masterwork Renderer + Skill FX v3.0

Vex follows the renderer discipline used by the merged Thorne v2 Pixel
Masterwork work; the skill FX layer was fully rewritten to **v3.0 "Void
Astral Cinematic"** (2026-09-01).

## Renderer scope

- **100% procedural** in `heroes/_bundle.py` namespace `_NS_vex`.
- **No PNG/sprite-sheet/image.load** dependency.
- **Native rig scale:** `RIG_SCALE = 1.52`; the hero pipeline still
  normalizes the final arena size.
- **Material language:** 4-5 band void/astral hue ramps, upper-left key
  light, selout, jagged robe silhouette, robe dither bands, armor/staff
  specular clusters, crescent staff cradle, faceted orb, and orbit glints.
- **Animation:** living idle, walk foot/greave solver with contact motes,
  cloak/staff secondary motion, and multi-keyframe attack timeline with
  wind-up, release, `ATTACK_IMPACT`, smear, and impact flash.
- **Skill body reaction:** Q/W/R overcharge and E astral state alter
  chest, crest, staff, and ambient glow.

## Skill FX v3.0 — Void Astral Cinematic

Skill FX are world-space via `_fx_scale(hero) = clamp(1 / _render_scale,
1.0, 2.6)` so telegraphs stay readable when the cached hero sprite is
downscaled. Gameplay radii are compensated: **W ring = exact 60 world-px,
R ring = exact 180 world-px** at every cache scale.

### Architecture

Every skill is composed in **three deterministic phases** —
`AKTIVASI` (burst/pillar) → `STEADY` (living loop) → `RELEASE`
(converge + fade) — as a pure function of `(progress, phase)`; no
per-frame randomness. A new primitive library (all fast-path
`pygame.draw`, no per-segment surface allocation) powers the FX:

| Primitive | Purpose |
| --- | --- |
| `_rune_glyph` / `_sigil_ring` | 5 procedural micro-runes; tilted 3/-view rune rings with fake depth |
| `_crystal_shard` | 5-point faceted shard: dark body, key-light facet, bright selout rim, specular pixel, glowing tip |
| `_beam3` / `_energy_arc` | 3-layer outlined beam; deterministic jagged energy arcs with dark under-glow |
| `_nova` / `_arc_band` | Polygon petal bursts; allocation-free ellipse arc bands (accretion, glass domes) |
| `_dither_disk` | Bounded checkerboard dither fill for pixel-art ground shading |
| `_chain_link` / `_orbit_glints` | Astral tether links; orbiting spark dots with 1px tails |

### Per-skill identity

| Skill | Visual standard |
| --- | --- |
| Q Arcane Orb | Staff aperture iris + pillar, 12-segment conduit beam (3-layer + side filaments + traveling energy packets + rune nodes + chevrons), and a target **collapse portal**: double ring, rotating sigil, converging iris petals, brackets, and glow core. Foreground: rune aperture, converging tailed motes, jumping energy arcs, release star. |
| W Sanity's Eclipse | Dithered void disk, exact 60-px ring, counter-rotating sigil, jagged cracks, inward chevrons — and a **black-sun eclipse** floating above the caster whose shadow disc closes over a teal corona (diamond-ring flare mid-eclipse). Foreground: mini-accretion portal and a two-row **faceted crystal crown** with specular glints and soul motes spiraling inward. |
| E Astral Imprisonment | Astral **chain-link tether** (sag + wobble + pulse packets) from staff to target, rune pillar with falling glyphs, prison footprint (rings + sigil + crosshair + corner brackets). Foreground: **glass cage** — back/front rune bars with depth sorting, glass dome arcs, orbiting astral shards, rising motes, pole flares. |
| R Essence Flux | Exact 180-px ultimate ring with double magma+gold rim, gold sigil ring, magma cracks, compass brackets. Foreground: **event horizon** — pure-black core with double photon ring (teal + gold), tilted **accretion disk** (gold/magma front + back bands), lensing arcs, nova petals + edge-launched ray burst, spiral wisps feeding in from behind the horizon, ember columns, orbit glints. |

Projectiles (`ArcaneOrbProjectile`, `AstralOrbProjectile`) share the same
language: comet ribbon trails, rune-glyph halos, faceted orb with crescent
specular, and — on E impact — a full miniature glass cage.

Static aura/mist/platform/shadow surfaces stay cached in
`_STATIC_SURFACES`; per-frame animation is limited to lightweight direct
draws and deterministic motes.

## Audit / preview output

Run:

```bash
python tools/_audit_vex_v2.py      # acceptance criteria + review sheets
python tools/test_vex_masterwork.py  # regression suite
python tools/_probe_vex_fx_v3.py   # pixel-forensics probe per FX feature
```

Generated review sheets:

- `docs/vex_v2_review.png`
- `docs/vex_v2_anim_strip.png`
- `docs/vex_v2_ingame.png`
- `docs/vex_v2_skills.png`

Latest audit snapshot (2026-09-01, Skill FX v3.0):

- Native idle bbox: `111x165`
- Pipeline-normalized screen height: `81.2 px`
- Walk frames: `8/8` unique; Attack frames: `10/10` unique
- FX pixels outside body silhouette: Q `558`, W `419`, E `705`, R `1281`
- W ring @ `_render_scale=0.5`: `180/180` sampled hits at radius `60 / 0.5`
- R ring @ `_render_scale=0.5`: `180/180` sampled hits at radius `180 / 0.5`
- Q/E target telegraph annulus: `68` / `349` hits
- Cache-miss timings: idle `~1.6 ms`, Q `~2.6 ms`, W `~3.5 ms`,
  E `~3.1 ms`, R `~3.4 ms` (soft target `~3.5 ms`, hard cap `4.2 ms`)
