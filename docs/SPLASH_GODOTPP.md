# Migrasi `splash_screen.py` → godot++ (GDExtension C++)

Port `splash_screen.py` (371 baris: splashscreen pembuka — logo + judul
`MYSTIC ARENA` + tagline + 46 partikel + latar gradien/vignette + glow judul +
hint skip) ke tiga lapisan dari satu sumber: Python (oracle), GDScript
(`SplashModel.gd`), dan C++ (`MysticSplash`, GDExtension `mystic_splash`).
Status paritas menyeluruh: [`docs/GODOT_PARITY.md`](GODOT_PARITY.md) (FASE 38).

Cakupan yang SENGAJA keluar: piksel (`pygame.draw`, `Surface`, cache tekstur
`_bg_cache`/`_logo_cache`, `smoothscale`) dan **metrik font** — keduanya tetap
di renderer (`godot/scenes/ui/SplashScreen.gd` + `UiTheme`). Yang dimigrasi
adalah **lapisan model**: setiap angka, geometri, dan predikat yang menentukan
apa yang digambar dan kapan splash selesai.

## Kenapa C++ untuk splashscreen?

Alasan yang sama dengan levels (FASE 34) / maps (FASE 35) / ui (FASE 36), plus
dua alasan khusus splash:

1. **Splash adalah layar pertama yang dilihat pemain** — dan justru di sini
   port Godot lama menyimpang paling jauh: latarnya gradien ungu tipis padahal
   pygame menghasilkan **interior hitam pekat + rim 2 px** (§7), dan skip-nya
   memakai timer sejak tombol ditekan padahal pygame mengukur **elapsed total**
   (§5). Keduanya deviasi produksi yang baru bisa dibuktikan dengan
   MENJALANKAN pygame aslinya — jadi fase ini memulai dari oracle, bukan dari
   port.
2. **Rantai float panjang.** Posisi partikel adalah akumulasi 120+ langkah
   `x += drift + sin(t*0.8+phase)*0.05` dengan `t` yang juga diakumulasi
   (`t += dt`). Melewatkan state ini lewat `Vector2` (float 32-bit) atau
   membulatkan `elapsed` ke 9 digit cukup untuk membalik ambang wrap/`done`
   (§4, §12).

## Arsitektur

```
splash_screen.py                       (sumber kebenaran, TIDAK disunting)
  │ AST (tools/gen_splash_cpp.py)        │ dibaca oracle (tools/test_godot_splash_parity.py)
  ▼                                      ▼  MENJALANKAN pygame ASLI (SDL dummy +
gdext/mystic_splash/src/                    font palsu + TrackSurface)
  splash_processor.h   (108 baris)          │
  splash_processor.cpp (715 baris)          ▼
  62 method static bound              godot/tests/fixtures/splash_parity.json (141 KB)
        │                                   │
        │                          ┌────────┴─────────┐
        │                          ▼                  ▼
        │            scripts/ui/SplashModel.gd   tools/test_splash_cpp_selftest.py
        │            (480 baris, fallback)       (1585/1580 cek, 6524 perintah,
        │                          │              eksekusi .cpp di luar engine)
        ▼                          ▼
  scripts/ui/SplashBackend.gd (522 baris) — saklar: C++ dulu, jatuh ke GDScript
        │
        ▼
  scenes/ui/SplashScreen.gd (279 baris) — renderer; SEMUA angka lewat Backend
```

### Peta berkas

