# Gorath v2 — Pixel Masterwork + Skill FX

Upgrade renderer Gorath (`bosses/level2.py`, namespace `_NS_gorath`) ke standar
**Thorne v2 Pixel Masterwork + v2.1 Skill FX**. 100% prosedural: tidak ada PNG,
sprite-sheet, atau `pygame.image.load`.

## Before / after

| | v1 | v2 |
|---|---|---|
| Rig native (idle) | 87 × 79 px | **94 × 145 px** (`RIG_SCALE` 1.5×) |
| Buffer rig | 240 × 260 (jangkar 120/130) | 140 × 156 (`RIG_OX/OY` 70/98) |
| Warna unik idle / attack | 215 / 224 | **412 / 435** |
| Warna portrait LOD | — | 415 |
| Bbox di arena | 110 × 100 | 112 × 98 (**tetap sekelas keluarga**) |
| Keyframe serangan | 1 (lerp tunggal) | **7 + frame IMPACT** di `ap=0.54` |
| Telegraph skill | px canvas (menyusut) | **world-space** W 150 / E 85 / R 190 px dunia |
| Biaya cache-miss | ~1.4 ms | 1.9 ms pose, 2.5–3.3 ms saat skill (budget 3.5 ms) |

**Kenapa rig tidak membesar di layar.** Gorath adalah mini-boss level-2:
`tools/test_level2_masterwork.py` mengunci `alchemist (true boss) ≥ gorath`, dan
label + HP bar duduk di `y-r-25` / `y-r-15`. Jadi polanya mengikuti
`GORNAK_V2_RENDERER.md` / `MORGATH_V2_RENDERER.md`: rig di-*author* 1.5× lebih
besar di resolusi native (kepadatan detail naik), lalu ditampilkan lewat **satu**
`SCALE = 0.62` yang dipakai jalur boss, lane hero, dan portrait. Jangan
memisahkan scale per jalur — itu merusak normalisasi `_measure_native_size` di
`heroes/__init__.py`.

## Pixel-art discipline

1. **Ramp 4–7 band dengan hue-shift** — kulit 7 band (gelap ungu-merah → terang
   kuning-oranye), darah 8, tulang 5, logam 5, kulit-samak 5, rambut 4, emas 3,
   rune 3.
2. **Selout** — tiap poligon/limb menaruh salinan `shadow_deep` di `(+facing, +1)`;
   komposit akhir menambah outline hitam 1 px 4 arah **setelah** penskalaan.
3. **Siluet bergerigi** — `_tuft_points` memecah rambut, hem loincloth, dan plume
   kabut jadi zigzag deterministik; helai kain meruncing ke ujung.
4. **Specular cluster** — 2–3 titik (`*_high` → `*_shine`) di bahu, pektoral,
   tanduk, bilah; bukan satu piksel putih.
5. **Dither band** — `_dither_dots` di transisi perut dan kain.
6. **Key light kiri-atas** — konsisten dengan `lighting.LIGHT_DIR`; pass akhir
   `_lighting.apply_to_rig(rim_add=(46,18,16), shade_mul=168)`.

## Anatomi & senjata

Tengkorak demon dengan brow ridge menggantung, socket cekung + iris menyala
(kedip deterministik ~2,6 dtk), moncong underbite bertaring yang duduk **di bawah**
garis mata, dua tanduk ivory melengkung, war-paint darah di dahi + guratan pipi.
Torso 5 band dengan rune darah berdenyut, harness X kulit ber-jahitan, kalung
trofi tulang, pauldron tulang ber-duri. Dua **kukri** crescent (utama + tangan
belakang): gagang kulit berlilit, guard tulang, bilah 5 band dengan fuller gelap,
edge highlight, dan darah panas saat rage.

## Animasi

- **Float solver** (pengganti foot solver — Gorath melayang, tanpa kaki): dua
  kolom kabut darah bergantian memanjang/menyentuh tanah, menghasilkan riak dan
  tetesan saat kontak.
- **Inersia sekunder**: rambut dan hem loincloth tertinggal dari akselerasi badan
  (`hair_lag`, `cloth_lag`).
- **Living idle**: napas, sway, bob, denyut rune, tetes darah bersiklus.
- **Attack 7 keyframe** (`_attack_pose`): wind-up → tension (tremble 1 px) →
  strike → **IMPACT (0.54)** → follow-through → recover, dengan smear sabit 3
  lapis dan bintang/retakan di frame impact.

## Skill FX (3 tahap, world-space)

Semua FX dikompensasi `_fx_scale = 1/_render_scale` (cap 2.6) supaya ukurannya
**di layar** tidak menyusut bersama sprite cache; telegraph memakai `_ring_r`
yang mengubah radius dunia → px canvas dan meng-clamp ke dalam canvas.

| Skill | Durasi | Aktivasi | Steady | Telegraph |
|---|---|---|---|---|
| **Q Bloodrage** | 90 | pilar darah 4 lapis + shockwave ganda + bintang 8-spike | mahkota api darah 2 ring, aura 3 cincin, kolom bara, glint orbit | rune ring ganda berlawanan arah yang mengembang + chevron masuk + 6 retakan magma |
| **W Bloodrite** | 60 | muzzle star + voli 3 proyektil (trail berlapis + glint ujung) | duri darah meletus, splat marker 2 cincin, cipratan | **ring jangkauan tepat 150 px dunia** + tick ring + ring konvergen + chevron kardinal |
| **E Thirst** | 35 | kilat lompat + bintang di titik tolak | beam pelacak 3 lapis, crosshair berdenyut, partikel mengalir | **ring AOE 85 px dunia di target** + ring konvergen + retakan pendaratan + chevron berbaris di jalur |
| **R Rupture** | 90 | pilar cahaya darah + shockwave ganda + bintang | rantai darah bergelombang, wisp spiral 2 lengan, ledakan + duri menyembur | **ring AOE 190 px dunia di caster** + dashed ring ganda + 6 chevron + retakan magma ber-seam |

