# Peta Sisa Migrasi — status singkat

Peta ini mencatat migrasi visual Godot yang berlangsung per slice.

## Status terkini — branch `arena/799d0e95-mystic-arena`

- PR #334 sudah di-merge (`a134020`). 9aw WaveAnnouncer + PathPreview, 9ax ikon
  AchievementPopup, 9ay HitParticle, 9az FloatingText, dan 9ba panel
  AchievementPopup sudah ada di `main`.
- 9bb melengkapi visual `KillFeed.draw()`: kotak latar hitam, border membulat
  warna tim, fade-in/hold/fade-out, slide-in 100 px, dan teks 22 px rata kanan
  di (layar-20, 250). Oracle `kill_feed_draw_source_oracle.py` menjalankan
  `draw()` asli di bawah shim pygame perekam (31 frame, 192 op);
  `kill_feed_draw_checks.gd` mereplay fixture lewat layout murni dan lewat state
  `KillFeed` produksi. Rincian ada di bagian "Slice 9bb" paling bawah.
- 9bc melengkapi visual `ComboCounter.draw()`: bar timer 80x4, teks `xN` 48 px
  berbayang (cincin 8 arah atau satu bayangan (2, 2) menurut `cheap_alpha`)
  di (layar-100, 100), label tier dari 5 kill, dan lerp flash ke putih.
  Oracle `combo_counter_draw_source_oracle.py` menjalankan `draw()` asli di
  bawah shim pygame perekam (52 frame, 426 op); `combo_counter_draw_checks.gd`
  mereplay fixture lewat layout murni dan lewat state `ComboCounter` produksi.
  Rincian ada di bagian "Slice 9bc" paling bawah.
- 9bd melengkapi visual `BossIntroCinematic.draw()`: banner 600x92 membulat
  (latar `(10, 10, 18)` pada `210*alpha/255`, border 2 px `entrance_color`),
  corner ticks emas hanya di atas alpha 60, teks tag / nama 46 px / judul
  ber-kutip dengan alpha fade, dan bar HP membulat 150x12. Bar HP digambar
  langsung ke layar sehingga **tidak ikut fade** (kuirk sumber yang
  dipertahankan). Oracle `boss_intro_draw_source_oracle.py` menjalankan `draw()`
  asli plus `ui_theme.corner_ticks` asli di bawah shim pygame perekam (22 frame,
  279 op); `boss_intro_draw_checks.gd` mereplay fixture lewat layout murni, lewat
  state `BossIntroCinematic` produksi, dan lewat `PrototypeView`. Rincian ada di
  bagian "Slice 9bd" paling bawah.
- 9be melengkapi visual `BossDeathAnimation._draw_celebration()` (true boss):
  overlay `darken` hingga 180, tint emas `(80, 60, 20, 40)`, `BOSS DEFEATED!`
  66 px dengan enam salinan bayangan yang memantul, nama 46 px berbayang, judul
  ber-kutip, hadiah emas dengan ikon koin, `HERO UNLOCKED!` dengan dua bintang
  vektor, enam percikan berputar, dan hint skip berdenyut. Oracle
  `boss_celebration_draw_source_oracle.py` menjalankan `draw()` asli di bawah
  shim pygame perekam bersama (`tests/draw_recorder.py`; 20 frame, 547 op);
  `boss_celebration_draw_checks.gd` mereplay fixture dari state terekam, dari
  `BossDeathAnimation` produksi, dan lewat `PrototypeView`. Rincian ada di bagian
  "Slice 9be" paling bawah.
- 9bf melengkapi visual `BossDeathAnimation._draw_death_sequence()`: kilat putih
  aditif 15 tick, gelombang ledakan (cincin 3 px konsentris + inti setengah alpha,
  bergeser 2 px dari boss), badan dua warna yang memudar, fragmen persegi
  berotasi dengan tepi 1 px, dan partikel jiwa naik dengan glow radial. Seluruh
  `boss_death.draw()` kini digambar PALING AKHIR di screen space (setelah level
  intro dan tanpa goncangan), seperti `_core.py`. Oracle
  `boss_death_sequence_draw_source_oracle.py` menjalankan `draw()` asli dengan
  fragmen/partikel acak ber-seed lalu menyimpan spesifikasinya agar Godot
  mereplay lewat `configure(...)` (12 frame, 2299 op); `boss_death_sequence_draw_checks.gd`
  mereplay lewat state produksi dan `PrototypeView`. Rincian ada di bagian
  "Slice 9bf" paling bawah.
- 9bg melengkapi visual `DeathExplosion.draw()` dan `HitParticle.draw()`: kilat
  pusat berupa dua cakram di satu surface SRCALPHA (inti putih `size // 2`
  MENIMPA cakram pucat `size`) pada anchor `int(x), int(y)`, dan tiap percikan
  berupa sprite (cakram warna + inti putih yang menimpa tengahnya) yang diskalakan
  ke `max(1, int(size * rasio))` dan di-blit dengan alpha `int(255 * rasio)`.
  Percikan ledakan dan partikel dunia kini memakai satu layout
  (`hit_particle_layout.gd`). Oracle `death_explosion_draw_source_oracle.py`
  menjalankan `DeathExplosion` dan `HitParticle` asli di bawah shim bersama
  (`transform.scale` dimodelkan di geometri lingkaran; 25 frame, 582 op);
  `death_explosion_draw_checks.gd` mereplay lewat state produksi dan
  `PrototypeView`. Rincian ada di bagian "Slice 9bg" paling bawah.
- 9bh melengkapi langkah terakhir `MapRenderer.draw()`: tint ambient per tema
  (53 dari 54 tema; forest tidak punya) yang menutup seluruh peta di bawah
  unit. Sebelumnya `theme["ambient_tint"]` selalu `null` di Godot dan tidak ada
  yang menggambarnya. Dengan `Quality.cheap_alpha` tint di-blit apa adanya
  (alpha 12-22); tanpa itu layar dikalikan `255 - (255 - c) * a / 255`.
  Oracle `map_tint_draw_source_oracle.py` menjalankan `MapRenderer.draw` asli di
  bawah shim bersama dengan tint tiap tema dibaca dari literal tema asli
  `map_components/_bundle.py` (54 tema x 2 jalur = 108 frame, 106 op);
  `map_tint_draw_checks.gd` mereplay tabel dan frame lewat layout murni dan
  `PrototypeView`. Rincian ada di bagian "Slice 9bh" paling bawah.
- 9bi memin urutan gambar dari sumber: `Game.draw` melukis banner boss SEBELUM
  `effects.draw_ui` (wave announcer, lalu achievement), lalu level intro, dan
  `boss_death.draw` paling akhir; `EffectManager.draw` melukis path preview, ledakan,
  partikel, lalu teks melayang, dan `tactical.draw_world` sesudahnya. Sebelumnya
  Godot melukis banner boss DI ATAS announcer dan achievement, dan efek taktis di
  bawah path preview. Oracle `draw_order_source_oracle.py` membaca urutan itu
  langsung dari `_core.py` / `_render.py` dengan `ast`; `prototype_view` kini melukis
  dari konstanta `OVERLAY_ORDER` / `WORLD_LAYER_ORDER` yang dibaca balik
  `draw_order_checks.gd`. Rincian ada di bagian "Slice 9bi" paling bawah.
- 9bj mengubah arah migrasi visual (keputusan user: "bake PNG dari pygame"). Tampilan Godot
  masih jauh dari pygame karena art dunia (peta, unit, menara, hero, boss) masih placeholder;
  slice overlay 9bb-9bi tidak mengubahnya. Kode art pygame dijalankan headless (`pygame`,
  `numpy`, `Pillow`) oleh skrip di `godot_rebuild/bake/`, hasilnya PNG di
  `godot_rebuild/assets/art/` dengan manifes `godot_rebuild/data/art/*.json` (ukuran, byte,
  sha256). Layer 9bj membake dekorasi + bangunan toko tiap tema (54 PNG, ~1 MB) dan
  menggambarnya antara lane dan tembok tepi (`MapArt`, hook `_draw_map_decor`). Rincian di
  bagian "Slice 9bj" paling bawah.
- 9bk membake sprite minion (5 tipe x 5 level nexus x biru/merah, 50 atlas, 2,7 MB, 2500
  frame) dan menggambarnya di `MinionView._draw_unit` lengkap dengan bar HP dan aura slow
  sumber; lingkaran lama jadi cadangan bila atlas belum diimpor. Rincian di bagian "Slice
  9bk" paling bawah.
- 9bl membake sprite menara (Archer/Cannon/Ice/Mage x biru/merah x level), kastil nexus
  level 1-5 (lima frame api obor) dan lencana perisai, lalu menggambarnya di `SiegeView`
  dengan bar HP/perisai, lencana level, dan label perisai kastil seperti sumber. Struktur
  kini dilukis SEBELUM unit (seperti `Game.draw`). Rincian di bagian "Slice 9bl".
- 9bm membake penanda slot bangun (lima frame glow biru + satu merah, `BuildSlots` asli) dan
  menggambarnya di bawah menara, seperti `Game.draw`. Rincian di bagian "Slice 9bm".
- 9bn menambah suite scene `painter_scene_checks.gd` yang menjalankan `_draw` view prototipe
  sungguhan di CI (penghitung `draw_count`) dengan semua tipe minion, menara tiap jalur,
  seleksi, slow, hurt, dan tembakan. Rincian di bagian "Slice 9bn".
- 9bo membake badan hero untuk tujuh hero berkit native (Kaizen, Thorne, Grimjaw, Sylara,
  Vex, Zephyr, Alchemist; biru + merah; 8 fase diam, 8 fase jalan, pose serang, dua arah;
  14 atlas, 5,5 MB) dan menggambarnya dengan overlay `Hero.draw` (bar HP 45x6, papan nama
  dan bintang level, bayangan, cincin seleksi, strip cooldown). Hero lain tetap memakai
  penanda siluet. Rincian di bagian "Slice 9bo".
- 9bp membake peluru menara (panah 16 arah per tim, bola meriam, kristal es, bolt mage; satu
  sheet 6 KB) dan menggambarnya di `SiegeView` menggantikan titik 4 px. Peluru hero
  (`world.hero_projectiles`) belum. Rincian di bagian "Slice 9bp".
- 9bq membake badan 216 boss (pose diam fase 0, dua arah; satu PNG per boss, 2,6 MB) dan
  menggambarnya menggantikan lingkaran bermahkota, dengan bayangan, bar HP, dan papan nama di atas
  puncak sprite (`BOSS_LABEL_TOP`). Rincian di bagian "Slice 9bq".
- Urutan bake berikutnya (user: "semuanya"): skin HUD/menu (9br: tema, 9bs: latar menu utama;
  HUD dan arena layar penuh belum), peluru hero, pose jalan/serang boss.
  Sisanya di luar bake: `DynamicRenderer`
  (partikel, kabut, obor, air bergerak) dan `tactical_commands.draw_world/draw_ui`.
  Keputusan user: combo counter dan kill feed tetap tampil di Godot (walau tidak digambar
  pygame).

## Catatan historis portrait Hero Shop

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
| `lighting.py` (239 baris) | **Terport (layer 9aq)** — `scripts/ui/sprite_lighting.gd`: matematika mask eksak (gradien kanonik 28x28, rim/terminator/band-2) dipaku oracle `sprite_lighting_source_oracle.py`; adaptor vektor dipakai `prototype_view._draw_lit_polygon` untuk siluet hero & badan boss |
| `mobile/combat_audio.py` (332 baris) | **Terport (layer 9ar)** — `scripts/audio/combat_audio.gd`: gate SFX tempur (7 jenis, `_KONFIG` volume/jeda, anggaran 4 per frame, 24 kanal tanpa rebut, master*sfx) dipaku oracle `combat_audio_source_oracle.py`; dipanggil di serangan dasar hero, tembakan menara per jalur (biru 1.0/merah 0.8), ayunan minion dan serangan boss; pool 24 `AudioStreamPlayer` di `audio_manager.gd` |
| `mobile/sidepanel.py` (741 baris) | **Terport (layer 9as)** — `scripts/ui/side_panel_layout.gd` (tata letak murni: aturan lebar layar 2200/120 px, kotak STATUS/HEROES/TACTICAL, hit-test popup) + `side_panel.gd` (Control: latar batu, irama segar 250 ms, sentuhan) dipaku oracle `side_panel_source_oracle.py`; dipasang `prototype_screen._build_side_panel`, `project.godot` stretch aspect `expand` |
| `splash_screen.py` (371 baris) | **Terport (layer 9at)** — `scripts/ui/splash_timeline.gd` (fade/skip/partikel/gradien/vignette/logo/tata letak murni) + `scenes/splash/splash_screen.gd` (Control, latar dipanggang sekali, tap/klik/tombol skip) dipaku oracle `splash_screen_source_oracle.py`; `app.gd` kini boot ke SPLASH lalu `finished` -> menu; logo `assets/logo.png` disalin dari sumber |
| Top-up / voucher (`topup_currency.py` 221, `topup_voucher.py` 95, `Menu.topup_*` di `_core.py`, klien `server/app.py`) | **Terport (layer 9au)** — `scripts/match/topup_currency.gd` (deteksi locale -> mata uang, konversi IDR, format harga), `scripts/match/topup_voucher.gd` (format `MA-`, allowlist `voucher_codes.txt`), `scripts/match/topup_flow.gd` (mesin fase select/processing/paying/success/redeem, grant + riwayat + cap 50), `scripts/net/topup_client.gd` (HTTPRequest ke `/api/topup/create|status|qr`, timeout 6 s), `scripts/ui/topup_panel.gd` (dialog modal di atas Hero Shop, keypad voucher, QR); oracle `topup_source_oracle.py` menjalankan modul sumber asli + metode Menu yang dipanen `ast` + `server/app.py` mode MOCK |
| `LevelIntroScreen.draw()` (`_render.py` 2761-3391) | **Terport (layer 9av)** — `scripts/ui/level_intro_layout.gd` (op list murni: darken, tint tema 33+forest, vignette 60 cincin, pembatas + 3 berlian, kolom level dengan angka 200 px + 6 bayangan, bar kesulitan, koin reward/starting gold, kolom boss dengan pill tag, aura berdenyut, 12 sinar, siluet tubuh/inner/duri, mata bercahaya, nama + 5 bayangan, judul, PREPARE FOR BATTLE + ikon warn, prompt PRESS SPACE berdenyut + panah) dirender `prototype_view._draw_intro_op`; oracle `level_intro_draw_source_oracle.py` menjalankan kelas ASLI di bawah shim pygame perekam |
| WaveAnnouncer + PathPreview visual (`_render.py`) | **Terport (layer 9aw)** — banner lengkap: gradien 80 strip, border emas ganda, 40 diagonal, corner ticks, judul berbayang + subtitle; panah lane segitiga kini memakai geometri hasil gambar sumber (termasuk pembulatan floor Python). Oracle `wave_announcer_source_oracle.py` memaku kotak visual; `path_preview_source_oracle.py` memaku semua vertex panah dan fase animasi. Tetap prosedural, tanpa aset hero final. |
| AchievementPopup ikon (`_render.py::AchievementPopup._draw_icon`) | **Terport (layer 9ax)** — ikon star/sword/skull/shield/gold berikut lencana lingkaran/warna alpha dan fallback; oracle menjalankan method sumber dan membandingkan primitive fixture lewat `AchievementPopupChecks`. |
| HitParticle sprite (`_render.py::HitParticle`) | **Visual dilengkapi (layer 9ay); digambar dari daftar op sumber sejak layer 9bg (`hit_particle_layout.gd`)** — mempertahankan gerak/umur yang sudah terport, menggambar ulang lingkaran warna + inti putih dari sprite sumber dengan ukuran mengikuti lifetime; oracle merekam primitive `pygame.draw.circle` asli dan suite memaku warna, radius, pusat, serta skala inti. |
| FloatingText presentation (`_render.py::FloatingText.draw`) | **Visual dilengkapi** — renderer memakai anchor integer dan font size ter-clamp dari sumber, teks ber-shadow ber-offset (1,2), warna alpha dan body style normal/critical; oracle menjalankan `draw()` cached-surface path dengan fake font/surface perekam dan fixture mengunci kedua blit. |
| KillFeed draw (`_render.py::KillFeed.draw`) | **Terport (layer 9bb)** — `scripts/ui/kill_feed_layout.gd::ops(entries, screen_w, measure)`: alpha fade-in 15 tick / hold / fade-out 45 tick, slide-in 100 px, kotak latar `inflate(12, 4)` hitam alpha/2, border membulat r=3 warna tim alpha/2, teks 22 px rata kanan di (layar-20, 250+int(y_offset)); dirender `prototype_view._draw_kill_feed`; oracle `kill_feed_draw_source_oracle.py` menjalankan kelas ASLI di bawah shim pygame perekam (31 frame, 192 op). |
| ComboCounter draw (`_render.py::ComboCounter.draw`) | **Terport (layer 9bc)** — `scripts/ui/combo_counter_layout.gd::ops(state, screen_w, measure, cheap_alpha)`: bar timer 80x4 di (layar-140..-60, 140) dari 2 kill, teks `xN` `int(48*display_scale)` px berpusat di (layar-100, 100) dengan bayangan 8 arah (`cheap_alpha`) atau (2, 2), label tier 24 px di (layar-100, 70) dari 5 kill, warna tier 5/10/15/20 dan lerp flash `color_flash/20` ke putih; dirender `prototype_view._draw_combo_counter`; oracle `combo_counter_draw_source_oracle.py` menjalankan kelas ASLI di bawah shim pygame perekam (52 frame, 426 op). |
| BossIntroCinematic draw (`_render.py::BossIntroCinematic.draw`) | **Terport (layer 9bd)** — `scripts/ui/boss_intro_layout.gd::ops(intro)`: banner 600x92 (maks `layar-40`) membulat r=10 dengan latar `(10, 10, 18)` alpha `210*alpha/255` dan border 2 px `entrance_color`, 8 garis corner ticks emas `(255, 220, 120)` panjang 12 inset 5 hanya bila alpha > 60, teks tag 24 px / nama 46 px (`title`) / judul ber-kutip 24 px pada `(banner_x + 14, banner_y + 8/26/64)` dengan alpha fade, bar HP 150x12 r=5 (track `(40, 8, 12)`, isi `entrance_color`, outline putih 1 px) yang TIDAK ikut fade; dirender `prototype_view._draw_boss_intro` lewat `_draw_banner_op`; oracle `boss_intro_draw_source_oracle.py` menjalankan kelas ASLI di bawah shim pygame perekam (22 frame, 279 op). |
| BossDeathAnimation celebration (`_render.py::BossDeathAnimation._draw_celebration`) | **Terport (layer 9be)** — `scripts/ui/boss_celebration_layout.gd::ops(anim, ticks, measure, cheap_alpha)`: `darken` 180 (fade-in <15 %, fade-out >85 %), tint `(80, 60, 20, 40)` sampai 85 %, `BOSS DEFEATED!` 66 px `title` (emas, 6 bayangan hitam alpha maks 80 atau 1 tanpa `cheap_alpha`) memantul 60 px sampai 30 %, nama 46 px `entrance_color` + bayangan (+2, +2), judul ber-kutip 32 px, hadiah `+ N GOLD` + koin (r=10) + `HERO UNLOCKED!` + 2 bintang `draw_icon("star", s=0.5)` setelah 30 %, 6 percikan setelah 40 %, hint `[SPACE] to continue` setelah 50 %; dirender `prototype_view._draw_boss_celebration`; oracle `boss_celebration_draw_source_oracle.py` (20 frame, 547 op). |
| BossDeathAnimation death sequence (`_render.py::BossDeathAnimation._draw_death_sequence`) | **Terport (layer 9bf)** — `scripts/ui/boss_death_sequence_layout.gd::ops(anim)`: `flash` aditif `int(200*(1-t/15))`, per gelombang cincin lebar 3 `range(r, r-20, -3)` alpha `alpha*r/radius` + inti `max(1, r-15)` alpha/2 di (boss+2, boss+2), badan `boss_color` + inti `entrance_color` alpha/2 selama progress <0.5, fragmen persegi berotasi + tepi 1 px `entrance_color` sampai alpha <10, partikel jiwa glow `size+2..1` + inti putih; petunjuk painter `covered` / `ring_inner` untuk timpa-piksel SRCALPHA; dirender `prototype_view._draw_boss_death_animation` (paling akhir, screen space); oracle `boss_death_sequence_draw_source_oracle.py` (12 frame, 2299 op). |
| DeathExplosion + HitParticle draw (`_render.py::DeathExplosion.draw`, `HitParticle.draw`) | **Terport (layer 9bg)** — `scripts/ui/death_explosion_layout.gd::ops(explosion)` + `scripts/ui/hit_particle_layout.gd::ops(particle)`: kilat = cakram `(255, 255, 200, int(200*i))` radius `int(20*i)` + inti putih `(255, 255, 255, int(255*i))` radius `size // 2` di `int(x), int(y)` selama 8 tick (`i = timer/8`); percikan = cakram warna radius `base` + inti putih `max(1, base // 2)` diskalakan `current_size / base`, alpha permukaan `int(255 * lifetime / max_lifetime)`, di `int(x) - current_size*3//2`; petunjuk painter `ring_inner` / `covered` untuk timpa-piksel; dirender `prototype_view._draw_world_effects` lewat `_draw_death_op`; oracle `death_explosion_draw_source_oracle.py` (25 frame, 582 op). |
| MapRenderer ambient tint (`_render.py::MapRenderer.draw`) | **Terport (layer 9bh)** — `scripts/ui/map_tint_layout.gd::ops(theme, screen, cheap_alpha)` + tabel `TINTS` (54 tema, forest `null`): satu `fill` seukuran peta `(r, g, b, a)` (`cheap_alpha`) atau perkalian `255 - (255 - c) * a / 255` (`BLEND_RGB_MULT`); dirender `prototype_view._draw_map_overlay`, hook baru di `minion_view.gd` tepat setelah lapisan peta dan sebelum markas/unit; oracle `map_tint_draw_source_oracle.py` (108 frame, 106 op). Lapisan peta dinamis (`DynamicRenderer`), dekorasi, dan toko tetap belum diport. |
| Urutan gambar (`_core.py::Game.draw`, `_render.py::EffectManager.draw/draw_ui`) | **Terport (layer 9bi)** — `prototype_view.gd`: `WORLD_LAYER_ORDER` (path preview, efek, tactical) dan `OVERLAY_ORDER` (banner boss, announcer, [combo, kill feed], achievement, level intro, boss death) sebagai satu-satunya sumber urutan di `_draw()`; oracle `draw_order_source_oracle.py` membaca urutan dengan `ast`. |
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