| Berkas | Peran |
| --- | --- |
| `tools/gen_splash_cpp.py` (1.367 baris) | AST `splash_screen.py` → C++; `--check` untuk CI |
| `godot/gdext/mystic_splash/src/splash_processor.{h,cpp}` | **GENERATED** — `MysticSplash : RefCounted`, 62 method static |
| `godot/gdext/mystic_splash/src/register_types.{h,cpp}` | entry `mystic_splash_library_init` (level SCENE) + `ClassDB::register_class` |
| `godot/gdext/mystic_splash/SConstruct` | output → `../../addons/mystic_splash/bin/` |
| `godot/gdext/mystic_splash/selftest/splash_dispatch.inc` | **GENERATED** — tabel perintah (wajib 1:1 dengan API) |
| `godot/gdext/mystic_splash/selftest/{splash_selftest.cpp,godot_stub.hpp,shim/}` | harness stdin-TAB + stub `Variant`/`String`/`Color`/`Rect2`/`Vector2` (bukan bagian lib) |
| `godot/addons/mystic_splash/mystic_splash.gdextension` | kunci `debug`/`release` → berkas `template_*` |
| `godot/scripts/ui/SplashModel.gd` | kembaran GDScript 62 fungsi + konstanta + `API_SIGNATURE` |
| `godot/scripts/ui/SplashBackend.gd` | saklar backend (pola `MapDBLoader`/`LevelDBLoader`) |
| `godot/scenes/ui/SplashScreen.gd` | renderer (`CanvasLayer` + `_SplashView._draw`) |
| `godot/tests/SplashParityTest.{gd,tscn}` | fixture vs backend GDScript + smoke scene asli |
| `godot/tests/SplashGdextParityTest.{gd,tscn}` | fixture vs backend C++ + A/B seluruh API |

## Bentuk API di C++

Satu kelas `MysticSplash : RefCounted` dengan **62 method static** — tidak ada
state di sisi C++, jadi tidak ada risiko lifecycle lintas backend (pola
`MysticUI` FASE 36). Pengelompokan: meta (3), konstanta (16), partikel (9),
timing & state (11), latar (6), konten & logo (10), glow judul + aksen (5),
hint (2). Daftar lengkap: [`godot/gdext/mystic_splash/README.md`](
../godot/gdext/mystic_splash/README.md).

Dua aturan tipe yang mengikat:

- **Partikel = `Dictionary` of double, bukan `Vector2`.** `particle_move` /
  `particle_advance` mengembalikan `{"x": .., "y": .., "wrapped": ..}`. `Vector2`
  Godot menyimpan `float` 32-bit, jadi satu kali round-trip sudah cukup untuk
  menggeser rantai 120 langkah (dan memindahkan frame wrap). `Vector2` hanya
  dipakai untuk posisi gambar yang sudah di-`int()` (`particle_draw_pos`,
  `hint_pos`, `content_center`).
- **`int` Python = trunc, `round()` Python = half-to-even.** Generator
  menurunkan helper `py_int()` / `py_round()` (bukan `(int)` / `std::round`
  C++ yang half-away) karena `gq = round((0.85 + 0.15*grow) * 20) / 20.0`
  (`splash_screen.py:278`) dan `int(alpha * 0.28)` (`:333`) persis berada di
  atas kasus setengah.

## Semantik yang dikunci (Python vs Godot)

### 1. Gerak partikel per FRAME, bukan per detik

`update()` menggeser `p["y"] -= p["speed"]` dan
`p["x"] += p["drift"] + sin(elapsed*0.8 + phase)*0.05` (`:139-146`) — `speed`
dan `drift` adalah **per frame**, tidak dikali `dt`. Renderer Godot memanggil
`particle_advance` sekali per `_process` (bukan `delta * speed`), dan `elapsed`
yang dikirim adalah akumulasi `delta` — jadi pada 30 FPS splash Godot bergerak
setengah kecepatan pygame. Itu memang perilaku pygame-nya (frame-based), dan
fixture mengunci 120 langkah apa adanya.

### 2. Wrap: `< -6` strict, respawn `h + 6`, `x` dari RNG

`if p["y"] < -6: p["y"] = self.h + 6; p["x"] = random.uniform(0, self.w)`
(`:143-146`). Predikatnya strict (`particle_wrapped(-6.0) == false`), dan
`respawn_x` **argumen pemanggil** — bukan tanggung jawab backend (§3).

