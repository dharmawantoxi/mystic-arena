# Grimjaw v2 — Renderer Pixel-Art Masterwork

> Rewrite penuh namespace `_NS_grimjaw` di `heroes/_bundle.py`.
> Tetap **100% prosedural** — tidak ada PNG / sprite-sheet / `image.load`.

## Apa yang berubah

| Aspek | v1 (lama) | v2 (baru) |
|---|---|---|
| Rig native (bbox idle) | ~110 × 100 px (solid 68) | **74 × 186 px** (1.5×, telapak `y=+70`, puncak mane `y=-106`) |
| Kepadatan detail di layar | ~1.34 px native / px layar | **~2.5 px native / px layar** |
| Warna unik (idle native) | ~90 | **142** (portrait LOD: 155) |
| Skala pipeline | 0.745 (canvas 378²) | **0.402** (canvas 528²) |
| Ukuran di arena | ~74 px | **~75 px** (sama — pipeline menormalkan) |
| Biaya render | ~1–2 ms | idle **1.4 ms**, skill **1.9–2.4 ms** (hanya saat cache miss; pass v2.1) |

Memperbesar rig TIDAK memperbesar hero di arena: `heroes/__init__.py`
mengukur badan lalu men-scale agar tinggi final tetap ~51 px. Yang berubah
adalah **resolusi efektif** — setiap piksel layar kini disampel dari ~2.5
piksel native, sehingga cluster, ramp, dan muka tetap tajam setelah
smoothscale + lighting + outline pass.

## Disiplin pixel-art yang diterapkan

1. **Ramp 4–5 nilai per material dengan hue-shift** — api dingin-kepanas
   (`fire_darkest` → `fire_core`), mask ivory 5-band (`mask_shadow` →
   `mask_shine`), baja dingin 5-band, kulit 4-band, cloth merah 4-band.
2. **Selout (selective outlining)** — outline gelap hanya di sisi
   bayangan (+f, +1); sisi cahaya dibiarkan bersih + rim 1 px.
3. **Siluet bergerigi** — mane api di-generate `_tuft_points()` dari
   spine + `_hash01` deterministik (aman untuk cache), bukan poligon halus.
4. **Specular sebagai cluster** — kilau mask/baja/emas jadi 1–2 px
   yang disengaja, bukan gradien.
5. **Dither band** — titik `skin_light` di perut/kepala, tekstur klasik
   pixel-art yang selamat dari downscale.
6. **Key light kiri-atas** konsisten dengan `lighting.py`
   (`LIGHT_DIR = (-1, -1)`).

## Anatomi baru

- **Flame mane 5-layer** (`_draw_elite_flame_mane`): volume tuft
  5 tingkat + 9 lick ber-inersia (`crest_tilt` saat serang, `flare`
  saat fury/crit/omni), 12 ember deterministik naik.
- **Mask putih 5-band** (`_draw_elite_mask`): pita cahaya kiri-atas,
  strip darah (brow ridge + scar snarl), emblem emas diamond di dahi,
  grille rahang 4 gigi, **mata combat-glow** (menyala saat
  attack/spin/crit, green saat ward) + blink saat idle.
- **Tubuh berserker**: torso V-taper + dither, war-sash diagonal,
  harness X emas, medallion, belt + buckle, loincloth ber-tuft hem,
  hip tassets, pauldron baja 4-band, bracer + grip.
- **Foot solver** (`_draw_grimjaw_elite`): telapak menapak/terangkat
  bergantian, lift dari fase, **bayangan kontak per telapak**,
  debu saat menapak.
- **Flame blade 4-band** (`_draw_elite_flame_blade`): gradient
  `fire_dark` → `fire_hot` + mix incandescent saat crit/omni,
  3 lick ujung, omni-red core saat R, pommel/quillon, ember orbit.

## Animasi

- **Timeline basic attack** (dipakai bersama rig + FX tebasan,
  konstanta lama dipertahankan):
  `ATTACK_WINDUP_END = 0.25`, `ATTACK_SWING_END = 0.62`,
  `ATTACK_ARC_START = -2.30`, `ATTACK_ARC_SWEEP = -3.05`,
  `ATTACK_ARC_END = -5.35`. Tebasan **SELALU** negatif (turun).
- **1.5× keyframe pegangan** (`_blade_grip_local`): wind-up
  `(14,1)→(20,-27)`, tebas `(20,-27)→(36,-21)→(39,9)`, recovery
  `→(17,3)`; siku `_front_arm_elbow` menjaga panjang lengan
  ~19 px di semua pose.
- **Loop closure tanpa pop**: recovery (grip, sudut `→0.12`, panjang
  bilah `58→52`, lunge kaki, tilt mane, lengan belakang, siku)
  berakhir **persis di pose jaga** — frame akhir attack = frame idle
  kecuali combat-glow mata (38 px, disengaja).
- **Smear ayunan** (`_draw_blade_swing_trail`): 12 titik jalur
  ujung bilah, aktif `0.30 < ap < 0.88`, crescent 3-band.
- **Spin Blade Fury** (`_draw_spin_flame_sweep`): 3 cincin
  selang-seling arah + 2 ghost blade + 6 ember radial + shockwave.
- **Idle hidup**: napas (root bob + sway), blink, ember mane,
  mist api + platform api ter-cache.

## Skill FX (world-space, 100% prosedural)

