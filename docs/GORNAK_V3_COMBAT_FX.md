# Gornak v3 — Combat FX & Game Feel (lapisan hidup 100% prosedural)

> Rewrite penuh sistem tempur **GORNAK** (mini boss anti-mage level 1, sekaligus
> hero yang bisa di-unlock). Tetap **100% prosedural**: tidak ada PNG / JPG /
> sprite-sheet / texture eksternal. Semua dibangun dari `pygame.Surface`,
> `pygame.draw`, `pygame.transform`, `Rect`, dan `Vector2`.
>
> Dokumen ini memaparkan **sistem tempurnya** (animasi, ayunan, trail,
> proyektil, skill FX, impact, hit-stop, screen shake). Untuk geometri badan &
> disiplin pixel-art renderer, lihat [`GORNAK_V2_RENDERER.md`](GORNAK_V2_RENDERER.md).

---

## 1. Masalah yang sebenarnya

Sebelum v3, Gornak sudah punya rig yang bagus — tapi *tempurnya* terasa murah,
dan penyebabnya arsitektural, bukan estetika:

1. **Sprite hero di-cache dan di-kuantisasi.** `heroes/__init__.py`
   (`_hero_cache_key`) memakai ulang gambar selama pose-nya sama (fase
   diperbarui tiap 2 frame). Semua efek yang digambar **ke dalam canvas cache
   itu** ikut beku: trail ayunan tampak patah-patah, partikel berhenti, bolt
  skill"menempel" pada satu frame.
2. **Canvas cache di-smoothscale.** `_render_scale` lane hero ≈ 0.69 (renderer
   memakai `_fx_scale` dengan cap 2.6). FX yang digambar di ruang canvas ikut
   menyusut dan jadi lembek — persis "terlalu halus / vektor" yang dihindari.
3. **Animasi serangan bukan controller.** `_update_gnk_attack_anim` hanya
   menghitung timer untuk pose. Tidak ada nama fase, tidak ada jendela hit,
   tidak ada prioritas state, tidak ada delta time — jadi tidak ada satu pun
   tempat yang bisa ditanya "sekarang frame berapa, fase apa".
4. **Tidak ada game feel.** Hit mendarat tanpa hit-stop, tanpa shake terarah,
   tanpa impact flash. Damage instan (`take_damage` di `_entity.py`) membuat
   umpan balik harus dipicu dari tempat lain — dan tempat itu tidak ada.
5. **Satu karakter, dua jalur, dua bahasa visual.** Lane boss (`Boss.draw` →
   `draw_gornak`) dan lane hero (`render_hero`) terlihat berbeda karena yang
   pertama tidak di-cache.

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph)** | `bosses/level1.py :: _NS_gornak` | rig, palet, pose, **controller animasi**, debu langkah, E dome ring, R pillar, cast shockwave, blink after-image, **telegraph tanah Q/W/E/R**, dan seluruh **fallback** saat modul FX tidak dimuat |
| **Lapisan hidup 1:1** | `heroes/gornak_fx.py` (baru) | trail dua bilah, particle system, proyektil Mana Break, impact FX, hit-flash, slow-motion, overlay debug, ukuran & posisi di layar penuh |
| **Bus game feel (shared)** | `heroes/combat_feel.py` (baru) | hit-stop global, screen shake, delta-time frame, konsumsi freeze oleh `Game.update` |

Kenapa pembagian ini penting:

* lapisan hidup digambar **di luar** sprite cache → bergerak 60 fps sejati,
  pada skala layar 1.0, jadi trail/partikel tidak pernah menyusut atau beku;
* renderer tetap menjadi satu-satunya pemilik **geometri badan** — lapisan
  hidup tidak pernah menghitung ulang pose, dia **membaca** `_tip_local`,
  `_front_grip_local`, `_rig_shift`, `_attack_curve` lewat jembatan malas
  (`_renderer()`), sehingga bilah dan trail tidak mungkin berbeda frame;
* kalau `heroes.gornak_fx` gagal diimpor (tooling minimal, build aneh),
  `owns()` bernilai False dan renderer menggambar semuanya sendiri — visual
  kehilangan polish, **tidak pernah** kehilangan efek.

