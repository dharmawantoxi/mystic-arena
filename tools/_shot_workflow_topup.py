#!/usr/bin/env python3
# ================================================================
# tools/_shot_workflow_topup.py
#
# Menghasilkan screenshot step-by-step ALUR TRANSAKSI TOP UP
# (pemesanan paket -> checkout QRIS -> verifikasi pembayaran ->
# gold masuk otomatis) untuk dokumen
# docs/WORKFLOW_TRANSAKSI_MIDTRANS.pdf.
#
# Semua gambar berasal dari KODE ASLI repo ini yang benar-benar
# dijalankan headless (SDL dummy), bukan mock-up:
#   - UI: _core.py (Menu._draw_topup_* / _draw_hero_shop)
#   - Backend: server/app.py (invoice, QR, status, settle, webhook)
#
# Dua mode dijalankan:
#   A. MOCK      : server tanpa API key (default server/app.py)
#   B. MIDTRANS  : server dengan TOPUP_MIDTRANS_SERVER_KEY terisi.
#                  Karena kredensial sandbox Midtrans tidak ada di
#                  lingkungan build, API Midtrans di-emulasi stub
#                  lokal (POST /v2/invoice + qr_code_url) sehingga
#                  CABANG KODE MIDTRANS yang asli tetap tereksekusi:
#                  invoice lewat HTTP, QR di-proxy dari qr_code_url,
#                  pembayaran dikonfirmasi via POST /webhooks/midtrans.
#
# Jalankan:
#     pip install pygame-ce flask qrcode pillow
#     python tools/_shot_workflow_topup.py
#
# Keluaran:
#     docs/workflow_transaksi/*.png        (screenshot tiap langkah)
#     docs/workflow_transaksi/_artifacts.json  (payload nyata hasil run)
#     docs/workflow_transaksi/_server_log.txt  (log server top up)
# ================================================================

import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "workflow_transaksi")

# Driver dummy + locale Indonesia (region ID -> currency IDR) harus
# diset SEBELUM modul game di-import.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("LANG", "id_ID.UTF-8")
os.environ.setdefault("LC_ALL", "id_ID.UTF-8")
sys.path.insert(0, ROOT)

PORT_MOCK = 8391
PORT_MT = 8392
PORT_STUB = 8399
STUB_KEY = "SB-Stub-Demo-Key"     # pengganti server key sandbox
STUB_BASE = f"http://127.0.0.1:{PORT_STUB}"

ART = {}          # payload nyata hasil run (untuk lampiran PDF)
LOGS = {}         # stdout server top up


# ────────────────────────────────────────────────
# HTTP helper
# ────────────────────────────────────────────────

def http(method, path, payload=None, base=None, headers=None):
    if payload is None:
        raw = None
    elif isinstance(payload, (bytes, bytearray)):
        raw = bytes(payload)          # body mentah (webhook ber-signature)
    else:
        raw = json.dumps(payload).encode()
    req = urllib.request.Request(base + path, data=raw, method=method)
    if raw is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:      # 4xx/5xx = hasil yang sah
        return e.code, e.read()


def wait_server(port, timeout=25):
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            st, body = http("GET", "/healthz", base=base)
            if st == 200:
                return base, json.loads(body)
        except Exception:
            time.sleep(0.25)
    raise SystemExit(f"server top up di port {port} tidak siap")


def start_topup_server(port, db, extra_env=None):
    env = dict(os.environ, TOPUP_DB_PATH=db, TOPUP_PORT=str(port),
               TOPUP_MOCK_AUTO_SETTLE="0")
    env.update(extra_env or {})
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "server", "app.py")],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    base, health = wait_server(port)
    return proc, base, health


# ────────────────────────────────────────────────
# STUB API MIDTRANS (menggantikan api.sandbox.midtrans.com)
# ────────────────────────────────────────────────

STUB_CALLS = []
QR_DIR = tempfile.mkdtemp(prefix="stub_qr_")


def _make_qris_png(order_id, amount):
    """QR bergaya QRIS (payload EMVCo disederhanakan) - stub lokal."""
    import qrcode
    payload = (f"00020101021226580014ID.CO.QRIS.WWW0215ID10{order_id[-9:]}"
               f"51370014ID.CO.GOPAY.WWW0223stub-demo-merchant-mystic"
               f"52044812530336054{len(str(amount)):02d}{amount}"
               f"5802ID5913MYSTIC ARENA6007JAKARTA")
    img = qrcode.make(payload, box_size=8, border=2)
    path = os.path.join(QR_DIR, f"{order_id}.png")
    img.save(path)
    return path


