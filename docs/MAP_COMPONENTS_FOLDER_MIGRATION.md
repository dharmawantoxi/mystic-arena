# Migrasi folder `map_components/` ke Godot

Dokumen ini menutup sub-task **“lihat folder map_components dan migrasikan semua kegodot”**:
dua berkas Python (7.504 baris) yang memuat tujuh modul peta, dipetakan simbol per simbol
ke berkas Godot, ke data JSON, ke bake PNG, atau ke hasil eksekusi sumber.

## Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Berkas sumber | 2 (`_bundle.py` 7.403 baris + `__init__.py` 101 baris) |
| Modul gabungan | 7 (palettes, themes, generators, static_renderer, dynamic_renderer, decoration_renderer, shop_renderer) |
| Konstanta palet | 52 warna + `TILE_SIZE` = 16 |
| Tema | 54 dict, gabungan 77 kunci (55 kunci per tema) |
| Generator | 3 lane + 61 titik sungai + 14 array dekorasi |
| Kelas | 5 top-level + 4 kelas bersarang (`PathGenerator`, `DecorationGenerator`, `StaticRenderer`, `ShopRenderer`) |
| Simbol terklasifikasi | 194 |
| Sebaran jenis | bake 39, data 112, executed 9, internal 1, meta 2, native 31 |

Semua simbol wajib punya entri; oracle menolak jalan kalau ada simbol tanpa entri
(`AssertionError: unclassified symbols [...]`) dan menolak entri tanpa bukti
(`no evidence [...]`, yaitu target tanpa token di berkasnya).

## Kosakata klasifikasi

| Jenis | Arti | Bukti yang diminta |
| --- | --- | --- |
| `native` | perilaku diport ke skrip Godot | berkas + token (nama fungsi/konstanta) + nomor baris |
| `data` | nilainya pindah ke JSON yang dibaca runtime | berkas JSON + kunci |
| `bake` | simbol hanya melukis piksel; bake mereproduksinya | skrip bake + titik masuknya |
| `executed` | sumbernya dieksekusi oracle, hasilnya dipin | `tests/fixtures/map_components_source.json` |
| `meta` | plambing impor Python, tanpa arti runtime | `map_components/__init__.py` |
| `internal` | cache/memo yang hilangnya tidak mengubah gambar | berkas + catatan deviasi |

## Inventaris berkas dan modul

| Berkas | Baris |
| --- | --- |
| `__init__.py` | 101 |
| `_bundle.py` | 7403 |

`_bundle.py` adalah satu modul Python yang memuat tujuh modul lama berurutan.
Penanda `# map_components/<nama>.py` di dalamnya menjadi batas modul:

| Modul | Baris awal | Baris akhir | Baris |
| --- | --- | --- | --- |
| `palettes.py` | 36 | 129 | 94 |
| `themes.py` | 130 | 4659 | 4530 |
| `generators.py` | 4660 | 4953 | 294 |
| `static_renderer.py` | 4954 | 5327 | 374 |
| `dynamic_renderer.py` | 5328 | 6060 | 733 |
| `decoration_renderer.py` | 6061 | 7151 | 1091 |
| `shop_renderer.py` | 7152 | 7403 | 252 |

Jumlah tujuh rentang itu 7.368 baris; 35 baris pertama adalah header `_bundle.py`
(docstring + import), jadi 35 + 7.368 = 7.403 baris tanpa sisa.

Kelas yang dipetakan: `DynamicRenderer`, `DecorationRenderer`, `PathGenerator`,
`DecorationGenerator`, `StaticRenderer`, `ShopRenderer`, serta tiga pembungkus
namespace `_NS_generators`, `_NS_static_renderer`, dan `_NS_shop_renderer`.

## Modul 1 - `palettes.py` (palet warna)

52 konstanta warna yang tidak bergantung tema (radiant, dire, transisi, path, stone,
sungai, pohon, kristal, api, outline, bayangan) plus `TILE_SIZE`.
Semuanya pindah ke **`data/levels/map_palette.json`** (dibangkitkan oracle) dan dibaca
lewat **`scripts/ui/map_palette.gd`**.

Sebelum lapisan ini, tiga rasteriser menyalin warna stone/outline sebagai literal:
`wall_tiles.gd` (5 warna), `lane_tiles.gd` (5), `river_tiles.gd` (4).
Sekarang ketiganya memanggil `MapPalette.palette([...])`, jadi `palettes.py` berubah
maka test gagal, bukan diam-diam melenceng.

