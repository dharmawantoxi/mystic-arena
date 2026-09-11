# Peta cakupan `_system.py` → Godot

**Apa ini:** audit blok-per-blok `_system.py` (1.125 baris — gabungan 5 modul
lama: `performance.py`, `fps_counter.py`, `fps_limiter.py`, `sound_manager.py`,
`save_manager.py`, lihat docstring `:1-9`) terhadap port Godot di `godot/`.
Dipakai untuk menjawab "blok `_system.py` mana yang sudah pindah, mana yang
tidak usah, mana yang belum" tanpa menebak dari nama berkas.

**Cara baca:** setiap baris = blok pygame dengan rentang baris di `_system.py`,
padanannya di Godot, dan statusnya.

| Status | Arti |
|---|---|
| ✅ PORTED | Perilaku diport dan **dikunci fixture/oracle** (tes paritas menyebutnya) |
| 🟡 PARSIAL | Ada padanannya, tapi sebagian perilaku belum ada / belum diuji |
| ❌ BELUM | Tidak ada padanan di Godot |
| ⚪ N/A | Kode pygame-nya sendiri no-op / mati / khusus engine pygame |

Oracle + fixture: `tools/test_system_perf_parity.py` →
`godot/tests/fixtures/system_perf.json`; replay headless:
`godot/tests/SystemPerfParityTest.tscn`. Peta cakupan `_core.py`:
[CORE_PY_COVERAGE.md](CORE_PY_COVERAGE.md); `_entity.py`:
[ENTITY_PY_COVERAGE.md](ENTITY_PY_COVERAGE.md); `_render.py`:
[RENDER_PY_COVERAGE.md](RENDER_PY_COVERAGE.md); status paritas umum:
[GODOT_PARITY.md](GODOT_PARITY.md).

---

## 1. `performance.py` — `_system.py:29-185`

| Blok | Padanan Godot | Status |
|---|---|---|
| `FrustumCuller` (`:40-50`) — `MARGIN = 80`, `is_visible(x, y, radius=30)` | `scripts/systems/FrustumCuller.gd` (`is_visible`, `is_visible_world`) | ✅ (FASE 25; fixture `culler`: 17 kasus batas, `x = -margin - radius` inklusif s/d eksklusif 1 px; `is_visible_world` untuk pemanggil yang punya camera) |
| Konsumen culler: skip blit entitas (`_core.py:2875-2910`) + beku `death_anim` di luar layar (`_entity.py:5871-5878`) | `scenes/fx/WorldPopups.gd._draw` (`FrustumCuller.is_visible_world` + `POPUP_RADIUS 24`) | 🟡 sisi **draw** diport dan dikunci; **pembekuan animasi** sengaja TIDAK diport — Godot mengurangi `death_anim` di `_process`, lihat deviasi #1 di bawah |
| `SpatialGrid` (`:52-142`) — `cell_size=60`, `insert`/`clear`/`query_range(x, y, radius, team=None)` | `scripts/systems/SpatialGrid.gd` (`insert`, `clear`, `update_from`, `query_range`, `query_enemies`) | ✅ (fixture `grid`: 9 skenario × urutan bucket persis — cy loop luar, cx dalam; isi bucket = urutan insert; bbox prefilter lalu `dx²+dy² <= r²`; `team=None` TIDAK memfilter apa pun) |
| `_grid = SpatialGrid(cell_size=60)` (`:144`) | `CombatSystem._spatial_grid` (singleton autoload, `GRID_CELL_SIZE := 60.0`) | ✅ satu grid global, sama seperti pygame |
| `update_spatial_grid(minions, heroes)` (`:147-168`) — rebuild tiap frame GENAP (`_core.py:2007-2013`: `animation_time % 2 == 0`), `spatial_heroes = get_all_heroes() + [active_boss]`, **menara/base sengaja tidak diindeks** | `CombatSystem.update_spatial_grid` + `update_spatial_grid_from_tree()` + `_grid_tick % GRID_REBUILD_EVERY == 0` di `Main._process` (`GRID_REBUILD_EVERY := 2`) | ✅ urutan grup minion→hero→boss ditiru; unit mati dilompati saat insert (`.alive` dibaca ulang saat kueri di pygame → `_is_dead` dibaca saat `_query`) |
| `query_enemies_in_range(x, y, radius, team)` (`:170-185`) | `CombatSystem.query_enemies_in_range(team, center, radius)` | ✅ + dua penjaga khas Godot: `spatial_grid_fresh()` (grid basi → scan grup, supaya menu/pause/harness tidak pernah melihat hasil kosong) dan `_targetable` (Shadow Realm); menara + nexus di-scan langsung lalu **appended terakhir** |

