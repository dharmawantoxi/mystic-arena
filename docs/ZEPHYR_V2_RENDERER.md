# Zephyr v2 — Renderer Pixel-Art Masterwork

> Rewrite penuh namespace `_NS_zephyr` di `heroes/_bundle.py`.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (lama) | v2 (baru) |
|---|---|---|
| Rig native (bbox idle) | ~106 × 114 px | **107 × 150 px** (1.55×, crown `y=-102`, kaki `y=+50`) |
| Kepadatan detail di layar | ~1.9 px native / px layar | **~2.6 px native / px layar** |
| Warna unik (idle native) | ~93 | **97** (portrait LOD: 105) |
| Skala pipeline | 0.430× | **0.430×** (sama — pipeline menormalkan) |
| Ukuran di arena | ~64 px layar | **~64 px layar** (sama) |
| Biaya render | ~1–2 ms | idle **~1.3 ms**, skill **~3.7 ms** (hanya saat cache miss) |

Memperbesar rig **tidak** memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~64 px. Yang berubah
adalah **resolusi efektif** — setiap piksel layar kini disampel dari ~2.6
piksel native, sehingga cluster, ramp, dan muka tetap tajam setelah
smoothscale + lighting + outline pass.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — bayangan dingin
   (ungu-hitam), highlight hangat (pink-putih). Volume terbaca sebagai
   cahaya, bukan pita datar.
2. **Selout (selective outlining)** — outline gelap hanya di sisi bayangan
   (kanan-bawah); sisi cahaya dibiarkan bersih + rim 1 px.
3. **Siluet bergerigi** — thorn-crown di-generate `_tuft_points()` dari
   spine + hash deterministik (aman untuk cache), bukan poligon halus.
4. **Specular sebagai cluster** — kilau sayap/baja/gold jadi 1–2 px yang
   disengaja, bukan gradien.
5. **Dither band** — titik corset & hem di gown, tekstur klasik pixel-art
   yang selamat dari downscale.
6. **Key light kiri-atas** konsisten dengan `lighting.py`
   (`LIGHT_DIR = (-1, -1)`).

## Anatomi baru

- **Crown 9 spike** (`_draw_zephyr_crown`): massa utama hair_darkest +
  hair_dark, 9 spike individual dengan secondary motion (hash deterministik),
  tips amber `hair_tip`, gold circlet + 3 amethyst pin.
- **Moth wings 2-pair** (`_draw_elite_wings`): upper wing 7-titik thorned,
  lower wing 6-titik rounder cadence; 3 vein per sisi; specular solid pixel
  di vein tip; Bedlam glow overlay; glass highlight patch di portrait LOD.
- **Gown 4 panel petal** + hem dither 6 titik.
- **Corset** charcoal-plum dengan lace crosshatch 5 baris + dither band.
- **Belt + buckle emas** + amethyst center.
- **Staff blackwood 3-band + vine 6 coil + kristal 4-faset** + thorn crown
  di orb.
- **Foot solver** (`_draw_zephyr_elite`): telapak menapak/terangkat
  bergantian, knee-lift saat jalan, contact shadow per telapak.

## Animasi

- **Walk**: foot solver stride ±5 px, knee-lift max 10 px, gown sway
  bergantian, mantle flap, bob ±3.5 px, sway ±2.5 px.
- **Idle**: breath ±1.1 px, hair_sway ±2.5 px, blink tiap ~10 detik,
  motes naik 4 titik.
- **Serangan 3 zona** (`_staff_tip_local`):
  - Wind-up (ap < 0.28): orb mundur ke rambut `(20, -42)`
  - Release (ap < 0.62): orb maju menusuk `(72, -22)`
  - Recovery: kembali ke posisi idle `(44, -22)`
- **IMPACT** frame (ap ≈ 0.50): 8-spike star burst + halo magenta
  (`_spark_star` + 2× `_aacircle`).
- **Bedlam state**: staff orb + ring corset menyala magenta (kwarg `bedlam=True`).

