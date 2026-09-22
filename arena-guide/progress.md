# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L29 (heartbeat fix) DONE** — user konfirmasi 2026-09-22.
- **Main.gd DIARSIPKAN** di `arena-guide/project/Main.gd` = kondisi **pasca-L29**
  (L15–L29 lengkap, heartbeat dedent benar).
- **AUDIT PARITAS VISUAL MAP #1–#6 SELESAI** (L23–L28 + screenshot).
- Animasi L19–L22 (torch/rune/asap/firefly/fog) harus hidup tiap 0.15 dtk lagi.
- Minion.gd arsip tetap (2026-09-22).
- **Tidak ada langkah map-bake wajib yang terbuka.**
- CATATAN PLATFORM: `git fetch` → `git reset --soft origin/branch` → add → commit → push.
  Jangan force-push.

## Project user (tidak ada di repo ini)

- Godot 4.7.1, renderer **Mobile**, 1280x720, desktop F5.
- Lokasi: `D:\mystic-godot-471` / `~/mystic-godot-471`.

## Geometri diagonal (dari L15, tidak berubah)

- BASE_BLUE=(130,595) BASE_RED=(1145,175) HERO_SPAWN=(250,580)
- SHOP_BLUE=(340,540) SHOP_RED=(940,180)
- threshold_y(x)=200+320x/1280

## Member penting (pasca-L29)

- `_decor16/21/22/23/24/25_cache`, `_flame_t`/`_flame_frame`, `_anim_t`
- Heartbeat `_process`: `_flame_t += delta` di level fungsi (1 Tab), tiap 0.15 →
  frame+1, `_anim_t+=9.0`, `queue_redraw()`
- L25 seed di file user = **3500**
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
| L25 | dead trees DIRE twisted (seed 3500) | DONE |
| L26 | bayangan dekor lama | DONE |
| L27 | terrain density + t2/d3 | DONE |
| L28 | slash → crack 1px | DONE |
| L29 | fix heartbeat dedent `_flame_t` | DONE |

## Audit paritas visual

| # | Gap | Status |
|---|---|---|
| 1–6 | lane/landmark/dead tree/shadow/terrain/slash | DONE |

**→ Sesi port map visual L15–L29 SELESAI.**

## Opsional berikutnya (bukan audit #1–#6)

1. Dark tree density pygame (~45) vs plan user (12) — gap terpisah.
2. Arsip script lain: Tower/Hero/Shop/HUD/Nexus/LevelDB (minta paste).
3. Paritas unit/combat/FX/UI di luar map bake.
4. Stop — map bake sudah cukup.
