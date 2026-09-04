# Kelancaran Mini Boss & True Boss = Hero Unlock (paritas render/gerak/animasi)

> Keluhan yang diperbaiki:
> *"kenapa pergerakan, animasi dan lain-lain mini bos dan true bos tidak
> selancar saat mereka jadi hero unlock"*

Karakter yang sama (mis. Gornak, Morgath, Drakar, Abaddon, Varkul) terasa
kaku saat muncul sebagai mini boss / true boss, tetapi mulus saat dipakai
sebagai hero unlock. Selisihnya bukan di seni/rig — **rig-nya identik** —
melainkan di tiga jalur kode yang berbeda antara `Boss` (`bosses/base_boss.py`)
dan `Hero` (`_entity.py` + `heroes/__init__.py`).

Semua angka di bawah terukur headless
(`SDL_VIDEODRIVER=dummy`, pygame-ce 2.5.8, CPU desktop, quality *high*).

---

## 1. Diagnosa

### 1.1 Gambar: boss dirender prosedural penuh SETIAP frame

`Boss.draw()` memanggil renderer prosedural (`bosses/levelN.py`) langsung ke
layar setiap frame. Hero dengan karakter yang sama lewat **cache sprite**
(`heroes.render_hero`): pose di-kuantisasi, sprite di-cache, dan satu frame
hanya membayar satu `blit`.

| jalur | biaya draw per karakter |
|---|---|
| mini/true boss (lama) | median **2,22 ms**, maks **7,04 ms** (aeralith) — 216 tipe |
| hero unlock (cache sprite) | **0,66–0,76 ms** |

Di HP angka itu 3–6× lebih besar. Karena biaya draw boss naik-turun mengikuti
pose (skill jauh lebih mahal daripada idle), frame time berdenyut — inilah
"tidak selancar" yang paling terlihat.

### 1.2 Gerak: satu frame dibuang di setiap waypoint lane

`_move_forward()` lama:

```python
if d < 15:
    self.waypoint_index -= 1   # mundur satu waypoint
    return                     # sisa langkah DIBUANG
```

Boss berhenti total selama satu frame penuh tiap kali berpindah waypoint, lalu
mengulang proses mencari waypoint di frame berikutnya. Terukur **5–6 frame
stall per 120 frame** di setiap jalur lane (level 1–54 semua memakai pola ini).
Saat stall, perpindahan = 0 → `_detect_moving()` False → pose berkedip
WALK → IDLE → WALK. Kombinasi "berhenti sedetik + pose berkedip" terbaca
sebagai patah-patah.

Hero memakai `Hero._move_toward()` yang menghabiskan sisa langkah
(*residual budget*) sehingga tidak pernah kehilangan frame.

### 1.3 Animasi: jam boss setengah kecepatan jam hero

```python
# Boss.update (lama)      # Hero.update
self.pulse += 0.05        self.pulse += 0.1
```

Rig yang **sama persis** beranimasi setengah kecepatan saat menjadi boss.
Karena offset rig di-kuantisasi ke bilangan bulat
(`bob/sway/lift = int(sin(pulse * k) * n)`), fase yang lebih lambat berarti
satu nilai integer ditahan lebih lama lalu melompat 2 px sekaligus —
gerakannya terlihat *steppy*, bukan halus.

### 1.4 Arah hadap & kiting

* Di cabang "target sudah dalam jangkauan", `direction` **tidak pernah
  diperbarui** → boss menebas membelakangi target yang berpindah sisi.
* Arah bisa berbalik di tengah ayunan → pose swing terbalik (terlihat seperti
  animasi rusak). Hero mengunci `_attack_facing` selama `attack_timer > 0`.
* Boss ranged (kiting) memakai batas keras: `d < min_distance` → mundur,
  `d > prefer_distance` → maju, selain itu diam. Boss yang jaraknya bergetar
  di sekitar batas maju-mundur beberapa piksel tiap frame → badan gemetar dan
  pose WALK/IDLE berkedip.
* Langkah kejar tidak di-clamp ke jarak tersisa → boss cepat melompat
  *melewati* target lalu berbalik arah tiap frame (osilasi 1 px).

### 1.5 Governor FX tidak menghitung boss

`Game.draw()` memanggil `begin_fx_frame(count_busy_fx_heroes(...))` hanya
dengan daftar hero. Begitu boss ikut menyumbang partikel (lihat perbaikan di
bawah), governor akan meremehkan beban tepat saat pertarungan boss paling
ramai.

---

## 2. Perbaikan

### 2.1 `heroes/__init__.py` — pipeline cache sprite boss (`render_boss`)

Boss sekarang memakai pipeline yang **sama** dengan hero, pada skala native
1.0 (tidak ada perubahan ukuran/tampilan):

