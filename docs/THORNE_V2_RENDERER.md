# Thorne v2 — Renderer Pixel-Art Masterwork

> Rewrite penuh namespace `_NS_thorne` di `heroes/_bundle.py`.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (lama) | v2 (baru) |
|---|---|---|
| Rig native (bbox idle) | 106 × 114 px | **166 × 183 px** (1.55×) |
| Kepadatan detail di layar | 1.72 px native / px layar | **2.47 px native / px layar** |
| Warna unik (idle native) | 93 | **165** |
| Ukuran di arena | ~70 px | ~70 px (sama — pipeline menormalkan) |
| Biaya render | ~1.3–2 ms | ~1.6–2.1 ms (hanya saat cache miss) |

Memperbesar rig TIDAK memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~51 px. Yang berubah
adalah **resolusi efektif** — setiap piksel layar kini disampel dari ~2.5
piksel native, sehingga cluster, ramp, dan muka tetap tajam setelah
smoothscale + lighting + outline pass.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — bayangan bulu
   dingin (cokelat-ungu), highlight hangat (amber). Volume terbaca
   sebagai cahaya, bukan pita datar.
2. **Selout (selective outlining)** — outline gelap hanya di sisi
   bayangan (kanan-bawah); sisi cahaya dibiarkan bersih + rim 1 px.
3. **Siluet bergerigi** — tepi punggung di-generate `_tuft_points()`
   dari spine + hash deterministik (aman untuk cache), bukan poligon halus.
4. **Specular sebagai cluster** — kilau bulu/baja/gold jadi 1–2 px yang
   disengaja, bukan gradien.
5. **Dither band** — 4 titik `belly_light` di perut, tekstur klasik
   pixel-art yang selamat dari downscale.
6. **Key light kiri-atas** konsisten dengan `lighting.py`
   (`LIGHT_DIR = (-1, -1)`).

## Anatomi baru

- Punuk raksasa + **kipas quill 3 lapis ber-pita**: crimson → amber →
  ivory, 9 quill belakang + 9 utama + 4 mahkota, pangkal tertutup ridge
  bulu & pauldron.
- Kepala boar **underbite**: alis berat, socket mata besar + iris amber
  + blink, moncong dengan cuping (sniff), deretan gigi bawah, 2 taring
  bezier ivory 3-band, wart pipi, telinga (twitch).
- Perlengkapan: pauldron baja ber-rivet + duri, vambrace lengan belakang,
  strap X hijau ber-jahitan, sabuk + gesper emas + pouch, rok vest sobek,
  bundle quill cadangan di pinggul, ekor tuft.
- **Mace flanged**: gagang kayu 3-band + serat + grip kulit + pommel
  emas + collar baja + kepala bola 4 flange + 6 duri + specular cluster.

## Animasi baru

- **Foot solver**: telapak menapak/terangkat bergantian (lift dari
  fase), debu saat menapak, bayangan kontak per telapak.
- **Quill inertia**: crest tertinggal dari akselerasi badan
  (`crest_tilt`), crest mengembang saat serang (`flare`).
- **Idle hidup**: napas (root bob + dada), blink, sniff, ear-twitch,
  dengus napas dari moncong, mote bulu melayang.
- **Serangan 7 keyframe** (`_attack_pose`): wind-up → tension
  (gemetar) → strike (smear sabit 3-band + leading edge) → **IMPACT**
  (squash, bintang 6 spike, shockwave elips, 5 serpihan batu) →
  follow-through → recover.
- Walk: hip bob 2× frekuensi, counter-sway, lean maju, lengan ayun
  berlawanan, debu belakang kaki.

## Ground FX & skill (retune ke rig 1.5×)

Bayangan/mist/aura/platform di-cache statis (`_static`) — dibangun
sekali, tanpa alokasi per frame. Anchor tanah pindah ke `y+58..y+66`,
aura debu 260 px, rage 300 px, platform 195 px. Telegraph Quill Spray
kini dikonversi lewat `_render_scale` sehingga **ring pas dengan
jangkauan gameplay** (bukan radius px mentah).

