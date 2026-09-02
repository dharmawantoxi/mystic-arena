# Ignis Drachorn v3 — Renderer + Combat FX & Game Feel (100% prosedural)

> Rewrite penuh sistem **visual dan rasa tempur** untuk **IGNIS DRACHORN —
> The Molten Sovereign** (true boss level 4, `bosses/level4.py`). Tetap
> **100% prosedural**: tidak ada PNG / JPG / GIF / sprite-sheet / aset
> eksternal dan tidak ada `pygame.image.load`. Semua bentuk dibangun dari
> `pygame.Surface`, `pygame.draw`, `pygame.transform`, `Rect`, `Vector2`.
>
> Dokumen ini memaparkan renderer (rig, palet, pose, controller animasi)
> **dan** sistem tempurnya (ayunan, trail, proyektil, skill FX, impact,
> hit-stop, screen shake, debug). Polanya sengaja mengikuti
> [`GORNAK_V3_COMBAT_FX.md`](GORNAK_V3_COMBAT_FX.md) dan
> [`ZHAROK_V2_RENDERER.md`](ZHAROK_V2_RENDERER.md) supaya karakter ini tidak
> jadi arsitektur ke-15 di repo yang sama.

---

## 1. Masalah yang sebenarnya

Versi lama Ignis Drachorn punya penyakit yang sama dengan Gornak pra-v3,
plus beberapa yang khas dia sendiri:

1. **Semua efek hidup di dalam canvas badan.** Renderer boss menggambar
   badan ke satu surface, lalu (di lane hero) surface itu di-*cache* dan
   di-`smoothscale`. Trail pedang, bara, proyektil, dan FX skill yang
   digambar ke canvas yang sama ikut **beku** dan ikut **menyusut**.
2. **Tidak ada controller animasi.** Pose ditentukan `if` bertingkat dari
   `timer`/`active_skill`. Tidak ada nama state, tidak ada prioritas, tidak
   ada fase serangan, tidak ada delta time — jadi tidak ada satu tempat pun
   yang bisa ditanya *"sekarang frame berapa, fase apa, boleh kena tidak"*.
3. **Ayunan pedang tidak punya ARK.** Sudut bilah dihitung ad-hoc di dua
   tempat berbeda (badan & trail), jadi trail sering tidak menempel di
   bilah dan sabetan kehilangan bobot.
4. **Tidak ada game feel.** Damage instan, tanpa hit-stop, tanpa shake
   terarah, tanpa impact flash. Pukulan 320 damage terasa sama dengan 12.
5. **Blend additif yang salah.** Semua glow/aura di-blit dengan
   `BLEND_RGB_ADD` — yang **mengabaikan kanal alpha sepenuhnya**. Gradien
   yang sudah dibuat rapi muncul sebagai **cakram warna penuh bertepi
   keras** (lihat §11), sehingga karakter tertelan stiker oranye.

## 2. Pemecahan: pisahkan badan dari efek

| Lapisan | File | Memiliki |
|---|---|---|
| **Renderer (badan + telegraph + fallback)** | `bosses/level4.py :: _NS_ignis_drachorn` | rig, palet, pose, **controller animasi**, ARK pedang, bayangan, aura panas, bara tanah, elder dragon form (R), **seluruh fallback canvas** saat modul FX absen |
| **Lapisan hidup 1:1** | `heroes/ignis_drachorn_fx.py` (baru, ±3.1k baris) | swing trail, particle system, proyektil Fire Orb & Meteor, impact FX, skill FX q/w/e/r, afterimage, overlay debug — semuanya di **ruang layar**, skala 1.0 |
| **Bus game feel (dipakai bersama)** | `heroes/combat_feel.py` (sudah ada) | hit-stop global, screen shake, delta-time frame |

Kenapa pembagian ini penting:

* lapisan hidup digambar **di luar** sprite cache → 60 fps sejati, tidak
  pernah beku dan tidak pernah ikut menyusut;
* renderer tetap **satu-satunya pemilik geometri badan**. Lapisan hidup
  tidak menghitung ulang pose — ia **membaca** `sword_geometry()`,
  `_sword_arc()`, `_ign_state`, `_ign_attack_progress` lewat jembatan malas
  `_renderer()`. Bilah dan trail tidak mungkin berbeda satu frame pun;
