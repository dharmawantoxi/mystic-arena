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

## Batas scope

- Tidak ada portrait hero lain yang dimulai (hanya Kaizen + Thorne + fallback generik).
- `lighting.py` tidak diport: ia post-process per-piksel di atas pygame
  Surface, sementara `godot_rebuild` menggambar vektor. Memaksanya masuk
  berarti reinterpretasi, bukan port.
- `EffectManager` keseluruhan tidak diport; baru `FloatingText`,
  `HitParticle`, `PopupAnimation`, `ScreenShake`, `KillFeed`, dan
  `ComboCounter`. Masih belum ada
  (0 kemunculan di `scripts/` + `scenes/`):
  `WaveAnnouncer`, `PathPreview`, `AchievementPopup`, `LevelIntroScreen`,
  `BossIntroCinematic`, `SpriteCache`, `RenderCache`. `DeathExplosion` dan
  `BossDeathAnimation` baru kontrak **waktunya** yang diport (via
  `boss_presentation_source_oracle.py` + `boss_death_pause_checks.gd`),
  kelas visualnya belum. `MapRenderer` juga belum — yang ada baru
  `terrain/lane/river/wall_tiles.gd`.
- Klaim "AIPlayer penuh belum ada" di `HERO_MIGRATION_PROGRESS.md` **sudah
  usang**: AI terport lintas 9 modul (`ai_build/controller/draft/
  hero_control/items/policy/recruitment/shields/upgrades`, 52 fungsi) dengan
  `ai_controller.tick()` sebagai entry.
- Top-up flow Python dan voucher allowlist tidak disentuh.
- Tidak ada sistem lain yang diaudit atau diubah.
- Top-up flow Python dan voucher allowlist tidak disentuh.