Aktivasi tiap skill juga memicu `_draw_shockwave` pada 12 frame pertama
(`age < 12`). Badan bereaksi ke state skill: rune dada dan mata membara saat
`q`/`r`, mata berburu saat `e`/`w`, bilah berlumur darah panas saat rage.

## Performa & cache

Surface statis (mist wisp, kolam tanah, aura, bayangan) dibangun sekali lewat
`_static` / `_shadow_cache` / `_aura_cache`; per frame hanya `set_alpha` + blit.
`_clamp` di-memo karena dipanggil puluhan ribu kali per detik. Hem loincloth dan
plume digambar sebagai poligon meruncing per band, bukan polyline per segmen.
Terukur (median, canvas 528×528): idle 1.9 ms, attack 1.9 ms, Q 2.8 / W 2.8 /
E 2.5 / R 3.3 ms — semuanya di bawah budget 3.5 ms dan hanya dibayar saat cache
miss.

## Kompatibilitas

Semua nama & signature publik lama dipertahankan (49 nama, diverifikasi oleh
test): `draw_gorath`, `draw_boss`, `_draw_gorath_body(_raw)`, `_draw_shadow(...,
lift=0)`, `_draw_shockwave`, `BloodProjectile`, seluruh `_draw_*` bagian tubuh
dan skill, serta primitif `_clamp/_aacircle/_aaline/_poly/_ellipse/_rect`.

## Tools

- `tools/test_gorath_masterwork.py` — regresi khusus (rig, pixel-art, animasi,
  FX world-space, 3 tahap, cache statis, budget).
- `tools/_audit_gorath_v2.py` — audit terukur + 5 preview sheet.
- `tools/test_grimjaw_masterwork.py` — paritas kosakata FX antar renderer v2.
- `tools/_gorath_v1_snapshot.py` — snapshot renderer v1 untuk sheet before/after.
- Preview: `docs/gorath_v2_{review,anim_strip,ingame,skills,before_after}.png`.

## Revisi FX tanah: decal ber-falloff (menggantikan cincin stroke)

Pass pertama menggambar telegraph sebagai **stroke vektor**: 25 pemanggilan
`_ring` (lingkaran sempurna, `pygame.draw.circle` lebar 1-4 px) ditumpuk
dengan 9 `_dashed_ring` ber-`squash` 0.42-0.6. Tiga masalah:

1. **Dua perspektif di bidang tanah yang sama.** Lingkaran penuh
   (`squash` 1.0) dan elips pipih (`squash` .42) digambar bertumpuk di
   titik yang sama, sehingga tidak ada satu pun bidang lantai yang
   konsisten.
2. **Tepi keras, nilai rata.** Stroke lebar tetap tidak punya gradien,
   jadi terbaca sebagai garis UI yang melayang, bukan cahaya di lantai.
3. **Zona kosong.** Hanya garis batas yang digambar; area di dalamnya
   tidak pernah dibaca sebagai "daerah berbahaya".

### Perbaikan

Radius gameplay itu euclidean (`dist <= 150`), jadi **lingkaran penuh**
adalah bidang yang benar dan elips `squash` yang dibuang. Semua FX tanah
sekarang memakai satu bidang.

| Primitif baru | Fungsi |
| --- | --- |
| `_ground_ring` | Batas AOE ber-gradien; alpha mengikuti kurva kuadratik terhadap radius nominal, blit additive |
| `_rune_ring` | Cincin busur berputar; segmen meruncing di ujung, diputar lewat `transform.rotate` (geometri tidak dibangun ulang) |
| `_zone_fill` | Wash zona **edge-weighted**: pekat di tepi, bening di tengah -> batas jelas tapi karakter tetap terbaca |
| `_ground_scorch` | Alas tanah gosong ber-tepi gumpalan lembut; membuat telegraph menempel di lantai |
| `_glow` | Gradien radial ter-cache (mengganti tumpukan `_aacircle`) |
| `_decal` / `_blit_decal` | Cache LRU 48 entri; radius di-`_quantize` ke kelipatan 6-10 px supaya cache nyangkut |

Komposisi juga dirapikan: cincin konvergen sekarang hanya muncul di paruh
akhir cast (bukan sepanjang durasi), R memakai satu rune ring bukan dua
yang berlawanan arah, dan rim kolam darah digambar **elips** karena
mengikuti bentuk kolam/bayangan - bukan bidang AOE.

### Hasil

Decal dibangun sekali lalu di-blit, jadi lebih cepat dari stroke per-frame:

| Pose | Sebelum | Sesudah |
| --- | --- | --- |
| idle / walk / attack | 1.89 / 1.90 / 1.92 ms | 1.44 / 1.54 / 1.49 ms |
| q / w / e / r | 2.75 / 2.83 / 2.47 / 3.27 ms | 2.24 / 2.86 / 2.19 / **2.85** ms |

Radius telegraph tetap eksak (W 150 / E 85 / R 190 world px). Empat test
baru di `tools/test_gorath_masterwork.py` mengunci perbaikan ini:
`test_ground_fx_use_decals_not_vector_strokes`,
`test_ground_ring_has_soft_falloff`, `test_zone_fill_is_edge_weighted`,
`test_decals_are_cached`.
