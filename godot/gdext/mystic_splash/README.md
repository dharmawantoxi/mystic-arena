# Mystic Splash GDExtension (godot++)

Port `splash_screen.py` (lapisan **MODEL** splashscreen pembuka: timing/fade,
gerak partikel, gradien + vignette latar, geometri logo + cincin glow, glow
judul + garis aksen, hint skip) ke Godot C++ GDExtension.

Dokumen status paritas: [`docs/AUDIT_ULANG_DARI_AWAL.md`](../../../docs/AUDIT_ULANG_DARI_AWAL.md)
(FASE 38) dan [`docs/AUDIT_ULANG_DARI_AWAL.md`](../../../docs/AUDIT_ULANG_DARI_AWAL.md).
**Status: generator, oracle pygame, self-test C++ tanpa engine, backend
GDScript + saklar loader, dan dua scene paritas engine SEMUA hijau. Flag
`mystic/splash/use_gdext_splash` tetap `false` (default produksi = GDScript),
jadi tidak ada perilaku pemain yang berubah sampai flag itu dinyalakan.**

## Tujuan

- **Satu sumber** — `src/splash_processor.{h,cpp}` + `selftest/splash_dispatch.inc`
  dibangkitkan dari AST `splash_screen.py` (`tools/gen_splash_cpp.py`), bukan
  ditulis tangan. Setiap angka (durasi 3.0, fade in 0.4 / fade out 0.45 /
  skip 0.25, ambang judul 0.5 + ramp 0.6, 46 partikel, 48 batang gradien,
  70 bingkai vignette, cincin glow langkah −3, lapisan glow `[(24,1),(14,2),(8,3)]`,
  fill `int(alpha*0.28)`, aksen `0.85`/gap `+18`/panjang 46/lebar 2, hint
  margin 48 alpha 140) datang dari AST, bukan salinan.
- **Yang diport hanya yang deterministik** — angka, geometri, dan predikat.
  Piksel (`pygame.draw`, `Surface`, cache latar) dan **metrik font** tetap di
  renderer (`godot/scenes/ui/SplashScreen.gd`); lebar teks dikirim sebagai
  argumen (`accent_gap`, `title_glow_surface`) supaya kedua backend memakai
  angka yang sama tanpa bergantung font engine (pola oracle `ui_theme` FASE 31).
- **RNG partikel TIDAK diklaim paritas** — pygame memakai RNG global tak
  ber-seed, jadi tidak ada stream yang bisa direproduksi. Godot memakai seed
  tetap `777` (`SplashScreen._ready`) supaya boot deterministik; nilai respawn
  `x` dikirim pemanggil sebagai argumen `particle_advance`, dan fixture merekam
  nilai `random.uniform` pygame yang sebenarnya (di-spy) supaya RANTAI 120
  langkah tetap bisa dibandingkan bit-dekat.
- **Fail-hard** — generator MENOLAK (bukan menebak) kalau literal/ekspresi yang
  dibutuhkan hilang atau berubah bentuk.

## Struktur

```
godot/gdext/mystic_splash/
  SConstruct                          # output -> ../../addons/mystic_splash/bin/
  src/register_types.{h,cpp}          # entry mystic_splash_library_init (level SCENE)
  src/splash_processor.h              # GENERATED — class MysticSplash : RefCounted
  src/splash_processor.cpp            # GENERATED — 62 fungsi ter-bind
  selftest/godot_stub.hpp             # stub Variant/String/Color/Rect2/Vector2 (BUKAN bagian lib)
  selftest/splash_selftest.cpp        # harness stdin TAB — menjalankan .cpp di luar engine
  selftest/splash_dispatch.inc        # GENERATED — tabel perintah (wajib 1:1 dengan API)
  selftest/shim/godot_cpp/**          # header kosong: include godot-cpp jadi no-op
godot/addons/mystic_splash/
  mystic_splash.gdextension           # kunci debug/release -> berkas template_*
  bin/                                # hasil build (di-gitignore kecuali .gitkeep)
godot/scripts/ui/SplashModel.gd       # kembaran GDScript (fallback default)
godot/scripts/ui/SplashBackend.gd     # saklar backend (pola MapDBLoader/LevelDBLoader)
godot/scenes/ui/SplashScreen.gd       # renderer: SEMUA angka lewat SplashBackend
godot/tests/SplashParityTest.{gd,tscn}        # fixture vs backend GDScript
godot/tests/SplashGdextParityTest.{gd,tscn}   # fixture vs backend C++ + A/B
tools/gen_splash_cpp.py               # Python AST -> C++ (+ --check)
tools/test_godot_splash_parity.py     # oracle pygame ASLI -> fixture + audit wiring
tools/test_splash_cpp_selftest.py     # compile + jalankan C++ tanpa engine
```