### 3. RNG partikel TIDAK punya paritas (deviasi disengaja)

`_make_particles` (`:105-124`) dan respawn memakai RNG global pygame yang
**tidak pernah di-seed**, jadi tidak ada stream yang bisa diklaim. Keputusan:

- Godot memakai `RandomNumberGenerator` ber-seed tetap **777** di
  `SplashScreen._ready` supaya boot deterministik (posisi awal berbeda dari
  pygame, distribusi sama: rentang `r`/`speed`/`drift`/`phase` + 4 warna
  dikunci fixture lewat `particle_ranges()`/`particle_colors()`);
- paritas RANTAI tetap diuji: oracle me-`spy` `random.uniform` sehingga nilai
  respawn pygame yang sebenarnya terekam di fixture
  (`particles.respawn = [[lo, hi, value], ...]`), lalu self-test C++ dan kedua
  scene engine menyulang nilai itu ke `particle_advance` dan membandingkan
  posisi akhir 46 partikel setelah 120 langkah (1 wrap terpakai, `x` respawn
  `687.6113336934955`).

### 4. `elapsed` akumulasi — jangan dibulatkan

pygame menjumlahkan `dt`: pada frame 180 `elapsed = 2.9999999999999996 < 3.0`,
jadi `done` masih `False` dan baru `True` di frame 181. Fixture menyimpan
`elapsed` **presisi penuh**; percobaan pertama menyimpan `round(t, 9)` dan
self-test langsung merah di dua baris ambang (`is_done(3.0) == True` padahal
rekaman pygame `False`).

### 5. Skip: `skip()` hanya menyetel bendera; ambangnya elapsed TOTAL

```python
def skip(self):                      # :125-128
    if not self.done: self.skipped = True
...
if self.skipped:                     # :148-155 (update)
    if self.elapsed >= 0.25: self.done = True
else:
    if self.elapsed >= dur: self.done = True
```

Dua konsekuensi yang dilewatkan port lama:

- `done` baru dihitung `update()` **frame berikutnya**, jadi pada frame tempat
  `skip()` dipanggil `done` masih `False` walau alpha sudah memakai bendera
  baru. Fixture menyimpan **dua bendera per baris** (`skipped_update`,
  `skipped_alpha`) supaya ambang ini tidak bisa "lulus" karena kebetulan.
- Ambangnya `self.elapsed` **total**, bukan waktu sejak skip: skip di `t = 2.0`
  langsung selesai di frame berikut, dan `_overall_alpha()` (`:167-176`)
  memakai `max(0, 1 - t/0.25)` sehingga layar sudah tak tampak sesudah
  `t = 0.25` **berapa pun** waktu skip-nya.

Port Godot lama memakai `_skip_t` (timer sejak skip). Semantik lama itu TIDAK
dihapus tapi dipindah ke backend sebagai `overall_alpha_godot` /
`is_done_godot` (argumen `skip_t`), jadi A/B harness bisa menunjuk bedanya
baris demi baris dan `SplashScreen.gd` kini memanggil varian pygame
(`overall_alpha` / `is_done`).

### 6. `title_alpha` dan alpha yang digambar

`t < 0.5 → 0`, selain itu `int(255 * min(1, (t-0.5)/0.6))` (`:157-162`); yang
digambar `ta = int(title_alpha * a)` (`:259`) — dua kali trunc, dikunci
`title_alpha` + `title_alpha_drawn`.

### 7. Vignette MENJENUH ke 255 → interior hitam, rim 2 px

```python
for i in range(140, 0, -2):                     # :219-223
    alpha = min(255, int(2.2 * (140 - i)))
    pygame.draw.rect(vig, (0, 0, 0, alpha), (i, i, w - 2*i, h - 2*i))
```