> **Historis.** Rencana ini sudah mendarat dan dikoreksi di layer 9aj (lihat
> "Siluet hero arena — selesai" di bawah); bukan kandidat slice berikutnya.

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

> Hanya state. Visual `KillFeed.draw()` ditutup di layer 9bb dan visual
> `ComboCounter.draw()` di layer 9bc (bagian "Slice 9bb" / "Slice 9bc" paling
> bawah).

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

- Seluruh visual utama WaveAnnouncer kini digambar oleh renderer Godot;
  geometri panah PathPreview dipusatkan ulang dari surface 20×20 pygame ke
  koordinat dunia.
- `_ease_out_back` sengaja diduplikasi dari `popup_animation.gd` agar tiap
  port berdiri sendiri; keduanya dikunci oleh oracle-nya masing-masing.

## Slice 9ax — AchievementPopup (ikon)

Lapisan visual utama WaveAnnouncer + PathPreview selesai pada 9aw. Slice 9ax
melengkapi ikon achievement untuk star, sword, skull, shield, gold, dan fallback.

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
  saat sumbernya tidak menggambar glow sama sekali. `icon_ops()` memaparkan
  geometri sumber untuk star/sword/skull/shield/gold; renderer menggambar semua
  primitives dan fallback tetap memakai lencana lingkaran.
- Oracle menjalankan draw icon asli dan fixture mengunci warna, titik, ukuran,
  stroke, lingkaran, serta simbol `$` untuk semua tipe dan fallback.
- Oracle menjalankan 760 tick dengan 4 unlock (tick 0/10/20/190): tick 10 dan
  20 mengantre di belakang popup yang sedang tayang (antrean memuncak di 2),
  lalu popup berganti tepat di tick 180/360/540 dan antrean habis di tick 720.

## Slice 9ba — AchievementPopup (panel)

Panel selain ikon kini digambar oleh `PrototypeView`: 60 baris gradien dark-gold,
outline emas membulat (radius 6 dan 5), corner ticks saat alpha > 60, label
header dengan letter spacing, title/description yang di-fit dengan ellipsis,
dan glow rounded berwarna emas pada 30% awal slot. Warna dan alpha mengikuti
sumber tanpa mengubah ikon 9ax atau state/replay dari popup.

`achievement_popup_source_oracle.py` merekam operasi dari `draw()` asli pada
fase fade-in dan hold, serta teks panjang untuk memastikan fallback ellipsis.
`achievement_popup_checks.gd` membandingkan geometri, warna, opacity, label,
glow, dan ukuran hasil clipping; validator mem-pin wiring renderer/fixture,
dan workflow tetap menjalankan source oracle sebelum Godot suite.

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

## BossIntroCinematic (state + getter; draw ditutup di layer 9bd)

> Bagian ini mencatat state dan getter (layer lama). Visual `draw()` ditutup
> di layer 9bd (bagian "Slice 9bd" paling bawah); daftar "Yang sengaja tidak
> diport" di bawah sudah dikoreksi.

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

- ~~Pixel drawing~~ (sudut emas `corner_ticks`, background rounded-rect, pengisian
  bar HP): kini digambar, layer 9bd.
- Siluet boss, aura, dan sinar (`_draw_boss_silhouette`, `_draw_true_boss_silhouette`,
  `_draw_mini_boss_silhouette`): **koreksi 9bd** — tidak pernah dipanggil dari
  `draw()` (kode mati seperti tiga helper di bawahnya), jadi bukan gap migrasi.
- `_draw_boss_text`, `_draw_hp_preview`, dan `_draw_skip_hint` tidak pernah
  dipanggil dari `draw()` (kode mati di sumber), jadi tidak diport.
- Pemanggil yang membuat banner dari `Boss` hidup (`_core.py` di dua tempat)
  belum ada di Godot; saat ini banner hanya bisa dibuat dari fixture/test.

## Slice 9ay: HitParticle sprite

Logika gerak/umur HitParticle, suite replay dan oracle state sudah ada. Slice
9ay menutup detail visual yang tertinggal: sprite pygame sumber menggambar
lingkaran berwarna lalu inti putih, tetapi renderer Godot hanya menggambar
lingkaran luar. `prototype_view` kini menggambar ulang kedua lapisan sebagai
geometri vektor; radius inti mengecil sesuai skala sprite/lifetime.

Oracle mengeksekusi constructor sumber dan merekam ukuran sprite serta kedua
panggilan `pygame.draw.circle`; kasus tanpa velocity tetap merekam hasil
`random.uniform` seed sehingga replay state tidak berubah.

- `tests/hit_particle_source_oracle.py` → fixture state + primitive sprite
- `scripts/ui/hit_particle.gd` + `tests/hit_particle_checks.gd`
- Suite sudah terdaftar di `run_all.gd`; oracle sudah terdaftar di workflow CI.

## FloatingText / damage number

Logika gerak/drift/lifetime FloatingText dan suite state sudah ada. Slice visual
ini melengkapi gap renderer: sumber mem-blit shadow gelap di offset `(1,2)` lalu
teks berwarna di pusat integer, mengatur alpha terpisah (`min(220, alpha)` untuk
shadow), serta mengecilkan cached font ke ukuran clamp 8–64. Renderer Godot kini
menggambar pasangan teks tersebut memakai font size, anchor, warna, dan alpha
yang diungkap `presentation_state()`; critical diberi penebalan visual ringan.

Oracle tidak mengimpor `_render` karena circular import. Ia mengeksekusi kelas
asli dengan fake font/surface dan menjalankan `draw()` cached-surface path,
kemudian merekam pasangan blit di sampel normal, critical, dan heal.

- `tests/floating_text_source_oracle.py` → fixture motion + draw samples
- `scripts/ui/floating_text.gd` + `tests/floating_text_checks.gd`
- Suite/oracle telah terdaftar di `run_all.gd` / workflow CI.

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
  `DeathExplosion`) serta screen overlays (`_draw_wave_announcer`,
  `_draw_combo_counter`, `_draw_kill_feed`, `_draw_achievement_popup` dengan glow
  awal slot, `_draw_boss_intro` dengan subtitle & border alpha, dan
  `_draw_level_intro` dengan theme tint, difficulty bars, gold/passive, boss
  preview). `_draw_boss_death_animation` (fase kematian 9bf lalu perayaan 9be)
  dipanggil paling akhir di screen space. `overlay_draw_summary()` memaparkan
  ringkasan state-nya.
- **Scene & Runtime Checks** — diuji di `effect_manager_checks.gd`,
  `map_renderer_checks.gd`, `sprite_cache_checks.gd`, `render_cache_checks.gd`,
  `level_intro_screen_checks.gd`, `boss_intro_cinematic_checks.gd`,
  `boss_death_animation_checks.gd`, `death_explosion_checks.gd`,
  `popup_animation_checks.gd`, `screen_shake_checks.gd`, `kill_feed_checks.gd`,
  `achievement_popup_checks.gd`, `boss_death_pause_scene_checks.gd`, dan
  `forge_scene_checks.gd`.

## Batas scope

- Pada checkpoint ini belum ada portrait hero lain selain Kaizen + Thorne + fallback generik; catatan historis ini dikoreksi pada 9bw–9bx untuk portrait Vex dan Sylara.
- `lighting.py` semula tidak diport (post-process per-piksel vs vektor).
  **Dibuka pengguna 2026-10-16 ("migrasi penuh, buka semua pembatas")** →
  layer 9aq: matematika mask diport eksak, pengecatan vektor sebagai adaptor
  (lihat seksi "Lighting pass (layer 9aq)" di akhir dokumen).
- Kelas state di `scripts/ui/` mempertahankan state/getter murni tanpa objek
  Surface/Font pygame, sementara penggambaran vektor dilakukan secara native di
  `PrototypeView` (`scenes/prototype/prototype_view.gd`).
- Klaim "AIPlayer penuh belum ada" di `HERO_MIGRATION_PROGRESS.md` **sudah
  usang**: AI terport lintas 9 modul (`ai_build/controller/draft/
  hero_control/items/policy/recruitment/shields/upgrades`, 52 fungsi) dengan
  `ai_controller.tick()` sebagai entry.
- Top-up flow Python dan voucher allowlist tidak disentuh (saat itu; kini terport di layer 9au).
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

## Wiring 60 situs shake cast terakhir — roadmap 9ao TUNTAS (layer 9ao-4)

Sub-slice penutup roadmap 9ao: SEMUA 60 situs `_shake_screen` dari 53 method
sisanya kini dirutekan lewat `BossAI._shake`, sehingga seluruh tabel 128 situs
(2 enrage + 126 cast) ter-wire — 127 call site native (`_gorath_r` dua
gerbang):

- Enam keluarga 8u (helper cast tanpa guard, shake di ekor cabang): abaddon
  Q 10 / W 12 (setelah heal perisai) / E 8 / R 20; ancient_apparition Q 10 /
  E 15; ignis_drachorn W 15 / E 10 (setelah heal 20%) / R 28 (setelah heal
  25%); gornak Q 10 / W 8 / E 12 / R 20; morgath Q 10 / W 8 / E 10 (setelah
  heal 8%) / R 15 (setelah heal 15%); drakar Q 12 (cabang self-enrage,
  setelah heal 10%) / W 15 / E 18 / R 25.
- Line-AOE bersyarat (sumber early-return TANPA shake saat target hilang atau
  dist 0; shake hanya di jalur tembak): cabang native direstruktur ke bentuk
  early-return sumber (ekuivalen gameplay — `normalized()` nol tidak
  menghasilkan hit) — ancient_apparition W chilling 8 / R cold feet 25,
  ignis_drachorn Q dragon breath 12, kunkka Q tide bringer 15 (cabang native
  sudah early-return, cukup append).
- Tujuh keluarga guard: malzareth Q 14 / W 12 / E 10 / R 22; akashari Q 14 /
  W 12 / E 16 / R 25; vorenmarr Q 12 / W 8 / E 18 / R 25; vhorethzir Q 10
  (whiff >300) / 14 (hit) + W 12 (whiff >320) / 16 (hit) + E 14 + R 30;
  vaerith Q 8 (whiff >280) / 10 + E 10 (whiff >220) / 14 (setelah lifesteal)
  + W 12 + R 24; vhyssarion W 8 (whiff >300) / 12 + Q 14 + E 16 + R 26;
  gravewake Q 12 (guard target hilang) / 12 (guard dist-0) / 15 (hit) + W 14
  + E 10 + R 25. Guard whiff memakai inversi pembungkus `closest` (pola
  xirthalis E 9ao-2); vhorethzir W sekaligus memulihkan cek `> 320` sumber
  yang dulu hilang di port (paritas sumber; cabang `nearby >= 2` membuat
  jalur itu praktis tak tercapai).

Pin: oracle/fixture kini 126 baris wired / 0 sisa, multiset 127 == native;
validate memin hitungan 127; suite menaikkan pin shape ke 126/0, wired_rows
128, dan menambah dua probe replay hidup (gravewake Q whiff target-hilang →
intensity 12.0; vhyssarion W whiff closest-hilang → 8.0).

Roadmap shake 9ao SELESAI: 128/128 situs (2 enrage + 126 cast). Tidak ada
baris `wired:false` tersisa di fixture.

Batas slice 9ao-4: 60 insert `_shake` + 4 restruktur early-return line-AOE +
5 inversi guard closest (semua ekuivalen gameplay kecuali pemulihan guard
>320 vhorethzir W menuju paritas sumber) + oracle/fixture/suite/pin/docs.
`lighting.py`, sumber Python, balance, UI tidak disentuh. Hero tetap
prosedural (keputusan pengguna).

## Baseline balance terukur dipaku CI (layer 9b, rebalance v1)

Permintaan pengguna membuka kunci rebalance dijawab dengan lapisan dasar yang
mengukur, bukan mengubah angka: katalog produksi diaudit dengan alat proyek
sendiri (`tools/balance_audit.py --ingame`, rumus identik dengan pass
`hero_balance.py`) dan hasilnya SEHAT — violations [] (corr(HP,DPS) 0.535,
identity spread 1.64x, school ratio 1.000/1.001, boss pref 1.49, price spread
1.89x, pool power delta 1.000/1.000, starter gap 5.67x, balance pass 216
hero). Karena tidak ada pelanggaran terukur, TIDAK ada angka hero/boss yang
diubah; yang dibangun adalah infrastruktur agar setiap rebalance berikutnya
harus menggerakkan metrik secara sengaja:

- Oracle baru `tests/balance_baseline_source_oracle.py`: menjalankan audit
  headless (stub pygame MagicMock via PYTHONPATH + SDL dummy — tanpa engine,
  tanpa display, tanpa pygame terpasang), memaku saklar hero_balance
  (REBUDGET on, SCHOOL_MOD off, CATCHUP on) dan snapshot metrik persis ke
  fixture `tests/fixtures/balance_baseline_ingame.json`.
- Suite native baru `tests/balance_baseline_checks.gd` (terdaftar di
  `run_all.gd`): violations kosong, 222/216 hero, band target alat, pin
  snapshot (corr/spread/boss-pref/price/starter/multiplier pass/level curve)
  dan enam sel identity grid.
- Baris CI baru di `godot-rebuild.yml` + pin validate (preload/run suite,
  fixture ada, fixture tidak drift dari oracle, kontrak ada).
- `BALANCE_CONTRACT.md` baru: doktrin 4 aturan (audit mengukur; sumber
  read-only; baseline dipaku CI; rebalance = pergerakan metrik disengaja
  dengan angka sebelum/sesudah) + tabel baseline + catatan Troll lab tetap
  paritas sumber yang sengaja.

Temuan audit sampingan (tidak diubah — paritas sudah benar): regen minion
produksi SUDAH tick di native (`minion_battle.gd:175` dipakai bersama oleh
prototype_battle lewat siege_battle, termasuk interaksi anti-heal dan skala
nexus `scaled_minion_definition` — cermin `_entity.py:5534` + `:5422`).

