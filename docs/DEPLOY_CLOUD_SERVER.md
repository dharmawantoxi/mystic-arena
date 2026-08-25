# Deploy Cloud Save Server (pilih yang GRATIS)

Panduan men-deploy server cloud save Mystic Arena ke **Render** atau
**Railway**, ditulis untuk memakai opsi **GRATIS**.

## Pilihan cepat

| Platform | Ada tier gratis? | Rekomendasi |
|---|---|---|
| **Render** | ✅ **Ya**, tier **Free** (web service gratis) | **PILIH INI** |
| Railway | ⚠ Hanya **kredit trial** (±$5, lalu mulai ~$5/bln) | Untuk coba, bukan permanen |

> Kesimpulan: **pilih → Render Free.** Railway tidak punya tier gratis
> permanen lagi, jadi hanya cocok untuk uji coba singkat.

---

## 1. Deploy ke Render (GRATIS)

### A. Siapkan repo di GitHub (kalau belum)

Push repo ini ke GitHub. Render akan membangun dari repo itu.

```bash
cd mystic-arena
git add -A
git commit -m "cloud save server"
git push origin main
```

### B. Deploy dari `render.yaml` (paling cepat)

1. Buka <https://render.com> → **New** → **Blueprint**.
2. Pilih repo GitHub `mystic-arena`.
3. Render membaca `render.yaml` di root dan membuat service
   **mystic-arena-cloud** (plan **Free**).
4. Klik **Apply / Deploy**.
   - Saat diminta variable `MYSTIC_CLOUD_R2_*` (sync: false), gunakan
     nilai dari bucket R2 yang kamu buat (lihat Bagian 5). Kalau kamu
     tidak pakai R2, hapus/masukkan nilai kosong — server tetap jalan,
     tapi file disimpan sementara di filesystem Render.
5. Tunggu build ±1-2 menit (Render akan `pip install` boto3 dari
   `tools/cloud_server/requirements.txt`).

Setelah selesai, Render memberi URL, misalnya:
```
https://mystic-arena-cloud.onrender.com
```

Cek server hidup:
```
curl https://mystic-arena-cloud.onrender.com/health
# {"ok": true, "service": "mystic-arena-cloud-server", "version": 1, ...}
```

> Kalau tidak memakai Blueprint, cukup buat **New → Web Service**,
> pilih repo, set:
> - Build command: `pip install -r tools/cloud_server/requirements.txt`
> - Start command: `python tools/cloud_server/server.py`
> - Instance type: **Free**

### C. Sambungkan game ke Render

```bash
# PC / uji lokal
MYSTIC_CLOUD_URL=https://mystic-arena-cloud.onrender.com python main.py

# Build Android (pakai URL Render, bukan localhost)
MYSTIC_CLOUD_URL=https://mystic-arena-cloud.onrender.com buildozer android debug
```

API key dibuat otomatis oleh Render (env `MYSTIC_CLOUD_API_KEY`).
Kalau kamu set sendiri di dashboard, game harus memakai nilai yang sama:

```bash
MYSTIC_CLOUD_URL=... MYSTIC_CLOUD_API_KEY=<statusRender> buildozer android debug
```

---

## 2. Deploy ke Railway (hanya uji coba gratis)

Railway tidak memiliki **free tier permanen**. Akun baru mendapat
**kredit trial sekali pakai** (±$5, seingatnya juga butuh kartu untuk
lanjut). Setelah kredit habis, minimal pakai plan **Hobby (~$5/bln)**.

### Langkah (jika ingin mencoba)

1. Buka <https://railway.com> → **New Project**.
2. **Deploy from GitHub Repo** → pilih `mystic-arena`.
3. Tambah variable:
   - `START_COMMAND = python tools/cloud_server/server.py`
   - `PORT` dibiarkan (Railway isi otomatis).
   - (opsional) `MYSTIC_CLOUD_API_KEY = sesuatu_rahasia`
4. Railway akan memberi URL:
   ```
   https://<project>-<name>.up.railway.app
   ```
5. Game menghubungkan ke URL itu lewat `MYSTIC_CLOUD_URL`.

> Karena bukan permanen gratis, untuk produksi sebaiknya pakai Render
> free (atau Render Starter jika butuh `persistent disk`).

---

## 3. ⚠ Batasan penting tier gratis (Wajib dibaca)

**Render FREE memakai filesystem sementara.** File yang disimpan
server di `./cloud_data` akan hilang ketika:

- service **restart**,
- service **redeploy** (push kode baru),
- service **spin-down** (idle ≥ 15 menit).

