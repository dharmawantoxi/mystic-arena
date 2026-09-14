# Kaizen v4 — Godot 4.x Rebuild (Renderer + Animation + Skill FX + Game Feel)

> Rebuild penuh karakter **KAIZEN** ("The Wind Blade", assassin starter)
> di Godot 4.x — bukan patch rig lama. Standar master prompt:
> **QUALITY > READABILITY > GAME FEEL > PERFORMANCE > COMPLEXITY.**
> Yasuo dipakai hanya sebagai *quality benchmark* (silhouette/polish/feel);
> desain, warna, ability, dan identitas tetap milik Kaizen.
> Dokumentasi renderer pygame lama: [`KAIZEN_V2_RENDERER.md`](KAIZEN_V2_RENDERER.md),
> FX lama: [`KAIZEN_V3_COMBAT_FX.md`](KAIZEN_V3_COMBAT_FX.md).

## 1. Arsitektur modular (satu script = satu tanggung jawab)

```
godot/scenes/hero/kaizen/
├── KaizenSkeleton.tscn     scene root (path lama dipertahankan —
│                           RendererRegistry + KaizenDemo memakainya)
├── KaizenSkeleton.gd       ROOT: state, blending pose, drive() API, sinyal
├── KaizenAnimator.gd       state → pose target (prosedural, keyframe math)
├── KaizenPose.gd           data pose (sudut FK + secondary motion)
├── KaizenRenderer.gd       pose → gambar _draw() berlapis
├── KaizenSkillFX.gd        skill key → urutan VFX (sequencer)
└── KaizenPalette.gd        palette terkontrol BASE/SHADOW/HIGHLIGHT/ACCENT

godot/scripts/vfx/          lapisan VFX reusable SELURUH GAME (autoload)
├── VFXManager.gd           pooling + API: ring/slash/flash/streak/sparks/
│                           glow/wall/impact(tier)
└── VFXActor.gd             actor draw-based multi-mode (di-pool)
```

Rig lama (Skeleton2D + 25 Polygon2D per tulang) **dihapus total** dan
diganti satu CanvasItem `_draw()` per karakter: lebih murah di Android,
lebih mudah dijaga, tidak ada node-per-bagian.

## 2. Renderer prosedural berlapis

Urutan gambar sesuai lapisan standar:

```
SHADOW (ellipse tanah) → BACK (ponytail, scarf, saya, lengan/kaki belakang)
→ BODY (hakama pleat, gi, kepala) → ARMOR (obi emas, pelat dada, pauldron)
→ WEAPON (lengan depan + katana: tsuka, tsuba emas, bilah baja, hamon
          bergelombang, kissaki, glint) → DETAIL (mata amber + blink,
          alis, bekas luka, kerah V, hachimaki berekor) → HIGHLIGHT
          (rim light dingin 3 goresan) → MAGIC (3 lidah angin kecil,
          hanya saat wind_glow > 0)
```

Semua titik di-snap ke piksel bulat + outline tinta 1px → gaya pixel-art
fantasy, siluet kuat saat kamera zoom out. Pose dihitung lewat FK
sederhana (bukan tulang engine) dari `KaizenPose`.

## 3. Animasi (KaizenAnimator)

State minimum lengkap:

```
IDLE · WALK · RUN · ATTACK · SKILL Q/Q2/W/E/R · HURT · DEATH · VICTORY
```

Setiap state mengikuti kurva **ANTICIPATION → ACTION → IMPACT →
FOLLOW THROUGH → RECOVERY** (serangan dasar: windup 0–0.22, tebasan
ease-in 0.22–0.55, impact-hold singkat, recovery). Transisi antar-state
di-blend root dengan `lerp_angle` per-sudut (rate tergantung state) →
tidak robotic. Secondary motion: scarf 3 segmen, ponytail 3 segmen, tali
hachimaki 2 segmen — semua fungsi fase + "stream factor" (kain lurus
terseret saat dash, berkibar saat idle). Kedip mata terjadwal mandiri.

## 4. Skill FX — clean & elegant (KaizenSkillFX + VFXManager)

Rebuild total; hierarki visual 70/20/10:

```
PRIMARY   = sabit tebasan solid / streak dash / dinding angin
SECONDARY = percikan TERARAH (≤ 10 titik, umur < 0.4 dtk, ada arah)
ACCENT    = flash singkat + glow alpha rendah
```

