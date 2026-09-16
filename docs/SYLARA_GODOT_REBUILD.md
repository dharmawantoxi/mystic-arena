# Sylara — Godot 4.x Character (Procedural Rig + Pooled VFX)

Karakter **Sylara** (Wind Ranger — recurve bow, daun, angin laminar)
diimplementasikan sebagai **rig prosedural Godot-native**: satu CanvasItem
`_draw()` berlapis + animator pose + sequencer skill FX pooled. Bukan
sprite strip, bukan placeholder geometris.

* Karakter: `hero_type = "sylara"` (Wind Ranger).
* Referensi kualitas: Wind Ranger Dota 2 (silhouette, readability, combat
  feel) — sebagai **benchmark kualitas, bukan untuk disalin**. Identitas
  Sylara: hijau hutan + emas daun + busur recurve + sihir angin.
* Target platform: **Android** (renderer Mobile / Compatibility).

---

## 1. Architecture

```
sylara/
├── SylaraSkeleton.tscn   — scene tree (root + Renderer + SkillFX + Feel)
├── SylaraSkeleton.gd     — root: state machine, blending, drive() API, sinyal,
│                            pemilihan swing otomatis, hook proyektil
├── SylaraRenderer.gd     — pose → gambar _draw() berlapis (1 CanvasItem)
├── SylaraAnimator.gd     — state → pose target (tulis pakai-ulang, tanpa alokasi)
├── SylaraPose.gd         — data pose tulang + secondary motion (+ reset())
├── SylaraSkillFX.gd      — skill key → urutan VFX pooled (bidik target asli)
├── SylaraCombatFeel.gd   — sinkron audio/shake/hit-stop/arc + impact R tertunda
├── SylaraArrow.gd        — visual proyektil basic attack (subclass TowerBullet)
└── SylaraPalette.gd      — palet terkontrol (satu-satunya sumber warna)
```

**Bukan bagian arsitektur** (sengaja): gameplay Sylara (damage, cooldown,
buff/debuff, timer kit) milik `HeroSkillKit.sylara_*` + `CombatSystem` yang
parity-locked terhadap pygame. Rig ini **murni visual + feel** dan tidak
boleh mengubah state gameplay — dikunci `GameplayParityTest`
(experimental_hero_rigs on/off hasilnya identik).

**File yang dihapus** (sistem paralel mati, tidak direferensikan, layer
collision tidak kompatibel arena): `Sylara.tscn`, `Sylara.gd`,
`SylaraCombat.gd`, `SylaraHitbox.gd`, `SylaraHurtbox.gd`, `SylaraAudio.gd`.
Satu-satunya controller hero adalah `Hero.gd` generik.

---

## 2. Visual Identity

**Palet** (`SylaraPalette.gd` — BASE → SHADOW → HIGHLIGHT → MAGIC ACCENT):

- Hijau hutan `#376234` — tunic, hood, cape (identitas utama)
- Emas `#aa8228` — trim, buckle, quiver band (aksen hangat)
- Kayu `#825a32` — busur recurve (senjata utama)
- Angin `#6ec35a` — sihir (AKSEN, bukan dominan)

**Siluet** (harus terbaca saat zoom out): hood + cape berkibar + quiver +
busur recurve. Detail identitas: telinga elf, mata emerald + blink, vest
kulit + clasp permata angin, pauldron bahu depan, pisau sabuk, bracer,
cuff boots.

**Lapisan gambar** (belakang → depan): ground shadow → cape/hair/quiver/
lengan belakang/kaki belakang → kaki depan/boots/tunic/torso → belt/vest/
hood → kepala/wajah → lengan depan/pauldron/busur+panah → rim light +
wind wisps → hurt flash seluruh badan.

---

## 3. Animation System

### State Machine