| Simbol | Jenis | Target |
| --- | --- | --- |
| `CRYSTAL_BLUE_D` | `data` | `godot_rebuild/data/levels/map_palette.json`:3 |
| `CRYSTAL_BLUE_H` | `data` | `godot_rebuild/data/levels/map_palette.json`:8 |
| `CRYSTAL_BLUE_L` | `data` | `godot_rebuild/data/levels/map_palette.json`:13 |
| `CRYSTAL_BLUE_M` | `data` | `godot_rebuild/data/levels/map_palette.json`:18 |
| `CRYSTAL_RED_D` | `data` | `godot_rebuild/data/levels/map_palette.json`:23 |
| `CRYSTAL_RED_H` | `data` | `godot_rebuild/data/levels/map_palette.json`:28 |
| `CRYSTAL_RED_L` | `data` | `godot_rebuild/data/levels/map_palette.json`:33 |
| `CRYSTAL_RED_M` | `data` | `godot_rebuild/data/levels/map_palette.json`:38 |
| `DEAD_TREE_1` | `data` | `godot_rebuild/data/levels/map_palette.json`:43 |
| `DEAD_TREE_2` | `data` | `godot_rebuild/data/levels/map_palette.json`:48 |
| `DEAD_TREE_3` | `data` | `godot_rebuild/data/levels/map_palette.json`:53 |
| `DIRE_ASH` | `data` | `godot_rebuild/data/levels/map_palette.json`:58 |
| `DIRE_BURNT` | `data` | `godot_rebuild/data/levels/map_palette.json`:63 |
| `DIRE_EARTH_1` | `data` | `godot_rebuild/data/levels/map_palette.json`:68 |
| `DIRE_EARTH_2` | `data` | `godot_rebuild/data/levels/map_palette.json`:73 |
| `DIRE_EARTH_3` | `data` | `godot_rebuild/data/levels/map_palette.json`:78 |
| `DIRE_EARTH_4` | `data` | `godot_rebuild/data/levels/map_palette.json`:83 |
| `FIRE_D` | `data` | `godot_rebuild/data/levels/map_palette.json`:88 |
| `FIRE_H` | `data` | `godot_rebuild/data/levels/map_palette.json`:93 |
| `FIRE_L` | `data` | `godot_rebuild/data/levels/map_palette.json`:98 |
| `FIRE_M` | `data` | `godot_rebuild/data/levels/map_palette.json`:103 |
| `OUTLINE` | `data` | `godot_rebuild/data/levels/map_palette.json`:108 |
| `PATH_CRACK` | `data` | `godot_rebuild/data/levels/map_palette.json`:113 |
| `PATH_MOSS` | `data` | `godot_rebuild/data/levels/map_palette.json`:118 |
| `PATH_STONE_1` | `data` | `godot_rebuild/data/levels/map_palette.json`:123 |
| `PATH_STONE_2` | `data` | `godot_rebuild/data/levels/map_palette.json`:128 |
| `PATH_STONE_3` | `data` | `godot_rebuild/data/levels/map_palette.json`:133 |
| `PATH_STONE_4` | `data` | `godot_rebuild/data/levels/map_palette.json`:138 |
| `RADIANT_GRASS_1` | `data` | `godot_rebuild/data/levels/map_palette.json`:143 |
| `RADIANT_GRASS_2` | `data` | `godot_rebuild/data/levels/map_palette.json`:148 |
| `RADIANT_GRASS_3` | `data` | `godot_rebuild/data/levels/map_palette.json`:153 |
| `RADIANT_GRASS_4` | `data` | `godot_rebuild/data/levels/map_palette.json`:158 |
| `RADIANT_GRASS_HIGH` | `data` | `godot_rebuild/data/levels/map_palette.json`:163 |
| `RADIANT_MOSS` | `data` | `godot_rebuild/data/levels/map_palette.json`:168 |
| `RIVER_DEEP` | `data` | `godot_rebuild/data/levels/map_palette.json`:173 |
| `RIVER_FOAM` | `data` | `godot_rebuild/data/levels/map_palette.json`:178 |
| `RIVER_GLOW` | `data` | `godot_rebuild/data/levels/map_palette.json`:183 |
| `RIVER_LIGHT` | `data` | `godot_rebuild/data/levels/map_palette.json`:188 |
| `RIVER_MID` | `data` | `godot_rebuild/data/levels/map_palette.json`:193 |
| `SHADOW` | `data` | `godot_rebuild/data/levels/map_palette.json`:198 |
| `STONE_DARK` | `data` | `godot_rebuild/data/levels/map_palette.json`:203 |
| `STONE_HIGH` | `data` | `godot_rebuild/data/levels/map_palette.json`:208 |
| `STONE_LIGHT` | `data` | `godot_rebuild/data/levels/map_palette.json`:213 |
| `STONE_MID` | `data` | `godot_rebuild/data/levels/map_palette.json`:218 |
| `TILE_SIZE` | `data` | `godot_rebuild/data/levels/map_palette.json`:266 |
| `TRANSITION_1` | `data` | `godot_rebuild/data/levels/map_palette.json`:223 |
| `TRANSITION_2` | `data` | `godot_rebuild/data/levels/map_palette.json`:228 |
| `TREE_LEAVES_D` | `data` | `godot_rebuild/data/levels/map_palette.json`:233 |
| `TREE_LEAVES_H` | `data` | `godot_rebuild/data/levels/map_palette.json`:238 |
| `TREE_LEAVES_L` | `data` | `godot_rebuild/data/levels/map_palette.json`:243 |
| `TREE_LEAVES_M` | `data` | `godot_rebuild/data/levels/map_palette.json`:248 |
| `TREE_TRUNK_D` | `data` | `godot_rebuild/data/levels/map_palette.json`:253 |
| `TREE_TRUNK_L` | `data` | `godot_rebuild/data/levels/map_palette.json`:258 |

