# Mystic Arena — Godot Edition

> **Status: port masih parsial, belum sama sepenuhnya dengan Pygame.**
> Audit dan daftar selisih yang tersisa: [GODOT_PARITY.md](../docs/GODOT_PARITY.md).
> Bake visual dan keberhasilan export Android bukan bukti paritas seluruh game.

Port GPU dari versi `pygame-ce`. **Visual 222 unit kini hasil bake renderer
pygame asli** (Fase 5, Opsi A): `tools/convert_to_godot.py --units-png`
me-render 6 hero masterwork + 216 boss lewat choke point cache sprite game
(`_call_renderer_on_canvas`, `heroes/__init__.py:1729`) menjadi strip PNG
per unit di `assets/units/`, lalu `BakedSprite` (scene generik + manifest
`data/baked_units.json`) mengirisnya jadi animasi idle/walk/attack — jadi
pose, warna, dan proporsi identik dengan pygame tanpa port ribuan baris
renderer per boss. Kaizen di arena normal juga memakai bake Pygame.
Rig `Skeleton2D` tetap tersedia sebagai showcase/opt-in, bukan pengganti default.
Live FX, UI, minion/tower/nexus, dan mekanik skill belum semuanya setara.

Lapisan gameplay MOBA-nya juga sudah diport (2026-09-06): **menara 4 jalur + 18 slot bangun**, **nexus/castle dengan shield → menang/kalah**, **skill QWER**, **toko item 6 slot (33 item)**, dan **ekonomi identik pygame** (3 gold/s + 0.3/level, pengali difficulty, milli-gold). Lihat bagian "Gameplay yang sudah diport" di bawah.

**Menu utama + progresi level** juga jalan (sesi 2026-09-06 kedua): boot jatuh ke **MENU UTAMA** (`scenes/ui/MainMenu.gd`, state machine paritas `MenuState` pygame: MAIN / LEVEL_SELECT / HERO_SHOP / SETTINGS / HOW_TO_PLAY / CREDITS / PAUSE), pilih level 1–54 dari `levels.json` (nama, deskripsi, tema, mini boss, true boss, kunci `unlock_after_level`), HERO SHOP pakai meta gold, volume SFX/BGM tersimpan di save, dan setelah VICTORY tekan **ENTER** untuk lanjut ke level berikutnya (tema map + boss berbeda).

**Cinematic juga sudah diport** (Fase 5d, 2026-09-07): layar intro split-screen sebelum tiap level (pause sampai SPACE/ENTER/klik), banner nama boss yang meluncur saat mini/true boss turun, dan urutan kematian boss — ledakan + dissolve + pecahan, ditutup perayaan "BOSS DEFEATED!" untuk true boss. Lihat bagian "Cinematic (Fase 5d)" di bawah.

**Map kini bake dari renderer pygame sendiri** (Fase 3, 2026-09-07): `tools/convert_to_godot.py --maps-png` membake 6 layer `static_map` (terrain+details, river, 3 lane, dekor, shop, border wall) jadi SATU tekstur 1280×720 per tema — 54 tema, ±3,2 MB di `assets/maps/` — lalu `ArenaMap` menampilkannya lewat Sprite2D (padanan persis arsitektur cache `static_map` + blit pygame). Gambar statik bersumber dari renderer asli; cuaca/lighting live tetap implementasi Godot. Fallback prosedural hidup kalau bake belum ada. Lihat bagian "Bake map statik (Fase 3)" di bawah.

## Koreksi tata letak di jendela desktop (2026-09-14 — UI modal di dalam frame)

Laporan pemain: **layar VICTORY/DEFEAT dan dialog TOP UP muncul di luar frame**
saat dimainkan di Godot desktop. Akarnya bukan koordinat isinya, tapi titik acu
yang dipakai.

**Sebabnya.** Kamera arena dipasang `Main._frame_camera()` dengan
`position = (640, 360)` + limit `0..1280` × `0..720` + zoom 1, dan Camera2D
MENGUNCI rect layar ke limit itu (`scene/2d/camera_2d.cpp:172-186`, `:225-241`):
arena tidak pernah melebar mengikuti jendela. Di jendela 16:10 / ultrawide /
maximize-dengan-taskbar, sisa kanan-bawah viewport ada DI LUAR peta — jadi titik
`anchor = 0.5` (= pusat viewport) bukan lagi pusat arena. Seluruh UI modal port
ini memakai anchor itu, padahal pygame menggambar semuanya ke surface 1280×720
(`cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2`) sehingga hasilnya selalu di tengah
peta. Di jendela yang LEBIH KECIL dari 1280×720 masalahnya cerminannya: kamera
terpotong rata tengah, dan baris tombol di bawah (`cy + 292`) bisa lewat tepi
layar.

**Perbaikannya** — satu sumber angka baru di `MobileLayout` (`arena_frame_rect`,
`arena_center`, `arena_center_offset`, `arena_visible_rect`, `arena_fit_scale`,
`place_in_arena`, `cover_arena`), lalu pemakainya:

- `GameOverOverlay`: judul, panel stat, popup NEW LEVEL UNLOCKED, baris keycap,
  hitungan achievement, dan baris tombol NEXT/REPLAY/MENU dipasang lewat
  `place_in_arena` (offset desain pygame apa adanya terhadap pusat peta) dan
  dipasang ulang tiap `MobileLayout.layout_changed` — resize saat layar hasil
  tampil tidak lagi meninggalkan elemen di posisi lama.
- Lapisan gelap + ray/glow/sparkle overlay kini menutup **frame arena saja**
  (`cover_arena`), bukan seluruh jendela: paritas pygame yang tidak pernah
  menggelapkan panel kanan.
- `TopupDialog`: panel 920×580 dipusatkan di frame arena, dan skala fit-nya
  dihitung dari **bagian frame yang terlihat** (`arena_fit_scale`, margin 24 px)
  — di jendela kecil dialog mengecil proporsional alih-alih terpotong.
- `MobileLayout.modal_rect` (HERO SHOP / ITEM FORGE in-match) juga dipusatkan ke
  frame arena, dan chip TACTICAL tanpa rail (`TacticalBar`) menempel di
  kanan-bawah frame — bukan kanan-bawah viewport.

**Invarian penting:** di viewport 1280×720 `arena_center_offset()` = nol,
sehingga offset yang dihasilkan **identik** dengan kode lama — semua test paritas
yang berjalan di 1280×720 (UiHudParityTest, MatchScoringParityTest,
MobileSidePanelParityTest) tidak berubah sedikit pun; koreksi ini hanya berlaku
di jendela yang bukan 16:9.

**Pengaman kedua (desktop).** `AppShell._fit_window_to_screen()` (knob
`FIT_WINDOW_TO_SCREEN`, batas bawah 960×540) mengecilkan jendela saat boot kalau
jendela tidak muat di rect berguna layar (taskbar/dock sudah dikurangi) lalu
memusatkannya — jendela 1280×720 + title bar tidak muat di layar kecil atau pada
display scaling Windows 125-150% (yang membuatnya setara 1600×900), dan bagian
bawah jendela itulah yang memuat baris tombol NEXT LEVEL / PAY NOW. Tidak pernah
memperbesar, tidak menyentuh perangkat sentuh, dan tidak memanggil DisplayServer
sama sekali kalau jendelanya sudah muat.

Dikunci `tests/ArenaFrameLayoutTest.tscn` (CI: langkah 4z3) yang mensimulasikan
16:9, 1624×720 (HP landscape), 1866×1050 (16:10), 1000×600, dan 800×500 lewat
`MobileLayout.viewport_size` + Control pembungkus, lalu memeriksa aritmetika
frame, posisi semua blok overlay, lapisan gelap, tata ulang saat jendela diubah,
dan panel dialog TOP UP (terpusat + muat).

### Kontrak `ui_data.blocked` kartu Hero Shop (ikut diperbaiki di PR yang sama)

