# Verifikasi GDExtension di lokal — tanpa menunggu GitHub Actions

> **Jawaban singkat:** ada. Sebagian besar yang diperiksa
> `.github/workflows/godot-gdext.yml` **tidak butuh godot-cpp, tidak butuh
> compiler engine, dan tidak butuh Actions** — cukup `python3` + `g++`, dan
> selesai dalam **±25 detik**. Satu perintah:
>
> ```bash
> tools/gdext_local_check.sh          # L0-L2: ±25 detik, tanpa godot-cpp
> ```
>
> Dan setelah godot-cpp terkompilasi **sekali**, seluruh lapis yang bisa
> dilakukan di luar engine (L0-L4, enam lib + build `.so` sungguhan) selesai
> dalam **±64 detik** — bandingkan ±39 menit di CI.
>
> Workflow CI tetap perlu, tapi hanya untuk **satu hal** yang memang tidak bisa
> dilakukan di luar engine: memuat lib `.so` ke Godot 4.3 sungguhan (L5).

Semua angka di dokumen ini **diukur sungguhan** di sandbox 2 core / 3 GB RAM
(2026-09-14), jadi mesin developer biasa akan lebih cepat.

---

## 1. Kenapa CI terasa lama (dan bagian mana yang sebenarnya lama)

`godot-gdext.yml` membangun **enam lib berurutan** dalam satu job:

| Tahap CI | Biaya | Bisa di lokal? |
| --- | --- | --- |
| Checkout + setup-python | ±20 detik | — |
| 7× generator `--check` | **< 1 detik** | ✅ |
| Paritas statis levels + maps | **± 7 detik** | ✅ |
| 5× self-test C++ (stub Variant, `g++`) | **± 30 detik** | ✅ |
| Clone godot-cpp (cache miss) | ±30 detik | ✅ sekali saja |
| **Compile godot-cpp (969 objek + link `.a`)** | **±10 menit** (catatan workflow; di sandbox 2 core ±8 menit) | ✅ **sekali saja**, lalu tersimpan di `godot/gdext/godot-cpp` |
| **Build 6 lib (scons + link)** | **±6-9 menit per lib di runner** → total ±39 menit | ✅ inkremental |
| Unduh Godot 4.3 | ±20 detik (di-cache) | ✅ sekali saja |
| Import project + 8 scene tes | ±5 menit | ✅ |

Artinya **±85% waktu CI habis di langkah yang hasilnya deterministik**:
mengompilasi godot-cpp dan tabel C++ hasil *generate* yang isinya tidak berubah
kecuali generator/oracle-nya berubah. Dan **langkah termurah justru yang paling
sering menangkap bug** — lihat §3.

---

## 2. Enam lapis verifikasi, dari yang termurah

`tools/gdext_local_check.sh` menjalankan lapis yang sama dengan CI, dengan
perintah yang sama, urut dari yang paling murah. Berhenti di lapis berapa pun
lewat `--lapis N` (atau `--lib <nama>` untuk satu lib saja). Keluarannya
ringkasan `OK`/`GAGAL`/`LEWAT` + waktu per langkah; exit code 0 hanya kalau
tidak ada yang GAGAL — jadi bisa dipasang di pre-push hook.