## Modul 2 - `themes.py` (54 tema)

54 dict tema; tiap tema membawa nama, `boss_identity`, `boss_title`, `particle_type`,
`particle_count`, `fog_*`, 25 kunci warna, dan sekitar 14 flag `has_*` yang menggerbangi
dekorasi. Data native-nya ada di **`data/art/map_dynamic.json`** (dict penuh 55 kunci per
tema) dan **`data/levels/theme_palette.json`** (25 warna per tema untuk rasteriser).

`get_theme(name)` mengembalikan `THEMES.get(name, FOREST_THEME)`; padanannya
`terrain_palette.gd` memakai `palettes.get("forest", ...)` untuk nama tak dikenal.

Catatan shim: `_PLAIN_SYMS['themes']` hanya mengekspos 22 dari 54 nama `*_THEME`
(sisa tema tetap terjangkau lewat `THEMES`, dan itulah yang dipakai runtime). Ini sifat
sumber Pygame, bukan celah Godot; karena itu seluruh 54 tema diklasifikasi lewat `THEMES`.

| Simbol | Jenis | Target |
| --- | --- | --- |
| `ABYSSAL_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ABYSSTIDE_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ABYSS_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ASTRAL_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `CELESTIALPEAKS_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `COSMIC_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `CRIMSONDEVOURER_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `CRIMSONMATRIARCH_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `CRIMSON_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `CROWEYE_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `CRYSTALSTORM_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `DESERT_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `EARTHBORN_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ELDRITCH_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ELEMENTWEAVE_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `EMBERLION_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `EMBERWEAVER_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `EMPYREAN_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ETERNALFLAME_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ETERNALWARLORD_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `EXPLOSIVEART_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `FOREST_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `FROSTVEIL_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `HAUNTED_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `HEARTBANE_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `HEXBOUND_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `HOLLOWBANE_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ICE_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `LUNARHERALD_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `MOONBORN_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `MOONFANG_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `MOONREAPER_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `NETHERVENOM_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `OCEAN_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `OUTLAW_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `PRIMORDIAL_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `RADIANT_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `ROYAL_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SANCTUM_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SANDSHADOW_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SAWMILL_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SHADOWCHAIN_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SKYFURY_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SOLARIS_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SOULFORGED_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SPECTRAL_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SUNDERED_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `SUNFIST_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `TEMPEST_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `THEMES` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `VIOLET_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `VOIDBOUND_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `VOIDWING_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `VOLCANIC_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `WARSHADE_THEME` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `get_theme` | `native` | `godot_rebuild/scripts/ui/terrain_palette.gd`:15 |

## Modul 3 - `generators.py` (geometri + posisi dekorasi)

`PathGenerator.make_curved_path` adalah spline Catmull-Rom (`int()` per titik) dan diport
1:1 di **`scripts/data/lane_layout.gd::curved_path`**, termasuk trik aritmetika skalar
agar presisi `double` Python terjaga sebelum pemotongan.

