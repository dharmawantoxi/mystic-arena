# L15 — catatan (file verbatim tidak tersimpan)

L15 adalah full-paste `Main.gd` (~640 baris) + `Minion.gd` (~150 baris) konversi
FULL DIAGONAL. Isi verbatim-nya tidak tersimpan di arsip ini (panduan dikirim via chat
sebelum folder arsip ada). JANGAN merekonstruksi dari nol — minta user upload file bila butuh exact.

## Spesifikasi L15 (untuk acuan)

- Base sudut: `BASE_BLUE(130,595)`, `BASE_RED(1145,175)`; `HERO_SPAWN(250,580)`
- Shop ikut pygame: `(340,540)` biru, `(940,180)` merah
- 3 lane Catmull-Rom + sungai diagonal (waypoint & smooth lihat `progress.md`)
- `threshold_y(x)=200+320x/1280`, band sungai ±20
- Slot on-lane dari fraksi path (lihat `progress.md`), tanpa offset
- Lane: polyline 46 + `_draw_cobble` tiap 16px via `draw_set_transform` (wajib reset!)
  + border tiap 48px. River: polyline 58/46/30 + glow/bank
- Terrain diagonal + detail RNG seed 100; zona dekor radiant/dire; clearance
  lane 55 / sungai 60 / toko 100 / base 130 / slot 45 / antar-dekor 34
- Minion: `setup(team, lane_path, forward, lateral)` + path-follow `_path_target`;
  signature lama dihapus total; lateral `(i-1)*22`

## Jika user upload Main.gd/Minion.gd

Simpan exact copy di `arena-guide/project/` dan update `progress.md`.
