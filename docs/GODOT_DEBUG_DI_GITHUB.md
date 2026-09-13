# Godot di GitHub — menjalankan & men-debug tanpa memasang apa pun

> **Ringkas:** tab **Actions → Godot Debug Run** menjalankan game sungguhan di
> layar virtual (Xvfb) dan mengunggah **screenshot tiap N detik + `run.log` +
> `report.json` + (opsional) video** sebagai artifact. Untuk memakai **editor
> Godot interaktif di browser**, buka **Codespaces** pada repo ini.
>
> Keduanya memakai jalur yang sama dengan laptop: satu alat Python
> (`tools/godot_debug_run.py`) + satu harness GDScript
> (`godot/scenes/debug/DebugRun.tscn`). Tidak ada logika debug yang hanya hidup
> di CI.

Halaman ini untuk **menjalankan/melihat/memburu bug**, bukan mengukur paritas.
Audit paritas tetap di [GODOT_PARITY.md](GODOT_PARITY.md) dan
`../godot/README.md`.

| Berkas | Tugas |
|---|---|
| `.github/workflows/godot-run.yml` | tombolnya: `workflow_dispatch` + label `godot-debug` pada PR, Xvfb + Mesa, unggah artifact |
| `tools/godot_debug_run.py` | satu perintah untuk lokal **dan** CI (unduh engine, salin aset, import, jalankan, gerbang log, ringkasan) |
| `godot/scenes/debug/DebugRun.tscn/.gd` | harness di dalam engine: skenario, batas waktu, baris `[DebugRun] PASS/FAIL` |
| `godot/scenes/debug/DebugProbe.gd` | perekam: `shots/*.png` + `report.json` |
| `.devcontainer/devcontainer.json` + `setup.sh` | editor Godot di browser (Codespaces), versi engine disamakan dengan workflow |
| `tools/test_godot_debug_runner.py` | gerbang statis yang menjaga kelima berkas di atas tetap sepakat |

---

## 1. Dari GitHub Actions (1 klik, tanpa memasang apa pun)

1. Buka repo → tab **Actions** → pilih **Godot Debug Run** (kiri).
2. Klik **Run workflow**, pilih branch, isi input, **Run workflow**.

| Input | Arti |
|---|---|
| `scenario` | `menu` (layar menu) · `level` (mulai match) · `battle` (level + beli hero Kaizen) · `shop` (level + buka toko) · `scene` (scene apa adanya) |
| `level` | nomor level 1–54 (untuk `level`/`battle`/`shop`) |
| `seconds` | lama run; harness **keluar sendiri** saat batas ini lewat |
| `shot_every` | jarak screenshot dalam detik (`0` = hanya log, paling ringan) |
| `display` | `auto` (Xvfb kalau ada) · `xvfb` · `headless` (tanpa gambar sama sekali) |
| `scene` | scene `res://` lain, mis. `res://tests/BattleSmokeTest.tscn` (pakai dengan skenario `scene`) |
| `movie` | `true` = rekam video lewat `--write-movie` → `movie.mp4` |
| `touch` | `MYSTIC_FORCE_TOUCH=1` — tata letak HP di desktop |
| `godot_version` | `4.3` (versi minimum feature project) atau `4.7.2` (versi export Android) |
| `extra_engine_args` | flag engine tambahan, mis. `--debug-collisions` |

3. Setelah selesai: **ringkasan** run ada di tab **Summary** halaman run, dan
   berkasnya di bagian **Artifacts** → `godot-debug-<skenario>-<nomor>`.

Isi artifact:

| Berkas | Isi |
|---|---|
| `shots/frame_0001.png …` | isi layar, diambil tepat sesudah tiap frame digambar |
| `run.log` | keluaran engine apa adanya (baris `SCRIPT ERROR` / `Parse Error` ada di sini) |
| `report.json` | engine, driver, jumlah frame, FPS min/avg/maks, dan cuplikan keadaan tiap 0,5 s (state · wave · gold · hero per tim · minion) |
| `summary.md` | tabel ringkas + cuplikan keadaan + daftar berkas (juga tampil di Summary) |
| `trace.log` | jejak boot harness (satu baris per tahap, di-`flush` langsung) — penunjuk "berhenti di mana" kalau run macet/dibunuh |
| `preflight.log` + `marker.txt` | hasil uji penanda SEBELUM run sungguhan: engine menjalankan `scenes/debug/DebugMarker.tscn` (tanpa satu pun API game) dan menulis berkas. Lulus = engine+scene+berkas jalan; gagal = masalahnya di engine/project, bukan di skenario |
| `movie.mp4` | kalau `movie=true` (AVI dari Movie Maker diubah ffmpeg; kalau ffmpeg tidak ada, `.avi` dibiarkan) |
| `userdata/.../crash_log.txt` | log sesi yang sama dengan yang ditulis AppShell tiap boot |

