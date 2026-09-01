# Kaizen v3 — Combat FX & Game Feel (lapisan hidup 100% prosedural)

> Rewrite penuh sistem tempur **KAIZEN** (Wind Blade Assassin, starter
> hero). Tetap **100% prosedural**: tidak ada PNG / JPG / GIF /
> sprite-sheet / texture eksternal. Semua dibangun dari `pygame.Surface`,
> `pygame.draw`, `pygame.transform`, `Rect`, `Vector2`, dan API pygame
> sejenis yang dipakai pipeline.
>
> Dokumen ini memaparkan **sistem tempurnya** (animation controller, swing
> attack, weapon trail, projectile, skill FX, impact, particle, hit-stop,
> screen shake, debug overlay). Untuk geometri badan & disiplin pixel-art
> renderer masterwork, lihat [`KAIZEN_V2_RENDERER.md`](KAIZEN_V2_RENDERER.md).

---

## 1. Masalah yang sebenarnya

Sesudah pass renderer v3, Kaizen punya rig masterwork yang bagus — tapi
*tempurnya* belum selive Zephyr/Gornak/Grimjaw, dan penyebabnya
arsitektural:

1. **Sprite hero di-cache dan di-kuantisasi.** `heroes/__init__.py`
   (`_hero_cache_key`) memakai ulang gambar selama pose sama (fase serang
   diperbarui tiap 2 frame). Semua efek yang digambar **ke dalam canvas
   cache** ikut beku: smear iai patah-patah, sabit angin serangan dasar
   melompat-lompat mengikuti kuantisasi pose.
2. **Canvas di-smoothscale.** Skala pipeline Kaizen ≈ 0.416, jadi FX
   in-canvas ikut menyusut dan lembek — bukan chunky pixel-art di skala
   layar.
3. **Tidak ada progress serangan 60 Hz.** `_kz_attack_progress` hanya
   diperbarui saat cache sprite *miss*; tidak ada nama fase, prioritas
   state, transisi, delta-time.
4. **Tidak ada game feel sama sekali.** Basic attack Kaizen adalah damage
   **instan** melee (`_entity.py`); Q/W/E/R menerapkan damage dari
   `hero_skills` — Kaizen adalah satu-satunya starter melee yang tidak
   memicu hit-stop, shake, atau impact FX (Gornak & Grimjaw sudah punya).
5. **Tidak ada particle/projectile system hidup.** `WindSlashProjectile`
   hidup *di dalam* canvas cache, mote/daun idle bersifat deterministik
   per pose (bagus untuk cache, beku untuk umpan balik).

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph)** | `heroes/_bundle.py :: _NS_kaizen` | rig masterwork v3, palet, keyframe iai 7 pose, controller timer serangan, marker AOE E/R, dinding W / funnel R in-canvas, smear + sabit **fallback** saat modul FX tidak dimuat |
| **Lapisan hidup 1:1** | `heroes/kaizen_fx.py` (baru) | trail katana dari histori posisi tip nyata, particle system berbatas, proyektil sabit angin, impact FX, skill FX lifecycle, animation state machine cermin, hit-flash, overlay debug |
| **Bus game feel (shared)** | `heroes/combat_feel.py` | hit-stop global 0.03–0.08 s, screen shake meluruh, delta-time frame — dipakai bersama Zephyr, Gornak & Grimjaw |

Jaminan arsitektur (kontrak yang sama dengan Gornak/Grimjaw v3):

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati pada
  skala layar 1.0, tidak pernah menyusut atau beku;
* renderer tetap satu-satunya pemilik **geometri badan** — lapisan hidup
  *membaca* `_attack_pose` / `_katana_tip_local` / `_render_scale` lewat
  jembatan malas (`_renderer()`), jadi kissaki dan trail tidak mungkin
  beda frame;
* kalau `heroes.kaizen_fx` gagal diimpor, `owns()` = False dan renderer
  menggambar smear + sabit in-canvas sendiri — visual kehilangan polish,
  **tidak pernah** kehilangan efek;
* **nol perubahan gameplay/balance**: damage tetap milik `_entity.py` dan
  `hero_skills`; lapisan hidup hanya *membaca* state (`attack_timer`,
  `active_skill`, `_is_dashing`, `_wind_wall_timer`, `_ulti_timer`,
  `_q_stack`, `hp`, `alive`) dan menggambar.

## 3. Animation controller (KaizenFXDirector)

* **Progress 60 Hz dari gameplay** — `attack_timer` berkurang setiap
  langkah simulasi, jadi `_update_attack_timeline` menghitung progress
  serangan yang halus tanpa menunggu cache miss; edge `timer naik` =
  ayunan baru, `prev < 0` = director dibuat di tengah ayunan.
* **Fase timeline** ditarik dari konstanta renderer (`ATTACK_WINDUP_END
  = 0.28`, `ATTACK_IMPACT = 0.54`, `ATTACK_SWING_END = 0.72`):
  `ANTICIPATION → WINDUP → SWING → IMPACT → FOLLOW → RECOVERY`.
* **State machine berprioritas** (`ANIM_PRIORITY`): IDLE < WALK < RUN <
  CHARGE < CAST < ATTACK < SWING < SKILL < SPECIAL < HIT < HURT < DEATH;
  DEATH terkunci selama unit mati; transisi butuh prioritas ≥ atau
  `state_time > 0.05 s`.
* **Deteksi edge**: HURT dari penurunan `hp`, DEATH sekali per tumbang,
  dash Q2 dari `_is_dashing`, W/R dari timer gameplay mentah (tanpa
  menunggu `active_skill` pipeline).

## 4. Swing attack + weapon trail