70 bingkai, dan `2.2 * (140 - i) >= 255` mulai `i <= 24` → **12 bingkai
terakhir alpha 255**. Karena digambar luar→dalam lalu di-`blit` ke gradien,
interior layar hitam pekat dan hanya rim 2 px (`i < 2`) yang menampakkan
gradien. Fixture merekam 48 batang + 70 bingkai + **9 probe piksel hasil render
asli** (`(0,0)`/`(1,1)` = `[8,8,18]`, `(2,2)`..`(640,360)` = `[0,0,0]`,
`(1279,719)`/`(1278,718)` = `[6,6,15]`); kedua scene engine punya kompositor
kecil (gradien → vignette `dst * (255-a)/255`) yang harus mereproduksi
kesembilan probe itu. Renderer Godot menggambar 48 + 70 primitif apa adanya
(dulu: gradien ungu + vignette tipis).

### 8. Latar tidak dimodulasi alpha keseluruhan; `draw()` early-return

`a <= 0.001 → return` (`:180-181`) dan `surf.blit(bg, (0,0))` tanpa
`set_alpha` (`:230`) — latar selalu opaque selama splash tampak. Godot:
`draw_visible(a)` menjadi gerbang `_draw`, dan `_draw_bg()` tidak memakai
modulate.

### 9. Urutan gambar (blit + primitif) dikunci, bukan diasumsikan

`pygame.Surface.blit` tidak bisa di-monkeypatch (tipe C immutable), jadi oracle
memakai `class TrackSurface(pygame.Surface)` sebagai `screen` dan merekam
**urutan panggil** blit + `pygame.draw.*`. Hasilnya dua skenario fixture:

- dengan logo (`t = 1.5`): `bg → logo_glow → logo_img → glow_title_0..2 →
  title_copy → tagline → hint`, diselingi 46 `circle` partikel dan 4 `line`
  aksen;
- tanpa logo (`t = 2.0`): `bg → glow_title_0..2 → title_copy → tagline → hint`.

Scene engine membandingkan `dest` tiap blit dengan keluaran API model
(`title_glow_surface().position` == dest `glow_title_i`, `text_rect.position`
== dest `title_copy`, `logo_glow_rect().position` == dest `logo_glow`,
`center - size/2` == dest `logo_img`) dan triplet 46 circle dengan
`particle_draw_*` — jadi urutan tidak cukup "kira-kira sama".

### 10. Logo: skala, kuantisasi grow, cincin glow

`scale = min(340/w, 320/h, 1.0)` (`:263-265`) → `int()` trunc + `max(1, ..)`;
`grow = min(1, elapsed/0.9)`, `gq = round((0.85 + 0.15*grow) * 20)/20`
(**half-to-even**, `:275-278`) → 10 baris tabel fixture;
`glow_r = max(ww, hh)//2 + 30` (`:287`); judul `rect.bottom + 46`, tagline
`rect.bottom + 88`, cabang tanpa-logo judul di `base_y` dan tagline
`base_y + 66` (`:298-315`).

**Cincin glow melangkah −3**: `for g in range(glow_r, 0, -3)` (`:290`) dengan
`alpha_g = int(12 * (1 - g/glow_r))` (`:291`) → 64 cincin untuk `glow_r = 190`.
Generator draf pertama menyimpan langkah **+3**, dan `logo_glow_rings` di C++
(`while (g > 0) { ...; g += 3; }`) jadi **loop tak berujung** — self-test
kehabisan memori (`rc = -9`) sebelum sempat membandingkan apa pun. Arah
langkah kini bagian dari spec (`GLOW_STEP = -3`), self-test mengunci 64 cincin
menurun, dan kedua scene engine meng-assert `rings[1].r < rings[0].r`.

Karena pygame menggambar disk bertingkat ke surface SRCALPHA (tiap cincin
**menimpa**, bukan menumpuk), renderer Godot menggambar tiap cincin sebagai
`draw_arc` lebar 3 px — pendekatan piksel yang terdokumentasi, angkanya
(radius + alpha per cincin) dari backend.