Zephyr ikut dipindahkan ke bus yang sama (`heroes/zephyr_fx.py` kini
mendelegasikan `ScreenShake`/`HitStop`/`should_freeze_frame`/`hit_stop`/
`shake`/`tick`/`reset_all` ke `combat_feel`) supaya dua karakter tidak pernah
menumpuk freeze atau meluruhkan shake dua kali dalam satu frame.

## 3. Render order (dipakai apa adanya di kedua jalur)

```
GROUND (telegraph tanah, rune)      -> renderer + gornak_fx.draw_ground_layer
GROUND FX (skill ground, back part.)-> GornakFXDirector.draw_ground
SHADOW                               -> renderer (_draw_shadow)
BACK PARTICLES                       -> ParticleSystem.draw(layer="back")
back limb -> body -> armor -> head   -> _draw_gnk_rig (satu rig berlapis)
WEAPON                               -> _draw_gnk_blade (pose-driven)
ATTACK TRAIL                         -> SwingTrail.draw
PROJECTILE                           -> ProjectileSystem.draw
FRONT PARTICLES                      -> ParticleSystem.draw(layer="front")
SKILL FX (front)                     -> SkillFX.draw_front
IMPACT FX                            -> ImpactFX.draw + hit flash
DAMAGE TEXT / UI                     -> EffectManager (milik game, tidak diubah)
DEBUG OVERLAY                        -> paling akhir
```

## 4. Controller animasi (`_NS_gornak._update_gnk_attack_anim`)

Satu-satunya sumber kebenaran state karakter. Nama lama tetap diisi supaya
`tools/_audit_gornak_v2.py`, portrait, dan jalur skill tidak perlu berubah.

| Field | Arti |
|---|---|
| `_gnk_dt`, `_gnk_frame_duration` | delta-time nyata (detik, dijepit 1/240–1/20) |
| `_gnk_attack_active`, `_gnk_attack_frame`, `_gnk_attack_progress`, `_gnk_attack_raw` | **kontrak lama** — timeline serangan |
| `_gnk_attack_phase` | `ANTICIPATION / WINDUP / SWING / IMPACT / FOLLOW / RECOVERY / NONE` |
| `_gnk_hit_active` | True hanya di jendela hit (`ATTACK_ACTIVE_WINDOW`) |
| `_gnk_state`, `_gnk_state_prev`, `_gnk_state_time` | state machine berprioritas |
| `_gnk_hurt_frames` | respons kena damage (diterjemahkan dari `hurt_flash_timer` boss) |
| `_gnk_attack_manual` | mode alat preview: pemanggil menggerakkan `_gnk_attack_progress` sendiri |

Batas fase (fraksi durasi serangan, bukan fraksi waktu pose):

```
ANTICIPATION 0.00-0.16   WINDUP 0.16-0.30   SWING 0.30-0.46
IMPACT       0.46-0.60   FOLLOW 0.60-0.80  RECOVERY 0.80-1.00
```

Batasnya sengaja jatuh **persis di patahan `_attack_curve`** (`_SWING_WIND`
0.24, `_SWING_HIT` 0.80), jadi tabel grip, sudut bilah, dan nama fase tidak
pernah berbeda satu frame. Prioritas state (`ANIM_STATES`): IDLE 0, WALK 10,
RUN 15, CHARGE 30, CAST 35, ATTACK 40, SWING 45, SKILL 50, SPECIAL 55,
HIT 60, HURT 65, DEATH 100 — state baru menang bila prioritasnya ≥ yang lama,
atau state lama sudah lewat 0.08 s; `DEATH` mengunci.

**Retune kurva.** Segmen tebasan `_attack_curve` diubah dari `t**0.55` ke
`t**1.25`. Dengan eksponen < 1, frame pertama tebasan melompat ~32 px dari
pose yang sedang ditahan — terbaca sebagai glitch. Sekarang laju naik terus
sampai tepat sebelum IMPACT HOLD (langkah terbesar turun ke ~22 px dan
diapit tetangga yang mirip), jadi ayunannya "memukul masuk" ke freeze. Sifat
yang dikunci `test_gornak_masterwork.py` (monoton, ada hold, kontras laju)
tetap lolos.

## 5. Swing trail (`SwingTrail` + `_ribbon`)

Trail dibangun dari **histori posisi ujung bilah yang sebenarnya** — dua pasang
titik (grip, tip) per frame untuk bilah depan **dan** belakang, karena
serangan Gornak harus terbaca sebagai gunting dua bilah.