**Konsumen.** Satu-satunya jalur baca grid di pygame adalah `Minion._get_enemies`
(`_entity.py:5635-5680`) dan `Tower.update` (`_entity.py:808-860`). Di Godot yang
dialihkan hanyalah `Minion._find_target_smart` (radius aggro `attack_range + 30`).
Jalur sihir berantai, voly pemanah, splash meriam, AoE, aura dan item sengaja
**tidak** dialihkan ke grid: di pygame mereka membaca list biasa
(`game.minions + game.heroes`), dan urutan kandidat mereka sudah dikunci tes
lain — menukar urutan = merusak perilaku terkunci demi kecepatan yang belum
diukur. Lihat juga catatan menara di bagian "Temuan".

## 2. `fps_counter.py` — `_system.py:189-387`

| Blok | Padanan Godot | Status |
|---|---|---|
| `FPSCounter.__init__`/`toggle`/`set_enabled` (`:202-236`) | `scenes/ui/FpsCounter.gd` (`enabled`, `toggle()`, `set_enabled()`, cetak `[FPS COUNTER] ON/OFF`) | ✅ |
| `update(clock)` (`:237-256`) — `deque(maxlen=120)`, `frame_count >= 10` → reset 0, statistik dari 30 sampel terakhir | `FpsCounter.update(current_fps)` (`HISTORY_SIZE 120`, `DISPLAY_EVERY 10`, `DISPLAY_WINDOW 30`) | ✅ (fixture `fps.trace`: 15 pembaruan panel dari 150 sampel; angka **hanya** berubah pada frame kelipatan 10) |
| `draw(surface)` (`:258-386`) — panel 200×95 @(10,45) radius 8 fill hitam α200 tepi `(60,70,90)`, angka 40px, label `FPS`, status rata-kanan, petunjuk `[F8] toggle`, `AVG/MIN/MAX`, grafik 180×22 @(10,65) + dua garis panduan 60/30 + bar per sampel | `FpsCounter._draw()` mengeksekusi `build_ops(state, measurer)`; geometri/warna sebagai konstanta (`PANEL_POS`, `FPS_AT`, `NUM_SIZE`, `GUIDE_60`, `BAR_*`, …) | ✅ jejak `pygame.draw.rect/line` + `font.render` SUNGGUHAN direplay 1:1 oleh `SystemPerfParityTest` (32 op: panel, 7 teks, grafik, 2 garis, 21 bar) — `ops` fixture adalah sumber kebenarannya |
| Saklar F8 (`main_desktop_legacy.py:98-100`, SEBELUM dispatch state, tombol tidak ditelan) | `Main._on_key` → `toggle_fps_counter()` (`_build_fps_counter()` memasang node di `DebugLayer` CanvasLayer `PROCESS_MODE_ALWAYS`) | ✅ (diuji sebagai toggle, bukan sebagai rute menu — `HUD.toggle_debug_overlay` tetap milik tombol FPS TouchHUD/L3) |

## 3. `fps_limiter.py` — `_system.py:388-449`

| Blok | Padanan Godot | Status |
|---|---|---|
| `AdaptiveQuality` (`:400-448`) — `pygame.time.Clock`, `tick(target_fps)`, turun preset saat FPS jeblok | — (cap FPS = `Engine.max_fps` lewat `GameManager.apply_fps_limit`, paritas `main.py:637`/`main_desktop_legacy.py:469-471`; preset kualitas tidak otomatis) | ⚪ **tidak diport**: `build_dead_claims()` di tool oracle menegaskan kelas ini **nol call site** di luar `_system.py` (fixture `dead.adaptive_quality.sites == []`) — port-nya akan jadi perilaku baru, bukan paritas |
| Anggaran FX per preset kualitas (yang dilakukan `AdaptiveQuality` di jalur Android, via `mobile/perf.py`) | `GameManager` membaca `settings.quality` hanya untuk `world_popups.max_damage_numbers` (8/16/32) | 🟡 `mobile/perf.py:auto_detect_quality` (`:861`, dipasang `install_all` `:997-1003`) tidak punya padanan Godot — dan itu BUKAN kelas `_system.py`, jadi tidak ikut Fase ini |

## 4. `sound_manager.py` — `_system.py:450-731`

| Blok | Padanan Godot | Status |
|---|---|---|
| `_sound_path` (`:21-38`) + `_SOUND_DIR` | `godot/assets/sounds/` (sumber daya proyek, `AudioManager._path`) | ✅ |
| `SoundManager` BGM/SFX/ambient, volume `MASTER 0.7 × slider`, jeda & anggaran SFX tempur, `ambient_channel` | `scripts/autoload/AudioManager.gd` (`play`, `play_combat`, `play_ambient`, `stop_ambient`) | ✅ **sudah selesai sebelum FASE 25** (Fase 4e, lihat `GODOT_MIGRATION.md`) — audit ulang `tools/test_system_perf_parity.py` hanya menegaskan tidak ada metode `SoundManager` lain yang belum punya padanan berperilaku |
| `play_positional` (`:615`) | — | ⚪ dead code: `build_dead_claims()` mencatat `sound_manager_play_positional.sites == []` (nol call site di repo pygame) |

