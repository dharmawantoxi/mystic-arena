# Gornak v2 — Renderer Pixel-Art Masterwork + Skill FX v2.1

> Rewrite namespace `_NS_gornak` di `bosses/level1.py`.
> Standar mengikuti **Thorne v2 Pixel Masterwork + Thorne v2.1 Skill FX**
> (lihat docs/THORNE_V2_RENDERER.md).
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

> **STATUS (2026-09-01).** Dokumen ini membahas **badan/rig** dan skill FX v2.1,
> dan masih akurat untuk bagian itu. Setelah dokumen ini ditulis ada tiga pass
> lagi di `_NS_gornak` (jalur hero v3, kurva pose v3, pass cahaya v4) plus satu
> **rewrite sistem tempur penuh** yang tidak didokumentasikan di sini:
> controller animasi, fase ayunan, swing trail, proyektil, impact, hit-stop, dan
> screen shake kini tinggal di `heroes/gornak_fx.py` + `heroes/combat_feel.py`.
> Baca **[GORNAK_V3_COMBAT_FX.md](GORNAK_V3_COMBAT_FX.md)** untuk bagian itu,
> dan jalankan `python tools/_audit_gornak_v3.py` (46 cek terukur + lembar
> `docs/gornak_v3_*.png`) untuk melihat kondisi sebenarnya. Kalau tabel di bawah
> bertentangan dengan kode, **kode yang benar** — dokumen ini tidak otomatis
> diregenerasi.

Gornak adalah **mini-boss 1:1 DAN hero** (pipeline `heroes/__init__.py`
menormalkan tinggi lane). Tidak seperti Kaizen/Thorne/Grimjaw, rig
boss-path **tidak boleh tumbuh 1.5×**: HP bar mini-boss digambar di
`y-r-15`, tes mengunci `rect.top ≥ CY-58`, dan puncak krist sudah
~`CY-55.5`. Yang berubah adalah **kepadatan pixel-art** + FX
world-space, bukan bbox.

## Apa yang berubah

| Aspek | v1 (masterwork lama) | v2 (baru) |
|---|---|---|
| Rig native (boss 1x) | SCALE=1.32, RIG 176×160 | **sama** (paritas keluarga vs Morgath/Drakar/Abaddon) |
| Ukuran di arena (hero) | ~70 px | ~70 px (pipeline menormalkan, scale ≤ 1.02) |
| Pixel-art | ramp 4–5 band | + **selout**, **tuft** cape/loincloth, **dither** greave/jubah, **specular cluster** pauldron/bilah |
| Skill FX | canvas-space, R salah di target | **world-space** `_fx_scale` (cap 2.6); E=100 / **R=180 di caster** |
| Aura/bayangan | alokasi per frame | ter-cache `_static` |
| Biaya render idle | ~1.3–1.8 ms | ~1.5–2.0 ms (hanya cache miss) |

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — kulit, baja, jubah,
   bilah, ungu anti-sihir. Volume terbaca sebagai cahaya.
2. **Selout (selective outlining)** — outline gelap hanya di sisi
   bayangan (kanan-bawah relatif hadap); sisi cahaya bersih + rim 1 px
   ungu (`_draw_gnk_rimlight`). Key light kiri-atas =
   `lighting.LIGHT_DIR = (-1, -1)`.
3. **Siluet bergerigi** — hem cape & loincloth di-generate
   `_tuft_points()` (depth kecil, **tidak ke atas** — mohawk sudah di
   batas HP bar).
4. **Specular sebagai cluster** — kilau pauldron/bilah 1–2 px, bukan
   gradien.
5. **Dither band** — `_dither_dots()` 50% di greave & sisi bayangan jubah.
6. **Foot solver + idle hidup** — telapak dipatok `GROUND_DY`, debu
   tapak, napas, blink, head-bob, inersia jubah.

## Skill FX v2.1 — world-space

