# XERATHIS V3 — COMBAT FX / GAME FEEL (procedural)

Karakter: **`xerathis`** — Crystal Sorceress / mini-boss Level 3.

Rewrite ini menambahkan **lapisan hidup layar 1:1** di luar cache sprite,
mengikuti pola yang sudah dipakai Gornak / Zephyr / Nyzrak / dll. Semua
visual tetap 100% prosedural.

## Pembagian kerja

| Renderer (canvas, di-cache)      | `heroes/xerathis_fx.py` (layar, hidup) |
| -------------------------------- | -------------------------------------- |
| Rig sorceress + selout + rim     | trail staff dari histori posisi nyata  |
| Shadow, aura es, ground pattern  | particle (es, salju, debu kristal)     |
| Pose idle/walk/attack/cast       | proyektil frost shard (sistem nyata)   |
| Skill ground canvas q/e/r        | SkillFX lifecycle cast→release→fade    |
| Hurt-flash (canonical body)      | impact flash + shockwave + hit-stop    |
|                                  | screen shake + DEBUG overlay           |

## File

- `heroes/xerathis_fx.py` — paket game-feel lengkap.
- `bosses/level3.py` — animation controller V2 + bridge lapisan hidup.
- `bosses/base_boss.py` — hook UX skill & hit ke lapisan hidup.
- `heroes/__init__.py`, `_core.py` — registrasi HUD / pipeline FX.
- `tools/test_xerathis_v3_combat.py` — regression test.
- `tools/_shot_xerathis_v3.py` — preview generator.

## API modul FX

```python
attach(hero) / owns(hero)
tick(dt=None)
draw_ground_layer(surface, hero, x, y)
draw_live_layer(surface, hero, x, y)

notify_melee_impact(hero, target, damage, crit)
notify_projectile_impact(hero, x, y, angle, damage, crit, kind)
notify_projectile_cast(hero, x, y)
notify_skill_cast(hero, skill)
notify_skill_impact(hero, x, y, radius, skill)
notify_hurt(hero, amount)
reset_all() / total_particles()
```

## Animation state

```text
IDLE WALK RUN ATTACK SWING CAST SKILL SPECIAL HIT HURT DEATH CHARGE
```

Attack split:

```text
ANTICIPATION → WINDUP → SWING → IMPACT → FOLLOW THROUGH → RECOVERY
```

## Game feel

- Hit-stop di-bus `heroes/combat_feel.py` (0.03–0.08 s).
- Screen shake trauma-based, decay bertahap.
- Particle cap `MAX_PARTICLES = 190`; projectiles cap `18`.
- FX cache surfaces (`glow`, ring, spark, ground ellipse).
- `reset_all()` melepas semua director — tidak ada partikel bocor antar match.

## Debug

Set `DEBUG_CHARACTER = True` di `heroes/xerathis_fx.py` atau
`_NS_xerathis.DEBUG_CHARACTER` untuk overlay hitbox/hurtbox/range, state
anim, fase, frame, FPS, hit active, proyektil, partikel, skill count.
