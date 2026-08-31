# Drakar v2 — Renderer Pixel-Art Masterwork + Skill FX v2.1

> Rewrite penuh namespace `_NS_drakar` di `bosses/level1.py`.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (ORIGINAL-MAX) | v2 (baru) |
|---|---|---|
| Rig native (bbox idle) | 240 × 240 px | **360 × 360 px** (1.5×) |
| Kepadatan detail | ~1.9 px native / px layar | **~2.8 px native / px layar** |
| Warna unik (idle native) | ~180 | **~246** |
| Warna unik (attack) | ~220 | **~445** |
| Ukuran di arena | ~82 px | ~82 px (sama — pipeline menormalkan) |
| Biaya render | ~1.5–2 ms | ~2.5–3.5 ms (hanya saat cache miss) |

Memperbesar rig TIDAK memperbesar boss di arena: pipeline normalisasi
di `heroes/__init__.py` mengukur badan lalu men-scale agar tinggi final
tetap konstan. Yang berubah adalah **resolusi efektif** — setiap piksel
layar kini disampel dari ~2.8 piksel native, sehingga detail anatomi,
senjata, dan efek tetap tajam.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4-5 nilai per material dengan hue-shift** — bayangan kulit
   didorong dingin (merah-ungu gelap), highlight hangat (amber-koral).
   Volume terbaca sebagai cahaya, bukan pita datar.
2. **Selout** — outline gelap hanya di sisi bayangan (kanan-bawah);
   sisi cahaya dibiarkan bersih + rim 1 px.
3. **Siluet bergerigi** — rambut liar di-generate `_tuft_points()`
   dari spine + hash deterministik (aman untuk cache), bukan poligon halus.
4. **Specular sebagai cluster** — kilau dada/baja/blade jadi 1-2 px
   yang disengaja, bukan gradien.
5. **Dither band** — 4 titik `skin_light` di perut, tekstur klasik
   pixel-art yang selamat dari downscale.
6. **Key light kiri-atas** konsisten dengan `lighting.py`.

## Anatomi baru

- Barbarian berotot besar dengan dua tangan memegang kapak (two-handed axe).
- Kepala: brow ridge berat, socket mata besar + iris amber + glow saat attack,
  hidung lebar, rambut liar bergerigi via `_tuft_points`, janggut tebal 3-lapis.
- Badan: dada berotot dengan pectoral definition + central divide + 6-pack abs,
  scar diagonal di dada, bandolier diagonal kulit 5-band, sabuk besar dengan
  gesper armor + rune berdenyut, loincloth ber-lipat + ujung logam.
- Perlengkapan: **pauldron besi besar** ber-3 spike + rivet, vambrace di
  lengan depan, sarung tangan kulit.
- **Kapak besar**: gagang kayu 3-band + serat kayu + grip wrap kulit +
  pommel emas 3-band + collar baja + kepala kapak crescent 6-lapis +
  specular cluster + darah di blade saat attack.
- Kaki: paha leather pants + straps + studs + knee guard armor 5-band +
  boot berat + metal boot cap + toe stud.

## Animasi baru

- **Foot solver**: telapak menapak/terangkat bergantian (lift dari fase).
- **Idle hidup**: napas (root bob + dada), attack eye-glow.
- **Serangan 5 keyframe**: wind-up → tension → **IMPACT** (smear sabit
  5-band + leading edge) → follow-through → recover.
- Walk: hip bob 2× frekuensi, counter-sway, lean maju.

## Ground FX & skill (world-space via `_fx_scale`)

Semua efek skill dikompensasi `_render_scale` via `_fx_scale(boss)`
(= `1/_render_scale`, cap 2.6) sehingga ukuran di layar setara boss asli.

### Primitif FX baru
- `_spark_star` — bintang spike selang-seling + inti
- `_chevron` — panah telegraph menghadap arah
- `_dashed_ring` — rune ring berputar
- `_jagged_crack` — retakan zigzag deterministik
- `_tuft_points` — tepi bergerigi (rambut, api)

### Skill Q — Battle Hunger (self-buff rage)
- **AKTIVASI**: shockwave elips + bintang 8-spike
- **STEADY**: aura berlapis 3 cincin + retakan magma 5 radial
  (`_jagged_crack`) + mote ember naik
- **FOREGROUND**: kolom api 8 titik 6-lapis + core glow + blood spatters

### Skill W — Counter Helix (spin attack)
- **AKTIVASI**: shockwave + bintang 8-spike besar
- **STEADY**: ring dashed ganda berlawanan arah + 4 arc trail spin +
  glint orbit 6 titik
- **BODY FX**: helix crescent 5-lapis berputar + blood particles 28 titik

### Skill E — Berserker's Call (war cry, AoE)
- **AKTIVASI**: shockwave elips + bintang 6-spike
- **STEADY**: ring konvergen `_dashed_ring` + **chevron berbaris** 8 arah
- **FOREGROUND**: glow radial + 12 mote + expanding wave 28 partikel +
  14 ray beam

### Skill R — Culling Blade (targeted execute)
- **AKTIVASI**: ring konvergen + chevron menuju target + spark_star
- **STEADY**: filled ring + **7 retakan magma radial** (`_jagged_crack`)
- **FOREGROUND**: charge glow multi-layer → slash silang 6-lapis +
  core burst + bintang impact 8-spike + spatter → fade residual

## Kompatibilitas

- Semua nama publik lama dipertahankan: `PALETTE`, `draw_drakar`,
  `_drk_body_surface`, `_target_position`, `_update_drk_attack_anim`,
  `_detect_moving`, semua skill draw methods.
- Signature `draw_drakar(surface, boss, x, y)` tetap sama.
- Kwarg baru pada `_drk_body_surface` (`battlehunger`, `helix_active`,
  `berserk_call`, `rage_mode`) bersifat opsional.
- Regresi: `tools/test_drakar_max.py` (6 tes) — lulus.

## Alat

- `tools/test_drakar_masterwork.py` — 29 cek: rig 1.5x, FX helper, semua
  mode render, animasi kontinu, frame unik, world-space, prosedural,
  palette lengkap, timing < 10ms.
- `tools/_audit_drakar_v2.py` — audit terukur (skala, bbox, warna unik,
  coverage FX, timing, preview sheets) + 4 lembar preview:
  `docs/drakar_v2_review.png`, `docs/drakar_v2_anim_strip.png`,
  `docs/drakar_v2_skills.png`, `docs/drakar_v2_ingame.png`.
- `tools/test_drakar_max.py` — regresi lama (6 tes), diperbarui untuk
  rig 1.5x.