### 11. Glow judul + garis aksen

Lapisan glow hanya ada kalau `mobile.perf.Quality.cheap_alpha` (`:323-327`):
`[(24, 1), (14, 2), (8, 3)]`, permukaan `(w + 2*layer, h + 2*layer)` yang
tumbuh `+2` per `spread` lewat `smoothscale`, di-blit di
`(rect.x - layer - 1, rect.y - layer - 1)`, dan diisi
`(*ACCENT, int(alpha * 0.28))` dengan `BLEND_RGBA_MULT` (`:328-338`). Backend
menyediakan `title_glow_layers(cheap)` / `title_glow_surface(rect, layer,
spread)` / `title_glow_fill(alpha)`; **piksel** glow-nya tetap pendekatan
`UiTheme.draw_glow` (pola FASE 36). Cabang `cheap = false` (tanpa lapisan)
ikut di API supaya saklar kualitas pygame bisa dipakai apa adanya.

Aksen: `gap = rect.w // 2 + 18`, `y = rect.centery`, `off ∈ {-6: ACCENT,
6: ACCENT_2}`, `fac = (alpha/255) * 0.85`, panjang 46, lebar 2; garis kanan
digambar dari `(cx+gap, y+off)` ke `(cx+gap-46, y+off)` (`:346-357`) — arah
terbalik tidak mengubah piksel `pygame.draw.line`, dan renderer Godot
menyalin arah itu apa adanya.

**Metrik font tidak deterministik** (TTF asli + hinting per platform), jadi
oracle me-monkeypatch `_init_fonts` dengan font palsu
(`w = len(teks) * size // 2`, `h = size`) dan sisi Godot mengirim **lebar teks
terukur** ke fungsi murni (`accent_gap(int(tw))`,
`title_glow_surface(text_rect, ..)`) — geometri terkunci tanpa bergantung font
engine mana pun (pola oracle `ui_theme` FASE 31).

### 12. Presisi: `Vector2` float32 vs double

Selain §3, self-test membandingkan posisi akhir partikel dengan toleransi
`1e-9` (bukan `==`) karena C++ dan Python sama-sama double tetapi urutan
operasi harus identik: `x + drift + sin(t*0.8 + phase)*0.05`. Generator
menurunkan ekspresi apa adanya dari AST (bukan menyusun ulang), dan
`particle_move` mengembalikan `Dictionary` supaya tidak ada `Vector2` di jalur
state (§"Bentuk API").

## Nama berkas lib: `debug` ≠ `template_debug`

scons menghasilkan `libmystic_splash.linux.template_debug.x86_64.so`, sedangkan
kunci `[libraries]` di `.gdextension` adalah `linux.debug.x86_64`. Bug persis
ini (FASE 33) membuat lib tidak pernah termuat engine tanpa pesan jelas;
`.gdextension` mystic_splash ditulis dengan pemetaan yang benar dan langkah
build CI memverifikasi `nm -D --defined-only | grep " T mystic_splash_library_init"`.

Isi modul **tidak bisa** diverifikasi lewat symbol table: `symbols_visibility`
default godot-cpp = `hidden` (nama kelas tak ada di `nm -D`) dan
`SCONS_FLAGS debug_symbols=no` menambahkan `-s` (symbol statis hilang). Yang
tahan strip adalah string khas generator, jadi CI memeriksa
`splash_v1:1mod:62fn:` (`api_signature()`) + `MysticSplash` lewat `strings -a`
yang ditampung ke variabel dulu (menyalurkannya ke `grep -q` bikin `strings`
kena SIGPIPE → gagal palsu di bawah `set -o pipefail`).

## Build

```bash
cd godot/gdext/mystic_splash
ln -s ../godot-cpp godot-cpp        # atau clone godot-4.3-stable
scons platform=linux target=template_debug -j"$(nproc)"
# → godot/addons/mystic_splash/bin/libmystic_splash.linux.template_debug.x86_64.so
```