| Skill | Sequence FX |
|---|---|
| **Q Steel Wind** | flash kecil → sabit 34px depan → 6 spark searah → ring 40 → impact tier 1 |
| **Q2 Dash Strike** | streak sepanjang jalur dash (deteksi teleport posisi) → sabit + impact di titik tiba |
| **W Wind Wall** | dinding 3 sabit berorbit MENGIKUTI hero selama `kit._wind_wall_timer` (±3 dtk) + 2 hembusan |
| **E Whirlwind** | dua sabit berputar 2×TAU mengelilingi tubuh + ring tanah 52px + 6 spark |
| **R Tempest Fury** | PRE flash+glow → tebasan naik → silang-X 62px + ring 78 + impact tier 3 (hit-stop 0.05 dtk + shake) → aftermath glow |

Aturan absolut yang dijaga: **tidak ada particle spam** (semua bentuk
draw-based CPU, tanpa GPUParticles), **glow hanya aksen** (alpha ≤ 0.3),
**warna satu keluarga** (cyan-putih angin Kaizen), dan setiap efek harus
menjawab *WHO CAST IT / WHERE IT HAPPENED / WHAT IT DID*.

## 5. VFXManager (reusable + pooling)

Autoload baru (`scripts/vfx/VFXManager.gd`, terdaftar di project.godot):

* Pool 32 `VFXActor`; **tidak ada instantiate/queue_free saat gameplay**.
  Pool habis → actor tertua dicuri (jumlah efek di layar selalu terbatas).
* API: `ring`, `slash`, `flash`, `streak`, `sparks`, `glow`, `wall`,
  `impact(pos, tier, color)` — `impact` tier 0..3 menyinkronkan
  flash+bentuk+spark (+ `GameManager.request_hit_stop` & camera shake
  hanya tier ≥ 2, durasi dijaga pendek).
* Actor dipasang di container FX arena bila ada (konvensi
  `GameManager.attach_fx`), z-index = y posisi (painter's algorithm).
* Bisa dipakai hero/boss/tower lain — satu sumber bentuk FX game.

## 6. Game feel

* **Attack**: jejak bilah dua-nada (hanya saat swing 0.24–0.82), sinyal
  `attack_started`/`attack_impact` di root (dipakai demo untuk damage
  number di timing impact). Serangan dasar TETAP tanpa impact FX
  (kontrak paritas `test_basic_attack_no_impact_fx`).
* **Hit**: rig membaca HP hero tanpa coupling → pose HURT 0.3 dtk +
  tint merah kecil di dada (flash putih tetap dari HurtFlash Hero).
* **Skill**: shake kamera datang dari `kit_shake` yang sudah ada;
  impact tier 2/3 menambah shake proporsional via `call_group("camera",
  "add_trauma", …)` (di-`max`, tidak menumpuk — GameCamera.gd).
* **Audio**: memakai SFX yang sudah ada (`hero_skill` via `kit_sound`,
  `hero_melee` via Hero.try_attack) — tanpa aset baru.

## 7. Kontrak lama yang dipertahankan

* `RendererRegistry.HERO["kaizen"]` tetap menunjuk
  `KaizenSkeleton.tscn`; **default arena tetap bake pygame** (dikunci
  `GameplayParityTest`) — rig aktif lewat
  `mystic/rendering/experimental_hero_rigs=true` (project.godot) atau
  langsung di KaizenDemo.
* `drive(phase, action, attack_progress, facing, is_moving, skill, delta)`
  dipanggil `Hero._drive_visual` persis seperti sebelumnya; rig digambar
  menghadap +x dan flip dilakukan parent (`Visual.scale.x`).
* Baru: `handles_skill_fx(key) -> true` → `Hero.play_skill_fx` melewatkan
  ring+partikel generik untuk rig yang menangani FX sendiri (anti dobel).
* `get_katana_tip_global()` / `get_katana_grip_global()` dipertahankan.

## 8. Performa Android

* 1 CanvasItem per karakter; ±60–90 draw call kecil per frame, tanpa
  shader partikel, tanpa alokasi node saat gameplay (VFX di-pool; pose
  hanya RefCounted kecil per frame).
* VFXActor menonaktifkan `_process` saat idle di pool.
* Semua FX CPU-draw aman di renderer Compatibility/GLES.

## 9. Cara mencoba

```bash
# Showcase penuh (siklus otomatis + keyboard)
godot --path godot res://scenes/demo/KaizenDemo.tscn

# Di arena: set mystic/rendering/experimental_hero_rigs=true
# (project.godot → [mystic]) lalu mainkan seperti biasa.
```

Keyboard demo: `SPACE` attack · `1/2/3/4` skill Q/W/E/R (tekan `1` dua
kali = Dash Strike) · `H` hurt · `D` death · `V` victory · `F` flip ·
`R` reset.
