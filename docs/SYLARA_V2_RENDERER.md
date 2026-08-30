# Sylara v2 — Renderer Pixel-Art Masterwork

> Rewrite penuh namespace `_NS_sylara` di `heroes/_bundle.py`.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (lama) | v2 (baru) |
|---|---|---|
| Rig native (bbox idle penuh) | ~104 × 107 px | **124 × 124 px** (raw rig 54 × 95, bbox idle penuh incl. shadow/platform) |
| Kepadatan detail di layar | ~2.0 px native / px layar | **~2.6 px native / px layar** (raw rig 54×95 → 72 px di layar) |
| Warna unik (idle native) | ~44 | **48** (portrait LOD: 51) |
| Skala pipeline | 0.757× | **0.757×** (sama — pipeline menormalkan) |
| Ukuran di arena | ~72 px layar | **~72 px layar** (sama) |
| Biaya render | ~1–2 ms | idle **~1.4 ms**, skill **~2.3 ms** (hanya saat cache miss) |

Memperbesar rig **tidak** memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~72 px. Yang berubah
adalah **resolusi efektif** — setiap piksel layar kini disampel dari ~2.6
piksel native, sehingga cluster, ramp, dan muka tetap tajam setelah
smoothscale + lighting + outline pass.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — bayangan kulit
   didinginkan (cokelat-ungu), highlight dihangatkan; bayangan rambut
   didorong merah-ungu menuju kulit, highlight hijau gembira.
2. **Selout (selective outlining)** — outline gelap hanya di sisi bayangan
   (kanan-bawah); sisi cahaya dibiarkan bersih + rim 1 px.
3. **Siluet bergerigi** — cape & rambut di-generate `_tuft_points()` dari
   spine + hash deterministik (aman untuk cache), bukan poligon halus.
4. **Specular sebagai cluster** — kilau busur/baja/gold jadi 1–2 px yang
   disengaja, bukan gradien.
5. **Dither band** — titik di korset, tekstur klasik pixel-art yang selamat
   dari downscale.
6. **Key light kiri-atas** konsisten dengan `lighting.py`
   (`LIGHT_DIR = (-1, -1)`).

## Anatomi baru

- **Hood hijau runcing** + rambut merah berkibar (secondary motion, hash
  deterministik), blush + mata hijau dengan blink.
- **Cape robek ber-lapis per-panel** dengan inersia (tertinggal dari
  akselerasi + flare saat serang).
- **Quiver anak panah** + **busur recurve pose-driven** (`_bow_frame`,
  `_bow_point`, `_bow_nock`): grip/nock/tali dihitung dari sendi, tali
  menegang mengikuti tarikan, anak panah ternock saat draw.
- **Korset kulit hijau ber-strap** + gesper emas, sabuk kulit 3 band,
  boot kulit 3 band.
- **Foot solver** (`_draw_sylara_elite`): telapak menapak/terangkat,
  knee-lift saat jalan, contact shadow per telapak, debu saat menapak.

## Animasi

- **Walk**: foot solver stride, knee-lift, cape/hair lag, bob ±3 px,
  sway ±2 px, bayangan kontak + debu.
- **Idle**: breath ±2 px, sway kiri-kanan, blink, daun melayang
  (`_draw_floating_wind`), flutter busur.
- **Serangan multi-keyframe**:
  - Wind-up (ap < 0.30): busur ditarik, badan mundur, recoil.
  - Release (ap ≈ 0.55–0.65): **IMPACT burst** (bintang 8-spike +
    shockwave + smear angin mengikuti arah tembak) di ujung busur.
  - Recovery: kembali ke pose jaga (loop closure tanpa pop).
- **Skill-state body reaction** (`focus` / `wind` / `shackle` /
  `powershot` kwarg): busur + rim cape menyala hijau, orb charge di ujung
  busur, rune ring di pergelangan, afterimage vertigo.

## Skill FX (world-space, 3 fase tiap skill)

FX membaca `hero.active_skill` / `hero.active_skill_timer` dengan
**durasi VISUAL** `SKILL_VISUAL_DURATION = {q:180, w:180, e:150, r:60}`.

| Skill | Radius dunia | Visual |
|---|---|---|
| Q Focus Fire | 200 (skill_range) | pilar/shockwave gabung + bintang → ground ellipse aura + rune ring berputar + rune dots → pierce-line chevron berbaris |
| W Windrun | 70 | shockwave ganda + bintang → counter-rotating dual ring + speed streaks + daun melayang → chevron berbaris ke arah lari |
| E Shackle Shot | target | burst bintang di target + shockwave → tether rantai 14 segmen + rune dot berputar → reticle 2-ring + cross + chevron berbaris |
| R Powershot | 60 | pilar cahaya 3-lapis + shockwave ganda + bintang → orb konvergen + dashed ring berputar + mote naik + glint orbit → garis + chevron menuju target + retakan tanah |

