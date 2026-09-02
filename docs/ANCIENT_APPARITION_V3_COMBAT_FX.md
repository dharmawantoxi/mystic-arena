# Ancient Apparition v3 — Combat FX & Game Feel (lapisan hidup 100% prosedural)

> Rewrite penuh sistem visual + tempur **ANCIENT APPARITION** (True Boss
> Level 3 / Ice Mage). Tetap **100% prosedural**: tidak ada PNG/JPG/GIF,
> tidak ada sprite-sheet, tidak ada loader tekstur. Semua dibangun dari
> `pygame.Surface`, `pygame.draw`, `pygame.transform`, `pygame.Vector2`,
> `Rect`, alpha/additive blending, dan API pygame sejenis.
>
> Dokumen ini memaparkan hasil rewrite: renderer pixel-art chunky,
> animation controller, ayunan cakar berbasis busur, weapon trail,
> projectile modular, skill FX lifecycle Q/W/E/R, impact, particle
> system, hit-stop, screen shake, dan overlay debug.

---

## 1. Masalah sistem lama

Analisis sebelum rewrite (namespace lama `bosses/level3.py`):

1. **Animasi minim.** Hanya idle-bob/walk-bob; serangan = gelombang kecil
   tangan tanpa fase (anticipation / wind-up / swing / impact / follow
   through / recovery), tanpa bobot / momentum badan.
2. **Tidak ada controller animasi.** Tidak ada state (IDLE/WALK/RUN/
   ATTACK/CAST/SKILL/HIT/HURT/DEATH/CHARGE/SPECIAL), tidak ada prioritas
   atau transisi; RUN dan HURT tidak ada sama sekali.
3. **Sprite hero di-cache → FX beku.** Saat AA dimainkan, skill FX
   (vortex, beam, erupsi) digambar ke canvas cache yang dikuantisasi:
   efek meloncat mengikuti refresh cache dan ikut menyusut oleh
   smoothscale (≈ 0.63×).
4. **Proyektil lemah.** Jalur hero memakai shard generik (wajik + glow
   lingkaran); bidang tidak lengkap (tanpa `damage/lifetime/radius`
   formal), tanpa rotasi/inti/ekor facet.
5. **Tidak ada game feel.** Tidak ada particle system, impact FX,
   hit-stop, atau shake khusus karakter jalur hero.
6. **Semua efek = lingkaran.** Glow bertumpuk `_aacircle` di mana-mana,
   melanggar prinsip bentuk (shard, kristal, gerigi, retakan).

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph)** | `bosses/level3.py :: _NS_ancient_apparition` (rewrite penuh) | rig pixel-art chunky 2× (buffer ½ resolusi → upscale nearest), palet dark-fantasy, controller animasi (fase + state + bobot), shadow reaktif, platform beku, telegraph + skill FX **fallback** canvas, proyektil canvas fallback |
| **Lapisan hidup 1:1** | `heroes/ancient_apparition_fx.py` (baru) | arc ayunan cakar + trail ribbon dari histori, particle system berbatas, proyektil shard/bolt modular, vortex Q / beam gerigi W / Ice Blast E / Cold Feet R lifecycle, impact flash + shockwave + debris + serpihan, shatter kematian, hit-flash, overlay debug |
| **Bus game feel (shared)** | `heroes/combat_feel.py` | hit-stop global 0.03–0.08 s, screen shake meluruh bertahap, delta-time frame — dipakai bersama Zephyr/Gornak/Vex/… |

Jaminan arsitektur (kontrak yang sama dengan karakter v3 lain):

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati pada
  skala layar 1.0, tidak menyusut, tidak membeku;
* renderer tetap pemilik **geometri badan**: `arm_geometry()` dipanggil
  malas oleh modul FX (`_renderer()`), jadi trail & asal shard selalu
  menempel pada cakar yang digambar — angka shoulder/upper/fore/claw
  identik di kedua sisi (diuji `test_arm_geometry_mirror`);
* kalau `heroes.ancient_apparition_fx` gagal dimuat, `owns()` = False dan
  renderer menggambar sendiri beam W, bolt E, vortex Q, erupsi R versi
  canvas + trail canvas (`_draw_swing_trail`) — polish hilang, efek
  **tidak pernah** hilang;
* **nol perubahan balance**: damage tetap milik `_entity.py`,
  `hero_skills/_bundle.py`, dan `bosses/base_boss.py`; lapisan FX hanya
  *membaca* state (`attack_timer`, `active_skill`, `vortex_x/y`,
  `vortex_active_timer`, `w_dir_x/y`, `r_dir_x/y`, `hp`, `alive`).

