# ================================================================
# server/app.py — Server Top Up Hero Gold
#
# Tanggung jawab (mengotomatiskan langkah 4-6 alur top up):
#   1. Cetak invoice pembayaran  (Midtrans Invoice / mode mock)
#   2. Terima webhook Midtrans   (verifikasi signature HMAC-SHA512)
#   3. Otomatis issue kode redeem saat pembayaran SETTLE
#
# MODE
# ----
# - MOCK (default, tanpa API key): invoice dibuat lokal; pembayaran
#   disimulasikan via POST /api/mock/settle/<id> atau otomatis setelah
#   TOPUP_MOCK_AUTO_SETTLE detik. Cocok untuk development & testing.
# - MIDTRANS (dengan TOPUP_MIDTRANS_SERVER_KEY): invoice dibuat lewat
#   API Midtrans (https://api.midtrans.com/v2/invoice), status
#   mengikuti webhook resmi Midtrans.
#
# JALANKAN
# --------
#     pip install -r server/requirements.txt
#     python server/app.py
# Env vars: lihat server/README.md
# ================================================================

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.request

from flask import Flask, Response, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get(
    "TOPUP_DB_PATH", os.path.join(BASE_DIR, "topup.db"))
SERVER_KEY = os.environ.get("TOPUP_MIDTRANS_SERVER_KEY", "")
MIDTRANS_API = os.environ.get(
    "TOPUP_MIDTRANS_API", "https://api.midtrans.com")
MOCK_AUTO_SETTLE_SEC = int(os.environ.get("TOPUP_MOCK_AUTO_SETTLE", "0"))
PORT = int(os.environ.get("TOPUP_PORT", "8321"))

# ═══ PAKET (WAJIB SINKRON dengan TOPUP_PACKAGES di _core.py) ═══
# label -> (harga IDR, jumlah gold)
PACKAGES = {
    "PAKET 50K": (10000, 50000),
}

MOCK_MODE = (not SERVER_KEY) or SERVER_KEY.startswith("SB-Mock")

app = Flask(__name__)
_lock = threading.Lock()