### Menjalankan versi PR

Beri label **`godot-debug`** pada PR → workflow ini jalan untuk kode PR itu
(hasil artifact yang sama). Aman untuk PR dari fork: job ini hanya butuh
`contents: read`. Catatan: kalau `godot-run.yml` baru ada di PR itu (belum
masuk `main`), GitHub bisa belum mengenali triggernya untuk label pertama —
setelah merge, normal.

### Biaya

Workflow ini **manual saja** (tidak ada trigger push/pull otomatis), timeout 30
menit, dan satu run normal ±3–5 menit — sejalan dengan aturan hemat kuota
`godot-check.yml`. Label PR juga hanya jalan saat labelnya dipasang.

---

## 2. Codespaces — editor Godot di browser (interaktif)

```text
repo ini di GitHub → Code ▾ → Codespaces → Create codespace on <branch>
```

Container memakai `.devcontainer/devcontainer.json`:

* **desktop-lite** (Xvfb + fluxbox + noVNC) → tab **Ports** → **6080**
  ("Desktop noVNC") → terbuka desktop di browser;
* `.devcontainer/setup.sh` memasang **Godot 4.3** (versi default workflow,
  disamakan oleh `tools/test_godot_debug_runner.py`), Mesa software GL, ffmpeg,
  dan venv `~/.venv-mystic` untuk oracle paritas pygame.

Di terminal Codespace (port 6080 sudah terbuka di tab lain):

```bash
# EDITOR Godot (klik = pakai; renderer software, jadi sabar)
godot --editor --path godot

# JALANKAN game + screenshot (hasil di debug_out/, bisa dilihat di file explorer)
python3 tools/godot_debug_run.py --scenario battle --level 1 --seconds 30

# Jalankan scene uji persis seperti CI
python3 tools/godot_debug_run.py --scenario scene \
  --scene res://tests/BattleSmokeTest.tscn --display headless \
  --expect "[BattleSmokeTest] PASS"
```

`DISPLAY` sudah disetel otomatis oleh `setup.sh` (dideteksi dari proses Xvfb
milik desktop-lite, biasanya `:1`) dan ditulis ke `~/.bashrc`; kalau terminal
lama masih kosong, `export DISPLAY=:1` manual.

Kuota: Codespaces memakai jatah jam akun Anda, dan **tidak ada GPU** — bagus
untuk melihat layar + mengubah kode, bukan untuk mengukur FPS.

---

## 3. Lokal (satu perintah)

```bash
# sekali saja: taruh binary Godot di PATH, atau biarkan alatnya mengunduh
python3 tools/godot_debug_run.py --scenario battle --seconds 30 --download

# contoh lain
python3 tools/godot_debug_run.py --scenario menu --seconds 20          # menu utama
python3 tools/godot_debug_run.py --scenario shop --level 3 --seconds 25
python3 tools/godot_debug_run.py --scenario battle --seconds 20 --movie # + video
python3 tools/godot_debug_run.py --scenario battle --renderer vulkan    # Forward+ asli
python3 tools/godot_debug_run.py --scenario scene \
  --scene res://tests/UiHudParityTest.tscn --display headless           # tes apa pun
```

Yang dilakukan alat ini, berurutan: menyalin aset biner yang di-gitignore
(`sounds/`, `items/`, `presplash.png` — lewat `tools/convert_to_godot.py
--assets`) → `godot --import` bila `godot/.godot/` belum ada → menjalankan
scene + harness di layar virtual (atau `$DISPLAY`, atau headless) → gerbang log
yang sama dengan CI (`godot/tools/godot_log_gate.py`).

