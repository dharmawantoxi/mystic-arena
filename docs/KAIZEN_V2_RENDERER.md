# Kaizen — Doodle Renderer Masterwork + Skill FX + Swing + Projectile

> Rewrite penuh namespace `_NS_kaizen` di `heroes/_bundle.py`.
> Standar **Grimjaw v4 Doodle Sketchbook + Skill FX / swing trail**.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

> **Doodle rewrite (dari pixel-art)**: `_draw_kaizen_elite` ditulis ulang
> dari nol ke bahasa gambar "buku sketsa". Sebelumnya Kaizen adalah
> pixel-art masterwork yang rata dan kaku; sekarang digambar tangan dengan
> pulpen tinta + spidol + krayon di atas kertas. Siluet, landmark, geometri
> bilah, controller serangan, dan jembatan lapisan FX hidup **dipertahankan
> penuh** sehingga `heroes/kaizen_fx.py` dan pipeline sprite-cache bekerja
> tanpa perubahan.

## Gaya baru: DOODLE / SKETCHBOOK

| Aspek | v5 pixel-art (lama) | Doodle (sekarang) |
|---|---|---|
| Outline | selout solid (1 px rim) | **garis tinta bergoyang** (`_ink_stroke`/`_ink_polyline`) — jitter deterministik hash, 2 pass |
| Isi | ramp 4–5 band hue-shift | **isi spidol bercelah kertas** (`_marker_poly` + `_inset_pts`) — celah kertas ~1.5 px ke centroid antara fill & tinta |
| Bayangan | dither band | **arsiran pensil** (`_hatch_patch`) + **skribel loop** (`_scribble`) |
| Highlight | specular cluster 1–2 px | **goresan gel-pen putih** (`ink_stroke` warna terang) |
| Rambut/pita | tuft_points bergerigi | **gumpalan blob ber-tinta + lock terjumbai** + arsir gel-pen |
| Angin (FX) | cincin/arc kaku halus | **lidah teardrop doodle** (`_wind_tongue`) + skribel sian + bintang gambar-tangan + awan "poof" |
| Baja katana | ramp baja dingin | **isi spidol baja + garis tinta tepi + hamon bergoyang + gel-pen shine** |

Semua jitter adalah **fungsi murni dari pose/seed** (`_seed_q` kuantisasi
fase → seed stabil), sehingga sprite cache tetap valid; ganti fase animasi
= garis "mendidih" (boiling lines) seperti animasi tangan.

## Anatomi (tetap, kontrak dipertahankan)

- Kepala ¾, hachimaki + manik, topknot, ponytail tuft, iris amber
- Jaket tertutup, kerah V, obi, pauldron belakang, scarf inersia
- Saya lacquer + sageo, hakama pleat, kyahan + tabi, foot solver
- Katana: sori, hamon, kissaki, tsuba 4-lobe, ito, kashira, glint gel-pen

## Animasi + swing attack

- **Foot solver** + debu tapak
- **Inersia** ponytail / scarf / pita hachimaki
- **Idle hidup** — napas, sway, blink, lidah angin naik, mote
- **Serangan 7 keyframe** (`_attack_pose`): wind-up → tension → strike →
  **IMPACT 0.54** → follow → recover. Sudut wind-up `< 0 <` IMPACT.
- **Smear ujung-bilah** (`_draw_katana_swing_trail`): 10 sampel progress
  sebelumnya, 3-band sian + leading edge putih + bintang doodle IMPACT.
- Loop closure: progress 0.00 == 1.00 (9 pose unik dari 10 sampel).

## Projectile — `WindSlashProjectile`

- Homing world-space (`source` + `_world_to_local`, anti orb-acak)
- Trail pita 3-lapis + sabit mini
- Kepala: sabit terisi 3 band + glint berputar di ujung + speed line
- Burst kematian 8 frame (`dead_frames`) — awan "poof" + bintang doodle

## Skill FX — world-space, 3 fase

`SKILL_VISUAL_DURATION = {q:60, w:90, e:60, r:100}` (sinkron gameplay).
`_fx_scale` = `1/_render_scale` (cap 2.6). Telegraph E/R memakai `_ring_r`
(radius dunia **tanpa** cap) + `_aoe_marks` (tick radial + bracket,
**bukan** cincin/dashed-ring amateur) yang kini digambar dengan
outline-tinta (`_skill_outlined_line`) agar tegas di terrain terang.

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

Palet doodle menambah kunci `ink`, `ink_soft`, `paper` dan mempertahankan
semua kunci yang disinkronkan `heroes/kaizen_fx.py` (`wind_*`, `steel_*`,
`saya_*`, `cord_mid`, `ink`).

## Verifikasi

- `tools/test_kaizen_masterwork.py` — 9 tes (prosedural, swatch, 7-keyframe,
  portrait LOD, Q/W/E/R, **ring E=100 / R=150 world-space**, gale/storm, selout)
- `tools/test_kaizen_fx_combat.py` — **49 tes** (kontrak FX hidup, trail,
  projectile, lifecycle skill, hit-stop, shake, supresi ganda)
- `tools/test_swing_anim.py` — swing terpicu di 60/30/15/8/5 FPS
- `tools/_audit_kaizen_v2.py` — skala, frame unik, budget 3.5 ms (idle 0.86,
  skill ≤ 3.1 ms), FX di luar badan, 5 lembar preview

## Alat / preview

- `tools/_shot_kaizen_doodle.py` → `docs/kaizen_doodle_preview.png` (lembar 4 pose)
- `tools/_shot_kaizen_doodle_closeup.py` → `docs/kaizen_doodle_closeup.png`
- `tools/_shot_kaizen_fx.py` → `docs/kaizen_v3_combat_fx.png` (6 momen tempur)
- `tools/_shot_kaizen_masterwork.py` → `docs/kaizen_masterwork_preview.png`
- `tools/_audit_kaizen_v2.py` → `docs/kaizen_v2_review.png` +
  `kaizen_v2_anim_strip.png` + `kaizen_v2_ingame.png` + `kaizen_v2_skills.png`
