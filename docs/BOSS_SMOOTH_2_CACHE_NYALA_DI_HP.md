# Boss Smooth #2 — cache boss benar-benar NYALA di perangkat + FX 60 fps

> Keluhan lanjutan:
> *"pergerakan, animasi swing/projectile attack, skill fx, dan lain-lain
> mini bos dan true bos tidak sefluid hero starter atau hero unlock —
> buat perbaikan yang berlaku global ke semua boss, dan hapus unused
> code"*

Dokumen lanjutan dari [BOSS_HERO_SMOOTH_PARITY.md](BOSS_HERO_SMOOTH_PARITY.md).
Semua angka terukur headless (`SDL_VIDEODRIVER=dummy`, pygame-ce 2.5.8,
**tanpa numpy** — persis seperti bundle Android), kualitas *high*.

---

## 1. Temuan kunci: seluruh cache boss MATI di HP

Pipeline cache boss dari dokumen sebelumnya memiliki satu titik rawan:
probe paritasnya (`_boss_probe_diff_direct` → `_np_abs_diff`) memakai
`pygame.surfarray.array3d`, yang **wajib numpy**.

```
buildozer.spec: requirements = python3,pygame-ce,pyjnius,android
                                              ^^^^^^^ TANPA numpy
```

Konsekuensinya di perangkat (dan di semua lingkungan tanpa numpy):

1. Probe melempar `NotImplementedError: surfarray module not available`
   tepat saat boss pertama digambar.
2. Setelah 8 percobaan, `(tipe, pose)` masuk `_BOSS_PROBE_FAIL` dan
   `render_boss` mengembalikan `False` **selamanya**.
3. SEMUA mini boss & true boss kembali digambar prosedural penuh tiap
   frame (2–7 ms/boss di PC; 3–6× lipat di HP).

Smoke test loop game nyata (600 frame, pygame tanpa numpy = simulasi HP):

| level | boss | sebelum putaran ini |
|---|---|---|
| 10 | thalgryn | mean 5,55 ms · p95 8,32 · cache **0,0 %** |
| 30 | nyrethzalv | mean 8,72 ms · p95 16,82 · >16,7 ms 30/600 |
| 54 | nyxaris | mean 10,60 ms · p95 33,51 · >16,7 ms 77/600 |

Statistik cache: 0 entri, 0 hit — keluhan "boss tidak sefluid hero"
memang masih benar di perangkat, walau di PC pengembang (yang kebetulan
punya numpy) cache tampak bekerja.

---

## 2. Perbaikan (semua berlaku GLOBAL, tanpa menyentuh 216 renderer)

### 2.1 `heroes/__init__.py` — probe paritas tanpa numpy

`_surf_mean_abs_diff(sa, sb)` menggantikan `_np_abs_diff`:

```python
d1 = sa.copy(); d1.blit(sb, (0,0), special_flags=BLEND_RGB_SUB)  # max(0,a-b)
d2 = sb.copy(); d2.blit(sa, (0,0), special_flags=BLEND_RGB_SUB)  # max(0,b-a)
d1.blit(d2, (0,0), special_flags=BLEND_RGB_MAX)                  # |a-b|
buf = pygame.image.tobytes(d1, "RGB")
return sum(buf) / len(buf)
```

Seluruh operasi berat berjalan di level C (SDL). Metriknya **eksaK sama**
dengan `abs(a-b).mean()` milik numpy — tervalidasi bit-per-bit pada
render nyata (gornak 0,0221/0,0221 · nyxaris 2,4828/2,4828) — jadi
semua ambang lama (`BOSS_PARITY_TOLERANCE=0,35`,
`BOSS_STATEFUL_DRIFT=0,08`) tetap berlaku persis. Biaya ±0,9 ms sekali
per (tipe, pose), sama seperti jalur numpy sebelumnya.

### 2.2 `heroes/__init__.py` — pose swing/skill 60 fps untuk boss tanpa lapisan FX hidup

Hero starter/unlock punya lapisan FX hidup (partikel, trail, proyektil)
yang digambar 60 fps di atas sprite body yang terkuantisasi 2 frame.
Untuk ±185 boss tanpa lapisan tersebut, ayunan senjata/proyektil/FX
skill digambar **di dalam render badan** — dulu ikut terkuantisasi ke
30 fps.

Aturan baru di `_boss_cache_key`:

| tipe boss | kuantisasi atk/skill | hasil |
|---|---|---|
| punya lapisan FX hidup (`_LIVE_FX_HEROES`) | 2 frame (paritas hero) | FX sudah 60 fps di luar cache |
| tidak punya (±185 boss) | **1 frame** (`BOSS_FX_FRAME_QUANT`) | swing/proyektil/skill FX maju 60 fps seperti hero |

Kunci tetap dipakai ulang pada siklus serangan/cast berikutnya, dan
governor biaya (`_BOSS_KIND_HM` + `_BOSS_DIRECT_MS`) tetap mengembalikan
pose yang tidak dihemat cache ke jalur langsung. Renderer yang stateful
per-draw (mis. thalgryn saat menyerang, drift probe 0,42–0,76) tetap
otomatis ditolak probe → jalur langsung, sehingga animasi mereka 60 fps
secara inheren tanpa risiko FX membeku.

### 2.3 `bosses/base_boss.py` — aura enrage/frenzy/true-boss/ability di-cache

`Boss.draw()` dulu mengalokasi satu Surface (sampai ±330² px) + belasan
lingkaran konsentris **per frame per aura**:

* aura true boss: menyala SETIAP frame selama true boss hidup;
* aura enrage/frenzy: menyala permanen di sepertiga akhir duel;
* aura ability: menyala selama buff aktif.

