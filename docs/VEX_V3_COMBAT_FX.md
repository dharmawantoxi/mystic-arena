# Vex v3 — Combat FX & Game Feel (lapisan hidup 100% prosedural)

> Rewrite penuh sistem tempur **VEX** (Void Harbinger, mage ranged). Tetap
> **100% prosedural**: tidak ada berkas gambar eksternal, tidak ada
> sprite-sheet, tidak ada loader tekstur. Semua dibangun dari
> `pygame.Surface`, `pygame.draw`, `pygame.transform`, `pygame.Vector2`,
> `pygame.mask`, `Rect`, dan API pygame sejenis yang dipakai pipeline.
>
> Dokumen ini memaparkan **sistem tempurnya** (animation controller, swing
> staff berbasis busur, weapon trail, projectile modular, skill FX
> lifecycle, impact, particle, hit-stop, screen shake, debug overlay).
> Untuk geometri badan & disiplin renderer masterwork, lihat
> [`VEX_V2_RENDERER.md`](VEX_V2_RENDERER.md).

---

## 1. Masalah yang sebenarnya

Sesudah pass renderer v2, Vex punya rig void-harbinger yang solid — tapi
*tempurnya* belum selive Zephyr/Gornak/Grimjaw/Kaizen, dan penyebabnya
arsitektural (sama persis dengan pola Kaizen v3):

1. **Sprite hero di-cache dan di-kuantisasi.** `heroes/__init__.py`
   (`_hero_cache_key`) memakai ulang gambar selama pose sama. Semua efek
   yang digambar **ke dalam canvas cache** ikut beku: smear staff
   patah-patah, sabit void melompat mengikuti kuantisasi pose.
2. **Canvas di-smoothscale.** Skala pipeline Vex ≈ 0.62, jadi FX in-canvas
   ikut menyusut dan lembek — bukan pixel-art tegas di skala layar.
3. **Tidak ada progress serangan 60 Hz.** Tidak ada nama fase, prioritas
   state, transisi, atau delta-time; FX hanya bisa mengikuti cache miss.
4. **Tidak ada game feel sama sekali.** Orb Vex adalah proyektil generik
   (`_entity._draw_magic_orb_projectile`); Q/W/E/R menerapkan damage dari
   `hero_skills` tanpa hit-stop, shake, atau impact FX khusus karakter.
5. **Tidak ada particle/projectile system hidup.** Tidak ada pool, tidak
   ada cap, tidak ada lifecycle; semua efek deterministik per pose (bagus
   untuk cache, beku untuk umpan balik).

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph)** | `heroes/_bundle.py :: _NS_vex` | rig v2, palet, pose serang staff, telegraph AOE Q/W/E/R (besar), conduit beam, portal collapse, smear staff **fallback** saat modul FX tidak dimuat |
| **Lapisan hidup 1:1** | `heroes/vex_fx.py` (baru) | sabit void dari histori posisi orb staff, particle system berbatas, proyektil void modular, impact FX, skill FX lifecycle, animation state machine cermin, hit-flash, overlay debug |
| **Bus game feel (shared)** | `heroes/combat_feel.py` | hit-stop global 0.03–0.08 s, screen shake meluruh, delta-time frame — dipakai bersama Zephyr, Gornak, Grimjaw & Kaizen |

Jaminan arsitektur (kontrak yang sama dengan Gornak/Grimjaw/Kaizen v3):

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati pada
  skala layar 1.0, tidak pernah menyusut atau beku;
* renderer tetap satu-satunya pemilik **geometri badan** — lapisan hidup
  *membaca* pose lewat jembatan malas (`_renderer()`), memakai
  `staff_points()` / `render_scale()` / `swing_hitbox()` yang sumbernya
  sama dengan renderer, jadi orb dan trail tidak mungkin beda frame;
* kalau `heroes.vex_fx` gagal diimpor, `owns()` = False dan renderer
  menggambar smear in-canvas sendiri (`_draw_staff_smear`) — visual
  kehilangan polish, **tidak pernah** kehilangan efek;
