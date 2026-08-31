# Morgath v2 — Renderer Pixel-Art Masterwork + v2.1 Skill FX + v2.2 Bolt

> Rewrite penuh namespace `_NS_morgath` di `bosses/level1.py`.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (lama) | v2 (baru) |
|---|---|---|
| Rig native | 74 × 100 px | **154 × 117 px** (buffer; konten dibatasi extents semua pose) |
| Badan padat (mask ≥ 100) | ~55 px | **~103 px** (luas padat 1.65×, warna 2.8×) |
| Warna unik (idle native) | 27 | **68** (portrait LOD 78) |
| Ukuran di arena (boss) | H ~91 px (dgn FX) | **H ~113 px** (di bawah gornak 119 — kontrak keluarga) |
| Ukuran di lane | ~51 px final | ~51 px final (sama — pipeline menormalkan) |
| Biaya render | — | **~1.1 ms** (hanya saat cache miss; budget 3.5 ms) |
| Skill FX | raw canvas px (mengecil ikut sprite) | **world-space** (1/_render_scale, cap 2.6) |

Memperbesar rig TIDAK memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~51 px. Yang
berubah adalah **resolusi efektif** — setiap piksel layar disampel dari
lebih banyak piksel native, sehingga cluster, ramp, dan orb tetap tajam
setelah smoothscale + lighting + outline pass.

## Skala tunggal untuk semua jalur

Pola Thorne/Gornak v2: **satu `SCALE` (0.74)** untuk jalur boss 1x,
canvas lane hero, dan portrait Hero Shop. Pipeline mengukur jalur boss
(`_measure_native_size`) lalu menormalkan lane; memecah skala per jalur
(percobaan awal `K_BOSS ≠ SCALE`) memecah pengukuran pipeline — jangan
diulang. `K_BOSS` dipertahankan sebagai alias `SCALE` untuk kompatibilitas.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — robe ungu
   ber-shift ke biru-violet di bayangan; gold ber-shift ke cokelat;
   orb 6 band dari navy → cyan-white (nilai tertinggi di sprite).
2. **Selout** — bayangan internal (orb shadow band, hood lipatan) +
   outline siluet gelap 4 arah di `_draw_mor_rig_at` (pola Gornak).
3. **Siluet bergerigi** — hem cape & skirt di-generate `_tuft_points()`
   dari spine + hash deterministik (aman cache), bukan poligon halus.
4. **Specular sebagai cluster** — glint kaca orb kiri-atas 1–2 px,
   kilau pauldron/rivet, bukan gradien.
5. **Dither band** — rok jubah & cape memakai `_dither_rows()` 50%
   sebagai transisi mid→light.
6. **Key light kiri-atas** konsisten dengan `lighting.py`
   (`LIGHT_DIR = (-1, -1)`) — `GRAD_BOX` TETAP antar pose supaya arah
   lampu tidak "berkedip".

## Anatomi baru

- **Hood berlipat** dengan puncak menukik, 3 lipatan selout, mahkota
  diadem emas, dan **antena arc kembar** (sirip logam) yang memercikkan
  busur listrik saat serang/skill (puncak dijaga ≤ CY−62 agar tidak
  menyentuh HP bar boss).
- **Orb kristal 6 band** di rongga hood gelap (focal point paling
  terang) + halo dua lapis, facet lines, pusaran energi, dan **4 shard
  rune mengorbit** dengan glint.
- **Cuirass 5 band** + keystone arc (menyala sesuai skill) + gorget;
  **pauldron depan/belakang** ber-rivet dengan stud arc.
- **Sabuk emas** dengan **grimoire berantai** yang berayun (inertia) +
  tassel bergoyang.
- **Arc staff "Tempus"** tertanam: gagang 3 band + rune, **finial
  kristal melayang** di atas kepala staff dengan glow sewarna skill.
- Lengan: sleeve robe ber-lengan dengan selout, **gauntlet muzzle**
  (sumber beam) dengan node sihir di telapak yang menyala sesuai skill.

## Animasi baru

- **Foot solver**: boots menapak saat walk (lift dari fase + dust
  deterministik), bayangan kontak, hem cape/skirt tetap terpatok di
  garis tanah (`FEET_DY`) di semua pose.
- **Inertia/secondary motion**: cape sway membesar ke arah hem (lag +
  overshoot), staff/tassel/grimoire berayun beda fase.
- **Idle hidup**: napas (root bob), hover orb, shard orbit berputar,
  mote sihir naik, percik antena frame-gated deterministik.
- **Serangan 7 keyframe** (`_attack_pose`): rest → wind-up → tension
  (tremble 1 px) → thrust → **IMPACT HOLD di muzzle (0.90–0.96)** →
  release → recover; kurva `_mor_attack_curve` monoton dengan hold
  tegas (pola Gornak).
- **Smear berlapis 3 band** di jendela thrust + **burst IMPACT**
  (bintang 8-spike + shockwave ganda + forks + serpihan) saat ap ≈ 0.90.

## Skill FX v2.1 (world-space)

