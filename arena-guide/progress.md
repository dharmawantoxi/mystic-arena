# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **Main.gd user DIARSIPKAN ulang** di `arena-guide/project/Main.gd` (exact copy
  **pasca-L28**, 2026-09-22). L15–L28 lengkap.
- **REGRESI HEARTBEAT terdeteksi di paste user:** `_flame_t += delta` lagi
  ter-nest di dalam `if wave_timer <= 0.0` (sama bug yang pernah difix).
  → L29 fix SIAP (dedent 1 baris).
- **AUDIT PARITAS VISUAL MAP #1–#6 SELESAI** (L23–L28, screenshot OK).
- L25 seed di file user = **3500** (bukan 2500 snippet awal) — dibiarkan, placement
  tetap valid DIRE.
- Minion.gd arsip tetap (2026-09-22).
- CATATAN PLATFORM: `git fetch` → `git reset --soft origin/branch` → add → commit → push.
  Jangan force-push.

## Project user (tidak ada di repo ini)

- Godot 4.7.1, renderer **Mobile**, 1280x720, desktop F5.
- Lokasi: `D:\mystic-godot-471` / `~/mystic-godot-471`.

## Geometri diagonal (dari L15, tidak berubah)

- BASE_BLUE=(130,595) BASE_RED=(1145,175) HERO_SPAWN=(250,580)
- SHOP_BLUE=(340,540) SHOP_RED=(940,180)
- threshold_y(x)=200+320x/1280

## Member penting (pasca-L28)

- `_decor16/21/22/23/24/25_cache`, `_flame_t`/`_flame_frame`, `_anim_t`
- MapTheme forest `d3` dipakai L27
- `_draw17_slashes` L28: 28× crack 1px Color8(170,36,61)

## Urutan `_draw()` final

```
terrain, terrain_details, river, decor18, river_runes, lanes, decor23,
base_plates, border_wall, decor26, decor, decor25, decor17, decor16, decor24,
shops, shop_fx, particles, slots, fog, match_over overlay
```

## Jejak langkah

| Step | Isi | Status |
|---|---|---|
| L15–L23 | diagonal + ambient + lane bata | DONE |
| L24 | landmark dead-knight + panji | DONE |
| L25 | dead trees DIRE twisted (seed 3500 di file user) | DONE |
| L26 | bayangan dekor lama | DONE |
| L27 | terrain density + t2/d3 | DONE |
| L28 | slash → crack 1px | DONE |
| L29 | fix regresi heartbeat dedent `_flame_t` | SIAP |

## Audit paritas visual

| # | Gap | Status |
|---|---|---|
| 1–6 | lane/landmark/dead tree/shadow/terrain/slash | DONE |

## Setelah L29

- Animasi L19–L22 harus hidup lagi tiap 0.15 dtk.
- Opsional: dark tree density pygame (~45) vs plan 12.
- Opsional: arsip script lain (Tower/Hero/HUD/...).
