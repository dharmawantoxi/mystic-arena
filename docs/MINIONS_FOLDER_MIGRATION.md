# Migrasi folder `minions/` ke Godot

Dokumen ini menutup sub-task **“lihat folder minions dan migrasikan semua kegodot”**:
dua berkas Python (9.626 baris) berisi lima renderer tubuh minion, helper `base_renderer`,
dan shim `sys.modules`.

## Ringkasan

| Ukuran | Nilai |
| --- | --- |
| Berkas sumber | 2 (`_bundle.py` 9.531 baris + `__init__.py` 95 baris) |
| Modul gabungan | 6 (base_renderer, goblin, orc, troll, undead, dark_rider) |
| Namespace renderer | 5, total 178 metode (37/33/36/38/34) |
| Helper bersama | 8 fungsi + 7 konstanta |
| Simbol terklasifikasi | 201 |
| Sebaran jenis | bake 184, dead 3, delegated 1, meta 1, native 12 |
| Atlas tubuh | 50 sheet = 5 tipe x 2 tim x 5 level (sudah ada, layer 9bk) |

## Kosakata klasifikasi

| Jenis | Arti | Bukti yang diminta |
| --- | --- | --- |
| `native` | perilaku diport ke skrip Godot | berkas + token + nomor baris |
| `bake` | piksel direproduksi atlas hasil bake | skrip bake + titik masuknya |
| `delegated` | helper mati di sumber, tetapi kontrak bake menyerahkannya ke Godot | berkas + token |
| `dead` | didefinisikan tetapi tidak pernah dipanggil runtime | bukti call-site kosong di oracle |
| `meta` | plambing impor Python | `minions/__init__.py` |

## Inventaris dan rentang modul

| Berkas | Baris |
| --- | --- |
| `__init__.py` | 95 |
| `_bundle.py` | 9531 |

| Modul | Baris awal | Baris akhir | Baris | Metode |
| --- | --- | --- | --- | --- |
| `base_renderer.py` | 34 | 335 | 302 | - |
| `goblin.py` | 336 | 2232 | 1897 | 37 |
| `orc.py` | 2233 | 4030 | 1798 | 33 |
| `troll.py` | 4031 | 5935 | 1905 | 36 |
| `undead.py` | 5936 | 7785 | 1850 | 38 |
| `dark_rider.py` | 7786 | 9531 | 1746 | 34 |

Jumlah rentang = 9.498 baris; 33 baris pertama adalah header `_bundle.py`, jadi 33 + 9.498 = 9.531.

## `base_renderer.py` - helper bersama dan overlay hidup

Delapan helper top-level, tujuh konstanta, dan tiga helper yang **mati** di runtime.

| Simbol | Jenis | Target | Catatan |
| --- | --- | --- | --- |
| `MINION_CACHE_ENABLED` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:77 |  |
| `OUTLINE` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:31 |  |
| `SHADOW` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:32 |  |
| `_CANVAS_H` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:34 |  |
| `_CANVAS_W` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:34 |  |
| `_RENDERING_TO_CACHE` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:62 |  |
| `_SHADOW_CACHE` | `dead` | `godot_rebuild/tests/minions_source_oracle.py`:271 | memo for draw_shadow, which nothing calls |
| `_minion_cache_key` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:177 | ten-part key; pose part matches minion_anim.pose_key |
| `apply_hurt_flash` | `delegated` | `godot_rebuild/scripts/ui/minion_overlay.gd`:165 | no runtime caller, but the atlas bake delegates the +90 flash to Godot |
| `cached_minion_draw` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:3 | body render + red-team recolour + crop; overlays are split out natively |
| `calculate_animation_offsets` | `dead` | `godot_rebuild/tests/minions_source_oracle.py`:271 | returned bob/sway but no renderer calls it; baked frames carry the bob |
| `draw_hp_bar` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:90 | drawn live after the sprite blit; exact rects and colours |
| `draw_shadow` | `dead` | `godot_rebuild/tests/minions_source_oracle.py`:271 | each namespace has its own _draw_ground_shadow; this one is never called |
| `draw_slash_effects` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:131 | arbitrary angles, not only the 32 baked steps |
| `draw_slow_effect` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:114 | circle + three orbiting sparks; source freezes one frame |

### Helper yang tidak pernah dipanggil

| Helper | Bukti | Keputusan |
| --- | --- | --- |
| `draw_shadow` | 0 call-site di dalam maupun luar `minions/` | tidak diport; tiap namespace punya `_draw_ground_shadow` sendiri yang sudah ikut bake |
| `_SHADOW_CACHE` | memo untuk `draw_shadow` | tidak diport |
| `calculate_animation_offsets` | 0 call-site | tidak diport; bob/sway sudah ada di frame atlas hasil bake |
| `apply_hurt_flash` | 0 call-site | **diport** (`hurt_color`) karena docstring `bake_minion_atlas.py` menyerahkan kilatan +90 ke sisi Godot |

## Overlay hidup: primitif yang dipin

