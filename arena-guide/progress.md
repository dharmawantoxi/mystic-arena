# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **AUDIT PARITAS VISUAL MAP #1–#6 SELESAI** (L15–L28, screenshot L28 2026-09-22
  WAVE 2 / GOLD 562 — crack lane tipis 1px path_crack, dead trees, landmark+panji,
  bayangan, terrain density, lane bata semua tampil).
- L15–L28 semua DONE.
- **Main.gd + Minion.gd user DIARSIPKAN** di `arena-guide/project/` (exact copy 2026-09-22,
  kondisi **pre-L25**). Minta user paste ulang `Main.gd` untuk arsip final pasca-L28.
- **BUG heartbeat DIPERBAIKI user** (dedent `_flame_t += delta`).
- CATATAN PLATFORM: HEAD branch sesi bisa ter-reset. Alur commit aman:
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
- MapTheme forest punya `d3` (L27)
- `_draw17_slashes` pasca-L28: 28 crack 1px Color8(170,36,61), half 2.5–4.5

## Urutan `_draw()` user (final L26+)

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
| L27 | terrain density + t2 fix + d3 micro-detail | DONE |
| L28 | `_draw17_slashes` → crack 1px path_crack | DONE |

## Audit paritas visual (bake `godot/assets/maps/forest.png`)

| # | Gap | Status |
|---|---|---|
| 1 | Lane bata + border stone + crack | DONE (L23) |
| 2 | Landmark dead-knight + panji | DONE (L24) |
| 3 | Pohon mati twisted dire | DONE (L25) |
| 4 | Bayangan hitam bawah dekor | DONE (L26) |
| 5 | Ground micro-detail density | DONE (L27) |
| 6 | Slash L17 → crack 1px | DONE (L28) |

**→ Audit map visual SELESAI.** Tidak ada gap audit terbuka.

## Sisa di luar audit map (belum dikerjakan di sesi ini)

- Arsip `project/Main.gd` masih pre-L25 — minta paste ulang.
- Script lain belum diarsip: Tower/Hero/Shop/HUD/Nexus/LevelDB (ada draft di `scripts/`).
- Paritas unit/combat/FX/UI (bukan fokus L15–L28).
- Dark tree density pygame (45 placement) vs plan user (12) — gap terpisah, bukan #1–#6.

## Referensi pygame (ringkas)

- `map_components/_bundle.py`: terrain 4971+, dead trees 6199+, landmark ~7060,
  lane cobble 5200+, path_crack Forest (170,36,61), DEAD_TREE_1/2 (28,20,18)/(55,42,35).
