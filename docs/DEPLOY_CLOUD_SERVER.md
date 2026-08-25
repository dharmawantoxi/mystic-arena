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
4. Klik **Apply / Deploy**. Tunggu build ±1-2 menit.

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
> - Build command: `(kosong)`
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

**Solusi yang disarankan:**

1. **Tetap pentingkan Android Auto Backup + save lokal** — game sudah
   punya ini. Cloud server hanya lapisan tambahan.
2. **Pakai persistent disk (berbayar)** — Render hanya mendukung
   persistent disk di instance **berbayar** (Starter ~$7/bln). Setelah
   upgrade, tambahkan disk dengan mount path `cloud_data`.
3. **Pakai object storage gratis (disarankan untuk `$0`)** — mis.
   Cloudflare **R2** (10 GB gratis) atau Supabase Storage gratis.
   Server menyimpan envelope cloud ke bucket, bukan ke disk server.
   (Implementasi ini belum ada di `tools/cloud_server/server.py`; bisa
   ditambahkan kalau kamu mau lanjut.)

### Kalau hanya mau uji sebentar

Render free cukup untuk demo/testing dengan pengguna sedikit, tapi
ingat bahwa save bisa hilang saat server restart. Untuk jaminan
produk, kombinasi terbaik saat belum mau bayar adalah:
**save lokal + Android Auto Backup + server Render yang di-upgrade ke
persistent disk nanti.**

---

## 4. Parameter server yang bisa diatur

| Env var | Fungsi | Default |
|---|---|---|
| `HOST` | Alamat bind | `0.0.0.0` |
| `PORT` | Port (diisi otomatis Render/Railway) | `8080` |
| `MYSTIC_CLOUD_DATA_DIR` | Folder tempat menyimpan file save | `./cloud_data` |
| `MYSTIC_CLOUD_API_KEY` | Kunci bersama; kalau kosong, server tanpa auth | kosong |