Sekarang surface aura diraster sekali per `(radius, fase denyut, warna)`
lewat `_BOSS_AURA_CACHE` (LRU, anggaran 1,5 jt px ≈ 6 MB), fase sinus
dikuantisasi 12 langkah (radius denyut berubah ~1 px per langkah —
di bawah ketebalan garis auranya). Berlaku untuk **semua** boss,
termasuk yang renderernya tidak bisa di-cache sprite.

### 2.4 Governor FX sudah menghitung boss

Dari putaran sebelumnya: `begin_fx_frame(count_busy_fx_heroes(heroes +
[active_boss]))` di `_core.py`. Tidak diubah; tercakup verifikasi
lebih lanjut di putaran ini.

---

## 3. Unused code yang dihapus

`heroes/__init__.py` (≈ **−330 baris**):

| kode | status |
|---|---|
| `_boss_render_sprite` (jalur afine 2-pass, ~200 baris) | mati: satu-satunya pemanggil memakai jalur cepat; juga bergantung numpy → mustahil jalan di HP |
| `_boss_solve_layers`, `_boss_pack_layers`, `_boss_get_opaque`, `_BOSS_OPAQUE_POOL`, `_BOSS_BG1/_BG2` | hanya dipakai jalur afine |
| `_BOSS_PATH`, `_BOSS_AFFINE_MIN_HITRATE`, `_BOSS_AFFINE_MIN_MISS`, `BOSS_PARITY_TOLERANCE_AFFINE`, `BOSS_FAST_FALLBACK_DIFF`, `_BOSS_FAST_DIFF`, statistik `downgrade` | cabang selalu-False (`_BOSS_PATH` tidak pernah berisi `"affine"`) |
| `_boss_uses_wallclock`, `_BOSS_WALLCLOCK`, `BOSS_WALL_QUANT_MS`, render referensi ke-3 (`drift_time`), `_WT` bergulir | `_BOSS_WALLCLOCK` ditulis probe tetapi **tidak pernah dibaca**; `_PROBE_TICK` konstan tetap dipertahankan supaya perbandingan adil |
| `_BOSS_NO_CACHE` + statistik `types_nocache` | set kosong permanen (guard yang tidak pernah diisi) |
| `add_surf` di entri cache & blit aditifnya | selalu `None` sejak jalur afine mati — entri cache kini `(sprite, ax, ay)` |
| `probe_baru` di `render_boss` | sisa refactor |
| `_np_abs_diff` | diganti `_surf_mean_abs_diff` |

`bosses/base_boss.py`:

| kode | status |
|---|---|
| `take_damage_with_defense` | tidak pernah dipanggil di seluruh repo |
| `hp_ratio` (AI xerathis), `stats` (AI malzareth) | variabel mati (pyflakes) |

Perbaikan sampingan gratis: `hero_cache_bytes()` dulu diam-diam selalu
mengembalikan 0 (entry hero `(sprite, ax, ay, uses)` tidak cocok dengan
`_sprite_pixels` lama; exception-nya ditelan). `_sprite_pixels` baru
mengukur `entry[0]` sehingga keduanya benar.

---

## 4. Hasil terukur

### 4.1 Loop game nyata (600 frame/level, tanpa numpy = kondisi HP)

| level | boss | sebelum | sesudah |
|---|---|---|---|
| 1 | gornak | 6,45 ms¹ | **4,17–5,18 ms** · cache 87 % · >16,7 ms 4–6/600 |
| 10 | thalgryn | 5,55 ms | **4,08 ms** · p95 5,08 |
| 30 | nyrethzalv | 8,72 ms | **7,46 ms** · p95 7,98 · >16,7 ms 19/600 |
| 54 | nyxaris | 10,60 ms | **8,95 ms** · >16,7 ms 68/600 |

¹ baseline `MYSTIC_BOSS_CACHE=0` dari dokumen sebelumnya; di HP
tanpa numpy angka inilah yang sebenarnya tampil bahkan saat cache
"nyala".

Tipe yang renderer-nya memang tidak setia di canvas (nyxaris 2,48,
nyrethzalv 0,54; 115 dari 216) tetap digambar langsung — perilaku
desain yang sama seperti di PC — tetapi mereka ikut diuntungkan cache
aura (§2.3) dan perbaikan gerak putaran sebelumnya.

### 4.2 Regresi (tools/test_boss_hero_smooth_parity.py --all, 216 boss)

| uji | hasil |
|---|---|
| frame stall gerak (mini+true) | **0 / 432 jalur** |
| kecepatan pulse boss vs hero | 0,100 vs 0,100 (identik) |
| kunci arah hadap saat swing | 0 flip |
| hit rate cache sprite | 89 % sampel; 2 158 hit / 976 miss seluruh tipe |
| cache lebih lambat dari jalur lama | 0 tipe |
| biaya draw boss vs hero (median) | **0,18×** (terburuk 0,62×) |
| exception | 0 dari 216 |
| FX terpotong tepi sprite | 0 / 194 sprite |
| anchor bbox bergeser | 0 px |
| regresi visual (tools/_diag_boss_pixel_parity.py) | 0 / 22 tipe |

### 4.3 Diagnostik perangkat

Overlay debug (`mobile/debug.py`) menampilkan `cache BOSS hit %` —
cara termudah memastikan di HP bahwa cache benar-benar menyala setelah
perbaikan ini (sebelumnya selalu 0 % / kosong).

---

## 5. Cara memverifikasi ulang

```bash
# tanpa numpy (kondisi perangkat) — semua harus tetap hijau:
python3 tools/test_boss_hero_smooth_parity.py --all
python3 tools/_diag_boss_scene_smoke.py
python3 tools/_diag_boss_pixel_parity.py
python3 tools/_diag_boss_probe_dist.py
```