Keluaran ada di `debug_out/run-<stempel waktu>/` (di-gitignore) dan `user://`
diisolasi ke `<run>/userdata/`, jadi **save pemain tidak pernah tersentuh** —
dan sebaliknya save lama tidak bisa mengubah hasil debug.

### Opsi CLI yang sering dipakai

| Opsi | Arti |
|---|---|
| `--scenario`, `--level`, `--seconds`, `--shot-every`, `--max-shots` | sama dengan input workflow |
| `--display auto\|x11\|xvfb\|headless` | `x11` = pakai layar yang sedang ada |
| `--renderer opengl3\|vulkan` | `opengl3` = gl_compatibility + llvmpipe (default, juga di CI) |
| `--godot PATH`, `--download`, `--godot-version 4.3\|4.7.2` | dari mana binary engine-nya |
| `--out DIR`, `--label NAMA` | tempat keluaran + nama di `report.json` |
| `--movie`, `--fixed-fps 15` | video lewat Movie Maker |
| `--touch`, `--splash`, `--fps N` | MYSTIC_FORCE_TOUCH=1 · biarkan splash boot · batas FPS lewat `AppShell.apply_fps_limit` |
| `--expect "BARIS"`, `--no-gate` | baris wajib di log (`--expect ""` = hanya cek error) |
| `--extra ARG`, `--dry-run` | flag engine tambahan · cetak perintahnya saja |

---

## Apa yang dijalankan harness (dan apa yang TIDAK)

`godot/scenes/debug/DebugRun.tscn` **membungkus scene produksi apa adanya**
(`res://scenes/main.tscn` secara default) sebagai anak node-nya:

* tidak ada satu baris pun gameplay yang diubah; `main.tscn` tidak menyentuh
  berkas debug ini;
* skenario `level`/`battle`/`shop` memulai match lewat jalur yang sama dengan
  tombol PLAY (`GameManagerConnector.start_match`, pola
  `godot/tests/BattleSmokeTest.gd`), lalu melewati intro dengan mengirim
  SPACE/`H` ke `Main._on_key` — bukan dengan memanggil internal;
* `battle` membeli Kaizen seperti pemain baru membelinya; `shop` membuka toko
  dengan hotkey `H`;
* harness punya `process_mode = ALWAYS` supaya intro/pause tidak membekukan
  perekamnya, sementara scene produksi tetap `PAUSABLE` (semantik pause tidak
  berubah);
* batas waktu (detik/frame) datang dari `--seconds`/`--max-frames`, ditambah
  rem darurat `--quit-after` di level engine.

Yang **tidak** dikerjakan: mengubah FPS, memalsukan waktu, atau menonaktifkan
sistem apa pun. Kalau butuh match yang dipercepat, itu urusan scene uji
`tests/*ParityTest.tscn` yang memang hidup untuk itu.

---

## Troubleshooting