* **Kunci pose paritas hero** (`_boss_cache_key`): `timer`, `direction`,
  `boss_class` (mini vs true), `team`, `hurt_flash_timer` (kuantisasi 2 frame
  supaya flash putih tetap terlihat), `is_enraged`, `active_skill` +
  `active_skill_timer`, `ability_active`, `alive`, dan `_moving_cached`.
  Kuantisasi pose memakai konstanta hero: `BOSS_ANIM_PHASES =
  HERO_ANIM_PHASES`, `BOSS_ATK_QUANT`, `BOSS_SKILL_QUANT`.
* **Urutan lapisan identik dengan `Boss.draw` lama**:
  `GROUND FX → BADAN (sprite cache) → FX RENDERER → LIVE FX ATAS`.
  Lapisan FX hidup (`_live_fx_pre` / `_live_fx_post`) jalan **setiap frame di
  luar cache**, sama seperti hero — jadi partikel/aura tidak ikut terpanggang
  menjadi gambar beku.
* **Controller pose tetap di-tick saat cache HIT** (`_tick_boss_pose`), karena
  renderer tidak lagi dipanggil tiap frame. Tanpa ini animasi berhenti.
* **Geometri per (tipe boss, pose)**, disimpan di `_BOSS_GEOM`:
  * canvas mulai `BOSS_CANVAS_MIN_HALF = 150` dan **membesar otomatis**
    (+55 px, maks `BOSS_CANVAS_MAX_HALF = 460`) kalau konten menyentuh tepi
    canvas → tidak ada FX yang terpotong;
  * rect crop dihitung **sekali** per (tipe, pose) lalu dipakai ulang.
    `Surface.get_bounding_rect()` itu mahal — 0,30 ms pada canvas 300 px,
    1,58 ms pada 640 px — dan dulu dipanggil setiap cache miss;
  * deteksi "konten keluar rect" memakai 4 strip 2 px (**0,02 ms**) —
    `_rect_edges_inked()`; bbox penuh hanya dihitung ulang saat strip itu
    benar-benar kena tinta;
  * rect tetap ⇒ **anchor tetap** ⇒ tidak ada pergeseran 1 px antar pose
    (blit selalu mendarat persis di `(x, y)` karena semua nilai integer).
* **FX milik renderer tetap hidup**: proyektil `_drk_projs` (drakar) di-step
  dan digambar sendiri tiap frame (`_BOSS_LIVE_STEP_SPECS` /
  `_BOSS_LIVE_DRAW_SPECS`), dan beam serangan morgath (`_BEAM_PASS_HEROES`)
  digambar live di layar pada skala 1.0. Saat render ke canvas, list proyektil
  di-*park* supaya tidak terpanggang beku dan tidak di-step dua kali.
* **Anggaran memori**: `_BOSS_CACHE_MAX = 200` entri dan
  `_BOSS_CACHE_PIXEL_BUDGET = 8 juta px` (~32 MB, 4 byte/px) dengan evict LRU;
  sprite lebih besar dari `BOSS_SPRITE_MAX_SIDE = 900` px tidak di-cache.
  Cache dibersihkan saat `Game.reset()`.

### 2.2 `bosses/base_boss.py` — gerak, jam animasi, arah hadap

* `self.pulse += 0.1` — **jam boss = jam hero**.
* Deteksi gerak dihitung di `update()` dari **perpindahan nyata**
  (`math.hypot(x - _prev_x, y - _prev_y) > 0.05`), bukan dari jeda antar
  pemanggilan `draw()`; renderer tidak lagi jalan tiap frame.
* `_move_forward()` memakai *residual budget*: sisa langkah dipakai lanjut ke
  waypoint berikutnya dalam frame yang sama → **nol frame stall**.
* `_face(dx, dy)` baru: mengunci arah selama ayunan, dan punya dead-zone
  vertikal (komponen horizontal sangat kecil tidak membalik arah) supaya
  sprite tidak berkedip kiri/kanan saat menyusuri lane berbelok.
* Kunci arah ayunan: `_attack_facing` + `_attack_lock_timer`
  (`min(15, max(6, attack_cooldown // 3))` frame) — paritas hero, tetapi
  cukup pendek supaya boss tetap bisa berputar mengejar target setelahnya.
* Kejar/kiting: `step = min(speed, jarak_tersisa)` (tidak melompat melewati
  target) + **histeresis `_kite_mode`** dengan band 12 px
  (`back` / `in` / `hold`) — boss ranged tidak lagi gemetar di batas
  `min_distance` / `prefer_distance`.

### 2.3 `bosses/level1.py` — pass cahaya tetap jalan

