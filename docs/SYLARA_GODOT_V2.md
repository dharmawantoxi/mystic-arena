# Sylara v2 — Total Rebuild (Procedural Layered Renderer + IK Animator)

Dokumen ini mendeskripsikan **total rework** rig **Sylara** (Godot 4.x)
berdasarkan MASTER PROMPT V2: audit sistem lama → identifikasi kelemahan →
redesain arsitektur → rebuild dari nol → verifikasi kontrak → polish.

* Karakter: `TARGET_CHARACTER = sylara` (Wind Ranger — recurve bow).
* `REFERENCE_CHARACTER = wind ranger dota 2` hanya BENCHMARK kualitas
  (silhouette, polish, combat feel) — TIDAK ada elemen desain yang disalin.
* Sumber identitas visual: masterwork bake pygame v3
  (`assets/units/sylara.png`, palet `heroes/_bundle.py:_NS_sylara`).
* Target platform: **Android** (compatibility renderer, CPU draw, pooling).

> Perubahan dokumen v1 (`SYLARA_GODOT_REBUILD.md`, `SYLARA_V2_RENDERER.md`,
> `SYLARA_V3_COMBAT_FX.md`) digantikan sebagian besar oleh dokumen ini.
> Yang masih relevan: timing serangan pygame (impact 0.52) dan resep swing
> arc.

---

## 1. Hasil Audit v1 (mengapa rebuild total)

| # | Temuan | Dampak |
|---|--------|--------|
| 1 | **Kaki slide** — pose kaki sinus tanpa solver; telapak menggeser di tanah | Jalan/lari terlihat "melayang+geser", robotic |
| 2 | **Nock busur salah geometri** — tali ditarik menyamping, tidak ke arah pemanah | Serangan terlihat salah secara kinematik |
| 3 | **Trail koordinat global digambar di ruang lokal** — jejak melenceng saat flip/gerak | Sweep melee rusak visual |
| 4 | **`draw_rect` ganda = blok tinta pekat** di pouch sabuk (filled default) | Bodi rusak 1 spot |
| 5 | **Lengan busur bergoyang** seperti lengan bebas saat jalan | Identitas "membawa senjata siaga" hilang |
| 6 | **Easing sinus linier** di semua transisi | Gerakan tanpa anticipation/overshoot |
| 7 | **Skill R tanpa momen release visual** (charge hanya glow diam) | Ultimit terasa datar |
| 8 | **6 file yatim** (`Sylara.gd/.tscn`, `SylaraCombat/Hitbox/Hurtbox/Audio.gd`) | Kebingungan arsitektur, risiko double-node |
| 9 | **Proyektil serangan dasar = panah generik tim** | Hilangnya identitas panah angin Sylara |
| 10 | **Secondary motion cape/hair berbasis waktu global, bukan kecepatan** | Tidak ada rasa "angin" saat sprint |

Kesimpulan audit: fondasi v1 (modular Skeleton/Renderer/SkillFX, kontrak
`drive()`) **bagus dan kompatibel** → DIPERTAHANKAN. Visual, animasi, dan
combat feel **tidak layak di-patch** → REBUILD TOTAL.

---

## 2. Arsitektur (modular, Godot-native, tanpa framework)

```
scenes/hero/sylara/
├── SylaraSkeleton.tscn   — root + 3 anak (Renderer, SkillFX, Combat)
├── SylaraSkeleton.gd     — root: state machine, blending, drive() API,
│                           sinyal, keputusan combat (swing-riposte, aim,
│                           edge skill release R), style_projectile hook
├── SylaraRenderer.gd     — pose → _draw() 14 lapis (CPU, 1 CanvasItem)
├── SylaraAnimator.gd     — state → pose target: solver kaki 2-bone IK,
│                           easing, timeline attack/skill, secondary motion
├── SylaraPose.gd         — data pose (sudut/offset/secondary motion)
├── SylaraPalette.gd      — palet 5-nilai per material (ramp shade→high)
├── SylaraSkillFX.gd      — sequencer FX Q/W/E/R (VFXManager pooled +
│                           bentuk custom live-aim: koridor, sulur, siklon,
│                           suction, gale tunnel)
└── SylaraCombat.gd       — kebijakan feel: hit-stop/trauma proporsional
```