Batas slice 9b: oracle/fixture/suite/registrasi/kontrak/docs saja — NOL
perubahan angka gameplay. `lighting.py`, sumber Python, art tidak disentuh.
Rebalance angka menunggu arahan desain eksplisit (kandidat terukur: starter
gap 5.67x, sel PHYSICAL|TANK 1.38, regen Troll lab).

## Lapisan override rebalance native, tabel kosong by decision (layer 9c)

> (Catatan 9c-S3: tabel tidak lagi kosong — entri arahan 2026-10-16 S1–S3
> tercatat di tiga seksi "Rebalance terarah" di akhir dokumen.)

Menutup domain rebalance yang dibuka pengguna: sesudah baseline terukur (9b)
menunjukkan NOL pelanggaran target yang ditegakkan audit, slice ini membangun
MEKANISME perubahan angka tanpa mengubah satu angka pun:

- Modul baru `scripts/data/balance_overrides.gd`: satu-satunya permukaan
  native untuk deviasi rebalance yang disengaja. `HERO_OVERRIDES` kosong by
  decision (deviasi band prosa 0.84/1.38 adalah trade yang diterima pass
  balance sumber 2026-08-30; tanpa arahan playtest, mengubahnya = opini).
  Kontrak entri: `damage_mult`/`hp_mult` default 1.0 + `reason` wajib;
  reader murni menolak non-numerik/<=0/non-finite ke 1.0.
- Titik aplikasi hanya produksi: `prototype_battle._spawn_production_hero`
  merutekan keempat spawn hero produksi (Kaizen biru/merah awal, purchase
  biru, purchase merah/AI); multiplier diterapkan ke base_hp/base_damage
  sebelum `apply_level_stats()` ulang. Lab tempur tetap memanggil
  `spawn_hero` langsung — paritas sumber lab tidak bergeser.
- Suite baru `balance_override_layer_checks.gd` (run_all.gd): tabel kosong
  dipaku, entries_without_reason() kosong, default 1.0/1.0 untuk id nyata &
  tak dikenal, tujuh kasus reader sintetis (termasuk NAN/negatif/nol/string),
  dan bukti no-op end-to-end: spawn terute stat-identik dengan spawn
  langsung (.tres utuh, hp penuh).
- Pin validate: preload suite, tabel kosong, preload BalanceOverrides di
  prototype, dan tepat 5 kemunculan `_spawn_production_hero(` (definisi +
  4 call site). BALANCE_CONTRACT.md mendapat seksi mekanisme 9c.

Batas slice 9c: NOL perubahan angka gameplay (tabel kosong; wrapper no-op
terbukti). Sumber Python, `.tres`, fixture 9b, `lighting.py`, art tidak
disentuh. Entri rebalance pertama di masa depan wajib: reason + regenerate
baseline + angka sebelum/sesudah di PETA.

## Rebalance terarah S1: starter catch-up produksi (layer 9c, entri pertama)

Arahan pengguna 2026-10-16: starter gap 5.67x -> <= 4.0x lewat entri
`balance_overrides.gd` untuk enam hero starter (kaizen, thorne, grimjaw,
sylara, vex, zephyr), `damage_mult` saja.

- Pengukuran (rumus audit `tools/balance_audit.py` starter_gap, dijalankan
  headless dengan stub pygame): unlock avg dps 486.1; starter avg 85.7 (gap
  5.67x). Multiplier damage hanya menggerakkan porsi auto-attack (skill
  tidak ikut, cermin `apply_level_stats`), sehingga estimasi linear 1.42
  tidak cukup; sapuan 0.01: 1.45 -> 4.12x, 1.49 -> 4.00x (tepi), **1.5 ->
  3.97x**. Dipilih 1.5 (bulat terkecil yang lolos). Depois: starter avg
  dps 122.5, gap **3.97x**. Damage produksi: kaizen 45->68, thorne 41->62,
  grimjaw 42->63, sylara 57->86, vex 43->65, zephyr 34->51; HP tetap.
- Suite `balance_override_layer_checks.gd`: pin enam entri (mult 1.5, hp
  1.0, reason berisi "5.67x -> 3.97x"), non-starter tetap 1.0/1.0, dan
  bukti spawn: `_spawn_production_hero(KAIZEN)` damage 68 vs `spawn_hero`
  langsung 45 (hp/skill identik, hp penuh).
- Opt-in per dunia: `Prototype.balance_overrides_enabled` (default false)
  dinyalakan hanya oleh alur match playable (`app.gd` ->
  `PrototypeSession.enable_balance_overrides()` sebelum `_ready`/setup_arena).
  Dunia yang dibangun langsung oleh suite paritas-sumber dan lab tetap
  memakai stat `.tres` sehingga fixture Python (ai_upgrade dkk.) tidak
  bergeser; suite override memaku flag mati -> 45 dan flag hidup -> 68.
- Pin validate: `STARTER_DAMAGE_MULT := 1.5`, enam entri, tepat enam
  reason S1, flag opt-in + pemanggilan app.gd + method session.
  BALANCE_CONTRACT.md: tabel "Rebalance terarah" antes/depois.

Batas S1: fixture 9b tidak diubah (override native tidak terlihat audit
sumber); `.tres`, sumber Python, lab tempur, `lighting.py` tidak disentuh.

## Rebalance terarah S2: nerf sel PHYSICAL|TANK produksi (layer 9c)

Arahan pengguna 2026-10-16: power sel PHYSICAL|TANK 1.38 -> <= 1.25 lewat
entri override untuk hero-hero sel itu (39 hero: akaroth ... zhyvrek, daftar
dipaku `PHYSICAL_TANK_IDS` di suite).

- Pengukuran (hemat): baris hero audit `--ingame` diambil headless (stub
  pygame), sel via `hero_archetypes.get_archetype`, kandidat multiplier
  diterapkan ke dps/ehp baris sel, lalu power sel + identity spread + corr +
  school ratio + price spread + pool delta dihitung ulang dengan rumus
  audit. Hasil: damage_mult 0.90 -> 1.29, 0.88 -> 1.28, 0.86 -> 1.26,
  **0.85 -> 1.25**; hp_mult sendirian baru 1.27 di 0.5 (corr -0.03);
  campuran tidak lebih kecil. Dipilih `damage_mult 0.85` seragam (hp tetap).
- Antes -> depois: power sel 1.38 -> 1.25 (avg dps 646.2 -> 571.0, ehp
  3069 tetap); identity spread 1.64x -> 1.47x; corr 0.535 -> 0.484; school
  ratio 1.000/1.001 -> 1.045/1.094; price spread 1.89x -> 1.85x; pool dps
  0.972 / ehp 1.000; sel lain bergeser <= 0.01. Violations tetap [].
- Suite `balance_override_layer_checks.gd`: 39 entri (mult 0.85, hp 1.0,
  reason "1.38 -> 1.25"), tabel = 6 + 39, bukti spawn produksi Akaroth
  damage 320 -> 272 (hp paritas, hp penuh). Pin validate: konstanta 0.85,
  S2_REASON, tepat 39 reason S2, lima entri sampel. Kontrak: baris S2 di
  tabel "Rebalance terarah".

Batas S2: fixture 9b tidak diubah; `.tres`, sumber Python, lab, `lighting.py`
tidak disentuh.

## Rebalance terarah S3: regen Troll produksi 0.6 -> 0.15/tick (layer 9c)

Arahan pengguna 2026-10-16: turunkan regen Troll HANYA di jalur produksi;
lab tetap paritas sumber 0.6 (kontrak QA `COMBAT_CONTRACT.md`).

- Permukaan minion baru di `balance_overrides.gd`: `MINION_OVERRIDES
  {"troll": {"regen_per_tick": 0.15, "reason": ...}}` + reader
  `minion_definition_for(definition)` yang mengembalikan resource yang SAMA
  bila tak ada entri, atau DUPLIKAT dengan nilai ditimpa (pola
  `scaled_minion_definition`; `.tres`/definisi lab tidak pernah dimutasi).
  `entries_without_reason()` kini memeriksa kedua tabel.
- Titik aplikasi: `prototype_battle._spawn_match_minion` (gelombang
  produksi) memakai duplikat itu bila `balance_overrides_enabled` (opt-in
  alur match playable dari S1); skala tier nexus tetap mengalikan di
  atasnya. Nilai: 0.15 < dps Orc 13/60 ~ 0.217 per tick sehingga duel bisa
  selesai (antes 0.6 = 36 HP/s, depois 0.15 = 9 HP/s).
- Suite `balance_override_layer_checks.gd`: pin entri + reason, orc 13 dmg
  sebagai batas, `.tres` tetap 0.6, duplikat != resource sumber dengan stat
  lain utuh, wave troll opt-in regen 100 -> 100.15, tanpa opt-in definisi
  preload tetap, lab `minion_battle.spawn_unit` regen 100 -> 100.6. Pin
  validate: entri 0.15, duplicate(), routing di `_spawn_match_minion`,
  `.tres` 0.6. COMBAT_CONTRACT.md catatan Troll: rebalance produksi
  terpasang, lab tetap paritas.

Batas S3: fixture 9b, `.tres`, sumber Python, lab, `lighting.py` tidak
disentuh. S1-S3 menutup arahan rebalance 2026-10-16.

## Lighting pass `lighting.py` (layer 9aq) — pembatas dibuka pengguna

Arahan 2026-10-16: "lakukan migrasi penuh, buka semua pembatas, kecuali
render hero tetap prosedural". Satu-satunya modul sumber yang tercatat belum
terport adalah `lighting.py` (pass pencahayaan per-sprite: gradien arah,
rim light, terminator dua band, semua dari mask alpha, cahaya kiri-atas).

- Oracle baru `tests/sprite_lighting_source_oracle.py`: menjalankan fungsi
  SUMBER ASLI (`_canonical`, `contour_masks`) di bawah shim pygame
  dict/set (Surface.set_at/get_at, Mask draw/erase/count) — tanpa pygame,
  tanpa stub nilai. Fixture `sprite_lighting_source.json`: semua konstanta
  (LIGHT_DIR (-1,-1), RIM_ADD (30,26,44), SHADE_MUL 168, BAND2_RATIO 0.42
  → band-2 218, MASK_ALPHA 170, GRAD 205/255/22, 28 langkah, lantai 24
  piksel), grid kanonik 28x28 (mul + add), dan set piksel rim/shade/
  outer-rim/band-2 untuk tiga bentuk (persegi 8x8, L, "tiny" 20 piksel →
  ditolak).
- Modul native `scripts/ui/sprite_lighting.gd`: matematika mask EKSAK
  (`gradient_t/mul/add`, `canonical_table`, `rim_shade_cells`,
  `band2_cells`, `band2_mul`) + adaptor vektor karena Godot menggambar
  poligon, bukan surface: `point_t` (posisi gradien kontinu di kotak
  acuan), `lit_color` (mult + sheen, alpha utuh), `rim_color` (ADD),
  `shade_color` (MULT 168 / 218), `classify_edges` (normal keluar vs arah
  cahaya, independen winding), `inward_normal`, `should_light` (luas < 24
  px → datar, cermin `solid.count() < 24`), `circle_points` (badan boss
  32-gon). Tanpa aset — hero tetap prosedural (ini shading, bukan art).
- View `prototype_view._draw_lit_polygon`: `draw_polygon` dengan warna per
  vertex (gradien atas kotak poligon sendiri — jalur hero sumber menerangi
  crop rapat), garis 1 px band-1 + band-2 di tepi bayangan (offset normal
  ke dalam 0.5/1.5 px), garis rim 1 px di tepi cahaya. Dipakai untuk siluet
  hero (`HeroMarker.silhouette`) dan badan boss (menggantikan
  `draw_circle` datar). Varian `rim_add` per-boss sumber (mis. level2
  (46,18,16)) tidak ikut: boss Godot adalah badan generik, jadi memakai
  default RIM_ADD.
- Suite `tests/sprite_lighting_checks.gd` (run_all.gd): konstanta, 784 sel
  grid kanonik sel-demi-sel, set piksel tiga bentuk (rim/shade/outer/band-2
  + penolakan tiny), klasifikasi tepi persegi (atas/kiri rim, kanan/bawah
  shade, dua winding), normal ke dalam, lantai luas, `point_t`, angka warna
  (122/127, 80, 130/126/144, 66/85), warna vertex, 32-gon boss, dan wiring
  view. Pin validate: suite + baris CI oracle + fixture tidak drift +
  konstanta + wiring view + modul bebas aset.

Catatan paritas visual: hasilnya *setara komposisi* (arah cahaya, kekuatan
rim/terminator/gradien identik angka) — bukan identik piksel, karena sumber
bekerja pada bitmap sprite sedangkan Godot pada poligon vektor.

## SFX tempur `mobile/combat_audio.py` (layer 9ar)

Audit lanjutan arahan "migrasi penuh" menemukan berkas suara serangan
(`hero_melee/hero_ranged/tower_*/minion_hit`) sudah ada di `assets/audio`
tetapi tidak pernah dimainkan: sumber memainkannya lewat gate
`mobile/combat_audio.py`, bukan `SoundManager`.

- `scripts/audio/combat_audio.gd`: gate murni + clock-injected (`request()`),
  konstanta `_KONFIG`, `AMBANG_RANGED=100`, anggaran 4/frame (`new_frame()`
  dipanggil `minion_battle.step_tick`), statistik `main/tolak_jeda/
  tolak_anggaran/tolak_channel`, klasifikasi `attack_kind/tower_kind/hero_kind`
  (`is_melee` menang atas jangkauan, seperti `play_hero_basic`).
- Titik panggil = titik sumber: `prototype_battle.hero_basic_attack`
  (`_entity.py:4420`), `siege_battle.fire_projectile` untuk menara
  (`_entity.py:881`, biru 1.0 / merah 0.8), `minion_battle.apply_hit` cabang
  minion (`_entity.py:5588`), `prototype_battle._boss_basic_attack`
  (`base_boss.py:750`).
- `audio_manager.gd`: pool 24 kanal (`play_combat`, `combat_free_channels`,
  `combat_global_volume`); tanpa AudioManager (suite headless) wrapper
  berperilaku seperti cabang `_mati` sumber (tidak memainkan, tidak menghitung).
- Oracle `tests/combat_audio_source_oracle.py` menjalankan modul sumber ASLI
  di bawah shim pygame (jam, kanal kosong, volume SoundManager) dan merekam
  18 keputusan + klasifikasi; `tests/combat_audio_checks.gd` memutarnya ulang.
- Perbedaan sadar: anggaran direset per tick simulasi (60 Hz = frame sumber),
  jadi pada kecepatan permainan >1x budget per frame layar ikut berlipat.

## Panel kanan layar lebar `mobile/sidepanel.py` (layer 9as)

Sumber mengumpulkan sisa lebar layar >16:9 (lebar tampilan maks 2200 px,
panel hanya bila sisa >= 120 px) di kanan arena 1280 px dan mengisinya
dengan tombol JEDA, kotak STATUS (emas/mode/level/wave), daftar HEROES
(nama, level, bar HP, titik Q/W/E/R) dan tombol TACTICAL COMMANDS.
Notifikasi/kill feed sudah dihapus pengguna di sumber (no-op) - tidak diport.

- `scripts/ui/side_panel_layout.gd`: `build(snapshot, panel, measure)`
  menghasilkan daftar gambar yang sama persis dengan `_gambar_status/_hero/
  _tactical` (angka, string, warna, hit box, aturan baris 42/38 px, tutup
  236 px, syarat tombol taktis, warna hold/press), `hit_test` (popup -> hanya
  JEDA), `display_width`/`panel_rect` dari `platform_utils.create_display`.
- `scripts/ui/side_panel.gd`: Control di `HUD`, latar bata
  (`_gambar_panel_samping`), cache 250 ms + segar saat status berubah /
  animasi tekan, sentuhan: JEDA -> `pause_match`, taktis tekan/lepas ->
  `_start_panel_tactical`/`_finish_tactical` (sama dengan tombol HUD).
- `project.godot`: `window/stretch/aspect` `keep` -> `expand`; di 16:9 tidak
  ada perubahan, di layar lebar area kanan menjadi panel dan kotak taktis
  melayang disembunyikan (seperti sumber memindahkan panel melayangnya).
- Oracle `tests/side_panel_source_oracle.py` menjalankan `SidePanel` ASLI di
  bawah shim pygame perekam (glyph 7 px) untuk 5 skenario + 9 hit-test;
  `tests/side_panel_checks.gd` memutar ulang; lebar teks nyata disuntik lewat
  `measure` sehingga posisi rata-kanan/tengah mengikuti font Godot.

## Splash screen `splash_screen.py` (layer 9at)

`main.py` boot ke `STATE_SPLASH`: logo (`assets/logo.png`, dimuat ke kotak
340x320 lalu tumbuh 85 % -> 100 % dalam 0,9 s per 5 %) atau judul teks
bercahaya, subjudul, petunjuk "Tap anywhere to skip", 46 partikel di atas
gradien + vignette yang dipanggang sekali; fade-in 0,4 s, judul mulai 0,5 s
selama 0,6 s, fade-out 0,45 s terakhir dari 3 s; tap -> `skipped`, selesai
saat `elapsed` (sejak boot) >= 0,25 s (tap terlambat = potong langsung,
perilaku sumber dipertahankan).

- `scripts/ui/splash_timeline.gd`: semua angka murni (alpha, done, partikel,
  48 baris gradien, 70 cincin vignette, skala/tumbuh logo dengan pembulatan
  half-even Python, cincin glow, `layout()` dengan `measure` font).
- `scenes/splash/splash_screen.gd` + `SplashScreen.tscn`: `advance(dt)` dengan
  `min(0.05, delta)`, latar dipanggang ke `ImageTexture` sekali (catatan:
  `pygame.draw.rect` TIDAK memadukan alpha, jadi cincin vignette terdalam
  (inset 2, alpha 255) menimpa semuanya - latar sumber efektif hitam dengan
  bingkai gradien 2 px; dipertahankan demi paritas), glow judul
  sebagai outline 24/14/8 px (adaptor vektor dari salinan blur sumber).
- `app/app.gd`: `_install_screen(SPLASH)` saat boot, sinyal `finished` ->
  `show_menu`; suite runtime `run_all.gd` kini boot ke splash, skip, lalu menu.
- Oracle `tests/splash_screen_source_oracle.py` menjalankan `SplashScreen` ASLI
  di bawah shim pygame perekam (18 sampel linimasa, jalur skip, gerak partikel
  120 frame, tata letak dengan/tanpa logo); `tests/splash_screen_checks.gd`
  memutar ulang.