Cache boss men-set `boss._render_scale = 1.0` sebagai penanda "jalur lane"
untuk renderer. Gornak (`_HERO_LANE`) dan Morgath (`_MOR_LANE`) memakai
penanda itu untuk **melewati pass cahayanya sendiri** (di jalur hero pass itu
diambil alih `heroes._finish_hd_sprite`). Karena jalur cache boss tidak punya
HD pass, kedua penanda sekarang dijaga:

```python
NS._HERO_LANE.v = hero_lane and not getattr(boss, "_boss_native_cache", False)
```

Tanpa penjagaan ini boss akan kehilangan rim/terminator (tampilan berubah).

### 2.4 `_core.py` — reset & governor

* `Game.reset()` memanggil `clear_boss_sprite_cache()` (paritas
  `clear_hero_sprite_cache()`).
* Governor FX menghitung boss aktif:
  `count_busy_fx_heroes(get_all_heroes() + [active_boss])`.

### 2.5 `mobile/debug.py`

Overlay debug menampilkan `cache BOSS hit %d%% (%d miss, %d entri)` supaya
kelihatan di perangkat apakah cache boss benar-benar menyala.

---

## 3. Hasil terukur

### 3.1 Biaya draw per karakter (cache warm)

| karakter | boss (baru) | hero unlock | rasio |
|---|---|---|---|
| gornak | 0,06 ms | 0,68 ms | 0,09× |
| abaddon | 0,26 ms | 0,68 ms | 0,38× |
| drakar | 0,45 ms | 0,57 ms | 0,79× |
| morgath | 0,48 ms | 0,89 ms | 0,53× |
| varkul | 0,56 ms | 0,79 ms | 0,71× |
| aeralith | 1,00 ms | 1,20 ms | 0,84× |

Rasio terburuk dari 216 boss: **1,14× hero** (sebelum perbaikan: hingga
~10× hero).

### 3.2 Adegan penuh (150 frame, `tools/_diag_scene_boss_vs_hero.py`)

Level 1 — selisih biaya frame "boss aktif" vs "karakter sama sebagai hero":

| karakter | sebelum | sesudah |
|---|---|---|
| gornak | +2,41 ms/frame (1,91×) | **+0,27 ms (1,11×)** |
| varkul | +1,79 ms (1,63×) | **−0,17 ms (0,93×)** |
| morgath | +1,11 ms (1,38×) | **−0,19 ms (0,92×)** |
| drakar | +1,04 ms (1,35×) | **−0,15 ms (0,94×)** |
| abaddon | +0,90 ms (1,29×) | **−0,03 ms (0,99×)** |

Level 30 (adegan lebih berat): nyrethzalv 1,10×, zyvareth 1,06×,
pyrhaan 0,90×, nyzrak 1,04×, kairenji 0,83×.

Loop game **nyata** (`Game.update()` + `Game.draw()`, 600 frame pertarungan
boss, `tools/_diag_boss_scene_smoke.py`, dijalankan berpasangan dalam satu
sesi):

| level | boss | `MYSTIC_BOSS_CACHE=0` | cache boss nyala |
|---|---|---|---|
| 1 | gornak | 6,45 ms/frame | **5,30 ms** (−18 %) |
| 10 | thalgryn | 4,21 ms/frame | **4,18 ms** (−1 %) |
| 30 | nyrethzalv | 7,73 ms/frame | **4,71 ms** (−39 %) |
| 54 | nyxaris | 9,07 ms/frame | **7,09 ms** (−22 %) |

Hit rate di permainan nyata 70–84 %, memori sprite 1,6–7,4 MB per
pertarungan boss, tanpa error dan tanpa pose baru yang harus digambar
langsung.

### 3.3 Gerak & animasi

| ukuran | sebelum | sesudah |
|---|---|---|
| frame stall di waypoint | 5–6 per 120 frame | **0** (432 jalur boss) |
| kecepatan `pulse` | 0,05/frame | **0,100/frame = hero** |
| arah berbalik saat swing | bisa tiap frame | **0 flip** (kunci 6 frame) |

### 3.4 Cache & memori (216 boss × 4 pose, `--all`)

* 2 870 miss / 7 295 hit → **hit rate 71,8 %** (jalur jalan/idle: 89 %).
* canvas membesar otomatis 147× (tidak ada FX terpotong).
* 164 entri, median sprite 219×219, terbesar 434×249, **30,4 MB** saat
  seluruh 216 boss di-cycle bergantian (satu level nyata hanya 1–3 boss →
  beberapa MB).

### 3.5 Regresi visual: tidak ada

