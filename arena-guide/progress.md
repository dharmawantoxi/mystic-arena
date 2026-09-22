# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L32 (lane tidy — anti berantakan): SIAP & TERPASANG di `scripts/Main.gd` + `project/Main.gd`.**
  MID zig-zag 4 belokan → monotonic diagonal halus 9 titik; SMOOTH [10,8,10]→[12,12,12]; `_draw_lanes` cuma outline 52 + p1 46 + highlight 10 tipis (tanpa cobble dobel); bata 16px radius 27 + border jarak-tempuh 32px merata; crack %7→%11 & moss >85→>90 → lane tidak bercak-bercak. TOP/BOT juga diperhalus & diperrapat.
  `godot/scenes/map/ArenaMap.gd` fallback juga diperhalus (antialiased + cobble/moss dipersparse).
- **L31 (panel kanan bata + STATUS/HERO/SKILL/TACTICAL): SNIPPET SIAP.**
  Viewport 1624x720, arena 1280 kiri, rail bata 344 kanan. Tactical = stub visual dulu.
- L30 lane-clean (mid smooth + hide hint) — **tergantikan L32** (lebih lengkap, sudah termasuk L30 + TOP/BOT).
- L29 heartbeat DONE. Audit map #1–#6 DONE.
- `project/Main.gd` = pasca-L32 (sinkron dengan `scripts/Main.gd` — lane rapi).
- CATATAN PLATFORM: fetch → reset --soft origin/branch → add → commit → push.

## Geometri panel (pygame paritas)

- VIEW 1624x720; ARENA 0..1280; PANEL_X=1280 PANEL_W=344
- Latar bata 16px path_stone + outline
- Zona: pause y14 | STATUS ~96 | HEROES | SKILLS QWER | TACTICAL 5 tombol

## Geometri lane (L32 — rapi)

- LANE_TOP_WP 12 titik: (90,590)…(1180,180) — sudut atas diperhalus (115,230 /165,175 /235,110 /360,78 /520,68 /690,70 /860,80 /1020,115)
- LANE_MID_WP 9 titik monotonic: (170,550) (280,450) (400,380) (520,350) (640,340) (760,330) (880,300) (1000,240) (1110,170)
- LANE_BOT_WP 13 titik: (130,630)…(1180,180) + 2 titik vertical smoothing (1185,410 /1185,235)
- LANE_SMOOTH [12,12,12] — Catmull-Rom 12 step/segmen, join bulat anti-aliased
- Lebar lane: outline 52 + p1 46 + highlight 10 (0.28 alpha) — bata 16px di _decor23
- Bata axis-aligned 16px: jarak 27px radius (729), border batu tiap 32px jarak-tempuh (bukan tiap 6 idx), crack %11 (9%), moss >90 (10%)

## Urutan _draw() rapi

`_draw_terrain → _draw_terrain_details → _draw_river → _draw_decor18 → _draw20_river_runes → _draw_lanes (garis dasar) → _draw_decor23 (bata+border) → _draw_base_plates → _draw_border_wall → _draw_decor26/24/25/17/16 → _draw_shops → ... → _draw22_fog` — lane dasar dulu baru bata L23 di atasnya (tidak tertutup draw lain), tidak ada cobble dobel di bawah bata.

## Jejak

| Step | Isi | Status |
|---|---|---|
| L15–L29 | map parity + heartbeat | DONE |
| L30 | mid lane smooth + no cobble + hide hint | SIAP (diganti L32) |
| L31 | side panel brick + status/hero/skill/tactical | SIAP |
| **L32** | **lane tidy total (TOP/MID/BOT smooth + uniform 12 + clean draw + bata rapat + border merata + crack/moss sparse)** | **SIAP & TERPASANG** |

## File baru

- `arena-guide/scripts/SidePanel.gd` + `steps/L31-side-panel.gd`
- `arena-guide/steps/L32-lane-tidy.gd` — snippet lane rapi total (pengganti + pelengkap L30)