FX membaca `hero.active_skill` / `hero.active_skill_timer` dengan
**durasi VISUAL** `SKILL_VISUAL_DURATION = {q:180, w:90, e:60, r:90}`
— bukan timer gameplay. Setiap skill punya 3 fase (aktivasi
shockwave+bintang → steady → puncak):

| Skill | Radius dunia | Visual |
|---|---|---|
| Q Blade Fury | `skill_range` (70) | ring konvergen, dashed ring, ellipse tanah, chevron, orbit particles, spin sweep |
| W Healing Ward | 100 | ring rune green, totem + pilar cahaya, heal aura + motes naik |
| E Critical Strike | cone 60 | telegraph cone + chevron + retakan tanah, glint orbit, burst bintang di pendaratan |
| R Omnislash | AOE 150 (fallback) | 4 ghost afterimage (ter-cache), pilar cahaya, slash radial 7, retakan 5, marker target + reticle |

**World-space**: `_fx_scale(hero)` = `1/_render_scale` (cap 2.6) —
efek dikompensasi agar radius di layar cocok dengan jangkauan
gameplay, tidak menyusut bersama sprite. `_ring_r()` clamp ke dalam
canvas cache (efek tidak keluar canvas = tidak terpotong).

**Tanpa alokasi per-frame**: mist, shadow, fire/rage aura, dan
platform dibangun sekali lalu di-cache (`_static`); afterimage
omnislash di-cache per `(facing, bucket pose)` (`_GHOST_BUF`) —
re-render 4× per frame di v0 (12 ms) menjadi blit 4× (0.16 ms).

## Pass performa v2.1 (budget 3.5 ms terjamin)

Audit sempat mengukur skill Q 4.3 ms & R 4.0 ms — di atas budget.
Optimasi yang diterapkan (semua visual-aman):

1. **`_clamp` fast-path** — warna palet sudah int valid 0..255;
   buang genexpr/max/min per saluran (dulu ~10% waktu rig).
2. **Scratch-surface pool** (`_scratch`) — jalur alpha
   `_aacircle`/`_aaline`/`_poly` tidak lagi mengalokasikan Surface
   per-primitif (ribuan alokasi/frame), melainkan memakai pool
   reusable ber-`fill(0)`.
3. **Blit aura tanpa `copy()`** — `set_alpha` mutasi + restore di
   static (fire/rage/heal aura, mist, glow); hemat satu copy penuh
   280×260 per frame.
4. **Ghost afterimage di-crop ke bbox konten** (di-cache bersama
   buffer) — blit hanya area berisi piksel.
5. **Rig body omnislash di-cache per bucket fase (12/s)**
   (`_OMNI_BUF`) — jitter teleport tetap live di blit; pipeline hero
   sendiri sudah mengkuantisasi frame skill, jadi tidak ada
   kuantisasi visual baru.
6. **Trail swing 5 band → 4 band, 12 → 10 langkah**; slash radial
   5 band → 3 band (standar smear berlapis Thorne v2).

Hasil (median-of-9, canvas cache 528²):

| Frame | Sebelum | Sesudah |
|---|---|---|
| idle penuh | 1.95 ms | **1.40 ms** |
| Q Blade Fury | 4.27 ms | **2.32 ms** |
| W Healing Ward | 3.25 ms | **1.89 ms** |
| E Critical | 2.64 ms | **1.97 ms** |
| R Omnislash | 3.99 ms | **1.87 ms** (fase live 1.87) |

## Kompatibilitas

Semua nama publik lama dipertahankan (lihat `_EXTRA['grimjaw']` di
`heroes/__init__.py`): `draw_grimjaw`, `draw_hero`,
`_draw_grimjaw_elite`, `_draw_grimjaw_idle/walk/attack/body`,
`_draw_grimjaw_ghost`, `_blade_angle`, `_blade_grip_local`,
`_blade_len`, `_blade_tip_local`, `_update_attack_anim`,
`_detect_moving`, `PALETTE`, dll. Atribut privat yang dipakai test
(`_gj_attack_active`, `_gj_attack_progress`, `_gj_crit_active`,
`_gj_prev_timer`, `_gj_last_x/y`) tetap diset oleh
`_update_attack_anim` / `_detect_moving`.

## Verifikasi

- `tools/test_grimjaw_swing_arah.py` — arah tebasan ATAS→BAWAH,
  puncak di paruh pertama, pendaratan depan-bawah, recovery tidak naik.
- `tools/test_grimjaw_masterwork.py` — prosedural, swatch palet,
  geometri blade pose-driven, portrait LOD, 12 frame animasi,
  Q/W/E/R, **ring AOE world-space** (fs 1.0 vs 0.45), outline.
- `tools/_audit_grimjaw_v2.py` — audit + 5 sheet:
  `docs/grimjaw_v2_{review,anim_strip,ingame,skills,before_after}.png`.
  Cek: skala pipeline (75 px layar), frame unik, portrait LOD,
  swatch, coverage mane, telapak/mata, **budget 3.5 ms**
  (median-of-9, canvas 528²), ring Q tepat di radius dunia,
  FX W/E/R di luar badan.
- `tools/test_gornak_masterwork.py` — keseimbangan ukuran antar-hero
  (W/H Grimjaw vs Gornak/Kaizen) tetap hijau.
- `tools/_shot_grimjaw_masterwork.py` — sheet preview lama, canvas
  sudah di-retune untuk rig 1.5×.