* kalau `heroes.ignis_drachorn_fx` gagal diimpor, `owns()` bernilai False
  dan renderer menggambar semuanya sendiri — visual kehilangan polish,
  **tidak pernah** kehilangan efek.

## 3. Render order (dipakai apa adanya di kedua jalur)

```
1  GROUND telegraph skill            SkillFX.draw_ground()      (FX)
2  GROUND FX + partikel belakang     ParticleSystem "back"      (FX)
3  SHADOW                            _draw_shadow               (renderer)
4  AURA panas + bara tanah           _draw_fire_aura            (renderer)
5  RIG: kaki belakang -> badan -> armor -> kepala
                                     _draw_ignis_body           (renderer)
6  WEAPON (greatsword magma)         _draw_flame_sword          (renderer)
7  ATTACK TRAIL                      SwingTrail                 (FX)
8  PROJECTILE                        ProjectileSystem           (FX)
9  partikel depan                    ParticleSystem "front"     (FX)
10 SKILL FX depan                    SkillFX.draw_front()       (FX)
11 IMPACT FX + hit flash             ImpactFX                   (FX)
12 DEBUG OVERLAY                     draw_debug_overlay         (FX)
```

Pembagian layer di dalam rig sendiri (`_draw_ignis_body_raw`):
`sayap belakang → ekor → jubah → kaki → torso → rok/tasset → pauldron →
kepala → lengan belakang → pedang → lengan depan → perisai → highlight`.

Badan selalu lewat **komposit yang sama**: buffer tetap 220×230 →
`get_bounding_rect` → outline siluet hitam 1 px di 4 arah → `lighting.
apply_to_rig(rim_add=(52,24,14))` → blit. Elder Dragon Form (R) memakai
jalur komposit yang sama, jadi siluetnya sama kokohnya dengan pose normal.

## 4. Controller animasi (`_NS_ignis_drachorn._update_ignis_anim`)

Satu-satunya sumber kebenaran state/fase/timing. Overlay debug, lapisan
hidup, dan alat uji semuanya membacanya dari sini.

* **Delta time nyata** dari `pygame.time.get_ticks()`, di-clamp ke
  `(0, 0.05]` → `boss._ign_dt`.
* **State + prioritas** (`ANIM_STATES`), angka besar menang:

  | state | prio | | state | prio |
  |---|---|---|---|---|
  | IDLE | 0 | | SKILL | 50 |
  | WALK | 10 | | SPECIAL | 55 |
  | RUN | 15 | | HIT | 60 |
  | CHARGE | 30 | | HURT | 65 |
  | CAST | 35 | | DEATH | 100 |
  | ATTACK | 40 / SWING 45 | | | |

* **Timeline serangan.** `timer` engine menghitung **mundur**; serangan baru
  dideteksi saat timer melonjak naik ke ≈`attack_cooldown`. Panjang animasi
  `max(10, min(cooldown-1, 34))` frame supaya ayunan tetap berbobot walau
  cooldown pendek.
* **Fase** (fraksi progres 0..1), lengkap dengan anticipation/active/recovery:

  | fase | rentang | isi |
  |---|---|---|
  | ANTICIPATION | 0.00–0.12 | badan mundur, pedang turun |
  | WINDUP | 0.12–0.30 | pedang terangkat ke belakang kepala |
  | SWING | 0.30–0.50 | bilah menyapu cepat ke depan |
  | IMPACT | 0.50–0.62 | tahan sesaat + lunge ≈ +10 px |
  | FOLLOW | 0.62–0.82 | sisa momentum |
  | RECOVERY | 0.82–1.00 | kembali ke posisi istirahat |

  `ATTACK_ACTIVE_WINDOW = (0.36, 0.62)`, `ATTACK_IMPACT_FRAME = 0.52`.
* Output: `_ign_dt`, `_ign_state`, `_ign_state_prev`, `_ign_state_time`,
  `_ign_state_priority`, `_ign_attack_progress`, `_ign_attack_phase`,
  `_ign_hit_window`.

## 5. Melee swing system — ARK greatsword

