# Mystic Arena — Godot Edition

Port GPU dari versi `pygame-ce`. Visual hero naik drastis via `AnimatedSprite2D` + **`Skeleton2D` Kaizen 25 bones + hamon shader** + `GPUParticles2D` + `PointLight2D`.

## Quick Start

```bash
# 1. Convert data pygame -> Godot JSON (sudah jalan, 222 hero, 216 boss, 54 level)
python tools/convert_to_godot.py

# 2. Buka di Godot 4.3+
godot godot/project.godot
# F5 untuk run. Main arena jalan (fallback kotak warna). Untuk Kaizen showcase:
# Di FileSystem dock: double-click godot/scenes/demo/KaizenDemo.tscn → F5 (atau Run Current Scene)
# Siklus idle 3s → walk 3s → attack loop (hamon kilat + wind ribbon). SPACE=force attack, F=flip, R=reset.
```

## Asset Pipeline

- `godot/data/*.json` — hasil convert, dibaca `HeroDB`/`BossDB`.
- `godot/assets/heroes/<hero>/SpriteFrames.tres` — buat dari Aseprite: `File → Export Sprite Sheet` → import ke Godot `AnimatedSprite2D`.
- `godot/assets/shaders/outline.gdshader` — outline 1-pass + hit flash + rim light (ganti 5 blit manual pygame).
- `godot/shaders/hamon.gdshader` — hamon temper katana Kaizen (wave + temper cloud + attack pulse).

## Kaizen Skeleton2D (contoh flagship)

```
godot/scenes/hero/kaizen/KaizenSkeleton.tscn  — 25 Bone2D (Root→Hips→Torso→Chest→Head/Ponytail 3×/Scarf 3×/Katana + Arms/Legs)
godot/scenes/hero/kaizen/KaizenSkeleton.gd   — drive(phase, action, attack_progress, facing) — busur 1 sumber kebenaran (ATTACK_ARC_*), inertia scarf/ponytail, hamon shader time, wind ribbon Line2D
godot/scenes/demo/KaizenDemo.tscn/.gd       — showcase isolasi: F5 Run Current Scene untuk lihat 60fps bone interpolasi vs pygame 6-frame patah
```
Integrasi `Hero.gd`: `hero_type == "kaizen"` → `sprite.visible=false` → `KaizenSkeletonScene` di `Visual`, `anim_phase` → `skeleton.drive(...)` tiap `_physics_process`. Tip katana untuk damage/ FX via `get_katana_tip_global()`.

## Android Build

`Project → Export → Android → Export AAB` → `godot/build/MysticArena.aab` (1-2 menit, bukan 8-12 menit buildozer).

Package: `io.github.dharmawantoxi.mysticarena` (sama, save cloud tetap kebaca).

Lihat `docs/GODOT_MIGRATION.md` untuk roadmap lengkap.
