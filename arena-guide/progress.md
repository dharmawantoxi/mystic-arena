# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L28 (polish slash L17 → crack 1px): SNIPPET SIAP — ganti `_draw17_slashes` saja.**
- **L27 (terrain density): DONE** — screenshot user 2026-09-22 (wave 1, GOLD 515,
  dead trees DIRE, landmark+panji, bayangan, lane bata, terrain padat).
- **L24 + L25 + L26 DONE** (user konfirmasi + screenshot L27 memverifikasi semuanya).
- L15–L23 DONE.
- Audit paritas visual #1–#5 DONE; #6 = L28 (polish opsional, tapi disiapkan).
- **Main.gd + Minion.gd user DIARSIPKAN** di `arena-guide/project/` (exact copy, 2026-09-22,
  pre-L25). Minta re-paste Main.gd setelah L28 untuk arsip final.
- **BUG heartbeat DIPERBAIKI user** (dedent `_flame_t += delta`).
- CATATAN PLATFORM: HEAD branch sesi bisa ter-reset ke base tiap turn. Alur commit aman:
  `git fetch` → `git reset --soft origin/branch` → `git add` → commit → push.
  Jangan force-push.

## Project user (tidak ada di repo ini)

- Godot 4.7.1 fresh dari nol, renderer **Mobile**, 1280x720, target desktop (F5 jalan).
- Lokasi: `D:\mystic-godot-471` atau `~/mystic-godot-471` (PC user, agent tidak punya akses).
- Sistem lama L1–L12/L14: hero Kaizen HP550 skill Q/W/E/R, tower, shop ITEM/SHOP, gold,
  wave, HUD (GOLD/WAVE di LUAR `_draw()`).

## Geometri diagonal (Main.gd user, dari L15)

- `BASE_BLUE=Vector2(130,595)`, `BASE_RED=Vector2(1145,175)`, `HERO_SPAWN=Vector2(250,580)`
- Shop biru=`Vector2(340,540)`, shop merah=`Vector2(940,180)`
- `threshold_y(x)=200+320x/1280`; radiant = y>threshold, dire = y<threshold
- Waypoints: LANE_TOP/MID/BOT + RIVER (lihat steps L15-note)
- Clearance dekor: lane 55, sungai 60, toko 100, base 130, slot 45, antar-dekor 34

## Member penting Main.gd user (terkonfirmasi)

- `slots`, `_decor16/21/22/23/24/25_cache`, `_flame_t`/`_flame_frame`, `_anim_t`
- Heartbeat `_process` 0.15 dtk → frame+1, `_anim_t+=9.0`, `queue_redraw()`
- MapTheme forest punya `d3` (dipakai L27)

## Urutan `_draw()` user (setelah L26)

```
terrain, terrain_details, river, decor18, river_runes(L20), lanes, decor23,
base_plates, border_wall, decor26, decor, decor25, decor17, decor16, decor24,
shops, shop_fx(L20), particles(L21), loop slots, fog(L22),
overlay match_over (TERAKHIR)
```

## Jejak langkah

| Step | Isi | Status |
|---|---|---|
| L15–L23 | diagonal + decor ambient + lane bata | DONE |
| L24 | landmark dead-knight + panji (seed 2400) | DONE |
| L25 | pohon mati DIRE twisted 2-tone (seed 2500) | DONE |
| L26 | bayangan hitam bawah dark_tree/bush/rock/grave | DONE |
| L27 | terrain density + t2 fix + d3 micro-detail | DONE (screenshot) |
| L28 | ganti `_draw17_slashes` → crack 1px path_crack | SIAP tempel |

## Audit paritas visual (bake `godot/assets/maps/forest.png`)

| # | Gap | Status |
|---|---|---|
| 1 | Lane bata + border stone + crack | DONE (L23) |
| 2 | Landmark dead-knight + panji | DONE (L24) |
| 3 | Pohon mati twisted dire | DONE (L25) |
| 4 | Bayangan hitam bawah dekor | DONE (L26) |
| 5 | Ground micro-detail density | DONE (L27) |
| 6 | Slash L17 kepanjangan vs crack 1px | L28 SIAP |

## Setelah audit map selesai

- Opsional: paste ulang Main.gd → arsip `project/Main.gd`
- Sisa di luar audit map: unit/FX/UI lain (bukan fokus arena-guide L15+)