```
Hero._drive_visual / Demo
    ↓ drive(phase, action, attack_progress, facing, is_moving, skill, delta)
SylaraSkeleton._derive_state()   → override > skill > attack/swing > gerak > idle
    ↓
SylaraAnimator.compute(..., pose_target)   → tulis pakai-ulang (nol alokasi)
    ↓
_blend_pose(pose_current → pose_target)    → lerp sudut (anti-robotic)
    ↓
SylaraRenderer._draw()
```

### Sinkronisasi serangan (RELEASE-FIRST)

`Hero.try_attack()` melepaskan proyektil / damage **instan di ap=0**
(paritas pygame — tidak boleh digeser). Karena itu siklus serangan
dirancang terbalik dari biasanya:

```
ap 0.00 = RELEASE / STRIKE (tali snap + proyektil beterbangan)
   ↓ FOLLOW-THROUGH → READY → ANTICIPATION → DRAW (wrap = lepas lagi)
```

Sinyal `attack_impact` menyala di `ATTACK_IMPACT_PROGRESS = 0.08`.
Melee riposte (`swing`) dipilih otomatis saat target hero ≤ 64 px
(dibaca dari `Hero.target` — tanpa mengubah `Hero.gd`).

### Animation States

| State | Trigger | Catatan |
|-------|---------|---------|
| idle / walk / run | gerak | napas, stride, secondary cloth |
| attack | ap 0→1 | release-first, sinkron spawn |
| swing | target ≤ 64px | strike-first, sabit via Feel |
| skill_q/w/e/r | active_skill | fase pre/cast/impact/aftermath |
| hurt | HP turun terdeteksi | recoil + tint seluruh badan |
| death | Hero.die() | robah dramatis + fade (0.9 dtk, lalu hide) |
| victory | demo/showcase | angkat busur |

Secondary motion: cape 3 segmen, hood 2 segmen, rambut 3 segmen,
eye blink mandiri — kontinu berbasis fase cloth.

---

## 4. Combat Feel

| Jalur | Sinkronisasi |
|-------|--------------|
| Basic ranged | spawn `SylaraArrow` dari ujung busur di ap=0 + kilatan nock kecil di impact. **Nol** impact FX / hit-stop / shake (kontrak `test_basic_attack_no_impact_fx`). |
| Basic melee | damage instan + **satu** sabit angin di ujung busur (world-space, pooled). |
| Skill Q/W/E | shake + suara dari kit saat cast (sudah ada); visual FX mengikuti. |
| Skill R | charge 0–0.45 dtk → release (visual + bunyi busur) → **impact di 0.95 dtk = momen damage** (flash + ring + sparks terarah + hit-stop 0.05 + shake 0.14 + sinyal `skill_impact`). |
| Kematian | `Hero.die()` → `hide()` instan (kontrak paritas `Dead hero is hidden`); pose death + FX perpisahan tersedia di demo/showcase via `play("death")`. |

Sinyal: `attack_started`, `attack_impact`, `skill_cast(key)`,
`skill_impact("r", pos)`, `character_hurt`, `character_died`.

---

## 5. Skill Visual Effects (anggaran pool!)

`VFXManager` = **32 aktor untuk SELURUH arena**. Tiap skill Sylara dibatasi
±12 aktor konkuren (sebelumnya R ≈ 25, Q ≈ 21 — memakan efek hero lain):

| Skill | Komposisi | Puncak |
|-------|-----------|--------|
| Q Focus Fire | 5 streak (1/ panah, ke target asli) + 1 ring + 1 flash + sparks + ring kaki | ±7 |
| W Windrun | 6 hembusan + 1 ring aura 70px + 2 sabit siklon + sparks + glow tanah | ±12 |
| E Shackle Shot | 2 sulur (nock → target asli) + 1 ring + 1 flash + 3 node daun + sparks + glow | ±8 |
| R Powershot | charge (2 ring + 3 sedot + flash + glow) → 5 panah kerucut + tunnel + sparks → impact terjadwal | ±12 |

Aturan: 70% bentuk solid primer, 20% sekunder terarah, 10% aksen.
Glow hanya aksen. Trail proyektil pendek (3 titik).

---