## Top-up / voucher `topup_*.py` + `Menu.topup_*` + klien `server/app.py` (layer 9au)

Dialog TOP UP HERO GOLD sumber dibuka dari Hero Shop (`topup_open`): pilih
paket (`PAKET 50K`: 50.000 gold, Rp 10.000) + metode (GoPay/OVO/DANA/
ShopeePay/Bank), lalu (a) tanpa `MYSTIC_TOPUP_URL` -> fase `processing`
simulasi 1,6 s (97 frame akumulasi float) -> `topup_complete`; (b) dengan URL
-> fase `paying`: POST `/api/topup/create {"pkg"}` -> invoice + GET QR PNG ->
poll `/api/topup/status/<id>` 60 frame pertama lalu tiap 120 frame (atau
tombol "I'VE PAID") -> `settled` + `code` -> `_redeem_grant` otomatis;
`expired`/`cancel` -> pesan gagal; server tak terjangkau -> "Top up server
tidak terjangkau..." + TRY AGAIN. Fase `redeem`: keypad 3x4 (`vpk_*`), kode
`MA-` + maks 6 digit (regex 4-8 digit), pesan "Invalid code..." /
"Code already redeemed." / "Unknown code. Contact admin." (allowlist
`voucher_codes.txt`, tidak ada file = mode demo terima semua kode valid).
Grant: `meta_gold` += jumlah, `redeemed_codes` (cap 50), `topup_history`
(cap 50, tx `MA-` + 10 digit ms epoch, `price_cur` hasil `convert_idr`).

- `scripts/match/topup_currency.gd`: tabel `IDR_PER_UNIT`/simbol/region/
  bahasa identik, `parse_locale_name`, `currency_for`, `detect_currency`
  (`OS.get_locale()` + fallback LANG/LC_*), `convert_idr`, `format_price`
  (pembulatan half-even Python untuk mata uang tanpa desimal, pemisah ribuan
  `{:,}`, IDR memakai titik), `fmt_idr`.
- `scripts/match/topup_voucher.gd`: `is_valid_format`, `parse_allowlist`
  (`CODE` / `CODE=jumlah`, komentar `#`, jumlah non-int dilewati, kosong =
  null/demo), `load_vouchers` (`res://` lalu `user://`).
- `scripts/match/topup_flow.gd`: port 1:1 handler klik (`topup_pay`,
  `topup_paid`, `topup_cancel_pay`, `topup_retry`, `topup_redeem`, `vback`,
  `vpk_*`, `topup_pkg_*`, `topup_method_*`), `tick()` per frame, mesin server
  (`on_http_result` dikonsumsi pada tick berikutnya seperti thread sumber),
  `grant()` bersama. Perbaikan kecil yang disengaja: pembelian simulasi juga
  menyetel `last_method` (sumber membiarkan "redeem" menempel sehingga layar
  sukses berikutnya salah judul).
- `scripts/net/topup_client.gd`: `HTTPRequest` satu per waktu, header JSON
  untuk POST, HTTP >= 400 dihitung gagal (setara `HTTPError` urllib).
- `scripts/ui/topup_panel.gd`: dialog 920x580 di atas Hero Shop, lima halaman
  fase, QR dari bytes PNG, keypad + tombol keyboard (digit/Backspace/Enter/
  Esc); `meta_hero_shop_panel.gd` mendapat tombol TOP UP (`topup_requested`),
  `main_menu.gd` menyambungkan flow + klien + panel dan menyimpan profil lewat
  `SaveSlotStore.save_path`.
- Oracle `tests/topup_source_oracle.py`: mengeksekusi `topup_currency.py` dan
  `topup_voucher.py` asli, memanen metode `Menu.topup_*`/`_redeem_*`/
  `_topup_server_tick` dari `_core.py` dengan `ast` (jam beku, urllib
  terskrip, SoundManager/SaveManager perekam), serta mengimpor `server/app.py`
  di bawah shim Flask (SQLite sementara, MOCK) untuk memaku kontrak JSON.
  Suite `tests/topup_checks.gd` (harga 22 mata uang x 8 nominal, locale,
  allowlist, keypad, 10 skenario submit, cap, 8 alur server) +
  `tests/topup_scene_checks.gd` (tombol TOP UP -> dialog -> simulasi
  -> grant via save callable -> BACK; keypad via tombol).

## Visual `LevelIntroScreen.draw()` (layer 9av)

Sebelumnya hanya state/getter yang terport dan `prototype_view` menggambar
kartu 640x360 pendekatan. Kini seluruh `draw()` sumber diport sebagai daftar
op murni (`scripts/ui/level_intro_layout.gd::ops(state, timer, ticks_ms,
measure, screen)`) yang dipaku per-op oleh oracle (7 frame: dua level,
timer 0/15/31/45/60, tiga nilai `get_ticks`, kesulitan normal/hard/easy).

- Jalur yang dipilih: `mobile.perf.Quality.cheap_alpha = True` (jalur HP:
  vignette ter-cache, 6/5 lapis bayangan teks, 12 sinar aura).
- Metrik font lewat `measure` callable: oracle memakai `int(0.55*size)` px
  per glyph, view memakai `BossFont.get_string_size`; kode tata letak sama.
- `prototype_battle.level_intro_state()` kini juga mengekspos `boss_class`,
  `boss_entrance_color`, `boss_color_dark`, `hp_mult`, `difficulty_id`,
  `screen_w/h`.
- Semantik overwrite pygame pada surface SRCALPHA: cakram aura dan glow mata
  yang digambar besar->kecil saling menimpa, jadi op lingkaran membawa
  `ring_inner` dan view menggambar annulus (bukan cakram bertumpuk). Poligon
  inner siluet (alpha/3 di atas tubuh hitam) tetap diblend normal — deviasi
  kecil yang disadari (sumber memperlihatkan latar lewat area inner).
- `ui_theme.letter/corner_ticks/draw_icon("warn")` dipanen dari `ui_theme.py`
  asli di oracle; port GDScript-nya ada di layout yang sama.


## Slice 9bb — visual `KillFeed.draw()` (layer 9bb)

Sebelumnya hanya state `KillFeed` yang terport; `prototype_view` menggambar
teks 14 px rata kanan karangan di (980, 96+y) tanpa kotak dan dengan fade
berbeda dari sumber. Kini seluruh `draw()` sumber diport sebagai daftar op
murni, `scripts/ui/kill_feed_layout.gd::ops(entries, screen_w, measure)`, tiga
op per entri (kotak latar, border, teks) dalam urutan sumber:

- Alpha: fade-in 15 tick pertama (`int(255 * (max-lifetime)/15)`), hold 255,
  fade-out 45 tick terakhir (`int(255 * lifetime/45)`). Entri baru
  (`lifetime == max`) beralpha 0 sehingga **tidak digambar** sampai `update()`
  pertama. Slide-in `int((1 - progress) * 100)` px dari kanan pada 15 tick yang
  sama.
- Jangkar: `topright = (screen_w - 20 + slide_x, 250 + int(y_offset))`, font
  22 px `body_medium`. Kotak latar = `text_rect.inflate(12, 4)` (6 px kiri/kanan,
  2 px atas/bawah) hitam alpha//2; border 1 px membulat r=3 warna tim alpha//2;
  teks warna tim dengan alpha penuh.
- Oracle `kill_feed_draw_source_oracle.py` memanen `class KillFeed` dengan
  `ast` dan menjalankan `draw()` asli di bawah shim pygame perekam (font
  `int(0.55*size)` px per glyph, tinggi = size). State entri berasal dari
  `add_kill`/`update` asli (lima skenario: satu kill biru dari fade-in sampai
  habis, satu kill merah, tumpukan enam kill dengan cap 5 entri, kill yang baru
  ditambah sebelum `update()`, nama panjang). Fixture
  `kill_feed_draw_source.json` = 31 frame, 192 op; validator meregenerasinya
  dari `_render.py` dan membandingkan.
- `kill_feed_draw_checks.gd` memeriksa tabel fase alpha/slide, mereplay setiap
  frame dari state terekam, mereplay semua frame lewat `KillFeed` produksi
  (jalur `Color` -> RGB dan pemotongan `int(y_offset)` bit-demi-bit), dan
  memeriksa wiring `PrototypeView.kill_feed_draw_ops` dengan metrik font nyata.

Temuan yang ikut dipertahankan karena itu perilaku sumber: `y_offset` mendekati
`target_y` dari bawah dan tidak pernah mencapainya dalam umur entri
(79.99999999999997 di tick 170), jadi `int()` memarkir baris tertumpuk satu
piksel lebih tinggi. Jarak tumpukan 20 px lebih kecil dari tinggi kotak (teks
22 px + 4), sehingga kotak entri bertumpuk; font dinaikkan 16 -> 22 di sumber
tanpa menaikkan langkah tumpukan.

Divergensi yang disadari: `Barlow-Medium.ttf` (gaya `body_medium`) tidak ada di
`assets/fonts` Godot, jadi view memakai Barlow SemiBold dan mengukur teks dengan
metrik Godot (lebar kotak bisa beda beberapa piksel dari pygame; oracle memaku
tata letak, bukan metrik). Border adalah polyline anti-alias yang ditarik
setengah lebar goresan ke dalam (pygame menggores di dalam rect), bukan outline
piksel-presisi. `ComboCounter.draw()` menyusul di layer 9bc.

## Slice 9bc — visual `ComboCounter.draw()` (layer 9bc)

Sebelumnya hanya state `ComboCounter` yang terport; `prototype_view` menggambar
teks "N HIT COMBO" karangan di (1020, 160) tanpa bar timer, bayangan, atau
label tier. Kini seluruh `draw()` sumber diport sebagai daftar op murni,
`scripts/ui/combo_counter_layout.gd::ops(state, screen_w, measure, cheap_alpha)`
(`state_of(counter)` mengambil lima field yang dibaca `draw()`):

- Jangkar: `cx = screen_w - 100`, `cy = 100`. Bar timer 80x4 di
  `(cx - 40, cy + 40)` hanya dari 2 kill (latar `(40, 40, 40)`, isi warna tier
  `int(80 * timer / max_timer)`). Teks `x{count}` berpusat di (cx, cy) pada
  `int(48 * display_scale)` px, **dilewati bila < 8 px — setelah bar digambar**.
  Label tier 24 px berpusat di (cx, cy - 30) dengan bayangan (+1, +1), dari
  5 kill. Tier `>=`: 5 hijau KILLING SPREE!, 10 kuning RAMPAGE!, 15 oranye
  UNSTOPPABLE!, 20 merah GODLIKE!, selain itu putih COMBO. Flash: tiap kanal
  `int(c + (255 - c) * color_flash / 20)`; bar tetap memakai warna tier.
- Bayangan `x{count}`: `cheap_alpha` true = cincin 8 arah (urutan dx lalu dy,
  tanpa (0, 0)), false = satu bayangan (2, 2). Port menerima flag itu; view
  memakai default sumber (`Quality.cheap_alpha = True`, sama seperti 9av).
- Oracle `combo_counter_draw_source_oracle.py` memanen `class ComboCounter`
  dengan `ast` dan menjalankan `draw()` asli di bawah shim pygame perekam (font
  `int(0.55*size)` px per glyph, tinggi = size). `draw()` meng-import
  `mobile.perf.Quality` saat dipanggil, jadi oracle memasang stub `mobile.perf`
  selama berjalan (dipulihkan sesudahnya) dan sengaja **tidak** menyediakan
  `mobile.sidepanel`: `add_kill()` menelan ImportError itu seperti di game tanpa
  panel samping Python. State berasal dari `add_kill`/`update` asli: pendakian
  22 kill tiap 2 tick (semua batas tier, hold dengan bar menyusut, kedaluwarsa
  dan fade-out), tiga frame sebelum `update()` (flash penuh), empat frame
  dengan bayangan tunggal, serta dua kill dalam satu tick. Fixture
  `combo_counter_draw_source.json` = 52 frame, 426 op; validator
  meregenerasinya dari `_render.py` dan membandingkan.
- `combo_counter_draw_checks.gd` memeriksa tangga tier dan lerp flash, mereplay
  setiap frame dari state terekam, mereplay semua frame lewat `ComboCounter`
  produksi, dan memeriksa wiring `PrototypeView.combo_counter_draw_ops` dengan
  metrik font nyata. `prototype_view` juga memakai `HUD_SCREEN_W` dan
  `_measure_hud_text` bersama dengan kill feed (nama generik dari 9bb).

Perilaku sumber yang ikut dipertahankan: satu kill saja sudah menggambar `x1`
(penjaga awal hanya memeriksa `display_scale`, bukan `count`); setelah jendela
120 tick habis `count` menjadi 0 tetapi skala masih meluruh, jadi `x0` putih
ikut tergambar sampai skalanya turun di bawah 8 px (frame 161-172 di fixture);
dan dua kill dalam satu frame menggambar bar timer tanpa teks pada frame
sebelum `update()` pertama.

Divergensi yang disadari: `Barlow-Bold.ttf` (`body_bold`) dan `Barlow-Regular.ttf`
(`body`) tidak dipakai view; semua teks HUD memakai Barlow SemiBold dan metrik
Godot (posisi pusat bisa beda beberapa piksel dari pygame; oracle memaku tata
letak, bukan metrik). Stub `mobile.perf` hanya menyediakan `Quality`; hook
sidepanel (`beri_tahu_global`) tetap tidak diport (lihat bagian KillFeed +
ComboCounter).

## Slice 9bd — visual `BossIntroCinematic.draw()` (layer 9bd)

Sebelumnya hanya state dan getter `BossIntroCinematic` yang terport;
`prototype_view` menggambar rect bersudut siku dengan header karangan
`TAG · NAMA` 20 px, subjudul 14 px tanpa kutip, tanpa corner ticks, dan bar HP
persegi yang ikut memudar. Kini seluruh `draw()` sumber diport sebagai daftar op
murni, `scripts/ui/boss_intro_layout.gd::ops(intro)`. Layout memakai getter yang
sudah terverifikasi oracle state (`get_alpha`, `get_banner_x`, `get_banner_width`,
`get_background_alpha`, `get_hp_bar_rect`, `get_hp_fill_width`, `get_tag`), jadi
kurva fade, slide, dan bar tidak diduplikasi:

- Banner `(banner_x, 12, min(600, layar-40), 92)`: latar `(10, 10, 18)` pada
  `int(210*alpha/255)` dan border 2 px `(*entrance_color, alpha)`, keduanya
  `border_radius=10`. Corner ticks `ui_theme.corner_ticks((255, 220, 120),
  length=12, width=2, inset=5)` — 8 garis, **opaque** (tanpa alpha) dan hanya
  bila `alpha > 60`. Teks di `(banner_x + 14, 12 + 8/26/64)`: tag 24 px
  `body_medium` (TRUE BOSS merah / MINI BOSS kuning), nama 46 px `title` warna
  `entrance_color`, `"judul"` 24 px `(215, 215, 235)`; ketiganya `set_alpha(alpha)`.
- Bar HP `(banner_x + w - 166, 52, 150, 12)` r=5: track `(40, 8, 12)`, isi
  `entrance_color` selebar `int(150 * elapsed / 85)` (tidak digambar bila 0), outline
  putih 1 px. Digambar langsung ke layar, jadi **tidak memudar**: track dan outline
  sudah terlihat penuh pada frame alpha 0 dan tetap penuh sampai intro berakhir
  (kuirk sumber, dipin oracle dan validator).
- Oracle `boss_intro_draw_source_oracle.py` memanen `class BossIntroCinematic`
  dari `_render.py` dan fungsi `corner_ticks` dari `ui_theme.py` dengan `ast`,
  lalu menjalankan `draw()` asli di bawah shim pygame perekam. Boss berasal dari
  `bosses/boss_data.py` asli (`abaddon` true, `drakar` mini). `update()` asli
  mencoba `from _system import SoundManager`; oracle memasang stub `_system` tanpa
  `SoundManager` selama berjalan (dipulihkan sesudahnya) sehingga ImportError itu
  ditelan seperti di game tanpa pygame. Skenario: timeline true boss (tick 0, 1-4,
  8, 12, 18, 40, 70, 81, 90, 95, 96, 99, 100: batas alpha 60 di fade-in dan
  fade-out, selesai slide, awal fade-out, bar penuh, intro berakhir), mini boss
  (tag lain, warna lain), dan layar sempit 480 px (banner 440). Fixture
  `boss_intro_draw_source.json` = 22 frame, 279 op; teks direkam tanpa metrik font
  karena `draw()` tidak pernah mengukur teks.
- `boss_intro_draw_checks.gd` mereplay setiap frame dari state terekam, dari
  `BossIntroCinematic` produksi yang di-tick dengan `update()`, dan lewat
  `PrototypeView.boss_intro_draw_ops` (harus sama persis dengan fixture karena
  tidak ada metrik font); ditambah pin kuirk (bar HP opaque, intro selesai dan
  intro yang di-skip tidak menggambar apa pun). `prototype_view` melukis op lewat
  `_draw_banner_op`: rect membulat penuh = polygon terisi (radius dijepit ke sisi
  terpendek seperti pygame dan jatuh ke rect biasa untuk sliver < 2 px), rect
  membulat bergaris = outline inset milik kill feed, garis dan teks lewat painter
  level intro.

Divergensi yang disadari: nama 46 px (`title_font`, Cinzel) dan tag/judul
(`body_medium`) memakai Barlow SemiBold di view (hanya `style` yang dicatat);
polygon membulat tidak anti-alias seperti `draw.rect` pygame tetapi memakai 5
sampel per sudut, bukan algoritma pygame, sehingga tepi bisa beda sub-piksel;
pygame menimpa piksel di surface SRCALPHA sedangkan Godot memadukan border di atas
latar, jadi border semi-transparan sedikit lebih gelap saat fade. Suara
`nexus_hit` tetap diurus `step_boss_intro()` (tidak berubah).

## Slice 9be — visual `BossDeathAnimation._draw_celebration()` (layer 9be)

Sebelumnya `prototype_view` menggambar overlay datar `(0.02, 0.03, 0.06)` dan teks
karangan `NAMA DEFEATED!` 32 px, judul 18 px, `+N GOLD REWARD` dan hint
`PRESS SPACE OR ESC TO CONTINUE`. Kini seluruh `_draw_celebration()` sumber
diport sebagai daftar op murni, `scripts/ui/boss_celebration_layout.gd::ops(anim,
ticks, measure, cheap_alpha)`. Layout memakai `get_celebration_visual_state()`
(overlay, bounce, hadiah, hint sudah dipin oracle state), jadi kurva tidak
diduplikasi:

- `darken` (alpha 0 = tanpa op) lalu tint `(80, 60, 20, 40)` seukuran layar
  selama `progress < 0.85`. `cx = layar_w // 2`, `cy = layar_h // 2 - 50`.
- `BOSS DEFEATED!` 66 px `title`: bayangan hitam di offset 6..1 (`cheap_alpha`)
  atau satu di 3, `set_alpha(min(alpha, 80))`, berpusat di `(cx + o, cy - 40 +
  drop + o)`; lalu teks emas `(255, 220, 100)`. Nama 46 px `entrance_color` di
  `cy + 30 + drop` (bayangan hitam `alpha // 2` di +2, +2 digambar lebih dulu),
  judul ber-kutip 32 px `body_semibold` `(200, 200, 220)` di `cy + 75 + drop`.
  `drop` = `int((1 - eased) * 60)` selama bounce 30 % pertama.
- Hadiah (setelah 30 %): koin `(255, 200, 50)` r=10 + garis tepi `(200, 150, 30)`
  lebar 2 di kiri teks (digambar opaque, tanpa alpha), `$` 22 px `body_bold`, teks
  `+ N GOLD` 32 px, lalu `HERO UNLOCKED!` (`ui_theme.letter`, 24 px) dengan dua
  bintang `ui_theme.draw_icon("star", s=0.5)`: 4 garis lebar 2 sepanjang ±4 px +
  titik r=1.5, warna `255/180/220 * alpha / 255`. **Kuirk sumber**: baris
  `HERO UNLOCKED!` muncul untuk SETIAP boss true, bukan hanya yang membuka hero.
- Percikan (setelah 40 %): 6 pasang lingkaran emas `int(4 * pulse)` dan putih
  `int(2 * pulse)` di elips 220 x 60 yang berputar dengan `get_ticks()`; hint
  `[SPACE] to continue` 24 px (setelah 50 %) dengan alpha `int(180 * pulse)`.
- `tests/draw_recorder.py` adalah shim pygame perekam bersama untuk oracle 9be-9bi
  (Rect/Surface/Text/Font/Draw, `mobile.perf` darken/flash/Quality, `installed()`
  yang memulihkan `sys.modules`). Oracle memanen `BossDeathAnimation` dan
  `_skip_button_label` dari `_render.py` serta `letter` dan `draw_icon` dari
  `ui_theme.py`; bos berasal dari `bosses/boss_data.py` asli (`abaddon`,
  `alchemist` di layar 960x540). Teks diukur `int(size * 0.55)` px per huruf; view
  memberi metrik Barlow nyata ke layout yang sama.
- `boss_celebration_draw_checks.gd` mereplay 20 frame dari state terekam, dari
  `BossDeathAnimation` produksi (death phase 90 tick lalu `update()`), dan lewat
  `PrototypeView.boss_celebration_draw_ops`; ditambah pin tahap (tint berakhir 85 %,
  hadiah 30 %, percikan 40 %, hint 50 %, `cheap_alpha` tunggal).

Divergensi yang disadari: nama dan judul (`title_font`, Cinzel; `body_*`) memakai
Barlow SemiBold di view; sudut lingkaran koin tidak anti-alias pygame. Kilat
putih fase kematian masih versi lama (slice berikutnya).

## Slice 9bf — visual `BossDeathAnimation._draw_death_sequence()` (layer 9bf)

Sebelumnya `prototype_view` menggambar kilat putih alpha-blend, satu busur per
gelombang, satu lingkaran untuk badan, lingkaran polos untuk fragmen dan partikel,
semuanya di dalam `_draw_world_effects` (world space, ikut goncangan, di bawah HUD).
Kini seluruh `_draw_death_sequence()` sumber diport sebagai daftar op murni,
`scripts/ui/boss_death_sequence_layout.gd::ops(anim)`. Layout memakai
`get_death_visual_state()` (flash, gelombang, dissolve sudah dipin oracle state)
dan membaca fragmen / partikel dari state produksi:

- Kilat: `mobile.perf.flash` = `fill` aditif `(a, a, a)` layar penuh, `a =
  int(200 * (1 - elapsed / 15))`. Godot memakai alpha-blend putih sebagai
  pendekatan (aditif murni butuh material `CanvasItemMaterial` terpisah).
- Gelombang: surface 4 px lebih besar dari radius di-blit di `(boss - radius)`
  sedangkan pusat lingkaran di `(radius + 2)`, jadi seluruh gelombang bergeser (+2, +2).
  Cincin lebar 3 untuk `r in range(radius, max(0, radius - 20), -3)` dengan alpha
  `int(alpha * r / radius)`, lalu cakram inti `max(1, radius - 15)` alpha/2 yang
  MENIMPA cincin di dalamnya (pygame tidak memadukan di surface SRCALPHA); layout
  menandai cincin yang tertutup dengan `covered`.
- Badan (progress <0.5): lingkaran `boss_color` alpha `int(255 * (1 - 2p))` dan inti
  `entrance_color` alpha/2 jari-jari `size // 2` yang menimpa tengahnya (`ring_inner`).
- Fragmen: persegi `±size` diputar `rotation`, isi `color` + tepi 1 px
  `entrance_color` pada alpha `int(255 * life / max_life)`, dilewati bila `life <=
  0` atau alpha <10 (tick 58+ dari 60). Partikel jiwa: cakram glow `size+2 .. 1`
  (alpha `int(alpha * (1 - r / (size + 2)))`, tiap cakram menimpa yang lebih besar
  sehingga jadi cincin 1 px lewat `ring_inner`) dan inti putih r=1, alpha puncak
  `int(200 * life / max_life)`, dilewati di bawah 10.
- Oracle memanen `class BossDeathAnimation` dan menjalankan `draw()` asli di bawah
  `tests/draw_recorder.py`. Fragmen dan partikel acak: tiap skenario menyetel
  `random.seed(1107)` dan menyimpan dict yang dibuat; `boss_death_animation.gd::configure`
  menerimanya sebagai `particle_specs` / `rising_specs`, sehingga checks mereplay
  frame tanpa bergantung RNG. Skenario: true boss (tick 0, 7, 15, 25, 44, 45, 57, 60,
  89: awal/akhir kilat, tiga gelombang, badan hilang di progress 0.5, fragmen
  habis) dan mini boss (2, 30, 58). Fixture 12 frame, 2299 op.
- `boss_death_sequence_draw_checks.gd` mereplay setiap frame dari
  `BossDeathAnimation` produksi yang di-tick (posisi fragmen/partikel dihitung
  `update()`), ditambah pin tahap (kilat, jumlah cincin 4/14/7/0, 50 / 30 polygon,
  batas badan), petunjuk timpa-piksel, dan `PrototypeView.boss_death_draw_ops`.
- Urutan gambar: `_core.py` memanggil `boss_death.draw(self.screen)` sebagai
  pemanggilan TERAKHIR (setelah `level_intro.draw`) di layar tanpa goncangan.
  `_draw_boss_death_animation` kini dipanggil paling akhir di `_draw()`, memuat
  fase kematian lalu perayaan 9be; `_draw_boss_death_sequence` lama dan
  `_draw_boss_celebration` dihapus.

Divergensi yang disadari: kilat aditif = alpha-blend; `covered` / `ring_inner`
meniru timpa-piksel dengan `draw_arc` 1 px, bukan rasterisasi pygame; lingkaran
tidak anti-alias seperti pygame; tepi fragmen digambar sebagai polyline tertutup
di atas isian (tepi pygame menimpa piksel).

## Slice 9bg — visual `DeathExplosion.draw()` + `HitParticle.draw()` (layer 9bg)

Sebelumnya `prototype_view` menggambar kilat ledakan sebagai dua `draw_circle`
berpadu (radius inti `size * 0.5` tanpa pembulatan, pusat float), percikan ledakan
sebagai satu lingkaran tanpa inti putih di pusat float, dan percikan dunia lewat
`core_radius()` (9ay) dengan inti yang berpadu di atas cakram. Kini kedua `draw()`
sumber diport sebagai daftar op murni:

- `scripts/ui/death_explosion_layout.gd::ops(explosion)`: bila `flash_timer > 0`
  dan `size = int(20 * timer / 8) > 0`, dua cakram berpusat `int(x), int(y)`:
  `(255, 255, 200, int(200 * i))` radius `size` lalu `(255, 255, 255, int(255 * i))`
  radius `size // 2` (menimpa, bukan memadu). Lalu tiap percikan lewat
  `hit_particle_layout.gd`.
- `scripts/ui/hit_particle_layout.gd::ops(particle)`: sprite sumber digambar sekali
  di constructor (cakram warna radius `base = max(1, int(size))`, inti putih
  `max(1, base // 2)`) dan di setiap frame diskalakan ke `current_size =
  max(1, int(size * rasio))` lalu di-blit di `(int(x) - current_size*3//2, int(y) -
  current_size*3//2)` dengan `set_alpha(int(255 * rasio))`. Layout menghitung pusat
  dan radius terskala (`half * factor + offset`, `base * factor`, `core * factor`);
  `ring_inner` menjadikan cakram warna sebagai cincin di sekeliling inti, dan
  `covered` menandai cakram yang sepenuhnya tertutup inti (`size` 1).
- `tests/draw_recorder.py` kini memodelkan `pygame.transform.scale` pada geometri
  lingkaran sprite (pusat dan radius dikali faktor). Oracle memanen `HitParticle` dan
  `DeathExplosion` asli, menyetel `random.seed` per ledakan dan menyimpan
  percikan yang dibuat (`particle_specs` untuk `death_explosion.gd::configure`).
  Skenario: ledakan red small (8 percikan), blue medium (15), blue large (25) dengan
  anchor pecahan (120.5, 80.25) dan (640.9, 360) dan frame di tick 0-34, plus empat
  `HitParticle` mandiri (size 1, 2, 3, 6; satu mati sebelum tick 9). Fixture 25
  frame, 582 op.
- `death_explosion_draw_checks.gd` mereplay setiap frame dari `DeathExplosion` dan
  `HitParticle` produksi yang di-tick, plus pin kilat (radius/alpha per tick,
  anchor terpotong), petunjuk timpa-piksel, sprite terskala, dan
  `PrototypeView.death_explosion_draw_ops` / `hit_particle_draw_ops`.
- `prototype_view._draw_world_effects` kini melukis ledakan lalu partikel dunia lewat
  `_draw_death_op`; dua pin lama 9ay (`particle.core_radius()` di view dan
  `Color(1.0, 1.0, 1.0, p_alpha)`) diganti pin yang setara untuk layout
  (`float(core) * factor`, inti putih `[255, 255, 255, 255]`). `core_radius()` tetap
  ada di state port dan masih dipin `hit_particle_checks.gd`.

Divergensi yang disadari: pygame menskalakan piksel sprite (nearest neighbour)
sedangkan Godot menggambar lingkaran bergeometri terskala, sehingga tepi bisa beda
sub-piksel; lingkaran tidak anti-alias seperti pygame.

## Slice 9bh — tint ambient `MapRenderer.draw()` (layer 9bh)

Sumber menutup `MapRenderer.draw()` dengan tint ambient tema (`theme.get
("ambient_tint")`) di atas peta statis + dinamis, di bawah bangunan, menara, minion,
hero, boss, dan efek (`_core.py` memanggil `map_renderer.draw` sebelum semuanya).
Port state `MapRenderer` hanya menyimpan `ambient_tint`; `prototype_battle.gd` mengisinya
`null` dan `prototype_view` tidak menggambar apa pun, jadi 53 tema kehilangan semburat
warna petanya. Kini langkah itu diport sebagai daftar op murni,
`scripts/ui/map_tint_layout.gd::ops(theme, screen, cheap_alpha)`:

- `Quality.cheap_alpha` (default PC): surface SRCALPHA seukuran layar diisi
  `(r, g, b, a)` tema lalu di-blit: satu op `fill` `[0, 0, 1280, 720]`, `blend` 0.
  Tanpa `cheap_alpha`: `fill` `(int(255 - (255 - r) * a / 255), ...)` dengan
  `BLEND_RGB_MULT` (blend 3). Tema tanpa tint (forest, atau nama tak dikenal yang jatuh
  ke forest lewat `get_theme`) tidak menggambar apa pun.
- Tabel `TINTS` (54 tema) memuat nilai dari literal tema asli `map_components/
  _bundle.py`; oracle membacanya dengan `ast` (`THEMES` + tiap `*_THEME`), karena
  modul itu tidak bisa diimpor tanpa pygame. Validator membandingkan baris
  `TINTS` di GDScript dengan fixture, sehingga tabel tidak bisa menyimpang diam-diam.
- Oracle memanen `MapRenderer.draw` asli dan menjalankannya di instance tanpa
  `__init__` (peta statis dan renderer dinamis berupa stand-in kosong) di bawah
  `tests/draw_recorder.py`. Fixture: 54 tema x {cheap_alpha, perkalian} = 108 frame,
  106 op (forest tanpa op).
- `minion_view.gd` mendapat hook `_draw_map_overlay()` (kosong) yang dipanggil tepat
  setelah tekstur dinding dan sebelum `_draw_base`; `prototype_view.gd` meng-override-nya
  untuk melukis tint lewat painter level intro (`fill`). Tint ikut transform goncangan
  seperti seluruh peta di sumber (surface dunia di-shake utuh).
- `map_tint_draw_checks.gd` mereplay tabel dan 108 frame lewat layout murni, memeriksa
  kuirk (blend 0 vs 3, forest, tema tak dikenal, ukuran layar), dan lewat
  `PrototypeView.map_tint_draw_ops` dengan `level_config["map_theme"]`.

Divergensi yang disadari: Godot hanya memakai jalur `cheap_alpha` (alpha blend);
jalur perkalian di-pin di layout dan oracle tetapi tidak dilukis. Lapisan dinamis
`DynamicRenderer` (animasi air, obor, dll.) dan renderer dekorasi/toko masih belum
diport, jadi tint menutup peta yang belum memuat lapisan itu.

## Slice 9bi — urutan gambar overlay dan lapisan dunia (layer 9bi)

Layer 9bb-9bh memport tampilan tiap overlay; slice ini memin POSISI-nya di tumpukan,
dibaca dari sumber tanpa menjalankan apa pun (`draw_order_source_oracle.py`):

- `_core.py::Game.draw`: `map_renderer.draw` < `effects.draw` < `tactical.draw_world`
  (lapisan dunia, ikut goncangan) < `boss_intro.draw` < `effects.draw_ui` <
  `level_intro.draw` < `boss_death.draw` (lapisan UI, tanpa goncangan). Komentar sumber
  menyatakan banner boss sengaja digambar sebelum `effects.draw_ui` agar wave
  announcer tidak pernah tertutup, dan `boss_death.draw` adalah panggilan paling akhir.
- `EffectManager.draw`: `path_preview`, `explosions`, `particles`, `floating_texts`;
  `draw_ui`: `wave_announcer`, `achievement` (loop `for e in self.explosions` diselesaikan
  ke nama daftarnya).
- `prototype_view.gd` sebelumnya memanggil `_draw_wave_announcer`, `_draw_combo_counter`,
  `_draw_kill_feed`, `_draw_achievement_popup`, `_draw_boss_intro`, `_draw_level_intro`
  berurutan: banner boss menimpa announcer dan popup achievement (kebalikan sumber), dan
  `_draw_tactical` dilukis sebelum path preview dan efek. Kini `_draw()` mengiterasi
  `WORLD_LAYER_ORDER` dan `OVERLAY_ORDER` lewat `_draw_world_layer` / `_draw_overlay_layer`.
  Combo counter dan kill feed tidak pernah digambar sumber (lihat catatan di bawah),
  jadi mereka tetap di slot lama di antara announcer dan achievement.
- `draw_order_checks.gd` membaca balik `overlay_paint_order()` / `world_layer_order()` dan
  membandingkannya dengan urutan sumber (`effects_ui` diperluas jadi daftar `draw_ui`).
  Validator menambah pin statis: isi konstanta di view, urutan blok ledakan < partikel <
  teks di `_draw_world_effects`, dan fixture tidak menyimpang dari sumber.

## Catatan 9bi — `KillFeed.draw()` dan `ComboCounter.draw()` tidak dipanggil sumber

Audit saat mengerjakan 9bi (grep seluruh `*.py` di luar `godot_rebuild/`):
`EffectManager.draw_ui` hanya menggambar `wave_announcer` dan `achievement`
(komentar sumber: "NOTIFIKASI DIHAPUS (request user)"), `register_kill` langsung
`return`, dan tidak ada pemanggil `combo_counter.draw(`, `kill_feed.draw(` maupun
`kill_feed.add_kill(`; `_core.py` hanya memanggil `combo_counter.add_kill()` (state).
Jadi di game Python asli combo counter dan kill feed TIDAK PERNAH tampil. Layer
9bb/9bc memport `draw()` keduanya dengan setia dan `prototype_view` sudah lebih dulu
melukis keduanya, sehingga Godot menampilkan overlay yang tidak ada di sumber.
Menyembunyikannya (hapus `combo_counter` dan `kill_feed` dari `OVERLAY_ORDER`) adalah
keputusan produk. Keputusan user (sesi 9bj): biarkan tampil; `OVERLAY_ORDER` tidak berubah.

## Slice 9bj — bake dekorasi dan toko peta (layer 9bj)

Latar: Godot memakai tile native untuk lapisan 1-3 (terrain, sungai, lane) dan 6 (tembok tepi)
`MapRenderer._render_static_map`, tetapi lapisan 4 (`DecorationRenderer.draw_all`: pohon, batu,
nisan, bendera, kristal, semak) dan 5 (`ShopRenderer.draw`: bangunan Hero Shop dan Item Forge)
belum pernah digambar. Kode keduanya besar (`map_components/_bundle.py` 315 KB), jadi dibake,
bukan diport tangan.

- `bake/pygame_env.py`: boot pygame headless (driver SDL dummy), mengalihkan folder save game
  ke folder sementara supaya repo tidak tercemar, dan menulis PNG + manifes secara
  deterministik (`Pillow`, `optimize`, tanpa metadata).
