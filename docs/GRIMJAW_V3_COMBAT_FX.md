# Grimjaw v3 — Combat FX & Game Feel (lapisan hidup 100% prosedural)

> Rewrite penuh sistem tempur **GRIMJAW** (Juggernaut / The Blade Fury,
> starter hero). Tetap **100% prosedural**: tidak ada PNG / JPG / GIF /
> sprite-sheet / texture eksternal. Semua dibangun dari `pygame.Surface`,
> `pygame.draw`, `pygame.transform`, `Rect`, `Vector2`, dan `pygame.mask`
> API sejenis yang dipakai pipeline.
>
> Dokumen ini memaparkan **sistem tempurnya** (animation controller, swing
> attack, weapon trail, projectile, skill FX, impact, particle, hit-stop,
> screen shake, debug overlay). Untuk geometri badan & disiplin pixel-art
> renderer masterwork, lihat [`GRIMJAW_V2_RENDERER.md`](GRIMJAW_V2_RENDERER.md).

---

## 1. Masalah yang sebenarnya

Sesudah pass renderer v2, Grimjaw punya rig masterwork yang bagus — tapi
*tempurnya* belum selive Gornak/Zephyr, dan penyebabnya arsitektural:

1. **Sprite hero di-cache dan di-kuantisasi.** `heroes/__init__.py`
   (`_hero_cache_key`) memakai ulang gambar selama pose sama (fase serang
   diperbarui tiap 2 frame). Semua efek yang digambar **ke dalam canvas
   cache** ikut beku: smear ayunan patah-patah, impact flash hanya berganti
   tiap 2 frame.
2. **Canvas di-smoothscale.** Skala pipeline Grimjaw ≈ 0.402 (canvas 528²),
   jadi FX in-canvas ikut menyusut dan lembek — bukan chunky pixel-art.
3. **Tidak ada animation controller.** `_update_attack_anim` menghitung
   `_gj_attack_progress` untuk pose, tapi tidak ada nama fase, prioritas
   state, transisi, delta-time — tidak ada yang bisa ditanya "sekarang
   fase apa, sudah berapa detik".
4. **Tidak ada game feel.** Basic attack Grimjaw adalah damage **instan**
   melee (`_entity.py`), Q/R men-tick damage dari `hero_skills` — tidak ada
   satu pun tempat yang memicu hit-stop, shake, atau impact FX.
5. **Tidak ada particle/projectile system hidup.** Ember api di rig bersifat
   deterministik per pose (bagus untuk cache, beku untuk umpan balik), dan
   kit Grimjaw tidak punya bahasa proyektil sama sekali.

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph)** | `heroes/_bundle.py :: _NS_grimjaw` | rig masterwork v2, palet, pose & keyframe bilah, controller timer serangan, marker tanah Q/W/E/R, smear/impact **fallback** saat modul FX tidak dimuat |
| **Lapisan hidup 1:1** | `heroes/grimjaw_fx.py` (baru) | trail pedang dari histori posisi nyata, particle system berbatas, proyektil gelombang bilah, impact FX, skill FX lifecycle, animation state machine cermin, hit-flash, overlay debug |
| **Bus game feel (shared)** | `heroes/combat_feel.py` | hit-stop global 0.03–0.08 s, screen shake meluruh, delta-time frame — dipakai bersama Zephyr & Gornak |

Jaminan arsitektur (sama dengan kontrak Gornak v3):

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati pada skala
  layar 1.0, tidak pernah menyusut atau beku;
* renderer tetap satu-satunya pemilik **geometri badan** — lapisan hidup
  *membaca* `_blade_grip_local` / `_blade_tip_local` / `_render_scale`
  lewat jembatan malas (`_renderer()`), jadi bilah dan trail tidak mungkin
  beda frame;
* kalau `heroes.grimjaw_fx` gagal diimpor, `owns()` = False dan renderer
  menggambar smear + impact pop in-canvas sendiri — visual kehilangan
  polish, **tidak pernah** kehilangan efek;
* **nol perubahan gameplay/balance**: damage tetap milik `_entity.py` dan
  `hero_skills`; lapisan hidup hanya *membaca* state (`_blade_fury_timer`,
  `_omnislash_timer`, `_heal_ward_timer`, `_crit_buff_timer`, `hp`,
  `alive`) dan mendeteksi tepi (edge-triggered).

## 3. Isi `heroes/grimjaw_fx.py`