Yang tidak boleh (dan dulu terjadi): polygon `[tip_lama, tip_baru, grip_baru,
grip_lama]`. Bentuk itu jadi "lembaran" raksasa begitu bilah berputar cepat
atau berbalik saat recovery — persis efek yang menutupi karakter.

Yang dilakukan sekarang:

1. histori diubah jadi `(poros grip, sudut, radius, umur)`;
2. bilah nyaris diam (Δ sudut < 0.035 rad) tidak menambah sampel;
3. arah berbalik **memutus strip** (satu tebasan = satu strip, recovery tidak
   menyapu badan);
4. sapuan total dipangkas ke `MAX_SWEEP` = 1.95 rad (≈112°) dari ekor;
5. tiap pasangan digambar sebagai **sector cincin** di sekitar poros: radius
   luar 97% panjang bilah, radius dalam 5.5%–16% lebih pendek (makin muda
   makin lebar) → sabit tipis, bukan kipas;
6. busur dipecah per `ARC_STEP` = 0.16 rad supaya tepi luarnya mulus;
7. tiga lapis: wash (`fx_mid`, 62% alpha), inti (`fx_bright`), dan **garis
   glint 1–2 px tepat di lintasan ujung** (`fx_white`);
8. alpha ∝ `rank²` dan dilemah­kan untuk langkah sudut besar
   (`spread = min(1, 0.34/|Δθ|)`) — saat frame drop, trail jadi lebih pudar,
   bukan jadi bidang penuh.

## 6. Projectile (`GornakProjectile` + `ProjectileSystem`)

Kontrak field lengkap sesuai master prompt: `position, velocity, speed,
damage, lifetime, target, radius, rotation, trail, particles, active` (plus
`state`, `kind`, `homing`, `max_lifetime`, `hit_pos`). Bergerak dengan
`pygame.Vector2` × delta time; lifecycle `TRAVEL → IMPACT → DEAD` dengan
auto-cleanup, cap `MAX_PROJECTILES` = 16, `max_lifetime` 1.9 s (tak ada
proyektil abadi).

* **Visual-only.** `damage = 0` — damage Q tetap milik `hero_skills` (instant
  `take_damage`). Bolt di sini tidak pernah menambah damage dan tidak masuk
  `game.projectiles`, supaya tidak ada double-damage dan regresi tes lama.
* **Lahir dari ujung bilah** (`blade_points` → `_tip_local`), bukan dari titik
  melayang di samping pinggang; diuji dengan jarak ≤ 10 px dari tip.
* Gambarnya bukan lingkaran: ekor meruncing → halo → outline gelap → kepala
  panah 3 lapis → fuller ungu → 2 serpihan orbit spiral → glint ujung, plus
  after-image dan percikan. Bisa dipanggil berdiri sendiri lewat
  `draw_mana_bolt(surface, px, py, angle, age, crit, radius, spin_seed)`.

## 7. Skill FX (`SkillFX`)

Lifecycle `CAST → CHARGE → RELEASE → TRAVEL/AREA → IMPACT → AFTER → FADE`
dengan `TIMELINE` per skill (detik) dan `TINT` per skill, jadi Q/W/E/R tidak
terasa sama. Yang dipakai: cincin tanah patah, retakan zigzag, mote tersedot,
arus drain, pilar, bara, barisan chevron — **bukan** tumpukan lingkaran.

Aturan kepemilikan agar tidak ada yang digambar dua kali:

| Efek | Pemilik | Alasan |
|---|---|---|
| cincin telegraph E (100 px) / R (180 px), pilar R, ground rune | **renderer** | boleh ikut ter-cache; dikunci `test_gornak_masterwork.py` |
| proc foreground Q, pita ayunan, cast shockwave | **lapisan hidup** saat `owns()` | di-canvas menyusut & beku |
| mote, retakan, shockwave hidup, impact, bolt | **lapisan hidup** | butuh 60 fps sejati di skala 1.0 |

Pusat ledakan R dibaca dari `mana_void_x/y` (pusat AOE dunia) dengan pemetaan
dunia→layar delta-camera, **bukan** dari badan; burst W di titik asal
`blink_from_x/y`. Keduanya direaksi dari state yang sudah ditulis engine
(`_watch_engine_events`), jadi `hero_skills/_bundle.py` tidak disentuh sama
sekali — tidak ada jalur baru yang bisa merusak damage/cooldown/timing skill.
`SKILL_DUR` lapisan hidup = angka yang ditulis `_bundle.py` (q40 w25 e60 r90)
dan dikunci test terhadap `SKILL_DUR` renderer.