* **nol perubahan gameplay/balance**: damage tetap milik `_entity.py` dan
  `hero_skills`; lapisan hidup hanya *membaca* state (`attack_timer`,
  `active_skill`, `_sanity_eclipse_timer`, `_astral_prison_timer`,
  `_essence_flux_timer`, `hp`, `alive`) dan menggambar.

## 3. Animation controller (`VexFXDirector`)

* **Progress 60 Hz dari gameplay** — `attack_timer` berkurang tiap langkah
  simulasi, jadi `_update_attack_timeline()` menghasilkan progress halus
  tanpa menunggu cache miss; edge `timer naik` = ayunan baru, `prev < 0`
  = director dibuat di tengah ayunan (kasus ini **langsung mempersenjatai**
  `_attack_live` kalau `timer > 0`, supaya unit baru tidak kehilangan
  sabit pertamanya).
* **Fase timeline ditarik dari renderer** (`_resolve_timeline()`), jadi
  renderer tetap satu sumber kebenaran. Hasil resolusi saat ini:

  | Fase | Rentang progress |
  |---|---|
  | ANTICIPATION | 0.00 – 0.129 |
  | WINDUP | 0.129 – 0.28 |
  | SWING | 0.28 – 0.50 |
  | IMPACT | 0.50 – 0.64 |
  | FOLLOW | 0.64 – 0.66 |
  | RECOVERY | 0.66 – 1.00 |

  dengan `ATTACK_IMPACT_POINT = 0.56`, `ATTACK_SWING_END = 0.66`, dan
  jendela senjata aktif `SWING_START = 0.26 … SWING_END = 0.88`.
* **State machine berprioritas** (`ANIM_PRIORITY`): IDLE 0 < WALK 10 <
  RUN 15 < CHARGE 30 < CAST 35 < ATTACK 40 < SWING 45 < SKILL 50 <
  SPECIAL 55 < HIT 60 < HURT 65 < DEATH 100. DEATH terkunci selama unit
  mati; transisi butuh prioritas ≥ **atau** `state_time > 0.05 s`
  (anti flicker antar state berprioritas rendah).
* **Deteksi edge**: HURT dari penurunan `hp` (atau `notify_hurt`), DEATH
  sekali per tumbang, W/E/R dari timer gameplay mentah (tanpa menunggu
  `active_skill` pipeline), Q dari `active_skill == "q"` / edge timer.

## 4. Swing attack + weapon trail (arc-based, bukan lerp)

* Trail dibangun dari **histori posisi orb staff yang tersimpan**: tiap
  frame swing, `staff_points()` membaca pose renderer, lalu
  `SwingTrail.push()` menyimpan pasangan (inner, outer). OLD → CURRENT
  membentuk pita poligon translucent berlapis pada rentang **0.34 – 1.30**
  dari vektor grip→orb, jadi pita menutup dua pertiga luar staff dan
  sedikit melampaui orb (smear terbaca tanpa menutupi tangan).
* **Sabit void** digambar sebagai 3 busur bertumpuk (halo gelap 8 px →
  badan 5 px → inti terang 3 px) dengan `span = 0.62 + 0.55 * power` dan
  `base_r = 13 + 32 * power * (0.45 + t)`, plus 3 busur fragmen yang
  memecar keluar dan chevron 3 garis di ujung sabit. Semua **arc-based**,
  dikunci tes (`test_orb_staff_mengikuti_busur_bukan_lerp`).
* **Release** di titik IMPACT: `ring(8, 7, speed=(40,100), swirl=1.6)` +
  `shake(2.6, 0.14)` walau serangan meleset.
* Saat lapisan hidup memiliki unit (`owns()`), renderer **melewati**
  `_draw_staff_smear` in-canvas (flag `_FX_LIVE`) — tidak ada efek yang
  digambar dua kali.

## 5. Projectile — void shard (`VexProjectile`)