Oracle mengimpor `_bundle.py` dengan stub pygame yang **merekam** primitif
(`Surface.blit`, `draw.rect/circle/ellipse/lines`), jadi `hp_bar`, `slow_aura`, dan
`slash_ops` di Godot dibandingkan dengan permintaan gambar aslinya, bukan hasil ketik ulang.
Titik disimpan dalam mikropiksel (`round(x * 10_000)` dipotong) agar tidak bergantung
pada format float. Kanvas sprite tetap `120 x 120`.

| Replay | Jumlah kasus | Hasil |
| --- | --- | --- |
| `hp_bar` | 8 | 1 latar + 1 fill + 1 border; fill hanya jika `int(w * rasio) > 0` |
| `slow_aura` | 4 | 1 lingkaran `radius + 2` + 3 kotak 2x2 pada `timer * 0.1 + i * 2.1` |
| `slash` | 7 | 2 garis (putih 3 px, krem 1 px) x 7 titik; alpha 220 x (1 - progress) |
| `hurt_flash` | 4 | `+90` per kanal, di-clamp 255 |
| `cache_key` | 5 | tuple 10 bagian (pose, arah, hurt, bleed, charge, regen, slow) |
| `shadow` | 3 | hanya bukti; helper-nya mati |
| cache guard | 1 | HP bar dan slash kosong saat `_RENDERING_TO_CACHE` | 

### Warna dan ambang HP bar

| Bagian | Nilai |
| --- | --- |
| Tim biru: latar / border | `(12, 22, 44)` / `(90, 165, 255)` |
| Tim merah: latar / border | `(44, 12, 10)` / `(255, 95, 85)` |
| Fill `> 0.6` | `(70, 200, 80)` |
| Fill `> 0.3` | `(225, 190, 60)` |
| Fill sisanya | `(215, 60, 55)` |
| Tinggi bar | 4 px |

### Offset bar per renderer

| Modul | Lebar (`radius * 2 + ?`) | Y (`y - radius - ?`) |
| --- | --- | --- |
| `base_renderer.py` | +6 | 18 |
| `dark_rider.py` | +12 | 22 |
| `goblin.py` | +6 | 18 |
| `orc.py` | +8 | 18 |
| `troll.py` | +8 | 18 |
| `undead.py` | +8 | 18 |

Nilai yang dipakai permainan adalah jalur `cached_minion_draw` (+6 / 18), karena badan
dirender dengan `_RENDERING_TO_CACHE = True` sehingga bar di dalam renderer per-tipe
dilewati. Nilai +8 / +12 hanya hidup kalau sprite cache dimatikan; itu sebabnya
`overlay_ops()` memakai +6 / 18 dan tabel di atas tetap dipin sebagai bukti.

## Lima renderer tubuh

Setiap namespace berisi helper anti-alias, palet, dan 5 level tubuh. Seluruh pikselnya
sudah native lewat `bake/bake_minion_atlas.py` yang menjalankan `Minion.draw` asli.

### `goblin.py` (37 simbol)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `_aacircle` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aaline` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aapolygon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_blend_alpha` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_clamp_color` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_offhand` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_offhand_dagger` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_weapon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_bleed_ground_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_bleed_particles` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_bleed_stacks_icons` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_boot` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_bracer` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_crown` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_dagger` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_deadly_nick_arc` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_deadly_nick_impact` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_fist` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_goblin_full` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_goblin_lvl1` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_goblin_lvl2` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_goblin_lvl3` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_goblin_lvl4` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_goblin_lvl5` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_ground_shadow` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_head` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_legs` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_master_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_red_hood` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_spiked_pauldron` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_swing_blur` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_armored` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_simple` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_vest` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_get_palette` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `draw_goblin` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |

### `orc.py` (33 simbol)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `_aacircle` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aaline` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aapolygon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_blend_alpha` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_clamp_color` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_offhand` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_weapon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_axe` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_bracer` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_brutal_blows_arc` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_brutal_impact` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_fist` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_ground_shadow` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_head` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_heavy_boot` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_horns` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_legs` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_muscular_arm` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_orc_full` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_orc_lvl1` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_orc_lvl2` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_orc_lvl3` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_orc_lvl4` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_orc_lvl5` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_red_shoulder_pad` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_swing_blur` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_topknot` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_armored` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_bare` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_harness` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_warchief_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_get_palette` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `draw_orc` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |

### `troll.py` (36 simbol)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `_aacircle` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aaline` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aapolygon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_blend_alpha` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_clamp_color` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_offhand` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_weapon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_bracer` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_champion_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_fist` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_ground_shadow` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_head` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_impact_sparkle` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_legs` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_mace` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_mohawk` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_muscular_arm` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_regen_cross_icon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_regen_ground_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_regen_particles` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_spiked_pauldron` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_swing_arc` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_swing_blur` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_armored` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_bare` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_harness` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_harness_bones` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_troll_foot` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_troll_full` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_troll_lvl1` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_troll_lvl2` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_troll_lvl3` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_troll_lvl4` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_troll_lvl5` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_get_palette` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `draw_troll` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |

### `undead.py` (38 simbol)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `_aacircle` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aaline` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aapolygon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_blend_alpha` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_clamp_color` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_offhand` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_arm_weapon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_armor_boot` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_armored_arm` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_aura_sparkles` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_cape` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_chest_emblem` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_crown` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_death_knight_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_floating_souls` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_gauntlet` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_ground_shadow` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_head_skull` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_helm` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_legs` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_shield` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_shoulder_spikes` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_soul_skull` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_swing_blur` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_sword` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_chestplate` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_torso_ribs` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_undead_full` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_undead_lvl1` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_undead_lvl2` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_undead_lvl3` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_undead_lvl4` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_undead_lvl5` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_unholy_arc` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_unholy_ground_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_unholy_impact` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_get_palette` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `draw_undead` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |

### `dark_rider.py` (34 simbol)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `_aacircle` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aaline` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_aapolygon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_blend_alpha` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_clamp_color` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_cape` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_chest_emblem` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_crown` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_curse_arc` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_curse_ground_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_curse_impact` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_dark_rider_full` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_death_charge_icon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_dread_lord_aura` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_ground_shadow` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_hoof_flames` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_horse` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_horse_barding` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_horse_legs` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_body_armored` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_body_light` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_head` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_lvl1` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_lvl2` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_lvl3` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_lvl4` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_lvl5` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_rider_weapon` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_shoulder_spikes` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_speed_trail` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_sword` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_draw_sword_blur` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `_get_palette` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |
| `draw_dark_rider` | `bake` | `godot_rebuild/bake/bake_minion_atlas.py`:60 |

## Registry dan dispatcher (`__init__.py`)

| Simbol | Jenis | Target |
| --- | --- | --- |
| `MINION_RENDERERS` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:59 |
| `_install_aliases` | `meta` | `minions/__init__.py`:24 |
| `render_minion` | `native` | `godot_rebuild/scripts/ui/minion_overlay.gd`:85 |

`MINION_RENDERERS` memetakan lima tipe ke lima fungsi draw; `render_minion` mencoba
`mobile.spritecache.render_minion_cached` lebih dulu, lalu memanggil renderer langsung,
dan hanya mencetak peringatan untuk tipe tak dikenal. Padanan native:
`minion_overlay.gd::TYPES` + `has_type()`.

## Bukti uji

| Lapisan | Berkas | Isi |
| --- | --- | --- |
| Oracle | `tests/minions_source_oracle.py` | stub pygame perekam, eksekusi 6 helper, klasifikasi 201 simbol, deteksi call-site |
| Fixture | `tests/fixtures/minions_source.json` | inventaris, rentang modul, konstanta, primitif overlay, cache key, klasifikasi |
| Suite native | `tests/minions_checks.gd` | 8 HP bar + 4 aura + 7 slash + 5 cache key dibandingkan primitif, 50 atlas, histogram jenis |
| Bake | `bake/bake_minion_atlas.py` | 50 sheet, 25 pose x 2 arah per (tipe, tim, level) |
| Bake FX | `minion_combat_fx.json` | 5 atlas slash/death, 75 kasus, 32 langkah sudut |
| Validator | blok `9cc` di `tests/validate_project.py` | drift oracle vs fixture, larangan helper mati diport, tabel offset bar |

## Determinisme dan deviasi

- **DEVIASI (slow aura):** sumber tidak menjaga `draw_slow_effect` dengan `_RENDERING_TO_CACHE`,
  jadi aura ikut masuk sprite cache dan **beku** pada frame pertama; Godot menggambarnya
  hidup tiap frame dari `slow_timer`. Bentuk dan posisi tiga percikannya identik.
- **DEVIASI (slash):** atlas bake menyimpan 32 langkah sudut; `slash_ops()` menghitung
  sudut sembarang persis seperti sumber, jadi replay perilaku tidak dibatasi atlas.
- **DELEGATED (hurt flash):** `apply_hurt_flash` tidak dipanggil runtime, tetapi atlas
  sengaja dirender tanpa kilatan dan komentarnya menyerahkan `+90` ke Godot.
  `hurt_color()` menutup kontrak itu.
- **DEAD:** `draw_shadow`, `_SHADOW_CACHE`, dan `calculate_animation_offsets` tidak diport.
  Shadow tubuh sudah ada di frame atlas lewat `_draw_ground_shadow` tiap renderer.
- **INTERNAL:** sprite cache pygame (crop + anchor, recolour tim merah memakai numpy)
  diganti atlas bake per tim; tidak ada perilaku yang hilang karena key cache sudah
  mencakup timnya.

## Yang belum

- **BELUM:** `minion_art.gd` dan `minion_overlay.gd` belum dipakai view pertandingan.
  Belum ada node/`_draw` yang memanggil keduanya, jadi minion belum tampil di Godot.
  Datanya lengkap dan beruji; lapisan yang tersisa adalah wiring view.
- **BELUM:** parity piksel/GPU dan bukti perangkat. Suite membuktikan primitif, geometri,
  dan data, bukan tangkapan layar.