class StubMidtrans(BaseHTTPRequestHandler):
    """Endpoint Midtrans yang dipakai server/app.py:
       POST /v2/invoice  -> {invoice_url, qr_code_url, ...}
       GET  /qr/<id>.png -> gambar QRIS
    """

    def log_message(self, *a):     # diamkan log default
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/v2/invoice":
            return self._json({"error": "not_found"}, 404)
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        STUB_CALLS.append({
            "method": "POST",
            "path": self.path,
            "authorization": self.headers.get("Authorization", ""),
            "content_type": self.headers.get("Content-Type", ""),
            "body": body,
        })
        oid = body.get("transaction_id", "unknown")
        amt = body.get("gross_amount", 0)
        qr = _make_qris_png(oid, amt)
        ART.setdefault("midtrans", {})["create_request"] = STUB_CALLS[-1]
        ART["midtrans"]["qr_file"] = qr
        self._json({
            "id": oid,
            "invoice_url": f"{STUB_BASE}/invoice/{oid}",
            "qr_code_url": f"{STUB_BASE}/qr/{oid}.png",
            "status": "PENDING",
            "merchant_id": "G-STUB-DEMO",
            "amount": amt,
            "currency": body.get("currency", "IDR"),
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    def do_GET(self):
        if self.path.startswith("/qr/") and self.path.endswith(".png"):
            name = os.path.basename(self.path)
            path = os.path.join(QR_DIR, name)
            if not os.path.exists(path):
                return self._json({"error": "no_qr"}, 404)
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._json({"error": "not_found"}, 404)


# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)

    import pygame
    import _core
    from _core import Menu, MenuState

    pygame.init()
    screen = pygame.display.set_mode((_core.SCREEN_WIDTH,
                                      _core.SCREEN_HEIGHT))

    shots = []

    def grab(name, note=""):
        path = os.path.join(OUT, name)
        pygame.image.save(screen, path)
        shots.append({"file": name, "note": note})
        print(f"  [shot] {name}" + (f"  <- {note}" if note else ""))

    def frames(menu, n=1):
        for _ in range(n):
            menu.update()
            menu.draw()

    tmp = tempfile.mkdtemp(prefix="workflow_topup_")
    servers = []

    # ═══════════════════════════════════════════════
    # RUN A — mode MOCK (tanpa API key Midtrans)
    # ═══════════════════════════════════════════════
    print("\n=== RUN A: mode MOCK ===")
    srv_a, base_a, health_a = start_topup_server(
        PORT_MOCK, os.path.join(tmp, "a.db"))
    servers.append(srv_a)
    ART["mode_mock"] = {"healthz": health_a, "base": base_a}
    print(f"  server mock siap: {health_a}")

    menu = Menu(screen)
    menu.topup_server_url = base_a

    # Saldo awal dibuat 0 supaya efek top up terlihat jelas.
    menu.meta_gold = 0
    menu.save_data["meta_gold"] = 0
    from _system import SaveManager
    SaveManager.save(menu.save_data)

    # ── 01. Menu utama ──
    menu.state = MenuState.MAIN
    frames(menu, 40)
    grab("01_menu_utama.png", "Menu utama Mystic Arena")

    # ── 02. Hero Shop (saldo + tombol TOP UP) ──
    menu.state = MenuState.HERO_SHOP
    frames(menu, 10)
    assert "topup_open" in menu.buttons
    grab("02_hero_shop.png", "Hero Shop: saldo Hero Gold + tombol TOP UP")

    # ── 03. Dialog top up: pilih paket ──
    menu._on_button_click("topup_open")
    frames(menu, 3)
    assert menu.topup_open and menu.topup_phase == "select"
    ART["currency"] = menu.topup_currency
    grab("03_pilih_paket.png", "Dialog TOP UP: pilih paket")

    # ── 04. Pilih metode pembayaran ──
    menu._on_button_click("topup_method_2")       # DANA
    frames(menu, 2)
    assert menu.topup_method_idx == 2
    grab("04_pilih_metode.png", "Pilih metode pembayaran (DANA)")

    # ── 05. PAY NOW -> server mencetak invoice ──
    menu._on_button_click("topup_pay")
    menu.draw()
    assert menu.topup_phase == "paying" and menu.topup_pay_state == "creating"
    grab("05_mencetak_invoice.png", "PREPARING PAYMENT: invoice dicetak server")

    # ── 06. Checkout QRIS ──
    for i in range(600):
        frames(menu)
        if menu.topup_pay_state == "awaiting" and menu._topup_qr_bytes:
            break
    assert menu.topup_pay_state == "awaiting", menu.topup_pay_state
    assert menu._topup_qr_bytes[:4] == b"\x89PNG"
    inv = menu.topup_invoice
    ART["invoice"] = inv
    st, body = http("GET", f"/api/topup/status/{inv['id']}", base=base_a)
    ART["status_pending"] = {"http": st, "json": json.loads(body)}
    grab("06_checkout_qris.png", "Checkout QRIS: scan & bayar")

    # QR close-up (byte PNG asli dari server, bukan hasil crop layar)
    with open(os.path.join(OUT, "07_qris_closeup.png"), "wb") as f:
        f.write(menu._topup_qr_bytes)
    shots.append({"file": "07_qris_closeup.png",
                  "note": "QR pembayaran (PNG dari /api/topup/qr/<id>)"})
    print("  [shot] 07_qris_closeup.png")

    # ── 07. Pemain membayar -> menunggu verifikasi ──
    st, body = http("POST", f"/api/mock/settle/{inv['id']}", base=base_a)
    settle = json.loads(body)
    ART["settle"] = {"http": st, "json": settle}
    frames(menu, 1)
    grab("08_menunggu_verifikasi.png",
         "Sudah dibayar, game menunggu konfirmasi (poll status)")

    # ── 08. Gold masuk otomatis ──
    for i in range(60 * 40):
        frames(menu)
        if menu.topup_phase == "success":
            break
    assert menu.topup_phase == "success", menu.topup_phase
    ART["gold_after_mock"] = menu.meta_gold
    ART["history_entry"] = menu.save_data["topup_history"][-1]
    grab("09_pembayaran_sukses.png", "TOP UP sukses: gold masuk otomatis")

    # ── 09. Saldo bertambah di Hero Shop ──
    menu._on_button_click("topup_back")
    frames(menu, 6)
    assert menu.meta_gold == 50000, menu.meta_gold
    grab("10_saldo_masuk.png", "Hero Shop: saldo Hero Gold bertambah")

    # ── 10. Jalur error (server tidak terjangkau) ──
    menu.topup_server_url = "http://127.0.0.1:1"
    menu._on_button_click("topup_open")
    menu.draw()
    menu._on_button_click("topup_pay")
    for i in range(60 * 8):
        frames(menu)
        if menu.topup_pay_state == "error":
            break
    assert menu.topup_pay_state == "error"
    assert "topup_retry" in menu.buttons
    grab("11_error_server.png", "Gagal hubungi server: TRY AGAIN / BACK")
    menu._on_button_click("topup_cancel_pay")

    # ── 11. Alur cadangan: redeem kode manual ──
    frames(menu, 2)
    menu._on_button_click("topup_redeem")
    for ch in "123456":
        menu._on_button_click(f"vpk_{ch}")
    frames(menu, 2)
    grab("12_redeem_manual.png", "Alur cadangan: redeem kode manual")

    srv_a.terminate()
    LOGS["mock"] = _drain(srv_a)

    # ═══════════════════════════════════════════════
    # RUN B — mode MIDTRANS (API Midtrans = stub lokal)
    # ═══════════════════════════════════════════════
    print("\n=== RUN B: mode MIDTRANS (API Midtrans di-stub lokal) ===")
    stub = ThreadingHTTPServer(("127.0.0.1", PORT_STUB), StubMidtrans)
    threading.Thread(target=stub.serve_forever, daemon=True).start()

    srv_b, base_b, health_b = start_topup_server(
        PORT_MT, os.path.join(tmp, "b.db"),
        {"TOPUP_MIDTRANS_SERVER_KEY": STUB_KEY,
         "TOPUP_MIDTRANS_API": STUB_BASE})
    servers.append(srv_b)
    assert health_b.get("mock") is False, "server harus mode MIDTRANS"
    ART["mode_midtrans"] = {"healthz": health_b, "base": base_b,
                            "stub_api": STUB_BASE}
    print(f"  server mode MIDTRANS siap: {health_b}")

    mb = Menu(screen)
    mb.topup_server_url = base_b
    # Reset saldo run B supaya efek +50.000 terlihat bersih.
    mb.meta_gold = 0
    mb.save_data["meta_gold"] = 0
    SaveManager.save(mb.save_data)
    mb.state = MenuState.HERO_SHOP
    frames(mb, 6)
    grab("13_midtrans_hero_shop.png", "Hero Shop sebelum transaksi Midtrans")

    mb._on_button_click("topup_open")
    frames(mb, 3)
    grab("14_midtrans_pilih_paket.png", "Pilih paket (mode Midtrans)")

    mb._on_button_click("topup_pay")
    mb.draw()
    assert mb.topup_phase == "paying"
    grab("15_midtrans_mencetak_invoice.png",
         "Server memanggil API invoice Midtrans")

    for i in range(600):
        frames(mb)
        if mb.topup_pay_state == "awaiting" and mb._topup_qr_bytes:
            break
    assert mb.topup_pay_state == "awaiting", mb.topup_pay_state
    assert mb.topup_invoice.get("mock") is False, \
        "invoice harus buatan Midtrans (bukan mock)"
    inv_b = mb.topup_invoice
    ART["midtrans"]["invoice"] = inv_b
    ART["midtrans"]["qr_bytes_len"] = len(mb._topup_qr_bytes)
    grab("16_midtrans_checkout_qris.png",
         "Checkout QRIS dari Midtrans (tanpa badge MOCK)")
    with open(os.path.join(OUT, "17_midtrans_qris_closeup.png"),
              "wb") as f:
        f.write(mb._topup_qr_bytes)
    shots.append({"file": "17_midtrans_qris_closeup.png",
                  "note": "QR Midtrans yang di-proxy server"})
    print("  [shot] 17_midtrans_qris_closeup.png")

    # ── Webhook Midtrans: pembayaran terverifikasi ──
    notif = {
        "transaction_id": inv_b["id"],
        "order_id": inv_b["id"],
        "status_code": "200",
        "transaction_status": "settle",
        "payment_type": "qris",
        "gross_amount": f"{inv_b['amount']}.00",
        "currency": "IDR",
        "fraud_status": "accept",
        "transaction_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    raw = json.dumps(notif).encode()
    sig = hmac.new(STUB_KEY.encode(), raw, hashlib.sha512).hexdigest()
    st, body = http("POST", "/webhooks/midtrans", payload=raw,
                    base=base_b, headers={"x-signature-1": sig})
    ART["midtrans"]["webhook"] = {
        "payload": notif,
        "header_x_signature_1": sig,
        "response_http": st,
        "response_json": json.loads(body),
    }
    print(f"  webhook Midtrans -> HTTP {st} {body.decode()}")

    # Signature salah harus ditolak (bukti validasi berjalan).
    st_bad, body_bad = http(
        "POST", "/webhooks/midtrans", payload=raw, base=base_b,
        headers={"x-signature-1": "0" * 128})
    ART["midtrans"]["webhook_bad_signature"] = {
        "response_http": st_bad, "response_json": json.loads(body_bad)}
    print(f"  webhook signature salah -> HTTP {st_bad}")

    frames(mb, 1)
    grab("18_midtrans_menunggu_verifikasi.png",
         "Menunggu game membaca status settle")

    for i in range(60 * 40):
        frames(mb)
        if mb.topup_phase == "success":
            break
    assert mb.topup_phase == "success", mb.topup_phase
    st, body = http("GET", f"/api/topup/status/{inv_b['id']}", base=base_b)
    ART["midtrans"]["status_settled"] = {"http": st,
                                         "json": json.loads(body)}
    ART["gold_after_midtrans"] = mb.meta_gold
    grab("19_midtrans_pembayaran_sukses.png",
         "Webhook settle -> gold masuk otomatis")

    mb._on_button_click("topup_back")
    frames(mb, 6)
    grab("20_midtrans_saldo_masuk.png", "Saldo bertambah setelah settle")

    srv_b.terminate()
    LOGS["midtrans"] = _drain(srv_b)
    stub.shutdown()

    # ── Tulis artefak nyata ──
    ART["shots"] = shots
    ART["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    ART["git_commit"] = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
        capture_output=True, text=True).stdout.strip()
    with open(os.path.join(OUT, "_artifacts.json"), "w",
              encoding="utf-8") as f:
        json.dump(ART, f, indent=2, ensure_ascii=False, default=str)
    with open(os.path.join(OUT, "_server_log.txt"), "w",
              encoding="utf-8") as f:
        for k, v in LOGS.items():
            f.write(f"===== server top up ({k}) =====\n{v}\n")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(QR_DIR, ignore_errors=True)
    print(f"\n{len(shots)} screenshot + artefak tersimpan di "
          f"{os.path.relpath(OUT, ROOT)}")


def _drain(proc):
    """Ambil stdout server (sudah di-terminate oleh pemanggil)."""
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    try:
        return (proc.stdout.read() or b"").decode(errors="replace")
    except Exception:
        return ""


if __name__ == "__main__":
    main()