| Lapis | Isi | Butuh | Biaya (2 core) | Menangkap apa |
| --- | --- | --- | --- | --- |
| **L0** | `tools/gen_*.py --check` — `.h`/`.cpp`/`HeroSkillKit.gd` ter-commit harus byte-identik dengan hasil transpile AST | `python3` | **< 1 detik** | data/tabel C++ **basi** (oracle Python berubah, generator tidak dijalankan ulang) |
| **L1** | `test_godot_level_data_parity.py` (5.458 cek), `test_godot_map_data_parity.py` (18.946 cek) | `python3` | **± 7 detik** | nilai/tipe/urutan kunci tidak cocok antar oracle ↔ fixture ↔ literal C++ ↔ `*.json`; **wiring closed-world** (loader, autoload, `project.godot`, `.gdextension`, `.gitignore`, kedua workflow, allowlist log gate); arity helper di scene tes |
| **L2** | 5× `test_*_cpp_selftest.py` — **mengeksekusi** `*_processor.cpp` apa adanya lewat stub `Variant` (`godot/gdext/*/selftest/`) | `g++` saja | **± 20 detik** (levels 253 cek, maps 19.834, ui 213, mobile 1.564, splash 1.580) | **logika** helper C++ (bukan cuma data): `row_index`, `get_level_config`, `is_level_unlocked`, `get_next_level`, `py_contains`, kurva path, dekorasi + **RNG MT19937 bit-eksak**, timeline splash, gesture mobile; closed-world tabel perintah == `bind_static_method` == deklarasi `.h` |
| **L3** | `-fsyntax-only` + compile/link/strip `.so` **probe** terhadap header godot-cpp **asli** (otomatis aktif kalau `godot/gdext/godot-cpp` ada) | `g++` + `gen/include` | **± 20 detik** | API godot-cpp yang **salah nama/tidak ada** — kelas bug yang lolos dari stub karena stub punya API sendiri |
| **L4** | `scons` sungguhan → `.so` per lib + `nm -D` entry symbol + `strings` api_signature | `scons`, godot-cpp terkompilasi | **6 menit lib pertama bila godot-cpp belum terkompilasi**; **±10 detik/lib** setelah hangat | lapisan **binding + link**: `ClassDB::bind_method`, `entry_symbol`, `symbols_visibility=hidden`, `.so` ter-strip |
| **L5** | `godot --headless --import` + 8 scene tes (`*GdextParityTest` dipaksa backend `gdext`, plus baseline GDScript) lewat `godot/tools/godot_log_gate.py` | binary Godot 4.3 | **± 5 menit** | lib benar-benar **termuat engine**; A/B `str(Variant)` seluruh permukaan API; replay fixture oracle pygame/Python di dalam scene produksi |

**Default skrip = L0-L2** karena itulah rasio tangkapan/biaya terbaik:
**25 detik** (hangat) / 38 detik (dingin, pertama kali) untuk ±27.000 cek.

### Hasil ukur di sandbox 2 core / 3 GB (2026-09-14)

| Perintah | Kondisi | Waktu |
| --- | --- | --- |
| `tools/gdext_local_check.sh` | tanpa godot-cpp sama sekali | **25 detik** |
| `tools/gdext_local_check.sh --lapis 3` | godot-cpp sudah ada (header jadi) | **±45 detik** |
| `tools/gdext_local_check.sh --lapis 4` | **hangat** — 6 lib + 6 `.so` + `nm`/`strings` | **64 detik** |
| `tools/gdext_local_check.sh --lib levels --lapis 4` | **dingin** — termasuk compile godot-cpp (969 objek) + link `.a` | 6 menit 1 detik |
| `gdparse` 160 berkas `.gd` (`--gdsyntax`) | — | 8 detik |
| `godot-gdext.yml` di Actions | cache-hit godot-cpp, 6 lib serial | ±39 menit |

`.so` yang dihasilkan lokal identik perannya dengan CI (ukuran 973 KB-1,6 MB,
`entry_symbol` diekspor dinamis, `api_signature` tahan strip):

```text
973K libmystic_levels...so   1.2M libmystic_maps...so    1.1M libmystic_mobile...so
1.6M libmystic_skills...so   1.1M libmystic_splash...so  1.2M libmystic_ui...so
```

---

## 3. Bukti lapis murah benar-benar menangkap bug (diukur, bukan diklaim)

Dua bug disuntik sengaja ke working tree, lalu dipulihkan lagi dengan
`git checkout`:

**Bug A — data oracle berubah tanpa regenerasi** (kelas bug paling umum:
sunting `levels/level_data.py`, lupa menjalankan generator).
`"meta_gold_reward_win": 3000` → `3100` di level 1:

```text
GAGAL L0 gen_levels_cpp.py --check                        (0 detik)
GAGAL L1 test_godot_level_data_parity.py                  (0 detik)
      FAIL: levels.json[0] (level 1).meta_gold_reward_win 3000 != 3100
      FAIL: kLevels[0]      (level 1).meta_gold_reward_win 3000 != 3100
      FAIL: fixture level_data.json BASI — jalankan ... --write-fixture
GAGAL L2 test_levels_cpp_selftest.py                      (1 detik)
      FAIL: row:00, allrow:00, config:04, config:16  (4 dari 253 cek)
```

Tertangkap di **tiga lapis sekaligus dalam 1 detik**, dengan pesan yang
menyebut level + field + nilai. Di CI bug yang sama baru ketahuan setelah
clone + compile godot-cpp, yaitu **menit ke-10 atau lebih**.

