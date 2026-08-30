# Kaizen v2 — Renderer Pixel-Art Masterwork + Skill FX v2.1

> Rewrite penuh namespace `_NS_kaizen` di `heroes/_bundle.py`.
> Standar mengikuti **Thorne v2 Pixel Masterwork + Thorne v2.1 Skill FX**
> (lihat docs/THORNE_V2_RENDERER.md).
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (lama) | v2 (baru) |
|---|---|---|
| Rig native (bbox idle) | 104 × 112 px | **158 × 168 px** (~1.5×) |
| Ukuran di arena | ~70 px | ~70 px (sama — pipeline menormalkan) |
| Warna unik (idle native) | 245 | **330+** |
| Biaya render pose | ~0.8 ms | ~1.1–1.6 ms (hanya saat cache miss) |
| Biaya render skill | — | avg 2.1–3.2 ms per frame (budget 3.5 ms) |

Memperbesar rig TIDAK memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~70 px
(`_get_hero_scale("kaizen")` otomatis 0.695 → 0.416). Yang berubah
adalah **resolusi efektif** — setiap piksel layar kini disampel dari
lebih banyak piksel native, sehingga ramp, cluster, dan muka tetap
tajam setelah smoothscale + lighting + outline pass.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — kulit hangat ke
   highlight, rambut bayangan dingin, indigo jaket mengarah ungu di
   bayangan dan sian di cahaya; volume terbaca sebagai cahaya.
2. **Selout (selective outlining)** — outline gelap hanya di sisi
   bayangan (kanan-bawah relatif hadap); sisi cahaya bersih + rim 1 px.
3. **Siluet bergerigi** — ponytail, ujung scarf, dan hem hakama
   di-generate `_tuft_points()` dari spine + hash deterministik
   (aman untuk cache), bukan poligon halus.
4. **Specular sebagai cluster** — kilau baja/emas/dada jadi 1–2 px
   yang disengaja, bukan gradien.
5. **Dither band** — `_dither_dots()` 50% klasik di hakama dan sisi
   bayangan dada.
6. **Key light kiri-atas** konsisten dengan `lighting.py`
   (`LIGHT_DIR = (-1, -1)`).

## Anatomi baru

- **Kepala**: wajah ¾ ekspos (mahkota rambut hanya di atas ikat kepala),
  alis tebal, mata iris amber + pupil + glint + blink, parut pipi,
  manik hachimaki menyala saat ultimate, topknot chonmage ber-wrap tinta,
  2 pita hachimaki berinersia cepat.
- **Badan**: jaket terbuka dua sisi + dada kulit 3 plane, X-strap kulit
  berjahitan, obi anyam + knot belakang + aksen emas, pauldron baja
  abu-abu dingin ber-rivet + rim emas + specular cluster (hue terpisah
  dari scarf), sode 2 lame di bahu belakang, scarf ekor tunggal
  ramping berinersia.
- **Pinggul & kaki**: saya lacquer merah-delagma 3 band + sageo + kojiri
  emas, hakama panel berlipat + hem bergerigi + dither, kyahan + tabi
  putih, sandal + tali; **foot solver** — kaki langkah terangkat dari
  fase stride, telapak tumpuan menapak + debu.
- **Katana masterwork** (`_draw_elite_katana`): kurva sori, hamon
  bergelombang, kissaki facet, tsuba 4-lobe emas, tsuka wrap berlian
  ito, kashira emas, glint spekular meluncur sepanjang bilah,
  glow buff (gale/storm/attack) di tepi potong.

## Animasi baru

- **Foot solver** + debu tapak (hanya saat |stride| mendekati 1).
- **Inersia/secondary motion** — ponytail, scarf, dan pita hachimaki
  bergerak dengan fase tertunda dari badan.
- **Idle hidup** — napas root-bob, sway berat badan kiri-kanan, blink,
  daun angin melayang, mote, wisps orbit.
- **Serangan 7 keyframe** (`_attack_pose`): wind-up → tension (gemetar
  1 px) → strike → **IMPACT** (squash, bintang, shockwave elips,
  serpihan) → follow → recover. Smear sabit 3-band + afterimage
  katana + leading edge HANYA aktif di jendela strike 0.3–0.72
  (wind-up menampilkan bilah terangkat yang bersih).

## Skill FX v2.1 — "mewah & terlihat" (world-space)