## 8. Particle system

Satu-satunya pengelola partikel karakter. `Particle` punya `pos/vel/acc`
(dengan alias baca `position/velocity/acceleration`), `life/max_life/size`,
`rotation/rotation_speed`, `alpha`, `gravity`, `color`/`color_end`, `drag`,
`fade_pow`, `shape` (`pixel/spark/streak/shard/dust/glow/wisp/smoke`),
`additive`, `layer`.

* `ParticleSystem(cap)` — pool reusable, cap dihormati (permintaan berlebih
  dinaikkan ke `dropped`, tidak pernah menggrow tak terbatas),
  `spawn/burst/stream/update/draw/clear/count/alive`.
* bentuk digambar **langsung** (polygon ke scratch buffer), bukan
  `transform.rotate` per blit — rotasi surface cache mengalokasi surface baru
  tiap panggilan dan itu yang paling cepat menjatuhkan FPS saat ramai.
* umur selalu berujung mati; `test_gornak_v3_combat.py` menuntut 0 partikel
  dan 0 piksel di buffer 400 frame setelah pertarungan berhenti.

## 9. Impact & game feel

Satu benturan memicu paket lengkap (`ImpactFX` + burst): flash bintang 8-sisi
(pendek & tebal, bukan cross-hair vektor), shockwave elips gepeng tegak lurus
arah tebasan, cincin dalam, spoke debris, spark arah, serpihan bilah berputar
(gravity), debu jubah di lapisan back, screen shake, dan hit-stop. `kind`
memilih bahasa visual: `blade` / `mana` / `ward` / `void`.

**Bus `heroes/combat_feel.py`:**

* `HITSTOP.trigger(sek)` meng-clamp ke **0.03–0.08 s** dan membulatkan ke
  2–5 LANGKAH SIMULASI (`MAX_FRAMES` = 5) — permintaan 5 detik pun jadi 5
  frame.
* `Game.update` memanggil `should_freeze_frame()`; frame **gambar** tetap
  jalan, jadi flash & serpihan masih terlihat bergerak — `fx_dt()` mengembalikan
  `dt × 0.18` selama beku (slow-mo, bukan hang).
* `frame_dt()` adalah jam tunggal: satu dt per frame untuk semua karakter,
  dan `SHAKE.update()` dijalankan **sekali**. Ini yang mencegah shake
  meluruh dua kali cepat ketika Zephyr dan Gornak bertempur berdekatan.
* `SHAKE` tetap **frame-based** (`shake_duration -= dt`, decay 0.85 di
  `EffectManager`) — itu yang dipakai `test_screen_shake_meluruh_ke_nol`.
* `shake()` meneruskan angka yang sama ke `EffectManager.shake_screen`, satu-
  satunya tempat kamera benar-benar di-offset. Setting `screen_shake_enabled`
  ditegakkan di `EffectManager`, dan di-sync ke bus lewat
  `GameSettings.set_screen_shake` (modul karakter tidak pernah membaca
  GameSettings sendiri).
* damage number **tidak** ditiru: popper milik `_core/_entity/_render/base_boss`.

## 10. Kualitas & performa

Semua menghormati `mobile/perf.py :: Quality`: `particles`/`particle_ratio`
(anggap jumlah, bisa 0 = mati total), `glow` (halo & additive),
`screen_shake`, `cheap_alpha` (full-screen alpha blit fatal di ARM).
Surface cache (`glow/spark/ring/ellipse_ring/ground_glow`) dibatasi
`_SURF_CACHE_MAX` = 384 dengan evict terlama 25%, dan radius/alpha di-kuantisasi
(2–3 px, 16 tingkat) supaya animasi yang terus membesar tidak membuat cache
meledak.

Terukur (median-of-5, `tools/_audit_gornak_v3.py`):

| Pengukuran | Angka |
|---|---|
| `draw_gornak` idle lane boss | ~1.7 ms/frame |
| renderer + lapisan hidup saat ramai (impact per 10 frame) | ~2.9 ms/frame |
| lapisan hidup saja, idle | ~0.005 ms/frame |
| partikel hidup saat ramai | ≤ 170 (cap), `dropped` mencatat yang ditolak |
| entri surface cache setelah Q/W/E/R + impact | ~110 / 384 |