`sword_geometry(facing, action, phase, ap) -> ((gx,gy), (tx,ty), theta)`
adalah **satu-satunya** sumber posisi bilah, dipakai renderer (menggambar
pedang) **dan** lapisan hidup (trail + titik lahir proyektil).

* `theta` diukur dari sumbu ATAS, positif ke arah `facing`;
  `tip = grip + (f·sinθ·L, −cosθ·L)`, `BLADE_LEN = 56`,
  `GRIP_LOCAL = (16, −6)`.
* `SWORD_ARC` — tabel **bersambung** (nilai akhir segmen = nilai awal
  segmen berikutnya), jadi senjata tidak pernah teleport:

  | t0–t1 | θ | easing |
  |---|---|---|
  | 0.00–0.12 | 2.42 → 2.00 | out |
  | 0.12–0.30 | 2.00 → −1.30 | in-out |
  | 0.30–0.50 | −1.30 → 1.80 | out-cubic |
  | 0.50–0.62 | 1.80 → 2.12 | hold |
  | 0.62–0.82 | 2.12 → 2.72 | in-out |
  | 0.82–1.00 | 2.72 → 2.42 | in-out |

  Uji regresi mengunci: langkah sudut per 0.5 % progres < 0.30 rad, dan
  θ(0) == θ(1) (loop mulus). Idle bersandar di 2.42 (ujung menghadap
  bawah-depan), walk 2.30 dengan lift 0.08.
* **Hitbox**: garis grip→tip + lingkaran radius 16 px di ujung, aktif hanya
  selama `ATTACK_ACTIVE_WINDOW` (terlihat di overlay debug).
* **Slash trail** (`SwingTrail`): histori 9 sample `(grip, tip)` dengan umur
  0.13 s. Setiap **pasangan** sample jadi **quad-nya sendiri** dengan alpha
  sendiri (baru = terang, lama = nyaris hilang) — itu yang membuat sabetan
  terbaca sebagai *gerak*, bukan sebagai pelat oranye. Pita hanya menutup
  ±35 % terluar bilah supaya tidak menelan karakter.
* **Impact**: pada `ATTACK_IMPACT_FRAME` director memicu `_melee_impact()`
  → flash bintang + 2 busur sabit + shockwave + 14 bara + 6 serpihan
  obsidian + debu tanah + `shake(7.0, 0.18)` + `hit_stop(0.055)`.
  Dedup per sabetan (`swing_done`) supaya AI boleh ikut memanggil
  `notify_melee_impact()` tanpa efek dobel.

## 6. Projectile system (modular)

`BaseProjectile` menetapkan kontrak, dua turunan mengisinya:

| | `FireOrbProjectile` | `MeteorProjectile` |
|---|---|---|
| dipakai | serangan jarak jauh + Q | ultimate R (5 buah) |
| kecepatan | 620 px/s | 780 px/s |
| bentuk | cangkang api 12-sisi lonjong searah gerak + inti putih + cincin orbit | kepala batu 8-sisi + urat magma + ekor api panjang |
| trail | pita meruncing dari histori posisi | glow bertumpuk dari histori |
| tabrakan | radius vs target (`Vector2`) atau titik tujuan | menyentuh tanah |
| impact | ledakan bara + asap + `shake(4.5)` + `hit_stop(0.035)` | kawah + retakan lava + debris + `shake(9)` + `hit_stop(0.05)` |

Atribut wajib lengkap dan semuanya dipakai: `position`, `velocity`,
`speed`, `damage`, `lifetime`, `target`, `radius`, `rotation`, `trail`,
`particles`, `active` — dengan `pygame.Vector2` dan delta-time.

Lifecycle: `spawn → travel → update_trail → emit → check_collision →
destroy → on_impact`. `ProjectileSystem` melakukan cull tiap frame dan
menegakkan `MAX_PROJECTILES = 20` (yang tertua dibuang, bukan ditolak).

## 7. Skill FX (`SkillFX`) — lifecycle penuh

Enam fase, semua diuji benar-benar terjadi:

```
CAST 0.00–0.16 → CHARGE 0.16–0.34 → RELEASE 0.34–0.46
     → AREA 0.46–0.74 → IMPACT 0.74–0.86 → AFTER 0.86–1.00
```