| Bagian | Hasil | Bukti |
| --- | --- | --- |
| `generate_lanes(1280,720)` | 3 lane: 111/65/101 titik | `lane_layout.gd::create_paths()`, dibandingkan titik per titik |
| `generate_river(1280,720)` | 61 titik | `data/levels/river_path.json` + `terrain_palette.river_path()` |
| `DecorationGenerator.generate_all()` | 14 array | `data/art/map_dynamic.json` layout (5) + bake overlay (9) |

`generate_all()` memanggil `random.seed(42)` di awal sehingga posisi dekorasi
deterministik, lalu `random.seed()` (entropi) di akhir supaya undian gambar berikutnya
tidak berkorelasi. Oracle mengeksekusi generator itu apa adanya dan membandingkan
hasilnya dengan data native — bukan menyalin angka dari dokumentasi.

| Simbol | Jenis | Target |
| --- | --- | --- |
| `DecorationGenerator.__init__` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator._is_dire` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator._is_radiant` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator._is_valid` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator._too_close_to_base` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator._too_close_to_lane` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator._too_close_to_river` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator._too_close_to_shop` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `DecorationGenerator.generate_all` | `executed` | `godot_rebuild/tests/map_components_source_oracle.py`:254 |
| `PathGenerator.generate_lanes` | `native` | `godot_rebuild/scripts/data/lane_layout.gd`:9 |
| `PathGenerator.generate_river` | `native` | `godot_rebuild/scripts/ui/terrain_palette.gd`:5 |
| `PathGenerator.make_curved_path` | `native` | `godot_rebuild/scripts/data/lane_layout.gd`:67 |
| `bake.ancient_ruins` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.boss_landmarks` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.crystals_blue` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.crystals_red` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.dark_bushes` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.dark_trees` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.dead_trees` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.glow_flowers` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.mushrooms_dark` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `bake.spike_traps` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `data.bones` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `data.gravestones` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `data.rocks_mossy` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |
| `data.torch_stones` | `data` | `godot_rebuild/data/art/map_dynamic.json`:1 |

### Array dekorasi: apa yang dibaca runtime

Runtime Pygame membaca enam array dekorasi:` `bones`, `boss_landmarks`, `crystals_blue`, `gravestones`, `rocks_mossy`, `torch_stones`.
Empat di antaranya ada di layout native; dua sisanya hanya dipakai saat melukis dan
karena itu masuk bake:

| Array | Jumlah (seed 42) | Nasib |
| --- | --- | --- |
| `ancient_ruins` | 4 | bake overlay |
| `bones` | 4 | data (`map_dynamic.json` layout) |
| `boss_landmarks` | 30 | bake overlay (dibaca `_draw_true_boss_decorations_filled`) |
| `crystals_blue` | 4 | bake overlay (dibaca `_draw_true_boss_decorations_filled`) |
| `crystals_red` | 2 | bake overlay |
| `dark_bushes` | 3 | bake overlay |
| `dark_trees` | 8 | bake overlay |
| `dead_trees` | 5 | bake overlay |
| `glow_flowers` | 6 | bake overlay |
| `gravestones` | 1 | data (`map_dynamic.json` layout) |
| `mushrooms_dark` | 6 | bake overlay |
| `rocks_mossy` | 8 | data (`map_dynamic.json` layout) |
| `spike_traps` | 2 | bake overlay |
| `torch_stones` | 18 | data (`map_dynamic.json` layout) |

Jadi tidak ada array yang hilang diam-diam: `boss_landmarks` (30 titik) dan
`crystals_blue` (4) tetap dipakai, hanya saja pikselnya masuk `assets/art/map/*.png`.

## Modul 4 - `static_renderer.py` (terrain, sungai, lane, dinding)

Rect/triangle command stream dari renderer statis sudah native:

| Keluaran sumber | Data native | Rasteriser |
| --- | --- | --- |
| `draw_terrain` | `data/levels/terrain_tiles.json` | `scripts/ui/terrain_tiles.gd` |
| `draw_river` | `data/levels/river_tiles.json` | `scripts/ui/river_tiles.gd` |
| `draw_lane` (+ cobblestone, border stone) | `data/levels/lane_tiles.json` | `scripts/ui/lane_tiles.gd` |
| `draw_border_wall` (+ block, spike) | `data/levels/wall_tiles.json` | `scripts/ui/wall_tiles.gd` |
| `draw_terrain_details` | — (piksel saja) | `bake/bake_map_base.py`, seed 100 |

