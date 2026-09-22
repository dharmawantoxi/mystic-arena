# Progress — mystic-godot-471 (port manual Godot)

> Untuk agent di chat baru: baca seluruh file ini sebelum menjawab user.

## Status terakhir

- **L24 (landmark dead-knight + panji): kode + hook TERKONFIRMASI ADA di file user,
  menunggu screenshot ("langkah 24 done").**
- L15–L23 DONE, semuanya terverifikasi via screenshot.
- User menolak klaim "paritas selesai" (benar) → audit paritas dibuka, gap dikerjakan berurutan.
- **Main.gd + Minion.gd user DIARSIPKAN** di `arena-guide/project/` (exact copy, 2026-09-22).
- **BUG heartbeat DIPERBAIKI user** (dedent `_flame_t += delta` ke 1 Tab, 2026-09-22);
  arsip Main.gd = kondisi setelah fix. Animasi L19–L22 seharusnya hidup kembali.
- `_draw_decor` user SUDAH diketahui → bayangan pohon (audit #4) tidak lagi blocked.
- CATATAN PLATFORM: HEAD branch sesi bisa ter-reset ke base tiap turn (file kerja tetap ada
  sebagai untracked). Alur commit yang aman: `git fetch` → `git reset --soft origin/branch`
  → cek `git status` → `git add` → commit → push. Jangan pernah force-push.

## Project user (tidak ada di repo ini)

- Godot 4.7.1 fresh dari nol, renderer **Mobile**, 1280x720, target desktop (F5 jalan).
- Lokasi: `D:\mystic-godot-471` atau `~/mystic-godot-471` (PC user, agent tidak punya akses).
- Sistem lama dari L1–L12/L14 tidak berubah: hero Kaizen HP550 skill Q/W/E/R, tower,
  shop ITEM/SHOP, gold, wave, HUD (GOLD/WAVE digambar di LUAR `_draw()`).

## Geometri diagonal (Main.gd user, dari L15)

- `BASE_BLUE=Vector2(130,595)`, `BASE_RED=Vector2(1145,175)`, `HERO_SPAWN=Vector2(250,580)`
- Shop biru=`Vector2(340,540)`, shop merah=`Vector2(940,180)` (ikut pygame)
- `threshold_y(x)=200+320x/1280`; radiant = y>threshold (hijau), dire = y<threshold (coklat)
- Waypoints: `LANE_TOP_WP` 12pt (90,590)->(1180,180) smooth 10 (~111 titik);
  `LANE_MID_WP` 9pt (170,550)->(1110,170) smooth 8 (~65 titik);
  `LANE_BOT_WP` 11pt (130,630)->(1180,180) smooth 10 (~101 titik);
  `RIVER_WP` 7pt (0,200)->(1280,520) smooth 10 (~61 titik)
- Fungsi yang ADA di Main.gd: `_build_paths`, `_curved_path(wp,smooth)`,
  `_threshold_y(x)`, `_side_of`, `_dist_to_pts`, `_draw_cobble`, `_draw_terrain_details`
- Lane: polyline 46 + cobble tiap 16px (`draw_set_transform`, WAJIB reset!) + border tiap 48px.
  SEJAK L23: permukaan lane ditutup overlay bata 16px (cobble lama tertutup, kode lama dibiarkan).
- Sungai: polyline 58/46/30 + glow/bank (lebar luar 58 → setengah 29).
- Slot menara ON-LANE persis tanpa offset (ikut pygame `_generate_build_slots_from_lanes`):
  top/bot blue [0.15,0.30,0.45] red [0.85,0.70,0.55];
  mid blue [0.10,0.25,0.40] red [0.90,0.75,0.60]
- Minion.gd: `setup(team,lane_path,forward,lateral)`, path-follow `_path_target`, lateral (i-1)*22
- Clearance dekor: lane 55, sungai 60, toko 100, base 130, slot 45, antar-dekor 34

## Member penting Main.gd user (terkonfirmasi)

- `slots`: Array of Dict `{pos:Vector2, team:"blue"/"red", taken:bool}`
- `_decor16_cache` [kind,Vector2,int], `_decor21_cache` [base,amp,sp,ph,size,Color],
  `_decor22_cache` [base,size,vx], `_decor23_tiles` Vector2i + `_decor23_borders`,
  `_decor24_cache` [pos,variant]
- `_flame_t`/`_flame_frame` (api obor), `_anim_t` (waktu animasi, +=9.0/heartbeat)
- Heartbeat `_process`: tiap 0.15 dtk → frame+1, `_anim_t+=9.0`, `queue_redraw()`

## Urutan `_draw()` user (terkini)

```
terrain, terrain_details, river, decor18, river_runes(L20), lanes, decor23,
base_plates, border_wall, decor, decor17, decor16, decor24, shops, shop_fx(L20),
particles(L21), loop slots, fog(L22), overlay match_over (VICTORY/DEFEAT, TERAKHIR)
```

## Jejak langkah

| Step | Isi | Status |
|---|---|---|
| L15 | Full-paste Main.gd + Minion.gd diagonal (base sudut, 3 lane Catmull-Rom, sungai diagonal, slot fraksi) | DONE (file verbatim TIDAK tersimpan di sini!) |
| L16 | Ruins/spike/glow-flower (seed 1600) + 18 torch border fixed | DONE (+fix: pakai member slots) |
| L17 | Shadow bawah dekor16 + 42 slash merah lane (seed 1700) | DONE |
| L18 | Bank sungai checker + titik magenta | DONE |
| L19 | Api obor 4 frame + heartbeat `_process` 0.15dtk | DONE (animasi per konfirmasi user) |
| L20 | Rune sungai + glow/asap toko; `_anim_t`; fix `roundf`+explicit float | DONE |
| L21 | 30 firefly, warna ikut sisi diagonal (seed 2100) | DONE |
| L22 | 15 kabut sisi dire, drift fposmod (seed 2200) | DONE |
| L23 | Lantai lane bata 16px grid + border stone; fix `len`→`seglen` | DONE |
| L24 | ~30 landmark dead-knight abaddon + panji tiap index%6==0 (seed 2400) | PENDING konfirmasi |

## Audit paritas visual (bake `godot/assets/maps/forest.png`)

| # | Gap | Status |
|---|---|---|
| 1 | Lane bata persegi + border stone + crack merah | DONE (L23) |
| 2 | Landmark dead-knight + panji merah | L24 pending |
| 3 | Pohon mati twisted dire (d1 28,20,18 d2 55,42,35; kode `_draw_dead_trees` sudah dibaca) | TODO (butuh baca placement count) |
| 4 | Bayangan hitam bawah pohon/bush/batu | BLOCKED — butuh user paste `_draw_decor` (diminta 4x) |
| 5 | Ground micro-detail density + palette | TODO (sentuh terrain) |
| 6 | Slash L17 kepanjangan vs crack 1px pygame | Polish opsional |

## Referensi pygame yang sudah dibaca (di repo ini)

- Slot: `_core.py:1654` `_generate_build_slots_from_lanes`
- Dekor: `map_components/_bundle.py` — ruins 6304, spike 6392, flower 6462, torch 5743-5894,
  placement 4795-4890, lane 5156-5200, cobble tile 5201-5264, border stone 5265+,
  dead trees 6199-6260, landmark abaddon ~7060-7090, fog 5424/5542, river anim 5565,
  shop glow/smoke 5601-5666, particles 5366/5666. TILE_SIZE=16. Warna Forest path_stone
  (58,52,45)(85,76,65)(115,105,90)(145,130,108), moss (65,90,45), rmoss (55,90,40),
  crack (170,36,61). Torch border: x=120..1120 step200 di y=32/688 + y=120..520 step200 di x=32/1248.

## Yang BELUM ada di arsip

- Main.gd ✅ + Minion.gd ✅ tersimpan di `arena-guide/project/` (exact copy 2026-09-22).
- Masih kurang: script/scene lain (Tower/Hero/Shop/HUD/Nexus/LevelDB/...).
  Minta user attach file `.gd` → simpan exact copy di `arena-guide/project/`.