| Gejala | Sebab yang paling sering | Tindakan |
|---|---|---|
| Artifact tidak berisi `shots/` | `display=headless` (driver dummy memang tidak bisa menggambar), atau Xvfb/GL gagal | pakai `display=xvfb`; di log cari `Unable to create an OpenGL context` → pastikan `libgl1-mesa-dri` terpasang (workflow & Codespace sudah memasangnya) |
| Status run **FAIL** | ada `SCRIPT ERROR`/`Parse Error`/`[DebugRun] FAIL` di `run.log` | tab Checks menampilkan baris itu sebagai anotasi `::error::GODOT-DEBUG:`; log lengkap ada di artifact |
| `report.json` tidak ada | harness tidak selesai (mis. scene uji memanggil `quit()` sendiri, atau engine dihentikan timeout) | normal untuk scene uji; untuk skenario lain lihat `run.log` + naikkan `--timeout` |
| `summary.md` menulis **harness TIDAK PERNAH JALAN** | skrip `scenes/debug/DebugRun.gd` gagal dikompilasi (analyzer GDScript menolak panggilan method di luar `Node` tanpa `has_method(...)`) atau scene tidak dijalankan engine | bandingkan dengan `preflight.log`: kalau penanda (`DebugMarker`) lulus, masalahnya di skrip harness → cari `Parse Error`/`SCRIPT ERROR` di `run.log`. Trap ini dikunci `tools/test_godot_debug_runner.py`, yang menolak panggilan tanpa `has_method` |
| `summary.md` menulis **preflight GAGAL** | engine tidak bisa menjalankan bahkan scene penanda yang tidak memakai API game | lihat `preflight.log`: `Parse Error` (skrip penanda), project tidak termuat, atau dependensi GL/X11 tidak ada |
| Video tidak ada | `movie=false`, atau `ffmpeg` tidak ada | pakai `movie=true`; kalau `ffmpeg` tidak ada, `movie.avi` tetap diunggah (buka dengan VLC) |
| Screenshot/lampu terlihat beda dari desktop | CI memakai **gl_compatibility + llvmpipe**, bukan Forward+ | untuk urusan piksel: jalankan lokal `--renderer vulkan` |
| Ukuran artifact besar | 30 detik × 1 screenshot ≈ 10 MB; video 15 fps ± 5 MB/menit | turunkan `seconds`, naikkan `shot_every`, atau `max_shots` |
| Unduhan Godot gagal | URL hanya untuk **linux x86_64** (yang dipakai CI) | Windows/macOS: pasang Godot sendiri lalu `--godot /path/ke/godot` |
| Run berhenti sendiri di tengah | itu memang desainnya (`--seconds`/`--max-frames`) | perbesar `seconds` |
| Run **jauh lebih lama** dari `seconds` | game mengubah `Engine.time_scale` (hit-stop hero/boss = 0.05, setting Game Speed 0.5x-2x): `delta` bukan waktu nyata | batas run sudah memakai jam dinding (`harness_seconds_wall`), jadi ini hanya terjadi pada versi lama; bandingkan kolom `detik nyata` vs `jam game` di `summary.md` |
| Run mati sendiri tepat di batas `--timeout` | harness/engine tidak keluar setelah `seconds` | `trace.log` menyebut tahap terakhir; kalau tahapnya `boot`, harness berhenti sendiri di 60 detik dengan baris `[DebugRun] FAIL` (lihat juga 40 baris terakhir `run.log`); rem darurat membunuh **seluruh process group**, jadi tidak ada proses yatim |
| `run.log` berhenti mendadak tanpa sebab | engine dibunuh sebelum buffer stdout-nya penuh | engine dijalankan lewat `stdbuf -oL -eL` (log baris-per-baris) — kalau baris ini hilang dari `run.log`, alatnya versi lama |

---

## Batasan jujur

1. **Screenshot ≠ paritas piksel.** Driver grafis CI bukan GPU; glow/cahaya
   bisa sedikit berbeda. Yang sama: tata letak, teks, posisi, urutan UI.
2. **FPS di software rendering tidak bermakna** untuk menilai performa HP.
   Untuk itu tetap pakai benchmark pygame (`tools/bench_mobile.py`) atau
   perangkat asli.
3. **Headless tidak bisa screenshot** (Godot memakai display/render driver
   dummy). Karena itu workflow ini mengunduh Xvfb + Mesa.
4. Hanya isi **root viewport** yang tertangkap; `Window` terpisah (kalau nanti
   ada) tidak ikut.
5. Berkas di `debug_out/` **tidak masuk git** (memory `.gitignore`), jadi hasil
   run lokal tidak akan tidak sengaja ter-commit.

---

## Kalau ingin lebih jauh

* **Menjalankan scene uji dari CI tanpa lokal**: isi `scenario=scene` +
  `scene=res://tests/<X>.tscn` (harness melepas tuntutan baris
  `[DebugRun] PASS` karena scene uji punya baris PASS-nya sendiri).
* **Menjadikan harness bagian godot-check.yml**: belum dilakukan — harness ini
  sengaja tidak menambah waktu/waktu tunggu workflow utama sebelum terbukti
  hijau di beberapa run manual. Setelah itu, langkah termurahnya adalah:

  ```yaml
  - name: DebugRun smoke (harness)
    run: |
      set -o pipefail
      python3 tools/godot_debug_run.py --godot "$HOME/godot-bin/godot" \
        --scenario battle --seconds 4 --shot-every 0 --display headless \
        --out /tmp/debugrun --no-assets 2>&1 | tee /tmp/debugrun.log
  ```

  (gate-nya sudah ikut di dalam alat; cukup tambahkan `--require` bila perlu).