## Skill FX (world-space, 3 fase tiap skill)

FX membaca `hero.active_skill` / `hero.active_skill_timer` dengan
**durasi VISUAL** `SKILL_VISUAL_DURATION = {q:240, w:180, e:180, r:240}`.

| Skill | Radius dunia | Visual |
|---|---|---|
| Q Bramble Maze | 60 | ring duri 12 spine + chevron 3 menuju trap + dashed ring + burst bintang |
| W Shadow Realm | 100 | pilar cahaya 3-lapis → kubah kaca crescent + **dual rune ring berlawanan arah** |
| E Casket Curse | 70 | thorn tether 10 segmen + reticle 2-ring + cross + glint orbit 4 titik |
| R Bedlam | 80 | pilar 4-lapis + ground cracks 5 radial + **ring konvergen** + chevron 8 kardinal + fairy orbit 6 + trail glitter 4 |

**World-space**: `_fx_scale(hero)` = `1/_render_scale` (cap 2.6) —
efek dikompensasi agar radius di layar cocok dengan jangkauan gameplay,
tidak menyusut bersama sprite. `_ring_r()` clamp ke dalam canvas cache.

**Tanpa alokasi per-frame**: shadow, rim-light, fey-aura, dan platform
dibangun sekali lalu di-cache (`_static`); key menggunakan nama string
unik per jenis.

## Terukur (audit `tools/_audit_zephyr_v2.py`)

- bbox idle 107×150 px native, skala 0.430 → 64 px di layar ✓
- 8 walk frame unik + 10 attack pose unik ✓
- 10 swatch palet (wing_shine, thorn_light, boot_light, gold_light,
  jewel_light, hair_tip, cloak_light, corset_light, rune_light,
  jewel_mid) sampai ke render final ✓
- Crown spikes: 499 px di kuadran atas ✓
- Wing left: 3422 px di sisi kiri kanvas ✓
- idle render: ~1.3 ms (budget <3.5 ms) ✓
- skill render: ~3.7 ms (budget <6.0 ms) ✓
- `_fx_scale(0.40)` = 2.50 (dalam range 2.0–2.6) ✓
- Ring Q 9350 px FX di luar badan, W 13619 px, E 3164 px, R 15921 px ✓
- Bedlam glow mengubah penampilan badan karakter ✓

## Kompatibilitas

Semua nama publik lama dipertahankan:
`draw_zephyr`, `draw_boss`, `_draw_zephyr_idle`, `_draw_zephyr_walk`,
`_draw_zephyr_attack`, `_draw_zephyr_body`, `_draw_zephyr_rig`,
`_draw_zephyr_elite`, `_draw_zephyr_crown`, `_draw_elite_wings`,
`_draw_elite_staff`, `_draw_zephyr_masterwork_details`,
`_staff_tip_local`, `_staff_orb_position`,
`_detect_moving`, `_update_attack_anim`,
`_manage_projectiles`, `_spawn_magic_bolt`, `_spawn_casket`,
`MagicBoltProjectile`, `CasketProjectile`,
`PALETTE` (semua kunci lama termasuk `bramble_*`),
`SKILL_VISUAL_DURATION`,
`ATTACK_WINDUP_END`, `ATTACK_SWING_END`, `ATTACK_ARC_START`,
`ATTACK_ARC_SWEEP`, `ATTACK_ARC_END`.

## Alat

- `tools/_audit_zephyr_v2.py` — audit terukur (25 cek) + 5 lembar preview:
  `docs/zephyr_v2_review.png`, `docs/zephyr_v2_anim_strip.png`,
  `docs/zephyr_v2_ingame.png`, `docs/zephyr_v2_skills.png`,
  `docs/zephyr_v2_before_after.png`.
- `tools/test_zephyr_masterwork.py` — 14 tes regresi (7 legacy + 7 v2 baru).
- `tools/_shot_zephyr_masterwork.py` & `tools/zephyr_anim_demo.py`
  diperbarui ke canvas rig v2.