## 3. Renderer pixel-art chunky (§ render + gaya)

* **PIXEL = 2**: seluruh rig digambar di buffer 64×76 (½ resolusi) lalu
  di-upscale nearest-neighbor → piksel chunky 2×2, tepi keras, highlight
  & shadow per-piksel (rasio blok terukur 0.83 — lihat audit).
* Urutan layer rig: back arm → orbit → skirt (jubah shard) → torso →
  pauldron (armor) → head (hood berongga + wajah glow) → crown → front
  arm + claw (senjata) → orbit depan → rim highlight.
* Silhouette: wraith es mengambang — tanpa kaki (hem shard berselang),
  mahkota 5 paku tinggi, mata menyala; 3 splinter mengorbit sebagai
  sumber visual shard basic attack.
* Komposit lama dipertahankan (`_composite_boss_body`): crop rapat →
  outline siluet 1 px 4 arah → pass pencahayaan rim es.
* Cache kelas: `_rig_lo/_rig_px`, `_shadow_cache`, `_aura_cache`,
  `_ground_cache`, `_mist_cache`, `_body_buf` (idle terukur
  **0.72 ms/frame**, budget 2.35).

## 4. Animation controller (§ animasi + attack)

* **Fase serangan** (`ATK_PHASES`, progress 0..1):
  `anticipation 0–0.20 → windup 0.20–0.38 → swing 0.38–0.55 →
  follow 0.55–0.75 → recovery 0.75–1.0`; shard lepas di titik IMPACT
  0.50. Lengan bergerak **menerus via busur** (`arc_angle`, ease
  in/out/in-out) — tidak pernah teleport (diuji
  `test_arc_swing_not_teleporting`, `test_claw_sweeps_forward`).
* **State director** (prioritas): `DEATH > HURT > HIT > SPECIAL(R) >
  SKILL(Q/W) > CAST(E) > SWING > CHARGE > ATTACK > RUN > WALK > IDLE`,
  edge-triggered dari state gameplay, transisi ber-hysteresis.
* Pose per skill: Q menyalurkan, W mendorong dua tangan, E gather di
  dada, R terangkat tinggi (+hover). HURT = tilt + flicker mata + jitser.
* Timeline 60 Hz diambil dari `attack_timer` gameplay (bukan pose cache),
  jadi progress tetap halus walau sprite dipakai ulang.

## 5. Weapon trail (§ swing trail)

`SlashTrail` menyimpan 12 sampel `(grip, tip)` ujung cakar; ribbon
polygon transparan per segmen (alpha memudar + teksis terah 1 px
mengikuti arah ayunan) + partikel piksel dari ujung saat menyapu.
Fallback canvas: `_draw_swing_trail` (histori `boss._aa_trail`).

## 6. Projectile system (§ projectile + visual)

`ApparitionProjectile` — bidang lengkap `position/velocity/speed/
damage/lifetime/target/radius/hit_radius/rotation/trail/particles/
active`, `pygame.Vector2`, delta-time, homing steering, lifecycle
`SPAWN → TRAVEL → TRAIL → HIT → IMPACT FX → DESTROY`:

* **shard** — basic attack: shard es bersegi berarah, inti panas, halo,
  ekor facet memudar;
* **bolt** — E Ice Blast: besar, lambat, 3 shard pengorbit;
* reaver/tracer R — jejak dingin cepat.

Jalur hero memakai renderer bersama `draw_ice_shard()` (dipanggil
`_entity._draw_ice_shard_projectile`) supaya shard generik tampil
identik dengan lapisan hidup; impact diumumkan lewat
`notify_projectile_impact` (paritas Vex/Sylara/Razak).

## 7. Skill FX lifecycle (§ skill fx)

`SkillFX` per skill — `CAST → CHARGE → RELEASE → TRAVEL/AREA →
IMPACT/AFTER → FADE`, durasi sinkron gameplay (Q 3.9 s mengikuti
`vortex_active_timer` 180, W 0.95 s/45, E 1.75 s/50, R 2.6 s/90):

* **Q Ice Vortex** — di lokasi `vortex_x/y` dunia (dipetakan ke layar):
  genangan elips bergerigi, 6 shard orbit 3 ketinggian berputar, salju
  tersedot spiral ke dalam, mist naik, tick ring tiap ⅓ s mengikuti
  damage tick DOT.
