# PANDUAN LENGKAP — Mystic Arena dari pygame ke Google Play

Dokumen ini adalah peta jalan **dari kode desktop → APK di HP → rilis di
Play Store**, khusus untuk proyek ini. Semua angka performa di sini
adalah hasil pengukuran nyata pada kode Anda, bukan perkiraan.

**Daftar isi**

| Bagian | Isi |
|---|---|
| [0](#0-keputusan-arsitektur) | Keputusan arsitektur & kenapa |
| [1](#1-repo-github) | Menyiapkan repo GitHub |
| [2](#2-kontrol-sentuh) | Mengganti keyboard/gamepad → sentuh |
| [3](#3-optimasi-performa) | Optimasi agar tidak lag di Android |
| [4](#4-debug-di-hp) | Debug & monitoring di perangkat nyata |
| [5](#5-build-apk-lokal) | Build APK/AAB di komputer sendiri |
| [6](#6-build-otomatis-github-actions) | Build otomatis lewat GitHub Actions |
| [7](#7-aset-toko) | Aset yang wajib disiapkan |
| [8](#8-keystore--signing) | Keystore & penandatanganan |
| [9](#9-publikasi-play-store) | Publikasi di Play Console (aturan 2026) |
| [10](#10-setelah-rilis) | Setelah rilis: update & pemantauan |
| [11](#11-troubleshooting) | Error yang paling sering muncul |

---

## 0. Keputusan arsitektur

### 0.1 Jalur teknis yang dipilih

Ada tiga cara membawa pygame ke Android. Yang dipilih untuk proyek ini:

| Jalur | Hasil | Cocok? |
|---|---|---|
| **Buildozer + python-for-android + pygame-ce** ✅ | APK/AAB native, performa terbaik, bisa masuk Play Store | **DIPAKAI** |
| pygbag (WebAssembly) + WebView | mudah, tapi lambat & Play Store tidak suka "app pembungkus web" | tidak |
| Tulis ulang dengan Kivy/Godot | performa bagus, tapi 60.000 baris harus ditulis ulang | tidak |

Alasan penting: kode Anda **murni pygame** dan menggambar semua sprite
secara vektor. Buildozer memakai bootstrap SDL2 yang sama dengan
pygame di PC, jadi ~99% kode berjalan tanpa perubahan.

### 0.2 Kunci desain: resolusi logis tetap 1280×720

Kode Anda memakai koordinat absolut di mana-mana
(`SCREEN_WIDTH = 1280`, `panel_y = SCREEN_HEIGHT - 165`, dst).
Menulis ulang jadi relatif = ribuan perubahan berisiko.

Solusi yang sudah dipasang (`mobile/platform_utils.create_display()`):

```python
pygame.display.set_mode((1280, 720), pygame.SCALED | pygame.FULLSCREEN)
```

`pygame.SCALED` membuat SDL merender di 1280×720 lalu **menskalakan di
GPU** ke resolusi asli HP (mis. 2400×1080), lengkap dengan letterbox
otomatis. Efeknya:

* semua koordinat lama tetap benar — nol perubahan di 60k baris;
* koordinat mouse/sentuh **otomatis diterjemahkan balik** oleh SDL;
* HP dengan layar 1080p tidak perlu menggambar 2,4× lebih banyak
  piksel di CPU — ini penghematan besar (bisa 2-3× FPS).

### 0.3 Kunci desain: adaptor input, bukan bedah total

Semua UI lama sudah lewat satu pintu:
`game.handle_click(pos, button)` dan `game.handle_key(key)`.
Jadi lapisan sentuh baru cukup **menerjemahkan** gerakan jari ke
pemanggilan fungsi yang sama — bukan membongkar UI.

```
jari  →  mobile/touch.py  →  handle_click(pos, 1)   (ketuk)
                          →  handle_click(pos, 3)   (tahan lama)
                          →  handle_click(pos, 4/5) (geser = scroll)
      →  mobile/hud.py    →  handle_key(K_q/w/e/r)  (tombol skill)
```

---

## 1. Repo GitHub

### 1.1 Inisialisasi lokal

Repo di workspace ini **sudah** di-`git init` dan di-commit.
Yang perlu Anda lakukan tinggal menyambungkannya ke GitHub:

```bash
cd mystic-arena

# 1. Buat repo kosong di github.com (JANGAN centang "Add README")
#    misal: https://github.com/USERNAME/mystic-arena

# 2. Sambungkan
git remote add origin https://github.com/USERNAME/mystic-arena.git
git branch -M main
git push -u origin main
```

### 1.2 Repo privat atau publik?

Kode game komersial → **privat**. GitHub Actions tetap gratis
2.000 menit/bulan untuk repo privat (cukup untuk ±20 build Android).

### 1.3 Aset besar (font, suara, musik)

`.wav` musik bisa puluhan MB. Dua pilihan:

```bash
# Opsi A (disarankan): konversi ke .ogg dulu, ukuran turun 5-10x
ffmpeg -i assets/sounds/bgm_battle.wav -c:a libvorbis -q:a 4 \
       assets/sounds/bgm_battle.ogg

# Opsi B: Git LFS kalau tetap ingin menyimpan wav besar
git lfs install
git lfs track "assets/sounds/*.wav"
git add .gitattributes
```

> ⚠️ Ganti juga pemanggilan nama berkas di `SoundManager` bila Anda
> mengonversi ke `.ogg`. Ini sekaligus **mengurangi ukuran APK** —
> penting karena batas Play Store untuk satu AAB adalah 200 MB.

### 1.4 Alur kerja cabang yang disarankan

```
main         → selalu bisa dibangun; tiap push memicu build APK debug
dev          → pekerjaan harian
tag v1.0.0   → memicu build AAB release yang ditandatangani
```

```bash
git checkout -b dev
# ...kerja...
git commit -am "feat: tombol skill sentuh"
git push origin dev
# setelah diuji, merge ke main lalu:
git tag v1.0.0 && git push origin v1.0.0     # → AAB otomatis dibuat
```

---

## 2. Kontrol sentuh

### 2.1 Apa yang sudah dikerjakan

Berkas baru `mobile/touch.py`, `mobile/hud.py`, dan `main.py` versi baru
sudah menggantikan **seluruh** jalur input keyboard + gamepad:

| Input lama | Pengganti sentuh | Di mana |
|---|---|---|
| Klik kiri | **Ketuk** (< 14 px geser) | `touch.py` → `handle_click(pos,1)` |
| Klik kanan | **Tahan 450 ms** | `touch.py` → `handle_click(pos,3)` |
| Scroll wheel | **Geser vertikal** + inersia (fling) | `touch.py` → `handle_click(pos,4/5)` |
| `Q W E R` | 4 **tombol skill** kanan bawah + busur cooldown | `hud.py` |
| `H` | Tombol **SHOP** kiri bawah | `hud.py` |
| `ESC` | Tombol **⏸** kanan atas | `hud.py` |
| `SPACE` skip cinematic | Ketuk layar / tombol **LEWATI** | `main.py` |
| `R` / `N` layar akhir | Tombol **ULANGI / LEVEL LANJUT / MENU** | `hud.py` |
| `F8` FPS | Tombol **FPS** (4 mode) | `debug.py` |
| Gamepad (semua) | dihapus dari alur Android | `main.py` |

Teks petunjuk di layar juga sudah diubah:
`"PRESS SPACE TO BEGIN"` → `"TAP TO BEGIN"`,
`"CLICK TO BUILD"` → `"TAP TO BUILD"`,
`"Click to open"` → `"TAP TO OPEN"`,
`"INPUT: KEYBOARD + MOUSE"` → `"INPUT: TOUCHSCREEN"`,
serta teks tutorial di `_core.py`.

### 2.2 Aturan ergonomi yang dipakai

* **Target sentuh ≥ 48 dp.** Tombol skill dibuat radius 38-46 px logis,
  dan area sentuhnya masih diperlebar 12 px di tiap sisi
  (`TouchButton.hit_rect`) karena jempol tidak presisi.
* **Safe area.** `platform_utils.get_safe_area()` menyisakan 28 px di
  kiri-kanan supaya tombol tidak tertutup poni/kamera atau gesture bar.
* **Tangan kanan/kiri.** Skill di kanan bawah (pola kipas), shop di kiri
  bawah, pause di kanan atas — tidak saling menutupi.
* **Getar halus** 18 ms saat menekan skill (`platform_utils.vibrate`).

### 2.3 Yang sebaiknya Anda lakukan berikutnya

1. **Coba layout di PC dulu** — jauh lebih cepat daripada build APK:
   ```bash
   MYSTIC_FORCE_TOUCH=1 python main.py
   ```
   Semua tombol sentuh muncul dan bisa diklik pakai mouse.
2. **Geser posisi tombol** kalau menutupi HUD lama: semua koordinat ada
   di satu fungsi, `TouchHUD._build_layout()` di `mobile/hud.py`.
3. **Tooltip berbasis hover** (bila ada) → di HP tidak ada hover.
   Kode lama memakai `pygame.mouse.get_pos()` di 16 tempat; di Android
   nilainya = posisi sentuhan terakhir, jadi tooltip akan "menempel".
   Rekomendasi: tampilkan tooltip hanya saat jari **menyentuh**
   (`touch.active_pos is not None`).
4. **Mode kidal** (opsional): tambahkan pengaturan yang mencerminkan
   layout tombol secara horizontal — cukup satu baris di `_build_layout`.

---

## 3. Optimasi performa

### 3.1 Hasil pengukuran nyata (kode Anda, CPU desktop, headless)

**Adegan intro boss level 1** — adegan terberat di game:

| Tahap optimasi | ms/frame | FPS | Peningkatan |
|---|---|---|---|
| Kode asli | 29,43 | 34 | — |
| + perbaikan siluet boss | 15,10 | 66 | 1,9× |
| + cache font & teks | 11,14 | 90 | 2,6× |
| + `darken()`/`flash()`, vignette & gradien di-cache | **5,41** | **185** | **5,4×** |

**Waktu buka aplikasi & memori:**

| | Sebelum | Sesudah |
|---|---|---|
| Waktu sampai game siap | 3,50 s | **0,14 s** (25×) |
| RAM puncak saat start | 100 MB | **39 MB** |
| Modul boss dimuat saat start | 54 berkas (±4 MB kode) | **0** |

**Gameplay (boss + 5 menara + minion):** 6,32 → 5,69 ms/frame (HIGH),
4,77 ms/frame (preset LOW).

> Catatan: CPU HP kelas menengah ±3-5× lebih lambat daripada CPU
> desktop untuk Python murni. Angka 5,41 ms di sini kira-kira setara
> 16-27 ms di HP — artinya intro yang tadinya *tidak mungkin* 30 FPS
> di HP (29 ms × 4 = 118 ms/frame ≈ 8 FPS) sekarang masuk akal.

### 3.2 Perbaikan yang sudah dipasang

**a. Cache font + cache hasil render teks** (`mobile/perf.py`)

Profil menunjukkan `pygame.font.Font(None, 18)` dipanggil **4×/frame**
— tiap panggilan **membuka berkas font dari disk**. Lalu `font.render()`
dipanggil ~34×/frame untuk teks yang isinya tidak berubah.

`perf.install_font_cache()` menambal `pygame.font.Font` dan `SysFont`
secara global sehingga objek font dipakai ulang dan hasil `render()`
di-cache (LRU 1.500 entri). Statistik dari benchmark:

```
font_created 15 | font_reused 1206 | text_rendered 883 | text_cached 11422
```

93% panggilan teks kini gratis, **tanpa mengubah satu pun berkas lama**.

**b. `darken()` dan `flash()` menggantikan overlay layar penuh**

Pola `Surface(1280x720, SRCALPHA) → fill → blit` muncul di belasan
tempat dan jalan tiap frame. Hasil ukur untuk satu overlay layar penuh:

| Cara | ms |
|---|---|
| alokasi + fill + blit (kode asli) | 1,10 |
| blit surface yang di-cache | 0,35 |
| **`perf.darken()`** — `fill(BLEND_RGB_MULT)` | **0,17** |

`darken(surface, alpha)` menghasilkan piksel yang **identik secara
matematis** dengan blit persegi hitam beralpha
(`dst × (255−a)/255`), tapi tanpa surface tambahan.
`flash()` memakai `BLEND_RGB_ADD` untuk kilat putih.

**c. Perbaikan `_draw_boss_silhouette`** (`_render.py`)

Versi lama membuat **satu Surface seukuran layar untuk tiap sinar,
bayangan, badan, dan tiap duri mahkota** → 14+ alokasi dan 14+ blit
layar penuh tiap frame. Sekarang: **satu** overlay dari pool, sekali
blit. Pola yang sama juga sudah diperbaiki di sinar entrance boss,
sinar layar menang/kalah, dan lingkaran jangkauan menara.

**d. Vignette & gradien layar akhir di-cache**

Vignette menggambar 60 persegi layar penuh tiap frame; gradien layar
menang/kalah menggambar **720 garis tiap frame**. Keduanya statis →
digambar sekali lalu disimpan (`perf.cached_render`).

**e. Impor malas untuk 54 modul boss** (`bosses/_boss_index.py`)

`heroes/__init__.py` dulu meng-import **semua** `bosses/level*.py`
saat start hanya untuk mencari fungsi `draw_*()`. Sekarang dipakai
indeks statis dan modulnya baru dimuat saat boss itu digambar.
Regenerasi indeks setelah menambah boss:

```bash
python tools/gen_boss_index.py
```

**f. Rantai 215 `if/elif` diganti lookup dict** (`bosses/base_boss.py`)

`Boss.draw()` dulu memilih renderer lewat 215 cabang `elif` (rata-rata
107 perbandingan string per boss per frame, ±650 baris). Sekarang satu
lookup dict yang juga malas. Diuji: **215/215 boss tetap tergambar**.

**g. Preset kualitas benar-benar tersambung**

`Quality` kini memengaruhi jumlah partikel & kabut peta
(LOW 35%, MEDIUM 65%, HIGH 100%), mematikan asap dekoratif, dan
menukar `pygame.draw.aacircle` → `draw.circle` saat LOW (anti-alias
dipakai puluhan kali per unit di 57 berkas renderer).
`AdaptiveQuality` menurunkan preset otomatis kalau FPS jeblok.

**h. Surface pool** (`perf.POOL`) — surface sementara dipakai ulang,
mengurangi tekanan garbage collector (penyebab utama stutter berkala).

**i. `pygame.SCALED`** — render 720p, GPU yang menaikkan ke resolusi HP.

**j. Buffer audio 1024** + `pygame.mixer.pre_init` sebelum
`pygame.init()`.

**k. Perbaikan bug**: `main.py` lama memanggil `pygame.display.flip()`
dan `fps_counter` **dua kali** tiap frame.

### 3.3 Yang SUDAH diuji dan ternyata TIDAK menguntungkan

Supaya Anda tidak membuang waktu mengulanginya:

**Cache sprite minion** (`mobile/spritecache.py`) — idenya menggambar
tiap minion sekali lalu memakai ulang hasilnya.

* Kebenaran: **lulus** — `tools/test_spritecache.py` membuktikan hasil
  lewat cache identik piksel-per-piksel untuk 80 kombinasi.
* Kecepatan: **lebih lambat**.

| Jumlah minion | tanpa cache | dengan cache |
|---|---|---|
| 10 | 0,15 ms | 0,31 ms |
| 30 | 0,33 ms | 0,66 ms |
| 60 | 0,66 ms | 1,07 ms |

Penyebabnya: renderer minion ternyata sudah murah (±11 µs/unit),
sementara alokasi surface + blit tambahan lebih mahal daripada
menggambar ulang. Karena itu `Quality.sprite_cache = False`.
Modulnya dipertahankan sebagai alat ukur — aktifkan dengan
`MYSTIC_SPRITE_CACHE=1` dan ukur sendiri lewat
`python tools/bench_minions.py`.

### 3.4 Optimasi lanjutan yang masih tersisa

Diurutkan berdasarkan rasio manfaat/usaha:

1. **`.convert()` / `.convert_alpha()`** untuk setiap Surface yang
   di-blit berulang — SDL tidak perlu mengubah format piksel tiap blit.
2. **Kurangi partikel efek skill hero** — pola `Quality.particle_ratio`
   sudah tersedia, tinggal dipasang di `hero_skills/_bundle.py`.
3. **Batasi FPS ke 30 di perangkat lemah** (`Quality.target_fps`, sudah
   otomatis untuk preset LOW). 30 FPS stabil terasa lebih baik daripada
   45 FPS yang naik-turun, dan baterai lebih awet.
4. **`pygame.event.set_allowed()`** — izinkan hanya event yang dipakai.
5. **Sisa pola surface layar penuh** — cari lagi dengan:
   ```bash
   grep -rn "SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA" --include=*.py .
   grep -rn "screen_w, self.screen_h), pygame.SRCALPHA" --include=*.py .
   ```

### 3.5 Cara mengukur ulang setelah tiap perubahan

```bash
python tools/bench_mobile.py             # adegan intro (terberat)
python tools/bench_mobile.py --nopatch   # pembanding tanpa cache font
python tools/bench_heavy.py --quality low   # adegan gameplay
python tools/bench_heavy.py --profile       # cari hotspot baru
python tools/bench_minions.py            # skala jumlah minion
python tools/test_spritecache.py         # uji kebenaran cache sprite
```

Untuk mencari hotspot baru:

```bash
python -m cProfile -s tottime tools/bench_mobile.py 2>&1 | head -40
```

---

## 4. Debug di HP

### 4.1 Overlay di layar

Tekan tombol **FPS** (kanan atas) untuk memutar 4 mode:

| Mode | Isi |
|---|---|
| `off` | tidak tampil |
| `mini` | FPS + ms/frame |
| `full` | FPS, rincian ms (event/update/draw/flip), jumlah entitas, preset kualitas, statistik cache font, pemakaian RAM, model HP + API level |
| `graph` | `full` + grafik waktu frame 180 frame terakhir dengan garis 60/30 FPS |

Lingkaran biru mengikuti jari juga digambar — berguna untuk memastikan
area sentuh benar-benar sesuai posisi tombol.

Sebelum rilis produksi, matikan tombolnya:
```python
hud.show_debug_button = False    # di main.py
```

### 4.2 Log ke logcat

Semua `print()` Python masuk ke logcat Android:

```bash
adb devices                       # pastikan HP terdeteksi
adb logcat -c                     # bersihkan log lama
adb logcat -s python:*            # hanya log Python
adb logcat *:E                    # semua error (kalau app crash saat start)
```

Overlay debug juga mencetak ringkasan tiap 5 detik:

```
[PERF] fps=52.3 frame=19.1ms upd=3.2 draw=14.8 q=medium ent=m24/t8/h4/p12 mem=214MB
```

### 4.3 Crash log tanpa kabel

`mobile/debug.install_crash_handler()` (sudah aktif di `main.py`)
menulis traceback ke `crash_log.txt` di folder privat aplikasi:

```bash
adb shell run-as io.github.dharmawantoxi.mysticarena cat files/crash_log.txt
```

### 4.4 Uji tanpa perangkat fisik

```bash
# Emulator x86_64 lebih cepat, tapi WAJIB tambahkan arch-nya:
#   android.archs = arm64-v8a,armeabi-v7a,x86_64
# Uji akhir tetap harus di HP asli — performa emulator menipu.
```

---

## 5. Build APK lokal

### 5.1 Prasyarat

Buildozer **tidak jalan di Windows secara langsung**. Pilihan:

* **Linux / WSL2 (Ubuntu 22.04)** ← paling umum
* **Docker** (`kivy/buildozer`) ← paling bersih, tidak mengotori sistem

```bash
# Ubuntu / WSL2
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
     autoconf libtool pkg-config zlib1g-dev libncurses-dev \
     cmake libffi-dev libssl-dev build-essential ccache

python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install buildozer==1.5.0 "cython<3.0" virtualenv
```

### 5.2 Sesuaikan `buildozer.spec`

Minimal yang **wajib** diganti sebelum build pertama:

```ini
package.domain = com.namaanda      # ← applicationId tidak bisa diubah
                                   #    setelah rilis pertama!
```

Periksa juga: `title`, `version`, `icon.filename`, `presplash.filename`.

### 5.3 Build pertama

```bash
buildozer -v android debug
```

Build **pertama** mengunduh Android SDK, NDK, dan mengompilasi
Python + SDL2 + pygame-ce → **30-60 menit**. Build berikutnya 2-5 menit.
Hasil: `bin/mysticarena-1.0.0-arm64-v8a-debug.apk`.

### 5.4 Pasang & jalankan

```bash
adb install -r bin/*.apk
adb logcat -s python:*        # pantau saat aplikasi dibuka
```

### 5.5 Build AAB untuk Play Store

```bash
buildozer android release     # menghasilkan bin/*.aab
```
(Penandatanganan dijelaskan di [bagian 8](#8-keystore--signing).)

### 5.6 Cara Docker (alternatif tanpa merusak sistem)

```bash
docker run --rm -v "$PWD":/home/user/hostcwd -w /home/user/hostcwd \
  kivy/buildozer:latest android debug
```

---

## 6. Build otomatis (GitHub Actions)

Berkas `.github/workflows/build-android.yml` sudah siap:

| Pemicu | Hasil |
|---|---|
| push ke `main` / PR | **APK debug** diunggah sebagai artifact (14 hari) |
| push tag `v*` | **AAB release bertanda tangan** + GitHub Release |

Langkah aktivasi:

1. Push repo ke GitHub (bagian 1).
2. Tambahkan 4 secret di **Settings → Secrets and variables → Actions**:
   `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEYALIAS`,
   `KEYALIAS_PASSWORD` (lihat bagian 8).
3. **(Disarankan)** Tambahkan secret `DEBUG_KEYSTORE_BASE64` supaya
   semua APK debug dari CI punya tanda tangan yang sama. Ambil dari
   PC yang sudah pernah build debug:
   ```bash
   base64 -w0 ~/.android/debug.keystore   # Linux/macOS
   ```
   Tanpa secret ini, **tiap build debug dari GitHub Actions ditandatangani
   keystore debug baru** (runner selalu baru) → menginstall APK debug
   build terbaru di atas yang lama gagal dengan *"App not installed as
   package conflicts with an existing package"*. Kalau secret belum
   diisi, workflow otomatis mengunggah artefak `debug-keystore` — unduh
   sekali, simpan sebagai secret. Jangan lupa uninstall dulu APK lama
   saat beralih dari tanda tangan lama ke baru (save bisa dipulihkan
   lewat ☁ CLOUD SAVE / BACKUP).
4. Buka tab **Actions**, jalankan workflow secara manual sekali
   (`Run workflow`) untuk memanaskan cache.

Catatan: build pertama di CI ±50-70 menit; setelah cache SDK/NDK
tersimpan, ±10 menit. Batas job GitHub adalah 6 jam, jadi aman.

---

## 7. Aset toko

Siapkan sebelum mengisi Play Console:

| Aset | Ukuran / format | Catatan |
|---|---|---|
| Ikon aplikasi (dalam APK) | 512×512 PNG → `assets/icon.png` | tanpa alpha di tepi |
| Ikon Play Store | 512×512 PNG, < 1 MB | boleh sama |
| Feature graphic | **1024×500** PNG/JPG | wajib, tampil di atas listing |
| Screenshot HP | min. **2**, ideal 4-8; 16:9 landscape, min. sisi pendek 320 px | ambil dari game asli |
| Presplash | 1280×720 PNG → `assets/presplash.png` | tampil saat Python dimuat |
| Video promo | opsional, tautan YouTube | menaikkan konversi |
| Judul | maks. 30 karakter | "Mystic Arena: Tower Defense" |
| Deskripsi singkat | maks. 80 karakter | |
| Deskripsi panjang | maks. 4.000 karakter | |
| Kebijakan privasi | URL publik | **wajib**, walau game offline |

Kebijakan privasi bisa dihosting gratis di GitHub Pages dari repo ini
(`docs/privacy-policy.md` → Settings → Pages).

---

## 8. Keystore & signing

### 8.1 Membuat keystore (SEKALI SEUMUR HIDUP APLIKASI)

```bash
keytool -genkey -v -keystore mystic.keystore \
        -alias mystic -keyalg RSA -keysize 2048 -validity 10000
```

> 🔐 **Kehilangan keystore = tidak bisa memperbarui aplikasi selamanya.**
> Simpan cadangan di 2 tempat berbeda (password manager + drive
> terenkripsi). **JANGAN** commit ke Git (sudah masuk `.gitignore`).
> Aktifkan **Play App Signing** di Play Console agar Google menyimpan
> kunci penandatanganan akhir dan Anda hanya memegang upload key.

### 8.2 Menandatangani secara lokal

```bash
export P4A_RELEASE_KEYSTORE=$HOME/mystic.keystore
export P4A_RELEASE_KEYSTORE_PASSWD='passwordkeystore'
export P4A_RELEASE_KEYALIAS=mystic
export P4A_RELEASE_KEYALIAS_PASSWD='passwordalias'
buildozer android release
```

### 8.3 Menyiapkan secret untuk GitHub Actions

```bash
base64 -w0 mystic.keystore > keystore.b64   # Linux
# macOS: base64 -i mystic.keystore -o keystore.b64
```
Salin isi `keystore.b64` ke secret `KEYSTORE_BASE64`, lalu hapus
berkasnya. Isi juga `KEYSTORE_PASSWORD`, `KEYALIAS`, `KEYALIAS_PASSWORD`.

---

## 9. Publikasi Play Store

> Aturan di bawah adalah kondisi **2026**. Sumber:
> [target API level](https://developer.android.com/google/play/requirements/target-sdk),
> [closed testing 12 penguji](https://support.google.com/googleplay/android-developer/answer/14151465),
> [verifikasi developer](https://developer.android.com/developer-verification).

### 9.1 Akun developer

1. Daftar di [play.google.com/console](https://play.google.com/console)
   — biaya **$25 sekali seumur hidup**.
2. Pilih tipe akun:
   * **Personal** — wajib menjalani closed testing 12 penguji × 14 hari.
   * **Organization** (butuh D-U-N-S number) — **bebas** dari syarat itu.
     Kalau Anda punya badan usaha (CV/PT), jalur ini jauh lebih cepat.
3. Verifikasi identitas (KTP/paspor + alamat).
   ⚠️ **Khusus Indonesia**: verifikasi developer Android mulai berlaku
   **30 September 2026** di Indonesia, Brasil, Singapura, dan Thailand
   (gelombang pertama). Selesaikan verifikasi lebih awal.

### 9.2 Syarat teknis rilis 2026

| Syarat | Nilai | Status di proyek ini |
|---|---|---|
| Format upload | **AAB** (`.aab`), APK ditolak | ✅ `android.release_artifact = aab` |
| Target API | **36** (Android 16) wajib untuk submission baru sejak 31 Agu 2026 | ✅ `android.api = 36` |
| Min API | bebas; 24 mencakup >98% perangkat | ✅ `android.minapi = 24` |
| 64-bit | wajib ada `arm64-v8a` | ✅ |
| Play App Signing | wajib untuk app baru | aktifkan saat upload pertama |
| Ukuran AAB | maks. 200 MB | pantau; pakai `.ogg` |

### 9.3 Urutan pengerjaan di Play Console

1. **Create app** — nama, bahasa default, tipe **Game**, gratis/berbayar.
2. **App content** (semua wajib hijau sebelum bisa rilis):
   * Privacy policy (URL)
   * Ads — pilih "tidak ada iklan" bila memang tidak ada
   * App access — kalau semua konten terbuka, nyatakan begitu
   * Content rating — isi kuesioner (game fantasi bertarung →
     biasanya rating "Teen/12+")
   * Target audience — hati-hati bila memilih anak-anak (aturan ketat)
   * **Data safety** — game offline tanpa pengumpulan data → deklarasi
     paling sederhana; pastikan konsisten dengan permission di manifest
     (Anda hanya minta VIBRATE + WAKE_LOCK, keduanya bukan data pribadi)
   * Government apps, financial features → "tidak"
3. **Store listing** — judul, deskripsi, aset dari bagian 7.
4. **Internal testing** — unggah AAB pertama, uji sendiri (100 penguji,
   rilis instan). **Tidak dihitung** untuk syarat 14 hari.
5. **Closed testing** — inilah yang dihitung:
   * minimum **12 penguji** yang **benar-benar opt-in** (klik tautan
     dan memasang aplikasi — sekadar menambahkan email tidak dihitung)
   * **14 hari berturut-turut** tanpa putus
   * disarankan undang 20-25 orang sebagai cadangan
   * lakukan minimal 1-2 update selama periode ini; Google menilai
     "apakah pengujian benar-benar terjadi"
6. **Apply for production access** — kuesioner tiga bagian; jawab
   spesifik (siapa penguji, umpan balik apa, perbaikan apa yang Anda
   lakukan). Review biasanya ≤ 7 hari.
7. **Production** — rilis bertahap (staged rollout) 5% → 20% → 50% → 100%
   sambil memantau Android Vitals.

### 9.4 Perkiraan waktu realistis

| Tahap | Durasi |
|---|---|
| Build APK pertama berhasil | 1-3 hari (banyak trial-error) |
| Uji & poles kontrol sentuh di HP asli | 3-7 hari |
| Optimasi performa sampai stabil 30-60 FPS | 3-10 hari |
| Aset toko + kebijakan privasi | 1-2 hari |
| Closed testing (akun personal) | **14 hari (tidak bisa dipercepat)** |
| Review produksi | 1-7 hari |
| **Total realistis** | **4-6 minggu** |

---

## 10. Setelah rilis

* **Naikkan `android.numeric_version`** setiap upload — Play Console
  menolak versionCode yang sama.
* **Android Vitals** — pantau ANR rate & crash rate. Ambang "buruk":
  crash > 1,09% atau ANR > 0,47% sesi pengguna; melewatinya membuat
  aplikasi diturunkan di hasil pencarian.
* **Pre-launch report** — Google menjalankan game Anda otomatis di
  perangkat nyata dan melaporkan crash + screenshot. Gratis, sangat
  berguna untuk game pygame yang rentan masalah driver.
* **Simpan tag Git untuk tiap rilis** agar bisa reproduksi build lama.
* **Perhatikan tenggat API berikutnya**: API 37 (Android 17) akan
  diwajibkan sekitar Agustus 2027 — cukup ubah `android.api` lalu build
  ulang.

---

## 11. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| Build gagal: `Cython ... longintrepr.h` | Cython terlalu baru → `pip install "cython<3.0"` |
| Build gagal saat resep pygame-ce | Hapus cache: `rm -rf .buildozer/android/platform/build-*` lalu build lagi; atau turunkan `version` di `p4a-recipes/pygame-ce/__init__.py` ke 2.5.0 |
| APK terpasang tapi langsung tertutup | `adb logcat -s python:*`. Penyebab paling umum: berkas aset tidak ikut (`source.include_exts` kurang ekstensi), atau `import` modul yang tidak ada di Android |
| Layar hitam, hanya suara | Driver GL bermasalah → coba `set_mode` tanpa `vsync=1`, atau tambahkan `os.environ['SDL_RENDER_DRIVER']='opengles2'` sebelum `pygame.init()` |
| Sentuhan meleset dari tombol | Anda menggambar HUD di koordinat jendela, bukan koordinat logis. Semua HUD harus memakai koordinat 1280×720 |
| Sentuhan terdeteksi dua kali | SDL mengirim FINGER *dan* mouse sintesis. `TouchManager` sudah membuang salah satunya — jangan menangani MOUSEBUTTONDOWN secara terpisah di Android |
| Suara pecah / delay | Naikkan buffer `pre_init(..., buffer=2048)`, kurangi jumlah channel, konversi wav → ogg |
| Game lag setelah main 10 menit | Kebocoran surface/cache. Panggil `perf.clear_text_caches()` saat ganti level (sudah dipasang) dan cek daftar partikel yang tidak pernah dibersihkan |
| Aplikasi crash saat kembali dari background | Sudah ditangani `_handle_background()` di `main.py`; pastikan tidak ada kode lain yang mengakses surface saat app di background |
| Pasang APK gagal: `App not installed as package conflicts with an existing package` | **Tanda tangan (signature) APK baru ≠ APK yang sudah terpasang.** Penyebab umum: (a) dulu pasang APK **debug**, sekarang install APK **release** (atau sebaliknya); (b) APK debug di-build di **mesin berbeda** — termasuk **setiap build dari GitHub Actions**: runner selalu baru sehingga `~/.android/debug.keystore` dibuat ulang dan tiap APK debug CI punya tanda tangan berbeda; (c) keystore dibuat ulang/berubah; (d) build release tanpa `P4A_RELEASE_*` → Buildozer memakai keystore debug acak. Solusi cepat: simpan save dulu (Settings → ☁ CLOUD SAVE → UPLOAD, atau BACKUP → EXPORT), **uninstall** aplikasi lama, install APK baru, lalu restore. Solusi permanen agar `adb install -r` bisa update debug APK: isi secret **`DEBUG_KEYSTORE_BASE64`** (base64 `~/.android/debug.keystore`) — lihat bagian 6. Untuk release, selalu pakai keystore yang sama (`P4A_RELEASE_*` / `KEYSTORE_BASE64`) dan naikkan `android.numeric_version` tiap rilis |
| Play Console: "App bundle not signed" | Variabel `P4A_RELEASE_*` tidak terbaca saat `buildozer android release` |
| Play Console: "Target API level" | `android.api = 36` dan build ulang (bukan hanya ubah spec) |

---

## Lampiran A — Perintah cepat

```bash
# Uji layout sentuh di PC
MYSTIC_FORCE_TOUCH=1 python main.py

# Benchmark + uji gesture & HUD (tanpa layar)
python tools/bench_mobile.py

# Build & pasang APK debug
buildozer android debug && adb install -r bin/*.apk

# Pantau log
adb logcat -c && adb logcat -s python:*

# Rilis: tandai versi → CI membuat AAB
git tag v1.0.1 && git push origin v1.0.1

# Ambil crash log dari HP
adb shell run-as io.github.dharmawantoxi.mysticarena cat files/crash_log.txt
```

## Lampiran B — Checklist sebelum upload pertama

- [ ] `package.domain` sudah diganti (tidak bisa diubah lagi!)
- [ ] `assets/icon.png` 512×512 dan `assets/presplash.png` ada
- [ ] Musik dikonversi ke `.ogg`, AAB < 200 MB
- [ ] Tombol debug FPS dimatikan (`hud.show_debug_button = False`)
- [ ] Diuji di minimal 2 HP berbeda (1 kelas bawah, 1 kelas menengah)
- [ ] FPS ≥ 30 stabil di HP kelas bawah pada wave dengan boss
- [ ] Tombol back Android tidak menutup game mendadak (uji perilakunya)
- [ ] Save game tersimpan di folder privat (`get_writable_dir()`)
- [ ] Keystore dicadangkan di 2 tempat
- [ ] Kebijakan privasi online dan URL-nya valid
- [ ] `android.numeric_version` unik untuk tiap upload
- [ ] Secret `DEBUG_KEYSTORE_BASE64` diisi (supaya APK debug dari CI
      bisa di-update dengan `adb install -r` tanpa uninstall)

## Lampiran C — Backup save lokal (export/import)

Selain Android Auto Backup (Google Drive), game punya backup lokal
**tanpa internet** ke folder publik:

```
Download/MysticArena/mystic_arena_backup.json
```

Implementasi: `backup_manager.py` (format file, checksum sha256,
semua backend tulis/baca). Tiga fitur:

1. **Auto-export** — tiap `SaveManager.save()` menulis salinan backup
   di background (non-blocking, tanpa dialog, gagal = hanya log).
   - Android 10+ : `MediaStore.Downloads` via pyjnius, tanpa permission.
   - Android 7-9 : path publik + `WRITE_EXTERNAL_STORAGE`
     (dideklarasikan `maxSdkVersion=28`, jadi tidak pernah diminta di
     Android 10+). Auto-export **tidak pernah** memunculkan dialog
     izin — kalau izin belum ada, export dilewati.
   - Desktop : folder `~/Downloads` (override: env `MYSTIC_BACKUP_DIR`).
2. **Deteksi restore** — saat game dibuka dan semua slot kosong
   (indikasi install ulang), backup dicari di background; kalau ada,
   dialog "BACKUP FOUND" muncul di main menu — satu ketukan RESTORE
   memulihkan semua slot + settings.
3. **Tombol manual** — Settings → bagian **BACKUP**: EXPORT (dengan
   konfirmasi kalau backup di disk berisi data lebih baru) dan IMPORT
   (selalu konfirmasi karena menimpa save yang ada; file korup /
   checksum salah ditolak dengan pesan jelas).

Catatan jujur soal scoped storage: di Android 10+, setelah UNINSTALL
kepemilikan file MediaStore hilang, sehingga install baru tidak selalu
bisa membacanya kembali — di kasus itu Auto Backup Google Drive adalah
jalur restore utama, dan file Download tetap berguna sebagai arsip
yang bisa dipindah manual (file manager / PC).

Uji tanpa HP:

```bash
python3 tools/test_backup_manager.py   # 44 pemeriksaan, headless
```

## Lampiran D — Cloud Save (Google Play Games Saved Games)

Cloud save melengkapi Auto Backup: selain backup lokal & Auto Backup
Google Drive, progres juga disimpan ke **Google Play Games Saved
Games** milik akun Google. Ini yang membuat save tetap ada setelah
UNINSTALL dan bisa dipulihkan di HP baru (dengan akun Google yang
sama).

Bagian kode:

- `mobile/cloud_save.py` — manajer cloud: init bridge, cek sign-in,
  auto-upload tiap save, upload/download payload, conflict check, poll
  status file dari Java. Berjalan aman (no-op) di PC/CI.
- `src/io/github/dharmawantoxi/mysticarena/CloudSaveBridge.java` —
  bridge Java: Play Games Services v2 (`PlayGamesSdk`,
  `GamesSignInClient`, `SnapshotsClient`). Semua operasi async lewat
  Task, hasilnya ditulis ke file `cloud_status.json` yang di-poll
  Python — tidak perlu listener/interface Java dari Python.
- `_system.py` — `SaveManager.save()` memanggil auto-upload cloud
  setelah menulis save lokal (non-blocking, gagal hanya log).
- `_core.py` — Settings → **☁ CLOUD SAVE** (SIGN IN / UPLOAD /
  DOWNLOAD) + dialog restore cloud saat slot lokal kosong.

### Setup di Google Play Console (saat siap rilis ke Play Store)

1. **Play Console → Game services** (atau buat game di
   <https://play.google.com/console> → Game services) → pilih game.
2. Aktifkan **Saved Games** (toggle di tab Features/Configuration).
3. Salin **Project ID** (angka, di halaman **Configuration**).
4. Pastikan **OAuth clients** sudah ada:
   - Android client dengan *package name*
     `io.github.dharmawantoxi.mysticarena` (sesuai `buildozer.spec`).
   - SHA1 yang dipakai harus mencocokkan **App signing key** di Play
     Console (untuk release) atau **debug keystore** (untuk APK uji).
     Kalau tidak cocok, sign-in akan gagal di perangkat.

### Memberikan Project ID ke build

p4a hook (`tools/p4a_hooks.py`) menaruh meta-data
`com.google.android.gms.games.APP_ID` + resource `game_services_project_id`
hanya jika Project ID tersedia:

- **GitHub Actions**: tambahkan **repository secret**
  `MYSTIC_GAMES_PROJECT_ID` (nilai: angka Project ID). Build berikutnya
  otomatis memakainya.
- **Build lokal**:
  ```bash
  MYSTIC_GAMES_PROJECT_ID=123456789012 buildozer android debug
  # atau
  MYSTIC_GAMES_PROJECT_ID_FILE=~/mystic_games_id.txt buildozer android debug
  ```

Jika tidak diset, aplikasi tetap build & jalan; cloud dalam mode
NONAKTIF (tidak crash) dan 3 jalur penyimpanan lama tetap dipakai.

### Uji

```bash
python3 tools/test_cloud_save.py      # 18 pemeriksaan headless (desktop)
python3 tools/test_backup_manager.py  # backup lokal tidak terpengaruh
```

Untuk uji di HP (setelah APP_ID diset): masuk Play Games → buka game →
tampilkan Settings → ☁ CLOUD SAVE → SIGN IN → UPLOAD → hapus aplikasi →
pasang ulang → masuk akun sama → dialog "CLOUD SAVE FOUND" → RESTORE.

