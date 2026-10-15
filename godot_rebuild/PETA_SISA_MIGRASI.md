# Peta Sisa Migrasi — status singkat

Dokumen ini hanya mencatat **slice portrait Hero Shop** yang dikerjakan pada
branch `arena/2aa50b3c-mystic-arena`. Bukan audit sistem lain.

## Catatan penting tentang handoff sebelumnya

Sesi ini **tidak mewarisi worktree dirty** dari handoff sebelumnya:

- Branch `arena/2aa50b3c-mystic-arena` dibuat baru dari `cd77e4d` (merge PR #325).
- `git status` bersih, `git stash list` kosong, tidak ada commit di branch ini.
- `godot_rebuild/PETA_SISA_MIGRASI.md` belum pernah ada di repo.
- Tidak ada satu pun kode portrait di `godot_rebuild/` sebelum sesi ini.

Karena itu slice ini **dibangun dari nol**, bukan diselesaikan dari WIP lama.
Kalau WIP aslinya masih ada di sandbox/branch lain, dokumen ini yang perlu
digabung sebelum lanjut.

## Yang sudah selesai (slice Kaizen/Thorne)

| Berkas | Peran |
|---|---|
| `scripts/ui/hero_portrait.gd` | Kanvas prosedural. `kaizen` dan `thorne` punya canvas sendiri; id lain jatuh ke bust generik deterministik dari hash id. |
| `scripts/ui/hero_shop_card.gd` | Shared Hero Shop card. Tetap `extends Button` agar scene suite tetap menemukan baris lewat `tooltip_text` dan tetap membaca `.text` / `.disabled`. |
| `scripts/ui/hero_shop_panel.gd` | Panel in-match memakai shared card (lebar 485). |
| `scripts/ui/meta_hero_shop_panel.gd` | Panel main-menu memakai shared card (lebar 525). |
| `tests/hero_shop_portrait_checks.gd` | Suite native: dispatch, fallback deterministik, kontrak card, wiring panel. |
| `tests/run_all.gd` | Suite portrait terdaftar. |

Kontrak yang sengaja dijaga:

- `hero_requested.emit(hero_type)` tetap di panel in-match.
- `unlock_requested.emit(hero_type)` tetap di panel permanent, dan panel tetap
  request-only (tanpa `save_state`).
- Portrait punya `mouse_filter = MOUSE_FILTER_IGNORE` supaya tidak memakan klik baris.
- Teks card digeser lewat `content_margin_left` stylebox, bukan child label.

## Validasi yang sudah dijalankan

```
gdparse   $(find godot_rebuild -name '*.gd')        -> OK
gdlint    $(find godot_rebuild -name '*.gd')        -> Success: no problems found
gdformat --check $(find godot_rebuild -name '*.gd') -> 248 files unchanged
git diff --check                                    -> OK
python3 godot_rebuild/tests/validate_project.py     -> PASS: 12333 static checks
```

`gdtoolkit 4.5.0` dipasang di sandbox untuk menjalankan batch di atas.

## Regresi teks terpotong — ditemukan lalu diperbaiki

Menaruh portrait di kiri card memakan lebar teks. Diukur dengan font asli
proyek (Barlow-SemiBold 20) terhadap seluruh 222 hero di roster:

| Panel | Sebelum portrait ada | Portrait 72 (pertama) | Setelah perbaikan |
|---|---:|---:|---:|
| Match (lebar 485) | 3/18 terpotong | 17/18 | **0/18** |
| Meta (lebar 525) | 314/666 terpotong | 600/666 | **5/666** |

Perbaikan yang dipakai:

- `PORTRAIT_SIZE` 72 → 64, `PORTRAIT_INSET` 12 → 10, margin kanan 18 → 16
  (ruang yang direserve turun 96px → 84px).
- `autowrap_mode = TextServer.AUTOWRAP_WORD_SMART`: baris panjang wrap, bukan
  dipotong.
- `CARD_HEIGHT` 92 → 112, cukup untuk 3 baris ter-wrap.

Hasil akhir lebih baik dari kondisi sebelum slice ini dimulai, dan regresi
yang sempat masuk sudah hilang. Pengukuran di atas bisa diulang dengan mirror
Python yang sama (skrip scratch, tidak ikut commit).

## Validasi runtime — SUDAH dijalankan lewat CI

Sandbox authoring tidak punya engine Godot (unduhan engine resmi mengarah ke
`objects.githubusercontent.com`, tidak terjangkau dari sana). Runtime test
karena itu dijalankan lewat **PR #326** (workflow `godot-rebuild.yml`).

Hasil: job `validate` **pass** (9m25s), run `37931273704`, semua langkah
penting sukses:

| Langkah | Hasil |
|---|---|
| Static guardrails and GDScript lint | success |
| Install the pinned official engine | success |
| Native import (not the old converter) | success |
| Native simulation, input and screen lifecycle tests | success |

Langkah terakhir itu menjalankan `--headless --script res://tests/run_all.gd`,
yang sudah termasuk `HeroShopPortraitChecks`. Artinya:

- Risiko `add_child()` sebelum card masuk tree **terbukti aman** di engine.
- Suite portrait tidak menghasilkan `SCRIPT ERROR:` maupun `FAIL:`.

## Catatan verifikasi visual

Portrait belum pernah dirender engine (tidak ada screenshot dari CI).
Komposisi hanya diverifikasi secara numerik dengan mirror Python dari
draw call yang sama (skrip scratch, tidak ikut commit):

- bbox konten Kaizen / Thorne / generik semuanya di dalam kanvas 96×96
  (tepi 1.0–95.2 adalah frame 2px).
- coverage 28–36%, jadi figure tidak kosong dan tidak memenuhi frame.

Catatan kecil: backdrop Thorne gelap, jadi frame 2px hampir tidak terlihat
di sana. Bukan bug, hanya kontras rendah.

## Sisa pekerjaan slice ini

- Koreksi visual portrait Kaizen/Thorne kalau render nyata di review
  menunjukkan komposisi yang kurang pas.
- Merge PR #326.

## Peta sisa migrasi — temuan saat hendak lanjut

Dibaca hanya untuk memilih slice berikutnya, bukan audit menyeluruh:

| Area | Status |
|---|---|
| Kit hero | **222/222 selesai**, 0 pending (PR #292, merge `8119e31`) |
| item/forge | **Sudah terport** (`scripts/match/forge.gd`, `item_forge_panel.gd`, `forge_scene_checks.gd`) |
| Katalog level, audio, player command/shop, match pacing | Selesai (PR #318/#323/#324/#325) |
| `lighting.py` (239 baris) | **Belum terport** — tidak ada padanan di `godot_rebuild/` |
| `hero_marker.gd` | Selesai: placeholder 4-6 sisi tetap untuk `grimjaw_checks`, siluet per-hero dipakai `prototype_view.gd:619`; art roster dipaku golden fixture (layer 9aj) |

Catatan: `ui_components/hero_portraits.py` yang di-impor `_core.py:3056`
**tidak ada di repo**, jadi sumber Python untuk portrait arte-faktual sudah
hilang. Portrait karena itu dibangun prosedural, bukan disalin.

`HERO_MIGRATION_PROGRESS.md` menyebut sisa di luar kit: *AIPlayer penuh,
item/forge, art final — hanya atas permintaan pengguna*. Karena forge sudah
ada, efektif tinggal AIPlayer penuh dan art final. (**Koreksi 9ak:** baris ini
status pertengahan migrasi — AIPlayer penuh sejak itu ditutup, lihat
"Integrasi penuh AI lawan" di bawah, banner pembaruan di
`HERO_MIGRATION_PROGRESS.md`, dan "Rekonsiliasi klaim status AI" di akhir
dokumen ini; sisa sebenarnya hanya art final, dan `lighting.py` tetap di luar
scope.)

## Slice berikutnya: siluet hero arena (art)

`hero_marker.gd` menggambar semua 222 hero sebagai poligon 4–6 sisi dengan warna
turunan hash, jadi Kaizen dan Thorne tidak bisa dibedakan di arena.

Perubahan (aditif, tidak mengubah kontrak lama):

- `body()` tetap poligon 4–6 sisi karena `grimjaw_checks._markers`
  mengunci `points.size() >= 4 and <= 6` untuk seluruh roster.
- `silhouette(point, radius, hero_type)` baru: Kaizen ramping (8 titik),
  Thorne tambun (12 titik), hero lain wobble deterministik 7–10 titik.
  Semua titik di dalam `radius * MAX_REACH` (1.2) agar tetap terbingkai
  lingkaran tim.
- `fill()` kini memakai warna khas Kaizen/Thorne, hash untuk sisanya.
  Tetap opaque dan stabil, jadi `grimjaw_checks` tetap lolos.
- `prototype_view.gd` menggambar `silhouette()`, bukan `body()`.
- Suite baru `tests/hero_marker_checks.gd`, terdaftar di `run_all.gd`.

## PopupAnimation + ScreenShake

**`PopupAnimation`** — tanpa pygame dan tanpa RNG, jadi oracle-nya nol
dependensi. Yang diport: `progress += (target - progress) * 0.15` dengan jepretan
`|diff| < 0.01`, lalu turunan `_ease_out_back(progress)` untuk scale dan
`int((1 - progress) * 30)` untuk offset-Y. Oracle mengeksekusi blok sumber
**termasuk fungsi easing tingkat modul** yang dipanggil kelasnya, jadi kurva
`c1 = 1.70158`-nya benar-benar kurva sumber.

**`ScreenShake`** — `add_shake` menyimpan nilai terbesar, `update` memakai
decay 0.85 lalu memotong ke 0 di bawah 0.5, `get_offset` menarik dua bilangan
bulat acak dalam ±`int(intensity)`. Karena `get_offset` memakai RNG, suite
native **tidak** membandingkan nilai eksak; yang dikunci adalah invarian
sebenarnya: kedua komponen bilangan bulat di dalam batas intensitas. Invarian
yang sama juga diuji terhadap sampel sumber.

### Divergensi yang sengaja dipertahankan

`prototype_battle.gd` masih punya shake inline sendiri
(`boss_screen_shake_intensity` + `boss_screen_shake_timer`). Ia menambah gerbang
8 tick dan memakai offset `cos/sin`, bukan acak — keduanya **tidak ada di
sumber Python**.

Saya **tidak** menggantinya, karena
`boss_presentation_checks.gd` mengunci `boss_screen_shake_timer == 8` lalu
`== 7`. Menggantinya akan merusak perilaku PR #325 yang sudah merge. Jadi
`ScreenShake` baru adalah kelas yang bisa dipakai ulang, dan menyatukan kedua
jalur itu keputusan terpisah yang perlu Anda setujui.

## KillFeed + ComboCounter

Dua mesin state deterministik dari `_render.py`, diport dengan pola yang sama
(oracle sumber → fixture JSON → suite Godot yang memutar ulang fixture).

- `scripts/ui/kill_feed.gd` — `add_kill(killer, victim, team)` menyusun
  `"Kaizen >> Grimjaw"` (biru) atau `"<<"` (merah), mendorong `target_y` tiap
  entri lama +20, menambah entri baru, lalu `pop(0)` saat lewat 5 entri.
  `update()` menurunkan `lifetime` 180 dan meng-ease `y_offset` 20% menuju
  `target_y`, lalu membuang entri yang habis.
- `scripts/ui/combo_counter.gd` — tiap kill menyegarkan jendela 120 tick,
  mem-pop `target_scale` ke 1.3 dan menyalakan `color_flash` 20 tick. Saat
  jendela habis, `last_combo` mencatat combo lalu `count` nol dan panel
  memudar (`*0.85`, dipotong ke 0 di bawah 0.05).
- Oracle: `tests/kill_feed_source_oracle.py` (6 kill di tick 0/3/6/9/12/15,
  200 tick — tick 15 membuktikan cap 5 entri: entri terlama terbuang dan
  `target_y` tersisa `[80, 60, 40, 20, 0]`) dan
  `tests/combo_counter_source_oracle.py` (kill di tick 0/1/2/40/41, 220 tick —
  tick 120 membuktikan jendela 120 tick masih menyisakan `timer == 40`).

### Divergensi yang sengaja dipertahankan

`ComboCounter.add_kill()` di sumber juga mengirim banner tier ke panel samping
khusus Python (`from mobile import sidepanel`) di dalam `try/except Exception:
pass`. Efek samping itu **tidak diport**; ambangnya diekspos lewat
`ComboCounter.tier_for()`. Perhatikan sumber memakai `==`, bukan `>=`: combo 7
tidak mengumumkan apa-apa, dan suite Godot mengunci perilaku itu.

## WaveAnnouncer + PathPreview

Dua pengumum/penanda wave dari `_render.py`. Berbeda dengan slice
sebelumnya, **kurva animasinya hidup di dalam `draw()`**, bukan di `update()`.
Karena menulis ulang rumus fase di oracle akan membuat fixture sekadar salinan
tebakan saya, oracle mengeksekusi `draw()` asli dengan shim pygame/font
minimal lalu memakai `sys.settrace` untuk membaca lokal `x_offset` / `alpha`
langsung dari frame di baris `cx = screen_w // 2 + x_offset`. Shim-nya
berarti oracle tetap jalan tanpa pygame (CI tidak punya pygame).

- `scripts/ui/wave_announcer.gd` — `announce()`/`update()` mengurus umur 120
  tick; `get_offset_x(screen_w)` dan `get_alpha()` memaparkan tiga fase:
  slide-in (progress < 0.2, `_ease_out_back`), hold (0.2–0.7, offset 0,
  alpha 255), slide-out (≥ 0.7, `_ease_in_back`).
- `scripts/ui/path_preview.gd` — `show()`/`update()` mengurus umur 120 tick
  dan mengosongkan `paths` saat habis; `get_alpha()` memaparkan fade-in 20
  tick / hold / fade-out 40 tick dari alpha 200; `dash_offset()`,
  `pulse_index()`, `arrow_size()`, `arrow_alpha()` memaparkan fase dash
  berjalan dan pulsa per-arah-panah (pulse 0 → ukuran 8 & alpha penuh,
  selainnya ukuran 5 & alpha setengah).

### Yang sengaja tidak diport

- **Geometri segitiga panah** `PathPreview`. Titik-titiknya adalah offset di
  sekitar pusat surface blit 20×20 milik pygame; renderer Godot harus
  memusatkannya ulang. Yang diport hanya keputusan waktu/warna/ukuran yang
  dibutuhkan renderer.
- Isi visual `WaveAnnouncer`: gradasi latar, border emas, garis diagonal,
  `corner_ticks`, dan blit teks — semuanya menggambar pygame, bukan state.
- `_ease_out_back` sengaja diduplikasi dari `popup_animation.gd` agar tiap
  port berdiri sendiri; keduanya dikunci oleh oracle-nya masing-masing.

## AchievementPopup

Notifikasi achievement, diport dengan pola oracle yang sama. Seperti
`WaveAnnouncer`, kurvanya hidup di dalam `draw()`, jadi oracle menjalankan
`draw()` asli dengan shim pygame/font lalu memakai `sys.settrace` untuk
membaca `x_offset` / `alpha` / `glow_alpha` langsung dari frame.

- `scripts/ui/achievement_popup.gd` — `unlock()` mengantre notifikasi dan
  `update()` mengurasnya **FIFO ketat**, masing-masing dapat slot 180 tick.
  `get_offset_x()` / `get_alpha()` memaparkan tiga fase: slide-in dari kanan
  (progress < 0.15, `_ease_out_back` — yang sedikit **overshoot** melewati 0,
  jadi offset bisa negatif), hold sampai 0.85, lalu slide-out.
  `get_glow_alpha()` mengikuti 30% awal slot dan mengembalikan `-1` (`NO_GLOW`)
  saat sumbernya tidak menggambar glow sama sekali.
- Oracle menjalankan 760 tick dengan 4 unlock (tick 0/10/20/190): tick 10 dan
  20 mengantre di belakang popup yang sedang tayang (antrean memuncak di 2),
  lalu popup berganti tepat di tick 180/360/540 dan antrean habis di tick 720.

### Jebakan GDScript yang ditemukan di slice ini

`gdparse` dan `gdlint` **tidak** menangkap error inferensi tipe — hanya CI
yang menjalankan engine. Menulis

```gdscript
var tracked := (
    is_equal_approx(a, b)
    and x == int(c[0])
)
```

gagal saat kompilasi dengan `Cannot infer the type of "tracked" variable`,
karena `is_equal_approx` punya banyak overload sehingga tipe rantai `and`
tidak bisa ditentukan. Bentuk yang sama di posisi **`return`** aman (dipakai
`wave_announcer_checks.gd`), jadi solusinya mengembalikan ekspresi langsung
atau memberi anotasi tipe eksplisit (`: bool`). Bila ragu, pakai `return`
daripada `:=` untuk ekspresi majemuk.

### Catatan presisi

Di tick 0 sumbernya memberi `x_offset == 299`, bukan 300: `_ease_out_back(0)`
menghasilkan sisa floating-point ~`4e-16`, bukan nol eksak. Nilai ini
terekam apa adanya di fixture dan harus direproduksi bit-dem-bit oleh port —
alasan utama mengapa kurva tidak ditulis ulang dengan tangan.

### Yang sengaja tidak diport

Isi visual panel: gradasi, border emas, `corner_ticks`, geometri ikon per
`icon_type` (star/sword/skull/shield/gold), serta teks dan elipsis
(`ui_theme.fit_ellipsis` bergantung metrik font).

## LevelIntroScreen (state + getter, bukan draw)

Kartu intro level (`_render.py::LevelIntroScreen`) — diport **hanya state dan
fungsi `get_*()`**, mengikuti pola oracle yang sama. Kurva fade, tint tema,
bar kesulitan, dan teks gold/passive/boss-tag ada di dalam `draw()` dan
`_draw_*`, jadi oracle menjalankan draw() asli dengan shim pygame/font dan
`sys.settrace` membaca lokalnya.

- `scripts/ui/level_intro_screen.gd` — `setup()` menerima dict level dan dict
  boss; `update()` menaikkan timer dan mengembalikan `true` hanya di tick
  pertama (saat sumber memutar `wave_start`); `handle_skip()` menutup kartu
  lewat spasi/enter/klik. `get_fade_alpha()` (`int(255 * t/30)`, lalu 255),
  `get_theme_tint_alpha()`, `get_theme_tint_rgba()` (34 tema + default hutan),
  `get_difficulty_info()`, `get_bar_color()`, `get_starting_gold_text()`,
  `get_passive_text()`, `get_boss_tag()`, `get_begin_prompt()`,
  `get_show_prompt()`.
- Oracle: `level_intro_screen_source_oracle.py` → `fixtures/level_intro_screen_source.json`.
  Timeline 70 tick pada level 1 (fade, prompt muncul setelah tick 30, lalu
  skip), tabel skip (spasi, enter, huruf lain, klik, sudah nonaktif), dan
  20 level × 3 kesulitan (easy/normal/hard) pada tick 40.

### Yang sengaja tidak diport

- Seluruh `draw()` / `_draw_level_info` / `_draw_boss_preview` /
  `_draw_boss_silhouette` / `_draw_space_prompt`: vignette, divider, berlian,
  siluet boss, sinar aura, glow mata, panah prompt, shadow, dan pulse
  `pygame.time.get_ticks()` yang menggerakkannya.
- Gold awal dan passive income di sumber memakai `_core.compute_starting_gold`
  / `compute_gold_per_second` / `format_gold_rate`. Itu di luar slice ini,
  jadi oracle sengaja menyediakan `_core` tanpa fungsi tersebut, sehingga
  sumber jatuh ke fallback `except` (`starting_gold` dari level, default 1000,
  dan `PASSIVE +3/s`). Port mengikuti fallback itu. (**Ditutup layer 9al:**
  jalur `_core` penuh kini diport lewat `match_economy.gd` dan dikunci fixture
  dua kolom — lihat "Gold/passive intro dari `_core` penuh" di bawah.)
- Pemanggil yang mengambil boss dari `get_all_boss_types()` dan memanggil
  `setup()` belum ada; saat ini kartu hanya bisa dibuat dari fixture/test.
- `ui_theme.draw_icon("warn")` dan `corner_ticks` (ikon peringatan kedua sisi
  teks "PREPARE FOR BATTLE") tidak diport; teks peringatannya hanya
  tersedia lewat `get_warning_text()`.

## BossIntroCinematic (state + getter, bukan draw)

Banner nama boss di atas layar (`_render.py::BossIntroCinematic`). Tidak
memause gameplay. Diport **hanya state dan getter**, dengan oracle yang sama
seperti `LevelIntroScreen`: `draw()` asli dijalankan di bawah shim, dan
`sys.settrace` membaca `alpha`, `x_offset`, `banner_x`, `fill`, dan tag; shim
juga mencatat rectangle `pygame.draw.rect` sehingga lebar banner, alpha
background/border, dan rect bar HP datang dari sumber.

- `scripts/ui/boss_intro_cinematic.gd` — `setup()` menerima dict boss;
  `update()` menghitung mundur 100 tick dan mengembalikan `true` hanya di tick
  pertama (saat sumber memutar `nexus_hit`); `handle_skip()` menutup banner lewat
  spasi, escape, atau klik. Getter: `get_alpha()` (fade-in 12 tick, fade-out 20
  tick terakhir), `get_slide_offset()` (ease-out kubik, 18 tick, dari -640),
  `get_banner_x()`/`get_banner_width()` (maks 600), `get_background_alpha()`,
  `get_hp_fill_width()` (penuh di 85% durasi), `get_hp_bar_rect()`, `get_tag()`.
- Oracle: `boss_intro_cinematic_source_oracle.py` →
  `fixtures/boss_intro_cinematic_source.json`. Timeline penuh 100 tick pada
  `abaddon`, tabel skip (spasi, escape, huruf lain, klik, sudah nonaktif), dan
  seluruh 216 boss pada tick 1/12/18/40/80/88/99.

### Yang sengaja tidak diport

- Pixel drawing: sudut emas (`corner_ticks`), background rounded-rect, dan
  pengisian bar HP. Semuanya dipetakan ke angka di atas, tapi tidak digambar.
- Siluet boss, aura, dan sinar (`_draw_boss_silhouette`, `_draw_true_boss_silhouette`,
  `_draw_mini_boss_silhouette`) — ia dipanggil dari draw dan bergantung pada
  pulse `pygame.time.get_ticks()`. Belum ada port visualnya.
- `_draw_boss_text`, `_draw_hp_preview`, dan `_draw_skip_hint` tidak pernah
  dipanggil dari `draw()` (kode mati di sumber), jadi tidak diport.
- Pemanggil yang membuat banner dari `Boss` hidup (`_core.py` di dua tempat)
  belum ada di Godot; saat ini banner hanya bisa dibuat dari fixture/test.

## Slice berikutnya: efek `_render.py` — FloatingText lalu HitParticle

Dua kelas efek murni-state yang paling mudah dikunci, dikerjakan berurutan
dengan pola oracle yang sama.

### HitParticle (spark saat kena hit)

Diport dari `_render.py::HitParticle`: `x += vx`, `y += vy`, `vy += gravity`
(0.15), `vx *= 0.95`, countdown lifetime, lalu turunan `alpha_ratio =
lifetime / max_lifetime` untuk alpha dan ukuran.

Oracle mengeksekusi kelas aslinya **termasuk pre-render sprite pygame**
(`pygame.Surface` + `pygame.draw.circle`) — berjalan headless, jadi seluruh
badan sumber ikut dieksekusi apa adanya. Kasus tanpa velocity memakai
`random.uniform`, jadi diseed dan nilai awalnya direkam agar suite native
bisa me-replay lintasan yang sama.

- `tests/hit_particle_source_oracle.py` → `tests/fixtures/hit_particle_source.json`
- `scripts/ui/hit_particle.gd` + `tests/hit_particle_checks.gd`
- Terdaftar di `run_all.gd` dan di `godot-rebuild.yml`.

## Slice berikutnya: FloatingText / damage number

`godot_rebuild` belum punya runtime floating text — `floating_text` hanya
muncul di `boss_kill_credit_source.json`, tidak ada kelasnya.

Diport dari `_render.py::FloatingText`: gerak + drift, decay `velocity_y`
0.95, animasi scale (lerp 0.3 lalu susut 0.99), countdown lifetime, dan
kurva alpha `min(1, lifetime / (max_lifetime * 0.5))`.

**Oracle sumber tidak memakai `import _render`** — modul itu saat ini gagal
diimpor karena circular import yang sudah ada (`cannot import name
'MapRenderer' from partially initialized module '_render'`). Karena Python
asal read-only, oracle mengeksekusi blok `class FloatingText` **langsung dari
berkas sumber** dengan `get_font` distub, jadi angka di fixture tetap
berasal dari algoritma sumber yang sebenarnya.

- `tests/floating_text_source_oracle.py` → `tests/fixtures/floating_text_source.json`
- `scripts/ui/floating_text.gd` + `tests/floating_text_checks.gd` (replay fixture)
- Terdaftar di `run_all.gd`, dan oracle-nya dijalankan CI lewat
  `godot-rebuild.yml` (sebelum tes Godot, jadi drift sumber maupun drift port
  sama-sama menggagalkan CI).

## SpriteCache (state + getter, bukan drawing pygame)

`SpriteCache` dari `_render.py` kini punya port state-only di
`scripts/ui/sprite_cache.gd`, suite replay di `tests/sprite_cache_checks.gd`,
dan oracle tanpa pygame di `tests/sprite_cache_source_oracle.py` dengan fixture
`tests/fixtures/sprite_cache_source.json`. Port mempertahankan cache surface
penuh dan cropped, callback render sebagai metadata state, anchor hasil crop,
hit/miss, eviction FIFO, invalidation prefix, clear, statistik, serta shared
shortcut. Surface pygame dan pixel drawing sengaja tidak diport.

Suite dan oracle terdaftar di `tests/run_all.gd` dan
`.github/workflows/godot-rebuild.yml`.

## RenderCache (state + getter, bukan drawing pygame)

`RenderCache` dari `_render.py` kini punya port state-only di
`scripts/ui/render_cache.gd`, suite replay di `tests/render_cache_checks.gd`,
dan oracle tanpa pygame di `tests/render_cache_source_oracle.py` dengan fixture
`tests/fixtures/render_cache_source.json`. Port mempertahankan clamp ukuran
font, key style/bold, cache circle dengan clamp warna, cache glow dan metadata
layer, statistik, clear yang mempertahankan font, serta shared shortcut.
Objek Font/Surface pygame dan pixel drawing sengaja tidak diport.

Suite dan oracle terdaftar di `tests/run_all.gd` dan
`.github/workflows/godot-rebuild.yml`.

## MapRenderer (state + getter, bukan drawing pygame)

`MapRenderer` dari `_render.py` kini punya port state-only di
`scripts/ui/map_renderer.gd`, suite replay di `tests/map_renderer_checks.gd`,
dan oracle tanpa pygame di `tests/map_renderer_source_oracle.py` dengan fixture
`tests/fixtures/map_renderer_source.json`. Port mempertahankan dimensi map,
theme, data lane/river/dekorasi, readiness layer statis/dinamis, posisi toko,
getter lane/shop, serta hit-testing toko. Delegasi StaticRenderer,
DecorationRenderer, ShopRenderer, DynamicRenderer, dan seluruh pixel drawing
pygame sengaja tidak diport.

Suite dan oracle terdaftar di `tests/run_all.gd` dan
`.github/workflows/godot-rebuild.yml`.

## Wiring Runtime, Rendering `PrototypeView`, dan Scene Checks (PR #329)

Seluruh port UI/render dari `_render.py` kini telah dihubungkan ke runtime
pertandingan (`scripts/match/prototype_battle.gd`,
`scripts/match/battle_item_effects.gd`, `scenes/prototype/prototype_screen.gd`),
panel modal (`hero_shop_panel.gd`, `item_forge_panel.gd`,
`meta_hero_shop_panel.gd`), dan digambar secara vektor di
`scenes/prototype/prototype_view.gd`:

- **`EffectManager` (`scripts/ui/effect_manager.gd`)** — dikoordinasikan oleh
  `Prototype.effects`: damage numbers, heal/status floating text, gold popups,
  hit particles, death explosions, combo counter (`combo_count` & `combo_timer`
  didelegasikan langsung ke `effects.combo_counter`), wave announcer + path
  preview saat wave 1 dimulai, screen shake, kill feed (`register_kill` tetap
  no-op sesuai sumber), dan achievement popup saat boss dikalahkan/di-unlock.
- **`MapRenderer` (`scripts/ui/map_renderer.gd`)** — dikonfigurasi oleh
  `Prototype._configure_map_renderer()` saat inisialisasi dan `configure_level()`
  dengan path lane/river dan palet tema; menyediakan `is_click_on_shop()` dan
  `clicked_shop_at()`, serta dihubungkan ke klik shop di `PrototypeScreen`.
- **`SpriteCache` & `RenderCache` (`scripts/ui/sprite_cache.gd`,
  `scripts/ui/render_cache.gd`)** — dihubungkan ke `FloatingText.configure()`,
  `MapRenderer.cache_theme_assets()`, `EffectManager` (death explosion,
  wave announcer, achievement popup), dan `Prototype` (`_cache_hero_assets`,
  `_cache_boss_assets`, `cache_stats()`).
- **`LevelIntroScreen` (`scripts/ui/level_intro_screen.gd`)** — dikonfigurasi
  pada awal level (`_configure_level_intro()`), di-step tiap tick lewat
  `step_level_intro()` (memutar `wave_start` pada tick pertama), dan dapat
  di-skip lewat `KEY_SPACE`, `KEY_ENTER`, atau klik di `PrototypeScreen`.
- **`BossIntroCinematic` & `BossDeathAnimation`
  (`scripts/ui/boss_intro_cinematic.gd`, `scripts/ui/boss_death_animation.gd`)**
  — dikonfigurasi saat spawn boss (`_configure_boss_intro()`, memutar
  `nexus_hit` di tick pertama) dan saat boss dikalahkan
  (`_configure_boss_death()`, berjalan selama `boss_death_pause_ticks` 60/90
  tick lalu masuk fase celebration 120 tick untuk true boss), dengan dukungan
  skip `KEY_SPACE`, `KEY_ESCAPE`, atau klik di `PrototypeScreen`.
- **`PopupAnimation` (`scripts/ui/popup_animation.gd`)** — dihubungkan ke
  `HeroShopPanel`, `ItemForgePanel`, dan `MetaHeroShopPanel` (`open_panel()`,
  `close_panel()`, `_process()`, `popup_state()`).
- **`ScreenShake` (`scripts/ui/screen_shake.gd`)** — `Prototype.current_screen_shake_offset()`
  mempertahankan gate 8-tick `boss_presentation_offset()` untuk kompatibilitas
  `boss_presentation_checks.gd`, lalu mendelegasikan offset ke
  `effects.get_shake_offset()` dan dipakai oleh `PrototypeView._draw()`.
- **Rendering `PrototypeView` (`scenes/prototype/prototype_view.gd`)** —
  menggambar world effects (`_draw_path_preview`, `_draw_world_effects` termasuk
  `DeathExplosion` dan `_draw_boss_death_sequence`) serta screen overlays
  (`_draw_wave_announcer`, `_draw_combo_counter`, `_draw_kill_feed`,
  `_draw_achievement_popup` dengan glow awal slot, `_draw_boss_intro` dengan
  subtitle & border alpha, `_draw_boss_celebration` dengan backdrop/reward/hint,
  dan `_draw_level_intro` dengan theme tint, difficulty bars, gold/passive,
  boss preview), serta memaparkan `overlay_draw_summary()`.
- **Scene & Runtime Checks** — diuji di `effect_manager_checks.gd`,
  `map_renderer_checks.gd`, `sprite_cache_checks.gd`, `render_cache_checks.gd`,
  `level_intro_screen_checks.gd`, `boss_intro_cinematic_checks.gd`,
  `boss_death_animation_checks.gd`, `death_explosion_checks.gd`,
  `popup_animation_checks.gd`, `screen_shake_checks.gd`, `kill_feed_checks.gd`,
  `achievement_popup_checks.gd`, `boss_death_pause_scene_checks.gd`, dan
  `forge_scene_checks.gd`.

## Batas scope

- Tidak ada portrait hero lain yang dimulai (hanya Kaizen + Thorne + fallback generik).
- `lighting.py` tidak diport: ia post-process per-piksel di atas pygame
  Surface, sementara `godot_rebuild` menggambar vektor. Memaksanya masuk
  berarti reinterpretasi, bukan port.
- Kelas state di `scripts/ui/` mempertahankan state/getter murni tanpa objek
  Surface/Font pygame, sementara penggambaran vektor dilakukan secara native di
  `PrototypeView` (`scenes/prototype/prototype_view.gd`).
- Klaim "AIPlayer penuh belum ada" di `HERO_MIGRATION_PROGRESS.md` **sudah
  usang**: AI terport lintas 9 modul (`ai_build/controller/draft/
  hero_control/items/policy/recruitment/shields/upgrades`, 52 fungsi) dengan
  `ai_controller.tick()` sebagai entry.
- Top-up flow Python dan voucher allowlist tidak disentuh.
- Tidak ada sistem lain yang diaudit atau diubah.

## Integrasi penuh AI lawan (penutup "AIPlayer penuh")

Checkbox terakhir di `AI_CONTRACT.md` ("uji integrasi penuh") ditutup oleh
`tests/ai_match_integration_checks.gd`, terdaftar di `run_all.gd`. Suite itu
menjalankan match produksi penuh, bukan per adaptor: replay deterministik dua
world ber-seed sama (wave ditunda supaya hanya RNG AI yang aktif), invarian per
tick pada match hidup (purse tidak negatif, roster <= 5, reserve draft hidup
setelah belanja non-hero, target draft tidak pernah dibuang), jendela ber-purse
pra-fund untuk rekrut/upgrade/item/auto-cast, pembekuan jam-counter-purse setelah
hasil match, sakelar merah mati tetap nol transaksi, dan jadwal elite level 54
hard (sembilan tick, tiga aksi). Tidak ada perubahan policy, balance, UI, sumber
Python, atau CI di slice ini.

## Tempest Veil (layer 9j)

`is_veiled()` kini dipakai di tiga tempat seperti sumber: serangan keluar
(`hero_basic_attack`, sudah ada), auto-cast opt-in pemain (`_step_hero_auto_cast`,
baru), dan imunitas damage masuk (`_hero_denies_hit` di `minion_battle._deliver_hit`,
baru - sebelumnya hero ber-veil justru menerima damage penuh). Oracle AST
`hero_veil_immunity_source_oracle.py` (15 kasus, kolom `expected`/`native_old`,
7 cek bentuk) plus suite replay `hero_veil_immunity_checks.gd`.

## Block damage hero (layer 9k)

`get_block()` kini benar-benar dikonsumsi: `minion_battle._damage_amount` memanggil
`_after_hero_block()` di posisi sumber (setelah mitigasi + amp, sebelum keep
Bristleback), dengan `max(block pasif, aura Bulwark Guard)`. Sebelumnya hanya aura
yang dikurangkan, dan itu pun setelah keep. Seam roll baru `block_roll_override`
dipakai match (`_item_rng`) dan lab (`block_rng`); `reset_ai` menyemai
`block_rng = seed + 3`. Oracle `hero_block_source_oracle.py` (8 kasus, angka
katalog asli) + suite `hero_block_checks.gd`. Kandidat berikutnya yang tercatat:
model armor item untuk hit magic dan urutan amp-versus-armor.

## Model armor hero (layer 9l)

Sumber `Hero.take_damage` memakai amp Soul Rend dulu lalu formula armor untuk
setiap hit non-fire tanpa melihat sekolah (semua hero `armor=0`/`MR=0`, jadi
hanya armor item yang relevan). Native sebelumnya memilih mitigasi dari sekolah
(magic -> MR = 0) dan menjalankan amp sesudahnya. Kini `DamageRules.hero_amount()`
+ `resolve_armor()` memegang ladder itu, `_deliver_hit` meneruskan `damage_type`,
dan jalur non-hero (magic minion -> MR, neutral raw) tetap. Oracle
`hero_armor_model_source_oracle.py` (9 kasus) + suite `hero_armor_model_checks.gd`.

## Arm skill sourceless (layer 9m)

`ThorneSkills` Q (Viscous Nose) kini mengirim `_deliver_hit(-1, ..., "neutral")`
sesuai sumber `e.take_damage(int(h.skill_damage * 0.8), h.team)` yang tanpa
`source=`: tidak dikreditkan ke `damage_dealt`, evasi korban tetap berlaku tanpa
true strike/blind penyerang, dan korban non-hero menerima damage raw (menara
armor 6: 56, bukan 41). Oracle `hero_skill_sourceless_source_oracle.py`
(4 baris, dua kolom dieksekusi dari `Hero.take_damage` + `Tower.take_damage`
asli, 7 cek bentuk) plus suite `hero_skill_sourceless_checks.gd`.


## Ladder damage minion (layer 9n)

Sumber `Minion.take_damage` (`_entity.py:5795-5825`) menjalankan amp Soul Rend
lebih dulu, lalu bonus Corroder (`min(1, shred * 0.06)`, non-`fire`), baru
mitigasi sekolah dengan `armor = self.armor - shred` (shred dikurangkan dua
kali); sekolah bebas tetap membawa amp. Native lama melakukan mitigasi dulu,
amp sesudahnya, dan `neutral` raw tanpa bonus shred. Kini
`DamageRules.minion_amount()` memegang ladder sumber; boss tetap memakai urutan
lama lewat `_school_first_amount()` karena `BaseBoss.take_damage` port
tersendiri. Oracle `minion_damage_ladder_source_oracle.py` (9 kasus, kolom
`expected`/`native_old`) plus suite `minion_damage_ladder_checks.gd`.


## Arm item pada menara/kastil (layer 9o)

Arm bonus damage item memanggil `target.take_damage(amount, h.team[, "magic"])`
tanpa `source=`, jadi korban menara/kastil berjalan dengan sekolah `None`:
armor menara tidak memotong bonus, tidak ada kredit `damage_dealt`, dan kastil
tetap menyerap lewat shield + reduksi 0.88. Native lama mengirim `dealer_id` +
sekolah deklarasi ke bus. Oracle `item_structure_arm_source_oracle.py` (4
baris, kolom `expected`/`native_old`) plus suite
`item_structure_arm_checks.gd`.


## Arm item pada minion/hero (layer 9p)

Rute sourceless 9o kini berlaku untuk seluruh korban bus arm item:
`battle_item_effects.deal_damage()` mengirim `-1`/`"neutral"` ke `_deliver_hit`,
jadi armor/magic resist minion tidak memotong bonus arm, kredit
`credit_hero_damage(None, ...)` kosong, dan korban hero tetap menjalankan armor
item (cabang armor sumber digerakkan damage_type, layer 9l). Oracle
`item_unit_arm_source_oracle.py` (4 baris) plus suite `item_unit_arm_checks.gd`;
kontrol minion suite 9o memaku nilai 9p (55/credit 0).


## Splash Cleave Axe (layer 9q)

Loop cleave sumber memanggil `u.take_damage(splash, h.team)` tanpa `source=`,
jadi `cleave_splash()` kini mengirim `-1`/`"neutral"` juga untuk korban unit
(armor minion tidak memotong, kredit kosong, armor item hero tetap berlaku);
cabang boss sudah sourceless sejak 9e. Oracle
`item_cleave_splash_source_oracle.py` (4 baris) plus suite
`item_cleave_splash_checks.gd` (troll 50/0 vs 45/45, hero armor 37/0 vs 37/37,
dua minion [50, 50]/0 vs [45, 50]/45).


## Tipe damage lengan magic pada korban unit (layer 9r)

Sumber memakai argumen posisional ketiga sebagai tipe damage
(`take_damage(damage, team, "magic")`), jadi `deal_damage_magic_sourceless()`
kini mengirim `"magic"` untuk seluruh korban (boss sejak 9g, unit sejak 9r) dan
gate windrun `_hero_denies_hit()` mengikuti `_is_physical_hit` (hanya
`normal`/`projectile` non-magic yang bisa meleset). Oracle
`item_magic_arm_unit_source_oracle.py` (4 baris) plus suite
`item_magic_arm_unit_checks.gd` (chain pada hero Windrun 45/0 vs 0/0, chain pada
hero evasi 45/0 vs 0/0, pierce pada hero armor 40/40, pierce pada troll 55/55).


## Reflect Razor Carapace pada penyerang unit (layer 9s)

Sumber memantulkan lewat `source.take_damage(dmg, team, "magic")` tanpa
`source=`, jadi `reflect_item_effects.deal_damage()` kini mengirim
`-1`/`"neutral"` + tipe `"magic"` untuk seluruh penyerang (boss sejak 9i, unit
sejak 9s); preload `BossState` dan cabangnya dihapus. Oracle
`item_reflect_unit_source_oracle.py` (4 baris) plus suite
`item_reflect_unit_checks.gd` (undead 170 vs 144, troll 170 vs 162, hero armor
125/125, hero tanpa armor 170/170).


## Reflect Bristleback (layer 9t)

Sumber memantulkan lewat `_src.take_damage(payload, self.team, source=None)`
tanpa sekolah, jadi `_deliver_hit` kini mengirim pantulan Bristleback sebagai
`"neutral"`/tipe `"normal"` dengan sumber `-1`; guard dan keep 0.70/0.85 tidak
berubah. Oracle `hero_bristleback_reflect_source_oracle.py` (5 baris) plus suite
`hero_bristleback_reflect_checks.gd` (troll 35 vs 31, troll masuk magic 42 vs
38, undead 35/35, hero armor 26/26, hero tanpa armor 35/35).


## Lengan skill Sylara (layer 9u)

Empat panggilan damage sumber hanya mengirim tim (tanpa sekolah), jadi
`sylara_skills.gd` kini mengirim `"neutral"` (Q line, E initial, E tick, R
powershot) dan `_stun()` mengikuti gate `hasattr(target, 'attack_timer')`
sehingga korban menara tidak ditulisi properti tak ada. Oracle
`sylara_skill_arm_source_oracle.py` (4 baris) plus suite
`sylara_skill_arm_checks.gd` (Q troll 95 vs 85, E troll 66 vs 59, E+tick troll
104 vs 93, E menara 66 vs 56).


## Hit pembuka R Grimjaw (layer 9v)

Sumber memanggil `h.target.take_damage(int(h.skill_damage * 2.5), h.team)` tanpa
sekolah, jadi `grimjaw_skills.gd` cabang `"r"` kini mengirim `"neutral"` (sumber
tetap `-1`); spin Blade Fury, tick Omnislash, cone E dan AOE fallback R sudah
paritas (sumber + sekolah `dmg_school`). Oracle
`grimjaw_skill_arm_source_oracle.py` (5 baris) plus suite
`grimjaw_skill_arm_checks.gd` (R troll 65 vs 58, R menara 65 vs 55, R hero armor
48/48, spin troll 253/253, cone E troll 35/35).


## Peluru menara/nexus (layer 9w)

`Bullet._on_hit` tidak pernah mengirim `source=`/`school=`, jadi
`siege_battle.gd::_projectile_school` kini selalu `"neutral"` dan gate Wind Wall
membaca sekolah hasil resolve (override 8q untuk boss dihapus karena aturannya
berlaku umum). Oracle `tower_bullet_school_source_oracle.py` (6 baris) plus
suite `tower_bullet_school_checks.gd` (archer troll 20 vs 18, mage troll 17 vs
16, splash cannon 25 vs 22, bolt mage vs Wind Wall 0 vs 17, hero armor 15/15,
archer vs Wind Wall 0/0).


## Serangan dasar minion (layer 9x)

`Minion.update` menyerang dengan `take_damage(self.damage, self.team)` tanpa
source/sekolah, jadi `minion_battle.apply_hit` kini mengirim `-1` + `"neutral"`
untuk penyerang non-hero (hero tetap bersumber seperti sumber `Hero`). Oracle
`minion_melee_school_source_oracle.py` (3 baris) plus suite
`minion_melee_school_checks.gd` (orc pada menara 13 vs 11, pada troll 13 vs 12,
hero armor 10/10, baris boss live: netral == jalur `_deliver_hit(-1, ...)`,
physical lebih kecil, tanpa pantulan Razor Carapace ke minion, dan tanpa
atribusi kill/source id: `killed_by` -1 untuk kill minion, boss tanpa
`last_hit_source_id`).


## Atribusi pengiriman skill bersama (layer 9y)

Audit 116 situs `Common.hit(` + `_deal_hero_aoe(` menunjukkan split native sudah
sama dengan sumber: 9 situs ber-atribut (shared 2, vex 3, zephyr 4), 107
sourceless, dan semua resep boss tetap sourceless. Tidak ada kode produksi yang
diubah; oracle `skill_hit_attribution_source_oracle.py` mengklasifikasi situs,
memaku split per kit, dan mengeksekusi baris Vex R (225 kredit 225 vs
sourceless 237 kredit 0), Thorne E (71 kredit 71), Gornak Q (268 kredit 0);
suite `skill_hit_attribution_checks.gd` mereplay ketiganya lewat produksi dan
menghitung ulang token situs dari skrip yang dikirim.


## Tick burn unit (layer 9z)

`_tick_burn` kini mengirim `_deliver_hit(-1, burn_team, unit, damage, "neutral",
unit.position, "fire")` seperti sumber `self.take_damage(dmg, burn_team or team,
"fire")`, dan blok hero dilewati untuk fire (bersarang di cabang non-fire).
Oracle `burn_tick_delivery_source_oracle.py` (6 baris) plus suite
`burn_tick_delivery_checks.gd`: hero amp 45 vs 30, Bristleback 21 vs 30, veil
0 vs 30, shadow realm 0/0, block item 30 dengan 0 undian, troll 30/30
(kontrol; Corroder hanya berlaku untuk hit non-fire 39).

## Tick item Miasma (layer 9aa)

`hero_items.py::_tick_miasma` (`:223-227`) mengirim `tgt.take_damage(m["damage"],
team, "magic")` - tiga argumen posisional tanpa `source=`/`school=`, jadi
sekolahnya `None` (`_entity.py:106-130`). Kini `tick_miasma` memakai
`effects.deal_damage_from(..., "neutral", "magic")` dan cabang non-boss bus
mengirim `world._deliver_hit(-1, source_team, tgt, amount, school, origin,
damage_type, true)` (korban boss tetap memakai handle sumber 9b/9d plus
`last_hit_is_miasma_tick`). Oracle `miasma_tick_delivery_source_oracle.py`
(7 baris) plus suite `miasma_tick_delivery_checks.gd`: kredit 0 di semua kolom
sourceless (native lama 30/22/8/28/30), troll MR 0.05 - 30 vs 28, shred
Corroder 39, menara armor 3 - 30 dengan kredit 0 vs 30, veil 0/0, dan kontrol
Razor Carapace/`killed_by`/boss tetap dipaku.

## Tick burn boss + damage number boss (layer 9ab)

Tick burn pada boss sudah paritas sejak 8g (`boss_state.gd::tick_tower_debuffs` +
`prototype_battle.gd::_step_active_boss`, sentinel `last_hit_source_id = -1`),
jadi yang berpindah di layer ini adalah **presentasi**-nya: `Boss.take_damage`
sumber memakai `is_critical=(effective_damage > max_hp * 0.03)` dan anchor
`y - radius - 10`, sedangkan port lama memakai ambang datar `dealt > 100` dan
`y - radius`. Helper `PrototypeBattle._boss_damage_number()` kini dipakai jalur
tick burn maupun jalur `_deliver_hit` boss.

Oracle `burn_boss_delivery_source_oracle.py` mengeksekusi `Boss.take_damage`
dan `_tick_tower_debuffs` asli (10 kasus + 2 baris refresh store), suite
`burn_boss_delivery_checks.gd` mereplay lewat `_step_active_boss` dan memaku
nol kredit untuk kill burn, kesetaraan `world.apply_burn` versus store boss,
serta interval tick `rules.burn_tick = 30 = DEBUFF_FPS 60`.

## Pengiriman damage boss tanpa source (layer 9ac)

`Boss.take_damage(damage, from_team)` sumber tidak pernah membaca `from_team`
maupun memfilter tim; blind hanya dikonsultasikan bila ada `source`
(`bosses/base_boss.py:5983`). Cabang boss `_deliver_hit` kini membaca
`ignore_team_guard` seperti cabang unit 9z/9aa, sehingga delivery sourceless
bertim sama bisa mendarat persis seperti sumber tanpa mengubah perilaku lama
tanpa flag. Oracle `boss_sourceless_delivery_source_oracle.py` (7 kasus, kolom
undian blind dan kredit) plus suite `boss_sourceless_delivery_checks.gd`.

## Tenacity debuff boss (layer 9ad)

`Boss.apply_slow` dan `Boss.apply_debuff` (`bosses/base_boss.py:528-552`) memotong `slow` dan
`atk_slow` dengan tenacity 0.50 (magnitude `min(0.35, a * 0.5)`, durasi `int(d * 0.5)`), sedangkan
`skill_down`/`anti_heal`/`burn` diteruskan mentah ke store `TowerDebuffMixin`; store unit sendiri
tidak mengenal tenacity. Pemanggil item/menara semuanya polimorfik di sumber, jadi tiga jembatan
native yang masih menulis ke store dunia diperbaiki: override `_mage_impact`, `apply_anti_heal` di
`battle_item_effects.gd` (lewat metode korban), dan dua panggilan aura di `_update_auras` yang pindah
ke bus boss-aware.

Oracle `boss_debuff_tenacity_source_oracle.py` (28 baris, kolom unit sebagai kontrol) plus suite
`boss_debuff_tenacity_checks.gd`. Angka terukur: mage L6 skill-down/anti-heal tetap 0.50/180 dan
1.00/180, ice L6 slow 0.65/150 -> 0.325/75 dan atk-slow 0.40/150 -> 0.20/75, Frostbite 0.28/180 ->
0.14/90 (anti-heal 0.45/180 mentah), Freezing Aura atk-slow 0.30/30 -> 0.15/15 (anti-heal 0.40/30
mentah), Cauterize 0.50/30 mentah, Arctic Blast 0.45/210 -> 0.225/105, Entangle root 1.00/120 ->
cap 0.35/60. Audit: Alchemist W / `_apply_slow` hanya menyasar unit, jadi jalur itu sudah paritas.

## Slow resist item pada arm bus (layer 9ae)

`TowerDebuffMixin.apply_slow` (`_core.py:853-867`) mengabaikan korban mati, menskalakan payload dengan
slow resist item korban (Abyss Breaker 0.30, cap 0.60), lalu menulis kedua field dengan aturan
`amount > slow_amount or slow_timer < duration`. Sebelumnya bus `battle_item_effects.gd::apply_slow`
hanya mendelegasi ke metode entitas untuk bos, sehingga hero/minion/struktur menerima tulis mentah
`maxf`/`maxi` tanpa resist dan tanpa guard mati. `UnitState.apply_slow` + `HeroState.slow_resist()`
kini memegang metode itu; `BossState.apply_slow` tetap menimpa dengan tenacity.

Oracle `item_slow_resist_source_oracle.py` (10 baris, kolom `native_old` pra-9ae) plus suite
`item_slow_resist_checks.gd`. Angka terukur: Frostbite 0.28/180 -> 0.196/180 pada hero Abyss Breaker,
Arctic Blast 0.45/210 -> 0.315/210, root 1.00 -> 0.70, cap 0.60 -> 0.40, merge menurun 0.50/20 lalu
0.20/120 -> 0.20/120 (lama 0.50/120), merge memendek 0.20/120 lalu 0.50/30 -> 0.50/30 (lama 0.50/120),
dan korban mati tidak lagi ditulis. Jalur dunia tetap 0.196 (resist sekali) dan bos tetap 0.14/90.

Temuan samping: pin minion 0.45/210 di `boss_item_slow_checks.gd` dulu berlaku pada goblin yang mati
(hp 45 ditelan 130 damage) - tulis mentah pra-9ae menembus kematian, sumber tidak. Probe kini hidup
(hp 10000) dan guard `alive` dipaku terpisah oleh probe kedua yang mati. Baris cap resist 0.60 dijalankan
lewat `ResistProbe` karena tidak ada item hidup dengan resist itu.

## Store silence item pada korban unit (layer 9af)

`_apply_silence_to` (`hero_items.py:2693-2697`) memanggil `target.apply_debuff('atk_slow'/'skill_down',
1.0, duration)` di dalam `try`; mixin hanya milik Hero/Minion/Boss, jadi menara tidak pernah disilence.
Cabang unit jembatan native dulu menulis field mentah (amount dipaksa 1.0, timer `maxi`, tanpa guard mati,
dan menyilence struktur). Kini ia lewat store dunia yang identik dengan mixin.

Oracle `item_silence_store_source_oracle.py` (7 baris) plus suite `item_silence_store_checks.gd`. Angka
terukur: 0.9/200 + silence 60 -> 1.0/60 (lama 1.0/200), 1.0/200 tidak ditulis, 1.0/10 -> 1.0/60, korban mati
0.5/5 tetap 0.5/5 (lama 1.0/60), skill-down 0.5/30 + 90 -> 1.0/90, dan menara tetap tak tersentuh.

Divergensi terbuka yang ditemukan di layer ini (kandidat berikutnya): store dunia menolak payload
non-positif (`amount <= 0 or duration <= 0`) sementara mixin sumber tidak punya guard itu. Terukur pada
baris `zero_duration_keeps_store` (sumber: amount 1.0 dengan jam 0; native: store dibiarkan), dipaku lewat
kolom `native_open`.

## Slow smart-AI boss + DOT Ice Vortex (layer 9ag)

39 lengan slow sumber di `Boss._smart_ai_*` dijalankan lewat `e.apply_slow(...)`; port `boss_ai.gd::_slow`
dulu menulis field mentah sehingga slow resist item korban terlewat. Kini `_slow` memanggil metode korban
(guard hidup + resist + aturan refresh 9ae); `StructureState` tetap dilewati seperti `hasattr` sumber.

Temuan yang ikut ditutup: DOT Ice Vortex (`base_boss.py:1414-1427`) hilang total di jalur AI - hanya timer
yang turun. `BossAI._tick_ice_vortex` kini menjalankan damage `skill_q_damage // 3` (243 -> 81) ke musuh
dalam 80 px plus slow 0.5/60 di awal resep Ancient Apparition.

Oracle `boss_ai_slow_source_oracle.py` (19 payload + 4 merge) dan suite `boss_ai_slow_checks.gd`; angka
terukur: 0.5/180 polos vs **0.35/180** ber-resist (lama 0.5/180), merge store 0.4/10 -> 0.35/180, dan
radius vortex 81 px nol damage.

## Attack lock smart-AI boss (layer 9ah)

46 penulisan `e.attack_timer = max(getattr(e, 'attack_timer', 0), N)` di `base_boss.py` semuanya di belakang
`hasattr`, dan `attack_timer` hanya milik `Hero` (`_entity.py:3392`). Port `_attack_lock` menambahkan cabang
`else` yang menulis `cooldown_ticks` minion - lock yang sumber tidak pernah pasang. Kini lock hanya untuk
hero, dengan aturan `max` dan payload 46/46 yang sudah paritas.

Oracle `boss_attack_lock_source_oracle.py` (9 baris: hero 90/200/150/30, minion 5 -> 5 vs lama 90, menara,
dua probe mati) plus suite `boss_attack_lock_checks.gd` dengan kontrol resep hidup Ancient Apparition E
(hero 90, minion 0).

### Status item terbuka store debuff (ditutup oleh layer 9ai)

Divergensi guard non-positif store dunia yang dicatat 9af kini **tertutup sebagai tidak terjangkau**, bukan sebagai paritas: seluruh payload sumber terbukti positif (minimum literal call site 0.35; tabel `ICE_LEVELS`/`CANNON_LEVELS`/`MAGE_LEVELS` minimum `slow 0.25`, `burn_dps 6`, `anti_heal 0.4`), dan lengan native (110 arm) tidak pernah mengirim payload non-positif. Guard tetap dipertahankan; enam baris divergensi dipaku dengan kolom `source_rule`/`divergence` di `tests/fixtures/debuff_payload_reach_source.json` (25 baris payload nyata + 4 sentinel + 2 window) dan direplay `tests/debuff_payload_reach_checks.gd`.

### Siluet hero arena — selesai, lalu tabrakan art diperbaiki (layer 9aj)

Rencana di atas sudah mendarat (`silhouette()`, `fill()` khas Kaizen/Thorne, `prototype_view.gd` menggambar siluet, suite `hero_marker_checks.gd` terdaftar). Yang belum: cakupan roster. Cabang generik memakai `(code >> (index % 12)) % 5`, yaitu hanya bit 0-9 dari kode di bawah 1000003, sehingga **33 pasang** dari 220 hero generik menggambar siluet identik (`gravefang` = `hitokage`, `kaerinya` = `kyumirra`, `lyrienne` = `lyssarethys`, dan 30 pasang lain).

Perbaikan: `spread = fingerprint * 48271 + 1021`, jumlah sisi dari `spread % 4`, dan wobble dari digit basis-5 `spread` (bukan bit rendah). Terukur: **222/222 siluet unik**, sisi {7, 8, 9, 10} untuk generik (Kaizen 8, Thorne 12), reach 1000-1120 untuk generik (Kaizen 1150, Thorne 1154) - semuanya ≤ `MAX_REACH` 1200, sehingga cincin tim tetap membingkai. Oracle `hero_marker_source_oracle.py` menulis golden fixture `hero_marker_source.json` (222 entri: keluarga, jumlah sisi, hash terkuantisasi 1e-4, reach mili, digest) dan suite merekomputasi seluruhnya dari `silhouette()` produksi, termasuk kontrol **222/222 unik** dan view wiring (`prototype_view.gd` memakai `HeroMarker.silhouette(`, tidak memakai `HeroMarker.body(`) yang dipin `validate_project.py`.


## Rekonsiliasi klaim status AI (layer 9ak, doc-only)

Audit "kandidat berikutnya" menemukan premis "AIPlayer penuh belum ada" sudah
usang tetapi masih tertulis di lima dokumen. Bukti audit (tanpa perubahan
produksi): **79/79** resep `_smart_ai_*` sumber punya arm dispatch native di
`boss_ai.gd` (set-diff kosong; `_generic` hanya untuk boss tanpa resep
khusus), **55** oracle boss khusus, `ai_match_integration_checks.gd` benar-benar
berjalan di `run_all.gd`, **0** TODO/stub di sembilan modul `ai_*.gd` maupun
`boss_ai.gd`, dan spot-check paritas semuanya bersih (basic attack + cleave 8k,
sourceless ability 8u, flux DOT/clone Morgath, Ice Vortex 9ag, attack lock 9ah,
school proyektil 9w). `validate_project.py` **PASS 13546 static checks** pada
`43e9637` sebelum slice ini.

Koreksi in-place (konvensi repo: klaim usang dikoreksi dengan penanda, bukan
dihapus diam-diam):

- `AI_CONTRACT.md` — "Status paket" (dulu: "Belum port AIPlayer lengkap …
  scene masih memakai defender lama"), bullet reserve (dulu: "item dan
  pemilihan prioritas kandidat masih pending"), penutup roster (dulu:
  "AIPlayer penuh … tetap belum selesai"), lengan upgrade (dulu: "Policy
  scheduler dan wiring scene belum aktif"), shield scene (dulu: "Scene belum
  memanggil AI shield otomatis dan belum memiliki tombol purchase shield" —
  padahal `RegenShieldButton`/`CastleShieldButton` ada di HUD dan lengan
  `regen_shield`/`castle_shield` ada di tabel prioritas), plus seksi 9ak baru.
- `SHIELD_CONTRACT.md` — "Belum ada tombol beli shield atau AI otomatis di
  scene" dan "kills descending masih pending" (keduanya sudah ada:
  `_stable_kills_descending`).
- `NEXUS_CONTRACT.md` — header "(WIP AIPlayer)" dan "loop AI otomatis belum
  aktif" → selesai/aktif.
- `UPGRADE_CONTRACT.md` — header "(WIP)" dan "urutan kandidat dan loop AI
  scene belum aktif" → diterapkan/aktif.
- `HERO_MIGRATION_PROGRESS.md` — banner pembaruan 9ak di bawah judul (bagian
  historis tidak ditulis ulang), penanda koreksi di "Sisa dan blocker tepat",
  dan pesan siap-salin diperbarui (versi lama adalah sumber premis usang yang
  menular antar-sesi).
- Dokumen ini — koreksi silang pada baris "efektif tinggal AIPlayer penuh dan
  art final".

Pin anti-drift baru di `validate_project.py` (blok 9ak): frase stale dilarang
muncul lagi di kelima dokumen (dicocokkan pada teks ternormalisasi whitespace),
penanda koreksi wajib ada, dan setiap klaim terkoreksi diikat ke anchor kode:
`set_ai_enabled(true)` + `reset_ai(AI_MATCH_SEED)` di `prototype_session.gd`,
`ai_controller.tick(` di `prototype_battle.gd`, delapan lengan prioritas di
`ai_policy.gd`, `draft.reserve()` di `ai_items.gd`/`ai_shields.gd`,
`_stable_kills_descending` di `ai_shields.gd`/`ai_upgrades.gd`,
`AIMatchIntegrationChecks.new().run(_check)` di `run_all.gd`, dan tombol shield
pemain di `PrototypeMatch.tscn`/`prototype_screen.gd`.

Batas slice 9ak: hanya dokumen + `validate_project.py`. Tidak ada perubahan
kode produksi, oracle, fixture, atau suite GDScript baru — fakta
dokumen/wiring dipin di `validate_project.py` mengikuti preseden pin
view-wiring 9aj, sehingga `run_all.gd` dan workflow CI tidak berubah (CI
sudah menjalankan `validate_project.py`). `lighting.py`, sumber Python,
balance, FX, UI, dan project settings tidak disentuh.


## Gold/passive intro dari `_core` penuh (layer 9al)

Item terbuka terakhir slice LevelIntroScreen. Sumber (`_render.py:3073-3094`)
memanggil `_core.compute_starting_gold` / `compute_gold_per_second` /
`format_gold_rate` supaya angka di kartu intro SAMA dengan gold yang benar-benar
diberikan `Game.reset()` (docstring `_core.py:232-241`). Port intro dulu hanya
mencerminkan fallback `except` (`starting_gold` mentah dari config, `PASSIVE
+3/s` datar), sementara ledger match (`prototype_battle.gd::
_apply_opening_economy`) sudah menjalankan jalur penuh lewat
`Economy.starting_gold`/`passive_rate` — jadi kartu intro menampilkan angka
yang salah di setiap level >1 atau difficulty non-normal. Terukur pada fixture
lama: L5 hard menampilkan "1000 GOLD" / "PASSIVE +3/s" padahal match memberi
1050 / 3.15→"3.2"; L1 easy menampilkan 1000 padahal match memberi 1250.

Perubahan produksi:

- `match_economy.gd` += `format_gold_rate()` — port `f"{rate:.1f}".rstrip("0")
  .rstrip(".")`. `"%.1f"` Godot dan format Python membulat ties-to-even atas
  nilai biner yang sama; kasus tie 3.75 → "3.8" (L1 easy) terekam di fixture.
- `level_intro_screen.gd`: `setup()` menerima `difficulty` (default `"normal"`,
  padanan `GameSettings().difficulty` di sumber), menghitung `starting_gold`
  dan `passive_rate` lewat Economy, dan `get_passive_text()` memformat lewat
  `format_gold_rate`. Konstanta `GOLD_PER_SECOND` tetap dipertahankan (dipin
  suite sebagai konstanta fallback sumber).
- `prototype_battle.gd::_configure_level_intro()` meneruskan difficulty hidup,
  sehingga kartu dan ledger pembukaan tidak bisa drift.

Oracle `level_intro_screen_source_oracle.py` kini mengeksekusi blok gold
`_core.py` apa adanya (konstanta + tiga fungsi; tanpa pygame, tanpa import
game) dan merekam 60 difficulty rows DUA kali: dengan `_core` penuh (kolom
`starting_gold`/`passive_text` = jalur produksi) lalu dengan `_core` stub
GameSettings-only (kolom `*_fallback` = perilaku pre-9al, jalur `except`
sumber). **59/60 baris berbeda** — hanya L1 normal yang kebetulan sama. Suite
`level_intro_screen_checks.gd` meneruskan difficulty per baris, mereplay kolom
penuh, dan memaku bukti divergensi (baris diverging > 0). `validate_project.py`
memin wiring (`Economy.starting_gold/passive_rate/format_gold_rate` di kartu,
`difficulty` di caller, `format_gold_rate` di Economy) dan bentuk fixture (60
baris, kolom fallback lengkap, tepat 59 diverging, format teks passive).

Batas slice 9al: hanya kartu intro + formatter Economy + satu caller +
oracle/fixture/suite/pin/docs. Ledger match tidak berubah (sudah paritas sejak
slice ekonomi), `GameSettings` tetap shim di oracle (difficulty hidup datang
dari world, bukan save settings), `lighting.py`, sumber Python, balance, FX,
UI lain, dan project settings tidak disentuh.

## Lifecycle stat buff-mandiri boss (layer 9am)

Audit `_tick_smart_clocks` terhadap resep sumber menemukan dua efek expiry
timer buff yang menyimpang dari `bosses/base_boss.py`:

- **Chemical Rage (alchemist).** Sumber (`:1257-1260`) meng-expire buff dengan
  `rage_active = False` SAJA. Cast (`_cast_e_chemical_rage`, `:1341`) menulis
  `self.damage = int(self.damage * 1.5)` terhadap damage SAAT INI, jadi boost
  1.5x persisten setelah expiry dan COMPOUNDING tiap recast (165 → 247 → 370
  di hard). Port pre-9am mereset `boss.damage = _source_damage(boss)` saat
  expiry — penemuan native yang menghapus compounding sumber.
- **Shukuchi (xirthalis).** Sumber `_xirthalis_q` (`:2248-2261`) menulis
  `self.speed = base_speed * 1.8` dengan `base_speed = stats.get("speed",
  1.15)` — speed KATALOG MENTAH, karena `_get_boss_stats` hanya men-scale key
  *damage*. Expiry (`:2211-2216`) memulihkan katalog mentah itu, jadi scaling
  speed difficulty/enrage HILANG permanen setelah satu siklus Q (perilaku
  sumber direplikasi apa adanya). Port pre-9am men-set flag tanpa write speed
  sama sekali dan expire tanpa memulihkan apa pun.

Paritas terkonfirmasi (tidak disentuh): expiry dragon form (reset damage via
stats ↔ `_source_damage`), dragon blood, corrosive, defense, arcane buff
(reset `base_damage` dua sisi), shield, xirthalis timelapse mark.

Perubahan produksi:

- `boss_state.gd` += `catalog_speed` — snapshot `float(stats.get("speed",
  1.15))` di `setup()`, kebal `apply_scaling`/enrage (padanan persis
  `_get_boss_stats()["speed"]` sumber yang tidak pernah di-scale).
- `boss_ai.gd::_tick_smart_clocks`: expiry rage kini HANYA clear flag; expiry
  shukuchi menulis `boss.speed_px_per_tick = boss.catalog_speed`.
- `boss_ai.gd::_xirthalis` arm Q: += `boss.speed_px_per_tick =
  boss.catalog_speed * 1.8`.

Oracle `boss_buff_expiry_source_oracle.py` memin bentuk AST (write-set kedua
blok expiry + segmen persis kedua write cast) dan mengeksekusi method sumber
ASLI (`_smart_ai_alchemist`, `_smart_ai_xirthalis`, `_cast_e_chemical_rage`,
`_xirthalis_q`, `_get_boss_stats`) di stub dengan katalog `boss_data` riil:
5 baris (cast/expiry/recast per boss), 4 divergent, tiap baris merekam kolom
`expected` (sumber) dan `native_old` (port pre-9am) dengan input masing-masing.
Suite `boss_buff_expiry_checks.gd` mereplay kolom `expected` lewat produksi
hidup (`world._spawn_boss` + `BossAI._tick_smart_clocks` + arm resep), memaku
restore katalog mentah (bukan `base_speed`), dan memaku visibilitas divergensi.
`validate_project.py` memin wiring (`catalog_speed` di state, kedua write
speed di AI, tepat satu `_source_damage` reset tersisa = dragon form) dan
bentuk fixture.

Batas slice 9am: hanya dua lifecycle buff di atas + oracle/fixture/suite/pin/
docs. Resep cast alchemist/xirthalis sudah paritas sejak 8u (tidak diubah
selain write speed Q), `lighting.py`, sumber Python, balance, FX, dan UI tidak
disentuh.

## Write damage buff dari stats ter-scale (layer 9an)

Audit lanjutan lifecycle buff boss (di luar sampel 8u) menemukan KELAS
divergensi kedua: empat pasangan buff menulis damage dari snapshot
`base_damage` (sudah di-bake difficulty, int-truncated) padahal sumber
membaca `_get_boss_stats()["damage"]` — katalog MENTAH × skill_down ×
dmg_scaling_mult × enrage, `int(round(v * mult))` — dibulatkan SEKALI:

- nyxarath Necromastery (W): cast `int(stats.damage * 1.4)`, expiry reset
  `stats.get("damage", 130)`.
- thalgryn Morph (E): `× 1.35`, fallback 92.
- syrentha Mirror Image (E): `× 1.4`, fallback 98.
- kunkka Rum (E, Ghost Ship): `× 1.3`, fallback 125.

Contoh hard + enrage nyxarath: sumber cast int(round(175×1.1×1.25)×1.4) = 337;
port pre-9an int(int(175×1.1)×1.4) = 268. Expiry dengan skill-down 0.3 di
hard: sumber 135; pre-9an 192 (baked, tanpa multiplier runtime).

Kelas KEBALIKAN dipin apa adanya: xerathis Arcane memakai ATRIBUT
`self.base_damage` sumber (cast `int(self.base_damage * 1.3)` :3583, expiry
`self.damage = self.base_damage` :3513) dan `base_damage` sumber di-bake
persis seperti native (init :388-389, apply_scaling :515-525) → native
:267/:3420 paritas verbatim, TIDAK disentuh; oracle 9an memaku kedua kelas
agar tidak pernah tertukar.

Perubahan produksi:

- `boss_state.gd` += `catalog_damage` — snapshot damage katalog mentah di
  `setup()` sebelum `apply_scaling` membakar `base_damage` (padanan
  `catalog_speed` 9am).
- `boss_ai.gd::_source_damage` didefinisikan ulang = `_skill_damage(boss,
  boss.catalog_damage)` — analog tepat bacaan stats sumber (single-round,
  multiplier lengkap). Dragon form expiry (:241) dan empat cast lama (:414,
  :3039, :3051, :3347) otomatis naik ke bentuk exact; pada multiplier 1.0
  nilainya identik sehingga semua fixture lama tetap hijau.
- Empat expiry (nyxarath/thalgryn/syrentha/kunkka) kini
  `boss.damage = _source_damage(boss)`; empat cast kini
  `int(float(_source_damage(boss)) * M)`.

Oracle `boss_buff_scaling_source_oracle.py`: pin AST (write-set + segmen
persis keempat expiry/cast, pasangan verbatim xerathis, segmen
`int(round(v * mult))`, dua write bake `base_damage`) dan 8 baris numerik
dari exec method sumber ASLI di stub dengan katalog riil (cast = hard+enrage,
expiry = hard+skill-down 0.3; SEMUA divergen, kolom `expected`/`native_old`).
Suite `boss_buff_scaling_checks.gd` mereplay kolom expected lewat produksi
hidup (`_spawn_boss` + spawn goblin/hero + arm resep per boss), memaku
`catalog_damage` mentah dan visibilitas divergensi. `validate_project.py`:
pin 9am `_source_damage` expiry 1 → 5, cast `_source_damage` == 8, jalur
verbatim base_damage tepat 1+1 (xerathis saja), wiring `catalog_damage`.

Batas slice 9an: hanya write damage buff empat boss + definisi `_source_damage`
+ oracle/fixture/suite/pin/docs. Heal/lock/AOE cast sudah paritas (fixture
boss_ability hijau sejak 8u), xerathis verbatim, presence/shell flag-only,
flux/clones/x_mark memakai `_skill_damage`/damage hidup (paritas), `lighting.py`,
sumber Python, balance, FX, UI tidak disentuh.

## Tabel situs screen-shake boss + shake enrage (layer 9ao)

Sumber menyalakan `_shake_screen(N)` dari **128 situs di 113 method**
`bosses/base_boss.py` (presentasi-only: helper merute ke
`game_instance.effects.shake_screen` dalam try/except). Fisika ScreenShake
sudah diport penuh (`scripts/ui/screen_shake.gd` + oracle/suite sendiri) dan
shake MATI boss sudah dirutekan (`_queue_boss_death_presentation`). Yang
bolong: shake kemampuan — `boss_ai.gd` tidak memanggil shake sama sekali.

Situs-situs cast tersebar di 112 method dengan pola posisi heterogen (64
setelah blok komentar, 12 setelah `pass` FX, sisanya menempel heal/guard
whiff/cabang enrage), jadi wiring 128 situs sekaligus tidak aman; slice ini
membuka jalur bertahap:

- Oracle `boss_shake_sites_source_oracle.py` merekam TABEL OTORITATIF semua
  128 situs (method, line, intensity, kelas, status wired) + histogram
  intensitas exact + pin wiring native. Fixture ini menjadi acuan sub-slice
  9ao-2+ (wiring cast per keluarga boss).
- Situs pertama yang di-wire: pasangan enrage one-shot di `Boss.update`
  (`_shake_screen(25)` true class `:624`, `_shake_screen(15)` mini `:639`).
  `boss_state.gd` += `enrage_fx_shake` (payload one-shot, diset di transisi
  enrage/frenzy yang sudah ada), `prototype_battle.gd` +=
  `_present_boss_enrage_shake()` yang mengonsumsi payload lewat gate 8-tick
  `boss_screen_shake_*` + `effects.shake_screen` — persis jalur shake mati —
  lalu mengosongkannya (konsumsi di `_step_active_boss` setelah
  `advance_combat_clock`).
- Suite `boss_shake_sites_checks.gd`: replay transisi enrage hidup (alchemist
  true → 25, morgath mini → 15) sampai intensity ScreenShake di
  EffectManager, memaku one-shot clear, gate 8-tick, bentuk tabel (128/113/
  126/112 + histogram) dan bahwa tepat dua situs ber-status wired.

Sisa roadmap 9ao: 126 situs cast / 112 method (tabel di fixture) — wiring
bertahap per keluarga boss; tiap sub-slice memindahkan baris fixture dari
`wired: false` ke `true` dan menaikkan pin hitungan.

Batas slice 9ao: hanya payload enrage + tabel/oracle/fixture/suite/pin/docs.
`screen_shake.gd`, EffectManager, shake mati, `lighting.py`, sumber Python,
balance, dan UI tidak disentuh. Hero tetap prosedural (keputusan pengguna).

## Wiring 30 situs shake cast keluarga teraudit (layer 9ao-2)

Sub-slice pertama roadmap 9ao: SEMUA 30 situs `_shake_screen` dari enam
keluarga boss yang sudah diaudit 9am/9an kini dirutekan lewat helper baru
`BossAI._shake(world, intensity)` (presentasi-only, kembaran helper sumber
`Boss._shake_screen:5947`):

- alchemist: Q acid 8, W concoction 15, E rage 12 (setelah heal, urutan
  sumber), R greed 25.
- xirthalis: Q shukuchi 6, W swarm 12, E geminate 8 (guard whiff) / 14 (hit),
  R timelapse 20.
- nyxarath: Q shadowraze 12 (whiff `>300`) / 12 (guard dist-0 — cabang baru,
  sumber `:4805`) / 18 (hit), W necromastery 16, E presence 14, R requiem 30
  (sebelum heal 13%, urutan sumber).
- thalgryn: Q waveform 12 (target null) / 12 (dist-0) / 18 (surge hit) —
  cabang native direstruktur agar ketiga jalur sumber terlihat, W strike 15,
  E morph 10, R replicate 22 (sebelum heal).
- syrentha: Q riptide 10/10/12 (guard guard hit), W song 14, E mirror 10,
  R siren 22 (sebelum heal).
- kunkka: W x-marks 8, E ghost ship 18 (setelah heal, urutan sumber),
  R torrent 28 (sebelum heal).

Shake tidak menyentuh state gameplay (ScreenShake max-accumulate + decay,
sudah diport dengan oracle sendiri), jadi penempatan mengikuti urutan statement
sumber tanpa efek simulasi. Pin: oracle membandingkan MULTISET intensitas
native (regex `_shake(world, N)`) dengan multiset 30 baris fixture ber-`wired`
— persis sama (7×12, 4×10, 3×8, 3×18, 3×14, 2×22, 2×15, 6/30/28/25/20/16);
validate memin helper + hitungan 30. Suite menambah dua probe replay hidup
(rage cast → intensity 12.0; geminate whiff → 8.0) dan pin tabel bergeser ke
32 wired / 96 sisa.

Sisa roadmap 9ao: 96 situs cast / 89 method (fixture = tabel otoritatif),
termasuk keluarga vhorethzir/vaerith/vhyssarion/razak/xerathis/gravewake dan
puluhan boss lain — tiap sub-slice menambah method ke `FAMILY_METHODS`,
mengangkat pin multiset, dan memindahkan baris `wired:false→true`.

Batas slice 9ao-2: hanya 30 insert `_shake` + satu guard dist-0 baru (nyxarath
Q, presentasi-only; jalur gameplay identik karena `normalized()` nol tidak
menghasilkan hit) + restruktur cabang thalgryn Q (identik secara gameplay) +
oracle/fixture/suite/pin/docs. `lighting.py`, sumber Python, balance, UI tidak
disentuh. Hero tetap prosedural (keputusan pengguna).

## Wiring 36 situs shake cast sembilan keluarga tanpa guard (layer 9ao-3)

Sub-slice kedua roadmap 9ao: SEMUA 36 situs `_shake_screen` dari sembilan
keluarga yang shake-nya berada di ekor/tengah helper cast TANPA cabang guard
(ast: 0 early-return, shake selalu dieksekusi) kini dirutekan lewat
`BossAI._shake(world, intensity)` di akhir tiap cabang resep native:

- razak: Q 10, W 14, E 12, R 20.
- khalros: Q 10, W 12 (setelah heal 8%), E 14, R 20.
- varkul: Q 10, W 14, E 10 (setelah heal 12%), R 20.
- xerathis: Q 12, W 14, E 10 (cabang arcane buff, setelah heal 10%), R 24.
- gorath: Q 12 (cabang self-enrage, setelah heal 8%), W 15, E 12, R 22 —
  helper sumber `_gorath_r` dipanggil DUA gerbang smart-AI (target low-HP dan
  self low-HP) dan arm native meng-inline keduanya, jadi shake 22 terpasang di
  akhir KEDUA cabang R (2 situs native untuk 1 baris sumber).
- nyzrak: Q 12, W 14, E 16, R 22 (setelah heal 15%).
- zharok (`_cast_zharok_*`): Q 10, W 5 (cabang kosong selain set-skill),
  E 15, R 20.
- pyrenth (`_cast_pyrenth_*`): Q 12, W 10 (setelah heal 8%), E 18, R 25.
- vokrahn (`_cast_vokrahn_*`): Q 12, W 18, E 15, R 20.

Penempatan: shake di level cabang (di luar pembungkus `if target != null`),
setara sumber karena helper cast tidak punya early-return — jalur whiff tetap
shake. Pin: tiap baris fixture kini membawa `native_occurrences` (jumlah call
site helper di sumber; `_gorath_r` = 2, lainnya 1) dan multiset oracle/suite
mengekspansi baris wired dengan faktor itu — 66 baris wired → 67 situs native;
validate memin hitungan 67. Suite menambah dua probe replay hidup (gorath
cabang R low-HP → intensity 22.0 dengan q/e timer diblok; xerathis arcane buff
→ 10.0) dan pin tabel bergeser ke 68 wired / 60 sisa.

Sisa roadmap 9ao: 60 situs cast / 53 method (fixture = tabel otoritatif),
didominasi keluarga ber-guard (vhorethzir, vaerith, gravewake, vhyssarion,
malzareth, akashari, vorenmarr) plus cast 8u (abaddon, ancient_apparition,
dragon, anti-mage, axe) dan tide_bringer Q.

Batas slice 9ao-3: hanya 37 insert `_shake` (36 baris + duplikat gorath R) +
oracle/fixture/suite/pin/docs — tanpa guard baru, tanpa restruktur cabang.
`lighting.py`, sumber Python, balance, UI tidak disentuh. Hero tetap
prosedural (keputusan pengguna).