**Bug B — API godot-cpp salah nama** (kejadian nyata PR #234: `color.r8()`
padahal godot-cpp 4.3 hanya punya `color.get_r8()`):

```text
$ g++ -std=c++17 -fsyntax-only -I godot-cpp/include -I godot-cpp/gen/include ...
error: 'struct godot::Color' has no member named 'r8'      (0,9 detik)

$ GODOT_CPP_DIR=$PWD/godot/gdext/godot-cpp python3 tools/test_ui_cpp_selftest.py
[ui_selftest] FAIL: ui_selftest.cpp gagal dikompilasi
```

Tertangkap di **L2 maupun L3 dalam < 1 detik** (stub UI ternyata ikut menolak
`r8()`; header asli memberi pesan "did you mean 'r'?"). Inilah yang dimaksud
catatan `docs/AUDIT_ULANG_DARI_AWAL.md`: tiga kegagalan nyata PR #234 kini ketahuan
lokal dalam ±10 detik, bukan ±30 menit siklus CI.

---

## 4. Persiapan sekali saja

### Linux / macOS

```bash
# alat dasar
sudo apt install g++ git unzip          # macOS: xcode-select --install

# python: scons (L4), gdtoolkit (gdparse), pygame-ce (oracle penuh)
python3 -m venv .venv && source .venv/bin/activate
pip install scons "gdtoolkit==4.*" "pygame-ce==2.5.*" pillow numpy

# godot-cpp: di-clone + di-symlink OTOMATIS oleh skrip saat --lapis 3/4
# (kalau mau manual, lihat §6)

# Godot 4.3 untuk L5 — diunduh otomatis ke ~/.cache/mystic-arena, atau:
python3 tools/godot_debug_run.py --download --godot-version 4.3 --dry-run
```

`.venv/` dan `~/.venv-mystic/` (venv milik `.devcontainer/setup.sh`)
dideteksi otomatis oleh skrip; kalau tidak ada, dipakai `python3` di `PATH`.

### Windows

L4/L5 butuh toolchain POSIX. Pilih salah satu:

* **MSYS2 / MinGW-w64**: `pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-scons`,
  lalu `scons platform=windows target=template_debug` (nama `.so` jadi `.dll`;
  skrip ini memeriksa nama berkas linux, jadi pakai L0-L2 saja di Windows dan
  serahkan L4 ke CI/WSL);
* **WSL2**: sama persis dengan Linux di atas — ini jalur paling tanpa gesekan;
* **Codespaces**: lihat §5, nol instalasi.

L0-L2 (yang paling berharga) hanya butuh Python + compiler apa pun, jadi di
Windows pun bisa lewat `python tools/test_levels_cpp_selftest.py` dsb. —
skrip bash-nya hanya pembungkus.

---

## 5. Tiga cara pakai, pilih sesuai kebutuhan

### A. Sebelum setiap push — ±25 detik (disarankan jadi kebiasaan)

```bash
tools/gdext_local_check.sh                    # L0-L2, semua lib
tools/gdext_local_check.sh --lib levels       # hanya lib yang disentuh
tools/gdext_local_check.sh --gdsyntax         # + gdparse 160 berkas .gd (±8 detik)
```

Kalau hijau, kemungkinan besar CI hijau untuk semua kegagalan **data/logika**.
Yang tersisa hanya risiko lapisan binding (L4) dan engine (L5).

### B. Setelah menyentuh generator / oracle — ±10 menit sekali, lalu cepat

```bash
tools/gdext_local_check.sh --lapis 4          # + build .so sungguhan
```

Run pertama membayar compile godot-cpp — 6 menit 1 detik total untuk
`--lib levels --lapis 4` di 2 core, sudah termasuk clone, compile 969 objek,
link `.a`, dan build lib-nya. **Setelah itu objek build tersimpan** di
`godot/gdext/godot-cpp` (gitignored) sehingga:

* **enam lib sekaligus hanya ±64 detik** (hasil ukur) — scons memverifikasi
  signature tiap target, jadi yang tidak berubah tidak dikompilasi ulang;
* mengubah satu tabel C++ → scons hanya mengompilasi ulang berkas itu.