Render juga bisa me-restart service gratis kapan saja tanpa
pemberitahuan. Artinya, kalau hanya mengandalkan `cloud_data` lokal,
save cloud bisa hilang — **tidak ideal untuk tujuan "save tidak
hilang"**.

**Solusi GRATIS yang sudah didukung (disarankan):**

✅ **Cloudflare R2** — object storage S3-compatible dengan **10 GB
gratis/tagihan** dan **tanpa biaya egress**. `server.py` sekarang
bisa menyimpan save langsung ke bucket R2, jadi walau Render restart /
redeploy / spin-down, save tetap ada di R2. Lihat **Bagian 5** di bawah.

Solusi lain (tidak dipilih karena berbayar):
2. **Persistent disk (berbayar)** — Render hanya mendukung persistent
   disk di instance **berbayar** (Starter ~$7/bln), mount path
   `cloud_data`.
3. **Supabase Storage** — opsi gratis lain, tapi butuh project
   Supabase + kredensial terpisah; R2 dianggap lebih sederhana.

### Kalau hanya mau uji sebentar (tanpa R2)

Render free cukup untuk demo/testing dengan pengguna sedikit, tapi
ingat bahwa save bisa hilang saat server restart/redeploy. Untuk
jaminan produk gratis, gunakan **R2** (Bagian 5).

---

## 4. Parameter server yang bisa diatur

| Env var | Fungsi | Default |
|---|---|---|
| `HOST` | Alamat bind | `0.0.0.0` |
| `PORT` | Port (diisi otomatis Render/Railway) | `8080` |
| `MYSTIC_CLOUD_DATA_DIR` | Folder storage lokal | `./cloud_data` |
| `MYSTIC_CLOUD_API_KEY` | Kunci bersama; kalau kosong, server tanpa auth | kosong |
| `MYSTIC_CLOUD_R2_ENDPOINT` | R2 endpoint S3 | kosong (= storage lokal) |
| `MYSTIC_CLOUD_R2_BUCKET` | Nama bucket R2 | kosong |
| `MYSTIC_CLOUD_R2_ACCESS_KEY_ID` | R2 Access Key ID | kosong |
| `MYSTIC_CLOUD_R2_SECRET_ACCESS_KEY` | R2 Secret Access Key | kosong |
| `MYSTIC_CLOUD_R2_PREFIX` | Prefix object di bucket | `mystic_arena` |

`/health` melaporkan storage aktif:
`{"storage": "r2"}` = menyimpan ke Cloudflare R2;
`{"storage": "local"}` = menyimpan ke filesystem server;
`{"storage": "r2-missing-boto3"}` = R2 dikonfigurasi tapi `boto3`
belum terpasang (jalankan `pip install -r tools/cloud_server/requirements.txt`).

## 5. Setup Cloudflare R2 (GRATIS, agar save awet)

R2 punya **10 GB gratis/bulan** dan **tanpa biaya transfer keluar**,
jadi cocok untuk menyimpan file save walaupun server Render Free
sering restart.

### Langkah di Cloudflare

1. Buka <https://dash.cloudflare.com> → **R2** → **Create bucket**.
   - Name: `mystic-arena` (atau nama bebas).
   - Location: bebas (mis. `auto` / `APAC`).
2. Buka bucket → **Settings** → salin **Endpoint** (format
   `https://<accountid>.r2.cloudflarestorage.com`).
3. Di dashboard R2 → **Manage R2 API Tokens** → **Create API token**.
   - Permission: **Object Read & Write** untuk bucket `mystic-arena`.
   - Salin **Access Key ID** dan **Secret Access Key**.

### Isi ke Render

Di Render → service **mystic-arena-cloud** → **Environment**:

| Key | Nilai |
|---|---|
| `MYSTIC_CLOUD_R2_ENDPOINT` | `https://<accountid>.r2.cloudflarestorage.com` |
| `MYSTIC_CLOUD_R2_BUCKET` | `mystic-arena` |
| `MYSTIC_CLOUD_R2_ACCESS_KEY_ID` | `<Access Key ID>` |
| `MYSTIC_CLOUD_R2_SECRET_ACCESS_KEY` | `<Secret Access Key>` |

Render akan build ulang dengan `boto3` (dari
`tools/cloud_server/requirements.txt`).

### Verifikasi

```bash
curl https://mystic-arena-cloud.onrender.com/health
# harus ada "storage":"r2"
```

Lalu main game → Settings → ☁ CLOUD SAVE → UPLOAD. Save disimpan di
bucket R2, bukan di filesystem Render, sehingga tetap ada saat Render
free restart / redeploy / spin-down.