`src/splash_processor.{h,cpp}` dan `selftest/splash_dispatch.inc` adalah **hasil
generate** — jangan disunting tangan. Ubah `tools/gen_splash_cpp.py`, lalu:

```bash
python3 tools/gen_splash_cpp.py          # regenerasi (3 berkas)
python3 tools/gen_splash_cpp.py --check  # CI: berkas ter-commit harus identik
```

## Cakupan API (62 fungsi, 1 modul)

| Kelompok | Fungsi |
| --- | --- |
| meta | `module_names`, `module_names_string`, `api_signature` |
| konstanta | `game_name`, `tagline`, `hint_text`, `splash_duration`, `logo_paths`, `accent`, `accent_2`, `text_main`, `text_dim`, `gradient_stops`, `particle_colors`, `font_sizes`, `font_fallback_sizes`, `font_styles`, `particle_count`, `particle_ranges` |
| partikel | `particle_move`, `particle_wrapped`, `particle_wrap_y`, `particle_advance`, `particle_twinkle`, `particle_channel`, `particle_draw_color`, `particle_draw_radius`, `particle_draw_pos` |
| timing & state | `fade_in`, `fade_out_normal`, `fade_out_skip`, `overall_alpha`, `overall_alpha_godot`, `title_alpha`, `is_done`, `is_done_godot`, `draw_visible`, `title_alpha_drawn`, `timings` |
| latar | `bg_step_h`, `bg_band_count`, `bg_band_rect`, `bg_band_color`, `bg_bands`, `vignette_frames` |
| konten & logo | `content_center`, `logo_center_y`, `logo_scale`, `logo_base_size`, `logo_grow_quant`, `logo_grow_size`, `logo_glow_radius`, `logo_glow_rect`, `logo_glow_rings`, `logo_offsets` |
| glow judul + aksen | `title_glow_layers`, `title_glow_surface`, `title_glow_fill`, `accent_gap`, `accent_lines` |
| hint | `hint_pos`, `hint_alpha` |

`module_names()` + `api_signature()` (`splash_v1:1mod:62fn:`) dipakai loader
untuk membuktikan backend C++ benar-benar aktif (baris log
`GDExtension MysticSplash aktif` di-require CI).

**Tipe balik partikel = Dictionary of double, BUKAN `Vector2`.** `Vector2` di
Godot 4 memakai `float` (32-bit) untuk `x`/`y` pada build default, jadi
melewatkan posisi partikel lewat `Vector2` akan membulatkan rantai 120 langkah
dan mematahkan paritas; `particle_move`/`particle_advance` mengembalikan
`{"x": .., "y": .., "wrapped": ..}` sebagai double, dan `Vector2` hanya dipakai
untuk posisi gambar yang sudah di-`int()` (`particle_draw_pos`).

## Build lib

```bash
cd godot/gdext/mystic_splash
ln -s ../godot-cpp godot-cpp        # atau: git clone -b godot-4.3-stable --depth 1 \
                                    #   https://github.com/godotengine/godot-cpp godot-cpp
scons platform=linux target=template_debug -j"$(nproc)"
# hasil: godot/addons/mystic_splash/bin/libmystic_splash.linux.template_debug.x86_64.so
```

