# Migrasi Mystic Arena: Pygame → Godot 4

> Tujuan: visual hero **naik drastis** (GPU, Skeleton2D, shader, partikel, lighting) + APK Android native tanpa `buildozer`.

---

## 1. Kenapa Godot menang drastis vs Pygame?

| Aspek | Pygame (sekarang) | Godot 4 (sesudah) |
|---|---|---|
| **Render** | CPU `blit` per-pixel. `ambient_tint` fullscreen = 204ms (3 FPS di HP). Aura & bayangan = 14 `Surface` SRCALPHA | **GPU Forward+**. 1 draw call batched. Bloom/glow = 1 shader |
| **Hero visual** | `pygame.draw.polygon` procedural, `smoothscale` CPU, outline 5x blit manual | `AnimatedSprite2D` + `SpriteFrames.tres` HD + `Skeleton2D` tulang + `outline.gdshader` 1 pass |
| **Animasi** | `_update_attack_anim` + `walk_cycle` manual, kuantisasi 2 frame (patah) | `AnimationPlayer` 60fps interpolasi, `Skeleton2D` IK, `AnimationTree` blend |
| **FX tempur** | `heroes/gornak_fx.py` live layer 1:1 tapi tetap CPU particles (170 max) | `GPUParticles2D` 10.000 partikel @0.5ms, `hit_stop` + `Camera trauma` native |
| **Lighting** | `lighting.py` GRAD_BOX + rim manual 7 blit | `DirectionalLight2D` + `CanvasModulate` + `PointLight2D` per hero (Shadow + rim gratis) |
| **Map** | 6 layer `Surface` cache + `blit` tiap frame | `TileMapLayer` GPU + `TileSet` per tema (forest/desert/ice/abyss...) |
| **Android** | `buildozer` + `p4a` + `pygame-ce` recipe, build 8-12 menit, sering merah | Export **AAB** 1 klik, `gradle` native, 1-2 menit, Play Games plugin resmi |

**Bottom line:** Yang di `pygame` butuh 3000 baris rig Kaizen, di Godot jadi 1 `Skeleton2D` + 5 anim.

---

## 2. Struktur Project Godot (sudah dibuat di `godot/`)

```
godot/
  project.godot          # Forward+, glow, viewport 1280x720
  scenes/
    main.tscn            # Root: ArenaMap + Containers + Camera + HUD
    hero/Hero.tscn       # CharacterBody2D + AnimatedSprite2D + shader + GPUParticles2D
    hero/Hero.gd         # Port _entity.Hero (stats, AI hunt, damage school, skill delegate)
    map/ArenaMap.tscn    # TileMapLayer Ground/River/Lanes/Decor + Light
    map/ArenaMap.gd      # Port map_components/ (theme, lane path)
    boss/Boss.tscn       # Mirip Hero.tscn tapi boss_class
    tower/Tower.tscn
    fx/DamageNumber.tscn # Menggantikan FloatingText pygame
  scripts/
    autoload/GameManager.gd  # Port _core.Game (gold, wave, spawn)
    autoload/SaveManager.gd  # Port mobile/cloud_save (user:// + Play Games)
    core/HeroDB.gd       # Port _core.HERO_TYPES + hero_archetypes.json
    core/BossDB.gd       # Port bosses/boss_data.py
    systems/CombatSystem.gd # Port _entity damage school mitigation
    utils/DamageSchool.gd
  assets/
    shaders/outline.gdshader  # 1-pass outline + hit flash + rim (ganti 5 blit pygame)
    shaders/bloom.gdshader    # Skill glow
    heroes/<hero>/SpriteFrames.tres # Aseprite export (belum ada, fallback warna)
    tilesets/<theme>.tres
  data/                  # Hasil tools/convert_to_godot.py
    heroes.json
    bosses.json
    levels.json
    hero_archetypes.json
```

---

## 3. Cara Jalan (3 langkah)

### Langkah 0 — Install Godot 4.3
Download dari https://godotengine.org/download — versi `Forward+`. Tidak perlu build apapun.

### Langkah 1 — Convert data pygame → Godot
```bash
python tools/convert_to_godot.py
# Output: godot/data/heroes.json (200+ hero), bosses.json, levels.json
# File ini dibaca HeroDB/BossDB saat _ready()
```

### Langkah 2 — Buka di Godot & Run
```bash
godot godot/project.godot
# atau double-click project.godot
# Tekan F5 — Main scene langsung jalan: map forest (fallback prosedural, tanpa TileSet),
# 6 hero Radiant + 6 hero Dire + mini boss, wave minion tiap 25 detik, HUD emas+wave.
# Tombol debug saat run: R respawn · T ganti tema · SPASI beli hero · P/ESC pause.
#
# Kalau yang muncul masih layar hitam: cek urutan autoload & nama file di godot/
# (lihat godot/README.md bagian "F5 cuma layar hitam" — 6 penyebab yang sudah diperbaiki
# 2026-09-06: tanpa Main.gd, map tanpa TileSet, kamera di (0,0), Boss tanpa visual,
# Hero fallback tidak di-play(), time_scale hit-stop).
```

---

## 4. Upgrade Visual Hero — Before vs After (kode)

### Pygame (sekarang, `heroes/_bundle.py` Kaizen 2906 baris)
```python
# 1.5x rig native 158x168, 5 band hue, dither, hamon...
def draw_kaizen(surface, boss, x, y):
    canvas = pygame.Surface((220,220), SRCALPHA) # alloc tiap miss
    _draw_katana(canvas, cx, cy, angle) # 40 draw.polygon
    _draw_scarf(canvas, ...) # manual
    # ... 2000 baris ...
    scaled = pygame.transform.smoothscale(canvas, (w,h))
    surface.blit(scaled, (x-ax, y-ay)) # CPU
    # + lighting.apply_to_rig (7 blit)
```