# ────────────────────────────────────────────────
# DATABASE (SQLite)
# ────────────────────────────────────────────────

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS invoices(
            id TEXT PRIMARY KEY,
            pkg TEXT,
            amount INTEGER,
            gold INTEGER,
            status TEXT DEFAULT 'pending',
            code TEXT,
            created REAL,
            settled REAL,
            midtrans_raw TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS codes(
            code TEXT PRIMARY KEY,
            invoice TEXT,
            redeemed INTEGER DEFAULT 0,
            redeemed_at REAL)""")


def _new_code():
    """Kode unik format MA-XXXXXX (sama dengan alur voucher manual)."""
    while True:
        code = f"MA-{secrets.randbelow(10**6):06d}"
        with _db() as c:
            if not c.execute(
                    "SELECT 1 FROM codes WHERE code=?", (code,)).fetchone():
                c.execute("INSERT INTO codes(code, invoice) VALUES(?, ?)",
                          (code, ""))
                return code


def _settle_invoice(invoice_id):
    """Mark settled + issue kode (idempotent)."""
    with _lock:
        with _db() as c:
            row = c.execute(
                "SELECT * FROM invoices WHERE id=?", (invoice_id,)
            ).fetchone()
            if row is None:
                return None
            if row["status"] == "settled":
                return row["code"]
            if row["status"] not in ("pending",):
                return None
            code = _new_code()
            c.execute(
                "UPDATE invoices SET status='settled', code=?, "
                "settled=? WHERE id=?",
                (code, time.time(), invoice_id))
            c.execute(
                "UPDATE codes SET invoice=? WHERE code=?",
                (invoice_id, code))
        print(f"[TOPUP] invoice {invoice_id} SETTLE -> kode {code}")
        return code


# ────────────────────────────────────────────────
# QR (PNG)
# ────────────────────────────────────────────────

def _qr_png(text):
    """Generate QR PNG (server-side dep: qrcode[pil])."""
    import io
    import qrcode
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ────────────────────────────────────────────────
# ENDPOINTS
# ────────────────────────────────────────────────

@app.get("/healthz")
def healthz():
    return jsonify(ok=True, mock=MOCK_MODE,
                   packages={k: list(v) for k, v in PACKAGES.items()})


@app.post("/api/topup/create")
def create_topup():
    """Cetak invoice. Body: {"pkg": "PAKET 50K"}."""
    data = request.get_json(silent=True) or {}
    pkg = data.get("pkg")
    if pkg not in PACKAGES:
        return jsonify(error="unknown_package"), 400
    price, gold = PACKAGES[pkg]
    invoice_id = ("mock-" if MOCK_MODE else "MA-") + \
        secrets.token_hex(8)

    midtrans_raw = None
    if not MOCK_MODE:
        body = {
            "transaction_id": invoice_id,
            "gross_amount": price,
            "currency": "IDR",
            "description": f"Mystic Arena - {pkg}",
        }
        try:
            req = urllib.request.Request(
                f"{MIDTRANS_API}/v2/invoice",
                data=json.dumps(body).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {SERVER_KEY}",
                })
            with urllib.request.urlopen(req, timeout=10) as r:
                midtrans_raw = r.read().decode()
        except Exception as e:
            print(f"[TOPUP] midtrans create gagal: {e}")
            return jsonify(error="midtrans_error", detail=str(e)), 502

    with _db() as c:
        c.execute(
            "INSERT INTO invoices(id, pkg, amount, gold, status, created, "
            "midtrans_raw) VALUES(?,?,?,?, 'pending', ?, ?)",
            (invoice_id, pkg, price, gold, time.time(), midtrans_raw))

    print(f"[TOPUP] invoice {invoice_id} dibuat ({pkg}, "
          f"{price:,} IDR, mock={MOCK_MODE})")
    return jsonify(id=invoice_id, pkg=pkg, amount=price, gold=gold,
                   status="pending",
                   qr_url=f"/api/topup/qr/{invoice_id}",
                   mock=MOCK_MODE)


@app.get("/api/topup/status/<invoice_id>")
def topup_status(invoice_id):
    with _db() as c:
        row = c.execute(
            "SELECT * FROM invoices WHERE id=?", (invoice_id,)
        ).fetchone()
    if row is None:
        return jsonify(error="not_found"), 404
    out = {"id": row["id"], "status": row["status"],
           "gold": row["gold"], "amount": row["amount"]}
    if row["status"] == "settled":
        out["code"] = row["code"]
    return jsonify(out)


@app.get("/api/topup/qr/<invoice_id>")
def topup_qr(invoice_id):
    with _db() as c:
        row = c.execute(
            "SELECT * FROM invoices WHERE id=?", (invoice_id,)
        ).fetchone()
    if row is None:
        return "not found", 404
    if MOCK_MODE or not row["midtrans_raw"]:
        # Mock: QR berisi payload simulasi (bukan pembayaran nyata).
        png = _qr_png(f"MOCK-PAY:{row['id']}:{row['amount']}")
    else:
        # Midtrans: proxy qr_code_url dari response invoice.
        raw = json.loads(row["midtrans_raw"])
        url = raw.get("qr_code_url")
        if not url:
            return "no_qr", 404
        png = urllib.request.urlopen(url, timeout=10).read()
    return Response(png, mimetype="image/png")


@app.post("/api/mock/settle/<invoice_id>")
def mock_settle(invoice_id):
    """HANYA mode mock: simulasi pembayaran berhasil."""
    if not MOCK_MODE:
        return jsonify(error="mock_disabled"), 403
    code = _settle_invoice(invoice_id)
    if code is None:
        return jsonify(error="cannot_settle"), 400
    return jsonify(ok=True, code=code)


@app.post("/webhooks/midtrans")
def webhook_midtrans():
    """Webhook resmi Midtrans (harus HTTPS di produksi)."""
    if MOCK_MODE:
        return jsonify(ok=True, ignored="mock_mode")
    raw = request.get_data()
    sig = request.headers.get("x-signature-1", "")
    expected = hmac.new(SERVER_KEY.encode(), raw,
                        hashlib.sha512).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return jsonify(error="bad_signature"), 400
    try:
        data = json.loads(raw)
    except ValueError:
        return jsonify(error="bad_json"), 400
    txn = (data.get("transaction_id")
           or data.get("order_id") or "")
    status = data.get("transaction_status")
    if status in ("settle", "capture"):
        _settle_invoice(txn)
    elif status == "cancel":
        with _db() as c:
            c.execute("UPDATE invoices SET status='cancel' "
                      "WHERE id=? AND status='pending'", (txn,))
    elif status == "expire":
        with _db() as c:
            c.execute("UPDATE invoices SET status='expired' "
                      "WHERE id=? AND status='pending'", (txn,))
    return jsonify(status="accepted")


@app.post("/api/redeem")
def api_redeem():
    """Tandai kode sudah dipakai (server-side, opsional)."""
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").upper()
    if not re.match(r"^MA-\d{4,8}$", code):
        return jsonify(ok=False, error="bad_format"), 400
    with _db() as c:
        row = c.execute("SELECT * FROM codes WHERE code=?",
                        (code,)).fetchone()
        if row is None:
            return jsonify(ok=False, error="unknown_code"), 404
        if row["redeemed"]:
            return jsonify(ok=False, error="already_redeemed"), 409
        c.execute("UPDATE codes SET redeemed=1, redeemed_at=? "
                  "WHERE code=?", (time.time(), code))
    return jsonify(ok=True)


# ────────────────────────────────────────────────
# AUTO-SETTLE (mock, untuk demo hands-free)
# ────────────────────────────────────────────────

def _auto_settle_loop():
    if MOCK_AUTO_SETTLE_SEC <= 0:
        return
    while True:
        time.sleep(2)
        cutoff = time.time() - MOCK_AUTO_SETTLE_SEC
        try:
            with _db() as c:
                rows = c.execute(
                    "SELECT id FROM invoices "
                    "WHERE status='pending' AND created < ?",
                    (cutoff,)).fetchall()
            for r in rows:
                _settle_invoice(r["id"])
        except Exception as e:
            print(f"[TOPUP] auto-settle error: {e}")


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=_auto_settle_loop, daemon=True)
    t.start()
    print("=" * 52)
    print(" SERVER TOP UP MYSTIC ARENA")
    print(f" mode       : {'MOCK (simulasi)' if MOCK_MODE else 'MIDTRANS'}")
    print(f" db         : {DB_PATH}")
    if MOCK_MODE and MOCK_AUTO_SETTLE_SEC > 0:
        print(f" auto-settle: {MOCK_AUTO_SETTLE_SEC}s")
    print(f" port       : {PORT}")
    print("=" * 52)
    app.run(host="0.0.0.0", port=PORT, debug=False)