Kontrak atribut penuh: `position, velocity, speed, damage, lifetime,
target, radius, rotation, trail, particles, active`.
Lifecycle: `SPAWN → TRAVEL (homing halus) → TRAIL pita menyempit → HIT
(radius vs radius unit) → IMPACT FX → DESTROY`.

* Badan = **serpihan kristal bersegi + orb bersegi 8** (bukan lingkaran
  polos) dengan glow premultiplied, speed line, dan glint orbit
  deterministik.
* Orb serangan dasar & Q memakai renderer bersama
  `draw_arcane_orb()` — dipakai langsung oleh
  `_entity._draw_magic_orb_projectile` (dengan fallback ke jalur lama
  kalau modul belum siap).
* Proyektil visual **tidak** membawa damage: serangan dasar dan Q/W/E/R
  tetap dihitung `_entity.py` / `hero_skills` (dikunci tes).

## 6. Skill FX (lifecycle `cast → charge → release → area → impact → fade`)

Radius dunia sinkron gameplay (`WORLD_RADIUS`): **Q = 250**, **W = 60**,
**E = 200**, **R = 180** px. Umur FX (`SKILL_TOTAL`) mengikuti status
gameplay yang sebenarnya, bukan hanya durasi pose:
`q 0.95 s, w 3.25 s, e 2.85 s, r 1.65 s`.

| Skill | Bahasa lapisan hidup (badan besar tetap milik renderer) |
|---|---|
| Q Arcane Orb | aperture iris membuka + paket stream menyusur conduit + chevron berarah; release memicu proyektil + streak (shake 4.2, hit-stop 0.035) |
| W Sanity's Eclipse | cincin retak tanah + crystal spike naik bertahap + tick tiap 20 frame selama `_sanity_eclipse_timer` (shake 5.5, hit-stop 0.042) |
| E Astral Imprisonment | kurungan bersegi + jeruji rune + rotasi lambat mengurung target, lalu **shatter** pecahan ungu (shake 3.4 pada cast) |
| R Essence Flux | implosi awal + debu tersedot, lalu ledakan void radial + serpihan terlempar — puncak game feel (shake 11.0, hit-stop 0.075) |

Pagar anti-beku: emisi W/E/R berhenti kalau timer gameplay macet > 15 s
(unit mati di tengah skill), dan director yang mati tidak lagi memancarkan
mote ambien — tidak ada partikel abadi di mayat.

## 7. Impact system + game feel

`notify_projectile_impact` (jalur ranged generik `_entity`) dan
`notify_melee_impact` (paritas karakter lain) memicu: flash bintang berarah
→ shockwave elips → spoke debris → fragmen sabit 3 busur (+ silang saat
crit) → serpihan void ber-gravitasi → puff debu belakang, plus:

* **hit-stop** `0.036 + 0.02·power (+0.014 crit)` detik — selalu di dalam
  rentang 0.03–0.08 s yang dijepit bus `combat_feel`;
* **screen shake** `3.4 + 3.2·power (+2.6 crit)` yang meluruh bertahap
  (trauma-based, satu jalur kamera lewat `EffectManager`);
* partikel dibudget `mobile.perf.Quality` (`particle_ratio`, cap keras
  170/director, pool dipakai ulang).

## 8. Integrasi (file yang berubah)

| File | Perubahan |
|---|---|
| `heroes/vex_fx.py` | **baru** — seluruh engine di atas |
| `heroes/__init__.py` | `vex` masuk `_LIVE_FX_HEROES` + `_LIVE_FX_PATHS["vex"] = "heroes.vex_fx"` |
| `heroes/_bundle.py` | `_NS_vex`: jembatan `_live_module`/`_fx_live_owned`/`_FX_LIVE`, attach + `draw_ground_layer` di jalur `hero_lane`, `draw_live_layer` di jalur boss, skip `_draw_staff_smear` saat owned |
| `_entity.py` | blok `notify_projectile_impact` Vex setelah Zephyr; `_draw_magic_orb_projectile` mendelegasi ke `vex_fx.draw_arcane_orb` |
| `_core.py` | `vex_fx` masuk tuple jumlah partikel HUD debug |

