# Vex v2.1 Pixel Masterwork Renderer

Vex now follows the same renderer discipline used by the merged Thorne v2 Pixel Masterwork and Thorne v2.1 Skill FX work.

## Renderer scope

- **100% procedural** in `heroes/_bundle.py` namespace `_NS_vex`.
- **No PNG/sprite-sheet/image.load** dependency.
- **Native rig scale:** `RIG_SCALE = 1.52`; the hero pipeline still normalizes the final arena size.
- **Material language:** 4-5 band void/astral hue ramps, upper-left key light, selout, jagged robe silhouette, robe dither bands, armor/staff specular clusters, crescent staff cradle, faceted orb, and orbit glints.
- **Animation:** living idle, walk foot/greave solver with contact motes, cloak/staff secondary motion, and multi-keyframe attack timeline with wind-up, release, `ATTACK_IMPACT`, smear, and impact flash.
- **Skill body reaction:** Q/W/R overcharge and E astral state alter chest, crest, staff, and ambient glow.

## Skill FX v2.1

Skill FX are rendered in world-space using `_fx_scale(hero) = clamp(1 / _render_scale, 1.0, 2.6)`. Rings/telegraphs stay readable when the cached hero sprite is downscaled by the arena renderer.

| Skill | Visual standard |
| --- | --- |
| Q Arcane Orb | Staff activation burst, segmented beam telegraph, target splat ring, converging rune ring, chevrons, charged staff motes, layered projectile trail, and tip glints. |
| W Sanity's Eclipse | Exact 60 world-px AOE ring, activation shockwave, dashed/rune rings, inward chevrons, jagged cracks, two rows of void crystals, motes, and orbit glints. |
| E Astral Imprisonment | Staff-to-target astral tether, target pillar, prison footprint/crosshair, dashed ring, foreground glass bubble/cage, projectile ribbon trail, and impact prison bubble. |
| R Essence Flux | Exact 180 world-px ultimate ring, pillar/shockwave activation, magma/void cracks, rotating runes, converging telegraph, nova core, spiral wisps, embers, and outer glints. |

Static aura/mist/platform/shadow surfaces are cached in `_STATIC_SURFACES`; per-frame animation is limited to lightweight alpha overlays and deterministic motes.

## Audit / preview output

Run:

```bash
python tools/_audit_vex_v2.py
python tools/test_vex_masterwork.py
```

Generated review sheets:

- `docs/vex_v2_review.png`
- `docs/vex_v2_anim_strip.png`
- `docs/vex_v2_ingame.png`
- `docs/vex_v2_skills.png`

Latest audit snapshot (2026-08-30):

- Native idle bbox: `111x165`
- Pipeline-normalized screen height: `81.2 px`
- Walk frames: `8/8` unique
- Attack frames: `10/10` unique
- W ring @ `_render_scale=0.5`: `180/180` sampled hits at radius `60 / 0.5`
- R ring @ `_render_scale=0.5`: `180/180` sampled hits at radius `180 / 0.5`
- Cache-miss timings on audit surface: idle `~1.6 ms`, Q `~2.3 ms`, W `~3.3 ms`, E `~3.0 ms`, R `~3.0 ms`