> **Jangan jalankan dua invocation `--lapis 4` bareng.** godot-cpp dipakai
> bersama semua lib, jadi dua scons yang membongkar-pasang objek di
> `gen/src/` saling merusak: link `.a` gagal dengan
> `ar: ...stream_peer_tcp...o: No such file or directory` (terjadi sungguhan
> saat mengukur dokumen ini, dan bukan kerusakan permanen — cukup jalankan
> ulang). Skrip memasang kunci `/tmp/gdext-local-check-<uid>.lock` dan keluar
> dengan kode 3 kalau ada invocation lain yang masih hidup. Jalankan **semua**
> lib dalam satu invocation, jangan paralel.

### C. Setara penuh dengan CI — tanpa memakai kuota Actions

```bash
tools/gdext_local_check.sh --lapis 5          # = --all
```

Menjalankan `--import` (di sinilah `.gdextension` + lib `.so` **dimuat
engine**), lalu 8 scene tes dengan `godot_log_gate.py` dan penanda wajib yang
sama dengan langkah 6-13 workflow — termasuk penanda
`GDExtension MysticLevels aktif` yang membuktikan jalur C++ benar-benar dipakai,
bukan diam-diam fallback ke GDScript. `XDG_DATA_HOME` diisolasi per tes supaya
`SaveManager` tidak menyentuh save game asli.

Scene yang dijalankan (persis CI):

| Lib | Scene | `--quit-after` |
| --- | --- | --- |
| skills | `HeroSkillGdextParityTest` + `HeroSkillParityTest` | 900 |
| levels | `LevelDataGdextParityTest` + `LevelDataParityTest` | 120 |
| maps | `MapDataGdextParityTest` + `MapDataParityTest` | 120 |
| splash | `SplashGdextParityTest` + `SplashParityTest` | 400 |
| ui, mobile | *belum ada scene engine di CI* — berhenti di L4 | — |

Kalau binary Godot tidak ada di `PATH`, skrip mengunduhnya sekali ke
`~/.cache/mystic-arena/godot-4.3/` (URL + tata letak cache sama dengan
`tools/godot_debug_run.py`; tag rilis Godot selalu `<versi>-<release>`, jadi
`4.3-stable` — URL `.../download/4.3/...` menjawab **404**). Binary juga bisa
ditunjuk manual lewat `MYSTIC_GODOT=/path/to/godot`.

> **Status verifikasi skrip ini.** L0-L4 dijalankan sungguhan di sandbox
> (semua hijau, enam `.so` terbangun). L5 **belum** bisa dijalankan di sana —
> sandbox memblokir TLS ke host aset rilis GitHub, jadi binary Godot tidak
> terunduh — sehingga plumbing-nya diuji dengan engine **stub**
> (`MYSTIC_GODOT=/tmp/godot-stub/godot`): penyalinan aset, `--import` +
> `godot_log_gate`, isolasi `XDG_DATA_HOME` per tes (terbukti: dua tes dapat
> direktori berbeda), pemetaan scene → penanda wajib, dan jalur gagal. Stub
> yang mencetak `SCRIPT ERROR` **dengan exit code 0** — persis kelakuan Godot
> yang membuat gate ini perlu — tetap membuat L5 GAGAL dan skrip keluar dengan
> kode 1. Jalankan sekali di mesin/Codespace Anda untuk konfirmasi L5 dengan
> engine sungguhan.

### D. Codespaces — "lokal" tanpa memasang apa pun

`.devcontainer/` sudah memasang Godot 4.3, X11/Mesa, ffmpeg, dan venv
(`pygame-ce`, `pillow`, `numpy`, `gdtoolkit`) lewat `setup.sh`. Buka repo di
Codespaces (4 core / 8 GB), lalu:

```bash
pip install scons                                   # belum ada di setup.sh
tools/gdext_local_check.sh --lapis 5
```

Biayanya kuota **Codespaces**, bukan kuota **Actions** — dan bisa dipakai
interaktif (editor Godot di tab Ports → 6080). Panduan:
[docs/GODOT_DEBUG_DI_GITHUB.md](GODOT_DEBUG_DI_GITHUB.md).

---

## 6. Kalau mau menjalankan tangan (apa yang sebenarnya dilakukan skrip)

