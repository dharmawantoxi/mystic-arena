# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L31 (panel kanan bata + STATUS/HERO/SKILL/TACTICAL): SNIPPET SIAP.**
  User minta panel kanan seperti pygame (`mobile/sidepanel.py`).
  Viewport 1624x720, arena 1280 kiri, rail bata 344 kanan.
  Tactical = stub visual dulu (logika penuh belakangan).
- L30 lane-clean SIAP (mid smooth + hide hint) — boleh digabung dengan L31.
- L29 heartbeat DONE. Audit map #1–#6 DONE.
- `project/Main.gd` = pasca-L29 (belum L30/L31).
- CATATAN PLATFORM: fetch → reset --soft origin/branch → add → commit → push.

## Geometri panel (pygame paritas)

- VIEW 1624x720; ARENA 0..1280; PANEL_X=1280 PANEL_W=344
- Latar bata 16px path_stone + outline
- Zona: pause y14 | STATUS ~96 | HEROES | SKILLS QWER | TACTICAL 5 tombol

## Jejak

| Step | Isi | Status |
|---|---|---|
| L15–L29 | map parity + heartbeat | DONE |
| L30 | mid lane smooth + no cobble + hide hint | SIAP |
| L31 | side panel brick + status/hero/skill/tactical | SIAP |

## File baru

- `arena-guide/scripts/SidePanel.gd` + `steps/L31-side-panel.gd`
