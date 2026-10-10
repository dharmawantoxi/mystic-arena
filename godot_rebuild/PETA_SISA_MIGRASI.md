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
| `hero_marker.gd` | Masih placeholder: "Temporary... Visual polish belongs after migration" |

Catatan: `ui_components/hero_portraits.py` yang di-impor `_core.py:3056`
**tidak ada di repo**, jadi sumber Python untuk portrait arte-faktual sudah
hilang. Portrait karena itu dibangun prosedural, bukan disalin.

`HERO_MIGRATION_PROGRESS.md` menyebut sisa di luar kit: *AIPlayer penuh,
item/forge, art final — hanya atas permintaan pengguna*. Karena forge sudah
ada, efektif tinggal AIPlayer penuh dan art final.

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
  dan `PASSIVE +3/s`). Port mengikuti fallback itu. Jalur `_core` penuh
  belum diverifikasi.
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
`.github/workflows/godot-rebuild.yml`. Slice berikutnya sesuai urutan kerja
adalah `RenderCache`.

## Batas scope

- Tidak ada portrait hero lain yang dimulai (hanya Kaizen + Thorne + fallback generik).
- `lighting.py` tidak diport: ia post-process per-piksel di atas pygame
  Surface, sementara `godot_rebuild` menggambar vektor. Memaksanya masuk
  berarti reinterpretasi, bukan port.
- `EffectManager` keseluruhan tidak diport; baru `FloatingText`,
  `HitParticle`, `PopupAnimation`, `ScreenShake`, `KillFeed`, `ComboCounter`,
  `WaveAnnouncer`, `PathPreview`, `AchievementPopup`, dan `LevelIntroScreen`
  (yang terakhir hanya state + getter, lihat bagian di atas), serta `BossIntroCinematic`
  (juga state + getter). Masih belum ada
  (0 kemunculan di `scripts/` + `scenes/`):
  `RenderCache`. `SpriteCache` kini punya port state + getter
  (`scripts/ui/sprite_cache.gd` dan fixture oracle-nya), tetapi surface pygame
  dan pixel drawing sengaja **tidak diport**. `DeathExplosion` kini punya port state + getter
  (`scripts/ui/death_explosion.gd` dan fixture oracle-nya), tetapi `draw()`
  pygame, flash sprite, dan spark drawing sengaja **tidak diport**.
  `BossDeathAnimation` kini punya port state + getter (`scripts/ui/
  boss_death_animation.gd` dan fixture oracle-nya), tetapi seluruh `draw()`
  pygame (gelombang, dissolve, fragmen, dan celebration) sengaja
  **tidak diport**. `MapRenderer` juga belum — yang ada baru
  `terrain/lane/river/wall_tiles.gd`.
- Klaim "AIPlayer penuh belum ada" di `HERO_MIGRATION_PROGRESS.md` **sudah
  usang**: AI terport lintas 9 modul (`ai_build/controller/draft/
  hero_control/items/policy/recruitment/shields/upgrades`, 52 fungsi) dengan
  `ai_controller.tick()` sebagai entry.
- Top-up flow Python dan voucher allowlist tidak disentuh.
- Tidak ada sistem lain yang diaudit atau diubah.
- Top-up flow Python dan voucher allowlist tidak disentuh.