- `bake/bake_map_overlay.py`: untuk tiap dari 54 tema membangun `MapRenderer` asli, merender
  lapisan 1-3 (alas) lalu menyalinnya dan menjalankan lapisan 4-5 asli di atasnya. Piksel yang
  warnanya berubah disimpan opak, sisanya transparan; skrip membuktikan `overlay + alas ==
  hasil sumber` (`assert`). Sumber mengacak ulang `random` dari entropi setelah membangun tata
  letak, sehingga detail tiap panggilan gambar berbeda antar-run; skrip menanam seed per
  lapisan (`{tema}:base|decorations|shops`) dan dua run penuh menghasilkan 54 PNG yang identik.
- `data/art/map_overlay.json`: generator, versi pygame, dan per tema `size`, `bytes`, `sha256`,
  `covered_pixels`. `assets/art/map/<tema>.png`: 1280x720 RGBA8. Seluruh 54 `map_theme` di
  `data/levels/level_*.json` punya overlay.
- `scripts/ui/map_art.gd` (`MapArt`): membaca manifes, memuat tekstur lewat `load()` hanya bila
  `ResourceLoader.exists` (tema yang belum diimpor tidak merusak gambar), dan men-cache per tema.
- `minion_view.gd` mendapat hook kosong `_draw_map_decor()` di antara tekstur lane dan tekstur
  tembok (urutan sumber: dekorasi, toko, tembok); `prototype_view.gd` menggambar overlay tema
  aktif di sana, sebelum tint 9bh dan sebelum unit.
- `tests/map_art_checks.gd` (terdaftar di `run_all.gd`): manifes = tema palet (54), tiap PNG
  ada dan terdekode 1280x720, `covered_pixels` >= 10000, tekstur forest/haunted/volcanic
  termuat lewat `load()` (ini menguji impor Godot di CI), cache, dan urutan hook.
  `validate_project.py` menambah pin statis: header PNG (RGBA8 1280x720), sha256 + byte tiap
  file, tema level = tema palet = tema manifes, urutan sumber dekorasi < toko < tembok, isi
  skrip bake, dan wiring view. Tidak ada oracle Python baru di workflow karena membake butuh
  pygame; integritas dijaga hash di manifes dan dijalankan validator di CI.

Cara membake ulang: `python godot_rebuild/bake/bake_map_overlay.py` (butuh `pygame`, `numpy`,
`Pillow`), lalu commit PNG dan manifes yang berubah.

Batas yang diketahui:

- Alas Godot (tile native dengan RNG visual tetap) bukan salinan piksel alas pygame; overlay
  menyalin warna akhir sumber di tiap piksel yang disentuh lapisan 4-5, termasuk bayangan
  yang di sumber transparan. Selisih hanya terlihat pada tepi bayangan.
- Belum ada animasi peta (`DynamicRenderer`: partikel, kabut, obor, kilau toko, air).
- Painter di view tidak dieksekusi suite headless; hanya pemuatan tekstur dan urutan hook
  yang diuji CI. Tampilan akhir harus dilihat di Godot.

## Slice 9bk — bake sprite minion (layer 9bk)

Latar: di Godot minion adalah lingkaran + garis arah + bar HP. Sumbernya
(`minions/_bundle.py`, 417 KB) menggambar tubuh tiap minion sekali per kunci cache
`(tipe, tim, level nexus, pose, arah, hurt, bleed, death charge, regen, slow)` lalu mem-blit
hasil yang sudah di-crop; bar HP, garis tebasan, dan aura slow digambar langsung.

- `bake/bake_minion_atlas.py` menjalankan `Minion.draw` ASLI (lewat sprite cache game) untuk
  tiap pose yang dicapai game lalu membaca sprite ter-crop + anchor dari cache. Pose wakil
  mengikuti urutan kena-pertama di game: serang `k` = `attack_anim_timer` `min(24, 2k + 1)`
  (kunci `atk // 2`, 13 pose), jalan `k` = `walk_cycle` `k / 2` (kunci `int(2 * wc) % 8`, 8
  pose), diam `k` = `anim_time` `20k` (kunci `int(0.05 * t) % 4`, 4 pose), tiap pose untuk dua
  arah (sprite kiri bukan cermin sprite kanan: hanya 61-88% piksel sama, jadi keduanya
  dibake). Tim merah ikut pewarnaan ulang sumber (`R*1.35+B*0.25, G*0.55, B*0.55`) karena
  yang dibaca adalah isi cache. Kilat hurt (+90 kecerahan) tidak dibake supaya sheet tetap
  50 frame; Godot memakai modulate 1,6 selama 8 tick.
- 50 sheet `assets/art/minions/<tipe>_<tim>_<level>.png` (10 kolom, sel seragam per sheet,
  RGBA8) + `data/art/minions.json` (ukuran, byte, sha256, tabel frame `[x, y, w, h, ax, ay]`,
  dan 96 baris `key_cases` hasil `_minion_cache_key` ASLI). Dua run penuh menghasilkan PNG
  yang identik.
- `UnitState.nexus_level` (metadata presentasi, tidak dibaca aturan apa pun) diisi
  `PrototypeBattle.spawn_unit` dari tier nexus tim saat spawn, seperti `Minion.nexus_level`.
- `scripts/ui/minion_anim.gd` membangun ulang jam animasi sumber di sisi view tanpa menulis
  ke unit: `anim_time` +1 per tick, `walk_cycle` +0,25 per tick saat bergerak (> 0,1 px/tick),
  ayunan 24 tick dimulai saat `cooldown_ticks` naik, flash hurt 8 tick saat HP turun.
  `pose_key` meniru kunci cache sumber dan diuji terhadap `key_cases`.
- `scripts/ui/minion_art.gd` memuat atlas (hanya bila `ResourceLoader.exists`) dan
  mengembalikan `{texture, src, anchor}`; `MinionView._draw_unit` mem-blit di
  `int(x) - ax, int(y) - ay` lalu menggambar aura slow dan bar HP seperti
  `minions/_bundle.py` (4 px, latar/border menurut tim, isi hijau/kuning/merah di 0,6/0,3).
- `tests/minion_art_checks.gd`: 50 atlas ada dan terdekode, 50 frame per sheet berada di
  dalam gambar dengan anchor di dalam crop, frame goblin/rider termuat sebagai tekstur
  (menguji impor di CI), `pose_key` identik dengan 96 kunci sumber, simulasi jam
  (diam -> jalan -> serang -> hurt -> prune), tier spawn, dan urutan pemanggilan di view.
  `validate_project.py` memin header/hash/isi tiap sheet, jenis minion dari `_core.py`,
  serta potongan sumber yang diandalkan bake dan view (kunci cache, jam `Minion`, konstanta
  bar HP dan aura slow). Workflow kini juga dipicu perubahan `minions/_bundle.py`.

Batas yang diketahui:

- Belum ada: animasi kematian minion (`Minion._draw_death_animation`), garis tebasan
  (`slash_effects`), ikon debuff menara (`_draw_tower_debuff_fx`), serta kunci bleed / death
  charge / regen yang belum dimodelkan simulasi Godot.
- Pose serang dipicu dari kenaikan `cooldown_ticks`; urutan pasti tick tebasan sumber belum
  dicocokkan kerangka per kerangka.
- Painter tidak dieksekusi suite headless; hanya pemuatan atlas, pemilihan pose, dan
  urutan pemanggilan yang diuji CI.

## Slice 9bl — bake menara, kastil, dan lencana perisai (layer 9bl)

Latar: di Godot menara dan nexus adalah kotak dengan tiga kotak kecil dan titik level.
Sumbernya menggambar badan menara dari `towers/_bundle.py` (299 KB) lewat cache
`("tw", tipe, tim, level, hadap, flash // 3)`, kastil dari kanvas 180x160 yang diskalakan 0,85
(api obor gerbang berkedip dari level 4), dan lencana perisai lewat cache
`(ukuran, warna, bucket rasio, bright)`.

- `bake/bake_structure_atlas.py` menjalankan `Tower._draw_tower_body`, `_render_castle_full` +
  `_render_dynamic_effects` + `smoothscale`, dan `_build_armor_crest` ASLI. Timer wakil
  mengikuti urutan kena-pertama di game: `shoot_flash_timer` 0/5/8/10 untuk `shoot_b`
  0/1/2/3 (turun dari 8, atau 10 untuk Cannon), `timer` kastil 0/3/5/8/10 untuk kedipan api
  `int((timer * 0.4) % 5)` 0..4.
- 42 sheet menara (`tower_<jalur>_<tim>_<level>.png`, 8 frame: hadap kiri/kanan x 4 flash),
  10 sheet kastil (`castle_<tim>_<level>.png`, 5 frame 153x136) dan `crests.png` (88 frame:
  ukuran 14/18 x tim x 11 bucket x bright), total ±1,2 MB. `data/art/structures.json` menyimpan
  ukuran, byte, sha256, tabel frame, timer wakil, blit kastil (`x - 76, y - 101`), dan offset
  bar HP per jalur/level (`get_*_top_y(0, 0, level)` ASLI).
- `scripts/ui/structure_art.gd` memuat sheet (hanya bila `ResourceLoader.exists`);
  `scripts/ui/structure_anim.gd` membangun ulang `shoot_flash_timer` dari kenaikan
  `cooldown_ticks` (8 tick, 10 untuk Cannon) dan kedipan api dari `tick`.
- `SiegeView._draw_structure` kini: sprite bake, lalu bagian hidup sumber (`Tower.draw`: lencana
  perisai di (x+26, y-28-level), bar perisai di atas bar HP 44x5 pada `top_y - 14`, kilau
  setengah tinggi, lencana level berborder kuning, tanda plus regen; `Castle.draw`: lencana
  18 di atas sprite, bar perisai 60x6 membulat di `y - 80` dan label `SHIELD n%`). Bila
  sheet belum diimpor, kotak lama tetap tergambar.
- Struktur dilukis lewat hook `_draw_structures()` di `MinionView` (setelah dasar, SEBELUM
  unit), meniru `Game.draw` yang menggambar kastil dan menara sebelum minion dan hero.
- `tests/structure_art_checks.gd`: 42+10+1 sheet ada dan terdekode, frame di dalam sheet,
  tiap dari 26 definisi struktur punya art untuk kedua tim, tabel offset dan bucket lencana,
  jam flash/kedipan (termasuk kecocokan dengan timer wakil bake), dan urutan pemanggilan.
  `validate_project.py` memin header/hash tiap sheet, cakupan definisi `data/structures`, serta
  potongan sumber yang diandalkan bake dan view (kunci cache, skala dan blit kastil, konstanta
  bar, warna perisai, posisi lencana, label).

Batas yang diketahui:

- Belum ada: kilat moncong Archer, kilat upgrade, lingkaran jangkauan versi sumber (Godot
  tetap memakai busur jangkauan miliknya), peluru `Bullet.draw` (anak panah HD) dan aura sihir
  kastil level 6 (nexus Godot berhenti di level 5).
- Hanya frame pertama tiap kunci cache yang dibake, seperti game; sprite menara yang berubah
  menurut sudut bidik di luar kunci (hadap kiri/kanan) tidak dicakup.
- Painter tidak dieksekusi suite headless; hanya pemuatan sheet, cakupan definisi, jam, dan
  urutan pemanggilan yang diuji CI.

## Slice 9bm — bake penanda slot bangun (layer 9bm)

Latar: slot bangun kosong di Godot berupa cincin dan tanda silang tipis. Sumbernya
(`ui_components/_bundle.py::BuildSlots.draw`) mem-blit satu surface 40x38 ter-cache per slot di
`(x - 20, y - 17)`: slot biru (platform batu, plus bersinar, label biaya "100G") dalam lima
varian denyut `pk = int(round(sin(animation_time * 0.08) * 2))` = -2..2 dan satu slot merah
statis. Label "100G" di sumber memang terpotong tinggi surface (hanya garis emas tipis yang
terlihat di bawah platform); itu ikut terbake apa adanya.

- `bake/bake_slot_atlas.py` memanggil `_render_blue_slot_surface(pk)` dan
  `_render_red_slot_surface()` ASLI dari `Game.ui.build_slots_component`, menyimpan
  `assets/art/slots/slots.png` (240x38, 6 frame, 1,6 KB) dan `data/art/slots.json` dengan
  tabel frame, versi pygame, dan 56 baris `pulse_cases` (rumus sumber untuk deretan waktu).
- `scripts/ui/slot_art.gd`: `pulse(tick)` meniru rumus sumber (jam = tick), memuat sheet hanya
  bila `ResourceLoader.exists`. `PrototypeView._draw_structures()` melukis slot kosong LEBIH
  DULU lalu menara (`super._draw_structures()`), karena `Game.draw` memanggil
  `draw_build_slots` sebelum menara. Pratinjau pilihan slot (cakram dan busur jangkauan
  Archer) tetap milik rebuild; bila sheet belum diimpor, penanda lama
  (`_draw_slot_outline`) tetap tergambar.
- `tests/slot_art_checks.gd`: sheet ada dan terdekode 240x38, enam frame di dalam sheet dengan
  anchor (20, 17), `pulse` identik dengan 56 jawaban sumber dan mencapai kelima ukuran glow,
  frame biru/merah termuat sebagai tekstur, dan urutan slot-di-bawah-menara. Validator memin
  header/hash sheet, potongan sumber (`BuildSlots`), urutan `draw_build_slots` < menara di
  `_core.py`, dan isi view. Workflow kini juga dipicu perubahan `ui_components/_bundle.py`.

Batas yang diketahui: denyut memakai `tick_count` sebagai `animation_time`; slot yang
terisi tidak digambar (seperti sumber); tombol bangun dan popup biaya tetap UI Godot.

## Slice 9bn — painter dijalankan sungguhan di CI (layer 9bn)

Sebelumnya painter `_draw_*` di `PrototypeView` hanya di-parse oleh CI. `CanvasItem.queue_redraw`
menunda `_draw` ke akhir frame (bukan lewat renderer), sehingga frame yang ditunggu suite scene
seharusnya sudah menggambar view; belum ada bukti dan keadaan yang digambar sangat sedikit.
`tests/painter_scene_checks.gd` (di-await dari `run_all.gd` setelah suite scene lain):

- membuktikan `_draw` berjalan di scene `PrototypeMatch` headless lewat `PrototypeView.draw_count`;
- mengisi match dengan lima tipe minion di kedua tim, empat menara biru (tiga di-upgrade ke
  Cannon/Ice/Mage), menara dan slot terseleksi, minion yang diperlambat dan terluka, serta
  menara yang menembak, lalu menjalankan 16 frame (6 tick per frame);
- memastikan jam animasi minion dan struktur terisi. Setiap `SCRIPT ERROR` di painter manapun
  (termasuk layer 9be-9bi) membuat langkah native gagal karena workflow men-grep log-nya.

Batas: renderer dummy tidak merasterisasi, jadi hasil gambar tetap tidak terlihat; hanya
kesalahan skrip (tipe, null, argumen) yang tertangkap.

## Slice 9bo — bake badan hero kit native (layer 9bo)

Latar: hero di Godot adalah lingkaran tim + poligon dari hash id. Sumbernya
(`heroes/__init__.py::render_hero`) men-cache satu badan ter-crop per kunci
`(tipe, tim, level, hadap, idle | serang, fase | timer // 3, bergerak)`, sedangkan
`Hero.draw` menggambar bar HP, papan nama, cincin, dan bayangan di sekelilingnya.

- Level tidak mengubah badan (piksel identik di level 1, 3, 8, 15), jadi level 1 mewakili semua.
- `bake/bake_hero_atlas.py` menjalankan `Hero.draw` ASLI lewat tiga lini masa dari cache kosong
  untuk tiap hadap dan tim, lalu mengambil sprite pertama yang diterima tiap kunci: (A) diam,
  `pulse` +0,1 per tick selama 40 tick; (B) berjalan 2 px per frame (renderer hanya sadar
  gerak dari perubahan posisi di dalam renderer, saat cache MISS, sehingga kunci 'bergerak'
  baru terisi di putaran kedua); (C) satu serangan dari diam, `attack_timer` dari cooldown
  efektif sampai 1. Anggaran render per frame (`_HERO_RENDER_LEFT`) diisi ulang tiap frame
  seperti game, dan kunci dihitung SEBELUM renderer jalan. Pose skill (`active_skill`) belum
  dibake.
- Tujuh hero yang punya kit native di Godot: kaizen, thorne, grimjaw, sylara, vex, zephyr,
  alchemist (14 atlas, 5,5 MB, deterministik). Alchemist tidak punya pose jalan (rendererya
  tidak pernah melapor "bergerak"), jadi Godot menampilkan pose diam saat ia berjalan.
  `data/art/heroes.json` memuat nama, radius, `top_offset` label, cooldown, tabel frame, dan
  241 baris `key_cases` hasil `_hero_cache_key` ASLI.
- `scripts/ui/hero_anim.gd`: `pulse` +0,1 per tick, "bergerak" = |dx| + |dy| > 0,3 per tick,
  `pose_key` meniru kunci sumber (timer asli `HeroState.attack_timer`, kuantum 3 dari preset
  PC `atk_quant_floor`). `scripts/ui/hero_art.gd` memuat atlas dan menolak diam-diam bila belum
  diimpor; timer serang di luar jangkauan memakai pose serang terakhir.
- `scripts/ui/hero_painter.gd` melukis seperti `Hero.draw`: elips kuning dan cakram jangkauan
  saat terseleksi, bayangan hitam penuh (alpha `(0, 0, 0, 100)` dibuang pygame pada layar
  tanpa alpha), sprite di `int(x) - ax, int(y) - ay`, bar HP 45x6 (hijau/kuning/merah
  di 0,5/0,25, border putih) di `y - max(radius, top_offset) - 6`, papan nama hitam 3 px di
  atasnya dengan nama 14 px dan sampai lima bintang (atau satu bintang dan `xN` setelah level
  5), dan strip skill di bawah kaki. `PrototypeView._draw_unit` mencobanya lebih dulu dan
  memakai penanda lama bila hero tidak dibake.
- `tests/hero_art_checks.gd`: 14 atlas ada dan terdekode, tiap pose punya frame dalam gambar,
  `pose_key` identik dengan 241 kunci sumber, simulasi jam (diam, jalan, serang, prune), dan
  urutan pemanggilan. Suite painter 9bn kini juga memastikan jam hero terisi (Kaizen
  menggambar di match bawaan). Workflow dipicu perubahan `heroes/__init__.py` dan
  `heroes/_bundle.py`.