`UiHudParityTest` di `main` sudah merah sebelum PR ini (2 cek: `OWNED reason`,
`FULL reason`), dan kegagalan itu men-skip SEMUA langkah CI sesudahnya —
termasuk test baru di atas. Sebabnya commit renderer kartu (#239):
`HeroShopCard.configure()` menuliskan **state kartu** (`"ACTIVE"`/`"MAX"`) ke
`ui_data.blocked`, padahal `blocked` adalah **alasan** dalam kosakata baris
toko pygame (`""`/`OWNED`/`FULL`/`POOR`/`LOCKED`). Dua hal itu memang berbeda:
kartu ber-state `ACTIVE` alasannya `OWNED`, kartu ber-state `MAX` alasannya
`FULL`, dan alasan `LOCKED` justru string kosong di baris toko.

Perbaikannya: `HeroShopCard.configure()` menerima `p_reason` **wajib** dari
pemanggil (`ShopPanel._make_hero_card()` sudah menghitung alasan itu dari state
permainan), disimpan di properti `reason`, dan itulah yang masuk ke
`ui_data.blocked`. Visual pill tetap memakai `state` — tidak ada perubahan
tampilan.

### Audit teks menu: widget yang menggambar teksnya sendiri

`LocalizationParityTest` (gate "SEMUA layar menu ikut bahasa") juga merah di
`main` setelah #239, dan kegagalan itu ikut menahan langkah CI berikutnya.
Sebabnya bukan teksnya, tapi **cara audit membaca teks**: widget proyek ini
menggambar teksnya sendiri di `_draw()` dan mengosongkan properti bawaan
Godot, jadi `_collect_texts()` tidak menemukan apa pun:

| widget | properti yang digambar | dibaca audit dari |
|---|---|---|
| `PygameButton` | `label_text` (`Button.text` = `""`) | `label_text` |
| `PygameChip` | `label_text` + `value_text` | keduanya |
| `OptionCycler` | `label_text` + `value_text()` | keduanya |
| `ScreenTitle` | `text` + `sub_text` | keduanya |

Tanpa cabang-cabang itu, sentinel `en/MAIN` (`PLAY GAME`/`HOW TO PLAY`/
`QUIT GAME`) dan SEMUA sentinel judul layar (`SELECT SAVE SLOT`, `PILIH LEVEL`,
… ) selalu dianggap hilang, dan gate closed-world "tak boleh ada label
Indonesia di layar `en`" ikut buta terhadap tombol. Satu bug kecil lagi di
audit yang sama: `forbidden[f]` di dalam argumen `_expect(...)` — GDScript
mengevaluasi SEMUA argumen, jadi lookup itu meledak justru pada label yang
SAH dan membatalkan sisa audit satu layar; kini `forbidden.get(f, "")`.

### Panel statistik VICTORY/DEFEAT: acuan tepi atas, bukan setengah tinggi

Tinggi panel statistik ditentukan tinggi minimum isinya (VBox 5 baris), bukan
tebakan `rows * ROW_H + 24 = 214 px` (nyatanya ~308 px). Karena acuan pygame
adalah tepi ATAS (`cy - 100`), setengah tinggi yang salah langsung menggeser
panel di jendela non-16:9 (terukur +20 px di CI). `_build_stats_panel()`
menyambung sinyal `resized` ke `_reanchor_stats_panel()` yang menghitung ulang
offset dari tepi atas yang sama memakai tinggi nyata, dan `_center_in_arena()`
menyimpan satu entri per Control supaya `_recenter()` selalu memakai ukuran
terakhir.

### Catatan verifikasi (2026-09-14)

`ArenaFrameLayoutTest` sudah benar-benar dijalankan CI (bukan sekadar parse):
aritmetika frame, lapisan gelap, dan dialog TOP UP untuk 5 ukuran jendela
LULUS; sisa kegagalan terakhir adalah tween intro panel statistik yang belum
selesai saat diukur (rect terukur 450x277 = skala 0.8999 dari 500x308), dan
test kini mematikan tween itu sebelum mengukur. Run yang memverifikasi commit
terakhir TIDAK jalan karena GitHub Actions menolak start job ("recent account
payments have failed or your spending limit needs to be increased") — jadi
tiga commit terakhir (kontrak blocked, audit teks, reanchor panel) baru
terverifikasi statis (`gdparse`, `gdlint`, `tools/tscn_lint.py`,
`tools/check_refs.py`) plus dua run CI sebelumnya, belum lewat run CI penuh.
Cara memverifikasi ulang setelah billing beres: jalankan workflow "Godot Check"
(atau `godot --headless --path godot res://tests/ArenaFrameLayoutTest.tscn
--quit-after 240`).

## Koreksi UI in-match (2026-09-13 — mengikuti pygame)

Empat perilaku UI in-match disetel ulang supaya persis seperti versi pygame;
dua di antaranya MENGHAPUS elemen yang tidak pernah ada di pygame karena
menutupi peta:

- **Kastil tidak menumpuk angka ke peta.** `Nexus._draw_overlays` kini hanya
  menggambar crest armor + bar SHIELD 60×6 di `y-80` dengan label `SHIELD n%`
  di atasnya — padanan persis `Castle._draw_castle_shield` +
  `Castle._draw_hp_bar` (`_entity.py:1892-1946`, yang fungsi keduanya memang
  hanya menggambar shield). Bar HP kastil 84×7, border putih, dan pip level
  emas di atas kastil DIHAPUS. HP/level nexus tetap terbaca di **tab NEXUS**
  toko, sama seperti pygame yang menyimpannya di popup. Menara TIDAK berubah —
  `Tower.draw` pygame memang masih menggambar bar HP.
- **Baris teks di bawah badge LEVEL/WAVE DIHAPUS.** `FieldStatus`
  ("medan: n hero · n minion · n boss · n fps") dan `DifficultyLabel`
  ("difficulty: … · gold x…") adalah penemuan port; HUD pygame = chip emas +
  badge level/wave + banner wave. Bersamanya ikut hilang pemindaian tree tiap
  0,33 s. Gerbang statis `python3 godot/tools/map_clutter_lint.py godot`
  menjaga keduanya tidak balik (juga membandingkan bentuk overlay dengan
  `_entity.py` asli).
- **Tab ITEM selalu bisa dilihat.** Tanpa hero (belum summon, atau semuanya
  mati) katalog 33 item TETAP dibangun — persis `ItemShopUI.draw`
  ("Grid item SELALU ditampilkan, walau pemain belum meng-klik hero di peta",
  `hero_items.py:3190-3200`) — hanya tombol BELI yang mati, plus banner
  merah `shop_no_hero_banner`. Strip **BELI UNTUK:** menampilkan tiap hero
  roster (hidup maupun mati, paritas `_draw_hero_strip` `:3241-3295`);
  penerimanya `GameManager.itemshop_target_hero()` (padanan
  `_resolve_shop_target` `:3169-3186`) sehingga mouse, papan ketik, dan
  controller memakai aturan yang sama. Deviasi tercatat: port belum punya
  antrean Item Forge (`pending_forge_items`), jadi chip hero MATI disabled —
  pygame mengantrekan item untuk hero mati, Godot menolaknya daripada
  kehilangan gold.
- **Bahasa benar-benar berlaku di dalam game.** HUD, ShopPanel, SkillBar, dan
  GameOverOverlay membaca dari tabel teks bersama (`Localization.gd`,
  106 kunci × 2 bahasa) dan menyambung `GameManager.language_changed`, jadi
  "English" di PENGATURAN langsung mengubah teks in-match. Rincian: bagian
  "Lokalisasi teks UI" dan `docs/LOCALIZATION_GODOTPP.md`.

## Koreksi paritas pertandingan (2026-09-07)

- Match mulai tanpa hero. Buka **B → HERO** untuk membeli; save baru membuka
  Kaizen saja. Maksimal 5 hero unik, termasuk hero yang menunggu respawn.
- Respawn **per hero setelah 10 detik**, tanpa reset arena; level/item biasa
  tetap, Holy Rapier rontok. Pause membekukan timer.
- Persiapan wave pertama 5 detik setelah intro. Wave berikutnya menunggu
  minimal 25 detik **dan** minion sebelumnya habis. Spawn bertahap tiap
  20 frame, satu komposisi penuh pada setiap lane, mengikuti waypoint.
- Komposisi/stat berasal dari nexus tim sendiri; nexus AI naik pada wave
  4/7/10/13. AI mulai 350 gold, income 3 + nomor wave. Mini boss diacak:
  easy 20–40, normal/hard 11–30, urutan tipe tetap.
- Tes baru membandingkan dengan output fungsi Pygame asli:
  `python tools/test_godot_match_parity.py` dan
  `godot --headless --path godot res://tests/GameplayParityTest.tscn --quit-after 300`.

## Quick Start

```bash
# 0. Salin aset biner (suara + 33 ikon item + presplash) -> godot/assets/.
#    Ketiganya DI-GITIGNORE (duplikat ±19 MB dari assets/ pygame), jadi harus
#    disalin ulang setiap clone. Tanpa pygame/numpy/venv — os+shutil saja:
python3 tools/convert_to_godot.py --assets
#    Tanpa langkah ini game tetap jalan: AudioManager no-op, ikon item jadi
#    badge prosedural, boot splash pakai bawaan Godot.

# 1. Convert data pygame -> Godot JSON (222 hero, 216 boss, 54 level, 54 tema map)
#    Sekaligus menyalin aset biner yang sama seperti langkah 0 (suara, ikon
#    item, presplash — semuanya di-gitignore).
#    Butuh pygame + SDL dummy (export_themes membaca map_components/themes.py):
python3 -m venv ~/.venv-mystic && ~/.venv-mystic/bin/pip install "pygame-ce==2.5.*"   # sekali saja
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy ~/.venv-mystic/bin/python tools/convert_to_godot.py

# 2. Buka di Godot 4.3+ (diuji di 4.7.2 Forward+)
godot godot/project.godot
# F5 -> MENU UTAMA (layar penuh; arena+HUD disembunyikan selama menu).
# MULAI GAME -> PILIH SLOT -> PILIH LEVEL -> pilih kartu LEVEL 1 -> MAIN.
# (LANJUTKAN mem-bypass slot select, langsung mulai level berikutnya.)
# Arena 1280x720: map forest, 2 nexus, 18 slot menara, roster kosong.
# Lewati intro, H -> tab HERO -> beli Kaizen. Wave pertama setelah 5 detik,
# wave berikutnya minimal 25 detik + tunggu field clear; mini boss wave acak,
# true boss Abaddon setelah 6 menara Dire hancur, HUD + skill bar QWER +
# toko (H, atau klik bangunan toko di map: Radiant=ITEM FORGE, Dire=HERO SHOP).
# Menang -> ENTER lanjut LEVEL 2 (tema desert, boss razak/khalros/gorath/alchemist).
```

## Jalankan & debug tanpa memasang Godot (GitHub Actions / Codespaces)

Port ini bisa dijalankan **dari repo** — berguna saat bug hanya muncul di
lingkungan bersih, atau saat ingin melihat layarnya tanpa memasang Godot + GPU:

```bash
# Lokal (tanpa X11 pun jalan: layar virtual Xvfb; hasil di debug_out/)
python3 tools/godot_debug_run.py --scenario battle --level 1 --seconds 30
python3 tools/godot_debug_run.py --scenario shop --level 3 --seconds 25 --movie
python3 tools/godot_debug_run.py --scenario scene \
    --scene res://tests/BattleSmokeTest.tscn --display headless   # tes apa pun
```

* **Di GitHub**: tab Actions → **Godot Debug Run** → Run workflow (pilih
  skenario/level/durasi). Artifact `godot-debug-*` berisi `shots/*.png` tiap N
  detik, `run.log` apa adanya, `report.json` (state · wave · gold · hero per
  tim · minion + FPS), `summary.md`, dan opsional `movie.mp4`. Memberi label
  **`godot-debug`** pada PR menjalankan kode PR itu. Workflow ini **manual
  saja** (kuota Actions tidak terpakai sampai dipanggil) dan tetap memakai
  gerbang log yang sama dengan godot-check.yml.
* **Di browser (editor Godot penuh)**: buka repo ini dengan Codespaces —
  `.devcontainer/` memasang Godot 4.3 + desktop noVNC (port 6080), versi
  engine-nya disamakan dengan workflow oleh `tools/test_godot_debug_runner.py`.

Logikanya ada di `tools/godot_debug_run.py` + harness
`scenes/debug/DebugRun.tscn` yang **membungkus `scenes/main.tscn` apa adanya**
(tidak ada satu baris gameplay yang diubah; `main.tscn` tidak merujuk berkas
debug ini). Sebelum run sungguhan alatnya **menguji dirinya lebih dulu**
(preflight, beberapa detik): (1) engine yang sama mengompilasi
`scenes/debug/*.gd` lewat `--check-only -s` — menangkap API yang tidak ada di
versi engine (mis. API 4.4 dipakai di engine 4.3), lalu (2) menjalankan
`scenes/debug/DebugMarker.tscn` yang tidak memakai satu pun API game. Jadi
"skrip debug salah" tidak lagi menyamar sebagai "engine menggantung".
Panduan + troubleshooting:
[`../docs/GODOT_DEBUG_DI_GITHUB.md`](../docs/GODOT_DEBUG_DI_GITHUB.md).

### Kontrol pemain

| Input | Efek |
|---|---|
| **klik kiri** | pilih unit: bangunan toko (Radiant → tab ITEM / Dire → tab HERO) · hero Radiant (→ skill bar) · menara milikmu (→ tab MENARA) · nexus (→ tab NEXUS) · lingkaran slot di lane (→ bangun menara) |
| `Q` `W` `E` `R` | cast skill hero yang sedang dipilih (bisa juga lewat tombol di skill bar) |
| `H` | buka/tutup toko (MENARA · ITEM · HERO · NEXUS) — satu-satunya hotkey toko (paritas pygame; `B` kini milik perintah taktis) |
| `G`/`F` `T` `C` `B` `D` (hold) | perintah taktis: GATHER (di posisi kursor) / PROTECT TOWER / PROTECT CASTLE / ATTACK BOSS / ATTACK DMG DEALER. Panelnya di dasar **panel kanan** saat layar lebih lebar dari 16:9; di layar tanpa panel kanan (16:9/potret) panelnya **terlipat** jadi chip **TACTICAL** kecil di kanan-bawah arena (ketuk untuk membuka, panel menutup sendiri setelah perintah dilepas) supaya map tidak tertutup |
| `ENTER` | setelah VICTORY: **lanjut level berikutnya** · setelah DEFEAT: ulangi level |
| `R` | setelah menang/kalah: replay level yang sama (is_replay → reward 1500/200, bukan 3000) |
| `F8` | panel **FPS** (angka + grafik 60/30 fps + AVG/MIN/MAX) — paritas `_system.FPSCounter` jalur desktop legacy, ditangani SEBELUM dispatch state sehingga tetap jalan di splash/menu/pause; L3 & tombol FPS TouchHUD tetap mengarah ke overlay debug `HUD.toggle_debug_overlay` (padanan `mobile/debug.py`, 4 mode) |
| `P` / `ESC` | menu PAUSE (RESUME / PENGATURAN / MENU UTAMA / KELUAR — paritas `MenuState.PAUSE`); ESC setelah menang/kalah = menu utama |
| `SPACE` / `ENTER` / klik | lewati layar intro level (gameplay beku sampai dilewati); SPACE/ESC/klik juga menutup banner nama boss & perayaan "BOSS DEFEATED!" |

**Gamepad (FASE 24):** tekan tombol **INPUT** di MENU UTAMA untuk berpindah
keyboard ⇄ controller (label kiri-bawah berubah jadi `INPUT: XBOX CONTROLLER`
/ `PLAYSTATION CONTROLLER` / `GENERIC CONTROLLER`). Tombol pad mengikuti
`main_desktop_legacy.py` pygame: **A** klik/konfirmasi (juga skip cinematic, dan
NEXT LEVEL saat victory) · **B** tutup UI berurutan lalu pause · **X/Y/LB/RB**
skill Q/W/E/R (X = REPLAY dan RB = NEXT LEVEL setelah match usai) · **START**
pause · **VIEW/SELECT** menu utama setelah match usai · **LT** toko (H) ·
**RT** klik kanan (perintah hero) · **L3** overlay FPS · **R3** snap kursor ke
tombol UI terdekat · **D-PAD** lompat kursor (atau gulir list saat toko/level
select/hero shop terbuka) · **stick kanan** gulir list. Kursor virtual
(crosshair + kotak sorot) muncul hanya di mode controller, dan hint bar bawah
ikut tampil dengan label tombol pad — persis `_draw_input_hints` pygame yang
hanya menggambar bar itu di mode controller. Rumble ikut menyala saat cast
skill. Dikunci `ControllerInputParityTest`.

**Performa & overlay FPS (FASE 25):** targeting minion membaca `SpatialGrid`
(`scripts/systems/SpatialGrid.gd`, padanan `performance.py` `_system.py:29-185`:
`cell_size` 60, satu grid global, dibangun ulang tiap 2 frame seperti
`animation_time % 2 == 0` di `_core.py:2007-2013`) — urutan kandidatnya adalah
urutan bucket, dan itu yang menentukan target mana yang diprioritaskan. Menara
dan nexus **tidak** diindeks grid (persis pygame) sehingga selalu hasil scan
langsung dan appended terakhir; jalur AoE/splash/rantai mage/voly pemanah juga
sengaja tidak dialihkan karena urutan kandidatnya sudah dikunci tes lain. Kalau
grid belum berlaku (menu, pause, harness), `query_enemies_in_range` jatuh ke
scan grup — himpunan sama, urutan ikut grup. `WorldPopups._draw` memakai
`FrustumCuller` (margin 80 + radius) untuk tidak membangun `draw_string` popup
yang berada di luar layar. Dikunci `SystemPerfParityTest` terhadap fixture
oracle pygame (`tools/test_system_perf_parity.py`); peta blok lengkapnya ada di
`../docs/SYSTEM_PY_COVERAGE.md`.

Hero Radiant yang tidak dipilih tetap bertarung sendiri (AI + auto-cast skill); yang dipilih berhenti auto-cast dan menunggu input QWER — sama seperti pygame.

Di layar sentuh (dan klik mouse): tombol **II** jeda di kiri atas, **SKIP >>** saat cinematic, dan **REPLAY / NEXT LEVEL / MENU** setelah match usai — paritas `mobile/hud.py` (tombol FPS hanya dengan `MYSTIC_DEBUG=1`, dan jeda pindah ke panel kanan di layar lebar). Dikunci `TouchHudParityTest`.

Panel hero (skill bar QWER + **UPGRADE HERO**) hanya muncul setelah hero Radiant dipilih — paritas `HeroPanel` pygame yang tidak digambar saat tak ada hero terpilih. Di layar lebih lebar dari 16:9 panelnya pindah KE DALAM panel kanan (`MobileLayout.hero_panel_rect`, paritas `platform_utils.panel_pos_bawah` + `ZONA_POPUP_Y`), jadi arena tidak pernah tertutup; tingginya ikut tinggi konten supaya tombol upgrade tak pernah keluar layar. Dikunci `MobileSidePanelParityTest`.

Pilih difficulty di menu PILIH LEVEL sebelum match.

### Perilaku layar menu

- Menu utama/sub-menu = **layar penuh opak**: arena, unit, slot, dan HUD
  disembunyikan selama menu terbuka (tidak ada lagi "menu menempel di samping
  arena"). PAUSE berbeda: arena BEKU tetap terlihat di belakang lapisan dim
  gelap — paritas pygame (pause = frame game terakhir + overlay).
- Flow mulai: **MULAI GAME → PILIH SLOT SAVE → PILIH LEVEL** (paritas
  pygame FASE 21); **LANJUTKAN** langsung mulai level berikutnya.
- PENGATURAN berisi: Volume Master/SFX/BGM, Screen Shake (hidup — camera
  trauma), Damage Numbers (live), info difficulty (dipilih di PILIH LEVEL),
  cycler Game Speed + FPS Limit, **baris BAHASA** (`< Bahasa Indonesia >` —
  port `localization.py`, lihat "Lokalisasi teks UI" di bawah), HAPUS SAVE
  slot aktif (dialog konfirmasi), dan catatan jujur bahwa cloud save Play
  Games belum di-port.

### Tombol debug

Hanya aktif bila `Main.enable_debug_controls = true` (default **false**).

| Tombol | Efek |
|---|---|
| `F1` | ulang match penuh (bukan respawn hero normal) |
| `D` | ganti difficulty untuk pengujian |
| `T` | ganti tema map: siklus 54 palet dari `data/themes.json` (forest → desert → ice → volcanic → …) |
| `SPASI` | "beli" 1 hero random untuk Radiant (lewat `GameManager.try_buy_hero`) |

Untuk Kaizen showcase saja: double-click `godot/scenes/demo/KaizenDemo.tscn` → **Run Current Scene**.
Siklus idle 3s → walk 3s → attack loop (hamon kilat + wind ribbon). SPACE=force attack, F=flip, R=reset.

## "F5 cuma layar hitam" — penyebab & perbaikannya

Log dulu berhenti di `[GameManager] Start Level 1 — gold 1000` dan viewport tetap gelap. Itu **bukan**
crash: memang tidak ada satu node pun yang menggambar. Yang hilang (dan sekarang sudah ada):

1. `scenes/main.tscn` tidak punya script root — `start_level()` hanya `print` + emit signal, tidak ada
   yang men-spawn unit. → ditambah `scenes/main/Main.gd` (roster + wave + framing kamera).
2. `ArenaMap.tscn` berisi 4 `TileMapLayer` tanpa `tile_set` (`assets/tilesets/*.tres` belum dibuat),
   dan 2 `Sprite2D` toko tanpa texture → 0 piksel tergambar. → `ArenaMap.gd._draw()` sekarang
   menggambar terrain/lane/river/base/toko/decor prosedural memakai palette asli
   `map_components/themes.py` (54 tema via `data/themes.json`). Begitu
   `assets/tilesets/<tema>.tres` di-import, fallback otomatis mati.
   *(Update Fase 3, 2026-09-07: rencana TileSet `.tres` diganti **bake tekstur tunggal** —
   diukur 533/576 sel 40px unik sehingga atlas TileSet sama besar dengan peta sendiri.
   `--maps-png` membake `assets/maps/<tema>.png`; `apply_theme()` menampilkannya sebagai
   Sprite2D `BakedMap`, fallback otomatis mati, dan 4 TileMapLayer kosong dihapus dari .tscn.)*
3. `Camera2D` ada di (0,0), padahal arena 0..1280 × 0..720 → isi arena (mis. base Radiant di
   y=620) berada di luar view. → kamera dipusatkan ke (640,360) + `limit_*` dikunci ke ukuran arena.
4. `Boss.tscn` tidak punya visual sama sekali (AnimatedSprite2D kosong, partikel tanpa material) →
   boss tak terlihat walau menghajar hero. → `UnitSilhouette` (badan + tanduk) + boss bar + AI.
5. `Hero.gd` fallback kotak/`SpriteFrames` null tidak pernah tergambar. → default `UnitSilhouette`
   pygame; `autoplay` dihapus dari .tscn (menghilangkan error spam tiap spawn).
6. `Engine.time_scale` di-hit-stop diubah dari node unit yang bisa `queue_free()` di tengah `await`
   (game bisa "nyangkut" 0.05 ≈ layar tampak beku). → hit-stop pindah ke `GameManager` dengan
   watchdog waktu nyata.

Catatan kecil yang juga sudah dibereskan:

- `Color("rrggbb")` **tanpa `#`** di Godot = warna tidak valid (jadi hitam/transparan). `PALETTE`
  Kaizen dan palette map sekarang semuanya `Color("#rrggbb")`.
- `Color8()` tidak boleh dipakai di dalam `const` (bukan konstanta yang dikenali GDScript) —
  pakai `Color("#...")`.
- Cek statis tanpa engine:
  `python3 godot/tools/tscn_lint.py godot/scenes/*.tscn`,
  `python3 godot/tools/check_refs.py godot` (ext_resource, preload, dan `$Node/Path`), dan
  `python3 godot/tools/particles_lint.py godot` (properti CPUParticles2D vs GPUParticles2D).
- **CPUParticles2D ≠ GPUParticles2D.** Node CPU tidak punya `process_material`:
  semua parameter emisi adalah properti node (`direction`/`gravity` = **Vector2**,
  skala = `scale_amount_min/max`). Node GPU kebalikannya — semua di
  `ParticleProcessMaterial` (Vector3, `scale_min/max`). Tertukar = tidak ketahuan
  saat parse, tapi runtime melempar
  `Invalid assignment of property or key 'process_material' ... on a base object of type 'CPUParticles2D'`
  tepat saat FX dipakai. Semua partikel game (cuaca map, aura boss, burst hero,
  impact proyektil skill, wind Kaizen) memakai CPU supaya aman di renderer
  Compatibility Android/GLES; `particles_lint.py` menjaganya.

## Parse error: `Cannot infer the type` / autoload gagal dikompilasi

`var nilai := ekspresi` hanya aman kalau tipe ekspresi diketahui saat compile.
Hasil lookup `Dictionary` atau pemanggilan method lewat variabel dinamis
(seperti `db`, `cs`, atau `status`) tidak selalu bisa diinfer. Gunakan tipe
hasil yang eksplisit, misalnya `var p: Dictionary = db.passive(item_id)` atau
`var amount: float = cs.calc_skill_damage(hero, mult)`.

Deklarasi terkait sudah diperbaiki di `ItemInventory`, `SkillBook`, `CombatSystem`,
`TowerDB`, dan `Main`. Error kompilasi pada `Hero.gd` / `Tower.gd` serta kegagalan
autoload adalah efek berantai dari script dependensi, bukan scene yang hilang.

Validasi dengan **binary Godot** dari root repository (pemeriksa statis di atas
mengecek sintaks/referensi, bukan inferensi tipe GDScript):

```bash
godot --headless --path godot --editor --import
godot --headless --path godot --quit-after 120
```

Pastikan log tidak mengandung `SCRIPT ERROR`, `Parse Error`, atau `Compile Error`;
exit code editor saja tidak cukup karena Godot bisa tetap keluar dengan kode 0.

### Parse error: `Too many arguments for "get()"` di AIPlayer / Node

`Dictionary.get(key, default)` boleh menerima dua argumen, tetapi `Object.get(property)`
(hanya satu argumen) yang dipakai untuk node dari `get_nodes_in_group()` atau hero
hidup. Perbaikan terkait:

1. Lane minion di `AIPlayer._assign_hero_lane()` memakai `m.get("lane")` (bukan default).
2. Minion menyimpan `lane`, diteruskan `Main` lewat `GameManager.spawn_minion()` untuk
   kedua tim; default `"mid"`, argumen keempat tetap pengali stat.
3. `Hero.die` menaikkan `killer.kills` lewat `killer.get("kills")` (satu argumen).
4. `ItemDB.is_magic_hero` / `suggest_item` membaca role & range lewat helper yang aman
   untuk Node **dan** Dictionary (dipakai AI saat beli item).

Error `Main.gd: Failed to compile depended scripts` dan `Nonexistent function 'new'
in base 'GDScript'` adalah efek berantai karena script AI gagal dikompilasi — jangan
mengganti `.new()` atau menghapus AI dari Main. Uji regresinya (setelah import):

```bash
godot --headless --path godot res://tests/AIPlayerTest.tscn --quit-after 120
```

Harus muncul `[AIPlayerTest] PASS` tanpa error script. Tes memuat Main, memeriksa lane
wave kedua tim, dan memastikan AI memilih minion biru hidup terdekat di lane paling
ramai (atau menara terdekat jika tidak ada minion). Juga menutup regresi
`Object.get(prop, default)` pada `Hero.die` (atribusi kill) dan
`ItemDB.suggest_item` / `is_magic_hero` (dipakai AI beli item). Tes tidak memulai
match atau menulis save.

Smoke battle (menu → level 1 → hero/minion/wave/AI), setelah import yang sama:

```bash
godot --headless --path godot res://tests/BattleSmokeTest.tscn --quit-after 180
```

Harus muncul `[BattleSmokeTest] PASS` tanpa error script.

Cinematic (Fase 5d: intro level pause+skip, banner boss, FX kematian +
perayaan true boss), setelah import yang sama:

```bash
godot --headless --path godot res://tests/CinematicTest.tscn --quit-after 960
```

Harus muncul `[CinematicTest] PASS`. `--quit-after` dihitung FRAMES (bukan
detik); tes menunggu animasi berbasis waktu nyata (fase kematian 60/90 frame
+ perayaan), jadi jangan turunkan di bawah ~900.

`Unable to open Android 'build-tools' directory` adalah masalah konfigurasi SDK
editor yang **terpisah**. Jika ingin export Android, instal Android SDK Build-Tools
melalui SDK Manager dan arahkan **Editor Settings → Export → Android → Android SDK
Path** ke root SDK (yang berisi folder `build-tools/`), bukan ke folder build-tools
itu sendiri. SDK Android tidak dibutuhkan untuk menjalankan versi desktop dengan F5.

## Gameplay yang sudah diport (2026-09-06)

| Sistem pygame | Port Godot | Catatan |
|---|---|---|
| `Tower` + `TOWER_UPGRADE_PATHS` (4 jalur, Lv1-6) | `scenes/tower/Tower.gd` + `scripts/core/TowerDB.gd` + `data/towers.json` | Archer (Lv6 double shot) · Cannon (splash + burn) · Ice (slow + atk slow, Lv6 AOE) · Mage (chain + skill down + anti-heal). Build 100g, upgrade 175/325/550/850/1300, shield = 40% HP, HP regen 0.3/frame setelah 5s tanpa damage, Regen Shield 850g (Lv4+) |
| `Castle` + `NEXUS_LEVELS` | `scenes/base/Nexus.gd` + `data/nexus.json` | Lv1 4000 HP → Lv5 15000 HP, Castle Shield menyerap 1:1 lalu sisa damage −88%, shield gratis sampai wave 10 lalu 850g, upgrade mempertahankan rasio HP + shield. Level castle awal dari levels.json: Radiant `starting_castle_level`, Dire `castle_start_level` **hanya di hard** (paritas `_core.py:1504-1508`) |
| menang/kalah | `GameManager.end_match()` + `HUD` banner | Nexus Dire hancur = VICTORY, nexus Radiant hancur = DEFEAT. Meta reward paritas `_grant_meta_reward` (`_core.py:2365-2456`): menang pertama `meta_gold_reward_win` (3000), replay win 1500 sekali lalu 200 unlimited (via `replay_reward_counts`), kalah 0 — ditulis ke save kunci `meta_gold`, guard `_meta_reward_granted`. `ENTER` = level berikutnya |
| `MenuState` + Menu pygame | `scenes/ui/MainMenu.gd` | State machine MAIN/LEVEL_SELECT/HERO_SHOP/SETTINGS/HOW_TO_PLAY/CREDITS/PAUSE, dibangun 100% dari kode (pola HUD/ShopPanel). LEVEL_SELECT: 54 kartu dari `BossDB.levels` + kunci `unlock_after_level` (`is_level_unlocked` paritas `level_data.py:2318`) + pemilih difficulty. HERO_SHOP: unlock hero pakai meta gold (paritas `_unlock_hero_in_meta_shop` `_core.py:5298`) → `SaveManager.unlock_hero()` |
| progresi level | `GameManager.next_level()` / `is_replay` + `GameManagerConnector.starting_level` | ENTER setelah menang → `get_next_level` paritas (`level_data.py:2340`); replay → `is_replay=true` (paritas `main.py:576`). Connector tidak lagi hardcoded level 1: `start_match(n)` dipanggil menu |
| enemy scaling hard | `GameManager.enemy_*_mult` + `Main`/`Boss`/`Minion` | `enemy_scaling_enabled = (difficulty == "hard")`; hp ×1.15, damage ×1.10 dari levels.json (`_core.py:1476-1483`). Diterapkan saat spawn: minion merah `apply_enemy_scaling` (`_core.py:1792-1796`), mini/true boss `apply_scaling` (`_core.py:1822/2097`) |
| unlock hero boss | `GameManager._auto_unlock_defeated_boss_heroes()` | Boss mati → `boss.gold_reward` langsung ke gold/skor pemain + `unlocked_bosses` persisten (termasuk saat kalah), SLAYER khusus last-hit hero blue dan popup `+nG` di map. Menang → hero-nya baru gratis masuk `unlocked_heroes` (paritas `_core.py:2113-2163/2322-2355`; `BossDeathRewardParityTest` FASE 14); kalah = tidak dapat hero gratis. Boss yang dikalahkan tapi belum dimenangkan → bisa DIBELI 4500 meta gold di HERO SHOP |
| `main.py` (entry point: boot, loop, lifecycle) | `scripts/autoload/AppShell.gd` | Autoload PALING AKHIR (butuh AudioManager + SaveManager siap). Port lapisan aplikasi: banner boot + `crash_log.txt` di `user://`, BGM/ambient sejak boot (menu tidak lagi diam), kebijakan loop (`physics_ticks_per_second=60` + `max_physics_steps_per_frame=4` = `MAX_CATCHUP` `main.py:332`), preset kualitas + adaptive quality (jendela 90 frame, 26/52 FPS, cooldown 180/300), batas FPS `min(setting, target)` di perangkat sentuh, dan pembekuan audio saat app ke latar. Splash boot dipasang `Main._maybe_show_splash()` (dulu `SplashScreen.gd` node yatim). Uji: `res://tests/MainEntryParityTest.tscn` |
| `SoundManager` + `mobile/combat_audio.py` | `scripts/autoload/AudioManager.gd` | BGM `bgm_track` per level (`start_level` → `play_bgm`), SFX UI/victory/defeat, **suara tempur penuh** (lihat baris berikut). Volume = `MASTER_VOLUME 0.7` × slider sfx/bgm dari `SaveManager.data["settings"]` — paritas `SoundManager.play` (`_system.py:589-598`), dibaca dari memory jadi tidak ada tulis file per frame. Aset 24 berkas audio disalin converter ke `godot/assets/sounds/` (di-gitignore) — **16 WAV + 7 Ogg Vorbis + 1 MP3**: nama `.wav` di `assets/sounds/` tidak selalu RIFF (SDL_mixer pygame mengendus isi berkas), sedangkan Godot memilih importer dari EKSTENSI, jadi `audio_container_ext()` di converter meluruskan ekstensi salinannya dan `_scan_sounds()` menerima ketiganya (`AUDIO_EXTS`). Kunci stream tetap nama tanpa ekstensi, jadi `play("ui_click")` tidak berubah |
| suara tempur (`combat_audio.py` skema v35) | `AudioManager.play_combat()` + 14 call site | 7 jenis suara: `hero_melee`/`hero_ranged` (Hero **dan** Boss, ambang jarak 100), `tower_archer`/`tower_cannon`/`tower_ice`/`tower_mage` (tim biru 1.0 / merah 0.8), `minion_hit` (semua jenis minion). Tiga pengaman pygame ikut: jeda per jenis 90/110/140 ms, anggaran 4 suara/frame, volume dasar 0.50-0.78. Ditambah `minion_death` 0.7 (throttle 120 ms), `goblin_spawn` 0.7, `hero_spawn`, `hero_skill` (volume per tombol q .8/w .6/e .7/r 1.0), `wave_start` 0.6, `nexus_hit` 0.7 (hanya castle biru, hanya kalau HP benar-benar turun), `tower_destroyed` 0.8, `explosion` (boss 1.5/1.0 `force`, splash cannon 0.3), `ui_sell`/`ui_upgrade`/`ui_buy`/`ui_error` dari `ShopPanel._run()`. Statistik penolakan dicetak 10 detik sekali, bukan per event |
| `map_components/themes.py` (54 palet) | `data/themes.json` + `ArenaMap._load_themes()` | `export_themes()` di converter mengubah tuple RGB pygame → hex; `ArenaMap` merge ke palet runtime saat `_ready` (const `THEMES` tidak bisa di-merge langsung: Dictionary const Godot 4 read-only rekursif). Warna palet dari JSON, `modulate`/`light`/`energy` tetap kurasi manual untuk 4 tema pertama. Nama tak dikenal → forest (paritas `get_theme`). Dekor ikut tema **dan ikut sisi peta**: pohon rimbun/batu berlumut hanya di Radiant, pohon mati (`has_dead_trees`) + tulang (`has_bones`) + nisan (`has_gravestones`) hanya di Dire — paritas `generate_all` (`_bundle.py:4767-4821`) yang memakai `_is_radiant()`/`_is_dire()`. Ambang jenis ditumpuk supaya jenis opsional jadi aksen (ambang tetap bikin tema ice keluar 49 kristal dari 70). Jalur juga memakai `path_moss`/`path_crack` (`_draw_cobblestone_tile` `:5206`) — tema volcanic = retakan lava menyala |
| `DynamicRenderer` partikel + fog (`map_components/_bundle.py:5370-5560`) | `ArenaMap._apply_weather()` + 2 `CPUParticles2D` | `particle_type` & `fog_*` tiap tema diekspor `export_themes()` lalu dipakai, bukan cuma disimpan. Yang ditiru adalah **gerak**, bukan warna: snow turun (`vy 0.3..0.8` px/frame `:5398-5400`), ember/acid naik (`vy -0.8..-0.3` `:5405-5408`), sand/mist menyapu mendatar (`vx 0.5..1.5` `:5401-5404`), firefly/ash/spirit melayang. Nilai px/frame pygame dikali 60 (`PYGAME_FPS`) jadi px/detik. Kabut = lapisan tipis dari `fog_color` + `fog_alpha` + `fog_count`. `CPUParticles2D` dipilih (bukan GPU) supaya aman di Android/GLES. Tipe `ash`/`spirit`/`mist`/`acid` yang di pygame TIDAK tergambar (tidak ada cabang di `_draw_particles`) di sini tergambar |
| `SoundManager.play_ambient` (`_system.py:688-710`) | `AudioManager.play_ambient()` / `stop_ambient()` | Loop `ambient_forest` di `AudioStreamPlayer` TERPISAH dari BGM (pygame juga pakai `ambient_channel` sendiri), volume `MASTER_VOLUME × ambient_volume 0.25 × 0.8` — pengali 0.8 dari call site `main.py:164`. Fade masuk 2 dtk / keluar 1,5 dtk (`fade_ms` pygame). Mulai di `GameManager.start_level()`, berhenti di `end_match()` + `return_to_menu()`, dibekukan saat menu PAUSE. Loop dipaksa lewat sinyal `finished` (jangan bergantung pada flag loop hasil import .wav) |
| `Game._generate_build_slots_from_lanes` | `Main._generate_build_slots()` | 3 slot × 3 lane × 2 tim, fraksi persis pygame (top/bot 0.15/0.30/0.45, mid 0.10/0.25/0.40, Dire dicerminkan) |
| `hero_skills/_bundle.py` (6 kelas skill) | `scripts/skills/SkillBook.gd` | Q = `skill_cooldown` hero (Kaizen 300f, Grimjaw 420f, Sylara 360f), W 4s, E 7s, R 15s + CDR item. Hero tanpa tabel memakai skill generik |
| `hero_items.py` (33 item, 6 slot) | `scripts/items/ItemDB.gd` + `ItemInventory.gd` + `data/items*.json` | Harga flat 4500g, cap atk speed 0.2-2.5 / lifesteal 1.75 / CDR 0.5 / skill amp 0.5 / evasion 0.5 / move speed 0.4, pasif Cleave + Corroder, 4 aura (Steel Aegis, Everfrost, Solar Brand, Searbrand) |
| `hero_items.get_icon` + `_ICON_CACHE` (`hero_items.py:1661-1699`) | `scripts/utils/ItemIcons.gd` + `ItemDB.item_icon()` | **Aset ikon item ikut termigrasi**: 33 PNG `assets/items/` disalin converter (`--assets`) ke `godot/assets/items/` (ikut repo supaya ikon asli tampil juga di editor/export lokal) dan dimuat lewat penjaga `ResourceLoader.exists()` → `load()`, lalu **di-scale CPU ke ukuran tampilan** (paritas `smoothscale` `hero_items.py:1678`) dan di-cache per (item, ukuran) — paritas `_ICON_CACHE`, sekaligus hemat VRAM: 33 ikon 256 px mentah ≈ 8,6 MB jadi ±150 KB untuk tampilan 20-26 px. PNG tidak ada → badge prosedural `ImageTexture` (kotak `color` radius 6 + border `glow` 2 px = geometri fallback pygame; deviasi: tanpa label 5 huruf karena `Button.icon` hanya menerima `Texture2D` dan Godot tidak punya raster font→Image). Pemakai: 6 chip slot item `SkillBar` (30 px, ikon 26 px = `SLOT_SIZE-4`, bg gelap + border warna katalog 2 px — paritas `_draw_slots` `:3026-3095`) dan baris toko `ShopPanel` tab ITEM (`Button.icon` + `expand_icon` + `clip_text`). Dikunci `HeroItemsParityTest._test_icons` + `tools/test_godot_asset_pipeline.py` |
| `HERO_LEVELS` (Lv1-15) | `data/hero_levels.json` + `HeroDB.level_data()` | hp/damage/skill multiplier per level, biaya upgrade 300 → 8000, boss hero ×1.6 |
| ekonomi `_core.py` | `GameManager._process()` | `(3 + 0.3×(level−1)) × pengali_difficulty` gold/s, gold awal `(350 + 100×(level−1)) × pengali`, pecahan disimpan sebagai milli-gold (persis loop 60-frame pygame), AI tim Dire menabung dengan laju sama |
| `AIPlayer` (6000+ baris) | `scripts/systems/AIPlayer.gd` + `Hero.gd` | Port penuh: `_ai_brain`/`_ai_elite` (`_entity.py:6027-6051`), `_ai_reserve` (tabungan draft hero), `think_timer` + beberapa aksi per tick, `_ai_step` 6 prioritas (build menara → beli hero → upgrade hero → beli item → upgrade menara → Regen Shield → Castle Shield → nexus). Gold dipakai dari `GameManager.ai_gold` (pygame `AIPlayer.gold`). Item dibeli pakai `ItemDB.suggest_item()` = paritas `hero_items.suggest_item_for_hero` (`hero_items.py:2936`); kontrol hero per-frame `_control_heroes()` + `_assign_hero_lane()`; **retreat HP <20% → base → heal → keluar di 80%** ada di `Hero.gd` (paritas `_entity.py:3983-4028`); **kombo auto-cast R→E(2+)→W(<40%)→Q** paritas `_try_auto_cast` (`_entity.py:4149-4240`); Kaizen Q Steel Wind↔Dash Strike bergantian di `SkillBook` (paritas `_bundle.py:3969`) |
| mini boss / true boss | `Main._boss_tick()` | Mini boss dari `levels.json["mini_bosses"]` (satu aktif pada satu waktu), true boss setelah 6 menara Dire hancur (`_core.py` 2089) |
| efek percikan/ledakan (`_render.py:418-571` + `EffectManager` `:601-800`) | `scripts/render/{HitSpark,DeathBurst,SparkField}.gd` + `scenes/fx/SparkLayer.gd` | **FASE 26.** Percikan kena pukulan (minion 4 / boss 6 / nexus 10, hero & menara 0) dan ledakan kematian (minion `medium`, boss `large`, taktik GATHER + PROTECT CASTLE `small` biru) — gravitasi 0.15, gesekan 0.95, alpha `int(255·sisa)`, palet per tim, kilat pusat 8 frame. Lapangan global 1 field = 1 `EffectManager` pygame: cap **500 partikel / 80 ledakan**, yang terbuang yang TERTUA. Data di `GameManager.spark_fx` (tick 60 Hz), gambar di z 800 |
| `PathPreview` (`_render.py:1275-1370`) | `scenes/fx/PathPreview.gd` | **FASE 26.** Panah lane 120 frame tiap wave dimulai (dulu tidak ada padanannya sama sekali): fade in 20 / out 40, `alpha = int(200·ratio)`, `offset = int(t·2) % 20`, panah tiap 8 titik, arah dari titik `i+4`, pulse `(i//8 + offset//5) % 4`, panah 8 px (pulse) / 5 px (redup, alpha//2). z 790, di bawah percikan (pygame menggambar path preview paling awal) |

### Deviasi yang disengaja (dicatat, bukan bug)

- **Menu utama disederhanakan dari pygame.** Tidak diport: multi-slot save (SLOT_SELECT), dialog TOP UP hero gold + voucher, cloud save Play Games, slider master/voice volume, dan kunci difficulty `run_difficulty` (di Godot difficulty bebas diganti; pygame menguncinya sampai semua level tamat — `_core.py:2416-2430`). Sisanya (state, kunci level, reward, hero shop) paritas.
- **`hp_regen` item sekarang benar-benar dipakai.** Di pygame `HeroItemInventory.get_hp_regen()` ada tapi tidak pernah dipanggil `_entity.py`; di Godot diterapkan sebagai HP/detik (dekat base 180 HP/s, di luar base 9 HP/s + regen item).
- **17 item aktif SUDAH diport** (`ItemInventory.tick()`), tapi **tanpa tombol** — dan itu memang benar: di pygame item aktif semuanya *auto-trigger*, tiap deskripsi menulis "(auto)" (`hero_items.py:628/668/1283`). Pemicunya cuma tiga: `hp_threshold` (HP turun), `trigger_enemies` (N musuh dekat), atau punya target. Menambah hotbar justru menyimpang dari sumber kebenaran. Satu pengecualian: Static Charge (`thunder_coil`) terpicu saat pemilik KENA damage dengan peluang 20% (`on_damage_taken` `hero_items.py:2449`), bukan saat menyerang — disambung lewat `Hero.take_damage`.
- **Efek on-attack** (Bash, Piercing Bash, Arc Chain/Lightning, Frostbite, Miasma + Polycephaly multishot, Empower Strike, Entangle) dipanggil dari `Hero.try_attack` untuk melee dan `TowerBullet._on_hit` untuk proyektil hero — meniru dua pintu pygame (`on_basic_attack_hit` / `on_ranged_attack_hit`). Keduanya bermuara ke `ItemInventory.on_attack_hit()`, padanan `_on_hit_common` (`hero_items.py:2519-2666`), dengan urutan proc yang sama persis. Lifesteal & cleave TIDAK ikut di jalur ranged karena di pygame sudah dibayar saat proyektil dilepas.
- **`on_attack`, `bash`, `multishot`, dan pasif sudah diport** (Fase 5b): Arc Chain/Lightning, Frostbite, Miasma + Polycephaly multishot, Entangle, Bash/Piercing Bash, Empower Strike, Leviathan Vitality — semuanya lewat `ItemInventory.on_attack_hit()`.
- **Proyektil skill = visual homing, damage tetap instan** — paritas `_spawn_skill_projectile` pygame (`_entity.py:4509-4530`): proyektil `damage=0` + `is_skill` hanya memberi visual terarah, damage otoritatif tetap instan di `SkillBook` (sama seperti pygame — `hero_skills/_bundle.py` yang menghitung damage). Implementasi: `scenes/fx/SkillProjectile.gd` (Node2D self-drawn, pola `TowerBullet`), dipanggil dari 3 call site paritas — Sylara R Powershot per musuh kena (`_bundle.py:4461`), Vex Q Arcane Orb (`:4820`), Vex E Astral Imprisonment (`:4924`). Batas 6/hero, umur 72f (target mati 36f), jarak 380px, snap ke target + impact FX hanya kalau target masih hidup — semua `_entity.py:3225-3232 / 3827-3943`. Satu deviasi kecil: peluru basic attack (`TowerBullet`) tidak ikut dihitung dalam cap-6; node terpisah dengan umur 4 detik + mati saat target mati. Gambar panah/orb = port fallback `_draw_projectile` (`_entity.py:4976-5210`); ornamen per-hero `heroes/*_fx.draw_arcane_orb` adalah fase visual terpisah.
- **AI dire**: roster kosong, saldo awal 350, income 3 + nomor wave; pembelian mempertahankan kepemilikan hero yang mati agar tidak duplikat. Statistik `total_built`/`total_upgraded`/`total_skills_cast` belum diport. Lihat audit paritas untuk batasan lain.
- **`play_positional` (`_system.py:615-629`) sengaja TIDAK diport.** Tidak ada satu pun call site di repo pygame — dead code, jadi tidak ada yang bisa dijaga paritasnya.
- **Preset kualitas `mobile.perf.Quality`** (yang di pygame mengurangi jumlah partikel/fog di HP kentang) tidak ikut diport ke cuaca Godot: pengurangan beban di sana urusan setelan render Godot, bukan cabang `try/except import` per tema.
- **Aura TRUE BOSS sekarang digambar** (`Boss.gd::_draw`, paritas `_draw_true_boss_aura` `bosses/base_boss.py:6351-6375`): penanda kelas yang di pygame menyala setiap frame selama true boss hidup — `aura_r = radius + 15`, 8 langkah 2 px, alpha `(aura_r - r) * 5 * pulse`, denyut `sin(pulse) * 0.3 + 0.7` dengan `pulse += 0.1`/frame (= `PULSE_SPEED` 6 rad/detik). Mini boss tidak punya. **Jebakan yang perlu diingat:** `pygame.draw.circle` TIDAK mem-blend — ia menimpa piksel di surface SRCALPHA, jadi 8 lingkaran itu gradien BERPITA, bukan tumpukan. `draw_circle()` Godot mem-blend, sehingga port naif membuat pusat aura ~3x lebih pekat (144/255 vs 49/255 pada pulse 0,7). Implementasi Godot memakai 1 cakram inti + 6 cincin `draw_arc` yang tidak saling menimpa; profilnya diuji melawan surface pygame asli di `tools/test_boss_true_aura_parity.py` (46 cek, plus `tools/boss_true_aura_parity.png` lewat `--shot`). Aura `ability_active` dan `is_enraged` belum diport karena mekanik enrage/ability boss memang belum ada di Godot. Node `FX/Aura` (partikel) tetap mati — itu upgrade, bukan baseline pygame.
- **Flash putih saat kena damage = `hurt_flash_timer` pygame, dideteksi dari `hp` yang turun.** `scripts/render/HurtFlash.gd` dipakai bersama Hero/Minion/Boss: 8 frame @60fps (`DURATION = 8.0/60.0`) turun linear, targetnya `silhouette.flash_amount` → `custom_visual.modulate` → fallback (`hit_flash_mat` hero / `body` minion / `sprite` boss). **Deteksinya menonton `hp`, bukan hook di `take_damage()`** — persis alasan pygame menaruhnya di `update()` (`_entity.py:5545-5551`, `bosses/base_boss.py:609-610`): damage masuk dari banyak pintu, dan di port Godot `take_damage()` hampir tidak pernah dipanggil karena `Hero._attack`, `TowerBullet`, `SkillBook`, item, dan reflect semuanya memanggil `CombatSystem.apply_damage()` langsung. Satu pengecualian yang disengaja: **hero** memakai `watch_hp = false` (flash hanya lewat `trigger()` dari `take_damage`/`play_hit_fx`), karena pygame tidak punya hurt flash hero dan menyalakannya tiap pukulan sama saja dengan memberi flash pada serangan dasar — dilarang kontrak di atas. Minion: pygame MENYIMPAN `hurt_flash_timer` tapi tidak pernah menggambarnya (tidak ada cabang di draw minion); di Godot digambar, sejalan dengan keputusan yang sama pada partikel cuaca `ash`/`spirit`/`mist`/`acid`.
- **Impact FX korban = SKILL saja, serangan dasar NOL FX.** Kontrak pemilik game (dikunci `tools/test_basic_attack_no_impact_fx.py`; komentar sumber `_entity.py:4376-4384`): benturan serangan dasar tidak boleh memicu flash/spark/shockwave/hit-stop, karena di combat ramai tumpukannya menutupi sprite. Karena itu `Hero.play_hit_fx()` (burst `FX/HitParticles` + flash putih) di-hook dari `SkillBook._damage()` — BUKAN dari `Hero.take_damage()` atau `CombatSystem.apply_damage()` yang dilewati semua jalur damage termasuk basic attack, tower, dan minion. Warna burst mengikuti `fill_color` caster supaya terbaca siapa yang memukul; ada jeda 0,08 detik per hero (`HIT_FX_COOLDOWN`) supaya skill AoE + ticker DoT tidak saling membatalkan burst lewat `restart()`. Minion/boss belum punya node partikel korban, jadi `has_method("play_hit_fx")` melewatinya dengan aman.
- **Efek `EffectManager` (percikan/ledakan/panah lane) memakai rasio partikel 1.0, bukan 0.70 pygame.** `add_hit_particles` pygame dikalikan `mobile.perf.Quality.particle_ratio`, dan preset HIGH desktop (`mobile/perf.py:499`) memberi **0.70**, jadi pygame sebenarnya memunculkan 3/4/7 percikan untuk minion/boss/nexus, bukan 4/6/10. Port Godot memakai 1.0 karena lapisan adaptive quality memang belum diport (lihat `docs/SYSTEM_PY_COVERAGE.md` §3) — `SparkField.particle_ratio` / `particles_enabled` tersedia sebagai knob supaya port perf nanti tidak perlu menyentuh berkas lain. Fakta pygame-nya direkam di fixture (`py_quality`) dan dikunci `RenderFxParityTest._test_wiring`.
- **Percikan/ledakan memakai RNG global, bukan stream `ParityRng` yang dikunci.** Pygame memakai `random.uniform/randint/choice` global; yang dijaga paritas adalah NILAI dan URUTAN roll per partikel (angle → speed → warna → spark → lifetime), yang di harness di-replay lewat RNG ter-script dan di produksi dari RNG global. Hasilnya percikan tidak identik antar-build — sama seperti pygame.
- **Raster efek tidak dibandingkan piksel demi piksel.** `draw_circle`/`draw_colored_polygon` Godot vs sprite hasil `transform.scale` + `blit` pygame; yang dikunci geometri (pusat, radius, titik), warna+alpha, dan urutan perintah gambar per frame. Headless Godot tidak bisa screenshot.
- **Sekolah damage** diambil dari penyerang (`DamageSchool.resolve`), dot `fire`/`ice` netral — paritas `resolve_damage_school` pygame.

## Skill hero: GDScript (default) atau C++ godot++ (opt-in)

`hero_skills/_bundle.py` punya **dua** port yang dibangkitkan dari AST Python
yang sama, dan `Hero.gd` tidak tahu mana yang jalan:

```
hero_skills/_bundle.py
  ├─ tools/gen_hero_skill_kit.py  -> scenes/hero/HeroSkillKit.gd   (GDScript, default)
  └─ tools/gen_hero_skills_cpp.py -> gdext/mystic_skills/src/*.cpp (C++ GDExtension)
                                        │ scons + godot-cpp
                                        ▼
                     addons/mystic_skills/bin/libmystic_skills.<platform>.<target>.<arch>.so
                                        │
              scenes/hero/HeroSkillKitLoader.gd  <- const HeroSkillKit di Hero.gd
```

Default `mystic/skills/use_gdext_skills=false`: semua skill jalan lewat
GDScript, **tanpa butuh compiler**. Untuk mencoba jalur native:

```bash
cd godot/gdext/mystic_skills
git clone -b godot-4.3-stable --depth 1 https://github.com/godotengine/godot-cpp godot-cpp
scons platform=linux target=template_debug -j4
# lalu set mystic/skills/use_gdext_skills=true di project.godot (atau
# HeroSkillKitLoader.force_backend("gdext") dari kode/harness)
```

Kalau lib tidak ada, loader jatuh ke GDScript tanpa error — jadi F5 di mesin
tanpa toolchain tetap normal. Paritas jalur C++ dijaga
`tests/HeroSkillGdextParityTest.tscn` (oracle Pygame 222 hero × 4 skenario +
A/B backend) di workflow `godot-gdext.yml`; kesegaran kedua generator dijaga
`gen_hero_skill_kit.py --check` + `gen_hero_skills_cpp.py --check` di
`godot-check.yml`. Rincian: `docs/HERO_SKILLS_GODOTPP.md`.

## Katalog level: GDScript (default) atau C++ godot++ (opt-in)

`levels/level_data.py` (54 level × 17 field + 4 helper) punya **dua** port dari
satu sumber, dan `BossDB` / `GameManager` / `SaveManager` tidak tahu mana yang
jalan:

```
levels/level_data.py
  ├─ tools/convert_to_godot.py -> data/levels.json -> scripts/core/LevelDB.gd   (GDScript, default)
  └─ tools/gen_levels_cpp.py   -> gdext/mystic_levels/src/*.cpp  (C++ GDExtension)
                                        │ scons + godot-cpp
                                        ▼
                     addons/mystic_levels/bin/libmystic_levels.<platform>.<target>.<arch>.so
                                        │
                     scripts/core/LevelDBLoader.gd  <- BossDB.load_levels(),
                                                       GameManager.level_count()/
                                                       next_level_number()/is_level_unlocked()
```

Default `mystic/levels/use_gdext_levels=false`: katalog jalan lewat GDScript,
**tanpa butuh compiler**. `LevelDB.gd` memulihkan tipe Python yang hilang di
`JSON.parse_string` (semua angka Godot jadi float) lewat `FIELD_KINDS`. Untuk
mencoba jalur native:

```bash
cd godot/gdext/mystic_levels
git clone -b godot-4.3-stable --depth 1 https://github.com/godotengine/godot-cpp godot-cpp
scons platform=linux target=template_debug -j4
# lalu set mystic/levels/use_gdext_levels=true di project.godot (atau
# LevelDBLoader.force_backend("gdext") dari kode/harness)
```

Kalau lib tidak ada, loader jatuh ke GDScript tanpa error — F5 di mesin tanpa
toolchain tetap normal. Paritas dijaga tiga lapis: `tools/test_godot_level_data_parity.py`
(statis, 5.162 cek: levels.json + FIELD_KINDS + literal tabel C++ vs
`level_data.py`, tanpa engine), `tools/test_levels_cpp_selftest.py`
(**menjalankan** `levels_processor.cpp` lewat stub Variant — butuh g++ saja,
±2 detik), dan `tests/LevelDataParityTest.tscn` /
`tests/LevelDataGdextParityTest.tscn` (replay fixture oracle di engine; yang
kedua memaksa backend C++ + A/B) di workflow `godot-gdext.yml`. Rincian:
`docs/LEVELS_GODOTPP.md`.

## Splashscreen: GDScript (default) atau C++ godot++ (opt-in)

`splash_screen.py` (logo + judul + tagline + 46 partikel + latar gradien/vignette
+ glow judul + hint skip) punya **dua** port model dari satu sumber, dan
`scenes/ui/SplashScreen.gd` tidak tahu mana yang jalan — berkas itu tinggal
renderer yang mengambil SEMUA angka lewat `SplashBackend`:

```
splash_screen.py
  ├─ (oracle) tools/test_godot_splash_parity.py -> tests/fixtures/splash_parity.json
  ├─ scripts/ui/SplashModel.gd              (GDScript, default)
  └─ tools/gen_splash_cpp.py -> gdext/mystic_splash/src/*.cpp (C++ GDExtension)
                                        │ scons + godot-cpp
                                        ▼
                     addons/mystic_splash/bin/libmystic_splash.<platform>.<target>.<arch>.so
                                        │
                       scripts/ui/SplashBackend.gd  <- const Backend di SplashScreen.gd
```

Default `mystic/splash/use_gdext_splash=false`: splash jalan lewat GDScript,
**tanpa butuh compiler**. Untuk mencoba jalur native:

```bash
cd godot/gdext/mystic_splash
ln -s ../godot-cpp godot-cpp   # atau: git clone -b godot-4.3-stable --depth 1 \
                               #   https://github.com/godotengine/godot-cpp godot-cpp
scons platform=linux target=template_debug -j"$(nproc)"
# lalu set mystic/splash/use_gdext_splash=true di project.godot (atau
# SplashBackend.force_backend("gdext") dari kode/harness)
```

Kalau lib tidak ada, backend jatuh ke GDScript tanpa error (satu baris log) —
F5 di mesin tanpa toolchain tetap normal. FASE 38 juga menutup dua deviasi
splash yang sudah ada di produksi: latar kini **hitam pekat + rim 2 px**
(alpha vignette pygame menjenuh ke 255 pada `i <= 24`, jadi 48 batang gradien +
70 bingkai vignette digambar apa adanya), dan skip memakai **elapsed TOTAL**
(`skip()` pygame hanya menyetel bendera; `done` dihitung `update()` frame
berikutnya) — bukan timer sejak tombol ditekan. Paritas dijaga empat lapis:
`tools/gen_splash_cpp.py --check` (transpile segar),
`tools/test_godot_splash_parity.py` (oracle: MENJALANKAN pygame ASLI, 613 cek +
audit wiring/arity/semantik argumen sweep/ruang lingkup identifier GDScript), `tools/test_splash_cpp_selftest.py` (**menjalankan**
`splash_processor.cpp` lewat stub Variant — butuh g++ saja, 1.585 cek dengan
checkout godot-cpp / 1.580 tanpa, 6.524 perintah), dan `tests/SplashParityTest.tscn` / `tests/SplashGdextParityTest.tscn`
(replay fixture di engine; yang kedua memaksa backend C++ + A/B seluruh API) di
workflow `godot-gdext.yml`. Rincian: `docs/SPLASH_GODOTPP.md` +
`gdext/mystic_splash/README.md`.

## Asset Pipeline

- `godot/data/*.json` — hasil convert, dibaca `HeroDB`/`BossDB`/`ArenaMap`. Ikut repo (bukan
  gitignore), jadi port jalan tanpa menjalankan converter dulu; `themes.json` tidak ada →
  `ArenaMap` mundur ke 4 palet const `THEMES`.
- `godot/assets/units/*.png` + `godot/data/baked_units.json` — strip bake 222 unit
  (Fase 5, lihat bagian "Strip bake 222 unit" di atas). **Ikut repo** — bukan duplikat
  file yang sudah ada (suara) melainkan satu-satunya salinan visual ter-bake; tanpa ini
  arena kembali ke `UnitSilhouette`, bukan error.
- `godot/assets/maps/*.png` + `godot/data/map_bakes.json` — bake map statik 54 tema
  (Fase 3, lihat bagian "Bake map statik (Fase 3)" di bawah). **Ikut repo** dengan alasan
  yang sama; tanpa ini `ArenaMap` mundur ke gambar prosedural, bukan error.
- `godot/assets/sounds/*` — **di-gitignore** (duplikat 15 MB dari `assets/sounds/`, sumber
  kebenaran tetap di sana). Jalankan converter setelah clone, kalau belum `AudioManager`
  no-op + log sekali dan game tetap jalan tanpa suara. Ekstensi salinan **diluruskan ke
  kontainer aslinya** (16 `.wav` + 7 `.ogg` + 1 `.mp3`): 8 berkas di `assets/sounds/` bernama
  `.wav` padahal isinya Ogg Vorbis/MP3 — pygame tidak peduli (SDL_mixer mengendus isi), Godot
  memilih importer dari ekstensi dan importer WAV menolak dengan `Not a WAV file ... found
  'OggS'` (8 SFX senyap, termasuk `victory` dan loop `ambient_forest`). Jangan rename sumbernya:
  `_system.py:543-574` merujuk literal `ui_click.wav` dkk.
- `godot/assets/items/*.png` — 33 ikon item ITEM FORGE, **ikut repo** (±3 MB; nama berkasnya
  field `icon` di `items.json`; converter `--assets` menyinkronkan dari `assets/items/`).
  Dibaca `scripts/utils/ItemIcons.gd`
  (port `hero_items.get_icon`, `hero_items.py:1661-1699`) dan dipakai `SkillBar` (6 chip slot item
  30 px, ikon 26 px = `SLOT_SIZE - 4`) + `ShopPanel` tab ITEM (`Button.icon` per baris). Kalau
  belum disalin, `ItemIcons` menggambar badge prosedural (kotak warna katalog radius 6 + border
  glow 2 px = cabang fallback `get_icon`) — toko tetap terbaca, hanya tanpa artwork.
- `godot/assets/presplash.png` — **di-gitignore** (duplikat 1,1 MB). Padanan `presplash.filename`
  buildozer (`buildozer.spec:79`): dipakai `application/boot_splash/image` di `project.godot`,
  dengan `boot_splash/bg_color` #0B0A12 = `android.presplash_color` (`:78`). Exporter Godot
  memaksa berkas mentah ini ikut PCK/AAB **hanya kalau ada di disk saat export**
  (`EditorExportPlatform::get_forced_export_files`) — karena itu CI menyalinnya sebelum export.
  Tanpa salinan: splash bawaan Godot + satu baris error "Non-existing or invalid boot splash".
- Ketiga salinan di-gitignore itu disalin satu perintah tanpa pygame/numpy:
  `python3 tools/convert_to_godot.py --assets` (CI: langkah "Salin aset biner (gitignored)" di
  `godot-check.yml` sebelum `--import`, dan di `build-android-godot.yml` sebelum export).
  Rantainya dikunci `tools/test_godot_asset_pipeline.py` (statis, tanpa engine).
- `godot/assets/shaders/outline.gdshader` — outline 1-pass + hit flash + rim light (ganti 5 blit manual pygame).
- `godot/shaders/hamon.gdshader` — hamon temper katana Kaizen (wave + temper cloud + attack pulse).

## Renderer (Pygame sebagai default)

`RendererRegistry.hero_scene()` mengutamakan strip bake untuk semua hero yang
memilikinya, **termasuk Kaizen** (`BakedSprite.tscn` + `baked_units.json`).
`UnitSilhouette` tetap fallback jika bake dan scene custom tidak tersedia;
minion masih memakai silhouette.

Rig hand-made di `RendererRegistry.HERO` bisa dicoba dengan
`Project Settings → mystic/rendering/experimental_hero_rigs = true`, atau
jalankan `scenes/demo/KaizenDemo.tscn` langsung. Default **false** supaya
visual Kaizen tidak diganti dengan desain lain ketika bermain normal.
Renderer boss memakai strip bake kecuali ada override di `BOSS`.

## Strip bake 222 unit (Fase 5 — Opsi A)

**Kenapa bake PNG, bukan port renderer prosedural per-hero ke GDScript?**
216 renderer boss (`bosses/level1..54.py`) + 6 hero masterwork
(`heroes/_bundle.py`, 16.723 baris) tidak realistis di-port 1:1 (Bulan +
tidak bisa diverifikasi paritasnya). Bake memakai **renderer pygame asli**
sebagai sumber kebenaran, jadi geometri/warna/pose tidak bisa drift.

```bash
# Hasil: godot/assets/units/<type>.png (222 strip, ±6,5 MB, ikut repo)
#        + godot/data/baked_units.json (manifest: frame/anchor/skala/fps)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    ~/.venv-mystic/bin/python tools/convert_to_godot.py --units-png
# --only gornak,sylara = debug 1 unit (manifest TIDAK ditimpa)
```

Per unit, strip berisi grid **[idle 8 | walk 8 | attack 8]** frame, 8
frame per baris (lebar maks 2.216 px — aman untuk batas tekstur 4096 px
GPU mobile), **anchor = telapak kaki** yang diratakan antar frame saat
bake (AnimatedSprite2D cuma punya satu offset untuk semua frame).
Mekanika pose mengikuti pygame persis:

| Aspek | Sumber pygame | Implementasi bake |
|---|---|---|
| fase idle/walk | `int(pulse*2) % 8` (`heroes/__init__.py:1777`, `HERO_ANIM_PHASES` `:1483`) | 8 sampel pulse rata |
| deteksi jalan | `_detect_moving` delta > 0.3 px (`bosses/level1.py:947-962`) | probe digeser 1.4 px/frame |
| pose serang | **mode manual** controller — "alat preview/tes ... hormati" (`bosses/level1.py:873-898`) | set `_XX_attack_progress` per frame |
| frame serang | diturunkan dari sisa timer, bukan jam (`bosses/level1.py:841-842`) | `drive()` memaksa frame dari `attack_progress` |
| skala hero lane | `_get_hero_scale` (`heroes/__init__.py:2148`, target tinggi 65 × global 0.78) | `hero_scale` di manifest → `sprite.scale` |
| skala boss | native 1.0 (`heroes/__init__.py:2873-2878`) | `boss_scale: 1.0` |
| fps idle/walk | fase baru tiap 10 frame hero / 5 frame boss (`_entity.py:1681` vs `base_boss.py:580`) | 6 fps hero / 12 fps boss |
| outline+rim | `_finish_hd_sprite` hanya jalur hero (`heroes/__init__.py:1866+`) | shader outline di `BakedSprite.tscn`, mati untuk boss |
| beam morgath | digambar live, di-skip saat cache (`heroes/__init__.py:2149-2151`) | tidak ikut strip (proyektil Godot yang menggambar) |

Kompresi: PNG palet 256 warna + alpha diperbaiki per entri palet (entri
alpha < 16 dipaksa 0) — 21 MB RGBA → 6,5 MB tanpa halo kotak samar di
area pad. Deterministik: seed per-frame + dt controller ter-jepit 1/60
(`bosses/level1.py:824-826`) → dua kali bake menghasilkan hash PNG
identik (diverifikasi saat pengembangan).

Deviasi yang disengaja (Fase 5; dua yang pertama DITUTUP di Fase 5c
di bawah):

- **Pose skill (q/w/e/r) belum dibake** — selama cast, badan memakai
  pose attack terakhir + FX proyektil Godot (`SkillProjectile.gd`,
  jalur visual skill sejak Fase 5b). Bake pose skill = fase lanjutan
  (timeline per skill beda-beda, `SKILL_VISUAL_DURATION` per namespace).
- **Elite/level tinggi tidak dibake** — bake memakai `boss_class`
  asli dari `boss_data.py` (168 mini + 54 true) pada level 1; bentuk
  elite (mis. `_draw_grimjaw_elite`) menyusul kalau diperlukan.
- **Rim cahaya tim** disederhanakan jadi 2 nilai shader (biru/merah)
  dari 2 tabel RGB pygame (`_HD_RIM_ADD*`, `heroes/__init__.py:1880-1883`).

## Pose skill + rage (Fase 5c — menutup 2 deviasi Fase 5)

Perintah bake sama (`--units-png`); keluarannya bertambah 222 strip
`<type>.skill.png` (±9,2 MB) + 1 strip `drakar.rage.png` dan manifest
**skema 2** (kunci baru `skill_dur`/`skill_anims`/`skills_png` +
geometri strip skill, `rage*` untuk drakar — pembaca skema 1
mengabaikannya, backward-compatible).

| Aspek | Sumber pygame | Implementasi |
|---|---|---|
| drive skill | `active_skill` + countdown `active_skill_timer` (kunci cache `heroes/__init__.py:1750-1766`) | sweep timer durasi cast → 1, 6 frame/pose |
| durasi cast | sisi-AI (`<X>Skills.SKILL_VISUAL_DURATION` + `BossHeroSkills._SKILL_REGISTRY`, `hero_skills/_bundle.py`) — BUKAN durasi render namespace | `skill_dur` di manifest; dipakai sweep bake + `SkillBook._visual_duration` + countdown `BakedSprite` |
| progress | renderer menghitung sendiri `1-timer/dur` (mis. `_skill_progress`, `heroes/_bundle.py:6807-6811`) | `BakedSprite` memaksa frame dari countdown, prioritas DI ATAS attack |
| pose statis | gerbang bake: selisih vs idle < 1.0 | 1 drop (`ursath/w`, visual identik — benar) + 2 fail renderer rusak (`sasori/e`, `vex/q`) → fallback attack |
| unit berlapis | `heroes/*_fx.py` digambar live di atas sprite (`_bundle.py`) | bake fallback kanvas saja (seperti Fase 5); FX hidup tetap tugas Godot |
| varian rage | `rage_active` 300 frame sejak cast q drakar (`hero_skills/_bundle.py`) | strip `drakar.rage.png` (24 frame idle/walk/attack beraura); `BakedSprite` mengganti pose dasar selama countdown rage |
| bentuk elite | "Elite" ternyata NAMA RIG UTAMA, bukan varian level: `_draw_grimjaw_elite`/`_draw_kaizen_elite` dipanggil tanpa syarat oleh wrapper `_draw_*_body` (`heroes/_bundle.py:1404-1411`, `:7431-7437`); `_draw_zharok_elite` (`bosses/level4.py:2125`) bahkan tak dipanggil. Level tidak dibaca di jalur draw; `boss_class` tetap per tipe | SUDAH tampil di strip dasar Fase 5 — deviasi ditutup sebagai salah-alamat (misnomer), tanpa bake tambahan |

**Jam virtual bake.** Klaim "dua kali bake = hash identik" Fase 5 ternyata
bocor untuk 2 unit: mulut emberwick membaca `get_ticks()` absolut saat
attack (`bosses/level41.py:476`, 4 hash berbeda terukur) dan controller
thalgryn memakai dt jam dinding (`bosses/thalgryn_v4.py:1019-1031).
Perbaikannya dari sisi bake (file `bosses/*.py` tidak boleh diubah):
`get_ticks()` dibekukan ke `_PROBE_TICK` selama SELURUH ekspor —
meniru pola resmi probe paritas game itu sendiri
(`heroes/__init__.py:3085-3103`). Hasil: 220/222 strip dasar
byte-identik dengan Fase 5; emberwick + thalgryn berubah SATU KALI
terdokumentasi, lalu stabil (446 file identik antar dua run penuh).

File penting: `scripts/render/BakedUnitDB.gd` (manifest + tekstur lazy,
FIFO cap 64), `scenes/render/BakedSprite.tscn` + `.gd` (SpriteFrames
dibangun runtime via AtlasTexture — tanpa 222 file .tres).

## Bake map statik (Fase 3 — tekstur tunggal, TileSet ditinggalkan)

Rencana awal Fase 3 = `TileMapLayer` + `TileSet` `.tres` per tema. Diukur
dulu sebelum membangun: map statik pygame di-grid 40px (ukuran tile
`draw_terrain`) menghasilkan **533 tile unik dari 576 sel** 1280×720 —
speckle terrain + kurva river/lane membuat hampir semua sel berbeda, jadi
atlas TileSet akan sama besar dengan peta itu sendiri dan 576 sel TileMapLayer
hanya menambah overhead. Arsitektur pygame sendiri adalah SATU Surface
`static_map` di-cache lalu di-blit tiap frame (`_render.py:141/196`); padanan
persisnya di Godot = satu `Texture2D` + `Sprite2D` (1 draw call, di-cache GPU).

`tools/convert_to_godot.py --maps-png` (ikut batch default) membake
`_render.MapRenderer._render_static_map()` — 6 layer dalam urutan persis game
(terrain+details, river, 3 lane, dekor, shop, border wall) — untuk 54 tema ke
`godot/assets/maps/<tema>.png` (opaque 1280×720, palet 256 warna, total ±3,2 MB)
+ manifest `godot/data/map_bakes.json`. `ArenaMap.apply_theme()` memuat tekstur
kalau ada (Sprite2D `BakedMap`, `procedural_fallback = false`); kalau belum ada,
fallback prosedural lama menggambar sendiri — jadi port jalan bahkan sebelum
converter dijalankan, sama seperti pola `UnitSilhouette`.

Determinisme: game aslinya mengacak speckle/jitter dekor (dua `random.seed()`
tanpa argumen di `_bundle.py:4889/:5074` — tiap match beda). Bake membekukan
kedua re-seed itu ke `MAP_BAKE_SEED` (pola "jam virtual" Fase 5) supaya dua run
converter byte-identik; distribusinya identik dengan game. Layer yang tetap
prosedural/live di Godot: cuaca (partikel + kabut, di atas tekstur — urutan yang
sama dengan pygame), `CanvasModulate`/`Light2D` (tint ambient), dan lane path
untuk gameplay (`get_lane_path`/`get_river_path` — AI/minion, bukan visual).
4 `TileMapLayer` kosong yang dulu placeholder dihapus dari `ArenaMap.tscn`.
`BattleSmokeTest` meng-assert bake aktif di headless CI
(`procedural_fallback == false` + `BakedMap` visible).

## Cinematic (Fase 5d — intro level, banner boss, kematian boss)

Tiga layar cinematic pygame (`_render.py`) sudah diport penuh; semuanya
masuk grup `"cinematic"` dan diprioritaskan di `Main._on_key` persis urutan
`Game.handle_key` pygame (`_core.py:2674-2686`): level intro → banner boss
→ perayaan kematian.

| File | Paritas pygame | Perilaku |
|---|---|---|
| `scenes/ui/LevelIntro.gd` | `LevelIntroScreen` (`:2679`), dibuat di `Game.reset` (`_core.py:1608`) | Split-screen: kiri angka level Cinzel 200 + nama + deskripsi + bar kesulitan + reward/starting gold/passive income (rumus `compute_starting_gold` yang sama dengan `Game.reset`), kanan FINAL BOSS + siluet prosedural (aura pulse, 12 sinar, mahkota, mata menyala). Tint 34 tema + vignette. **Pause gameplay** sampai SPACE/ENTER/klik; SFX `wave_start` |
| `scenes/ui/BossIntroBanner.gd` | `BossIntroCinematic` (`:2152`) | Strip 600×92 slide ease-out dari kiri, 100 frame, tag TRUE/MINI BOSS + nama warna `entrance_color` + HP bar preview + sudut emas. **Tidak pause**; dipicu `Main._boss_tick` saat mini/true boss turun; skip SPACE/ESC/klik; SFX `nexus_hit` |
| `scenes/fx/BossDeathFX.gd` | `BossDeathAnimation` (`:1622`) | Dipanggil `Boss.die()`: white flash + gelombang cincin + dissolve + pecahan + partikel roh. Fase kematian (60f mini / 90f true) **pause gameplay** (paritas `_core.py:1995`), lalu perayaan true boss 120f ("BOSS DEFEATED!" + "+ X GOLD" dari field `gold_reward` bosses.json + "HERO UNLOCKED!" + bintang berputar) tanpa pause + fanfare `victory`. Skip hanya fase perayaan |

Font Cinzel + Barlow kini ikut repo di `assets/fonts/` (salinan
`assets/fonts/` akar repo) supaya tipografi cinematic paritas dengan
`title_font()`/`get_font()` pygame — tanpa perlu menjalankan converter.
Uji regresinya: `tests/CinematicTest.tscn` (dijalankan godot-check CI);
`BattleSmokeTest` kini men-skip intro dulu sebelum mengamati combat.

Deviasi terdokumentasi: ikon vektor `ui_theme.draw_icon` (segitiga/bintang)
digambar langsung dengan draw API; bayangan teks multi-lapis pygame menjadi
shadow Label bawaan Godot.

## Efek percikan, ledakan, dan panah lane (Fase 26)

Tiga blok `effects.py` di `_render.py` yang **belum pernah punya padanan** kini
diport, semuanya sebagai data + satu view tipis per frame (pola
`FloatingTextQueue`/`WorldPopups` yang sudah terbukti di headless):

```
scripts/render/HitSpark.gd     — 1 partikel (HitParticle :418-493): gravitasi 0.15 setelah posisi, gesekan 0.95,
                                 alpha int(255*sisa), ukuran max(1, int(size*sisa)), 2 lingkaran konsentris
scripts/render/DeathBurst.gd   — DeathExplosion (:494-571): 8/15/25 partikel per preset + kilat pusat 8 frame
scripts/render/SparkField.gd   — lapangan global (EffectManager :601-800): cap 500 partikel / 80 ledakan,
                                 trim yang TERTUA, add_hit_particles / add_death_explosion
scenes/fx/SparkLayer.gd        — view: draw_circle per partikel, z_index 800 (di atas semua unit)
scenes/fx/PathPreview.gd       — PathPreview (:1275-1370): panah lane 120 frame, z_index 790
```

Pemiliknya `GameManager.spark_fx` (dibuat di `_bootstrap`, di-tick
`_process` dengan akumulator 60 Hz, dibersihkan di `return_to_menu`). View
dibuat oleh `Main._fx_ready()` — **node langsung**, bukan `call_group` (lihat
temuan 7 di `docs/PARITY_AUDIT.md`: call_group ke metode yang tidak ada diam
saja). Situs pemanggil mengikuti pygame persis: percikan di
`CombatSystem._hit_spark_count` (minion 4 `_entity.py:5842` · boss 6
`base_boss.py:6057` · nexus 10 `_entity.py:1816` · **hero & menara 0**),
ledakan di `Minion.die` (`medium`), `Boss.die` (`large`), dan dua cabang
`not silent` di `TacticalCommands` (`small` biru). Panah lane dipicu
`Main._show_path_preview()` dari `_on_wave_started` dengan urutan
`top, mid, bot` (`_core.py:1757`).

```bash
# Oracle: menjalankan HitParticle / DeathExplosion / EffectManager / PathPreview
# pygame ASLI + PathGenerator sungguhan, merekam jejak draw/scale/blit/set_alpha,
# lalu mengunci konstanta & ekspresi .gd:
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_render_parity.py

# Replay headless (CI godot-check langkah 4v):
XDG_DATA_HOME=$(mktemp -d) godot --headless --path godot res://tests/RenderFxParityTest.tscn --quit-after 300
```

Uji regresinya: `tests/RenderFxParityTest.tscn` — fixture
`tests/fixtures/render_fx.json` (419 KB; 73 frame percikan, 32 frame/792 op
ledakan, 4 skenario `add_hit_particles` + batas 500/80, 130 frame + 490 polygon
panah lane, wiring `spark_fx`).

## Lokalisasi teks UI (Fase 30 — port `localization.py`; aktif in-match sejak 2026-09-13)

```
godot/scripts/utils/Localization.gd   — class_name MysticLocalization (semua static): TEXT 106 kunci × 2 bahasa, LANGUAGES, LANGUAGE_LABELS, set_language/get_language/get_language_label/tr_text/is_english, _py_format/_py_str (semantik str.format + str() Python)
godot/tests/LocalizationParityTest.gd — replay fixture di engine + plumbing (GameManager/SaveManager/ItemDB/MainMenu)
godot/tests/fixtures/localization.json — oracle: dihasilkan localization.py ASLI
tools/test_godot_localization_parity.py — oracle TANPA pygame/Godot: tabel GDScript == localization.py (isi + URUTAN kunci), audit placeholder, audit closed-world pemakai `tr_text()`/`_loc()`, fixture segar
```

Pakai `MysticLocalization.tr_text("kunci", {"nama": nilai})` untuk teks UI
baru — **jangan** menulis kalimat dua kali. Namanya `tr_text`, bukan `tr`,
karena `Object.tr()` adalah method native engine (TranslationServer); oracle
menggagalkan `static func tr(` di port.

Bahasa aktif disinkronkan saat boot oleh `AppShell._apply_interface_language()`
(autoload paling akhir, jadi save sudah terbaca), dicerminkan
`GameManager.language`, dan diubah pemain lewat baris BAHASA di PENGATURAN
(`GameManager.set_language()` → validasi `("id","en")` → simpan →
`signal language_changed`). `ItemDB.item_mechanics_localized(item_id)`
mengembalikan mekanik item dalam bahasa aktif (padanan
`en = get_language() == "en"` di `hero_items.py:1632`).

**Berlaku di dalam game (2026-09-13).** Empat panel in-match membaca tabel ini
bukan teks hard-code — `HUD` (10 baris hint keycap), `ShopPanel` (judul TOKO/
SHOP, tombol tutup, 4 tab, konteks, isi tab MENARA/ITEM/HERO/NEXUS termasuk
alasan kartu item), `SkillBar` (label + tooltip), dan `GameOverOverlay`
(tombol ULANGI/MENU UTAMA/LANJUT + baris hint + catatan hasil). Keempatnya
menyambung `GameManager.language_changed`, jadi berpindah bahasa di PENGATURAN
(termasuk lewat menu pause) langsung terlihat tanpa menutup layar: ShopPanel
menyegarkan chrome + membangun ulang isinya, HUD/SkillBar menulis ulang
labelnya, GameOverOverlay membangun ulang baris hint + tombol (tanpa mengulang
animasi intro).

Yang TIDAK diterjemahkan karena pygame juga tidak menerjemahkannya:
`ITEM FORGE  (%d/6)`, `TIER I/II`, `SHIELD n%` di atas kastil, `AUTO-CAST ON`,
`MAX LEVEL`, `Lv.%d`, `VICTORY!`/`DEFEAT`, lima nama statistik layar hasil, dan
badge `LEVEL n`/`WAVE n`.

Catatan jujur: 25 kunci masih diport sebagai DATA (notifikasi forge, antrean
item + `queued_item_count`, `shop_no_hero_yet`, label halaman toko, popup
detail item) dan menunggu permukaan UI-nya — oracle mencetak daftarnya setiap
run, dan alasan per kelompok ada di
[`../docs/LOCALIZATION_GODOTPP.md`](../docs/LOCALIZATION_GODOTPP.md).

```bash
python3 tools/test_godot_localization_parity.py                 # oracle tanpa engine
python3 tools/test_godot_localization_parity.py --write-fixture # regenerasi (hanya bila localization.py berubah)
XDG_DATA_HOME=$(mktemp -d) godot --headless --path godot res://tests/LocalizationParityTest.tscn --quit-after 120
```

## Design system UI (Fase 31 — port `ui_theme.py`)

```
godot/scripts/utils/UiTheme.gd              — 32 warna palet, cache tekstur (glow radial langkah 2px + bayangan 1/8 ukuran), fungsi murni geometri/warna, 29 ikon vektor (ICON_NAMES), jalur immediate-mode draw_* (btns: Dictionary), font (title_font/body_bold/body_semibold/body_medium/body_regular + font_for_weight)
godot/scenes/ui/widgets/PygameChip.gd       — chip status auto-size (ikon + label + nilai opsional, align kiri/kanan); semua properti ber-setter, jadi `chip.label_text = "GOLD"` langsung menghitung ulang ukuran
godot/scenes/ui/widgets/SectionHeader.gd    — header seksi: ikon + judul letter-spaced + hairline aksen/redup (blok 34px)
godot/scenes/ui/widgets/PygameSlider.gd     — HSlider dengan visual pygame (visual native dikosongkan; ratio()/track_rect()). Sinyal `value_changed` baru terbit setelah widget ada DI DALAM TREE
godot/scenes/ui/widgets/OptionCycler.gd     — label + kotak nilai auto-width + chevron < > (signal value_changed, hit_rects(), press())
godot/scenes/ui/widgets/ScrollIndicator.gd  — thumb scroll 6px (follow(ScrollContainer) / set_scroll(pos, max) / thumb_rect())
godot/scenes/ui/widgets/GradientText.gd     — teks gradasi vertikal N pita clip (dipakai ScreenTitle)
godot/scenes/ui/widgets/PygameButton.gd     — 3 mode (MENU/PILL/TAB) mendelegasikan ke UiTheme.*_visual + back_button()
godot/tests/UiThemeParityTest.gd            — replay fixture di engine: fungsi murni + widget + smoke immediate-mode (dua cabang cheap_alpha); 1463 cek, hijau di CI
godot/tests/fixtures/ui_theme.json          — oracle: 18 seksi direkam dari ui_theme.py ASLI (SDL dummy + font palsu 7px/karakter)
tools/test_godot_ui_theme_parity.py         — oracle: 4 cek statik (palet/coverage/ikon/literal/wiring) + 17 seksi runtime
```

Port-nya **tiga lapis** supaya angka geometri/warna hanya punya satu sumber:

1. fungsi murni (`chip_rect`, `cycler_geom`, `slider_geom`, `button_hit_rect`,
   `button_label_cx`, `screen_title_geom`, `scroll_thumb_rect`, `tab_width_for`,
   `toggle_colors`, `pill_colors`, `dim`, `add_rgb`, `vgrad_row_color`, ...) —
   tidak menggambar apa pun, jadi bisa dibandingkan dengan angka oracle;
2. jalur immediate-mode `UiTheme.draw_*(cv, ...)` — port 1:1 badan fungsi
   pygame, dipanggil dari `_draw()`; komponen interaktif mengisi
   `btns: Dictionary` (id → Rect2) seperti `btns` pygame;
3. widget Control di `scenes/ui/widgets/` — memanggil lapis 2.

```gdscript
# Immediate-mode di dalam _draw() (paritas 1:1 dengan pemanggil pygame):
var btns := {}
UiTheme.draw_section_header(self, Vector2(40, 60), "AUDIO", "speaker",
    UiTheme.CYAN, UiTheme.body_semibold(), 22, 240.0)      # -> y berikutnya 94
UiTheme.draw_pill(self, btns, "play", "PLAY", Rect2(120, 90, 170, 40),
    "gold", UiTheme.body_semibold(), 18, hover, true, "play")
# btns["play"] hanya terisi bila enabled=true — tombol mati tidak bisa diklik.

# Atau sebagai widget:
var chip := PygameChip.new("HERO GOLD", "1.234", UiTheme.CYAN, "coin")
var header := SectionHeader.new("AUDIO", "speaker", UiTheme.CYAN, 240.0)
var cyc := OptionCycler.new("BAHASA")
cyc.set_options(["id", "en"], ["Bahasa Indonesia", "English"])
cyc.value_changed.connect(func(i: int, v: Variant) -> void: print(i, v))
var back := PygameButton.back_button()   # 200x42, kind neutral, ikon "back"
```

`UiTheme.cheap_alpha()` selalu true di Godot (komposisi alpha terjadi di GPU),
tetapi **kedua cabang** pygame tetap diport; pakai
`UiTheme.cheap_alpha_override = 0` untuk memaksa bentuk hemat (mis. uji visual
mode low-end), `1` untuk penuh, `-1` (default) untuk auto.

Dua warna pygame yang di `ui_theme.py` hanya muncul sebagai literal di
dalam badan fungsi diberi nama di sini supaya tidak ditulis ulang di tiap
pemakai: `TEXT_SHADOW` `(5,6,12)` (bayangan `draw_text`) dan `OUTLINE_DARK`
`(8,9,18)` (outline `gradient_text`/`outline_text`, dipakai `GradientText`
dan `ScreenTitle`). Oracle menerimanya sebagai konstanta Godot ekstra dan
`visual_parity_audit.py --section hardcode` memastikannya tidak bocor lagi
menjadi literal di berkas lain.

Tiga jebakan engine yang ketahuan saat run CI pertama (semuanya sudah
diperbaiki + dikunci `UiThemeParityTest`):

* `Range::emit_value_changed()` melewati node yang tidak ada di dalam tree,
  jadi `PygameSlider` harus `add_child()` dulu sebelum mengandalkan sinyal
  `value_changed` (nilainya tetap berubah di luar tree).
* `floor()`/`min()`/`max()` GDScript mengembalikan **Variant** → `var x :=
  floor(...)` gagal parse. Pakai `floorf`/`minf`/`maxf`/`mini`/`maxi`.
* `radial_texture()` sengaja menyatukan alpha sebucket
  (`max(4, min(120, a // 8 * 8))`: 74 dan 72 → 72) persis `_GLOW_CACHE`
  pygame, jadi instance-nya SAMA untuk alpha sebucket.

Catatan jujur: 6 widget baru di atas **belum dipasang** di layar mana pun —
`MainMenu.gd` masih merakit `_shop_chip`/`_mini_chip`/`_settings_header`/
`_volume_slider` sendiri, dan rewiring-nya ditahan karena
`MetaShopTxnParityTest`/`LocalizationParityTest` mengunci struktur node layar
itu. Rincian + semua deviasi (strip aksen opaque, pita gradasi teks, `pyrect`,
nama API): [`../docs/UI_THEME_GODOTPP.md`](../docs/UI_THEME_GODOTPP.md).

```bash
# Oracle: cek statik (tanpa engine) + menjalankan ui_theme.py ASLI untuk fixture
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_godot_ui_theme_parity.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_godot_ui_theme_parity.py --write-fixture  # hanya bila ui_theme.py berubah

# Replay headless (CI godot-check langkah 4y):
XDG_DATA_HOME=$(mktemp -d) godot --headless --path godot res://tests/UiThemeParityTest.tscn --quit-after 200

# Palet + literal warna tidak boleh ditulis ulang di luar UiTheme.gd
SDL_VIDEODRIVER=dummy python3 tools/visual_parity_audit.py --section palette,hardcode
```

## Kaizen Skeleton2D (showcase / opt-in)

```
godot/scenes/hero/kaizen/KaizenSkeleton.tscn  — 25 Bone2D (Root→Hips→Torso→Chest→Head/Ponytail 3×/Scarf 3×/Katana + Arms/Legs)
godot/scenes/hero/kaizen/KaizenSkeleton.gd   — drive(phase, action, attack_progress, facing) — busur 1 sumber kebenaran (ATTACK_ARC_*), inertia scarf/ponytail, hamon shader time, wind ribbon Line2D
godot/scenes/demo/KaizenDemo.tscn/.gd       — showcase isolasi: F5 Run Current Scene untuk lihat 60fps bone interpolasi vs pygame 6-frame patah
```
Rig Kaizen ada di `RendererRegistry.HERO`, tetapi arena default memakai bake asli.
Aktifkan `mystic/rendering/experimental_hero_rigs` untuk mencoba rig di arena.
Tip katana: `get_katana_tip_global()`.

## Android Build (Fase 6 — siap Play Store)

**Jalur utama = CI**: `git tag vX.Y.Z && git push origin vX.Y.Z` →
`.github/workflows/build-android-godot.yml` mengekspor **AAB** ditandatangani
(keystore = secret lama `KEYSTORE_BASE64`, package tetap
`io.github.dharmawantoxi.mysticarena` sehingga Play mengenali app yang sama
dan save player tidak hilang) → artefak + GitHub Release. Manual: tab
Actions → "Build Android (Godot)" (`debug` = APK sideload, `release` = AAB
verifikasi). Runbook lengkap: `docs/PLAYSTORE_RELEASE.md`.

Keputusan teknis Fase 6:

- **Godot 4.7.2 untuk export** (bukan 4.3): aturan Play 2026-08-31 mewajibkan
  `targetSdkVersion` 36; konstanta `DEFAULT_TARGET_SDK_VERSION` template
  Android baru 36 mulai Godot 4.7 (4.3 = 34, ditolak Play). CI
  `godot-check.yml` tetap 4.3 = versi minimum feature project.
- **Renderer Mobile di Android**: `project.godot` menambah
  `renderer/rendering_method.mobile="mobile"` (override platform).
  Forward+ tidak didukung Android, dan Mobile mendukung semua fitur 2D yang
  dipakai project (lighting, glow, shader canvas_item, 2D HDR); tanpa Vulkan
  engine otomatis jatuh ke OpenGL ES 3.0 (`fallback_to_opengl3` default) →
  minSdk 24, jangkauan perangkat sama dengan versi pygame. Desktop F5 tetap
  Forward+.
- **Ikon launcher** di `assets/android/` (192 main + 432 adaptive fg/bg dari
  `assets/icon.png` master 512); `assets/icon.png` project kini 512.
- **Suara**: `assets/sounds/` di-gitignore; CI menyalin dari `assets/sounds/`
  sebelum export. Build lokal: jalankan converter dulu (Quick Start). Converter
  juga meluruskan ekstensi 8 berkas yang namanya `.wav` tapi isinya Ogg/MP3
  (tanpa itu importer WAV Godot menolaknya dan SFX-nya senyap di HP).
- Keystore diisi via env `GODOT_ANDROID_KEYSTORE_RELEASE_PATH/USER/PASSWORD`
  (fitur Godot ≥ 4.7) — secret tidak pernah tersimpan di repo.

Lokal (editor): `Project → Export → Android → Export AAB` →
`godot/build/MysticArena.aab` (1-2 menit, bukan 8-12 menit buildozer).

### `Unable to open Android 'build-tools' directory`

Ini masalah SDK lokal, terpisah dari parse error GDScript:

1. Di Android Studio → **SDK Manager → SDK Tools**, install **Android SDK Build-Tools**
   sesuai kebutuhan versi Godot yang dipakai.
2. Di Godot → **Editor Settings → Export → Android → Android SDK Path**, pilih
   direktori **root SDK** yang berisi `build-tools/` dan `platform-tools/`, bukan
   direktori `build-tools/` atau subdirektori versinya. Pastikan foldernya bisa dibaca.
3. Buka ulang project setelah SDK/path diperbaiki. Untuk F5 desktop saja, SDK Android
   tidak diperlukan; jangan mengubah script atau menghapus preset export untuk menutupi pesan ini.

Path SDK adalah pengaturan editor per mesin, bukan path yang perlu disimpan di repository.

Lihat `docs/GODOT_MIGRATION.md` untuk roadmap lengkap.
