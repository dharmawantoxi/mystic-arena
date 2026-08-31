# Abaddon v2 — Pixel Masterwork + Skill FX v2.1

True boss di `bosses/level1.py` (`_NS_abaddon`). 100% prosedural.

Standar Thorne v2 / v2.1:

* ramp 4–5 band (cape, armor, horse, flame, blade)
* cape hem `_tuft_points`
* FX world-space `_fx_scale` (1/`_render_scale`, cap 2.6)
* Q Mist Coil / W Aphotic Shield (telegraph dashed ring + spark) / E Darkness Gale / R Death Sever
* melee: anticipation → IMPACT HOLD → follow-through + smear spark
* cache flame/aura/shadow; hurt flash; shadow lift

Tes: `tools/test_abaddon_masterwork.py`  
Audit: `tools/_audit_abaddon_v2.py`