Masalah lama: efek hero ikut mengecil bersama sprite cache
(`_render_scale` ~0.69×) dan **R Mana Void digambar di target** padahal
gameplay adalah AOE 180 px di `self.x/self.y`. Pass ini menggambar efek
**world-space** lewat `_fx_scale(boss)` (= `1/_render_scale`, cap 2.6).

- **Primitif**: `_spark_star`, `_chevron`, `_dashed_ring`,
  `_jagged_crack`, `_tuft_points`, `_dither_dots`, `_static`,
  `_fx_scale`, `_ring_r`, `_world_to_local`.
- **Q — Mana Break** (timer 40): TELEGRAPH di **ujung bilah** (cincin
  konvergen + chevron ke target + bintang) → bolt 3-lapis + glint
  berputar di ujung → impact ring + retakan zigzag. Tidak ada range ring.
- **W — Blink** (timer 25): ellipse tanah + dashed ring + bintang
  kedatangan; after-image rig yang sama.
- **E — Counterspell** (timer 60, **AOE 100 px dunia**): ring jangkauan
  TEPAT 100 + dashed ring + chevron kardinal + ring konvergen; kubah
  heksagon 3-lapis memeluk badan + mote orbit di ring 100.
- **R — Mana Void** (timer 90, **AOE 180 px dunia di CASTER**): telegraph
  ring 180 di diri sendiri + retakan radial + chevron; aktivasi **pilar
  3-lapis** (tinggi di-clamp `min(100·fs, 240)`) + shockwave + bintang;
  drain mote dari target → dada sebagai baca "mencuri mana"; rim violet
  di badan.

Aura anti-magic & bayangan kontak di-cache (`_static`). Portrait LOD
membuang seluruh FX arena. FX di-clamp ke rumus canvas hero
(`half = max(120, int(range/_render_scale)+40)`); ring R 180 pada scale
hero ~0.69 mungkin terpotong di tepi canvas — radius gameplay tetap
digambar.

## Kompatibilitas

Semua nama publik lama dipertahankan: `draw_gornak`, `_draw_gnk_rig`,
`_draw_gnk_legs/_torso/_head/_arm/_blade/_masterwork_details`,
`_blade_angle`, `_front_grip_local`, `_elbow`, `_tip_local/_tip_screen`,
`_compose_outline`, `_draw_crescent_slash`, `_attack_curve`, `_head_bob`,
`_draw_footfall_dust`, `_draw_gnk_rig_at`, `PALETTE` (kunci lama +
`magic_void`/`magic_core`/`blade_edge`), `RIG_W/H=176/160`,
`RIG_OX/OY=74/96`, `GROUND_DY`, `SCALE=1.32`, `LIFT=4`, `FEET_DY=44`,
`SKILL_DUR={q:40,w:25,e:60,r:90}`.

Body-part lama tetap dilarang: `_draw_leg`, `_draw_gnk_robe`,
`_draw_gnk_arm_back/_front`, `_draw_blade`, `_draw_mohawk`,
`_draw_counterspell_ground`.

Jalur cahaya: `_HERO_LANE.v` melewati pass boss saat lane hero (satu
pass di `_finish_hd_sprite`).

## Verifikasi

- `tools/test_gornak_masterwork.py` — prosedural, bbox keluarga, kaki
  menapak, bilah pose-driven, proc Q di ujung bilah, outline, portrait
  LOD, **ring E/R world-space** (fs 1.0 vs 0.5), perf < 5 ms.
- `tools/_audit_gornak_v2.py` — skala pipeline, frame unik, swatch,
  timing median ≤ 3.5 ms, FX di luar badan, telegraph 100/180 px dunia,
  5 lembar preview.
- Regresi: `tools/test_hero_lighting.py`, `tools/test_hero_hd_render.py`,
  `tools/test_swing_anim.py`, `tools/test_renderer_projectiles_not_baked.py`.
- Sheet lama: `tools/_shot_gornak_masterwork.py` →
  `docs/gornak_{masterwork_preview,animation_strip,portrait_preview}.png`.