Batas yang diketahui: pose skill, efek hidup hero (`_live_fx_*`), indikator HEAL, dan 215 hero
lain belum dibake; warna cakram jangkauan memakai warna tim, bukan `hero.color`; Godot
menghitung `eff_attack_cd` sendiri, sehingga timer di atas cooldown yang dibake memakai pose
serang terakhir.

## Slice 9bp — bake peluru menara (layer 9bp)

Latar: `SiegeView` menggambar setiap `ProjectileState` sebagai lingkaran 4 px. Sumbernya
(`_entity.py::_get_bullet_sprite`, dipakai `Bullet.draw`) men-cache satu sprite per kunci
`(bullet_type, team, angle_k)` dan mem-blit-nya di `(int(x - ax), int(y - ay))`.

- Hanya panah (`normal`) yang bergantung arah: 16 bucket `angle_k = (int(ang / (2 pi) * 16) +
  16) % 16` dari `atan2` ke target (target mati atau hilang = 0). Bola meriam, kristal es, dan
  bolt mage statis. Bucket 8 hanya tercapai oleh bearing tepat pi (target lurus ke kiri di baris
  yang sama), jadi sheet tetap memuatnya.
- `bake/bake_bullet_atlas.py` memanggil `_get_bullet_sprite` ASLI untuk 16 bucket x 2 tim
  panah plus tiga bolt x 2 tim: 38 frame, satu sheet 200x125 (6 KB), deterministik (dua run
  identik). `data/art/bullets.json` memuat tabel frame dan 66 `angle_cases` (bearing hasil
  `atan2` yang dilihat fungsi sumber -> bucket pilihannya).
- `scripts/ui/bullet_art.gd` memilih bucket dengan rumus yang sama dan menolak diam-diam bila
  sheet belum diimpor. `ProjectileState.kind` (`normal`/`cannon`/`ice`/`mage`) setara
  `bullet_type`; kind tak dikenal jatuh ke titik lama seperti `else` pada sumber.
- `SiegeView._draw_shot`: panah menghadap `(target - peluru).angle()` (= `atan2(dy, dx)` sumber);
  bolt tidak peduli arah. Peluru digambar setelah unit (sumber menggambarnya di dalam
  `Tower.draw`, sebelum minion); selisih urutan ini diterima karena peluru hanya hidup
  beberapa tick.
- `tests/bullet_art_checks.gd`: 38 frame di dalam gambar, bucket 66 kasus sumber, empat arah
  sumbu (0, 4, 8, 12), kind tak dikenal, dan pengabelan view. Suite painter 9bn kini memasukkan
  satu peluru tiap kind ke dalam penerbangan sehingga `_draw_shot` jalan di CI.

Batas yang diketahui: peluru hero (`world.hero_projectiles`; panah Sylara, bola, bolt, petir)
masih titik; jejak hit/impact tetap efek lama.

## Slice 9bq — bake badan boss (layer 9bq)

Latar: `PrototypeView._draw_boss` menggambar lingkaran bermahkota untuk ke-216 boss. Sumbernya
(`bosses/base_boss.py::Boss.draw`) menggambar aura, bayangan, badan dari
`heroes.render_boss` (sprite ber-cache per `_boss_cache_key`), lalu bar HP dan papan nama di
atas puncak sprite.

- `bake/bake_boss_atlas.py` menjalankan `heroes._boss_render_sprite_fast` ASLI untuk pose diam
  fase 0 (`key[8] == "idle"`, `key[9] == 0`, tidak bergerak) pada tiap boss di `BOSS_INDEX`, untuk
  `direction` -1 dan +1, dan menyimpan satu PNG per boss (dua crop bersebelahan, jarak 2 px):
  216 file, 2,6 MB, deterministik (dua run identik). Renderer memperbesar kanvasnya bertahap dan
  mengembalikan `None` sampai muat (game menggambar jalur langsung pada frame itu); bake cukup
  bertanya lagi (maks 12 kali; thalgryn dan xaerissa butuh putaran kedua).
- `data/art/bosses.json`: tabel frame + jangkar tiap boss, `radius`, `class`, `label_top`
  (`BOSS_LABEL_TOP.get(boss_type, radius)`), dan `facing_cases` dari `_boss_cache_key` ASLI
  (direction -3, -1, 0, 1, 2, 7). Roster, radius, dan kelas dicocokkan dengan
  `data/bosses/boss_stats.json` di CI dan validator.
- `scripts/ui/boss_art.gd`: `facing(direction) = 1 if direction > 0 else -1` (aturan
  `int(direction or -1) >= 0`), `label_top = max(BOSS_LABEL_TOP, radius)`, memuat sheet dan
  menolak diam-diam bila belum diimpor. `PrototypeView._draw_boss_sprite` menggambar bayangan
  hitam penuh `(x - (2r + 10 jika true) // 2, y + r - 5, ..., 12)` (alpha `(0, 0, 0, 120)`
  dibuang pygame di layar tanpa alpha) lalu badan di `(int(x) - ax, int(y) - ay)`; luka
  menaikkan kecerahan (modulate 1,6) seperti minion. Bar HP 60x8 (true: 70x10) kini di
  `y - head_top - 6 - bar_h`. Lingkaran bermahkota lama tetap sebagai cadangan
  (`_draw_boss_plain`).
- `tests/boss_art_checks.gd`: 216 sheet terdekode dengan ukuran manifest, crop dan jangkar di
  dalam gambar, roster/radius/kelas cocok dengan tabel Godot, aturan arah identik dengan kunci
  sumber, dan pengabelan view. Suite painter 9bn kini memunculkan boss sejati (`abaddon`),
  memutar arahnya tiap frame, mengedipkan luka, dan membuatnya mengamuk di paruh akhir sehingga
  `boss_sprite_draws > 0` terbukti di CI. Workflow dipicu perubahan `bosses/**`.

Koreksi (CI 9bq): registry native tidak pernah memegang boss (`active_boss` hanya ada di
`_by_id`), sehingga `_draw_unit` tidak pernah mencapai `_draw_boss` dan boss tidak tergambar
sama sekali di view match, juga sebelum slice ini. `PrototypeView._draw()` kini menggambar
`world.active_boss` yang hidup sendiri, sesudah hero dan panah mereka (urutan `Game.draw`:
"DRAW BOSS (di luar hero loop!)") dan sebelum presentasi kematian. Cek painter
`boss_sprite_draws > 0` yang menangkapnya.

Batas yang diketahui: pose jalan, serang, skill, dan kilat luka bawaan sumber, 7+ fase idle,
aura hidup (`_LIVE_FX_HEROES`), serta aura enrage/ability ber-cache masih pendekatan Godot
(busur) atau kosong; boss `entrance` tetap gambar lama.

## Slice 9br — skin UI dari `ui_theme.py` (layer 9br)

Latar: semua layar memakai satu `Theme` yang dibangun kode (`RebuildTheme.create_theme()`, dipasang
di `app.gd` dan tiap layar). Palet dan bentuknya (teal gelap, kotak 10 px) tidak ada di pygame,
yang memakai `ui_theme.py`: panel kaca gelap (gradasi, border emas, sudut emas, bayangan) dan
tombol pil berwarna.

- `bake/bake_ui_theme.py` memanggil `ui_theme.panel()` dan `ui_theme.pill()` ASLI pada kanvas
  transparan. `panels.png` (160x80) berisi dua panel 80x80 (`panel_bold` = panggilan dialog
  `border_w=2`, `panel` = bawaan; rect 72x72 di (4, 4) sehingga bayangan 4 px ada di tepi kanvas).
  `pills.png` (432x144) berisi 8 jenis pil x normal/hover (dengan glow radial)/disabled, kanvas
  54x48, rect 24x24 di (15, 12). Hasil deterministik (dua run identik), 7,7 KB. `draw_text`
  dimatikan saat bake karena teks digambar Godot.
- `data/art/ui_theme.json`: palet (semua konstanta warna modul, 32), frame, margin nine-patch
  (panel 20 px; pil 23x20), `expand` (bayangan 4 px; glow 15x12) dan tabel warna pil yang dibaca dari
  literal `colors` di sumber `pill()` (fill atas/bawah, tepi, teks).
- `scripts/ui/ui_skin.gd`: memotong `StyleBoxTexture` (`region_rect`, margin, expand) dari sheet
  menurut frame manifest; mengembalikan null bila sheet belum diimpor.
- `rebuild_theme.gd`: konstanta palet kini nilai `ui_theme.py` (INK = TEXT_WHITE, MUTED = TEXT_DIM,
  GOLD, CYAN; `TEAL` tetap sebagai nama lama = CYAN). Button: normal = pil `neutral`, hover = pil
  `neutral` hover, pressed = pil `gold` hover, disabled = pil `locked` disabled; teks
  `TEXT_BODY`/`GOLD_TEXT`/`TEXT_FAINT`. `PanelContainer` = panel dialog. Variasi tipe
  `GoldButton`, `SuccessButton`, `DangerButton`, `CyanButton`, `VioletButton` (jenis pil sumber).
  ProgressBar (track `hp_bar`), scrollbar (track dan jempol emas `scroll_indicator`) dan
  PopupMenu (panel + hover) memakai warna sumber. `create_theme(false)` memaksa fallback datar
  dengan warna yang sama (juga yang tampil bila sheet belum diimpor). Baris Hero Shop memakai warna
  kartu level sumber (`OPEN_*`, `LOCKED_*`). Warna kosong atau nama tak dikenal tampil magenta.
- `project.godot`: warna clear = `BG_DEEP` (9, 12, 26).
- `tests/ui_skin_checks.gd`: konstanta tema = konstanta `ui_theme.py` dari manifest, sheet terdekode
  dengan ukuran manifest, 24 frame pil + 2 panel di dalam sheet, piksel kunci (tengah buram, cincin
  bayangan tembus, sudut kanvas pil transparan), Button/Panel/variasi memakai frame yang benar
  dengan margin hasil bake, fallback datar, dan warna baris Hero Shop. Validator memeriksa palet
  manifest = setiap konstanta di `ui_theme.py`, hash PNG, tabel warna pil, tiap `Color8` tema
  bertanda nama sumber, dan fragmen sumber. Workflow dipicu perubahan `ui_theme.py`.

Divergensi yang diterima: glow hover di-bake untuk satu ukuran lalu diregang (sumber menggambarnya
elips sesuai ukuran tombol); bayangan panel sumber berupa cincin 4 px alpha 110 bersudut siku;
tombol menu utama (`button()` dengan aksen kiri dan ikon), toggle, slider dan tab belum diport; font
tetap Barlow Regular 20 dan SemiBold untuk tombol (sumber: Barlow Bold berspasi huruf).

## Slice 9bs — latar menu utama dan warna scene (layer 9bs)

Latar: menu utama Godot memakai lukisan buatan sendiri (`menu_backdrop.gd`, "bukan port"), sedangkan
pygame menampilkan satu surface 1280x720 hasil `Menu._build_main_background` (langit malam, nebula,
170 bintang, bulan besar, cincin rune, dua lapis gunung, tiga lane bercahaya, dua portal, kristal rune,
grid dan vignette). Kabut dan partikel animasi di atasnya belum diport.

- `bake/bake_menu_background.py` menjalankan `Menu._build_main_background` ASLI pada `Menu` hidup dan
  menulis `assets/art/menu/main_background.png` (1280x720, 107 KB, deterministik: dua run identik).
  `data/art/menu.json` memuat ukuran, hash, dan sembilan piksel kunci seperti yang dipegang surface
  sumber (`probes`), sehingga Godot di-pin ke sumber, bukan ke salinan.
- `menu_backdrop.gd`: menggambar PNG itu menutupi jendela (`cover_rect`: skala seragam, di tengah;
  jendela lebih lebar atau tinggi dipotong, tidak diregang). Lukisan lama tetap sebagai cadangan
  (`_draw_fallback`) bila sheet belum diimpor. `background_draws` membuktikan jalur baked jalan.
- `rebuild_theme.title()`: judul layar = emas badan `outline_text` (tengah gradasi `GOLD_BRIGHT` ->
  (196, 138, 40) = (225, 185, 99)) dengan outline gelap (8, 9, 18) selebar 2 px.
- Scene: literal teal lama diganti warna `ui_theme.py` (label redup = `TEXT_DIM`, hitungan emas =
  `GOLD`, eyebrow menu = `CYAN`) dan peredup jeda = (10, 10, 20, 200) seperti `_draw_pause_background`
  (8 + 1 + 1 + 4 literal di `MinionArena`, `Match`, `MainMenu`, `PrototypeMatch`, `SiegeArena`).
- `tests/menu_art_checks.gd`: sheet terdekode 1280x720, setiap piksel kunci sama dengan surface
  sumber, `cover_rect` untuk jendela 16:9, lebar, tinggi dan acak selalu menutup, dan tak ada scene yang
  masih memakai literal lama. `run_all.gd` membuktikan menu sungguhan menggambar jalur baked
  (`Backdrop.background_draws > 0`). Validator memeriksa hash PNG, fragmen `_build_main_background`,
  bake, backdrop, warna judul (dari `outline_text`) dan hitungan warna scene.

Belum: arena layar penuh dan HUD ringkas. Arena tetap 0,7 di dalam bingkai HUD karena skala 1,0
menaruh TopBar, BottomBar dan TacticalPanel (yang tombolnya ditekan tes lewat event mouse sungguhan)
di atas lane; perubahan itu perlu desain ulang HUD dan tidak bisa diverifikasi tanpa engine lokal.

## Slice 9bt — tebasan serang dan animasi kematian minion

- `bake/bake_minion_combat_fx.py` menjalankan `_entity.Minion._spawn_slash_effect`,
  `minions._bundle.draw_slash_effects`, dan `_entity.Minion._draw_death_animation` asli lewat
  `pygame_env.py`. Lima atlas (goblin/orc/troll/undead/dark_rider), masing-masing 1536x2496,
  404 frame (12 umur tebasan x 32 arah pygame + 20 frame mati); PNG total 178.380 byte.
  Dua bake menghasilkan SHA-256 PNG dan manifest yang identik.
- `data/art/minion_combat_fx.json` mem-pin ukuran, byte, hash, radius/distance sumber dan
  `key_cases` berupa hash hasil render pygame untuk sudut/umur tebasan serta awal/tengah/akhir mati.
  `scripts/ui/minion_combat_fx_art.gd` memilih atlas/frame; cek `ResourceLoader.exists` sebelum load
  dan tetap punya fallback painter vektor bila PNG belum diimpor.
- `minion_anim.gd` memulai tebasan pada transisi cooldown, memakai arah target/hit terakhir, dan
  menangkap snapshot kematian sebelum simulasi memensiunkan minion. `minion_view.gd` melukis efek;
  `siege_view.gd` dan `prototype_view.gd` mewarisi jalur yang sama. Counter `minion_slash_draws` /
  `minion_death_draws` dibuktikan >0 di `painter_scene_checks.gd`.
- `tests/minion_combat_fx_checks.gd` terdaftar di `run_all.gd`; validator mem-pin sumber, konstanta,
  hash PNG, frame bounds, key cases, dan trigger workflow `_entity.py` + `minions/_bundle.py`.

Batas: arah sumber kontinu dikuantisasi ke 32 sudut pygame; validator statis dan counter membuktikan
jalur aset, bukan kesamaan piksel. Hasil akhirnya tetap perlu Anda nilai di Godot.

## Slice 9bu — peluru hero dari `_entity.py:4976 Hero._draw_projectile`

- `bake/bake_hero_projectiles.py` menjalankan painter pygame asli per frame, dengan reset budget FX
  tiap draw. Delapan atlas PNG RGBA memuat 12.178 frame untuk 222 hero: panah Sylara, orb Vex
  (serangan/skill), bolt Zephyr (normal/crit), kilat Morgath, shard Ancient Apparition, dan fallback
  warna/crit generik. Usia 0–72, arah 32 langkah, sel per atlas 40–64 px untuk menahan jejak memori;
  dua bake mem-pin hash SHA-256.
- `data/art/hero_projectiles.json` menyimpan warna/radius hero, ukuran/hash atlas, pemetaan frame dan
  22 hash key-case hasil render pygame. `scripts/ui/hero_projectile_art.gd` memilih frame terdekat;
  `prototype_view.gd` menggambar tekstur dan mempertahankan titik fallback saat atlas belum tersedia.
- `hero_projectiles.gd` membawa `hero_type` dan `is_crit` sebagai metadata visual; aturan damage,
  gerak dan tabrakan tidak berubah. `painter_scene_checks.gd` membuktikan hitungan gambar >0, dan
  `hero_projectile_art_checks.gd` memeriksa 222 tipe, kelima cabang, frame, atlas serta key-case.
  Workflow mencakup perubahan FX Zephyr dan Ancient Apparition.

Batas: arah kontinu dibulatkan ke 32 langkah dan usia disampel pada tick integer. Validator/hash dan
counter membuktikan jalur serta sumber bake, bukan kesamaan piksel; tampilan akhirnya tetap perlu
Anda nilai di Godot.

## Slice 9bv — arena layar penuh dengan HUD overlay ringkas

- `PrototypeMatch.tscn` kini menggambar arena pada seluruh bidang logis 1280×720; bar atas dipadatkan
  dan menjadi overlay. Kontrol bawah dibungkus sebagai dock tertutup yang bisa dibuka dari tombol
  Kontrol, sehingga arena/area toko tidak tertutup secara awal. Panel taktis juga menjadi dock kanan
  tertutup dengan toggle Taktik; pada layar lebar, dock responsif yang sudah ada tetap mengambil alih.
- `prototype_screen.gd` menyelaraskan posisi feedback, menjaga jalur kontrol tower dan hero tidak
  berebut tinggi bar, serta menyinkronkan visibilitas toggle dengan dock layar lebar. Label status dan
  kontrol (termasuk toko hero) dipadatkan di bar atas dengan detail pada tooltip, agar tombol tidak
  menutupi titik sentuh arena. Tidak mengubah simulasi, aturan, renderer Python sumber, atau aset gambar.
- `prototype_layout_checks.gd` membuktikan transform arena, tinggi bar, panel tertutup di awal, dan
  transisi buka/tutup; `touch_gesture_scene_checks.gd` menjaga target sentuh bebas dari tombol HUD.
  Validasi statis juga memastikan tes tersebut terdaftar.

Batas: tata letak memakai bidang logis 1280×720 dan elemen HUD memang menimpa tepi arena. Tidak ada
bake gambar pada slice ini; visual akhir tetap perlu Anda nilai di Godot.

