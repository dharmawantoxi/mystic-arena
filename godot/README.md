# Mystic Arena — Godot Edition

Port GPU dari versi `pygame-ce`. Visual hero naik drastis via `AnimatedSprite2D` + **`Skeleton2D` Kaizen 25 bones + hamon shader** + `GPUParticles2D` + `PointLight2D`.

## Quick Start

```bash
# 1. Convert data pygame -> Godot JSON (sudah jalan, 222 hero, 216 boss, 54 level)
python tools/convert_to_godot.py

# 2. Buka di Godot 4.3+ (diuji di 4.7.2 Forward+)
godot godot/project.godot
# F5 -> arena 1280x720 langsung terisi: map forest digambar prosedural,
# 6 hero Radiant + 6 hero Dire + mini boss Gornak, wave minion tiap 25 detik,
# HUD emas/wave/announcer, damage number + bar HP.
```

Tombol saat run (helper debug, belum jadi kontrol pemain):

| Tombol | Efek |
|---|---|
| `R` | respawn roster (reset pertempuran) |
| `T` | ganti tema map: forest → desert → ice → abyss |
| `SPASI` | "beli" 1 hero random untuk Radiant (memakai `GameManager.spend_gold`) |
| `P` / `ESC` | pause (`get_tree().paused`; hero & minion ikut beku) |

Untuk Kaizen showcase saja: double-click `godot/scenes/demo/KaizenDemo.tscn` → **Run Current Scene**.
Siklus idle 3s → walk 3s → attack loop (hamon kilat + wind ribbon). SPACE=force attack, F=flip, R=reset.

## "F5 cuma layar hitam" — penyebab & perbaikannya

Log dulu berhenti di `[GameManager] Start Level 1 — gold 1000` dan viewport tetap gelap. Itu **bukan**
crash: memang tidak ada satu node pun yang menggambar. Yang hilang (dan sekarang sudah ada):

1. `scenes/main.tscn` tidak punya script root — `start_level()` hanya `print` + emit signal, tidak ada
   yang men-spawn unit. → ditambah `scenes/main/Main.gd` (roster + wave + framing kamera).
2. `ArenaMap.tscn` berisi 4 `TileMapLayer` tanpa `tile_set` (`assets/tilesets/*.tres` belum dibuat),
   dan 2 `Sprite2D` toko tanpa texture → 0 piksel tergambar. → `ArenaMap.gd._draw()` sekarang
   menggambar terrain/lane/river/base/toko/decor prosedural memakai palette asli
   `map_components/themes.py`. Begitu `assets/tilesets/<tema>.tres` di-import, fallback otomatis mati.
3. `Camera2D` ada di (0,0), padahal arena 0..1280 × 0..720 → isi arena (mis. base Radiant di
   y=620) berada di luar view. → kamera dipusatkan ke (640,360) + `limit_*` dikunci ke ukuran arena.
4. `Boss.tscn` tidak punya visual sama sekali (AnimatedSprite2D kosong, partikel tanpa material) →
   boss tak terlihat walau menghajar hero. → fallback kotak warna + aura `ParticleProcessMaterial`
   + boss bar + AI pendekat/serang.
5. `Hero.gd` fallback kotak warna tidak pernah di-`play()` (autoplay .tscn menunjuk `sprite_frames`
   yang masih null) → hero spawned tapi tak ter-render. → fallback membuat `SpriteFrames` lalu
   `play("idle")`; `autoplay` dihapus dari .tscn (menghilangkan error spam tiap spawn).
6. `Engine.time_scale` di-hit-stop diubah dari node unit yang bisa `queue_free()` di tengah `await`
   (game bisa "nyangkut" 0.05 ≈ layar tampak beku). → hit-stop pindah ke `GameManager` dengan
   watchdog waktu nyata.

Catatan kecil yang juga sudah dibereskan:

- `Color("rrggbb")` **tanpa `#`** di Godot = warna tidak valid (jadi hitam/transparan). `PALETTE`
  Kaizen dan palette map sekarang semuanya `Color("#rrggbb")`.
- `Color8()` tidak boleh dipakai di dalam `const` (bukan konstanta yang dikenali GDScript) —
  pakai `Color("#...")`.
- Cek statis tanpa engine:
  `python3 godot/tools/tscn_lint.py godot/scenes/*.tscn` dan
  `python3 godot/tools/check_refs.py godot` (ext_resource, preload, dan `$Node/Path`).

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