Kontak luar (TIDAK berubah — dikunci test):

* `Hero._drive_visual` → `drive(phase, action, attack_progress, facing,
  is_moving, skill, delta)` tiap physics frame.
* `handles_skill_fx(key) → true` → Hero melewatkan FX skill generik.
* `RendererRegistry.HERO["sylara"]` → `SylaraSkeleton.tscn`.
* `Hero._shoot_projectile` → rig opsional `style_projectile(bullet)`
  (3-line hook, visual only).

File yatim v1 **dihapus**: `Sylara.gd`, `Sylara.tscn`, `SylaraCombat.gd`
(lama), `SylaraHitbox.gd`, `SylaraHurtbox.gd`, `SylaraAudio.gd`.
Nama `SylaraCombat` dipergunakan kembali untuk node feel-policy baru.

---

## 3. Renderer — 14 lapis (satu CanvasItem, CPU draw)

Urutan gambar (setiap lapis punya tujuan siluet):

1. **GROUND** — bayangan kontak ellipse + **platform angin** (2 cincin busur
   tipis berputar arah berlawanan + 3 titik daun) — identitas Sylara.
2. **CAPE** — 3 segmen, ramp `CAPE_DARK→CAPE→CAPE_LIGHT`, hem **ber-tuft**
   (4 tuft deterministik), rim angin di ujung tuft saat `wind_glow`.
3. **HAIR BACK** — massa rambut **oranye** (blob 8-gon) + 3 untaian +
   highlight helai + flicker kilau.
4. **QUIVER** — strap diagonal, badan quiver kulit, 3 anak panah
   (fletch emerald + mata perak), band emas.
5. **LIMBS BACK** — lengan & kaki belakang (ramp bayangan 3 nilai).
6. **LIMBS FRONT** — kaki depan + **boots** (5-pt polygon, band ankle,
   tutup toe highlight) + tunic (hem gelap, lipatan, edge key-light).
7. **TORSO/VEST** — panel dada kulit, trim emas, dither 4 titik, pauldron
   + stud emas.
8. **BELT** — buckle emas, pouch (outline tinta, bukan blok pekat), strap.
9. **HOOD** — tudung **runcing** 7-pt di belakang kepala, bayangan dalam
   cowl, 2 segmen cowl trailing (secondary motion).
10. **HEAD** — wajah 12-gon, **fringe oranye** ber-notch, **mata emerald**
    + specular + blink line, alis/hidung/mulut temaram.
11. **TRAIL** — jejak sapuan 3 lapis (lebar menyusut, warna
    `WIND_DARK→WIND→WIND_BRIGHT`) — koordinat **LOKAL** (stabil terhadap
    flip parent).
12. **ARM FRONT** — lengan + bracer kulit + gesper emas.
13. **BOW** — recurve detail: limb Bézier 9-titik (taper 3.2→1.6 px, ink
    luar + wood shine dalam), horn recurve, grip wrap 3 lilit, nock emas
    + **glint berputar**, tali (sheen), **anak panah angin** (shaft + inti
    wind + mata perak + fletch emerald) saat `bow_draw > 0.22`.
14. **RIM/WISPS/FEEDBACK** — rim light 3 arc, wisp orbit di tip, daun
    orbit di nock, charge glow nock, debu kontak kaki, hurt flash (demo).

Disiplin teknis:

* **Buffer pool 12× `PackedVector2Array`** (`_pbuf(n)`) — resize+reuse,
  ZERO alokasi per frame.
* **Hash deterministik** (`_hash01(i, seed)`) untuk siluet bergerigi —
  aman cache, tidak ada RNG.
* **FK satu sumber** (`_solve()`) — semua anchor (grip/tip/nock) dihitung
  sekali; nock ditarik ke **−bow_dir** (ke arah pemanah) sesuai kinematika.
