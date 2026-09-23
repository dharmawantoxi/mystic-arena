# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L34 2026-09-23 — AUDIT VISUAL ITEM FORGE 1:1 (PYGAME VS GODOT): AUDIT SELESAI.**
  Audit komprehensif `hero_items.py` (ItemShopUI) vs `ShopPanel.gd`, `ItemForgeCard.gd`, `ItemIcons.gd`, `Shop.gd`:
  Panel 1100x720 (center px=90, py=0), kartu 250x200, ikon 56x56, grid 4x2 per halaman (8 item per halaman), 6 tab kelas (PHYSICAL 1/2, 2/2, MAGIC 1/2, 2/2, TANK 1/2, 2/2), strip BUY FOR hero, banner stat hero 2-baris, dan strip inventory bawah 6 slot (54x54) dengan aksi jual 70%. Dokumentasi lengkap di `arena-guide/docs/AUDIT_ITEM_FORGE.md`.
- **L31 (panel kanan bata + STATUS/HERO/SKILL/TACTICAL): PASANG & VERIFIED 2026-09-23.**
  Screenshot user `1.png` → panel 344px bata, STATUS GOLD/LV/Wave, HEROES Kaizen 550, SKILLS QWER, TACTICAL 5 tombol — 100% parity `mobile/sidepanel.py`. Viewport 1624x720 OK.
- **L33 2026-09-23 — TACTICAL FULL (G/T/C/B/D): SNIPPET SIAP.** Stub L31 (`print` + gather mini) → 5 perintah penuh: GATHER (250,580), PROTECT TOWER (tower biru terdekat/slot), PROTECT CASTLE (BASE_BLUE), ATTACK BOSS (640,360 tengah sungai), ATTACK DD (musuh terdekat → nexus). + hotkey G/T/C/B/D. `scripts/Main.gd` + `SidePanel.gd` + `FULL_L31` updated, `steps/L33-tactical-full.gd` baru.
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
- `project/Main.gd` = pasca-L29 (sudah paritas, belum L31). `scripts/Main.gd` = L15-L29 + L30b/c + L31 panneau + L33 tactical full.
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
| L31 | side panel brick + status/hero/skill/tactical | **PASANG & VERIFIED 1.png 2026-09-23** |
| L32 | halus patah + rapat castle → **DIBATALKAN** per instruksi “samakan pygame” | **ARSIP — KEMBALI PYGAME FINAL** |
| L33 | tactical 5 penuh G/T/C/B/D + hotkey (gather/tower/castle/boss/DD) | **SNIPPET SIAP 2026-09-23** |
| L34 | audit visual Item Forge 1:1 pygame vs Godot (panel 1100x720, kartu 250px, ikon 56px, grid 4x2, tab kelas, inv 6) | **AUDIT DONE 2026-09-23** |
| L35 | visual Item Forge 1:1 pygame (panel 1100x720, kartu 250x200, ikon 56px, grid 4x2, 6 tab kelas, inv 6 slot jual 70%, popup detail) | **VERIFIED 1.png 2026-09-23** |

## File baru

- `arena-guide/scripts/SidePanel.gd` + `steps/L31-side-panel.gd` + `steps/L33-tactical-full.gd` (tactical full)
- `arena-guide/docs/AUDIT_ITEM_FORGE.md` (audit item forge 1:1 pygame vs godot)
- `arena-guide/scripts/Shop.gd` + `godot/scripts/Shop.gd` (visual item forge 1:1 pygame)