| Komponen | Ringkasan |
|---|---|
| `GRIMJAW_PALETTE` | kontrak 9 kunci (`outline..fx`) + ramp api/darah/emas/rage/heal + asap; disinkronkan dari `_NS_grimjaw.PALETTE` lewat `_PALETTE_SYNC` (satu karakter, satu warna) |
| `Particle` | `position, velocity, acceleration, life, max_life, size, rotation, rotation_speed, alpha, gravity, color, color_end, drag, fade_pow, back`; bentuk: `pixel, glow, spark, shard, streak, ember, smoke` — semua hard-edge, pixel-snapped |
| `ParticleSystem` | pool reusable + cap keras (`MAX_PARTICLES=180`), `spawn/burst/stream/update/draw`, lapisan `back/front`, jumlah mengikuti preset kualitas mobile (`particle_budget`) |
| `SwingTrail` | histori `(grip, tip, umur)` → pita poligon **4 band** (selubung gelap → badan api → inti membara → garis ujung putih), umur 0.26 s, mode `spin_mode` untuk Blade Fury; otomatis mengikuti arah tebasan karena murni turunan lintasan bilah |
| `ImpactFX` | flash bintang 8 arah, **shockwave elips berarah** (bukan lingkaran), spoke debris, 3 slash-fragment busur, silang + pilar pendek (`omni`), lengkung sapuan horizontal (`spin`); varian `crit` emas |
| `GrimjawProjectile` | kontrak penuh `position/velocity/speed/damage/lifetime/target/radius/rotation/trail/particles/active`; lifecycle `SPAWN→TRAVEL→TRAIL→HIT→IMPACT FX→DESTROY`; homing halus, tumbukan radius vs target, callback `on_impact`; **visual-only** (damage gameplay tetap di `hero_skills`) |
| `ProjectileSystem` | cap 20, spawn/update/draw + auto-cleanup |
| `SkillFX` | lifecycle `CAST→CHARGE→RELEASE→TRAVEL/AREA→IMPACT→AFTER→FADE` untuk Q/W/E/R: pilar cahaya, nova ring, retakan tanah deterministik, rune diamond orbit, chevron kerucut (E), mote hijau (W), burst shard (R) |
| `GrimjawFXDirector` | satu per unit: state machine + event FX (lihat §4) |
| `draw_debug_overlay` | `DEBUG_CHARACTER=True` → hitbox kerucut, hurtbox, attack range, radius Q, lingkar tumbukan proyektil, state/fase/FPS/jumlah partikel/timer skill |
| API modul | `attach / owns / director_for / tick / reset_all / total_particles / total_projectiles / draw_ground_layer / draw_live_layer / notify_melee_impact / notify_skill_impact / notify_skill_cast / notify_hurt / draw_blade_wave / hit_stop / shake / should_freeze_frame / clear_cache` |

## 4. Animation controller (cermin renderer)

`ANIM_PRIORITY` berisi **semua** state master-prompt:
`IDLE WALK RUN CHARGE CAST ATTACK SWING SKILL SPECIAL HIT HURT DEATH`
(angka besar = lebih penting; `DEATH` mengunci).

Fase serangan di-*resolve* dari konstanta renderer sehingga rig, trail, dan
FX selalu sepakat kapan tebasan mendarat:

```
ANTICIPATION → WINDUP → SWING → IMPACT → FOLLOW → RECOVERY
0 .. WINDUP_END(0.25) .. SWING_END(0.62) .. 1.0
```

(`_resolve_timeline()` menarik `ATTACK_WINDUP_END`/`ATTACK_SWING_END` dari
`_NS_grimjaw` saat import — kalau renderer di-retune, fase FX ikut otomatis.)

Event yang dipicu director dari state hero (edge-triggered, delta-time):

| Pemicu | Event FX |
|---|---|
| `timer` naik (serangan baru) | debu antisipasi + smoke belakang, reset trail |
| fase `SWING..FOLLOW` | trail diisi dari `_blade_tip_local` tiap frame |
| `progress ≥ ATTACK_SWING_END` | **whoosh pop** (impact ringan — feedback walau meleset) |
| `notify_melee_impact` (dari `_entity.py`) | paket impact penuh: flash + shockwave + debris + slash fragment + **shake 4–10** + **hit-stop 0.038–0.073 s** |
| `_blade_fury_timer` 0→180 | cast Q: nova bara + `spin_mode` trail + shake 6 + hit-stop 0.045 |
| timer Q melewati kelipatan 15 | tick spin: cincin sapuan + bara radial + shake 2.4 (hit-stop hanya tiap tick ke-3 — 12 tick × 0.03 s akan membuat game patah) |
| `_heal_ward_timer` 0→360 | cast W di `_heal_ward_pos`: kelopak hijau, mote naik selama aktif |
| `_crit_buff_timer` 0→300 | cast E: suatan emas + **3 gelombang bilah** (proyektil) menyebar kerucut + shake 4 + hit-stop 0.04; bara emas mengikuti bilah selama buff |
| `_omnislash_timer` 0→90 | cast R: pilar rage + nova + shard + bolt pembuka ke target + shake 8 + hit-stop 0.07 |
| timer R melewati kelipatan 8 | tebasan omnislash di target: silang putih + pilar pendek + shake 5 + hit-stop 0.032 |
| `hp` turun | `HURT`: hit-flash 0.16 s + percikan bara |
| `alive` True→False | `DEATH`: bara padam + asap + debu + shake 6 |

## 5. Supresi ganda (tidak ada FX yang digambar 2×)

Saat `heroes.render_hero("grimjaw", ...)` pertama kali:

1. `_live_fx_pre` → `grimjaw_fx.draw_ground_layer` → `attach(hero)` →
   penanda `_gj_live_fx` + director terdaftar (sebelum cache sprite
   dibangun, jadi **tidak ada frame cache yang memuat versi dobel**);