**World-space**: `_fx_scale(hero)` = `1/_render_scale` (cap 2.6) —
efek dikompensasi agar radius di layar cocok dengan jangkauan gameplay,
tidak menyusut bersama sprite. `_ring_r()` clamp ke dalam canvas cache.

**Badan ikut bereaksi**: busur/cape menyala hijau saat Focus Fire &
Powershot, rantai hijau di pergelangan saat Shackle, afterimage saat
Windrun (`_draw_sylara_skill_overlay`).

**Proyektil diberi trail berlapis + glint**: `WindArrowProjectile`
(powered = Powershot) & `ShackleProjectile` menggambar 2-tone trail +
orbit glint di ujung saat ini.

**Tanpa alokasi per-frame**: shadow & aura dibangun sekali lalu di-cache
(`_static`); key memakai nama string unik per jenis.

## Terukur (audit `tools/_audit_sylara_v2.py`)

- bbox idle penuh 124×124 px native, skala 0.757 → 72 px di layar ✓
- 8 walk frame unik + 10 attack pose unik ✓
- 7 swatch material idle (hair_shine, cloth_light, leather_light,
  gold_light, eye_iris_light, string_shine, arrow_feather) sampai ke
  render final ✓
- hood + rambut muncul di ujung atas badan (1131 px) ✓
- busur recurve terbaca di sisi depan (2289 px) ✓
- idle render: ~1.4 ms (budget <3.5 ms) ✓
- skill render: ~2.3 ms (budget <6.0 ms) ✓
- `_fx_scale(0.40)` = 2.50 (dalam range 2.0–2.6) ✓
- ring lebih besar di canvas scale 0.40 vs 1.00 (rr40=190 vs rr100=100) ✓
- FX di luar badan: Q 9099 px, W 2117 px, E 1297 px, R 2830 px ✓
- focus/wind kwarg mengubah penampilan badan karakter ✓

## Kompatibilitas

Semua nama publik lama dipertahankan:
`draw_sylara`, `draw_boss`, `draw_hero`,
`_draw_sylara_idle`, `_draw_sylara_walk`, `_draw_sylara_attack`,
`_draw_sylara_windrun`, `_draw_sylara_body`, `_draw_sylara_rig`,
`_draw_sylara_elite`, `_draw_sylara_masterwork_details`,
`_draw_elite_bow`, `_draw_elite_arrow`, `_bow_frame`, `_bow_point`,
`_bow_nock`,
`_draw_bow_release_flash`, `_draw_powershot_charge`,
`_draw_windrun_ground`, `_draw_windrun_trail`,
`_draw_shackle_ground`, `_draw_focus_fire_ground`,
`_draw_focus_fire_effect`,
`_draw_wind_aura`, `_draw_wind_platform`, `_draw_ranger_silhouette_glow`,
`_draw_floating_wind`, `_draw_leaf`, `_draw_wind_arc`, `_draw_shadow`,
`_manage_projectiles`, `_spawn_arrow`, `_spawn_shackle`,
`_spawn_focus_fire_volley`, `_detect_moving`, `_update_attack_anim`,
`_world_to_local`, `_target_position`,
`WindArrowProjectile`, `ShackleProjectile`,
`PALETTE` (semua kunci lama), `RIG_W/RIG_H/RIG_OX/RIG_OY`,
`HAS_AACIRCLE`,

Ditambah (baru, world-space): `SKILL_VISUAL_DURATION`, `_STATIC_SURFACES`,
`_static`, `_hash01`, `_mix`, `_fx_scale`, `_ring_r`, `_spark_star`,
`_chevron`, `_dashed_ring`, `_jagged_crack`, `_tuft_points`,
`_draw_sylara_skill_overlay`, `_skill_flags`.

## Alat

- `tools/_audit_sylara_v2.py` — audit terukur (25 cek) + 5 lembar preview:
  `docs/sylara_v2_review.png`, `docs/sylara_v2_anim_strip.png`,
  `docs/sylara_v2_ingame.png`, `docs/sylara_v2_skills.png`,
  `docs/sylara_v2_before_after.png`.
- `tools/test_sylara_masterwork.py` — 8 tes regresi (6 legacy + 2 v2 baru
  untuk helper world-space + body-reaction).