CI memakai `optimize=none debug_symbols=no` dan satu checkout godot-cpp bersama
(`godot/gdext/godot-cpp`) yang di-symlink ke lima ekstensi. Menyalakan jalur
C++: `mystic/splash/use_gdext_splash=true` di `godot/project.godot`
(**default `false`**). Tanpa lib, `SplashBackend` turun ke `SplashModel.gd`
senyap — flag `true` di mesin tanpa compiler tidak merusak apa pun.

## Empat lapis verifikasi

```bash
# 1. kesegaran transpile (tanpa compiler, detik)
python3 tools/gen_splash_cpp.py --check

# 2. oracle: MENJALANKAN splash_screen.py ASLI (SDL dummy + font palsu +
#    TrackSurface) -> fixture, lalu bandingkan dengan SplashModel.gd + literal
#    C++, audit API tiga sisi + arity panggilan Backend.* + ruang lingkup
#    identifier GDScript + semantik argumen sweep, dan wiring closed-world
#    (613 cek; butuh pygame-ce)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 tools/test_godot_splash_parity.py
#    regenerasi fixture HANYA bila splash_screen.py berubah:
python3 tools/test_godot_splash_parity.py --write-fixture

# 3. jalankan C++ di luar engine (butuh g++ saja; 1585 cek dengan checkout
#    godot-cpp / 1580 tanpa, 6524 perintah)
python3 tools/test_splash_cpp_selftest.py

# 4. paritas runtime di engine (butuh Godot 4.3; langkah 2 butuh lib terbuild)
godot --headless --path godot res://tests/SplashParityTest.tscn --quit-after 400
godot --headless --path godot res://tests/SplashGdextParityTest.tscn --quit-after 400
```

Lapis 3 menutup **closed-world**: jumlah entri `splash_dispatch.inc` == jumlah
`bind_static_method` == deklarasi `.h`, setiap fungsi ter-bind wajib punya
perintah uji (termasuk `api_signature`), tidak ada perintah di luar tabel, id
unik — jadi menambah fungsi Python tanpa meneruskannya ke C++ membuat CI merah,
bukan sunyi. Lapis 2 menambahkan audit **arity tiap panggilan `Backend.*`** di
`SplashScreen.gd` + kedua scene uji: gdparse hanya memeriksa sintaks, sedangkan
Godot memeriksa arity lintas berkas saat scene dimuat (salah satu argumen =
Parse Error yang mematikan seluruh run tanpa menunjuk barisnya — pola bug yang
sama dengan `_fail("a", "b")` di FASE 34).

Lapis 2 juga mengunci **ruang lingkup identifier GDScript**: setiap nama
`ALL_CAPS` telanjang di lima berkas splash `.gd` harus terdeklarasi di berkas
itu sendiri atau ada di daftar global engine yang eksplisit (`PI`/`TAU`/`INF`/
`NAN`, `HORIZONTAL_ALIGNMENT_LEFT`, `MOUSE_BUTTON_LEFT`, `JSON`). Audit ini
lahir dari bug nyata yang lolos semua gerbang lokal dan baru meledak di CI:
`SplashModel.title_glow_surface` menulis `spread * GROW_GROW` di sumbu `y`
(seharusnya `GLOW_GROW = 2`, sama seperti `splash_processor.cpp` yang memakai
`spread * 2` di kedua sumbu). `gdparse` hanya memeriksa sintaks, jadi berkas
terasa sehat; Godot menolak saat `--import` dengan
`SCRIPT ERROR: Parse Error: Identifier "GROW_GROW" not declared in the current
scope` yang **menyeret** `SplashScreen.gd` dan `Main.gd` ikut gagal compile —
satu salah ketik konstanta mematikan seluruh proyek. Kini cek itu lokal, dan
regresinya dikunci dua arah (jumlah kemunculan `spread * GLOW_GROW` == 2).