* **Palet ramp 4–5 nilai** per material (bayangan dingin, highlight hangat)
  + selout tinta 1 px di tepi luar — siluet terbaca saat zoom out.

---

## 4. Animator — state → pose target

Kaidah: **ANTICIPATION → ACTION → IMPACT → FOLLOW THROUGH → RECOVERY** +
secondary motion.

* **Solver kaki 2-bone IK** (`_ik2`): telapak MENAPAK (tanpa slide), lutut
  selalu ke depan, heel-strike → mid-swing (lift) → toe-off terbaca;
  `dust` di-set saat kontak. Gait: kaki depan θ, belakang θ+π.
* **Easing nyata**: smoothstep, ease-in/out cubic, **ease-out back**
  (overshoot sapuan & release).
* **Lengan busur stabil** saat walk/run (senjata siaga), hanya lengan
  belakang yang mengayun.
* **Attack ranged** (impact 0.52 — paritas pygame): anticipation 0–0.08 →
  draw 0.08–0.46 (tension, wind glow naik) → release 0.46–0.52 (snap tali,
  shiver, recoil maju, dust) → follow-through 0.52–1 (recovery).
* **Swing (melee riposte)**: arc −1.24 → −0.26 → +0.86 rad (konstanta
  pygame), windup ease-in, strike cepat + overshoot, trail aktif, pivot
  radius membesar saat strike.
* **Skill**: Q 5-volley (draw/release tajam per volley), W sprint wind
  (low crouch + gait cepat + cape flare penuh), E aim presisi (tarik
  lambat, hold napas halus), R charge crouch (getar naik, lunge release
  + shiver + trail).
* **Secondary motion** velocity-driven: lag cape/hood/hair dari
  `speed01` + flare per-state; cloth roboh saat death.
* **Blink mandiri** (randf_range 1.8–3.8 s — hanya untuk ekspresi, di luar
  RNG gameplay yang dikunci paritas).

Blending di root: `k = 1 − e^(−rate·Δt)` per state (attack 26/s → snappy,
death 8/s → berat).

---

## 5. Combat feel (proporsional, dikunci)

| Momen | Feedback | Sumber |
|-------|----------|--------|
| Serangan dasar (proyektil) | **TIDAK ADA** hit-stop/impact FX/hurt flash — damage di `TowerBullet._on_hit` (paritas pygame) | — |
| Hit skill Q volley | impact tier 1 (tanpa freeze) | SkillFX |
| Cast E (shackle land) | impact tier 2 (shake 0.06) | SkillFX |
| Release R (Powershot) | impact tier 3 (hit-stop 0.05 + shake 0.14) + **trauma 0.45** | SkillFX + Combat |
| Kena pukul | hurt flash via `HurtFlash → custom_visual.modulate` (gratis) | engine |

Edge **skill release R** dideteksi di root dari state kit
(`_powershot_charging` true→false — damage kit terjadi di frame yang sama)
→ sinyal `skill_release("r")` → SkillFX (gale) + Combat (trauma).
Demo tanpa hero memakai fallback waktu (t ≥ 0.95).

**Swing-riposte** (paritas `SWING_RANGE = 64` pygame): di edge serangan,
jika `hero.target` < 64 px → state visual `swing` (damage tetap jalur
ranged — TIDAK diubah). **Aim** vertikal ke target di-lock di edge
serangan (clamp ±0.45 rad).

**Panah angin**: `Hero._shoot_projectile` memanggil
`style_projectile(bullet)` → `bullet.set_arrow_style("wind")` →
`TowerBullet._draw_wind_arrow()` (shaft, mata perak, fletch hijau-angin,
jejak angin pendek). Damage/timing TIDAK disentuh.

---

## 6. Resep Skill FX (70/20/10 — PRIMARY/SECONDARY/ACCENT)

Semua one-shot via **VFXManager pooled** (32 actor, CPU draw); bentuk
custom ringan digambar `SylaraSkillFX` di ruang lokal (ikut flip hero).
Semua FX **live-aim** ke `hero.target` (demo: `demo_target` tetap +
marker di panggung).