## 5. `save_manager.py` — `_system.py:732-1125`

| Blok | Padanan Godot | Status |
|---|---|---|
| `SaveManager` path/`_default_data`/save/load/migrasi, `format_time`, statistik `level_stats`, 3 slot | `scripts/autoload/SaveManager.gd` (slot API + migrasi legacy) | ✅ (Fase FASE 21; fixture `save_slots`: 8 kasus migrasi, 9 skenario save/load, 3 hapus, 6 `get_slot_info`, 17+15 baterai format, 15 kartu) |
| Progresi meta/voucher/achievements yang disimpan | `SaveManager` + `GameManager.grant_meta_reward/unlock_achievement` | ✅ (`meta_shop_txn`, `match_scoring`) |
| Upload cloud Google Play Games (`_system.py` `:965-1035`) | belum | ❌ keluar cakupan port 2D desktop/mobile Godot; tercatat di `GODOT_PARITY.md` |

---

## Temuan audit (tercatat, tidak "diperbaiki diam-diam")

1. **Panel FPS pygame tidak pernah tampil.** `FPSCounter.draw()` memanggil
   `get_font(size)`, tapi nama itu tidak pernah masuk ke namespace `_system`
   (`from _core import *` dieksekusi saat `_core` masih parsial karena import
   melingkar) → F8 di `main_desktop_legacy.py` = `NameError`. Tool oracle
   menambal `_system.get_font = _render.get_font` supaya jalur render-nya tetap
   bisa dijadikan sumber kebenaran, dan menyimpan faktanya di fixture
   (`fps.py_draw_needs_shim: true`, `fps.py_bug`). Port Godot **memperbaiki**
   jalur ini; tidak ada perilaku pygame yang direplikasi untuk meniru crash-nya.
2. **`main_desktop_legacy.py` men-samples FPS dua kali per frame** (`update/draw`
   di `:455-456` DAN `:461-462` — sisa penggabungan file). Itu kecelakaan, bukan
   kontrak: di Godot `FpsCounter._process` mengirim satu sampel per frame. Karena
   itu `trace` fixture (150 sampel, 1 sampel/frame) yang jadi acuan, bukan
   kecepatan tampilan di jendela legacy.
3. **Tie-break target menara berbeda dan itu laten di kedua sisi.** pygame
   `Tower._find_target` (`_entity.py:808-860`) memakai `dist <= best_dist`
   (= musuh TERAKHIR pada jarak sama yang menang) sementara Godot
   `CombatSystem.nearest_enemy` memakai `<` (= yang pertama). Jalur menara Godot
   saat ini TIDAK membaca grid (dan tie-break-nya tidak dikunci fixture), jadi
   ini **bukan** regresi FASE 25 — tapi ini selisih perilaku nyata yang harus
   diputuskan terpisah. Tercatat di `GODOT_PARITY.md` → "Belum setara".
4. **Overlay debug `main.py` (entry HIDUP) bukan kelas ini.** Di sana FPS/debug
   adalah `mobile/debug.py` dengan 4 mode (off/mini/full/grafik) + tombol
   TouchHUD; yang diport di `FpsCounter.gd` adalah `_system.FPSCounter`
   (jalur desktop legacy, satu-satunya konsumen kelasnya). Tombol FPS 4-mode
   masih terbuka dan tidak ikut Fase ini.

## Cara menjalankan

```bash
# 1) Oracle pygame (menulis/mengesahkan fixture + mengunci konstanta sumber .gd):
python3 tools/test_system_perf_parity.py                  # gate drift + kunci Godot
python3 tools/test_system_perf_parity.py --write-fixture   # regenerasi fixture

# 2) Replay Godot (butuh binary Godot; CI `godot-check.yml` langkah 4u):
export XDG_DATA_HOME="$(mktemp -d)"
godot --headless --path godot res://tests/SystemPerfParityTest.tscn --quit-after 300
```

Sisi Godot `check_godot_source()` di tool yang sama membaca sumber `.gd` dan
mem-pin konstanta (`CELL_SIZE 60`, `MARGIN 80`, `HISTORY_SIZE 120`,
`GRID_REBUILD_EVERY 2`, geometri & 15 warna overlay, `for group in
["towers", "nexus"]`, fallback `enemies_in_radius`) — supaya mesin tanpa Godot
tetap punya penjaga, dan pola regex yang hilang membuat tool **gagal**, bukan
diam-diam meloloskan perubahan.