| skill | ground layer | front layer | bentuk khas |
|---|---|---|---|
| **Q Dragon Breath** | kerucut telegraph putus-putus + chevron maju, lalu jejak bakar | kerucut 5 lapis bergerigi (gelap→putih panas) + gumpalan api di ujung + bara terbang | *cone*, bukan lingkaran |
| **W Dragon Tail** | cincin telegraph elips + cincin putus-putus, lalu shockwave elips ganda + 7 retakan tanah | pita **ekor naga** menyapu 2.9 rad, bersisik, dengan gada api di ujung | *sweep arc* |
| **E Dragon Blood** | genangan darah + cincin rune segi-lima berputar + goresan radial | 5 pilar api mengorbit badan + aura + **kepala naga spektral** | *ritual ring + pilar* |
| **R Elder Dragon Form** | danau lava + shockwave elips ganda + 10 retakan lava besar | kolom cahaya meruncing (bukan kotak), 3 cincin raungan, **sayap api spektral**, 5 meteor | *erupsi + hujan meteor* |

Semua radius FX **sama persis** dengan radius damage AI
(`WORLD_RADIUS = {q:250, w:130, e:110, r:220}`) dan durasi pose sama
dengan `SKILL_DUR = {q:45, w:40, e:60, r:90}` di `base_boss.py`. Dikunci
oleh tes.

Selain bentuk-bentuk di atas, kotak peralatan efeknya berisi: `glow`,
`spark_star`, `chevron`, `flame_poly`, asap, debu, `shockwave`, slash,
energy ring, `shard_poly` (debris), ground pool, `Afterimage`, dan camera
shake — sesuai daftar variasi yang diminta, dan **tidak** semuanya
lingkaran.

## 8. Particle system

`Particle` menyimpan `x, y, vx, vy, ax, ay, life, max_life, size,
rotation, rotation_speed, alpha, gravity, color, shape, drag, additive,
layer, scatter`. `shape` ∈ `ember | flame | streak | smoke | debris |
dust | spark | ring | scale`.

`ParticleSystem` adalah **pool dengan kursor melingkar** berukuran tetap
(`MAX_PARTICLES = 210`): tidak pernah alokasi saat runtime, tidak pernah
tumbuh, partikel tertua otomatis dipakai ulang. `burst()` menyediakan
ledakan terarah (sudut, sebaran, kecepatan, umur, ukuran, warna, gravitasi,
drag, rotasi) dalam satu panggilan.

Bara ambient punya kuota per detik (9/s idle, 14/s walk, 16/s E, 26/s R)
dan **berhenti otomatis** kalau unit sudah 0.5 s tidak digambar — jadi
boss di luar layar tidak membocorkan partikel.

## 9. Impact & game feel

`ImpactFX(kind)` — `melee` (sabit + retakan), `orb` (cangkang api
bergerigi), `meteor` (kawah + retakan lava + genangan), `skill` (umum).
Setiap dampak: flash bintang 0.09 s → shockwave memuai-menipis →
bentuk khas per jenis → fade. Umur 0.26–0.52 s, tidak ada yang abadi.

Hit-stop selalu di rentang yang diminta **0.03–0.08 s**
(`_feel_hit_stop()` melakukan clamp keras):

| kejadian | hit-stop | shake |
|---|---|---|
| melee mendarat | 0.055 (crit 0.075) | 7.0 × power, 0.18 s |
| fire orb kena | 0.035 | 4.5, 0.14 s |
| meteor mendarat | 0.05 | 9.0, 0.22 s |
| Q / W / E / R | 0.035 / 0.05 / 0.03 / 0.07 | 6 / 9 / 4 / 14–15 |
| kematian | 0.08 | 16.0, 0.5 s |

Semua lewat `heroes/combat_feel.py`, jadi Ignis tidak pernah bertengkar
dengan karakter lain soal siapa yang memegang shake.

## 10. Elder Dragon Form (R)

Bentuk R bukan lagi gumpalan merah. Rig naga purba digambar dengan urutan
`sayap jauh → ekor berduri → kaki belakang → badan → sisik → sayap dekat →
leher berduri → kepala → cakar depan`, lalu melewati **komposit yang sama**
dengan badan normal (outline siluet + rim light `(70,30,16)`).

