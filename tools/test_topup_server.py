# ================================================================
# Test E2E alur top up OTOMATIS (server + game).
#
# Jalankan:  python tools/test_topup_server.py
#
# Alur yang diuji (langkah 4-6 terotomatisasi):
#   game klik PAY NOW -> server cetak invoice -> dialog QRIS
#   -> (pembayaran disimulasikan via /api/mock/settle)
#   -> game poll status -> server issue kode -> GOLD MASUK OTOMATIS
#
# Server dijalankan sebagai subprocess (mode mock, DB sementara).
# ================================================================

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = 8391
BASE = f"http://127.0.0.1:{PORT}"


def http(method, path, payload=None, base=BASE):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read()


def main():
    tmpdir = tempfile.mkdtemp(prefix="topup_e2e_")
    db = os.path.join(tmpdir, "test.db")
    env = dict(os.environ, TOPUP_DB_PATH=db, TOPUP_PORT=str(PORT),
               TOPUP_MOCK_AUTO_SETTLE="0")
    server = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "server", "app.py")],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Tunggu server siap
    deadline = time.time() + 20
    ready = False
    while time.time() < deadline:
        try:
            st, body = http("GET", "/healthz")
            h = json.loads(body)
            if st == 200 and h.get("ok") and h.get("mock"):
                ready = True
                break
        except Exception:
            time.sleep(0.3)
    if not ready:
        out = server.stdout.read().decode() if server.stdout else ""
        server.terminate()
        raise SystemExit(f"SERVER TIDAK SIAP:\n{out[-2000:]}")
    print("OK S1: server mock jalan (healthz, mock=True)")

    try:
        # ── S2: API server ──
        st, body = http("POST", "/api/topup/create", {"pkg": "PAKET 50K"})
        inv = json.loads(body)
        assert st == 200 and inv["id"] and inv["status"] == "pending"
        assert inv["amount"] == 10000 and inv["gold"] == 50000
        st, body = http("GET", f"/api/topup/status/{inv['id']}")
        assert json.loads(body)["status"] == "pending"
        st, body = http("GET", f"/api/topup/qr/{inv['id']}")
        assert st == 200 and body[:4] == b"\x89PNG", "QR bukan PNG"
        print(f"OK S2: invoice {inv['id']} dibuat, QR PNG tersaji")

        # ── S3: settle (simulasi pemain bayar) -> kode otomatis ──
        st, body = http("POST", f"/api/mock/settle/{inv['id']}")
        code = json.loads(body)["code"]
        assert code.startswith("MA-") and len(code) == 9
        st, body = http("GET", f"/api/topup/status/{inv['id']}")
        s = json.loads(body)
        assert s["status"] == "settled" and s["code"] == code
        # Idempoten: settle ulang -> kode sama
        st, body = http("POST", f"/api/mock/settle/{inv['id']}")
        assert json.loads(body)["code"] == code
        print(f"OK S3: pembayaran settle -> kode {code} ter-issue "
              f"(idempoten)")

        # ═══ GAME E2E ═══
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        sys.path.insert(0, ROOT)
        import pygame  # noqa: E402
        import _core  # noqa: E402
        from _core import Menu, MenuState, TOPUP_PACKAGES  # noqa: E402

        pygame.init()
        screen = pygame.display.set_mode((_core.SCREEN_WIDTH,
                                          _core.SCREEN_HEIGHT))
        menu = Menu(screen)
        menu.topup_server_url = BASE  # aktifkan alur server

        # ── S4: game -> QRIS -> gold otomatis ──
        menu.state = MenuState.HERO_SHOP
        menu.draw()
        menu._on_button_click("topup_open")
        menu.draw()
        assert menu.topup_phase == "select"
        gold_before = menu.meta_gold
        menu._on_button_click("topup_pay")
        assert menu.topup_phase == "paying"

        settled_at_frame = None
        settled_code = None
        for frame in range(60 * 30):  # timeout 30 detik (frame)
            menu.update()
            menu.draw()
            # Simulasikan pemain membayar setelah dialog QR tampil
            # (settle INVOICE BARU yang dibuat game, bukan yang lama)
            if (settled_at_frame is None
                    and menu.topup_pay_state == "awaiting"
                    and frame > 10 and menu.topup_invoice):
                st, body = http(
                    "POST",
                    f"/api/mock/settle/{menu.topup_invoice['id']}")
                settled_code = json.loads(body)["code"]
                settled_at_frame = frame
            if menu.topup_phase == "success":
                break
        assert menu.topup_phase == "success", \
            f"gold tidak masuk otomatis (phase={menu.topup_phase}, " \
            f"pay_state={menu.topup_pay_state})"
        assert menu.meta_gold == gold_before + 50000
        h = menu.save_data["topup_history"][-1]
        assert h["method"] == "redeem" and h["code"] == settled_code
        assert h["gold"] == 50000
        print(f"OK S4: GOLD MASUK OTOMATIS (+50,000, kode {settled_code}) "
              f"tanpa pemain mengetik apa pun")

        # ── S5: QR benar-benar ter-download & ter-render ──
        assert menu._topup_qr_bytes and menu._topup_qr_bytes[:4] == \
            b"\x89PNG", "QR tidak ter-download ke game"
        print("OK S5: QRIS ter-download & ter-render di dialog")

        # ── S6: path error (server mati) -> UI error + tombol ──
        menu.draw()
        menu._on_button_click("topup_back")
        menu.topup_server_url = "http://127.0.0.1:1"  # port mati
        menu._on_button_click("topup_open")
        menu.draw()
        menu._on_button_click("topup_pay")
        for frame in range(60 * 5):
            menu.update()
            menu.draw()
            if menu.topup_pay_state == "error":
                break
        assert menu.topup_pay_state == "error", "error state tidak tercapai"
        menu.draw()
        assert "topup_retry" in menu.buttons
        assert "topup_cancel_pay" in menu.buttons
        menu._on_button_click("topup_cancel_pay")
        assert menu.topup_phase == "select"
        print("OK S6: server mati -> UI error + TRY AGAIN/BACK berfungsi")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\nSEMUA TES E2E SERVER LULUS")


if __name__ == "__main__":
    main()