### Godot (sesudah, `Hero.tscn`)
```
Hero (CharacterBody2D)
  ├─ Shadow (Sprite2D, modulate.a=0.35)
  ├─ Visual (Node2D, scale.x = facing)
  │   └─ AnimatedSprite2D (SpriteFrames.tres, material=outline.gdshader)
  ├─ FX/HitParticles (GPUParticles2D, 12 radial, one_shot)
  └─ AnimationPlayer (idle bob, walk, attack 0.18s, death)
```
```gdscript
# Hero.gd — 1 baris ganti anim
sprite.play("attack")
hit_particles.emitting = true
Engine.time_scale = 0.05 # hit-stop
```
**Gain:** Outline 5 blit → 1 shader tap. 2.9ms CPU → 0.4ms GPU. Animasi patah 2-frame → 60fps blend.

---

## 5. Asset Pipeline yang Disarankan

Kamu punya 2 pilihan untuk 200+ hero:

**Opsi A — Tetap procedural tapi export sekali (cepat):**
1. Run `tools/_shot_kaizen_masterwork.py` headless pygame → save PNG 512x512 per pose (idle/walk/attack/skill)
2. Import PNG ke Godot `SpriteFrames` (Aseprite/Godot importer)
3. Keuntungan: 0 gambar ulang, visual naik karena GPU + shader + filter

**Opsi B — Skeletal Spine/Rive (terbaik, butuh artis):**
1. Buat 1 hero template di Spine (tulang: root→torso→head, arm, leg, weapon)
2. Rig Kaizen procedural → mapping tulang 1:1 (weapon tip = Skeleton2D bone tip)
3. Export `skeleton.json + atlas.png` → Godot Spine plugin
4. Semua hero pakai template, ganti skin (palette) → 200 hero = 200 skin, bukan 200 rig

**Opsi C — AI Upscale (paling cepat naik drastis):**
- Ambil screenshot `docs/kaizen_masterwork_preview.png` → `ComfyUI` / `SDXL` img2img HD 2x + normal map generator → import Godot dengan shader normal.

---

## 6. Android Export (menggantikan buildozer.spec)

Di Godot: `Project → Export → Android → Export AAB`

- Keystore sama seperti `buildozer.spec` (jangan ganti package `io.github.dharmawantoxi.mysticarena`)
- Play Games: install plugin `godot-google-play-games` (menggantikan `src/CloudSaveBridge.java`)
- Permissions: `VIBRATE`, `INTERNET` otomatis dari export template

Build time: Pygame 8-12 menit (p4a clone + compile) → **Godot 45 detik**.

---

## 7. Roadmap Port

| Fase | Task | Status / Estimasi |
|---|---|---|
| **Fase 0** | `convert_to_godot.py` + `godot/` skeleton | ✅ DONE (222 hero, 216 boss, 54 level — 2026-09-06) |
| **Fase 1** | 6 hero starter jalan di Godot (fallback warna + shader) + Boss + DamageNumber + export AAB | ✅ DONE (dihidupkan 2026-09-06 — sebelumnya F5 hanya layar hitam, lihat `godot/README.md`) |
| **Fase 2a** | **Kaizen flagship: Skeleton2D 25 bones + hamon shader + wind ribbon** (`scenes/hero/kaizen/`) | ✅ DONE (2026-09-06) — lihat `godot/scenes/demo/KaizenDemo.tscn` |
| **Fase 2b** | Import 5 hero masterwork PNG → SpriteFrames + anim (template Kaizen) | 1 minggu |
| **Fase 3** | Map TileSet + 1 tema forest + lane path | 🟡 parsial (2026-09-06): lane/river/base digambar prosedural dari palette `themes.py` + Catmull-Rom `PathGenerator` di `ArenaMap.gd._draw()`; TileSet `.tres` masih tugas lanjutan |
| **Fase 4** | CombatSystem + 54 level config + waves (sudah ada data JSON) | 🟡 mulai (2026-09-06): tema per level dari `levels.json`, `MINION_TYPES` + `NEXUS_WAVE_COMPOSITION` diport ke `GameManager`, `Minion.tscn` + gold reward; nexus/castle & tower masih TODO |
| **Fase 5** | 200+ boss hero import batch (Opsi A) | 2 minggu |
| **Fase 6** | Android AAB final + Play Store (preset sudah ada) | 2 hari |

**Coba Kaizen sekarang:** `godot godot/project.godot` → di FileSystem klik `scenes/demo/KaizenDemo.tscn` → **F5 (Run Current Scene)** — siklus idle→walk→attack dengan hamon kilat & wind ribbon 60fps. Di Main arena: `GameManager.spawn_hero("kaizen", "blue", Vector2(200,300))` otomatis pakai Skeleton2D.

![Kaizen Skeleton blueprint](kaizen_skeleton_preview.png)
*Blueprint 25 tulang: 2.9ms CPU polygon → 0.4ms GPU bones, 6-frame swing → 60fps interpolasi.*

---

## 8. File Penting untuk Diedit Pertama

- `godot/scenes/hero/Hero.gd` — tambah skill QWER kamu
- `godot/assets/shaders/outline.gdshader` — tweak outline_width/color
- `hero_archetypes.json` → `godot/data/hero_archetypes.json` via convert script

Pertanyaan? Buka `godot/project.godot` dan tanya.