CI: `godot-check.yml` menjalankan lapis 1 + 3 di langkah kesegaran (sebelum
Godot diunduh) dan lapis 2 + `SplashParityTest` di langkah engine;
`godot-gdext.yml` menjalankan lapis 1 + 3 **sebelum** build godot-cpp (±10
menit), lalu build `mystic_splash`, `SplashGdextParityTest` (require
`[SplashGdextParityTest] PASS` **dan** baris `GDExtension MysticSplash aktif`),
dan regresi "lib terpasang tapi flag `false` → tetap GDScript".
Bug CI kedua juga kelas "lolos semua gerbang lokal": sweep latar di
`SplashParityTest.gd` mengirim **indeks batang** ke `bg_band_color(i, h)`,
padahal argumen pertamanya adalah **y piksel** (pygame menulis
`for i in range(0, self.h, step_h)`). Arity-nya sah — audit arity buta — dan
46 dari 48 batang keluar berwarna batang 0 karena `f = i/720` selalu `< 0.55`.
Oracle kini memeriksa **semantik argumen**: sweep wajib menurunkan
`var y: int = i * step_h` dan argumen pertama `bg_band_rect`/`bg_band_color`
wajib `y` atau ekspresi yang memuat `step_h`.

`godot_log_gate.py` diberi tiga entri allowlist **sempit**
(`libmystic_splash`, `addons/mystic_splash`,
`Failed loading resource.*mystic_splash`) — lib tidak ikut repo, jadi "Failed
loading resource" itu wajar, tapi baris FAIL harness tetap fatal.

## Batas yang disengaja

1. `mystic/splash/use_gdext_splash` tetap **`false`** — jalur produksi masih
   GDScript. C++ paritas-teruji di CI; menyalakannya untuk pemain berarti
   mewajibkan lib per platform (dua arch Android + wasm) di setiap rilis.
   `build-android-godot.yml` belum memanggil scons; CI hanya membuild linux
   x86_64.
2. `splash_screen.py` **tidak disunting** — deviasi Godot dicatat dan dikunci
   fixture, bukan "diperbaiki" di sumber (`docs/MIGRASI_1_1.md`).
3. RNG partikel tidak diklaim paritas (§3); yang diklaim adalah **rantai**
   dengan nilai respawn terekam (fixture) dan **distribusi** rentang/warna.
4. Piksel glow (cincin logo `draw_arc`, lapisan glow judul `UiTheme.draw_glow`)
   adalah pendekatan renderer; angka geometrinya dari backend dan dikunci
   fixture. `smoothscale`/`BLEND_RGBA_MULT` pygame tidak direplika bit-per-bit.
5. `draw_preview_frame` (`:361-371`, alat debug penulis pygame) tidak diport —
   nol call site di runtime.
6. Cache (`_bg_cache`, `_logo_cache`) tidak diport sebagai cache: Godot
   menggambar 118 primitif latar per frame lewat `draw_rect` (GPU) dan
   `draw_texture_rect` memakai tekstur yang sudah di-import. Kalau profiling
   HP low-end menunjukkannya, langkah berikutnya adalah memanggang latar ke
   `ImageTexture` sekali — di luar cakupan fase ini.

## Referensi

- [`godot/gdext/mystic_splash/README.md`](../godot/gdext/mystic_splash/README.md) — struktur, cakupan API, cara build, self-test
- [`GODOT_PARITY.md`](GODOT_PARITY.md) — status paritas FASE 38 (+ fase sebelumnya)
- [`MAPS_GODOTPP.md`](MAPS_GODOTPP.md), [`LEVELS_GODOTPP.md`](LEVELS_GODOTPP.md), [`UI_THEME_GODOTPP.md`](UI_THEME_GODOTPP.md) — pola yang sama untuk modul lain
- [`MIGRASI_1_1.md`](MIGRASI_1_1.md) — aturan "sumber Python tidak disunting"