* **W Chilling Touch** — chevron telegraph → beam gerigi bergerak
  (quad per segmen + gelombang sinus + gerigi tepi + gelombang dingin
  berjalan) — BUKAN lingkaran.
* **E Ice Blast** — gather shard saling mengunci di tangan → bolt besar
  terbang → ledakan: flash bintang, shockwave elips ganda, 8 paku es
  radial, retakan tanah, debris + smoke.
* **R Cold Feet** — lingkar peringatan berdenyut + silang → salju
  menguncup → erupsi: 12+8 paku es cincin + menara tengah, gelombang
  beku melebar, retakan radial (di target, arah `r_dir_x/y`).

## 8. Particle + impact + game feel (§10–12)

* `Particle`: `position, velocity, acceleration, life, max_life, size,
  rotation, rotation_speed, alpha, gravity, color, drag, shrink, shape`
  (pixel/shard/snow/spark/smoke/mist/star) + layer back/front;
  `ParticleSystem` pool cap 170, burst/stream/ring (rentang acak via
  `_range_val`), menghormati `mobile.perf.Quality`.
* `ImpactFX`: flash bintang 4+4 arah, shockwave elips melebar, sabit
  goresan (slash fragment) searah datang, debris shard ber-gravity,
  smoke, nova putih saat crit.
* **Hit-stop 0.038 / 0.06 / 0.07 s** (hit/blast/erupt) + **shake
  3.2–10 ber-peluruhan** lewat bus `combat_feel` (tidak menumpuk antar
  karakter); slow-motion FX 0.18× saat beku.
* **Alpha-safe XRGB**: buffer layar game tidak punya kanal alpha —
  semua bentuk transparan lewat `_poly_a/_line_a/_circle_a` (scratch
  SRCALPHA pool, diuji `test_fx_draw_on_xrgb_screen`).

## 9. Integrasi

* `heroes/__init__.py`: `ancient_apparition` masuk `_LIVE_FX_HEROES` +
  `_LIVE_FX_PATHS` (pre = ground/back particles, post = trail/proyektil/
  skill/impact/debug).
* `bosses/level3.py :: _live_fx()`: jalur BOSS menggambar lapisan hidup
  langsung (draw tiap frame tanpa cache); jalur HERO hanya `attach()`
  (penggambaran oleh pipeline hero) — `owned()` men-suppress FX canvas
  supaya tidak dobel (diuji `test_live_layer_suppression`).
* `_entity.py`: `_draw_ice_shard_projectile` → `draw_ice_shard()` +
  `notify_projectile_impact` di titik pendaratan proyektil generik.
* `_core.py`: modul masuk daftar HUD perf (`Hero FX: N particles`).
* Guard lama tetap: `_aa_hero_basic_shard` (hero memakai sistem Hero),
  `_skip_renderer_projectiles` (parking cache), `_portrait_hd`
  (Hero Shop tanpa FX layar).

## 10. Debug + pengujian

* `DEBUG_CHARACTER` (modul FX & renderer): hurtbox, hitbox jendela
  swing, jangkauan, tabrakan proyektil, state/fase animasi, FPS, jumlah
  partikel/proyektil/impact/skill, shake & hit-stop.
* `tools/test_ancient_apparition_v3_combat.py` (pytest, 32 uji):
  prosedural-murni, kontrak API, fase & state animasi, busur ayunan,
  mirror geometri, cap partikel & peluruhannya, lifecycle proyektil &
  skill, posisi cast (Q vortex dunia / R target / W tangan), jendela
  hit-stop, supresi ganda + fallback, durasi canvas == AI (60/45/50/90),
  render semua mode, jalur hero, XRGB, performa, overlay debug.
* `tools/_audit_ancient_apparition_v3.py`: audit piksel — siluet
  (crown/torso/skirt/orbit), glow mata, shadow menapak, rasio blok
  chunky 2× (0.83), tanpa flicker canvas, flash/trail ayunan depan,
  sway hem saat jalan.
* `tools/_shot_ancient_apparition_v3.py`: screenshot semua mode ke
  `tools/_aa_v3_shots/` (idle/walk/run/4 fase serangan/skill/hurt/
  impact blast).
* Regresi lama tetap hijau: `tools/test_level3_masterwork.py` (durasi
  FX == AI, hurt-flash, shadow reaktif, outline+lighting, bbox, perf)
  dan seluruh suite `tools/` (63 pass, hanya 2 gagal pre-existing yang
  butuh audio/server).