2. `_NS_grimjaw.draw_grimjaw` membaca `_fx_live_owned(hero)` → set
   `_FX_LIVE.v`;
3. rig **melompati** smear in-canvas (`_draw_blade_swing_trail`,
   `_draw_fire_slash_arc`, `_draw_impact_flash`,
   `_draw_critical_strike_burst`) karena sudah digantikan trail 60 fps +
   ImpactFX yang jauh lebih kaya.

Kalau modul FX tidak tersedia → `owns()` False → renderer menggambar semua
fallback in-canvas seperti v2. Potret (`_portrait_hd`) tidak pernah
dipasang director (potret hanya rig).

## 6. Game feel

* **HIT-STOP 0.03–0.08 s** — semua permintaan dijepit bus
  `combat_feel.HitStop`; `Game.update` membekukan **simulasi** saja, frame
  gambar tetap jalan dan `fx_dt()` melambat 0.18× supaya partikel tetap
  terlihat bergerak pelan (bogot, bukan patah).
* **SCREEN SHAKE trauma-based** — `shake_strength` + `shake_duration`,
  meluruh bertahap, hanya dimundurkan sekali per frame; jalur resmi ke
  kamera tetap `EffectManager` (mirror via bus).
* **IMPACT FLASH** — surface premultiplied + `BLEND_RGB_ADD`, cache
  per-(radius, warna, daya) yang dikuantisasi.
* Shake menghormati preset kualitas mobile (`shake_allowed`) dan setting
  pemain (sinkron `GameSettings` → `combat_feel.sync_settings`).

## 7. Performa

* Semua glow/ring/spark/crescent **di-cache** (`_SURF_CACHE`, ≤ 384 entri,
  evict 25% tertua); partikel & pita memakai **scratch-surface pool**
  berpangkat-2 — nol alokasi `pygame.Surface` per frame pada jalur stabil.
* Anggaran partikel mengikuti `mobile.perf.Quality` (`particle_budget`
  0.0–1.0); cap per director 180, registry director ≤ 12 unit.
* Emisi kontinu (bara fury, emas crit, mote ward) rate-limited dengan
  akumulator; `tick()` aman dipanggil berkali-kali dalam satu frame.
* **Pagar anti-beku**: timer gameplay selalu berkurang tiap langkah
  simulasi, TAPI kalau hero tewas di tengah skill, `Hero.update` berhenti
  jalan dan timer membeku > 0 — emisi bara/trail langsung dihentikan
  (gerbang `alive`), dan kasus timer macet pada hero hidup (mustahil di
  gameplay sehat) dipotong setelah 15 s tanpa penurunan. Regresi:
  `test_anti_beku_*`.
* Tidak ada efek abadi: regresi `test_lapisan_hidup_meluruh_penuh`
  memastikan partikel/proyektil/impact/skill = **0** setelah pertempuran.
* Terukur di CI: 12 director bertarung penuh (2 skill + impact + trail +
  draw) median **< 16 ms per frame** (lihat `test_budget_lapisan_hidup`).

## 8. Integrasi

| File | Perubahan |
|---|---|
| `heroes/grimjaw_fx.py` | **baru** — seluruh lapisan hidup (lihat §3) |
| `heroes/__init__.py` | `grimjaw` masuk `_LIVE_FX_HEROES` + `_LIVE_FX_PATHS` → pre/pass FX dijalankan `render_hero` |
| `heroes/_bundle.py` (`_NS_grimjaw`) | `_live_module()` / `_fx_live_owned()` / `_FX_LIVE`; `draw_grimjaw` meng-attach; 4 FX in-canvas jadi fallback ter-supresi. Semua nama publik lama tetap ada |
| `_entity.py` | `notify_melee_impact` untuk `hero_type == 'grimjaw'` di jalur damage melee instan (paritas Gornak) |
| `_core.py` | HUD debug menghitung partikel `grimjaw_fx` |

## 9. Verifikasi

* `tools/test_grimjaw_v3_combat.py` — **61 regresi**: prosedural-murni,
  API publik, sinkron palet, urutan & durasi fase, prioritas/lock state,
  ayunan busur (bukan lerp), trail histori & peluruhan, cap/pool partikel,
  lifecycle proyektil + tumbukan + callback, lifecycle SkillFX Q/W/E/R,
  tick Q/R tepat di kelipatan gameplay, hit-stop 0.03–0.08, shake meluruh,
  supresi ganda + fallback, integrasi pipeline & entity, overlay debug,
  budget performa.
* `tools/test_grimjaw_masterwork.py` + `tools/test_grimjaw_swing_arah.py`
  tetap hijau (renderer v2 tidak berubah kontrak).
* `tools/test_gornak_v3_combat.py`, `tools/test_zephyr_v3.py`, cache/HD
  pipeline — tetap hijau (bus & pipeline bersama tidak digeser).
* Sheet review: `python tools/_shot_grimjaw_v3_combat.py` →
  [grimjaw_v3_combat_sheet.png](grimjaw_v3_combat_sheet.png)
  (idle / jalan / tebasan / crit / Q / W / E / R + impact).