Masalah lama: efek hero ikut mengecil bersama sprite cache
(`_render_scale` ~0.42×) → cincin/telegraph nyaris tak terlihat di
arena. Pass ini menggambar efek **world-space** lewat `_fx_scale(boss)`
(= `1/_render_scale`, cap 2.6) sehingga ukuran di layar setara boss
asli, lalu memperkaya tiap skill dengan 3 fase jelas:

- **Primitif**: `_spark_star` (bintang spike selang-seling), `_chevron`
  (panah telegraph), `_dashed_ring` (rune ring berputar),
  `_jagged_crack` (retakan zigzag deterministik), `_dither_dots`,
  `_static` (cache permukaan), `_fx_scale`.
- **Q — Steel Wind / Dash**: TELEGRAPH = jalur + chevron berbaris +
  cincin konvergen di target; AKTIVASI = sabit ganda + bintang di tangan;
  STEADY = afterimage sepanjang jalur + speed streaks + seam tanah;
  muzzle burst world-space saat slash lepas; proyektil crescent
  trail 3-lapis + glint berputar di ujung.
- **W — Wind Wall**: TELEGRAPH = arc konvergen + garis tanah + chevron
  naik; AKTIVASI = dinding tumbuh + shockwave + bintang; STEADY = dinding
  3 lapis world-space + rune ring ganda berlawanan arah + swirl + mote
  naik + glint orbit + cap bintang; **scarf & bilah menyala sian**
  selama buff aktif (kwarg `gale`).
- **E — Sweep (AOE 100 px dunia)**: ring jangkauan TEPAT 100 px dunia
  (`100/_render_scale` px canvas — audit 180/180 hit pada fs 1.0/0.5/
  0.416) + tick ring berputar + ring konvergen + chevron kardinal +
  orb pusat; AKTIVASI = ring slash mengembang + bintang + shockwave
  elips; STEADY = 10 pilar angin mengelilingi ring.
- **R — Tornado (ultimate, AOE 150 px dunia)**: ring AOE sejati
  mengelilingi caster + retakan zigzag + chevron + rune ring di funnel;
  AKTIVASI = **pilar cahaya 3 lapis** + shockwave ganda + bintang;
  STEADY = funnel 8 lapis + lengan spiral 2 lengan + core + puing
  orbit + mahkota bintang + debu dasar + rune ring; **mata, manik
  hachimaki, dan tepi jaket menyala** (kwarg `storm`), aura badai
  ter-cache (`_draw_storm_aura`).

Jaga anggaran: rata-rata 2.1–3.2 ms per render cache-miss (bucket
`HERO_SKILL_QUANT=2`). Radius pilar R di-clamp `min(..., 230)` dan
seluruh FX digambar di dalam `_canvas_size_for` (clamp `_world_to_local`).

## Kompatibilitas

- Semua nama publik lama dipertahankan (`PALETTE` lengkap kunci lama +
  kunci baru, `draw_kaizen`, `draw_boss`, `WindSlashProjectile`, pose
  modes, skill FX, helper `_aacircle/_aaline/_poly/_ellipse/_rect`,
  `_world_to_local`, `_target_position`, dll.).
- `_draw_kaizen_body / _draw_kaizen_elite / _draw_elite_katana` menerima
  kwarg baru opsional (`gale`, `storm`, `glow`, `smear`) — signature
  posisi lama tetap jalan.
- `heroes/kaizen` alias modul tetap terekspor (termasuk helper FX v2.1,
  terdaftar di `_EXTRA` `heroes/__init__.py`).
- Regresi: `tools/test_kaizen_masterwork.py` (9 tes) — lulus.

## Alat

- `tools/_audit_kaizen_v2.py` — audit terukur (skala, bbox, frame unik,
  swatch palet, mata/telapak, timing pose + skill per frame timer jalan,
  **cek FX skill world-space di luar siluet badan**, **radius telegraph
  tepat dalam px dunia**) + 5 lembar preview:
  `docs/kaizen_v2_review.png`, `docs/kaizen_v2_anim_strip.png`,
  `docs/kaizen_v2_ingame.png`, `docs/kaizen_v2_skills.png`,
  `docs/kaizen_v2_before_after.png`.
- `tools/_shot_kaizen_masterwork.py` & `tools/kaizen_anim_demo.py`
  diperbarui ke canvas rig v2.
