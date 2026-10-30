# Migrasi Folder `towers/` ke Godot (layer 9cd)

Dokumen ini mencatat pemetaan **seluruh** isi folder Pygame `towers/` ke Godot.
Oracle sumber: `godot_rebuild/tests/towers_source_oracle.py`; fixture: 
`godot_rebuild/tests/fixtures/towers_source.json`; data runtime: 
`godot_rebuild/data/towers/render_catalog.json`; modul native: 
`godot_rebuild/scripts/ui/tower_render_catalog.gd`; suite: 
`godot_rebuild/tests/towers_checks.gd`.

Kontrak repo tetap: Pygame adalah oracle baca-saja. Kalau Godot berbeda, yang 
diperbaiki adalah `godot_rebuild/`, bukan Pygame.

## 1. Skala folder

| Berkas | Baris | Peran |
| --- | ---: | --- |
| `__init__.py` | 94 | shim `sys.modules` + dispatcher |
| `_bundle.py` | 7274 | bundle: base_renderer + 4 renderer tower |
| **total** | **7368** | 2 berkas |

## 2. Pembagian modul di dalam bundle

| Modul | Baris awal | Baris akhir | Jumlah baris | Metode namespace |
| --- | ---: | ---: | ---: | ---: |
| `base_renderer.py` | 30 | 408 | 379 | 10 fungsi bebas |
| `archer_tower.py` | 409 | 2194 | 1786 | 37 |
| `cannon_tower.py` | 2195 | 3965 | 1771 | 27 |
| `ice_tower.py` | 3966 | 5674 | 1709 | 34 |
| `mage_tower.py` | 5675 | 7274 | 1600 | 31 |

Header bundle (docstring + import) = **29 baris**. 
Total metode namespace = **129** 
(archer 37, cannon 27, ice 34, mage 31).

## 3. Konstanta `base_renderer`

| Konstanta | Nilai | Dipakai oleh |
| --- | --- | --- |
| `FIRE_ORANGE` | `(255, 150, 40)` | palet `fire_*` (bake) |
| `FIRE_PINK` | `(255, 100, 200)` | palet `fire_*` (bake) |
| `FIRE_PURPLE` | `(200, 40, 100)` | palet `fire_*` (bake) |
| `FIRE_YELLOW` | `(255, 220, 100)` | palet `fire_*` (bake) |
| `OUTLINE` | `(30, 25, 35)` | outline semua renderer (bake) |

## 4. Apa yang di-bake dan apa yang native

Atlas struktur (layer 9bl, `godot_rebuild/bake/bake_structure_atlas.py`) sudah 
memanggil kode sumber asli `Tower._draw_tower_body`, jadi **seluruh piksel badan 
tower** berasal dari sumber: 42 sheet, tiap sheet 8 frame (2 arah hadap x 4 
langkah kilat tembak), plus `tower_top_y` per level. Yang belum diport adalah 
bagian yang **berjalan saat pertandingan** dan tidak berupa piksel badan tower:

| Perilaku live | Sumber | Godot |
| --- | --- | --- |
| Titik spawn panah | `get_archer_bow_position` | `tower_render_catalog.gd::archer_position` |
| Titik spawn peluru meriam | `get_cannon_muzzle_position` (dengan `recoil`) | `tower_render_catalog.gd::cannon_position` |
| Titik spawn kristal es | `get_ice_crystal_position` | `tower_render_catalog.gd::ice_position` |
| Titik spawn kristal sihir | `get_mage_crystal_position` | `tower_render_catalog.gd::mage_position` |
| Posisi HP bar di atas tower | `get_archer_top_y`, `get_cannon_top_y`, `get_ice_top_y`, `get_mage_top_y` | `tower_render_catalog.gd::top_y` |
| Tabel warna per tim | `_get_palette(team)` tiap namespace | `data/towers/render_catalog.json` -> `palettes` |
| Konfigurasi level | `LEVEL_CONFIGS[1..6]` tiap namespace | `data/towers/render_catalog.json` -> `level_configs` |
| Dispatch tipe | `TOWER_RENDERERS` + `render_tower` | `tower_render_catalog.gd::TYPES` + `has_type` |