* **Q Focus Fire (3.0 s)** — cast: flash+ring+slash di nock, **koridor
  bidik** (band 3 lapis + dash berjalan). 5 volley (t=0.15+i·0.42):
  streak panah 2 lapis → impact tier 1 di target → 4 spark daun. Leaf
  glint ×3.
* **W Windrun (3.0 s)** — cast: ring kaki + glow tanah + **siklon**
  (VFXManager `wall` — 3 busur mengorbit, ikut hero). Ring pulse ×4,
  2 trail angin ×3 (arah velocity).
* **E Shackle Shot (2.5 s)** — cast: flash+ring nock. t=0.30: **sulur
  hidup** (sine curve 2 lapis + 5 daun, live-aim, meredup) + impact tier 2
  + cincin constriction + 6 spark; thorn (t=0.45); pulse constriction ×3;
  leaf ×3.
* **R Powershot (1.0 s)** — charge: **suction** (3 cincin menyusut ke
  nock) + halo charge. Release: **5 gale streak** paralel (staggered) +
  **gale tunnel** (3 garis lokal) + impact tier 3 di target + burst daun +
  flash putih + ring — satu freeze, satu sumber (tier 3).

---

## 7. Kontrak yang DIKUNCI (test)

* `drive()` 7 argumen + `handles_skill_fx()` → `GameplayParityTest`.
* Damage timing: basic = `TowerBullet._on_hit` (tanpa retime).
  `ATTACK_IMPACT_PROGRESS = 0.52` (sinyal `attack_impact`).
* **Basic attack = NO impact FX / hit-stop / hurt flash** →
  `tools/test_basic_attack_no_impact_fx.py` (kontrak dipertahankan).
* Durasi visual skill sinkron `VISUAL_DURATION` kit (q/w=180f, e=150f,
  r=60f) — `SKILL_DUR` di Animator & SkillFX.
* Windrun RNG & cooldown kit tidak disentuh (rig visual-only).

---

## 8. Performa Android

* **1 CanvasItem per karakter** (semua bentuk = `draw_*` CPU, aman
  Compatibility/GLES, tanpa shader partikel).
* **Zero alokasi per frame**: buffer pool 12, hash deterministik, pose
  instance di-recycle (1 `new()`/frame di Animator — objek kecil, GC-free
  via refcount).
* **VFX ter-batas**: pool 32 actor global; FX Sylara = 5–15 actor hidup
  sekaligus saat skill penuh; trail ≤ 10 titik.
* **Tidak ada** `instantiate()`/`queue_free()` di jalanan gameplay; tidak
  ada GPUParticles; tidak ada shader.
* Draw call efektif: 1 (rig) + ≤15 (VFX actor aktif) + 1 (SkillFX custom).

---

## 9. Menjalankan showcase

```
godot --path godot res://scenes/demo/SylaraDemo.tscn
```

Siklus otomatis: IDLE → WALK → RUN → ATTACK → **SWING** → Q → W → E → R →
HURT → DEATH → VICTORY. Keyboard: SPACE attack, 1/2/3/4 skill, H/D/V
override, F flip, R reset. Marker target (cincin hijau di kanan) = arah
semua FX skill di demo.

---

## 10. Pembatasan yang disengaja

* **No engine di sandbox ini** — verifikasi = checker statis (indentasi,
  bracket, preload, cross-file symbol) + CI `godot-check.yml` (pull
  request). Review visual in-game mengikuti push+PR.
* **Hit-stop hanya untuk skill** (bukan serangan dasar) — kontrak paritas
  pygame yang eksplisit.
* **Demo tanpa hero**: swing dipaksa via `demo_swing`, release R via
  fallback waktu — di arena keduanya memakai state hero/kit yang asli.
* Kaizen v4 tetap patokan kontrak `drive()`; Sylara v2 menambahkan
  `style_projectile` sebagai hook OPSIONAL (hero lain tidak terpengaruh).
