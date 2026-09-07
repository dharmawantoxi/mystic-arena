# Audit Paritas pygame → Godot (data mati & call site tanpa padanan)

Tanggal: 2026-09-07 · Cakupan: `godot/data/*.json`, `godot/**/*.gd`,
`tools/convert_to_godot.py`, dibandingkan ke sumber kebenaran pygame.

## Kenapa dokumen ini ada

Tiga bolong yang ditutup sesudah PR #169 semuanya bertipe **sama**: converter
sudah mengekspor data, tapi tidak ada satu baris GDScript pun yang membacanya
(`particle_type` cuma disebut di komentar selama berbulan-bulan). Bug jenis ini
tidak pernah muncul sebagai error — `gdparse` lolos, `check_refs` lolos, game
jalan, hanya saja fiturnya diam-diam tidak ada.

Audit ini menyapu sistematis untuk mencari sisa kasus serupa, bukan menunggu
ketahuan satu per satu.

## Metode

1. **Data mati**: kumpulkan semua nama *field* di `godot/data/*.json` (nama
   entitas seperti `aelyrion`/`ice` disaring keluar karena diakses dinamis
   lewat `HeroDB.get(name)`), lalu cari tiap nama itu di seluruh `.gd`. Yang
   tidak pernah muncul = kandidat data mati.
2. **Call site tanpa padanan**: daftar nama SFX yang benar-benar dimainkan
   pygame vs yang dipanggil GDScript.
3. Tiap kandidat diperiksa manual ke pygame: apakah di sana memang **dipakai
   renderer**, atau ternyata dead code juga.

Langkah 3 penting — `has_torch_stones` ada di 54 tema tapi `DecorationRenderer`
pygame tidak pernah membacanya, jadi memportnya justru menambah fitur yang
tidak ada di sumber kebenaran.

## Temuan

### A. Data mati yang NYATA (pygame memakai, Godot tidak)

| # | Kunci | Status pygame | Status Godot | Dampak |
|---|---|---|---|---|
| A1 | `has_dark_trees` (42/54 tema) | `DecorationRenderer.draw_all` `_bundle.py:6106` → `_draw_dark_trees` | ✅ **DIPERBAIKI** | dekor pohon gelap seragam |
| A2 | `has_dead_trees` (38/54) | `:6102` → `_draw_dead_trees` (cabang `elif` setelah `has_frozen_trees`) | ✅ **DIPERBAIKI** | pohon mati/kering tidak pernah muncul |
| A3 | `has_bones` (32/54) | `:6092` → `_draw_bones` | ✅ **DIPERBAIKI** | tema tulang-belulang hilang |
| A4 | `has_rocks_mossy` (54/54) | `:6088` → `_draw_rocks` | ✅ **DIPERBAIKI** | batu berlumut selalu batu polos |
| A5 | `path_moss`, `path_crack` | `_draw_cobblestone_tile` `:5206-5207` — `path_crack` volcanic = `(255,100,20)` **retakan lava menyala** | ✅ **DIPERBAIKI** `_draw_lane()` | jalur semua tema tampak sama; lava crack hilang |
| A6 | `meta_gold_reward_lose` | `_grant_meta_reward` `_core.py:2378-2380` baca dari cfg level | ✅ **DIPERBAIKI** `_grant_meta_reward()` | saat ini aman (54/54 level = 0), tapi ubah satu level di pygame → Godot diam-diam menyimpang |

`path_crack` (A5) menurut saya yang paling terasa: di tema `volcanic` nilainya
warna lava menyala, jelas dimaksudkan sebagai aksen visual, bukan sekadar
varian abu-abu.

### B. Bukan bug — sengaja / dead code di pygame juga

