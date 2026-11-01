# Migrasi `_system.py` → Godot (`godot_rebuild/`)

Status: **native GDScript, tanpa Python saat runtime**. Melanjutkan migrasi
`main.py` (#377), `_core.py` (#378), `_entity.py` (#379), `_render.py` (#380).
`_system.py` adalah gabungan 5 file: `performance.py`, `fps_counter.py`,
`fps_limiter.py`, `sound_manager.py`, `save_manager.py`.

## Cakupan

| Sumber Python | Native Godot | Catatan |
|---|---|---|
| `FrustumCuller` | `scripts/system/FrustumCuller.gd` | Margin 80, layar 1280×720; dipakai `ArenaView._draw_unit` untuk skip unit di luar layar. |
| `SpatialGrid`, `update_spatial_grid`, `query_enemies_in_range` | `scripts/system/SpatialGrid.gd` + `MatchModel` | Cell 60, satu bucket per entitas, urutan kueri cx→cy→insert. `MatchModel._update_spatial_grid()` tiap tick; `nearest_enemy_in_range()` dipakai target menara (tower/base tetap dicek langsung, tidak diindeks). |
| `FPSCounter` | `scripts/system/FpsCounter.gd` | History 120, jendela tampil 30, refresh tiap 10 frame; status SMOOTH/OK/SLOW/LAG; panel + mini graph native. `Main` meng-update tiap frame; `DebugView` mode 2 menampilkan AVG/MIN/MAX. |
| `AdaptiveQuality` | `scripts/system/AdaptiveQuality.gd` | History 30, ambang 50/35 → high/medium/low. `Main` memanggil `tick()`; bila `GameSettings.auto_quality` aktif, kualitas render diterapkan ke `CoreGame.apply_render_quality()` tiap 30 frame. |
| `SoundManager` | `scripts/audio/AudioDirector.gd` (diperluas) | 32 channel, throttle per suara, kategori sfx/voice/ambient, BGM fade/pause/resume/stop, ambient loop fade, `play_positional()` (max 800, floor volume 0.15), `set_master_volume()`. Manifest 17 suara dari `load_all()`. |
| `SaveManager` | `scripts/core/SaveRepository.gd` (diperluas) | 3 slot, backfill default, `all_slot_info()`, `migrate_legacy_save()` (progress.json → slot 1 + backup .bak), `format_playtime/format_time/format_last_played`, level stats (sudah ada sebelumnya). |
| `mobile.perf.Quality` (render) | `RenderQuality.gd` + `AdaptiveQuality` | Preset low/medium/high tetap manual via `render_quality`; `auto_quality` opsional mengikuti AdaptiveQuality. |

## Arsitektur runtime

```
Main._process(delta)
  ├── FpsCounter.update(Engine.get_frames_per_second())
  ├── AdaptiveQuality.tick(fps) ──(auto_quality)──► CoreGame.apply_render_quality()
  └── DebugView.refresh(fps, …)  # mode 2: AVG/MIN/MAX + status

MatchModel.step()
  ├── _update_spatial_grid()     # minion/hero/boss alive, cell 60
  ├── _update_unit / _update_tower
  │      └── nearest_enemy_in_range()  # grid + tower/base langsung
  └── …

AudioDirector (Node)
  ├── play_sfx / play / play_positional  # throttle + kategori volume
  ├── play_bgm / stop_bgm / pause_bgm / resume_bgm / update_bgm_volume
  └── play_ambient / stop_ambient / set_master_volume / set_background_paused

SaveRepository (RefCounted)
  ├── load_slot/save_slot/delete_slot    # user://godot_core, atomic tmp+rename
  ├── migrate_legacy_save()              # progress.json → slot_1.json + .bak
  └── slot_info/all_slot_info + format helpers
```

- Python `saves/` tidak disentuh; native menulis hanya di `user://godot_core/`.
  Migrasi legacy bersifat eksplisit di dalam direktori native dan idempotent.
- Cloud auto-upload tetap lewat `CloudSavePort`/`SaveRepository` yang sudah ada;
  tidak ada klaim Play Games aktif tanpa plugin.
- `AdaptiveQuality` tidak mengubah `Engine.max_fps`; ia hanya memilih preset
  efek/partikel. Batas FPS tetap `GameSettings.effective_fps()`.

## Kontrak data & tooling

```bash
python3 tools/prepare_godot_system.py         # tulis data/system_data.json
python3 tools/prepare_godot_system.py --check # gate CI (AST, tanpa pygame)
python3 tools/test_godot_system_prepare.py    # 5 tes regresi
```

`data/system_data.json` memuat: konstanta performa (margin/cell/history/ambang),
volume default + throttle + manifest 17 suara `SoundManager.load_all()`, jumlah
slot, kunci empty save, dan default level stats. Semua diekstrak dari AST
`_system.py`; perubahan sumber yang menggeser kontrak membuat `--check` gagal.

## Integrasi CI

- Path filter `godot-check.yml`/`godot-rebuild.yml` mencakup `_system.py`,
  `storage_paths.py`, `mobile/combat_audio.py`, dan tool system.
- Langkah prepare menjalankan `prepare_godot_system.py --check` +
  `test_godot_system_prepare.py`.
- `validate_project.py` memverifikasi modul system, kontrak, wiring spatial grid,
  frustum culling, audio posisional, migrasi legacy, dan adaptive quality.
- `run_all.gd` menambah `_test_system()` (spatial/frustum/FPS/adaptive/audio/save).

## Batasan yang jujur

- Output audio nyata belum diverifikasi (headless/dummy driver); tes memverifikasi
  state, throttle, kategori volume, dan positional gating, bukan gelombang suara.
- `FPSCounter.draw()` pygame asli mengalami `NameError: get_font` tanpa shim
  (lihat `tools/test_system_perf_parity.py`); port Godot memakai `RenderCache`
  sehingga jalur overlay benar-benar hidup, tetapi tidak diklaim pixel-perfect.
- Spatial grid dipakai untuk target menara; pencarian target hero/minion masih
  memakai `enemies_of()` langsung agar urutan target lama tetap stabil. Grid
  tersedia lewat `MatchModel.query_enemies_in_range()` untuk pemakaian lanjutan.
- Adaptive quality default **mati** (`auto_quality=false`) supaya perilaku render
  manual tidak berubah tanpa persetujuan pengguna.
- Migrasi legacy hanya menyalin `progress.json` di direktori native ke slot 1;
  ia tidak membaca `saves/` Python secara diam-diam.
- Android/perangkat nyata, keystore, Play Games, top-up produksi tetap di luar
  cakupan verifikasi system ini.