Geometri sumber selalu memakai kanvas **140 x 165** dengan skala **0.7**, tanah di 
`cy = 153`, dan offset akhir `-int(165 * 0.7) + int(30 * 0.7)` = **-94**. Semua 
nilai di-truncate dengan `int()` oleh sumber, sehingga hasil Godot juga integer.

## 5. Klasifikasi seluruh simbol

Jumlah simbol: **163**. Histogram kind: `{'bake': 125, 'data': 13, 'dead': 14, 'meta': 1, 'native': 10}`.

| Simbol | Kind | Target bukti | Token | Catatan |
| --- | --- | --- | --- | --- |
| `archer:HAS_AACIRCLE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `pygame.Surface((800, 600)` | anti-aliasing switch the baked renderer reads |
| `archer:LEVEL_CONFIGS` | data | `godot_rebuild/data/towers/render_catalog.json` | `"level_configs"` | tower_h / *_tier inputs of the live anchor geometry |
| `archer:_BASE_CACHE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `_TOWER_SPRITE_CACHE.clear()` | per-(face, shoot flash) frame memo cleared before every bake |
| `archer:_aacircle` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_aapoly` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_clamp_color` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_annex` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_archer` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_archer_full` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_arrow_bucket_ground` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_barrel` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_battlements` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_bow` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_cape` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_center_roof` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_chunky_brick` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_flags` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_flame_head` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_ground_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_helmet_golden` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_helmet_iron` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_hood` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_magic_aura` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_magic_head` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_main_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_merlon` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_platform` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_quiver` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_scroll` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_shadow` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_shield` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_single_flag` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_draw_torch` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_get_palette` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | colour table the bake reads; native copy keeps it inspectable |
| `archer:_render_archer` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_render_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:_render_effects` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `archer:draw_archer` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower_type, team, level)` | body pixels baked per (type, team, level, facing, shoot step) |
| `archer:get_archer_bow_position` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func archer_position(` | bullet spawn point; face/recoil/level clamp are behavioural |
| `archer:get_archer_top_y` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func top_y(` | HP bar anchor; also pinned by the baked `tower_top_y` manifest |
| `base:FIRE_ORANGE` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | fire/outline colours used by the palettes of both teams |
| `base:FIRE_PINK` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | fire/outline colours used by the palettes of both teams |
| `base:FIRE_PURPLE` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | fire/outline colours used by the palettes of both teams |
| `base:FIRE_YELLOW` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | fire/outline colours used by the palettes of both teams |
| `base:OUTLINE` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | fire/outline colours used by the palettes of both teams |
| `base:draw_aura` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | no renderer calls it; the aura is per-namespace `_draw_magic_aura` |
| `base:draw_ground_shadow` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | each namespace has a private `_draw_shadow`/`_draw_ground_base` |
| `base:draw_metal_plate` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | no renderer calls it |
| `base:draw_muzzle_flash` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | the live flash is `_entity.Tower.draw` + `tower_fx_layout.gd` |
| `base:draw_rivet` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | only called by the dead `draw_metal_plate` |
| `base:draw_shield_emblem` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | each namespace has a private `_draw_shield` instead |
| `base:draw_sparks` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | no renderer calls it |
| `base:draw_stone_block_pattern` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | each namespace bakes its own brick pass |
| `base:draw_torch` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | each namespace has a private `_draw_torch` that it actually calls |
| `base:get_team_palette` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | every namespace ships its own `_get_palette`; nothing calls this one |
| `cannon:HAS_AACIRCLE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `pygame.Surface((800, 600)` | anti-aliasing switch the baked renderer reads |
| `cannon:LEVEL_CONFIGS` | data | `godot_rebuild/data/towers/render_catalog.json` | `"level_configs"` | tower_h / *_tier inputs of the live anchor geometry |
| `cannon:_BASE_CACHE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `_TOWER_SPRITE_CACHE.clear()` | per-(face, shoot flash) frame memo cleared before every bake |
| `cannon:_aacircle` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_aapoly` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_clamp_color` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_ammo_storage` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_annex` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_arched_door` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_battlements` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_cannon` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | unreachable from draw_cannon/get_cannon_muzzle_position/get_cannon_top_y |
| `cannon:_draw_cannon_full` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_cannon_platform` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_cannon_v2` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_cannonball_crate` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_chunky_brick` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_ground_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_main_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_merlon` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_shadow` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_shield` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_small_cannonball_crate` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_draw_torch` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_get_palette` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | colour table the bake reads; native copy keeps it inspectable |
| `cannon:_render_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_render_cannon` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:_render_effects` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `cannon:draw_cannon` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower_type, team, level)` | body pixels baked per (type, team, level, facing, shoot step) |
| `cannon:get_cannon_muzzle_position` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func cannon_position(` | bullet spawn point; face/recoil/level clamp are behavioural |
| `cannon:get_cannon_top_y` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func top_y(` | HP bar anchor; also pinned by the baked `tower_top_y` manifest |
| `ice:HAS_AACIRCLE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `pygame.Surface((800, 600)` | anti-aliasing switch the baked renderer reads |
| `ice:LEVEL_CONFIGS` | data | `godot_rebuild/data/towers/render_catalog.json` | `"level_configs"` | tower_h / *_tier inputs of the live anchor geometry |
| `ice:_BASE_CACHE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `_TOWER_SPRITE_CACHE.clear()` | per-(face, shoot flash) frame memo cleared before every bake |
| `ice:_aacircle` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_aapoly` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_clamp_color` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_battlements` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_chunky_brick` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_cluster_tier1` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_cluster_tier2` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_cluster_tier3` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_cluster_tier4` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_corner_spikes` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_crystal_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_crystal_group` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | unreachable from draw_ice/get_ice_crystal_position/get_ice_top_y |
| `ice:_draw_crystal_spike` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_crystal_spike_detailed` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | unreachable from draw_ice/get_ice_crystal_position/get_ice_top_y |
| `ice:_draw_crystal_torch` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_floating_shards` | dead | `godot_rebuild/tests/towers_source_oracle.py` | `def dead_helpers(` | unreachable from draw_ice/get_ice_crystal_position/get_ice_top_y |
| `ice:_draw_glowing_door` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_ground_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_ground_crystals` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_ice_full` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_main_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_merlon` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_mini_crystal` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_shadow` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_shield` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_simple_crystal` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_draw_single_crystal` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_get_palette` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | colour table the bake reads; native copy keeps it inspectable |
| `ice:_render_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_render_crystal_cluster` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:_render_effects` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `ice:draw_ice` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower_type, team, level)` | body pixels baked per (type, team, level, facing, shoot step) |
| `ice:get_ice_crystal_position` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func ice_position(` | bullet spawn point; face/recoil/level clamp are behavioural |
| `ice:get_ice_top_y` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func top_y(` | HP bar anchor; also pinned by the baked `tower_top_y` manifest |
| `mage:HAS_AACIRCLE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `pygame.Surface((800, 600)` | anti-aliasing switch the baked renderer reads |
| `mage:LEVEL_CONFIGS` | data | `godot_rebuild/data/towers/render_catalog.json` | `"level_configs"` | tower_h / *_tier inputs of the live anchor geometry |
| `mage:_BASE_CACHE` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `_TOWER_SPRITE_CACHE.clear()` | per-(face, shoot flash) frame memo cleared before every bake |
| `mage:_aacircle` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_aapoly` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_clamp_color` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_alchemy_table` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_cauldron` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_chunky_brick` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_crystal_legendary` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_crystal_medium` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_crystal_small` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_crystal_twin` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_faceted_crystal` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_glowing_door` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_ground_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_ground_crystal` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_ground_crystals` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_horn_holder` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_mage_full` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_magic_torch` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_main_roof` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_main_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_purple_window` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_shadow` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_shield` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_draw_side_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_get_palette` | data | `godot_rebuild/data/towers/render_catalog.json` | `"palettes"` | colour table the bake reads; native copy keeps it inspectable |
| `mage:_render_base` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_render_effects` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:_render_top_crystal` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower._draw_tower_body(` | private draw helper; pixels land in the baked sheet |
| `mage:draw_mage` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `tower_type, team, level)` | body pixels baked per (type, team, level, facing, shoot step) |
| `mage:get_mage_crystal_position` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func mage_position(` | bullet spawn point; face/recoil/level clamp are behavioural |
| `mage:get_mage_top_y` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func top_y(` | HP bar anchor; also pinned by the baked `tower_top_y` manifest |
| `module:archer_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `TOWER_TYPES = (` | namespace body is driven by the real Tower._draw_tower_body |
| `module:cannon_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `TOWER_TYPES = (` | namespace body is driven by the real Tower._draw_tower_body |
| `module:ice_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `TOWER_TYPES = (` | namespace body is driven by the real Tower._draw_tower_body |
| `module:mage_tower` | bake | `godot_rebuild/bake/bake_structure_atlas.py` | `TOWER_TYPES = (` | namespace body is driven by the real Tower._draw_tower_body |
| `shim:TOWER_RENDERERS` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `const TYPES :=` | registry of the four draw functions |
| `shim:_install_aliases` | meta | `towers/__init__.py` | `_install_aliases` | sys.modules plumbing |
| `shim:render_tower` | native | `godot_rebuild/scripts/ui/tower_render_catalog.gd` | `static func has_type(` | dispatcher replaced by type lookup |

## 6. `LEVEL_CONFIGS` per level

| Tipe | L1 | L2 | L3 | L4 | L5 | L6 |
| --- | --- | --- | --- | --- | --- | --- |
| `archer` | 38 / basic | 42 / ranger | 46 / marksman | 52 / elite | 56 / elite_twin | 62 / legendary |
| `cannon` | 38 / basic | 42 / basic | 46 / bronze | 52 / iron | 56 / twin | 62 / legendary |
| `ice` | 40 / small | 44 / small | 48 / medium | 54 / medium | 58 / twin | 64 / legendary |
| `mage` | 45 / small | 48 / small | 52 / medium | 56 / medium | 60 / twin | 66 / legendary |

`tower_h` adalah satu-satunya masukan geometri level; `*_tier` memilih panjang 
laras, tinggi laras, dan tinggi kristal.

## 7. Palette per tim

| Tipe | Kunci biru | Kunci merah | Contoh biru | Contoh merah |
| --- | ---: | ---: | --- | --- |
| `archer` | 44 | 44 | `fire_dark` = `(180, 45, 15)` | `fire_dark` = `(140, 20, 90)` |
| `cannon` | 51 | 51 | `ball_dark` = `(25, 28, 35)` | `ball_dark` = `(30, 15, 18)` |
| `ice` | 39 | 39 | `crystal_dark` = `(55, 130, 220)` | `crystal_dark` = `(170, 40, 100)` |
| `mage` | 47 | 47 | `flag_dark` = `(100, 40, 145)` | `flag_dark` = `(135, 30, 45)` |

Semantik sumber `if team == "blue" ... else ...` berarti **nama tim apa pun 
selain `blue`** memakai tabel merah; `tower_render_catalog.gd::palette` 
mempertahankan perilaku itu dan diuji dengan `"green"`.

## 8. Hasil replay geometri yang dipin

Oracle menjalankan helper sumber asli untuk **192 titik spawn** 
(4 tipe x level 0-7 x 2 arah hadap x 2 origin x recoil meriam 0/3/7) dan 
**64 anchor HP bar** (4 tipe x level 0-7 x 2 origin).

| Kasus | Input | Keluaran sumber |
| --- | --- | --- |
| spawn | `archer` L1, face +1, recoil 0 | `(404, 278)` |
| spawn | `archer` L3, face +1, recoil 0 | `(404, 273)` |
| spawn | `archer` L6, face +1, recoil 0 | `(404, 262)` |
| spawn | `cannon` L1, face +1, recoil 0 | `(411, 276)` |
| spawn | `cannon` L1, face +1, recoil 7 | `(418, 276)` |
| spawn | `cannon` L3, face +1, recoil 0 | `(412, 271)` |
| spawn | `cannon` L3, face +1, recoil 7 | `(419, 271)` |
| spawn | `cannon` L6, face +1, recoil 0 | `(415, 259)` |
| spawn | `cannon` L6, face +1, recoil 7 | `(422, 259)` |
| top_y | `archer` L1 y=300 | `271` |
| top_y | `archer` L6 y=300 | `249` |
| top_y | `cannon` L1 y=300 | `271` |
| top_y | `cannon` L6 y=300 | `249` |
| top_y | `ice` L1 y=300 | `266` |
| top_y | `ice` L6 y=300 | `238` |
| top_y | `mage` L1 y=300 | `259` |
| top_y | `mage` L6 y=300 | `236` |

Catatan perilaku yang perlu diketahui: parameter `recoil` pada 
`get_cannon_muzzle_position` **mendorong** titik moncong ke depan 
(`0 -> 415`, `3 -> 418`, `7 -> 422` pada level 6), bukan menariknya ke belakang. 
Godot meniru angka sumber apa adanya, dan pemanggilan saat menembak memakai 
`recoil = 0` sehingga cabang ini tidak aktif di pertandingan.

## 9. Simbol yang tidak pernah dieksekusi (dead)

| Simbol | Bukti | Alasan |
| --- | --- | --- |
| `draw_aura` | inside 0 / outside 0 | no renderer calls it; the aura is per-namespace `_draw_magic_aura` |
| `draw_ground_shadow` | inside 0 / outside 0 | each namespace has a private `_draw_shadow`/`_draw_ground_base` |
| `draw_metal_plate` | inside 0 / outside 0 | no renderer calls it |
| `draw_muzzle_flash` | inside 0 / outside 0 | the live flash is `_entity.Tower.draw` + `tower_fx_layout.gd` |
| `draw_rivet` | inside 1 / outside 0 | only called by the dead `draw_metal_plate` |
| `draw_shield_emblem` | inside 0 / outside 0 | each namespace has a private `_draw_shield` instead |
| `draw_sparks` | inside 0 / outside 0 | no renderer calls it |
| `draw_stone_block_pattern` | inside 0 / outside 0 | each namespace bakes its own brick pass |
| `draw_torch` | inside 0 / outside 0 | each namespace has a private `_draw_torch` that it actually calls |
| `get_team_palette` | inside 0 / outside 0 | every namespace ships its own `_get_palette`; nothing calls this one |
| `_draw_cannon` | inside 0 / outside 0 | unreachable from draw_cannon/get_cannon_muzzle_position/get_cannon_top_y |
| `_draw_crystal_group` | inside 0 / outside 0 | unreachable from draw_ice/get_ice_crystal_position/get_ice_top_y |
| `_draw_crystal_spike_detailed` | inside 0 / outside 0 | unreachable from draw_ice/get_ice_crystal_position/get_ice_top_y |
| `_draw_floating_shards` | inside 0 / outside 0 | unreachable from draw_ice/get_ice_crystal_position/get_ice_top_y |

Sepuluh helper `base_renderer` mati karena setiap namespace punya versi 
privatnya sendiri (`_draw_torch`, `_draw_shield`, `_draw_shadow`, 
`_get_palette`, ...) yang benar-benar dipanggil; `draw_rivet` hanya dipanggil 
`draw_metal_plate` yang juga mati. `_draw_cannon` digantikan 
`_draw_cannon_v2`, dan trio kristal es digantikan `_draw_cluster_tier*`.

## 10. Dispatch dan titik masuk runtime

| Fakta | Nilai |
| --- | --- |
| Urutan `TOWER_RENDERERS` | `['archer', 'cannon', 'ice', 'mage']` |
| Peringatan tipe asing | `True` |
| Panggilan langsung `renderer(surface, tower, x, y, size)` | `True` |
| Renderer yang memakai sprite cache | 4 dari 4 |

| Simbol | Modul impor | Titik impor | Titik panggil |
| --- | --- | --- | --- |
| `TOWER_RENDERERS` | `towers` | `tools/convert_to_godot.py:2433` | — |
| `get_archer_bow_position` | `towers.archer_tower` | `_entity.py:1144` | `_entity.py:1149`, `_entity.py:901`, `_entity.py:949` |
| `get_archer_top_y` | `towers.archer_tower` | `_entity.py:1182` | — |
| `get_cannon_muzzle_position` | `towers.cannon_tower` | `_entity.py:967` | `_entity.py:969` |
| `get_cannon_top_y` | `towers.cannon_tower` | `_entity.py:1185` | — |
| `get_ice_crystal_position` | `towers.ice_tower` | `_entity.py:993` | `_entity.py:995` |
| `get_ice_top_y` | `towers.ice_tower` | `_entity.py:1188` | — |
| `get_mage_crystal_position` | `towers.mage_tower` | `_entity.py:1016` | `_entity.py:1022` |
| `get_mage_top_y` | `towers.mage_tower` | `_entity.py:1191` | — |
| `render_tower` | `towers` | `_entity.py:1346`, `tools/convert_to_godot.py:2341` | `_entity.py:1357`, `_entity.py:1376`, `tools/convert_to_godot.py:2357` |

`get_*_top_y` diimpor lalu disimpan sebagai `self._top_fn` (bukan dipanggil 
langsung), jadi kolom panggil kosong adalah perilaku sumber, bukan kekurangan.

## 11. Silang-cek dengan kode Godot yang sudah berjalan

| Berkas | Hubungan dengan sumber |
| --- | --- |
| `godot_rebuild/scripts/combat/siege_battle.gd::CANNON_MUZZLE` | `[tower_h, int(barrel_len * 0.85)]` per level |
| `godot_rebuild/scripts/combat/siege_battle.gd::ICE_CRYSTAL` | `tower_h` tipe ice per level |
| `godot_rebuild/scripts/combat/siege_battle.gd::MAGE_CRYSTAL` | `tower_h` tipe mage per level |
| `godot_rebuild/scripts/ui/tower_fx_layout.gd::BOW_HEIGHTS` | `tower_h` tipe archer per level |
| `godot_rebuild/data/structures/archer_level_*.tres::bow_platform_height` | `tower_h` tipe archer per level |
| `godot_rebuild/scripts/ui/structure_art.gd::tower_top_y` | `get_*_top_y(0, 0, level)` dari manifest |

Suite `towers_checks.gd` membandingkan keenamnya dengan katalog, jadi kalau salah 
satu bergeser, tes gagal sebelum sampai ke layar.

## 12. Deviasi dan yang BELUM

| Butir | Status |
| --- | --- |
| Badan tower (piksel) | Bake dari kode sumber (9bl); tidak digambar ulang native |
| Geometri spawn + HP bar | Native, diuji terhadap semua kasus yang dipin |
| `recoil` bukan 0 | Diport apa adanya, tetapi tidak pernah dipakai saat menembak |
| `ice`/`mage` punya parameter `face` | Sumber mengabaikannya; Godot tidak memintanya |
| Tipe tower asing | Sumber `print` peringatan; Godot memakai `has_type` dan melewati render |
| Slow/aura/muzzle flash | Berada di `_entity.py`, bukan `towers/`; sudah diport layer 9bv14 |
| Parity piksel/GPU | Belum diuji di perangkat |
| Suite native Godot | Dijalankan di PC pengguna; sandbox ini tidak punya biner Godot |

## 13. Cara verifikasi

```
python3 godot_rebuild/tests/towers_source_oracle.py          # cek fixtur tidak drift
python3 godot_rebuild/tests/towers_source_oracle.py --write  # regenerasi fixture + data
python3 godot_rebuild/tests/validate_project.py              # guardrail statis
```

Di Godot: jalankan `res://tests/run_all.gd`; suite `TowersChecks` memverifikasi 
163 simbol, 192 titik spawn, 64 anchor HP bar, empat palette, empat 
`LEVEL_CONFIGS`, 14 simbol mati, dan silang-cek konstanta `siege_battle.gd`.