## 11. Debug mode

Dua flag, default **False**:

* `bosses.level1._NS_gornak.DEBUG_CHARACTER = True` → `_draw_gnk_debug`:
  hurtbox (lingkaran radius unit), garis+jangkauan serangan, **hitbox ayunan**
  (`_swing_hitbox`, hanya muncul saat jendela hit aktif), lingkaran tumbukan
  proyektil lapisan hidup, dan panel state/frame/fase/attack timer/hurt/skill/
  particle count/dt/FPS.
* `heroes.gornak_fx.DEBUG_CHARACTER = True` → overlay per-director di lapisan
  hidup (dipakai lane hero, yang sprite-nya di-cache).

## 12. Uji & audit

```bash
# regresi permanen (jalur baru + kontrak lama)
/home/user/.venv/bin/python -m pytest tools/test_gornak_v3_combat.py -q      # 60 checks
/home/user/.venv/bin/python tools/test_gornak_masterwork.py                  # 16 checks (v2/v3 renderer)
/home/user/.venv/bin/python -m pytest tools/test_zephyr_v3.py -q             # bus bersama (Zephyr)
/home/user/.venv/bin/python -m pytest tools/test_swing_anim.py \
    tools/test_hero_hd_render.py tools/test_hero_lighting.py \
    tools/test_renderer_projectiles_not_baked.py -q

# audit terukur + lembar preview (docs/gornak_v3_*.png)
/home/user/.venv/bin/python tools/_audit_gornak_v3.py                        # 46 checks
```

Preview yang dihasilkan: `gornak_v3_swing_strip.png`, `gornak_v3_projectile.png`,
`gornak_v3_impact.png`, `gornak_v3_skillfx.png`, `gornak_v3_feel.png`,
`gornak_v3_ingame.png`, `gornak_v3_debug.png`.

Checklist yang dikunci `test_gornak_v3_combat.py`: render (kedua lapisan
berisi, kembali kosong), asset eksternal (nol di `gornak_fx`,
`combat_feel`, **dan** `_NS_gornak`), animasi (6 fase + durasi + prioritas +
DEATH mengunci + dt), ayunan (busur, tanpa pop, trail dibatasi & meluruh),
particle (cap, alias field, gravity, semua mati), proyektil (field, lifecycle,
lahir di tip, damage 0, cap), skill (4 lifecycle habis, pusat R & burst W di
tempat benar), impact (hit-stop 2–5 frame, shake → 0, idempoten per frame,
tanpa error saat target None), integrasi (supresi ganda, fallback,
`_LIVE_FX_HEROES`, `render_hero`), debug, dan performa (< 5 ms).

## 13. Integrasi engine (semua titik, semua guarded)

| File | Perubahan |
|---|---|
| `heroes/combat_feel.py` | **baru** — bus hit-stop/shake/frame-dt |
| `heroes/gornak_fx.py` | **baru** — lapisan hidup |
| `heroes/zephyr_fx.py` | bagian game-feel didelegasikan ke bus (nama publik tidak berubah) |
| `heroes/__init__.py` | `_LIVE_FX_HEROES = {"zephyr", "gornak"}` + path resolver |
| `bosses/level1.py :: _NS_gornak` | controller animasi + fase + jendela hit + state machine, retune `_attack_curve`, lapisan hidup di lane boss, supresi ganda, `_draw_gnk_debug`, `DEBUG_CHARACTER` |
| `_entity.py` | `Hero._do_attack` jalur melee → `gornak_fx.notify_melee_impact` (difilter `hero_type`) |
| `bosses/base_boss.py` | damage melee boss → notify yang sama (difilter `boss_type`) |
| `_core.py` | gerbang hit-stop `Game.update` → `combat_feel`; HUD debug menampilkan partikel/ shake/ hit-stop bus; `set_screen_shake` menyinkronkan bus |

Aturan untuk karakter berikutnya: **jangan** menambah salinan `ScreenShake` /
`HitStop` / perhitungan dt per modul karakter; tulis modul
`heroes/<nama>_fx.py` dengan `attach/owns/tick/draw_ground_layer/draw_live_layer`
dan daftarkan di `_LIVE_FX_HEROES` + `draw_<nama>` di lane boss. Bus, urutan
lapisan, dan anggaran waktunya sudah beres dari sini.
