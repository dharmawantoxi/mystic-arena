# Server Top Up (Mystic Arena)

Mengotomatiskan alur top up: **cetak invoice → terima webhook
Midtrans → issue kode redeem otomatis**. Gold di game masuk
otomatis setelah pembayaran ter-settle (tanpa dev mengetik kode).

## Jalankan (development / mock)

```bash
pip install -r server/requirements.txt
python server/app.py
```

Tanpa API key, server berjalan di **mode MOCK**:
- `POST /api/topup/create` → invoice lokal
- `POST /api/mock/settle/<id>` → simulasi pembayaran berhasil
  (atau set `TOPUP_MOCK_AUTO_SETTLE=10` agar settle otomatis 10
  detik setelah invoice dibuat — untuk demo hands-free)

Coba:
```bash
curl -X POST localhost:8321/api/topup/create -d '{"pkg":"PAKET 50K"}'
curl -X POST localhost:8321/api/mock/settle/mock-xxxx
curl localhost:8321/api/topup/status/mock-xxxx   # -> status settled + kode
```

## Konfigurasi (env vars)

| Var | Default | Keterangan |
|---|---|---|
| `TOPUP_MIDTRANS_SERVER_KEY` | *(kosong = mock)* | API key server Midtrans (`SB-...`) |
| `TOPUP_MIDTRANS_API` | `https://api.midtrans.com` | Ganti `https://api.sandbox.midtrans.com` untuk sandbox |
| `TOPUP_DB_PATH` | `server/topup.db` | Lokasi SQLite |
| `TOPUP_MOCK_AUTO_SETTLE` | `0` (off) | Detik auto-settle (mock saja) |
| `TOPUP_PORT` | `8321` | Port HTTP |

## Sambungkan ke game

Di `_core.py` (section menu), set:

```python
TOPUP_SERVER_URL = "https://topup.namagame.com"   # atau env MYSTIC_TOPUP_URL
```

Game akan: klik PAY NOW → server cetak invoice → dialog menampilkan
QRIS → game poll status tiap 2 detik → saat settle, kode di-issue
server dan **gold otomatis masuk** (pemain tidak perlu mengetik apa
pun). Tanpa URL server, game tetap memakai mode simulasi.

## Produksi (Midtrans)

1. Daftar [Midtrans](https://www.midtrans.com) (KYC KTP/rekening)
   — dana top up pemain akan dicairkan Midtrans ke rekeningmu (T+1).
2. Set `TOPUP_MIDTRANS_SERVER_KEY` (dan pakai `TOPUP_MIDTRANS_API`
   sandbox dulu untuk testing).
3. Deploy `server/app.py` ke host dengan **HTTPS** (wajib untuk
   webhook): VPS + Caddy/Nginx, atau Railway/Render/Fly.io.
4. Di dashboard Midtrans → **Notification URL** isi
   `https://<hostmu>/webhooks/midtrans`.
5. QRIS: supaya QRIS-nya benar (terhubung ke MID kamu), tambahkan
   parameter `qris` saat create invoice (lihat dokumentasi Midtrans
   Invoice) — di code sudah tersedia titik integrasinya.
6. Pastikan `PACKAGES` di `server/app.py` selalu sinkron dengan
   `TOPUP_PACKAGES` di `_core.py`.

## Endpoint

| Method & Path | Fungsi |
|---|---|
| `POST /api/topup/create` | Cetak invoice `{"pkg":"PAKET 50K"}` |
| `GET /api/topup/status/<id>` | Status + kode (saat settled) |
| `GET /api/topup/qr/<id>` | PNG QR (QRIS Midtrans / QR mock) |
| `POST /webhooks/midtrans` | Webhook Midtrans (signature divalidasi) |
| `POST /api/mock/settle/<id>` | Simulasi settle (mock saja) |
| `POST /api/redeem` | Tandai kode redeemed (server-side) |