```bash
# 1. godot-cpp SEKALI untuk semua lib (objek compile dipakai bersama)
git clone -b godot-4.3-stable --depth 1 \
  https://github.com/godotengine/godot-cpp godot/gdext/godot-cpp
for lib in mystic_skills mystic_levels mystic_maps mystic_ui mystic_mobile mystic_splash; do
  ln -sfn ../godot-cpp "godot/gdext/$lib/godot-cpp"
done

# 2. header godot-cpp (binding_generator) — ini yang dibutuhkan L3
cd godot/gdext/godot-cpp
scons platform=linux target=template_debug optimize=none debug_symbols=no -j"$(nproc)"
cd -

# 3. build satu lib (output -> godot/addons/<lib>/bin/)
cd godot/gdext/mystic_levels
scons platform=linux target=template_debug optimize=none debug_symbols=no -j"$(nproc)"
nm -D --defined-only ../../addons/mystic_levels/bin/libmystic_levels.linux.template_debug.x86_64.so \
  | grep ' T mystic_levels_library_init'          # entry symbol WAJIB ada
cd -

# 4. engine (aset biner gitignored harus disalin dulu, kalau tidak boot
#    mencetak error yang menutupi error sungguhan)
python3 tools/convert_to_godot.py --assets
godot --headless --path godot --import
godot --headless --path godot res://tests/LevelDataGdextParityTest.tscn --quit-after 120 \
  | tee /tmp/levels.log
python3 godot/tools/godot_log_gate.py /tmp/levels.log \
  --require "[LevelDataGdextParityTest] PASS" \
  --require "GDExtension MysticLevels aktif"
```

Flag `SCONS_FLAGS` sengaja sama dengan CI (`optimize=none debug_symbols=no`):
yang diuji **paritas**, bukan kecepatan, dan `optimize=none` memangkas waktu
compile drastis. Nama berkas `.so` = suffix scons (`template_debug`), sedangkan
kunci di `.gdextension` = `linux.debug.x86_64` — jangan "dikoreksi", engine
tidak akan menemukan lib-nya (lihat `docs/AUDIT_ULANG_DARI_AWAL.md`).

---

## 7. Yang TIDAK bisa diverifikasi di luar CI/engine (jujur)

1. **Lapisan binding godot-cpp** — L2 memakai stub `Variant`, jadi hanya L3/L4
   yang membuktikan kode benar terhadap header asli, dan hanya L4 yang
   membuktikan `ClassDB::bind_method` + link berhasil.
2. **Pemuatan lib oleh engine** — `.gdextension` salah nama berkas, ABI tidak
   cocok, atau `entry_symbol` hilang hanya ketahuan saat `--import` (L5).
3. **Perilaku di dalam scene produksi** — `ArenaMap`, `Hero.gd`, `SplashScreen`
   asli, dan autoload hanya hidup di engine (L5).
4. **Platform lain** — Windows/macOS/Android/Web. CI pun hanya membangun
   `linux x86_64`; `build-android-godot.yml` **belum memanggil scons**, jadi
   export AAB tetap jalan dengan fallback GDScript.
5. **Performa** — paritas bukan kecepatan. Untuk FPS pakai
   `tools/godot_debug_run.py` di mesin ber-GPU (Codespaces memakai llvmpipe/CPU,
   jadi jangan dipakai mengukur FPS).

Karena itu urutan yang masuk akal: **L0-L2 setiap push (±25 detik) → L4 kalau
menyentuh generator/binding → L5 sebelum merge → CI sebagai jaring terakhir**,
bukan sebagai satu-satunya tempat mengetahui kebenaran.

---

## 8. Kalau tetap ingin CI lebih cepat

Yang sudah ada di workflow: filter `paths` (hanya jalan kalau berkas
GDExt/skill/generator berubah), `concurrency` + `cancel-in-progress`, cache
godot-cpp **per commit SHA dengan `save-always: true`** (job yang gagal di
langkah tes tidak membayar ulang compile ±10 menit), cache binary Godot,
`optimize=none`, dan satu checkout godot-cpp yang di-symlink ke enam lib.

Yang masih bisa dipangkas, urut dari dampak terbesar:

1. **Cache hasil build per lib, keyed hash sumber.** `src/*.cpp` adalah *hasil
   generate* yang ter-commit, jadi isinya hanya berubah kalau generator/oracle
   berubah. Kunci `actions/cache` dengan
   `hashFiles('godot/gdext/<lib>/src/**', 'godot/gdext/<lib>/SConstruct')` +
   SHA godot-cpp + `SCONS_FLAGS`, simpan
   `godot/gdext/godot-cpp/bin/*.a` **dan** `godot/addons/<lib>/bin/*.so`.
   PR yang hanya mengubah data levels lalu tidak perlu membangun lima lib
   lainnya: ±39 menit → ±8 menit. Cek `nm -D`/`strings` tetap dijalankan pada
   `.so` hasil cache supaya tidak ada verifikasi yang hilang.
