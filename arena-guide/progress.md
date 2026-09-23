# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L31 (panel kanan bata + STATUS/HERO/SKILL/TACTICAL): SNIPPET SIAP.**
  User minta panel kanan seperti pygame (`mobile/sidepanel.py`).
  Viewport 1624x720, arena 1280 kiri, rail bata 344 kanan.
  Tactical = stub visual dulu (logika penuh belakangan).
- L30 lane-clean **REVISI 2026-09-23 — DIKEMBALIKAN KE PYGAME FINAL**: L30a mid-smooth
  (280,450...) DIBATALKAN atas instruksi user — lane harus 1:1 pygame. L30b/c
  (hapus cobble + hide hint) TETAP. `scripts/Main.gd` + `project/Main_FULL_L31.gd`
  + `steps/L30` sudah sync ke waypoint pygame `map_components/_bundle.py`.
- **L32 2026-09-23 — FIX PATAH + RAPAT CASTLE (dari screenshot 1.png) DIBATALKAN:**
  Atas instruksi user kedua “samakan dengan pygame game saja”, L32 halus (TOP+1wp,
  BOT geser, MID halus, SMOOTH 14, BASE_RED 1180) **DIKEMBALIKAN ke PYGAME FINAL**
  `map_components/_bundle.py`. `scripts/Main.gd` + `FULL_L31` kembali ke TOP
  (120,220/170,180/240,100), MID (300,420... 65°), BOT (1070,620/1170,500),
  SMOOTH [10,8,10], BASE_RED 1145,175 (spase 35px memang ada di pygame). L32
  snippet diarsipkan sebagai referensi visual saja, tidak dipakai.
- L29 heartbeat DONE. Audit map #1–#6 DONE. **Audit lane 2026-09-23 FINAL: 100%
  PYGAME — TOP 12wp / MID 9wp / BOT 11wp / RIVER 7wp + smooth [10,8,10] + trunc
  int(x),int(y). Patah & spase di 1.png memang ada di pygame asli.**
- `project/Main.gd` = pasca-L29 (sudah paritas, belum L31). `scripts/Main.gd` = L15-L29 + L30b/c + L31 (pygame final).
- CATATAN PLATFORM: fetch → reset --soft origin/branch → add → commit → push.

## Geometri panel (pygame paritas)

- VIEW 1624x720; ARENA 0..1280; PANEL_X=1280 PANEL_W=344
- Latar bata 16px path_stone + outline
- Zona: pause y14 | STATUS ~96 | HEROES | SKILLS QWER | TACTICAL 5 tombol

## Jejak

| Step | Isi | Status |
|---|---|---|
| L15–L29 | map parity + heartbeat | DONE |
| L30 | REVISI pygame: kembalikan mid ke (300,420...) + no cobble + hide hint | **SYNC PYGAME 2026-09-23** |
| L31 | side panel brick + status/hero/skill/tactical | SIAP |
| L32 | halus patah + rapat castle → **DIBATALKAN** per instruksi “samakan pygame” | **ARSIP — KEMBALI PYGAME FINAL** |

## File baru

- `arena-guide/scripts/SidePanel.gd` + `steps/L31-side-panel.gd`