| Simbol | Jenis | Target |
| --- | --- | --- |
| `StaticRenderer._draw_cobblestone_tile` | `native` | `godot_rebuild/scripts/ui/lane_tiles.gd`:6 |
| `StaticRenderer._draw_dark_stone_block` | `native` | `godot_rebuild/scripts/ui/wall_tiles.gd`:5 |
| `StaticRenderer._draw_lane_border_stone` | `native` | `godot_rebuild/scripts/ui/lane_tiles.gd`:6 |
| `StaticRenderer._draw_wall_spike` | `native` | `godot_rebuild/scripts/ui/wall_tiles.gd`:5 |
| `StaticRenderer.draw_border_wall` | `native` | `godot_rebuild/scripts/ui/wall_tiles.gd`:5 |
| `StaticRenderer.draw_lane` | `native` | `godot_rebuild/scripts/ui/lane_tiles.gd`:6 |
| `StaticRenderer.draw_river` | `native` | `godot_rebuild/scripts/ui/river_tiles.gd`:5 |
| `StaticRenderer.draw_terrain` | `native` | `godot_rebuild/scripts/ui/terrain_tiles.gd`:5 |
| `StaticRenderer.draw_terrain_details` | `bake` | `godot_rebuild/bake/bake_map_base.py`:40 |

## Modul 5 - `dynamic_renderer.py` (lapisan hidup)

Tema, kualitas, partikel, kabut, animasi sungai, glow/smoke toko, obor, dan efek bos.
Port native-nya: `scripts/ui/dynamic_map_renderer.gd` (state + replay),
`dynamic_map_layout.gd` (op list), `dynamic_map_painter.gd` (CanvasItem).

| Simbol | Jenis | Target |
| --- | --- | --- |
| `DynamicRenderer.__init__` | `native` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:60 |
| `DynamicRenderer._cached_surf` | `internal` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:7 |
| `DynamicRenderer._draw_flame_a` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:243 |
| `DynamicRenderer._draw_flame_b` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:254 |
| `DynamicRenderer._draw_flame_c` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:263 |
| `DynamicRenderer._draw_fog` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:25 |
| `DynamicRenderer._draw_particles` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:96 |
| `DynamicRenderer._draw_river_animation` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:40 |
| `DynamicRenderer._draw_shop_glow` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:58 |
| `DynamicRenderer._draw_shop_smoke` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:76 |
| `DynamicRenderer._draw_torches` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:141 |
| `DynamicRenderer._init_fog` | `native` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:88 |
| `DynamicRenderer._init_particles` | `native` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:88 |
| `DynamicRenderer.draw` | `native` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:120 |
| `DynamicRenderer.update` | `native` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:129 |

### Tambalan bos (fungsi top-level yang mem-monkeypatch DynamicRenderer)

Delapan fungsi top-level menambal `DynamicRenderer` saat modul dimuat; semuanya ikut
terklasifikasi. Identitas bos sumber: abaddon, alchemist, ignis_drachorn, krobellus,
dengan override tema “Haunted Veil” menjadi krobellus — keduanya ada di
`dynamic_map_layout.gd::_boss_ops`.

| Simbol | Jenis | Target |
| --- | --- | --- |
| `_boss_draw_particles` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:96 |
| `_boss_dynamic_draw` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:271 |
| `_boss_init_particles` | `native` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:173 |
| `_boss_update` | `native` | `godot_rebuild/scripts/ui/dynamic_map_renderer.gd`:129 |
| `_draw_boss_environment` | `native` | `godot_rebuild/scripts/ui/dynamic_map_layout.gd`:271 |
| `_draw_true_boss_decorations` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `_draw_true_boss_decorations_filled` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |

## Modul 6 - `decoration_renderer.py` (23 metode dekorasi)

Pohon, batu nisan, tulang, reruntuhan, kristal, jamur, glow flower, kaktus, palm,
dune, es, salju, dan dressing bos. Semuanya murni piksel statis, jadi jalurnya bake:
`bake/bake_map_overlay.py` memanggil `DecorationRenderer.draw_all(full, mr)` dan menulis
`data/art/map_overlay.json` (54 tema, sha256 + jumlah piksel tertutup) dengan
`random.seed(f"{tema}:decorations")` supaya hasilnya stabil, lalu menyimpan hanya piksel
yang berbeda dari base (layer 1-3). Bake itu meng-assert dirinya sendiri:
`composite == full` per tema.

