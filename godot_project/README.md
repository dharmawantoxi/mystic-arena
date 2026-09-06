# Mystic Arena — Godot 4.x Vertical Slice

> **Status:** Single-character vertical slice for **Kaizen — Wind Blade Assassin**.
> Reference benchmark: **Yasuo (League of Legends)** for animation read, VFX hierarchy,
> and game-feel timing. NOT a clone of Yasuo.

This directory is a fresh **Godot 4.x** project. It is the first stage of a
Pygame → Godot 4.x migration; only Kaizen is implemented at full polish here.
The Pygame sources in the repository root remain the canonical source of truth
for every other character / boss / system until they are migrated.

---

## How to run

```bash
# Install Godot 4.3 (or 4.x) from https://godotengine.org/download
# Then either:
#   * Open the godot_project folder in the Godot editor and press F5, or
#   * Run headless: godot --path godot_project
```

Controls:

| Key | Action                          |
|-----|---------------------------------|
| WASD | Move                            |
| J   | Basic attack (swing)            |
| Q   | Steel Wind (Q1) → Dash Strike (Q2) |
| W   | Wind Wall                       |
| E   | Sweep                           |
| R   | Tornado                         |

The HUD shows HP and skill cooldown timers. Skill buttons are clickable too
(for touch / Android testing).

---

## Folder layout

```
godot_project/
├── project.godot              # Godot 4.x project descriptor
├── icon.svg                   # placeholder icon
├── scenes/                    # .tscn scene files
│   ├── Main.tscn              # demo scene that runs Kaizen
│   ├── Kaizen.tscn            # the Kaizen character
│   ├── EnemyDummy.tscn        # target dummy for testing
│   └── CameraRig.tscn         # camera + shake
├── scripts/                   # GDScript
│   ├── autoload/              # singletons (GameFeel, VFXManager, etc.)
│   ├── characters/            # base Character class + Kaizen
│   ├── enemies/               # base Enemy + dummy
│   ├── fx/                    # VFX (particles, screen-shake, hit-stop)
│   └── ui/                    # HUD (skill buttons, HP bar)
├── resources/                 # .tres (palette, stats)
└── assets/                    # audio + textures (none in this slice)
```

The original Pygame `kaizen_fx.py` and `_bundle.py: _NS_kaizen` were the
references for **what** the character does. **How** it is built here is fully
Godot-native: nodes, signals, tweens, AnimationTree, shaders, GPUParticles2D.

---

## Kaizen — character sheet

| Slot | Skill     | Behaviour                                                          | Cooldown |
|------|-----------|--------------------------------------------------------------------|----------|
| Q    | Steel Wind → Dash Strike | Alternating combo: 1st press AOE slash, 2nd press dash-through slash.  Q1 = range 90, mult 1.0×. Q2 = dash + 80-radius slash, mult 1.5×. | 5 s |
| W    | Wind Wall | Spawn 1.5 s wall in front of the hero that blocks projectiles.     | 12 s |
| E    | Sweep     | AOE jump-attack 100 px, mult 1.0×, small camera shake.            | 7 s |
| R    | Tornado   | 150 px ult AOE, mult 2.0×, big shake + screen flash.              | 30 s |

(Cooldowns / damage multipliers match the Pygame `_NS_kaizen_skills` source.)

---

## Quality decisions

* **Animation**: all poses are built from `Node2D`-composed parts (body, head,
  arm, sword). Each part has an `AnimationPlayer` track; high-level state
  changes are driven by `AnimationTree` state machine for clean blend between
  `idle ↔ walk ↔ attack ↔ skill ↔ hit ↔ death`.
* **VFX**: 70/20/10 visual hierarchy. The primary effect is always a **single,
  readable shape** (a crescent slash, a wall, a tornado). Secondary particles
  and accent sparks layer on top — never the other way around.
* **Game-feel**:
  * Hit-stop = 50 ms on every regular hit, 90 ms on skill Q2 / R.
  * Camera shake = proportional (Q1=2, Q2=4, W=0, E=3, R=8).
  * Damage popups use a tiny object pool (5 entries pre-warmed, never
    instantiated mid-fight).
  * Wind wall blocks projectiles via a `ProjectileBlocker` Area2D.
* **Performance** (Android-friendly):
  * No `_process` overrides unless required for animation timing — base
    `Character` uses `CharacterBody2D` physics body only.
  * All VFX use `GPUParticles2D` with `fixed_fps = 30`.
  * VFX pool caps at 8 active impact bursts, 6 active projectiles.
  * No expensive shaders; just `CanvasItemMaterial` and additive blends.