2. **Pecah jadi matrix 6 job paralel.** Enam lib dibangun berurutan dalam satu
   job — itulah sebabnya `timeout-minutes` harus 75. Matrix
   (`strategy.matrix.lib: [skills, levels, maps, ui, mobile, splash]`) dengan
   cache godot-cpp bersama membuat wall time = lib terlambat (±10 menit),
   bukan jumlah semuanya. Biayanya: 6× restore cache godot-cpp (±1-2 menit
   masing-masing) dan kuota menit paralel — biasanya tetap jauh lebih murah
   daripada 40 menit serial.
3. **`ccache`** dengan `actions/cache` — membantu kalau sumber berubah sebagian,
   tapi dampaknya lebih kecil daripada (1) karena berkas `.cpp` hasil generate
   bersifat all-or-nothing.
4. **Jangan naikkan `optimize`**: `-O0` sudah pilihan tercepat untuk compile;
   yang diuji paritas, bukan kecepatan runtime.
5. **Pisahkan job "engine" dari job "build"**: `needs: build` + `download-artifact`
   untuk `.so`, sehingga kegagalan tes engine tidak memaksa build diulang.

---

## 9. Berkas terkait

| Berkas | Peran |
| --- | --- |
| `tools/gdext_local_check.sh` | **satu sumber** untuk semua perintah di atas (lapis, filter lib, ringkasan OK/GAGAL/LEWAT + waktu) |
| `tools/gen_*_cpp.py --check` | L0 — kesegaran transpile |
| `tools/test_godot_{level,map}_data_parity.py` | L1 — paritas statis + wiring closed-world |
| `tools/test_*_cpp_selftest.py` | L2/L3 — eksekusi `*_processor.cpp` di luar engine (+ probe `.so` kalau `GODOT_CPP_DIR` ada) |
| `godot/gdext/*/selftest/godot_stub.hpp` | stub `Variant`/`Array`/`Dictionary`/`String` semantik engine 4.3 |
| `godot/gdext/*/SConstruct` | L4 — build `.so` ke `godot/addons/<lib>/bin/` |
| `godot/tools/godot_log_gate.py` | L5 — gagalkan run kalau log headless memuat error (exit code Godot sering tetap 0) |
| `tools/godot_debug_run.py` | unduh binary Godot ke cache + jalankan scene/screenshot |
| `.github/workflows/godot-gdext.yml` | jaring terakhir: build + engine + paritas C++ ↔ oracle |
| `docs/AUDIT_ULANG_DARI_AWAL.md` | patokan tunggal paritas + desain per lib GDExt |

### Variabel lingkungan skrip

`PY` (auto-detect venv) · `CXX` (default `g++`) · `JOBS` (default `nproc`) ·
`GODOT_VERSION`/`GODOT_RELEASE`/`GODOT_CPP_REF` (default 4.3/stable, **harus**
se-versi engine — ABI GDExtension per minor) · `SCONS_FLAGS` ·
`GODOT_CPP_DIR` (checkout godot-cpp untuk L3) · `MYSTIC_GODOT` (binary engine) ·
`MYSTIC_GODOT_CACHE` (lokasi cache binary).

---

## 10. Perbaikan ikutan saat dokumen ini ditulis

`tools/godot_debug_run.py` membangun URL unduhan engine sebagai
`.../releases/download/{version}/Godot_v{version}_linux.x86_64.zip` dengan
`--godot-version` default `4.3`. Tag rilis Godot **selalu** memakai suffix
(`4.3-stable`), jadi URL itu menjawab **404** dan `--download` tidak pernah
berhasil — padahal `docs/GODOT_DEBUG_DI_GITHUB.md` §3 menganjurkannya untuk
menyiapkan binary lokal. Diperbaiki menjadi
`.../download/{tag}/Godot_v{tag}_linux.x86_64.zip` dengan
`engine_tag("4.3") == "4.3-stable"` (versi yang sudah bersuffix seperti
`4.4-rc1` dibiarkan apa adanya), mengikuti pola
`.github/workflows/godot-check.yml` (`V="${GODOT_VERSION}-${GODOT_RELEASE}"`).
Direproduksi dan dikonfirmasi: 404 sebelum, 302→aset sesudah.