## Skill FX v2.1 — "mewah & terlihat" (pass lanjutan)

Masalah lama: efek hero ikut mengecil bersama sprite cache
(`_render_scale` ~0.41×) → cincin/telegraph nyaris tak terlihat di
arena. Pass ini menggambar efek **world-space** lewat `_fx_scale(boss)`
(= `1/_render_scale`, cap 2.6) sehingga ukuran di layar setara boss
asli, lalu memperkaya tiap skill:

- **Primitif baru**: `_spark_star` (bintang spike selang-seling),
  `_chevron` (panah telegraph), `_dashed_ring` (rune ring berputar),
  `_jagged_crack` (retakan zigzag deterministik), `_fx_scale`.
- **Q — Viscous Nose**: band asam lebar 2-lapis + gelembung bergerak
  + chevron berbaris menuju target + splat marker 2 cincin; charge
  jadi vortex 2 arc berlawanan + droplet orbit; spit = bintang + ring
  + kipasan droplet.
- **W — Bristleback**: shockwave aktivasi ganda + bintang 8 spike,
  rune ring ganda berlawanan arah, **duri 2 baris** (18 luar + 12
  dalam) berdenyut dengan ujung emas/putih, kubah shimmer berkelip,
  mote emas naik, glint orbit; dan **crest di badan ikut menyala
  emas** (kwarg `bristle` — ramp crest di-mix ke gold + flare).
- **E — Quill Spray**: ring jangkauan tebal + tick ring berputar +
  **ring konvergen** mengecil ke pusat (membaca "incoming") +
  chevron kardinal; tiap voli = muzzle star + ring di punggung;
  proyektil quill mewah (trail 2-tone + glint berputar di ujung).
- **R — Warpath (ultimate)**: aktivasi **pilar cahaya 4-lapis** +
  shockwave ganda + bintang; steady: **7 retakan magma radial**
  ber-zigzag dengan seam menyala, cincin aura 3-lapis + ring emas,
  mahkota api 2 ring (17 api) dengan core emas, kolom bara sway,
  wisp spiral 2 lengan, denyut pusat.

Terukur (audit): W 860 px emas di luar siluet badan, R 628 px
rage/magma di luar badan, E ring jangkauan tepat di 100 px dunia
(180/180 hit pada canvas scale 0.5), Q jalur+splat sampai target.
Biaya 2.2–3.6 ms hanya saat cache miss (bucket tiap 2 frame; perangkat
lambat otomatis 4 frame). Pilar R di-clamp `min(100·fs, 240)` agar
selalu muat di canvas cache.

## Kompatibilitas

- Semua nama publik lama dipertahankan (`PALETTE` lengkap dengan kunci
  lama + kunci baru, `draw_thorne`, `draw_boss`, pose modes, skill FX,
  projectile, helper). `heroes/thorne` alias modul tetap jalan.
- Signature `_draw_thorne_elite / _draw_elite_club / _draw_elite_quill /
  _draw_thorne_masterwork_details` tetap (kwarg baru bersifat opsional).
- Regresi: `tools/test_thorne_masterwork.py` (4 tes) — lulus.

## Alat

- `tools/_audit_thorne_v2.py` — audit terukur (skala, bbox, frame unik,
  swatch palet, coverage quill, timing, **cek FX skill world-space**) +
  4 lembar preview: `docs/thorne_v2_review.png`, `docs/thorne_v2_anim_strip.png`,
  `docs/thorne_v2_ingame.png`, `docs/thorne_v2_skills.png`, dan
  `docs/thorne_v2_before_after.png`.
- `tools/_shot_thorne_masterwork.py` & `tools/thorne_anim_demo.py`
  diperbarui ke canvas rig v2.
