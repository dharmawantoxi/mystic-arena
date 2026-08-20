# MULAI DI SINI

Tiga langkah: **uji di PC → unggah ke GitHub → build APK**.

---

## 1. Uji dulu di PC (5 menit, tanpa Android sama sekali)

```bash
cd mystic-arena

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install pygame-ce

# salin folder assets Anda (font + suara) ke mystic-arena/assets/
# -> tanpa aset pun game tetap jalan, hanya tanpa suara & font khusus

python main.py                     # mode PC biasa (mouse + keyboard)
```

Untuk melihat **tata letak tombol sentuh** seperti di HP:

```bash
# Linux / macOS
MYSTIC_FORCE_TOUCH=1 python main.py

# Windows PowerShell
$env:MYSTIC_FORCE_TOUCH=1; python main.py
```

Yang harus Anda lihat: 4 tombol skill di kanan bawah (dengan busur
cooldown), tombol SHOP di kiri bawah, tombol ⏸ dan FPS di kanan atas.
Klik tombol FPS untuk memutar mode debug: off → mini → lengkap → grafik.

Cek performa:

```bash
python tools/bench_mobile.py       # adegan intro (paling berat)
python tools/bench_heavy.py        # adegan gameplay
```

---

## 2. Unggah ke GitHub

### Cara A — Git di terminal (disarankan)

1. Buat repo kosong di <https://github.com/new>.
   Nama: `mystic-arena`. **Jangan** centang "Add a README file".
   Pilih **Private** kalau kode ini komersial.

2. Di folder `mystic-arena`:

```bash
git init
git add .
git commit -m "Mystic Arena: versi Android dengan kontrol sentuh"
git branch -M main
git remote add origin https://github.com/USERNAME/mystic-arena.git
git push -u origin main
```

Kalau diminta password, GitHub **tidak lagi menerima password akun** —
buat Personal Access Token di
<https://github.com/settings/tokens> (centang scope `repo`), lalu
tempel token itu sebagai password.

### Cara B — Lewat browser (tanpa install Git)

1. Buat repo kosong seperti di atas, **centang** "Add a README file".
2. Klik **Add file → Upload files**.
3. Seret **isi** folder `mystic-arena` (bukan foldernya) ke jendela.
4. Tunggu semua terunggah, tulis pesan commit, klik **Commit changes**.

> Batas unggah lewat browser: 100 berkas sekali jalan. Bundel ini
> berisi 119 berkas, jadi unggah **dua kali**: pertama folder
> `bosses/`, lalu sisanya.

### Yang TIDAK ikut terunggah (sudah diatur `.gitignore`)

`__pycache__/`, `.buildozer/`, `bin/`, `*.apk`, `*.aab`,
`*.keystore`, `saves/`, `crash_log.txt`.
Keystore memang **tidak boleh** masuk repo.

---

## 3. Setelah repo jadi

1. Buka tab **Actions** di repo Anda → aktifkan workflow.
   Tiap `git push` ke `main` akan membuat **APK debug** otomatis
   (unduh dari halaman Actions → Artifacts).
2. Sebelum build rilis, ganti di `buildozer.spec`:
   ```ini
   package.domain = com.namaanda     # tidak bisa diubah setelah rilis!
   ```
3. Ikuti panduan lengkap: **[docs/PANDUAN_ANDROID.md](docs/PANDUAN_ANDROID.md)**
   — build lokal, keystore, GitHub Actions, sampai Play Console.

---

## Peta berkas singkat

| Berkas | Isi |
|---|---|
| `main.py` | entry point sentuh (versi lama: `main_desktop_legacy.py`) |
| `mobile/` | semua kode khusus Android: sentuh, HUD, performa, debug |
| `buildozer.spec` | konfigurasi build APK/AAB |
| `p4a-recipes/` | resep kompilasi pygame-ce untuk Android |
| `.github/workflows/` | build otomatis di GitHub |
| `tools/` | benchmark & generator indeks boss |
| `docs/PANDUAN_ANDROID.md` | panduan lengkap langkah demi langkah |