### Catatan performa — `_advance()` bukan `tick()`

`draw_ground_layer()` **tidak** memanggil `tick()` (yang akan memperbarui
*setiap* director, sehingga N unit Vex hidup = N×N pembaruan per frame).
Ia memanggil `_advance(director)`: sebuah stempel `pygame.time.get_ticks()`
per director (`_last_ms`) membuat tiap unit maju paling banyak sekali per
milis, sementara bus game-feel bersama (clock + peluruhan shake) tetap
dipacu lewat `_feel.fx_dt()`, dan hit-stop tetap menskala dt ×0.18.
`tick()` ikut menyetel `_last_ms` supaya kedua jalur tidak pernah
menggandakan langkah unit yang sama. Hasil terukur pada bench 6v4:
**10.00 → 8.70 ms/frame**, dan biaya per-unit menjadi linear
(1/2/4/8/12 unit → 0.80/0.69/0.71/0.66/0.64 ms per unit).

## 9. Verifikasi

* `tools/test_vex_v3_combat.py` — **60 tes** dalam 10 bagian:
  prosedural & API, animation controller (fase/prioritas/progress 60 Hz),
  swing & trail (busur vs lerp, histori posisi, hitbox), particle system
  (kontrak, cap, peluruhan, pool), projectile system (lifecycle penuh,
  homing, cap), skill FX (lifecycle Q/W/E/R, radius dunia, pagar
  anti-beku), impact/game-feel (rentang hit-stop, shake meluruh),
  supresi ganda (renderer vs lapisan hidup: owns/attach/release),
  overlay debug, dan performa (linearitas, cache, tidak ada kebocoran).
* Seluruh suite pytest `tools/` tetap hijau (**406 lulus**). Berkas uji
  bergaya skrip yang memanggil `sys.exit` pada impor dijalankan terpisah
  dan semuanya lulus; satu di antaranya (`test_tactical_hold.py`) bergantung
  pada *real-time clock*, sehingga gagal bila dikoleksi pytest — itu
  **sudah** terjadi sebelum perubahan ini (terbukti lewat worktree pada
  `HEAD`), dan `test_build_slots.py` kehilangan fixture `g` sejak lama.
* `tools/_shot_vex_fx.py` → `docs/vex_v3_combat_fx.png` (lembar momen
  tempur: IDLE, WALK, 5 pose SWING, Q cast/release/conduit, W rise/hold,
  E prison/shatter, R burst, IMPACT biasa & crit, projectile system,
  hurt flash, overlay debug).
* Simulasi penuh `Game(level_number=1)` 900 frame + 600 frame pembuangan:
  puncak partikel 684, puncak proyektil 32, 6 director, `reset_all()`
  mengembalikan 0 partikel / 0 proyektil — tanpa crash dan tanpa
  pertumbuhan tak terbatas.

## 10. Debug

`heroes/vex_fx.DEBUG_CHARACTER = True` → hitbox & hurtbox, jangkauan
serang, kerucut hit saat SWING/IMPACT, radius AOE W/E/R, collision
projectile, state & fase animasi, timer skill, jumlah partikel, nilai
shake, hit-stop, dan FPS.

## 11. Palet

`VEX_PALETTE` memegang kontrak 9 kunci karakter (`outline, shadow, dark,
body, mid, light, highlight, weapon, fx`) **plus** ramp void
(`fx_deepest … fx_white`), ramp astral ungu (`astral_deepest …
astral_hot`), rune emas (`rune_dark/mid/light`, `gold`, `gold_hot`),
material staff, kristal biru-es, dan materi lingkungan (dust, smoke).
`_PALETTE_SYNC` memetakan tiap kunci ke kunci renderer
(`_NS_vex.PALETTE`) dan divalidasi oleh
`_sync_palette()` — kalau renderer mengubah warna, lapisan hidup ikut
tanpa perlu disunting (dikunci tes `test_palet_sinkron_dengan_renderer`).