| Kunci | Alasan |
|---|---|
| `has_torch_stones` | ada di 54 tema, **tidak pernah dibaca** `DecorationRenderer` — dead code di pygame |
| `burnt`, `earth_high` | hasil `THEME_KEY_MAP` (`dire_burnt`/`dire_earth_4`); dipakai `_draw_terrain` Godot lewat `d.get("grass_high", ...)` pola dinamis, dan `burnt` memang cadangan palet |
| `entrance_color` (bosses) | ~~milik layar intro boss — belum diport~~ ✅ **DIPAKAI** sejak Fase 5d (2026-09-07): `BossIntroBanner.gd`, siluet `LevelIntro.gd`, dan ledakan/perayaan `BossDeathFX.gd` |
| `skill_desc`, `skill_duration` | teks UI + durasi AI; `SkillBook.gd` memakai tabel cooldown sendiri (deviasi terdokumentasi) |
| `playstyle`, `power`, `tier` | metadata arketipe untuk balancing, tidak dipakai runtime pygame |
| 23 field `items.json` (`proc_chance`, `dash_distance`, `root_radius`, …) | milik **17 item aktif** + `on_attack`/`bash`/`multishot` — sudah tercatat sebagai Fase 5b |
| kategori `items_meta.json` (`agility`, `frost`, …) | label kategori, dipakai sebagai nilai dinamis bukan nama field |
| `ambient_tint` alpha | sudah dipakai `_derive_theme_extras()` → `modulate` |

### C. Audio — bersih

Semua nama SFX yang dimainkan pygame sudah ada padanannya. Yang sempat
terlihat "hilang" ternyata dipanggil lewat `Callable.bind()` sehingga luput
dari grep literal:

- `ui_click` → `MainMenu.gd:378/975` (`play_sfx.bind("ui_click")`)
- `ui_sell`, `ui_upgrade` → `ShopPanel._run()`
- `bullet_hit` → sengaja tidak dipakai: **`bullet_hit.wav` tidak ada** di
  `assets/sounds/` walau `SoundManager.load()` memintanya (`_system.py:554`);
  sudah dicatat di `TowerBullet.gd:137-138`
- `play_positional` → dead code, sudah didokumentasikan

## Rekomendasi urutan kerja

1. ~~**A5 `path_crack`/`path_moss`**~~ — ✅ selesai. `_draw_lane()` kini
   menggambar bercak lumut + retakan memakai rumus varian deterministik
   pygame `(x*3 + y*7) % 100`; sebaran ±24% lumut / ±13% retakan (aksen, tidak
   menutupi jalur).
2. ~~**A6 `meta_gold_reward_lose`**~~ — ✅ selesai, `cfg.get(...)` menggantikan
   angka 0 hardcode.
3. ~~**A1-A4 flag dekor**~~ — ✅ selesai. `_build_decor()`/`_draw_decor()` kini
   punya `DECOR_DEAD_TREE` + `DECOR_BONES` dan lumut di batu, dan yang paling
   penting: **membedakan sisi peta**. pygame menaruh pohon gelap hanya di
   Radiant, pohon mati/tulang hanya di Dire (`generate_all` `_bundle.py:4767-4821`
   memakai `_is_radiant()`/`_is_dire()`), jadi `_is_dire()` ikut diport —
   tanpa itu peta terasa simetris dan sisi Dire kehilangan kesan gersang.

   Ambang jenis **ditumpuk**, bukan rentang tetap. Versi pertama memakai ambang
   tetap dan simulasi memberi tema `ice` 49 kristal dari 70 dekor: rentang
   kristal melar mengisi jatah jenis yang mati. Setelah ditumpuk: ice 11
   kristal / 11 pohon / 46 batu, forest 20 pohon / 17 pohon mati / 6 tulang.

**Semua temuan A1-A6 sudah ditutup.** Sisa pekerjaan paritas berikutnya bukan
lagi "data mati", melainkan fitur yang memang belum diport (Fase 5b item aktif,
AIPlayer penuh, TileSet `.tres`).

**Update 2026-09-07 (Fase 5d):** cinematic intro/celebration selesai diport —
`entrance_color` (tabel B) kini dipakai `LevelIntro/BossIntroBanner/BossDeathFX`,
layar intro boss & kematian boss `_render.py:1622-3300` tidak lagi "belum diport".
Field BARU `gold_reward` ditambahkan ke export `bosses.json` (dibaca perayaan
"BOSS DEFEATED!" — paritas `boss.gold_reward` `bosses/base_boss.py:394`).

Catatan verifikasi: tanpa binary Godot di sandbox, nomor 1-3 hanya bisa
divalidasi lewat `gdparse` + `tscn_lint` + `check_refs` (sintaks & konsistensi
referensi). Hasil visualnya tetap perlu dicek sekali di editor.
