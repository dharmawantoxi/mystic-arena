# Kaizen v5 — Renderer Pixel-Art + Skill FX + Swing + Projectile

> Rewrite penuh namespace `_NS_kaizen` di `heroes/_bundle.py`.
> Standar **Thorne v2 Pixel Masterwork + Grimjaw v2.1 Skill FX / swing trail**.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

> **v5 (rig rewrite from zero)**: `_draw_kaizen_elite` ditulis ulang supaya
> siluet bersih dan mudah dibaca di ukuran arena. Perubahan utama:
> wajah ¾ depan dengan dua mata jelas di bawah hachimaki (bukan profil yang
> kepalanya tampak besar), rambut kompak terjumbai di belakang kepala,
> badan tertutup rapi dengan kerah V dan sash, pauldron pindah ke belakang
> bahu, hakama/kaki memakai panel besar yang rapi, saya pendek dan bersih,
> dan aura/rim di ground di-render tipis supaya badan menonjol.

## Apa yang berubah (v3 rewrite)

| Aspek | v2 | v3 (sekarang) |
|---|---|---|
| Rig native (bbox idle) | 157 × 168 px | **157 × 168 px** (landmark sama) |
| Ukuran di arena | ~70 px | ~70 px (pipeline menormalkan) |
| Swing smear | ghost poligon + arc kaku | **jejak ujung-bilah 10 langkah, 3-band** (`_draw_katana_swing_trail`) |
| Projectile Q | arc + trail titik | **sabit terisi 3-lapis + pita trail + burst kematian** |
| Skill timer | hardcoded `/60 /90 /60 /100` | `SKILL_VISUAL_DURATION` + `_skill_progress` / `_ring_r` |
| Performa | Surface baru per primitif alpha | **scratch pool** + `_clamp` fast-path; aura tanpa `copy()` |
| Biaya skill cache-miss | ~2.1–3.2 ms | idle **1.2 ms**, Q/W/E **2.6–2.9 ms**, R **3.2 ms** (budget 3.5) |

Memperbesar rig TIDAK memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~70 px
(`_get_hero_scale("kaizen")` ≈ 0.416). Yang berubah adalah
**resolusi efektif**.

## Disiplin pixel-art

1. **Ramp 4–5 nilai per material dengan hue-shift**
2. **Selout** — outline gelap hanya sisi bayangan; sisi cahaya + rim 1 px
3. **Siluet bergerigi** — `_tuft_points()` deterministik (aman cache)
4. **Specular cluster** 1–2 px, bukan gradien
5. **Dither band** di hakama dan dada
6. **Key light kiri-atas** (`lighting.py` `LIGHT_DIR = (-1, -1)`)

## Anatomi (tetap)

- Kepala ¾, hachimaki + manik, topknot, ponytail tuft, parut pipi, iris amber
- Jaket terbuka, X-strap, obi, pauldron baja + sode, scarf inersia
- Saya lacquer + sageo, hakama pleat, kyahan + tabi, foot solver
- Katana: sori, hamon, kissaki, tsuba 4-lobe, ito, kashira, glint spekular

## Animasi + swing attack

- **Foot solver** + debu tapak
- **Inersia** ponytail / scarf / pita hachimaki
- **Idle hidup** — napas, sway, blink, daun angin, mote
- **Serangan 7 keyframe** (`_attack_pose`): wind-up → tension (gemetar) →
  strike → **IMPACT 0.54** → follow → recover. Sudut wind-up `< 0 <` IMPACT.
- **Smear ujung-bilah** (`_draw_katana_swing_trail`): 10 sampel progress
  sebelumnya, 3-band sian + leading edge putih + bintang IMPACT.
  Kepala smear **menempel di kissaki**. Wind-up tetap bersih.
- Loop closure: progress 0.00 == 1.00 (9 pose unik dari 10 sampel).

## Projectile — `WindSlashProjectile`

- Homing world-space (`source` + `_world_to_local`, anti orb-acak)
- Trail pita 3-lapis + sabit mini
- Kepala: sabit terisi 3 band + glint berputar di ujung + speed line
- Burst kematian 8 frame (`dead_frames`, bukan `age` beku)
- Spawn di jendela swing 0.45–0.55 jika `range > 80`

## Skill FX v3 — world-space, 3 fase

`SKILL_VISUAL_DURATION = {q:60, w:90, e:60, r:100}` (sinkron gameplay).
`_fx_scale` = `1/_render_scale` (cap 2.6). Telegraph E/R memakai `_ring_r`
(radius dunia **tanpa** cap) + `_aoe_marks` (tick radial + 4 bracket,
**bukan** cincin/dashed-ring amateur).

| Skill | Radius dunia | Visual |
|---|---|---|
| Q Steel Wind | jalur ke target | TELEGRAPH chevron + tick impact; AKTIVASI sabit + bintang; STEADY afterimage sabit + speed streak |
| W Wind Wall | dinding depan | TELEGRAPH chevron + bracket tanah; AKTIVASI spark; STEADY dinding 3-lapis + swirl + mote |
| E Sweep | **100 px** di `(x, y+30)` | marker AOE angular + tick konvergen + chevron; aktivasi crescent; 10 pilar |
| R Tornado | **150 px** di `(x, y+30)` | marker AOE angular + retakan + chevron; aktivasi pilar; funnel 5 lapis + lengan spiral + core |

Body reaction: `gale` (W) menyalakan scarf/bilah; `storm` (R) mata + bead.

## Kompatibilitas

Semua nama publik lama dipertahankan (`PALETTE`, `draw_kaizen`, `draw_boss`,
`WindSlashProjectile`, pose, skill FX, helper `_aacircle/_aaline/_poly/...`,
`_world_to_local`, `_target_position`, `_attack_pose`, `_fx_scale`, …).

Kwarg baru opsional: `_draw_elite_katana(..., progress=0.0)`.

## Verifikasi

- `tools/test_kaizen_masterwork.py` — 9 tes (prosedural, swatch, 7-keyframe,
  portrait LOD, Q/W/E/R, **ring E=100 / R=150 world-space**, gale/storm, selout)
- `tools/test_swing_anim.py` — swing terpicu di 60/30/15/8/5 FPS
- `tools/_audit_kaizen_v2.py` — skala, frame unik, budget 3.5 ms, FX di luar
  badan, 5 lembar preview

## Alat / preview

- `docs/kaizen_v2_review.png`
- `docs/kaizen_v2_anim_strip.png`
- `docs/kaizen_v2_ingame.png`
- `docs/kaizen_v2_skills.png`
- `docs/kaizen_v2_before_after.png` (jika baseline git tersedia)
