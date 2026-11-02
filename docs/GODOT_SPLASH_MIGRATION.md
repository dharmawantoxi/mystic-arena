# Migrasi `splash_screen.py` ke Godot

Dokumen ini menjelaskan port native splash screen dari `splash_screen.py`
(pygame) ke proyek aktif `godot_rebuild/`. Python tetap menjadi sumber
kebenaran dan oracle; Godot tidak memanggil Python saat runtime.

## Berkas utama

- `tools/prepare_godot_splash.py` — exporter fail-closed. Memakai ulang
  extractor AST murni `tools/gen_splash_cpp.build_spec()` (68 kunci) tanpa
  menghasilkan C++, lalu menjalankan `SplashScreen` asli secara headless
  dengan pygame 2.6.1 untuk membuat fixture parity.
- `godot_rebuild/data/splash.json` — kontrak runtime: konstanta, urutan
  gambar, pemetaan font, default `cheap_alpha`, hash sumber, dan nomor baris
  sumber untuk setiap literal/formula.
- `godot_rebuild/tests/fixtures/splash_parity.json` — oracle: 5 timeline,
  46 partikel, 4 ukuran background, 16 kasus layout, 3 profil glow logo.
- `godot_rebuild/scripts/ui/SplashModel.gd` — timing, alpha, partikel,
  geometri logo/title/hint, garis aksen, dan kuantisasi grow half-to-even.
- `godot_rebuild/scripts/ui/SplashEffects.gd` — cache texture background,
  glow logo, dan frame logo yang sudah dikuantisasi.
- `godot_rebuild/scripts/ui/SplashView.gd` — urutan gambar dan input skip;
  clamp dt pemanggil `min(delta, 0.05)` seperti `main.py`.
- `godot_rebuild/tests/SplashParityTest.gd` — parity native terhadap fixture.
- `tools/test_godot_splash_prepare.py` dan
  `tools/test_godot_splash_parity.py` — gate Python untuk exporter/oracle.

## Semantik yang dipertahankan

- Durasi 3.0 detik; fade-in 0.4 detik; fade-out normal 0.45 detik;
  fade-out setelah skip 0.25 detik.
- `skip()` paling cepat menyelesaikan splash pada `elapsed >= 0.25`.
  Fade setelah skip diukur dari **elapsed absolut**, bukan dari waktu skip;
  skip terlambat dapat langsung membuat konten tersembunyi. Ini memperbaiki
  port lama yang mengukur fade relatif terhadap momen skip.
- Alpha keseluruhan hanya memodulasi konten dan hint. Background, partikel,
  dan glow logo tidak ikut fade.
- Background gradien + vignette source runtuh secara analitis menjadi interior
  hitam opaque mulai inset 2 px; hanya cincin luar 2 px yang menyimpan gradien.
  Tinggi batang gradien `max(1, h // 48)`; alpha vignette
  `min(255, int(2.2 * (140 - i)))`. Port memanggang background sekali per
  ukuran dan diuji terhadap sampel/hash RGB pygame.
- Partikel: 46 buah, wrap di `y < -6`, respawn `y = h + 6`, drift + sin,
  twinkle, dan palet warna sesuai source. Distribusi RNG memakai
  `RandomNumberGenerator` Godot ber-seed 1234; parity numerik menyuntikkan
  state awal dan stream respawn dari oracle, sehingga tidak mengklaim
  kesamaan stream Mersenne Twister Python.
- Logo: skala `min(340/w, 320/h, 1)`, grow 0.85→1.0 dalam 0.9 detik,
  kuantisasi 1/20 dengan pembulatan half-to-even CPython, glow radius
  `max(w,h)//2 + 30`, cincin `range(r, 0, -3)` dengan alpha `int(12*(1-g/r))`.
- Judul/tagline/hint: ukuran font 92/66/22/16 (title/title-below/sub/hint),
  teks dan anchor source, termasuk
  `Tap anywhere to skip` pada `(w//2, h-48)` dengan alpha `int(140*a)`.
  Lapisan glow judul hanya aktif ketika `cheap_alpha` True, persis seperti
  source yang kontraintuitif. Default `cheap_alpha=True` dipertahankan;
  preset visual Godot tidak menyetel ulang default ini.
- Aritmetika float memakai epsilon judul `1e-5` dan toleransi boundary
  sub-mikrodetik untuk `done` agar akumulasi `dt` GDScript tidak berbeda satu
  frame dari CPython pada ambang eksak. Ini bukan penyetelan ulang konstanta.
- Fail-closed: kontrak hilang/rusak tidak mengarang angka. SplashView selesai
  agar pengguna tetap dapat mencapai menu, dan error dicatat oleh model.

## Input

Keyboard apa pun, klik mouse, dan tombol controller apa pun memanggil
`SplashView.skip()` melalui `Main.gd`. Sentuhan memakai jalur press yang sudah
ada di port Godot; klasifikasi gesture tap/long-press mobile pygame tidak
diklaim identik.

## Perintah

```bash
python3 -m pip install pygame==2.6.1 gdtoolkit==4.5.0
python3 tools/prepare_godot_splash.py
python3 tools/prepare_godot_splash.py --check
python3 tools/test_godot_splash_prepare.py
python3 tools/test_godot_splash_parity.py
python3 godot_rebuild/tests/validate_project.py
```

`--check` membandingkan byte JSON secara eksak dan tidak menulis apa pun.
CI menjalankan gate ini di `godot-check.yml` dan `godot-rebuild.yml`.

## Batas yang jujur

- Font asli (Cinzel/Barlow) dipakai di Godot, tetapi fixture layout memakai
  metrik font palsu deterministik. Metrik raster font asli tidak diklaim
  identik dengan pygame.
- Resize logo memakai interpolasi Godot dan cache ukuran terkuantisasi;
  double-smoothscale GENERIC pygame tidak diklaim piksel-identik.
- Glow judul native menggambar font yang diskalakan/dioffset, bukan
  smoothscale + BLEND_RGBA_MULT pygame. Geometri rect dan alpha factor diuji;
  raster blur tidak diklaim identik.
- Profil alpha glow logo diuji secara aksial terhadap pygame; rasterisasi
  lingkaran penuh Godot dapat berbeda pada tepi subpixel.
- Tidak ada audio, GPU visual verification, atau benchmark adaptif
  `cheap_alpha` pygame dalam port ini.
- `assets/presplash.png` bukan bagian dari `splash_screen.py` dan tidak
  dipakai oleh port ini. Varian logo opsional `splash_logo.png`, `logo.jpg`,
  `logo.jpeg` disalin oleh `prepare_godot_main.py` bila ada.