CI (`.github/workflows/godot-gdext.yml`) memakai `optimize=none debug_symbols=no`
dan memverifikasi: `nm -D --defined-only | grep " T mystic_splash_library_init"`
(entry) **plus** string khas yang tahan strip (`splash_v1:1mod:62fn:`,
`MysticSplash`) — bukan `nm -D` untuk nama kelas (visibility default godot-cpp
`hidden`) dan bukan symbol table statis (`.so` di-strip `-s`).

Menyalakan jalur C++ (opt-in):

```ini
; godot/project.godot
[mystic]
splash/use_gdext_splash=true
```

Tanpa lib di `addons/mystic_splash/bin/`, `SplashBackend` jatuh ke
`SplashModel.gd` senyap (satu baris log), jadi flag `true` di mesin tanpa
compiler tidak merusak apa pun.

## Self-test tanpa engine (yang menjaga paritas)

```bash
python3 tools/test_splash_cpp_selftest.py     # butuh g++ saja, ±10 detik
```

Harness menyala-nyalakan `splash_processor.cpp` APA ADANYA lewat
`selftest/godot_stub.hpp` (header asli ikut di-parse; include godot-cpp
diarahkan ke shim kosong), lalu membandingkan balasannya dengan fixture
`godot/tests/fixtures/splash_parity.json` yang direkam **SplashScreen pygame
ASLI** oleh `tools/test_godot_splash_parity.py` (SDL dummy, font palsu
7 px/karakter karena metrik TTF asli tidak deterministik, `TrackSurface` sebagai
`screen` karena `pygame.Surface.blit` tidak bisa di-monkeypatch):

- **1585 cek (1580 tanpa checkout godot-cpp) / 6524 perintah**: konstanta + timing, timeline 4 skenario × 200
  frame (`title_alpha`, `_overall_alpha()`, `done`, `draw_visible`, varian
  semantik Godot lama), **rantai 46 partikel × 120 langkah** (posisi akhir +
  respawn RNG pygame yang di-spy), 48 batang gradien + 70 bingkai vignette,
  tabel grow logo 10 baris + 64 cincin glow, 3 permukaan glow judul + 5 fill +
  4 baris aksen, hint;
- **closed-world**: jumlah entri tabel perintah == jumlah `bind_static_method`
  == deklarasi `.h`, setiap fungsi ter-bind wajib punya perintah uji, tidak ada
  perintah di luar tabel, id unik;
- **audit wiring**: entry symbol, `.gdextension`, `.gitignore`, rujukan kedua
  workflow, allowlist SEMPIT `godot_log_gate`, setting `project.godot` default
  `false`, dan bentuk cek isi `.so` yang benar.

Kalau ada checkout godot-cpp asli (`GODOT_CPP_DIR`, `godot/gdext/godot-cpp`,
atau `/tmp/godot-cpp`) dan `gen/include`-nya sudah dibangkitkan, skrip juga
mengompilasi `splash_processor.cpp` + `register_types.cpp` dengan
`-fsyntax-only` terhadap header **asli** (penangkap bug yang lolos dari stub,
mis. `color.r8()` alih-alih `color.get_r8()`) lalu meng-compile+**link**+
**strip** `.so` probe dengan flag default godot-cpp dan mengulang cek langkah
"Build mystic_splash".

Oracle-nya sendiri (613 cek, butuh `pygame-ce`) juga mengunci **kembaran
GDScript** (`SplashModel.gd`: 62 fungsi + konstanta + `API_SIGNATURE`),
**permukaan API tiga sisi** (bind C++ == routing `SplashBackend.gd` ==
deklarasi `.h`), **arity tiap panggilan `Backend.*`** di
`SplashScreen.gd` + kedua scene uji (gdparse hanya memeriksa sintaks; Godot
memeriksa arity lintas berkas saat scene dimuat), **ruang lingkup identifier**
(nama `ALL_CAPS` telanjang di lima berkas splash `.gd` harus terdeklarasi di
berkas itu atau ada di daftar global engine eksplisit — penangkap salah ketik
konstanta semacam `GROW_GROW` vs `GLOW_GROW` yang membuat Godot menolak
`--import` dan menyeret `Main.gd` gagal compile), **semantik argumen sweep**
(`bg_band_rect`/`bg_band_color` menerima **y piksel**, bukan indeks batang —
arity-nya sah sehingga audit arity buta; 46 dari 48 batang sempat keluar
berwarna batang 0 di CI), dan kesegaran fixture.