* Trail dibangun dari **histori posisi bilah nyata**: tiap frame swing,
  `katana_points()` membaca pose renderer, lalu `SwingTrail.push()`
  menyimpan pasangan (pangkal, tip). OLD → CURRENT membentuk pita
  poligon translucent **4 lapis**: selubung sian gelap → badan → inti
  nyaris putih → garis ujung putih 2 px. Bahasa iai: tipis, cepat pudar
  (0.20 s), presisi — bukan api berat Grimjaw.
* Pita hanya menempati **sepertiga luar** bilah, kepala trail menempel
  di kissaki karena murni turunan pose (arc-based, bukan lerp linear —
  dikunci tes `test_ujung_bilah_mengikuti_busur_bukan_lerp`).
* **Whoosh pop** di titik IMPACT 0.54 walau serangan meleset
  (`on_blade_land`): sabit fragment + streak + shake kecil.
* Saat lapisan hidup memiliki unit (`owns()`), renderer **melewati**
  `_draw_katana_swing_trail` in-canvas (flag `_FX_LIVE`) — tidak ada
  efek yang digambar dua kali.

## 5. Projectile — sabit angin (`KaizenProjectile`)

Kontrak atribut penuh: `position, velocity, speed, damage, lifetime,
target, radius, rotation, trail, particles, active`.
Lifecycle: `SPAWN → TRAVEL (homing halus) → TRAIL pita menyempit → HIT
(radius vs radius unit) → IMPACT FX → DESTROY`.

* Badan = **sabit terisi 3-band** (`crescent_surface(filled=True)`) yang
  berputar mengikuti arah terbang + glow premultiplied + speed line +
  glint orbit deterministik. Bukan lingkaran polos.
* Serangan dasar unit `range > 80` melepas sabit di jendela swing
  0.45–0.55 — menggantikan jalur canvas (`_spawn_wind_slash` sekarang
  menghormati `_skip_renderer_projectiles`).
* Q Steel Wind melepas 2 sabit visual pendek; `damage = 0` — damage
  gameplay tetap milik `hero_skills` (dikunci tes).

## 6. Skill FX (lifecycle `cast → charge → release → area → impact → fade`)

Radius dunia sinkron gameplay: **E = 100 px**, **R = 150 px**
(`kaizen_skills.py`); Q/W radius visual.

| Skill | Bahasa lapisan hidup (badan besar tetap milik renderer) |
|---|---|
| Q Steel Wind / Dash | sabit ganda susul-menyusul + speed streak + goresan tanah; Q2 dash: garis debu + afterimage streak + hit-stop 0.045 s |
| W Wind Wall | spark pembentukan + tirai mote naik ber-swirl selama `_wind_wall_timer` + spark defleksi menyusuri dinding |
| E Sweep | debu lepas landas + cincin gale + daun/debu terangkat di tepi 100 px + tepi cincin menyala berputar |
| R Tornado | hisapan awal + daun meledak naik + debu/daun **orbit** 150 px selama `_ulti_timer` + cincin debu kaki funnel + glint puncak |

Pagar anti-beku: emisi W/R berhenti kalau timer gameplay macet > 15 s
(unit mati di tengah skill) — tidak ada partikel abadi di mayat.

## 7. Impact system + game feel

`notify_melee_impact` (dipanggil `_entity.py`, paritas Gornak/Grimjaw):
flash bintang 6 arah → shockwave **elips berarah** → spoke debris →
slash fragment 3 busur (+ silang delima saat crit) → serpihan baja
ber-gravitasi → puff debu belakang, plus:

* **hit-stop** 0.036–0.08 s (dijepit bus `combat_feel`, maks 5 langkah);
* **screen shake** 3.6–9.0 yang meluruh bertahap (trauma-based, satu
  jalur kamera lewat `EffectManager`);
* partikel dibudget `mobile.perf.Quality` (`particle_ratio`, cap keras
  160/director, pool dipakai ulang).

## 8. Integrasi (file yang berubah)

| File | Perubahan |
|---|---|
| `heroes/kaizen_fx.py` | **baru** — seluruh engine di atas |
| `heroes/__init__.py` | `kaizen` masuk `_LIVE_FX_HEROES` + `_LIVE_FX_PATHS` |
| `heroes/_bundle.py` | `_NS_kaizen`: jembatan `_live_module`/`_fx_live_owned`/`_FX_LIVE`, attach di `draw_kaizen`, skip smear saat owned, guard `_spawn_wind_slash` |
| `_entity.py` | blok `IMPACT FX KAIZEN` di jalur melee instan |
| `_core.py` | `kaizen_fx` masuk HUD debug partikel |

## 9. Verifikasi

* `tools/test_kaizen_fx_combat.py` — **49 tes**: prosedural, API, palet
  sinkron renderer, fase & prioritas, progress 60 Hz, busur vs lerp,
  trail histori, whoosh sekali per ayunan, kontrak partikel + cap +
  peluruhan, lifecycle projectile penuh + homing + cap, lifecycle skill
  + radius dunia E/R + pagar anti-beku, hit-stop 0.03–0.08 s, shake
  meluruh, supresi ganda (owns/attach/release), pipeline layer, tick
  anti-dobel, overlay debug.
* `tools/test_kaizen_masterwork.py` (9), `tools/test_swing_anim.py`,
  `tools/_audit_kaizen_v2.py` — tetap hijau (fallback canvas utuh).
* `tools/_shot_kaizen_fx.py` → `docs/kaizen_v3_combat_fx.png` (lembar
  6 momen tempur).

## 10. Debug

`heroes/kaizen_fx.DEBUG_CHARACTER = True` → hitbox, hurtbox, attack
range, kerucut hit saat SWING/IMPACT, radius AOE E/R, garis dinding W,
collision projectile, state/fase, timer skill, jumlah partikel, shake,
hit-stop, FPS.