## 6. Integration

### RendererRegistry

```gdscript
const HERO := {
    "kaizen": preload("res://scenes/hero/kaizen/KaizenSkeleton.tscn"),
    "sylara": preload("res://scenes/hero/sylara/SylaraSkeleton.tscn"),
}
```

Aktif saat `mystic/rendering/experimental_hero_rigs=true` (default);
fallback = strip bake pygame.

### Hook Hero.gd (1 titik, aditif & parity-safe)

1. `_shoot_projectile()` → `custom_visual.spawn_attack_projectile(t, dmg)`
   bila rig menyediakannya (parameter TowerBullet identik — hanya gambar
   + titik spawn dari ujung busur yang berbeda).
2. (Death visual DITOLAK — kontrak paritas mengunci hero mati langsung
   hidden; pose `death` hanya untuk demo/showcase.)

### Demo

`godot/scenes/demo/SylaraDemo.tscn` — siklus penuh
IDLE → WALK → RUN → ATTACK → SWING → Q → W → E → R → HURT → DEATH →
VICTORY + kontrol keyboard (SPACE/1-4/H/D/V/F/R).

---

## 7. Performance (Android)

- 1 CanvasItem per hero; `_draw()` CPU tanpa shader partikel.
- Nol alokasi per frame: pose pakai-ulang, VFX pooled (nol
  instantiate/free), Feel `_process` hanya hidup saat antrean terisi.
- Tiap skill ≤ ±12 aktor pool; basic attack = 0 aktor pool
  (proyektil TowerBullet, bukan VFX).
- Tidak ada `_process` polling — semua event-driven via `drive()`.

---

## 8. Files Reference

### Core Scripts

- `godot/scenes/hero/sylara/SylaraSkeleton.gd` (+ `.tscn`) — root controller
- `godot/scenes/hero/sylara/SylaraRenderer.gd` — renderer prosedural
- `godot/scenes/hero/sylara/SylaraAnimator.gd` — state machine animasi
- `godot/scenes/hero/sylara/SylaraPose.gd` — data pose
- `godot/scenes/hero/sylara/SylaraSkillFX.gd` — sequencer skill FX
- `godot/scenes/hero/sylara/SylaraCombatFeel.gd` — lapisan combat feel
- `godot/scenes/hero/sylara/SylaraArrow.gd` — proyektil basic attack
- `godot/scenes/hero/sylara/SylaraPalette.gd` — palet

### Integration

- `godot/scripts/render/RendererRegistry.gd` — registrasi rig
- `godot/scenes/hero/Hero.gd` — hook proyektil + death visual
- `godot/scenes/hero/HeroSkillKit.gd` (`sylara_*`) — gameplay (JANGAN UBAH —
  parity-locked, hasil transpile `hero_skills/_bundle.py`)
- `godot/scenes/demo/SylaraDemo.tscn` (+ `.gd`) — showcase

---

## 9. Quality Checklist

- [x] Siluet kuat (hood + cape + quiver + recurve bow)
- [x] Identitas jelas, senjata/tubuh/wajah terbaca
- [x] Outline tinta tertutup, depth/shadow/highlight/rim terkontrol
- [x] Idle hidup; walk/run natural; attack/swing sinkron damage
- [x] Anticipation → impact → follow-through → recovery di semua aksi
- [x] Secondary motion (cape/hood/hair/blink) + easing natural
- [x] Skill FX: primer jelas, partikel terkontrol, glow aksen,
      tidak menutupi battlefield, anggaran pool ±12
- [x] Impact R di momen damage + hit-stop + shake proporsional
- [x] Basic attack: nol impact FX / hit-stop / shake (kontrak)
- [x] Death anim + FX tersedia (demo/showcase; arena hide instan per kontrak paritas)
- [x] Nol alokasi per frame; event-driven; Android-friendly
- [x] `gdparse` + `tscn_lint` + `check_refs` + `particles_lint` +
      `map_clutter_lint` + `log_gate` lolos