## Scene paritas engine

```bash
godot --headless --path godot res://tests/SplashParityTest.tscn --quit-after 400
godot --headless --path godot res://tests/SplashGdextParityTest.tscn --quit-after 400
```

- `SplashParityTest` — fixture vs `SplashModel.gd` (backend dipaksa
  `gdscript`), ditutup smoke test scene `SplashScreen` asli (fade in → `skip()`
  → signal `finished`). Jalan di `godot-check.yml` (tanpa compiler).
- `SplashGdextParityTest` — memaksa `gdext`, **GAGAL (bukan skip)** kalau lib
  belum dibuild, lalu menjalankan baterai yang sama lewat `MysticSplash`
  ditambah **A/B backend**: seluruh permukaan API dikumpulkan dua kali (C++
  lalu GDScript) dan dibandingkan kunci demi kunci lewat `str(Variant)`,
  sehingga urutan kunci `Dictionary`, tipe nilai, dan presisi double ikut
  terkunci. Jalan di `godot-gdext.yml` (require `PASS` + baris
  `GDExtension MysticSplash aktif`).

## Temuan port yang ditutup FASE 38

1. **Latar HITAM pekat, bukan gradien ungu tipis.** Loop vignette pygame
   (`for i in range(140, 0, -2)`, alpha `min(255, int(2.2*(140-i)))`) menjenuh
   ke 255 pada 12 bingkai terakhir (`i <= 24`), jadi interior layar hitam dan
   hanya rim 2 px yang menampakkan gradien. Renderer Godot kini menggambar 48
   batang + 70 bingkai apa adanya dari backend (urutan luar→dalam membuat
   bingkai terakhir menimpa interior, sama seperti pygame); fixture menyimpan 9
   probe piksel hasil render asli untuk menguncinya.
2. **Skip memakai elapsed TOTAL.** `splash_screen.py:151,172` membandingkan
   `self.elapsed` (bukan timer sejak skip) dengan `0.25`, dan `skip()` hanya
   menyetel bendera — `done` baru dihitung `update()` frame berikutnya. Port
   lama memakai `_skip_t`; semantik lama tetap tersedia di backend sebagai
   `overall_alpha_godot`/`is_done_godot` supaya A/B harness bisa menunjuk
   bedanya. Fixture merekam DUA bendera skip per baris (saat `update()` dan
   saat alpha direkam) agar ambang ini tidak bisa "lulus" karena kebetulan.
3. **`elapsed` tidak boleh dibulatkan.** pygame mengakumulasi `dt`, sehingga
   `t` frame 180 = `2.9999999999999996 < 3.0` dan `done` masih `False`.
   Fixture menyimpan elapsed presisi penuh; pembulatan 9 digit membalik hasil
   ambang batas (tertangkap saat pengembangan self-test).
4. **Cincin glow melangkah −3.** `range(glow_r, 0, -3)` — generator yang
   menyimpan `+3` membuat `logo_glow_rings` di C++ loop tak berujung (OOM).
   Arah langkah kini bagian dari spec, dan kedua scene uji mengunci 64 cincin
   yang menurun.

## Regenerasi fixture

```bash
python3 tools/test_godot_splash_parity.py --write-fixture   # butuh pygame-ce
```

Fixture wajib segar: oracle membandingkan rekaman baru dengan berkas
ter-commit dan GAGAL kalau `splash_screen.py` berubah tanpa regenerasi.