## Slice 9bw — portrait mage Vex di Hero Shop

- `hero_portrait.gd` menambahkan kanvas Vex bernuansa arcane yang dipanggil lewat jalur kartu Hero Shop; portrait Kaizen/Thorne dan bust generik lain tetap tersedia.
- `hero_shop_portrait_checks.gd` mengunci dispatch, fallback Sylara, serta penghitung pass `_draw()` dan cabang Vex; `run_all.gd` menunggu dua frame agar bukti hitung berasal dari renderer native.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan visual perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9bx — portrait Sylara, The Wind Ranger

- `hero_portrait.gd` menambahkan kanvas Marksman Sylara dengan busur, panah, dan aksen angin; dispatch Vex/Kaizen/Thorne dan bust generik tetap ada.
- `hero_shop_portrait_checks.gd` mengunci daftar custom, fallback Grimjaw, dan counter `_draw()` untuk Sylara serta Vex; runner menunggu dua frame sebelum pemeriksaan.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9by — portrait Grimjaw, The Berserker

- `hero_portrait.gd` menambahkan kanvas Fighter Grimjaw dengan kapak, armor, janggut, dan aksen bara; custom portrait Kaizen, Sylara, Thorne, dan Vex tetap tersedia.
- `hero_shop_portrait_checks.gd` mengunci dispatch Grimjaw, fallback generik Zephyr, serta penghitung `_draw()` Grimjaw, Vex, dan Sylara; runner menunggu dua frame sebelum pemeriksaan.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9bz — portrait Zephyr, Mage/Trickster

- `hero_portrait.gd` menambahkan kanvas Zephyr dengan tudung/selendang, pusaran angin, dan bola sihir; custom portrait Grimjaw, Kaizen, Sylara, Thorne, dan Vex tetap ada.
- `hero_shop_portrait_checks.gd` mengunci dispatch Zephyr, fallback generik Gornak, serta penghitung `_draw()` Zephyr bersama Grimjaw, Vex, dan Sylara; runner menunggu dua frame.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c0 — portrait Gornak, Boss/Anti-Mage

- `hero_portrait.gd` menambahkan kanvas Gornak dengan armor boss, pelindung rune, dan aura anti-sihir; custom portrait Grimjaw, Kaizen, Sylara, Thorne, Vex, dan Zephyr tetap ada.
- `hero_shop_portrait_checks.gd` mengunci dispatch Gornak, fallback generik Morgath, serta penghitung `_draw()` Gornak, Grimjaw, Vex, Sylara, dan Zephyr; runner menunggu dua frame.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c1 — portrait Morgath, Boss/Temporal Mage

- `hero_portrait_morgath.gd` melukis kanvas native bergaya chronomancer dengan jubah malam, halo jam, dan orb temporal; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci dispatch Morgath, fallback generik Alchemist, dan penghitung `_draw()` setelah dua frame bersama portrait sebelumnya.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c2 — portrait Alchemist, The Greed is Good

- `hero_portrait_alchemist.gd` melukis kanvas native True Boss/Bruiser dengan labu alkimia, aura emas-hijau, dan aksen koin; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci dispatch Alchemist, fallback generik Drakar, dan penghitung `_draw()` setelah dua frame bersama portrait sebelumnya.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c3 — portrait Drakar, Boss/Berserker

- `hero_portrait_drakar.gd` melukis kanvas native dengan tanduk, kapak berat, zirah boss, dan inti bara; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci dispatch Drakar, fallback generik Abaddon, dan penghitung `_draw()` setelah dua frame bersama portrait sebelumnya.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c4 — portrait Abaddon, True Boss/Knight

- `hero_portrait_abaddon.gd` melukis kanvas native dengan zirah spektral, pedang hantu, perisai rune, dan aura biru-frost; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci dispatch Abaddon, fallback generik Ancient Apparition, dan penghitung `_draw()` setelah dua frame bersama portrait sebelumnya.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c5 — portrait Ancient Apparition, The Inscrutable

- `hero_portrait_ancient_apparition.gd` melukis kanvas native True Boss/Ice Mage dengan jubah spektral, mahkota kristal es, tongkat kristal, dan fokus frost; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci dispatch Ancient Apparition, fallback generik Kunkka, dan penghitung `_draw()` setelah dua frame bersama portrait sebelumnya.
- Tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c6 — portrait Kunkka, The Admiral of the Fleet

- `hero_portrait_kunkka.gd` melukis kanvas native True Boss/Naval Admiral dengan coat biru, epaulet emas, topi tiga sudut, cutlass, sash merah, dan aksen ombak; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci daftar dan dispatch portrait Kunkka serta jalur gambar setelah dua frame; Raz kini menjadi hero roster non-custom untuk regresi generic fallback.
- Art-only: tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan tetap perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c7 — portrait Ignis Drachorn, The Molten Sovereign

- `hero_portrait_ignis_drachorn.gd` melukis kanvas native True Boss/Dragon Knight dengan zirah naga berlapis, tanduk, greatsword berinti magma, dan jantung bara; dispatch ada di `hero_portrait.gd`.
- Bust generic deterministik dipindah tanpa mengubah palet/geometri ke `hero_portrait_generic.gd` agar dispatcher utama tetap di bawah batas lint 1.000 baris; Raz tetap dipakai untuk regresi fallback.
- `hero_shop_portrait_checks.gd` mengunci daftar, dispatch, dan jalur gambar Ignis setelah dua frame; semua portrait custom sebelumnya tetap terdaftar.
- Art-only: tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan tetap perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c8 — portrait Aureth'zar, The Radiant Dawn

- `hero_portrait_aurethzar.gd` melukis kanvas native True Boss/Solar Archer dengan busur recurve bercahaya, halo matahari, circlet emas, mantel biru malam, dan sunstone di dada; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci daftar, dispatch, dan jalur gambar Aureth'zar setelah dua frame; Raz tetap menjadi hero roster non-custom untuk regresi generic fallback.
- Art-only: tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan tetap perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c9 — portrait Cogsworth, The Skyfury

- `hero_portrait_cogsworth.gd` melukis kanvas native True Boss/Steampunk Sky Machine dengan rotor atas, vanes penstabil, mata lensa bercahaya, turbin bahu, dan inti jam mekanis; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci daftar dan dispatch Cogsworth serta membuat kanvasnya ikut jalur gambar; Raz tetap menjadi hero roster non-custom untuk regresi generic fallback.
- Art-only: tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan tetap perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c10 — portrait Morthraxis, The Crimson Sovereign

- `hero_portrait_morthraxis.gd` melukis kanvas native True Boss/Vampire Lord dengan mantel bersayap, kerah aristokratik, mane hitam, mata ruby, taring, dan sigil darah; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci daftar, dispatch, dan jalur gambar Morthraxis; Raz tetap menjadi hero roster non-custom untuk regresi generic fallback.
- Art-only: tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan tetap perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c11 — portrait Grondmauris, The Earthborn

- `hero_portrait_grondmauris.gd` melukis kanvas native True Boss/Earth Colossus dengan siluet batu basalt, tanduk batu pecah, retakan hijau berpendar, moss, dan inti earthstone; dispatch ada di `hero_portrait.gd`.
- `hero_shop_portrait_checks.gd` mengunci daftar dan dispatch Grondmauris serta membuat kanvasnya ikut jalur gambar; Raz tetap menjadi hero roster non-custom untuk regresi generic fallback.
- Art-only: tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan tetap perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.

## Slice 9c12 — portrait Okeanora, The Deepborn Oracle

- `hero_portrait_okeanora.gd` melukis kanvas native True Boss/Kraken Priestess dengan mahkota karang, trisula, jubah laut, mata pearl-teal, dan tentakel bersucker sebagai bingkai; dispatch ada di `hero_portrait.gd`.
- Painter Kaizen yang sudah ada dipindah tanpa perubahan geometri/palet ke `hero_portrait_kaizen.gd` agar dispatcher tetap di bawah batas lint; pemeriksaan draw menjalankan painter hasil ekstraksi dan Okeanora.
- `hero_shop_portrait_checks.gd` mengunci daftar dan dispatch Okeanora; Raz tetap menjadi hero roster non-custom untuk regresi generic fallback.
- Art-only: tidak membuat PNG dan tidak mengubah Python, simulasi, aturan, atau aset gambar sumber.

Batas: ini satu tambahan art bertahap, bukan penyelesaian seluruh art final; tampilan tetap perlu dinilai pengguna di Godot. Tidak mengklaim pixel parity dengan pygame.


## Batch slice 9c13–9c15 — Aelyrion, Aeralith, Akahime

- **9c13 Aelyrion — The Divine Guardian**: metadata Boss/Steel Maiden Guardian;
  painter native dengan aureole, pelat baja bersegi, rambut pucat, gorget,
  sword tegak dan shield bersigil.
- **9c14 Aeralith — The West Gale**: metadata Boss/Wind Ranger; hood hijau,
  hembusan angin, scarf terbang, bulu panah, busur recurve dan tali busur.
- **9c15 Akahime — The Scarlet Blossom**: metadata Boss/Scarlet Kunoichi;
  rambut terikat, veil, ribbon merah, ornamen bunga lima kelopak, kunai,
  scarf dan pelindung lengan berlapis.
- Ketiga painter berada di `scripts/ui/hero_portrait_{id}.gd`. Sebelum
  menambah dispatch, painter Zephyr lama diekstrak ke `hero_portrait_zephyr.gd`
  tanpa perubahan geometri, palet, atau urutan draw; dispatcher menjauh dari
  batas 1.000 baris. Semua 19 custom sebelumnya dipertahankan.
- Tes portrait mengunci daftar 22 custom dan dispatch, serta menjalankan
  ketiga painter pada ukuran kartu dan 96 unit. Raz tetap generic fallback.
  Tidak ada reset/increment atau assertion counter per hero baru;
  `draw_pass_count` tetap shared di dispatcher.
- Art-only: tidak menambah image assets dan tidak mengubah Python, simulasi,
  atau gameplay. Tidak mengklaim pixel parity. Penilaian visual akhir tetap
  perlu dilakukan di Godot; ini bukan penyelesaian seluruh art final.
- Kandidat sesi berikutnya berdasarkan urutan metadata: Akaroth (belum custom).
- Validasi lokal batch: seluruh blok static guardrails workflow `godot-rebuild`
  lulus (`validate_project`, source contract/oracles, gdparse, gdlint,
  gdformat --check). Body Zephyr dibandingkan dengan HEAD: geometri/palet
  dan urutan draw tetap. Runtime native diserahkan ke CI Godot 4.7.2 karena
  unduhan release engine tidak dapat diakses dari sandbox.


## Batch slice 9c16–9c18 — Akaroth, Akashari, Akirakumo

- **9c16 Akaroth — The Crimson Fist**: metadata Boss/Crimson Brawler;
  siluet petarung berbahu lebar, dua gauntlet merah terangkat, wrist wrap,
  rambut pendek runcing, bekas luka alis dan garis impact.
- **9c17 Akashari — The Painbringer**: metadata Boss/Queen of Pain;
  sayap kelelawar tinggi, tanduk melengkung, kerah berduri, korset ruby,
  taring, lash melingkar dan dagger.
- **9c18 Akirakumo — The Moonfang Prince**: metadata True Boss/Moon Demon
  Prince; rambut perak, telinga runcing, tanduk bercabang, crescent jewel,
  pelat bahu berlapis dan moon blade diagonal.
- Painter native terpisah `scripts/ui/hero_portrait_{id}.gd`; daftar menjadi
  25 custom. Semua 22 custom sebelumnya tetap, Raz tetap generic fallback.
  Dispatcher tetap jauh di bawah batas 1.000 baris sehingga tidak perlu
  ekstraksi tambahan pada batch ini.
- Tes memperluas daftar/dispatch dan kanvas ukuran kartu + 96 unit, memakai
  grid dua baris untuk batch. Shared `draw_pass_count` tetap tanpa perubahan;
  tidak menambah assertion counter per hero.
- Art-only: tidak menambah image assets atau mengubah Python, simulasi,
  maupun gameplay. Tidak mengklaim pixel parity; review visual akhir tetap
  perlu dilakukan di Godot.
- Berikutnya berdasarkan urutan metadata: Akiraze (belum custom).
- Validasi lokal: 76 poligon baru tanpa edge silang; seluruh blok static
  guardrails workflow lulus satu kali setelah batch (`validate_project`,
  source contract/oracles, gdparse, gdlint, gdformat --check; 401 GDScript).
  Import/runtime native Godot 4.7.2 divalidasi lewat CI PR #337.


## Batch slice 9c19–9c21 — Akiraze, Astraelion, Aurelian

- **9c19 Akiraze — The Golden Tempest**: metadata Boss/Golden Ninja;
  crest dan brow plate emas, celah mata tajam, masker, scarf tertiup angin,
  bilah silang dan clasp shuriken pada harness diagonal.
- **9c20 Astraelion — The Starlight Swordmaster**: metadata Boss/Starlight
  Assassin; rambut perak menyapu, cape asimetris, rasi bintang, mata biru,
  clasp bintang, pedang tipis bercahaya dan bilah reverse-grip.
- **9c21 Aurelian — The Goldspear Sovereign**: metadata Boss/Fighter-Tank;
  helm bermahkota terbuka, janggut persegi, pauldron berat berlapis,
  sigil kerajaan, tombak emas tinggi dan shield kecil.
- Tiga painter native terpisah `scripts/ui/hero_portrait_{id}.gd` menambah
  daftar menjadi 28 custom; seluruh 25 custom sebelumnya dipertahankan,
  Raz tetap generic fallback. Dispatcher masih di bawah 1.000 baris,
  tanpa ekstraksi atau refactor tambahan.
- Tes daftar/dispatch dan draw ukuran kartu + 96 unit diperluas ke batch
  ini. Grid otomatis memakai baris ketiga. Shared `draw_pass_count` tidak
  berubah; tidak menambah reset/increment atau assertion counter per hero.
- Art-only: tanpa image assets atau perubahan Python, simulasi, gameplay.
  Tidak mengklaim pixel parity; review visual akhir tetap perlu di Godot.
- Kandidat berikutnya menurut urutan metadata: Aurelion (belum custom).
- Validasi lokal: 71 poligon baru tanpa edge silang; seluruh blok static
  guardrails workflow lulus sekali setelah batch (`validate_project`, source
  contract/oracles, gdparse, gdlint, gdformat --check; 404 GDScript).
  Import/runtime native Godot 4.7.2 dijalankan lewat CI PR #337.


## Batch slice 9c22–9c24 — Aurelion, Aurelix, Aurelyssa

- **9c22 Aurelion — The Golden Sovereign**: metadata True Boss/Royal King;
  mahkota tinggi, throne finial, mantle ermine, janggut bercabang,
  rantai/seal emerald dan sceptre orb untuk peran magic ranged.
- **9c23 Aurelix — The Time Sovereign**: metadata Boss/Time Mage;
  halo jam bersegmen dengan jarum offset, rambut perak, monocle,
  kerah bercabang, seal hourglass dan staff clock-head.
- **9c24 Aurelyssa — The Golden Blade Dancer**: metadata Boss/Blade Dancer;
  ponytail tinggi, circlet asimetris, ribbon melengkung, pose lengan
  terangkat serta dua bilah crescent melengkung ke dalam.
- Tiga painter native terpisah `scripts/ui/hero_portrait_{id}.gd` menjadikan
  daftar 31 custom; seluruh 28 custom sebelumnya tetap, Raz tetap generic
  fallback. Dispatcher 772 baris; tidak perlu ekstraksi tambahan.
- Tes daftar/dispatch dan draw ukuran kartu + 96 unit diperluas ke ketiga
  hero; grid memakai baris keempat. Shared `draw_pass_count` tetap, tanpa
  reset/increment atau assertion counter per hero baru.
- Art-only: tanpa image assets, perubahan Python, simulasi atau gameplay.
  Tidak mengklaim pixel parity; review visual akhir tetap perlu di Godot.
- Kandidat berikutnya: Aurex (Aurethzar sudah custom).
- Validasi lokal: 59 poligon baru tanpa edge silang; seluruh blok static
  guardrails workflow lulus sekali setelah batch (`validate_project`, source
  contract/oracles, gdparse, gdlint, gdformat --check; 407 GDScript).
  Import/runtime native Godot 4.7.2 dijalankan lewat CI PR #337.


## Batch slice 9c25–9c27 — Aurex, Auroth, Azkharion

- **9c25 Aurex — The Omega Knight**: metadata Boss/Omega Knight;
  helm tertutup bersegi, visor cyan, crest emas, pauldron berlapis,
  sigil omega bercahaya dan pedang rune lebar dengan gauntlet.
- **9c26 Auroth — The Celestial Bastion**: metadata Boss/Bastion Titan;
  siluet benteng dengan pauldron crenellated, wajah monolit batu,
  mahkota astronomis, inti kristal dan dua tinju batu berartikulasi.
- **9c27 Azkharion — The Ashen Warlord**: metadata Boss/Ashen Warlord;
  armour jelaga berduri, mantle merah robek, wajah abu-abu berbekas luka,
  helm perang terbuka, cinder serta kapak eksekusi bertakik.
- Tiga painter native terpisah `scripts/ui/hero_portrait_{id}.gd`; total
  34 custom. Seluruh 31 custom sebelumnya tetap, Raz generic fallback.
  Dispatcher 784 baris, belum perlu ekstraksi tambahan.
- Tes daftar/dispatch dan draw ukuran kartu + 96 unit diperluas ke batch.
  Grid batch menjadi delapan kolom dengan jarak 96 unit agar 30 kanvas
  tetap dalam empat baris, tidak tumpang tindih atau turun ke baris kelima.
  Shared `draw_pass_count` tetap tanpa reset/increment atau assertion
  counter per hero baru.
- Art-only: tanpa image assets atau perubahan Python, simulasi, gameplay.
  Tidak mengklaim pixel parity; review visual akhir tetap perlu di Godot.
- Kandidat berikutnya: Azureth (belum custom).
- Validasi lokal: 76 poligon baru tanpa edge silang; seluruh blok static
  guardrails workflow lulus sekali setelah batch (`validate_project`, source
  contract/oracles, gdparse, gdlint, gdformat --check; 410 GDScript).
  Import/runtime native Godot 4.7.2 dijalankan lewat CI PR #337.
