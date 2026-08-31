# Sylara v2 — Renderer Pixel-Art Masterwork

> Rewrite penuh namespace `_NS_sylara` di `heroes/_bundle.py`.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (lama) | v2 (baru) |
|---|---|---|
| Rig native (bbox idle) | ~104 × 107 px | **79 × 142 px** (buffer 240 × 210, `RIG_SCALE=1.52`) |
| Kepadatan detail di layar | ~2.0 px native / px layar | **~1.84 px native / px layar** (tinggi 142 → ~77 px di layar, scale 0.545) |
| Warna unik (idle native) | ~44 | **60** (portrait LOD: 62) |
| Skala pipeline | 0.757× | **0.545×** (pipeline menormalkan tinggi arena) |
| Ukuran di arena | ~72 px layar | **~77 px layar** |
| Biaya render | ~1–2 ms | idle **~1.8 ms**, skill **~3.3 ms** (hanya saat cache miss) |

Memperbesar rig **tidak** memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~70 px. Yang berubah
adalah **resolusi efektif** — setiap piksel layar disampel dari lebih banyak
piksel native, sehingga cluster, ramp, dan muka tetap tajam setelah
smoothscale + lighting + outline pass.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — bayangan kulit
   didinginkan, highlight dihangatkan; bayangan rambut didorong merah-ungu,
   highlight hijau gembira.
2. **Selout (selective outlining)** — outline gelap 4-arah membungkus rig
   (siluet 1 px seperti sprite sheet referensi).
3. **Siluet bergerigi** — cape di-generate `_tuft_points()` dari spine +
   hash deterministik (aman untuk cache).
4. **Specular sebagai cluster** — kilau busur/baja/gold jadi 1–2 px yang
   disengaja (`gold_shine`, `hair_high`, `leather_high`).
5. **Dither band** — `_dither_dots` di korset, tekstur klasik yang selamat
   dari downscale.
6. **Key light kiri-atas** konsisten dengan `lighting.py`
   (`LIGHT_DIR = (-1, -1)`).

## Anatomi baru

- **Hood hijau runcing** + rambut merah berkibar (secondary motion), mata
  hijau dengan blink idle.
- **Cape robek ber-tuft** dengan inersia (gust walk/windrun/attack flare).
- **Quiver anak panah** + **busur recurve pose-driven** (`_bow_frame`,
  `_bow_point`, `_bow_nock`): grip/nock/tali dihitung dari sendi.
- **Korset kulit hijau ber-strap** + gesper emas, boot kulit 3 band.
- **Foot solver**: telapak menapak/terangkat di y=+61 native, knee-lift,
  contact dust saat menapak.

## Animasi

- **Walk**: foot solver stride, knee-lift, cape/hair lag, bob, debu tapak.
- **Idle**: breath, sway, blink, daun `leaf_gold` / `leaf_ember`.
- **Serangan 7-keyframe** (`_attack_pose`):
  - 0.00 rest → 0.12 wind-up → 0.26 tension → 0.42 full draw
  - **0.52 IMPACT** release (bintang 8-spike + shockwave + smear angin)
  - 0.72 follow-through → 1.00 rest (loop closure).
- **Skill-state body reaction** (`focus` / `wind` / `shackle` /
  `powershot`): busur + rim cape menyala hijau, orb charge, rune ring,
  afterimage vertigo.

## Skill FX (world-space, 3 fase tiap skill)

FX membaca `hero.active_skill` / `hero.active_skill_timer` dengan
**durasi VISUAL** `SKILL_VISUAL_DURATION = {q:180, w:180, e:150, r:60}`.

| Skill | Radius dunia | Visual |
|---|---|---|
| Q Focus Fire | 200 (`skill_range`) | shockwave ganda + bintang → rune ring + crescent + retakan daun → pierce-line chevron |
| W Windrun | 70 | shockwave + bintang → crescent helix + dashed ring + daun + retakan → chevron arah lari |
| E Shackle Shot | target | burst orb di target → tether rantai 14 segmen + reticle → kandang menguncup + burst ikat |
| R Powershot | 60 | shockwave + bintang di busur → orb charge + rune ring + mote → X-slash + retakan di target |

**World-space**: `_fx_scale(hero)` = `1/_render_scale` (cap 2.6).
`_ring_r()` clamp ke dalam canvas cache.

**Proyektil**: `WindArrowProjectile` / `ShackleProjectile` memakai
`_drk_arrow` + pita comet + kilau `leaf_gold`.

**Tanpa alokasi per-frame**: shadow & aura di-cache `_static`.

## Terukur (audit `tools/_audit_sylara_v2.py`)

- bbox idle native **79×142**, skala **0.545** → **77.4 px** di layar
- 8 walk frame unik + 10 attack pose unik
- 11 swatch material idle sampai ke render final
- telapak menapak y=+61, hood/mata di zona kepala
- idle render ~1.8 ms; skill ~3.0–3.7 ms
- `_fx_scale(0.40)` = 2.50
- FX di luar badan: Q 2567, W 941 (1174 world-space), E 900, R 867 sampel
- 3 tahap FX per skill Q/W/E/R
- focus/wind kwarg mengubah badan

## Kompatibilitas

Semua nama publik lama dipertahankan:
`draw_sylara`, `draw_boss`,
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
`_draw_floating_wind`, `_draw_leaf`, `_draw_shadow`,
`_manage_projectiles`, `_spawn_arrow`, `_spawn_shackle`,
`_spawn_focus_fire_volley`, `_detect_moving`, `_update_attack_anim`,
`_world_to_local`, `_target_position`,
`WindArrowProjectile`, `ShackleProjectile`,
`PALETTE` (kunci lama + `hair_high` / `cloak_high` / `leather_high` /
`gold_shine` / `leaf_gold` / `leaf_ember`),
`RIG_W/RIG_H/RIG_OX/RIG_OY`, `HAS_AACIRCLE`.

Ditambah: `RIG_SCALE`, `ATTACK_WINDUP_END`, `ATTACK_RELEASE_END`,
`ATTACK_IMPACT`, `_attack_pose`, `_dither_dots`,
`SKILL_VISUAL_DURATION`, `_STATIC_SURFACES`, `_static`, `_hash01`,
`_mix`, `_fx_scale`, `_ring_r`, `_spark_star`, `_chevron`,
`_dashed_ring`, `_jagged_crack`, `_tuft_points`,
`_draw_sylara_skill_overlay`, `_skill_flags`.

## Alat

- `tools/_audit_sylara_v2.py` — audit terukur + 5 lembar preview:
  `docs/sylara_v2_review.png`, `docs/sylara_v2_anim_strip.png`,
  `docs/sylara_v2_ingame.png`, `docs/sylara_v2_skills.png`,
  `docs/sylara_v2_before_after.png`.
- `tools/test_sylara_masterwork.py` — regresi rig 1.52x, busur pose,
  7-keyframe, world-space Q/W/E/R, nama publik.
- `tools/test_grimjaw_masterwork.py` — paritas keluarga (kosakata FX
  `_fx_scale` cap 2.6 termasuk Sylara).