Sayap memakai 4 jari yang mengipas dari pergelangan dengan membran
**berlekuk** di antara ujung jari; sayap seberang digambar 0.74× lebih
kecil dan lebih gelap sebelum badan, sayap dekat penuh setelah badan —
itu yang memberi kedalaman alih-alih dua bentuk kembar. Dada punya inti
magma berdenyut (`_jagged_crack` + poligon `magma_bright`/`magma_white`).

## 11. Catatan teknis: `BLEND_RGB_ADD` mengabaikan alpha

Bug paling merusak di versi lama, dan layak didokumentasikan karena mudah
terulang di karakter lain:

```python
# SALAH — alpha per-piksel diabaikan, gradien jadi cakram warna penuh
surface.blit(glow, pos, special_flags=pygame.BLEND_RGB_ADD)

# BENAR — premultiply dulu: blit normal ke atas hitam, baru ditambahkan
tmp = _opaque(w, h)          # surface hitam buram dari pool
tmp.blit(glow, (0, 0))       # RGB ikut dikalikan alpha-nya
surface.blit(tmp, pos, special_flags=pygame.BLEND_RGB_ADD)
```

Helper `blit_add()` (FX) dan `_NS_ignis_drachorn._blit_decal(add=True)`
(renderer) sekarang melakukan ini. Efeknya besar: aura, glow, trail,
kerucut napas api, dan kolom ultimate berubah dari stiker bertepi keras
menjadi cahaya yang benar-benar meluruh ke gelap.

Selain itu, decal radial dibangun dari **annulus** (cincin ber-`width`),
bukan tumpukan lingkaran penuh — tumpukan lingkaran membuat alpha
terakumulasi di tengah dan menghasilkan cakram keras.

## 12. Kualitas & performa

* **Cache surface**: `glow_surface`, `ring_surface`, `ellipse_ring_surface`,
  `ground_pool_surface`, `ember_surface` semuanya ter-cache per
  (radius, warna, parameter); cache dibatasi 220 entri dan dibersihkan
  `reset_all()`. Tes mengunci `cache_size() <= 240`.
* **Scratch pool**: buffer SRCALPHA dan buffer hitam (premultiply) diambil
  dari pool, bukan dialokasikan tiap frame.
* **Cap keras**: 210 partikel, 20 proyektil, 5 skill, 9 impact, 6
  afterimage, 12 director per proses.
* **Anggaran frame**: tes mengukur badan + FX dengan **skill R aktif**
  (5 meteor, partikel penuh) → **≈3.3 ms/frame**, jauh di bawah 16 ms.
* **Tidak ada efek berumur tak terbatas**: setiap partikel, proyektil,
  skill, impact, dan afterimage punya `life`; tes memajukan 1500 frame dan
  memastikan semuanya habis.

## 13. Debug mode

`heroes/ignis_drachorn_fx.DEBUG_CHARACTER = True` (default `False`;
`_NS_ignis_drachorn.DEBUG_CHARACTER` untuk sisi renderer) menampilkan:

* **hitbox** senjata (garis grip→tip + lingkaran ujung, merah saat jendela
  hit aktif),
* **hurtbox** badan (kotak hijau),
* **attack range** (elips tanah biru) dan **radius skill aktif** (elips
  merah),
* **tabrakan proyektil** (lingkaran radius + garis ke tujuan),
* teks: state animasi + state sebelumnya + prioritas, nomor frame, waktu
  state, `dt`, progres & fase serangan + penanda `<HIT>`, timer serangan &
  cooldown, skill aktif + timernya, jumlah partikel/proyektil/impact, FPS,
  ukuran cache, jumlah sabetan.