Semua efek memakai `_fx_scale(boss)` = 1/_render_scale (cap 2.6) dan
`_ring_r(boss, world_px, surface)` yang men-clamp radius ke dalam canvas
cache. Tiap skill punya **3 fase** dan **badan ikut bereaksi** (pose
khusus + orb/keystone/gauntlet menyala):

| Skill | Telegraph | Aktivasi | Steady |
|---|---|---|---|
| **Q Spark Wraith** | chevron berbaris ke target + splat ring | vortex 2 lengan + bintang di telapak | orb terbang (kurva bezier) + trail 2-tone + glint orbit + IMPACT bintang |
| **W Flux** | 3 ring konvergen di TARGET (38 px dunia) | pilar ungu + shockwave ganda | pool berlapis + dashed ring berlawanan + wisps/mote/ember + core mendidih |
| **E Magnetic Field** | ring konvergen → **tepat 90 px dunia** | shockwave + bintang 8-spike | kubah statis (cached, smoothscale) + hex grid + spark berputar + busur petir |
| **R Tempest Double** | retakan zigzag + ring konvergen di **±60 px dunia** | pilar 4 lapis + burst petir radial 12 bolt | 2 ghost clone (rig buffer re-blit + tint) + tether listrik + bara/wisp/glint |

- Proyektil (beam basic & orb Q) memakai trail berlapis + glint di ujung.
- Surface statis (aura, rune, bayangan, kubah E) dibangun sekali via
  `_static()` lalu di-blit — tidak ada alokasi per frame.
- Aura memakai falloff α^4: pita alpha ≥ 100 selalu di dalam siluet
  badan di kedua jalur, jadi mask pengukuran pipeline melihat badan
  (aturan `_BODY_ALPHA_THRESHOLD`), bukan lingkaran aura.

## Basic attack — Lightning Bolt v2.2 (mewah)

Beam dasar bukan lagi garis putus-putus sederhana. `_draw_lightning_
projectile` di-rewrite penuh dengan **8 lapis elemen**, semuanya
prosedural & deterministik per-frame (belum ada PNG apa pun):

1. **Chord petir tepi-ke-tepi** — polyline bertekuk di tengah tiap
   segmen; tekukan morph hidup tiap frame (2 oktaf sinus + pulse),
   3 lapis pita (arc_dark → arc_mid → arc_light) dengan lebar menirus
   5→1 px menuju kepala + **offset tegak lurus antar lapis** (kesan
   heliks listrik), inti arc_hot menyala di 40% ujung dekat kepala.
2. **Ranting letik menyimpang** — 3 cabang `_jagged_line` 2-lapis
   dengan sisi selang-seling per-frame.
3. **Trail after-image berlubang** — 3 ghost ring (isi gelap + rim
   arc_mid) mengikuti kepala bolt.
4. **Mote bara listrik** — 4 piksel percik deterministik berjatuhan
   dari lintasan.
5. **Bloom radial** — sprite glow 4-band dibangun sekali via
   `_static()` (cache miss saja), di-blit dengan `set_alpha` +
   restore di kepala & telapak.
6. **Kepala bolt** — flare 5 lapis (arc_darkest → arc_hot) + inti
   putih + 2 paku cahaya silang berputar + **glint orbit 3 titik**
   (dulu 2 statis).
7. **Percik pelepasan** — bintang `_spark_star` 6-spike di telapak
   saat bolt lahir (t < 0.25).
8. **Benturan penuh** — ring ganda + bintang 8-spike + 8 garis
   radial + 5 serpihan deterministik (t > 0.88).

Kontrak tetap: lahir dari `MOR_MUZZLE` rig di semua skala render,
nol piksel sebelum progress 0.55, clamp ke canvas cache, dan budget
~0.6 ms untuk frame impact penuh (jauh di bawah 3.5 ms).

## Validasi

- `tools/test_morgath_masterwork.py` — 11 tes: prosedural murni,
  rig tunggal, band bbox keluarga, kaki menapak semua pose, buffer
  tidak terpotong, 8 pose unik, beam lahir dari telapak, outline,
  kurva serang monoton, portrait LOD, jalur lane + beam pass.
- `tools/_audit_morgath_v2.py` — audit terukur: ukuran layar final,
  keunikan frame, timing, presisi ring E 90 px dunia pada fs ∈ {1.0,
  0.45} (180/180 sample), clone R ±60 px, pool W di target, clamp
  canvas, before/after vs snapshot v1, plus **blok bolt v2.2**
  (lahir dari telapak, 5 band arc, kekayaan di luar sumbu, 8 frame
  morph unik, impact ring/spike, budget ≤ 3.5 ms).
- Regresi lintas: `test_hero_lighting`, `test_hero_hd_render`,
  `test_swing_anim`, `test_renderer_projectiles_not_baked`,
  `test_gornak_masterwork` (kontrak keluarga), `test_gale_morgath`.
- Preview: `docs/morgath_v2_review.png`, `morgath_v2_anim_strip.png`,
  `morgath_v2_ingame.png`, `morgath_v2_skills.png`,
  `morgath_v2_before_after.png`, `morgath_v2_bolt.png` (generator:
  `tools/_shot_morgath_v2.py`).