| Simbol | Jenis | Target |
| --- | --- | --- |
| `DecorationRenderer._draw_ancient_ruins` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_bones` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_cactus` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_crystals_amber` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_crystals_blue` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_crystals_red` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_dark_bushes` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_dark_oak` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_dark_pine` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_dark_trees` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_dead_trees` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_frozen_trees` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_glow_flowers` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_gravestones` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_ice_crystals` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_mushrooms` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_palm_trees` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_rocks` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_sand_dunes` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_snow_drifts` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_spike_traps` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer._draw_twisted_tree` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |
| `DecorationRenderer.draw_all` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:40 |

## Modul 7 - `shop_renderer.py` (bangunan toko)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `ShopRenderer._draw_building` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:42 |
| `ShopRenderer._draw_pixel_text` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:42 |
| `ShopRenderer.draw` | `bake` | `godot_rebuild/bake/bake_map_overlay.py`:42 |

Toko dilukis ke overlay yang sama (layer 5); Godot menambahkan glow/smoke-nya sendiri
lewat `dynamic_map_layout.gd::_shop_glow_ops` / `_shop_smoke_ops`, jadi bagian hidupnya
bukan bagian dari bake.

## Modul 0 - `__init__.py` (shim `sys.modules`)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `aliases` | `meta` | `map_components/__init__.py`:31 |
| `reexports` | `meta` | `map_components/__init__.py`:35 |

Shim mendaftarkan tujuh nama modul lama; `generators`, `static_renderer`, `shop_renderer`
dibungkus namespace (`_NS_generators`, `_NS_static_renderer`, `_NS_shop_renderer`) karena
namanya bentrok, empat lainnya datar. Tabel
`_EXTRA`/`_PLAIN_SYMS` adalah daftar simbol persis per modul lama — dipakai oracle
sebagai bukti “tidak lebih, tidak kurang”. Tidak ada padanan yang diperlukan di Godot:
GDScript memakai `preload`, bukan impor dinamis.

## Determinisme dan deviasi

Empat pemanggilan `random.seed` di folder ini:

| Baris | Argumen | Arti |
| --- | --- | --- |
| 4747 | `42` | seed tetap |
| 4889 | _(kosong)_ | reseed entropi |
| 5062 | `100` | seed tetap |
| 5074 | _(kosong)_ | reseed entropi |

- **DEVIASI (disengaja, sudah lama):** detail halus gambar statis bergantung RNG pygame
  setelah `random.seed()`; bake memilih satu hasil (seed per tema) sehingga satu
  screenshot Godot tidak akan identik piksel dengan satu run Pygame acak. Posisi
  dekorasi deterministik (seed 42) dan itu yang diuji.
- **DEVIASI:** `_cached_surf` (LRU 400 surface) tidak diport; Godot membangun ulang op
  list per frame. Cache murni memo, hasil gambar sama.
- **DEVIASI:** `TILE_SIZE` disimpan sebagai data (`map_palette.json`) dan hanya dipakai
  rasteriser yang memang perlu grid 16 px; tidak ada konstanta global di GDScript.
- **BELUM:** parity piksel per-piksel terhadap satu run Pygame ber-RNG bebas tidak bisa
  diuji di sandbox tanpa pygame+GPU; yang diuji adalah data, geometri, dan bake
  (sha256 + `composite == full` di skrip bake).

## Bukti uji

| Lapisan | Berkas | Isi |
| --- | --- | --- |
| Oracle | `godot_rebuild/tests/map_components_source_oracle.py` | impor bundle dengan stub `pygame`, eksekusi generator, 194 entri klasifikasi, tulis `map_palette.json` |
| Fixture | `godot_rebuild/tests/fixtures/map_components_source.json` | inventaris, modul, palet, tema, geometri, seed, alias, klasifikasi |
| Suite native | `godot_rebuild/tests/map_components_checks.gd` | 54 tema, lane titik-per-titik, 61 titik sungai, layout seed 42, target+token tiap entri |
| Validator | blok `9cb` di `godot_rebuild/tests/validate_project.py` | drift oracle vs fixture vs `map_palette.json`, histogram jenis, larangan literal warna |

Suite pendukung yang sudah ada dan tetap berlaku: `map_art_checks.gd`,
`map_renderer_checks.gd`, `dynamic_map_renderer_checks.gd`, `level_theme_checks.gd`,
`terrain_tiles_checks.gd`, `lane_tiles_checks.gd`, `river_tiles_checks.gd`,
`wall_tiles_checks.gd`, `map_tint_draw_checks.gd`.

