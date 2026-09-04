# Audit lintas-boss: FX menutupi karakter dengan cahaya

Lanjutan dari perbaikan Razak (`docs/RAZAK_V3_COMBAT_FX.md` §10).
Setelah Razak diperbaiki, SELURUH mini boss & true boss yang punya
lapisan FX hidup disapu dengan metrik yang sama.

## 1. Akar masalah (satu keluarga bug)

`pygame.BLEND_RGB_ADD` / `BLEND_RGBA_ADD` **mengabaikan kanal alpha**.
Empat pola berikut karena itu berubah dari "gradien lembut" menjadi
"cakram warna solid" di atas sprite:

| Pola | Kenapa salah |
|---|---|
| `circle(col, alpha=k)` lalu blit additive | alpha diabaikan → cakram RGB penuh |
| `surf.set_alpha(a)` lalu blit additive | `set_alpha` tidak berefek di mode additive |
| `fill((255,255,255,a), BLEND_RGBA_MULT)` lalu `BLEND_RGBA_ADD` | hanya alpha yang teredam, RGB tetap penuh |
| poligon FX berpusat di caster digambar **padat** | menutup siluet walau alpha benar |

Perbaikannya seragam: **premultiply** (intensitas masuk ke RGB *dan*
alpha), `_fade_copy()` ter-cache untuk jalur additive, dan poligon
berpusat-caster dijadikan **cangkang** (hollow).

## 2. Yang diperbaiki

| Modul | Perubahan |
|---|---|
| `heroes/razak_fx.py` | `glow_surface` + `ground_glow_surface` premultiplied; `_blit_faded` additive pakai `_fade_copy`; hit flash cakram putih r≈76 px → glow kecil + kilat dada |
| `heroes/gorath_fx.py` | idem 3 hal di atas; `SkillFX._star()` dapat parameter `hollow` — ledakan E & R yang meletus **di caster** kini cincin bintang, bukan poligon padat r≈176 px |
| `heroes/nyzrak_fx.py` | `glow_surface` premultiplied; `_blit_faded` additive pakai `_fade_copy`; hit flash cakram `fx_white` r≈44 px → glow + kilat; panel kubah R dari 7 baji penuh (dari titik pusat) → pita cangkang |
| `heroes/alchemist_fx.py` | `glow_surface` + `ground_glow_surface` premultiplied; `_blit_faded` additive meredam RGB juga; hit flash pakai falloff tajam (power 2.2) + radius lebih kecil |
| `heroes/ancient_apparition_fx.py` | `glow_surface` premultiplied |
| `bosses/level2.py` | aura "greed" Greevil's Greed: tumpukan lingkaran **padat** r 44→18 px di badan → cincin `thickness=2` |

## 3. Hasil terukur

Metrik: **putih%** = piksel sangat terang (min(r,g,b) ≥ 200) di dalam
siluet badan, dikurangi piksel terang bawaan sprite. **lum+** =
kenaikan luminansi rata-rata dibanding render bersih.

| Boss | Momen | Sebelum | Sesudah |
|---|---|---|---|
| gorath | kena damage | **100 %** (lum+212) | 0 % (lum+13) |
| gorath | R Rupture puncak | 26 % (lum+96) | 0 % (lum+22) |
| nyzrak | kena damage | **75 %** (lum+114) | 6 % (lum+3) |
| nyzrak | R Cold Embrace | 54 % (lum+73) | 4 % (lum+3) |
| alchemist | kena damage | **45 %** (lum+85) | 1 % (lum+19) |
| alchemist | R Greevil's Greed | 8 % (lum+46) | 0 % (lum+28) |
| ancient_apparition | E charge | 8 % (lum+37) | 3 % (lum+18) |
| razak | kena damage | **84 %** | 3 % |
| razak | R Firestorm | 20 % (lum+81) | 1 % (lum+26) |

Semua 21 boss ber-FX-hidup kini di bawah ambang (putih < 12 %,
lum+ < 60) — lihat tabel lengkap di output test. FX-nya **tetap
terang & terbaca** (lum+ 6…56); yang hilang hanyalah efek yang
menelan karakter.

## 4. Verifikasi

```
python3 tools/test_boss_no_white_cover.py    # sapu 21 boss + cek premultiply
python3 tools/test_razak_no_white_cover.py   # kontrak detail Razak
python3 tools/_shot_boss_white_cover.py      # docs/boss_white_cover.png
python3 tools/test_level2_masterwork.py
python3 -m pytest tools/test_razak_v3_combat.py tools/test_gorath_v3_combat.py \
                  tools/test_ancient_apparition_v3_combat.py \
                  tools/test_fx_stability.py -q
```

`tools/test_boss_no_white_cover.py` sudah diuji-balik: mengembalikan
`glow_surface` Gorath ke versi alpha-saja membuatnya GAGAL
(putih 3.9 %, lum+81), jadi penjaga ini benar-benar menangkap regresi.

## 5. Catatan

* Hurt-flash **siluet milik lane boss** (`hurt_flash_timer`, konvensi
  level1/level2 — mask badan di-blit putih selama ≤ 8 frame) sengaja
  DIPERTAHANKAN. Yang dibuang adalah flash KEDUA dari lapisan hidup;
  ketika lane boss sedang menyalakan flash-nya, kontribusi lapisan
  hidup diredam 0.35×.
* `xerathis` (9 %) dan `varkul` (5 %) punya piksel putih bawaan pada
  sprite (baju/salju). Metrik mengurangi baseline itu supaya yang
  diukur murni kontribusi FX.
* 5 test yang gagal di repo (`test_abaddon_masterwork`,
  `test_gorath_masterwork`, `test_menu_klik`, `test_popup_klik`,
  `test_topup_server`) sudah gagal SEBELUM perubahan ini — diverifikasi
  dengan `git stash`.