## 14. Uji

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    python3 tools/test_ignis_v3_combat.py
```

22 kelompok uji, semuanya hijau: API modul & backward compatibility
renderer, kontrak palet 9 kunci, controller animasi (state/prioritas/fase/
hit window/dt), kontinuitas ARK + satu sumber geometri renderer↔FX, swing
trail, lifecycle fire orb & meteor, cap proyektil, lifecycle 6 fase skill +
dedup cast/impact, sinkronisasi radius & durasi dengan AI, renderer + FX di
boss lane, semua pose (idle/walk/hurt/attack/ranged/q/w/e/r/death), mirror
facing + potret HD statis, hero-lane pipeline, boss lain di bundle level4
tidak rusak, overlay debug, integrasi `base_boss`, registrasi
`heroes/__init__`, prosedural murni, batas FX, batas cache, anggaran frame.

## 15. Integrasi engine (semua titik, semua ter-guard)

| Titik | File | Isi |
|---|---|---|
| dispatcher renderer | `bosses/_boss_index.py:58` | `ignis_drachorn → level4.draw_ignis_drachorn` (tidak berubah) |
| gate lapisan hidup | `bosses/level4.py :: _live_fx` | import malas, `owns()`, set `_ign_suppress_canvas_fx`, semua fallback canvas dijaga `if not owned` |
| ground + live layer | `bosses/level4.py :: draw_ignis` | `draw_ground_layer()` sebelum badan, `draw_live_layer()` paling akhir |
| spawn proyektil | `bosses/level4.py` | `notify_projectile_cast(boss, x, y)` pada frame cast |
| HUD partikel | `bosses/level4.py` | `total_particles()` |
| melee / bolt impact | `bosses/base_boss.py` (serangan dasar) | `notify_melee_impact()` / `notify_projectile_impact()`, difilter `boss_type == 'ignis_drachorn'` |
| skill Q/W/E/R | `bosses/base_boss.py :: _cast_q/w/e/r_*` | `notify_skill_cast()` + `notify_skill_impact()` pada tick yang sama |
| lane hero | `heroes/__init__.py` | `ignis_drachorn` didaftarkan di `_LIVE_FX_HEROES` + `_LIVE_FX_PATHS` |

Semua pemanggilan dibungkus `try/except` dan difilter per `boss_type`,
jadi karakter lain tidak pernah menarik modul FX yang bukan miliknya, dan
build tanpa modul FX tetap berjalan (memakai fallback canvas).

## 16. Ringkasan perubahan per berkas

| Berkas | Status | Perubahan |
|---|---|---|
| `heroes/ignis_drachorn_fx.py` | **baru** | seluruh lapisan hidup: palette, jembatan renderer, helper gambar + cache, `Particle`, `ParticleSystem`, `SwingTrail`, `ImpactFX`, `Afterimage`, `BaseProjectile`, `FireOrbProjectile`, `MeteorProjectile`, `ProjectileSystem`, `SkillFX`, `IgnisFXDirector`, registri + `tick/reset_all/total_particles/stats`, `draw_ground_layer` / `draw_live_layer`, tujuh `notify_*`, overlay debug |
| `bosses/level4.py` | **rewrite `_NS_ignis_drachorn`** | rig Molten Sovereign baru (helm poligon bertanduk, pauldron kubah, jubah tersapu angin, ekor pendek, perisai kepala naga, greatsword magma), controller animasi, `sword_geometry` + `SWORD_ARC`, komposit outline+rim, `_ground_pool_decal`, `_blit_decal` premultiply, Elder Dragon Form + `_draw_elder_wing` baru, gate `_live_fx`, penyimpanan `_last_rig` untuk afterimage, seluruh fallback canvas |
| `bosses/base_boss.py` | modifikasi | hook FX pada `_cast_q/w/e/r_*` (cast + impact) dan pada serangan dasar (melee / bolt), semua difilter `boss_type` + `try/except` |
| `heroes/__init__.py` | modifikasi | `ignis_drachorn` masuk `_LIVE_FX_HEROES` dan `_LIVE_FX_PATHS` |
| `tools/test_ignis_v3_combat.py` | **baru** | 22 kelompok uji regresi (lihat §14) |
| `docs/IGNIS_DRACHORN_V3_COMBAT_FX.md` | **baru** | dokumen ini |

Tidak ada variabel/kelas/fungsi lama yang diganti nama, tidak ada API lama
yang hilang (`PALETTE`, `FireProjectile`, `draw_ignis`, `draw_boss`,
`_update_attack_anim`, `_manage_projectiles`, `_spawn_fire_projectile`,
dan seluruh `_draw_*` lama tetap ada dan dipanggil ulang oleh jalur baru),
dan tidak ada boss lain yang tersentuh.