* **12 boss pixel-identical** (rata-rata selisih piksel **0,000**) antara
  jalur lama (`MYSTIC_BOSS_CACHE=0`) dan jalur baru pada pose yang sama.
  Bukti gambarnya ditulis `tools/_diag_boss_cache_visual.py` ke
  `docs/_boss_cache_<tipe>.png` (kiri: jalur lama, kanan: jalur baru);
  file PNG-nya artefak generatif sehingga tidak ikut di-commit.
* **Anchor 0 px** selisih bbox untuk semua tipe yang dibandingkan.
* **0 sprite terpotong** dari 164 sprite cache (tinta tidak menyentuh tepi
  sprite — diperiksa otomatis di test).
* **0 exception** pada 216 tipe × 4 pose × 12 frame.

### 3.6 Pengecualian yang disengaja: 9 pose skill

Pose **skill** dari 9 boss FX-nya melebar melebihi batas sprite
(> 900 px sisi / canvas > 460 px setengah), jadi pose itu **tetap digambar
langsung ke layar** seperti sebelumnya — lebih baik membayar 2–4 ms selama
beberapa detik skill daripada memotong FX:

`nyrethzalv` 4,34 ms · `zyvareth` 4,05 · `zarethyr` 3,39 · `pyrhaan` 3,24 ·
`xarnthuul` 2,93 · `morkhelvis` 2,85 · `zorothrax` 2,79 · `aelyrion` 2,23 ·
`selunara` 2,16 ms.

Perbaikan gerak/animasi (§2.2) tetap berlaku penuh untuk kesembilan boss ini;
di level 30 rasio frame-nya tetap 0,90–1,10× hero (§3.2).

---

## 4. Katup pengaman

| mekanisme | perilaku |
|---|---|
| `MYSTIC_BOSS_CACHE=0` | mematikan cache sprite boss (untuk membandingkan) |
| `BOSS_CACHE_ENABLED` | saklar runtime yang sama |
| renderer gagal di canvas | `render_boss()` return `False` → `Boss.draw()` menggambar langsung (jalur lama) |
| konten menyentuh tepi canvas | canvas membesar (+55 px) sampai `BOSS_CANVAS_MAX_HALF` |
| masih kebesaran setelah mentok | pose didaftarkan ke `_BOSS_UNSAFE` → digambar langsung, tidak di-cache |
| sprite > `BOSS_SPRITE_MAX_SIDE` | tidak di-cache (blit-nya tidak lebih murah daripada render) |
| memori | LRU + anggaran piksel; `clear_boss_sprite_cache()` saat ganti level |

Prinsipnya: **kalau ragu, gambar langsung** — cache tidak boleh mengubah
tampilan atau memotong FX.

---

## 5. Cara menguji

```bash
# 14 pemeriksaan regresi (gerak, jam animasi, arah, cache, biaya draw,
# render aman semua tipe, FX tidak terpotong, anchor)
python3 tools/test_boss_hero_smooth_parity.py          # sampel 30 boss
python3 tools/test_boss_hero_smooth_parity.py --all    # semua 216 boss

# biaya frame adegan penuh: boss aktif vs karakter sama sebagai hero
python3 tools/_diag_scene_boss_vs_hero.py 1 gornak morgath drakar

# smoke test loop game NYATA (update+draw, governor FX, wave/minion/tower)
python3 tools/_diag_boss_scene_smoke.py 1:gornak 30:nyrethzalv
MYSTIC_BOSS_CACHE=0 python3 tools/_diag_boss_scene_smoke.py   # pembanding

# survei kliping canvas semua boss + PNG banding lama-vs-baru
python3 tools/_diag_boss_cache_visual.py gornak morgath drakar

# diagnostik pendukung
python3 tools/_diag_boss_hero_smooth2.py gornak varkul abaddon
python3 tools/_diag_boss_draw_cost.py
python3 tools/_diag_boss_bbox.py
```

Test lain yang tetap hijau setelah perubahan ini: `test_hero_cache`,
`test_hero_pose_cache` (termasuk `test_jalur_mini_boss_tetap_jalan`),
`test_hero_hd_render`, `test_hero_lighting`, `test_boss_no_white_cover`,
`test_grimjaw_swing_arah`, `test_fx_stability`,
`test_basic_attack_no_impact_fx`, `test_gornak_v3_combat`,
`test_grimjaw_v3_combat`, `test_gorath_v3_combat`, `test_ignis_v3_combat`,
`test_drakar_max`, `test_gale_morgath`, `test_abaddon_masterwork`,
`test_codebase_heroes`.

> Catatan: `tools/test_gorath_masterwork.py` dan
> `tools/test_khalros_masterwork.py` gagal pada budget "skill r ≤ 3,5 ms"
> **juga di commit dasar** `ec93817` (4,18 / 4,38 ms) — kegagalan lama yang
> tidak berhubungan dengan perubahan ini (setelah perubahan: 3,59 / 4,33 ms).
