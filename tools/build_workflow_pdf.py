#!/usr/bin/env python3
# ================================================================
# tools/build_workflow_pdf.py
#
# Menyusun dokumen PDF "WORKFLOW TRANSAKSI — Pemesanan sampai
# Checkout Pembayaran Midtrans" dari screenshot asli hasil
# tools/_shot_workflow_topup.py (bukan mock-up: UI + server asli
# repo ini dijalankan headless).
#
# Jalankan (urutan):
#     python tools/_shot_workflow_topup.py
#     python tools/build_workflow_pdf.py
# Keluaran: docs/WORKFLOW_TRANSAKSI_MIDTRANS.pdf
#
# Dependensi: pip install reportlab pillow
# ================================================================

import json
import os

from PIL import Image, ImageDraw, ImageFont

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image as RLImage, KeepTogether,
                                PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "docs", "workflow_transaksi")
PDF_OUT = os.path.join(ROOT, "docs", "WORKFLOW_TRANSAKSI_MIDTRANS.pdf")

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

ART = json.load(open(os.path.join(SHOTS, "_artifacts.json"),
                     encoding="utf-8"))
LOG = open(os.path.join(SHOTS, "_server_log.txt"), encoding="utf-8").read()


# ────────────────────────────────────────────────
# Diagram urutan (digambar dengan PIL)
# ────────────────────────────────────────────────

def build_diagram(path):
    W, H = 1560, 1080
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_actor = ImageFont.truetype(FONTB, 26)
    f_lab = ImageFont.truetype(FONT, 19)
    f_api = ImageFont.truetype(FONTM, 17)

    xs = {"pemain": 170, "game": 560, "server": 980, "midtrans": 1380}
    names = {"pemain": "PEMAIN", "game": "GAME (KLIENT)",
             "server": "SERVER TOP UP", "midtrans": "MIDTRANS"}
    boxc = {"pemain": (70, 90, 160), "game": (24, 120, 78),
            "server": (140, 100, 20), "midtrans": (150, 40, 60)}

    top = 120
    d.rectangle((20, 20, W - 20, top - 20), outline=(120, 120, 120),
                width=2)
    d.text((40, 44), "DIAGRAM URUTAN — TRANSAKSI TOP UP "
                     "(PEMESANAN → CHECKOUT MIDTRANS → GOLD OTOMATIS)",
           font=f_actor, fill=(20, 20, 20))

    for k, x in xs.items():
        w = d.textlength(names[k], font=f_actor) + 36
        d.rectangle((x - w / 2, top - 44, x + w / 2, top + 4),
                    fill=boxc[k], outline=(30, 30, 30), width=2)
        d.text((x - w / 2 + 18, top - 36), names[k], font=f_actor,
               fill="white")
        for y in range(top + 10, H - 30, 12):
            d.line((x, y, x, min(y + 6, H - 30)), fill=(160, 160, 160),
                   width=2)

    BLUE, GREEN, ORANGE, PURPLE = ((30, 80, 190), (20, 130, 70),
                                   (210, 120, 20), (120, 50, 160))

    def arrow(y, a, b, label, sub, color):
        x1, x2 = xs[a], xs[b]
        d.line((x1, y, x2, y), fill=color, width=3)
        s = 12 if x2 > x1 else -12
        d.polygon([(x2, y), (x2 - s, y - 7), (x2 - s, y + 7)], fill=color)
        mx = (x1 + x2) / 2
        d.text((mx - d.textlength(label, font=f_lab) / 2, y - 46),
               label, font=f_lab, fill=(20, 20, 20))
        d.text((mx - d.textlength(sub, font=f_api) / 2, y - 25), sub,
               font=f_api, fill=color)

    def self_arrow(y, a, label, sub, color):
        x = xs[a]
        d.line((x, y, x + 120, y), fill=color, width=3)
        d.line((x + 120, y, x + 120, y + 34), fill=color, width=3)
        d.line((x + 120, y + 34, x, y + 34), fill=color, width=3)
        d.polygon([(x, y + 34), (x + 12, y + 27), (x + 12, y + 41)],
                  fill=color)
        d.text((x + 140, y + 8), label, font=f_lab, fill=(20, 20, 20))
        d.text((x + 140, y + 30), sub, font=f_api, fill=color)

    y = top + 60
    STEP = 92
    arrow(y, "pemain", "game", "1. Ketuk TOP UP, pilih paket + metode,",
          "   lalu PAY NOW", BLUE); y += STEP
    arrow(y, "game", "server", "2. POST /api/topup/create  {pkg}",
          "   -> invoice 'pending' + qr_url", BLUE); y += STEP
    arrow(y, "server", "midtrans", "3. POST /v2/invoice (Server Key)",
          "   transaction_id, gross_amount, currency", BLUE); y += STEP
    arrow(y, "midtrans", "server", "4. Response invoice",
          "   {qr_code_url, invoice_url}", GREEN); y += STEP
    arrow(y, "server", "game", "5. GET /api/topup/qr/<id>  (proxy QR)",
          "   dialog checkout menampilkan QRIS", GREEN); y += STEP
    arrow(y, "pemain", "midtrans", "6. Pemain scan QRIS & membayar",
          "   via e-wallet / m-banking", ORANGE); y += STEP
    arrow(y, "midtrans", "server", "7. Webhook notifikasi pembayaran",
          "   transaction_status + signature", ORANGE); y += STEP
    self_arrow(y, "server", "8. Validasi signature, status settled,",
               "issue kode redeem MA-XXXXXX", PURPLE); y += STEP + 34
    arrow(y, "game", "server", "9. Poll GET /api/topup/status/<id>",
          "   tiap +/- 2 detik", BLUE); y += STEP
    arrow(y, "server", "game", "10. status='settled' + code",
          "   (QRIS / e-wallet terverifikasi)", GREEN); y += STEP
    arrow(y, "game", "pemain", "11. Gold masuk OTOMATIS, layar SUKSES",
          "   riwayat transaksi tersimpan", GREEN)

    img.save(path)
    return path


# ────────────────────────────────────────────────
# Helper platypus
# ────────────────────────────────────────────────

STYLES = getSampleStyleSheet()
H1_S = ParagraphStyle("h1", parent=STYLES["Heading1"], fontSize=19,
                    spaceBefore=10, spaceAfter=8,
                    textColor=colors.HexColor("#1a2a5e"))
H2_S = ParagraphStyle("h2", parent=STYLES["Heading2"], fontSize=14,
                    spaceBefore=12, spaceAfter=6,
                    textColor=colors.HexColor("#28407c"))
H3_S = ParagraphStyle("h3", parent=STYLES["Heading3"], fontSize=11.5,
                    spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor("#4a4a4a"))
BODY = ParagraphStyle("body", parent=STYLES["BodyText"], fontSize=9.5,
                      leading=13.5, alignment=TA_LEFT)
CAP = ParagraphStyle("cap", parent=BODY, fontSize=8.5, leading=11.5,
                     textColor=colors.HexColor("#555555"),
                     alignment=TA_CENTER, spaceAfter=10)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.5, leading=12)


def H1(t): return Paragraph(t, H1_S)


def H2(t): return Paragraph(t, H2_S)


def H3(t): return Paragraph(t, H3_S)
TITLE_S = ParagraphStyle("t", parent=STYLES["Title"], fontSize=27,
                         leading=32, textColor=colors.HexColor("#1a2a5e"))
SUB_S = ParagraphStyle("s", parent=BODY, fontSize=13, leading=18,
                       alignment=TA_CENTER,
                       textColor=colors.HexColor("#555555"))
COVER = ParagraphStyle("c", parent=BODY, fontSize=10.5, leading=16,
                       alignment=TA_CENTER)


def shot(name, width_mm=168):
    p = os.path.join(SHOTS, name)
    with Image.open(p) as im:
        w, h = im.size
    ratio = h / float(w)
    wpt = width_mm * mm
    return RLImage(p, width=wpt, height=wpt * ratio)


def codeblock(text, size=7.4):
    st = ParagraphStyle("code", fontName="Courier", fontSize=size,
                        leading=size + 2.6,
                        textColor=colors.HexColor("#222222"))
    t = Table([[Preformatted(text, st)]], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f2f2")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.4,
                      leading=11)
CELLB = ParagraphStyle("cellb", fontName="Helvetica-Bold",
                       fontSize=8.6, leading=11, textColor=colors.white)


def tbl(rows, widths=None, header=True):
    data = []
    for r, row in enumerate(rows):
        out = []
        for val in row:
            if isinstance(val, str):
                out.append(Paragraph(val, CELLB if (header and r == 0)
                                     else CELL))
            else:
                out.append(val)
        data.append(out)
    t = Table(data, hAlign="LEFT", colWidths=widths)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbbbbb")),
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8.4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0),
                   colors.HexColor("#1a2a5e")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    t.setStyle(TableStyle(style))
    return t


def step_block(no, title, img_file, caption, bullets, extra=None):
    el = [H2(f"Langkah {no} — {title}")]
    el.append(shot(img_file))
    el.append(Paragraph(caption, CAP))
    for b in bullets:
        el.append(Paragraph(f"&bull;  {b}", BODY))
    if extra:
        el.append(Spacer(1, 4))
        el.append(extra)
    el.append(Spacer(1, 10))
    return KeepTogether(el) if False else el  # gambar besar: biarkan mengalir


def jdump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


# ────────────────────────────────────────────────
# Isi dokumen
# ────────────────────────────────────────────────

def build():
    diag = build_diagram(os.path.join(SHOTS, "00_diagram_urutan.png"))

    story = []
    inv = ART["invoice"]
    mt = ART["midtrans"]

    # ── COVER ──
    story += [Spacer(1, 55 * mm),
              Paragraph("MYSTIC ARENA", TITLE_S),
              Spacer(1, 3 * mm),
              Paragraph("WORKFLOW TRANSAKSI TOP UP", TITLE_S),
              Spacer(1, 6 * mm),
              Paragraph("Dari tahap pemesanan paket sampai checkout "
                        "pembayaran<br/>via QRIS / Midtrans — screenshot "
                        "step by step", SUB_S),
              Spacer(1, 14 * mm),
              shot("06_checkout_qris.png", width_mm=120),
              Spacer(1, 12 * mm),
              Paragraph(f"Dokumen disusun otomatis dari eksekusi nyata "
                        "aplikasi &amp; server top up<br/>"
                        f"(commit <font name='Courier'>{ART['git_commit']}"
                        "</font> &middot; dibuat "
                        f"{ART['generated_at']})", COVER),
              Spacer(1, 4 * mm),
              Paragraph("Mode A: simulasi (mock) &middot; Mode B: branch "
                        "Midtrans aktif (API Midtrans di-stub lokal)",
                        COVER),
              PageBreak()]

    # ── 1. RINGKASAN ──
    story.append(H1("1. Ringkasan Alur"))
    story.append(Paragraph(
        "Mystic Arena menjual <b>Hero Gold</b> (mata uang meta untuk "
        "membuka hero di Hero Shop). Transaksi top up berjalan melalui "
        "empat pihak di bawah ini. Semua screenshot pada dokumen ini "
        "diambil dari <b>eksekusi headless kode asli repositori</b> "
        "(<font name='Courier'>_core.py</font> untuk UI dan "
        "<font name='Courier'>server/app.py</font> untuk backend), "
        "bukan mock-up desain.", BODY))
    story.append(Spacer(1, 4))
    story.append(tbl([
        ["Aktor", "Peran", "Kode"],
        ["Pemain", "Memilih paket, memilih metode, scan QRIS & membayar",
         "-"],
        ["Game (klien pygame)", "Dialog TOP UP, menampilkan checkout "
         "QRIS, poll status, menambah gold otomatis",
         "_core.py (Menu._draw_topup_*, _topup_server_tick, "
         "_redeem_grant)"],
        ["Server top up (Flask)", "Cetak invoice, proxy QR, terima "
         "webhook, issue kode redeem", "server/app.py"],
        ["Midtrans", "Payment gateway: QRIS / e-wallet / VA bank, "
         "notifikasi pembayaran", "POST /v2/invoice, webhook"],
    ], widths=[30 * mm, 75 * mm, 65 * mm]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Prinsip keamanan yang dipakai: <b>game tidak pernah menambah "
        "gold sendiri</b> — penambahan hanya terjadi setelah server "
        "menyatakan transaksi <font name='Courier'>settled</font> "
        "(diverifikasi webhook Midtrans), lalu game membaca kode redeem "
        "lewat polling. Alur manual REDEEM CODE tersedia sebagai "
        "cadangan.", BODY))
    story.append(Spacer(1, 6))
    story.append(H3("Diagram urutan"))
    with Image.open(diag) as im:
        w, h = im.size
    story.append(RLImage(diag, width=170 * mm,
                         height=170 * mm * h / float(w)))
    story.append(Paragraph("Gambar 0. Diagram urutan transaksi "
                           "(nomor langkah mengikuti Bab 2-3).", CAP))
    story.append(PageBreak())

    # ── 2. LANGKAH MODE A ──
    story.append(H1("2. Step by Step — Pemesanan s.d. Checkout "
                    "(Mode Simulasi)"))
    story.append(Paragraph(
        "Mode simulasi adalah kondisi default "
        "<font name='Courier'>server/app.py</font> tanpa API key "
        "(badge MOCK MODE tampil transparan di checkout). Bab 3 "
        "mengulang alur yang sama dengan branch Midtrans aktif.", BODY))

    story += step_block(
        1, "Masuk ke permainan", "01_menu_utama.png",
        "Screenshot 1. Menu utama Mystic Arena.",
        ["Pemain menjalankan game; menu utama menampilkan PLAY GAME, "
         "CONTINUE, dan HERO SHOP.",
         "Fitur top up berada di dalam HERO SHOP (mata uang meta dipakai "
         "untuk membuka hero)."])

    story += step_block(
        2, "Buka Hero Shop — lihat saldo & tombol TOP UP",
        "02_hero_shop.png",
        "Screenshot 2. Hero Shop: chip saldo HERO GOLD (kiri atas) dan "
        "tombol TOP UP di sebelahnya.",
        ["Chip <b>HERO GOLD</b> menampilkan saldo meta_gold dari save "
         "(<font name='Courier'>_core.py:3132</font>).",
         "Tombol <b>TOP UP</b> (<font name='Courier'>_core.py:4829</font>) "
         "membuka dialog transaksi."])

    story += step_block(
        3, "Pilih paket (pemesanan)", "03_pilih_paket.png",
        "Screenshot 3. Dialog TOP UP HERO GOLD — kolom kiri memilih paket.",
        ["Paket diambil dari <font name='Courier'>TOPUP_PACKAGES</font> "
         "(<font name='Courier'>_core.py:3068</font>): PAKET 50K = "
         "Rp 10.000 &rarr; +50,000 gold.",
         "Harga ditampilkan dalam mata uang terdeteksi region perangkat "
         "(di sini <b>IDR</b>, lihat "
         "<font name='Courier'>topup_currency.detect_currency()</font>).",
         "Ringkasan TOTAL GOLD + harga total diperbarui otomatis."])

    story += step_block(
        4, "Pilih metode pembayaran", "04_pilih_metode.png",
        "Screenshot 4. Kolom kanan: metode pembayaran (GoPay/OVO/DANA/"
        "ShopeePay/Bank Transfer) + jalur cadangan REDEEM CODE.",
        ["Metode bersifat pilihan display; eksekusi pembayaran dilakukan "
         "gateway di tahap checkout (QRIS mendukung semua e-wallet).",
         "Tombol <b>PAY NOW &bull; Rp 10.000</b> memulai pemesanan "
         "invoice."])

    story.append(H2("Langkah 5 — PAY NOW: server mencetak invoice"))
    story.append(shot("05_mencetak_invoice.png"))
    story.append(Paragraph("Screenshot 5. Fase 'PREPARING PAYMENT' "
                           "sesaat setelah PAY NOW.", CAP))
    story.append(Paragraph(
        "Game memanggil <font name='Courier'>POST /api/topup/create</font> "
        "(<font name='Courier'>_core.py:5381 _topup_send_create</font>) "
        "dan server menyimpan invoice berstatus "
        "<font name='Courier'>pending</font> "
        "(<font name='Courier'>server/app.py:150 create_topup</font>). "
        "Response nyata dari eksekusi ini:", BODY))
    story.append(codeblock(jdump(ART["status_pending"]["json"])))
    story.append(Spacer(1, 8))

    story.append(H2("Langkah 6 — Checkout QRIS"))
    story.append(shot("06_checkout_qris.png"))
    story.append(Paragraph("Screenshot 6. Dialog checkout: QR di kiri, "
                           "nominal &amp; ID invoice di kanan.", CAP))
    story.append(Paragraph(
        "Game mengunduh QR dari "
        "<font name='Courier'>GET /api/topup/qr/&lt;id&gt;</font> "
        "(<font name='Courier'>_core.py _topup_server_tick</font> "
        "purpose='qr'; <font name='Courier'>server/app.py:212 "
        "topup_qr</font>) lalu menampilkan tombol I'VE PAID / CANCEL. "
        "Status saat ini:", BODY))
    story.append(codeblock(f'GET /api/topup/status/{inv["id"]}\n'
                           + jdump(ART["status_pending"]["json"])))
    story.append(Spacer(1, 4))
    story.append(shot("07_qris_closeup.png", width_mm=70))
    story.append(Paragraph("Screenshot 7. QR pembayaran — byte PNG asli "
                           "yang disajikan server (payload simulasi pada "
                           "mode mock).", CAP))

    story += step_block(
        8, "Pemain membayar — menunggu verifikasi",
        "08_menunggu_verifikasi.png",
        "Screenshot 8. Setelah pembayaran, dialog tetap 'AWAITING "
        "PAYMENT' sampai status diverifikasi.",
        ["Pemain scan QR dengan aplikasi QRIS/e-wallet mana pun dan "
         "membayar.",
         "Game melakukan polling "
         "<font name='Courier'>GET /api/topup/status/&lt;id&gt;</font> "
         "tiap &plusmn;2 detik (<font name='Courier'>_core.py:5391 "
         "_topup_server_tick</font>).",
         "Pada mode mock, pembayaran disimulasikan lewat "
         "<font name='Courier'>POST /api/mock/settle/&lt;id&gt;</font> "
         "(di produksi: webhook Midtrans, Bab 3)."])

    story += step_block(
        9, "Pembayaran terverifikasi — gold masuk otomatis",
        "09_pembayaran_sukses.png",
        "Screenshot 9. Dialog sukses menampilkan TX ID dan kode redeem.",
        ["Server men-settle invoice dan meng-issue kode "
         "<font name='Courier'>MA-XXXXXX</font> "
         "(<font name='Courier'>server/app.py:100 _settle_invoice</font>, "
         "idempoten).",
         "Game menerima status settled + kode, lalu "
         "<font name='Courier'>_redeem_grant()</font> "
         "(<font name='Courier'>_core.py:6048</font>) menambah "
         "+50,000 gold <b>tanpa pemain mengetik apa pun</b>.",
         "Transaksi masuk riwayat "
         "<font name='Courier'>save_data['topup_history']</font>:"])
    story.append(codeblock(jdump(ART["history_entry"])))
    story.append(Spacer(1, 8))

    story += step_block(
        10, "Saldo bertambah — siap belanja hero",
        "10_saldo_masuk.png",
        "Screenshot 10. Chip HERO GOLD kini 50,000; hero berbayar dapat "
        "dibuka.",
        ["Pemesanan &rarr; checkout &rarr; pembayaran &rarr; pengiriman "
         "gold selesai dalam satu alur tertutup."])

    story.append(H2("Penanganan kegagalan & alur cadangan"))
    story.append(shot("11_error_server.png"))
    story.append(Paragraph("Screenshot 11. Server tidak terjangkau: "
                           "pesan error + tombol TRY AGAIN / BACK.", CAP))
    story.append(Paragraph(
        "Jika server gagal dihubungi, game menampilkan error dan tombol "
        "TRY AGAIN (cetak invoice ulang) / BACK "
        "(<font name='Courier'>_core.py _topup_pay_fail</font>). "
        "Gold tidak pernah bertambah pada jalur gagal.", BODY))
    story.append(Spacer(1, 4))
    story.append(shot("12_redeem_manual.png"))
    story.append(Paragraph("Screenshot 12. Alur cadangan REDEEM CODE "
                           "(keypad on-screen) untuk voucher manual.", CAP))
    story.append(PageBreak())

    # ── 3. MODE MIDTRANS ──
    story.append(H1("3. Checkout dengan Midtrans (Mode Produksi)"))
    story.append(Paragraph(
        "Dengan <font name='Courier'>TOPUP_MIDTRANS_SERVER_KEY</font> "
        "terisi, <font name='Courier'>MOCK_MODE</font> menjadi False "
        "(<font name='Courier'>server/app.py:53</font>): invoice dicetak "
        "lewat <font name='Courier'>POST {MIDTRANS_API}/v2/invoice</font>, "
        "QR di-proxy dari <font name='Courier'>qr_code_url</font> milik "
        "Midtrans, dan pembayaran dikonfirmasi webhook "
        "<font name='Courier'>/webhooks/midtrans</font>.", BODY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Catatan kejujuran:</b> kredensial sandbox Midtrans tidak "
        "tersedia di lingkungan build dokumen ini, sehingga endpoint "
        "Midtrans di-emulasi stub lokal yang meniru kontrak API-nya "
        "(<font name='Courier'>POST /v2/invoice</font> &rarr; "
        "<font name='Courier'>qr_code_url</font>, webhook ber-signature). "
        "Branch kode Midtrans yang dieksekusi adalah branch yang sama "
        "dengan produksi; badge MOCK MODE hilang dari checkout.", BODY))

    story.append(shot("16_midtrans_checkout_qris.png"))
    story.append(Paragraph("Screenshot 13. Checkout QRIS pada mode "
                           "Midtrans: tanpa badge MOCK, QR berasal dari "
                           "qr_code_url gateway.", CAP))

    story.append(H3("Permintaan invoice yang dikirim server ke Midtrans"))
    story.append(codeblock(jdump({
        "method": mt["create_request"]["method"],
        "path": mt["create_request"]["path"],
        "headers": {
            "Content-Type": mt["create_request"]["content_type"],
            "Authorization": mt["create_request"]["authorization"]},
        "body": mt["create_request"]["body"]})))
    story.append(Spacer(1, 6))

    story.append(H3("Webhook notifikasi pembayaran (divalidasi)"))
    story.append(codeblock(
        "POST /webhooks/midtrans\n"
        f"x-signature-1: {mt['webhook']['header_x_signature_1']}\n\n"
        + jdump(mt["webhook"]["payload"]) + "\n\n"
        f"-> HTTP {mt['webhook']['response_http']} "
        + jdump(mt["webhook"]["response_json"]) + "\n\n"
        "Signature salah:\n"
        f"-> HTTP {mt['webhook_bad_signature']['response_http']} "
        + jdump(mt["webhook_bad_signature"]["response_json"])))
    story.append(Spacer(1, 6))

    story.append(shot("19_midtrans_pembayaran_sukses.png"))
    story.append(Paragraph("Screenshot 14. Setelah webhook settle "
                           "diverifikasi, gold +50,000 masuk otomatis.",
                           CAP))
    story.append(Paragraph(
        "Status transaksi setelah webhook (dibaca game lewat polling):",
        BODY))
    story.append(codeblock(jdump(mt["status_settled"]["json"])))
    story.append(Spacer(1, 4))
    story.append(shot("20_midtrans_saldo_masuk.png"))
    story.append(Paragraph("Screenshot 15. Hero Shop: saldo HERO GOLD "
                           "50,000 setelah settle Midtrans.", CAP))
    story.append(PageBreak())

    # ── 4. REFERENSI TEKNIS ──
    story.append(H1("4. Referensi Teknis"))
    story.append(H3("Endpoint server top up (server/app.py)"))
    story.append(tbl([
        ["Method & Path", "Fungsi"],
        ["POST /api/topup/create", "Cetak invoice {\"pkg\": "
                                   "\"PAKET 50K\"}"],
        ["GET /api/topup/status/<id>", "Status + kode redeem saat "
                                       "settled"],
        ["GET /api/topup/qr/<id>", "PNG QR (QRIS Midtrans / QR mock)"],
        ["POST /webhooks/midtrans", "Webhook Midtrans (signature "
                                    "divalidasi)"],
        ["POST /api/mock/settle/<id>", "Simulasi settle (mode mock "
                                       "saja)"],
        ["POST /api/redeem", "Tandai kode redeemed (server-side)"],
    ], widths=[60 * mm, 110 * mm]))
    story.append(Spacer(1, 6))
    story.append(H3("Konfigurasi (environment variables)"))
    story.append(tbl([
        ["Variabel", "Default", "Keterangan"],
        ["TOPUP_MIDTRANS_SERVER_KEY", "(kosong = mock)",
         "API key server Midtrans (SB-...)"],
        ["TOPUP_MIDTRANS_API", "https://api.midtrans.com",
         "Ganti https://api.sandbox.midtrans.com utk testing"],
        ["TOPUP_DB_PATH", "server/topup.db", "Lokasi SQLite"],
        ["TOPUP_MOCK_AUTO_SETTLE", "0", "Detik auto-settle (mock)"],
        ["TOPUP_PORT", "8321", "Port HTTP"],
        ["MYSTIC_TOPUP_URL", "(kosong)", "URL server dilihat game "
                                         "(mode simulasi jika kosong)"],
    ], widths=[52 * mm, 42 * mm, 76 * mm]))
    story.append(Spacer(1, 6))
    story.append(H3("Status transaksi"))
    story.append(tbl([
        ["Status", "Arti", "Efek"],
        ["pending", "Invoice tercetak, menunggu pembayaran",
         "Game menampilkan QRIS & poll"],
        ["settled", "Pembayaran terverifikasi (webhook/settle)",
         "Kode redeem di-issue, gold masuk otomatis"],
        ["cancel", "Dibatalkan", "Dialog kembali ke pilih paket"],
        ["expired", "Kedaluwarsa", "Pemain diminta mencoba lagi"],
    ], widths=[30 * mm, 70 * mm, 70 * mm]))
    story.append(PageBreak())

    # ── 5. CATATAN PRODUKSI ──
    story.append(H1("5. Catatan Produksi & Penyesuaian Spesifikasi "
                    "Midtrans"))
    story.append(Paragraph(
        "Butir berikut ditemukan saat menyusun dokumen ini dan "
        "<b>perlu disesuaikan sebelum go-live</b> agar sesuai "
        "spesifikasi resmi Midtrans:", BODY))
    story.append(Spacer(1, 4))
    story.append(tbl([
        ["#", "Temuan pada server/app.py", "Spesifikasi Midtrans / "
                                           "tindakan"],
        ["1", "Header Authorization dikirim apa adanya: "
              "'Basic <server_key>' (baris ~172)",
         "Midtrans meminta Basic base64(server_key + ':'). Perlu "
         "base64-encode sebelum dikirim."],
        ["2", "Webhook memvalidasi HMAC-SHA512 body mentah pada header "
              "x-signature-1 (baris ~250)",
         "Notifikasi resmi membawa signature_key = "
         "SHA512(order_id+status_code+gross_amount+server_key) di badan "
         "JSON. Sesuaikan verifikasi & terima pola ini."],
        ["3", "Status sukses dicek sebagai 'settle'/'capture'",
         "Untuk QRIS/VA/e-wallet Midtrans mengirim "
         "'settlement' (capture utk kartu kredit). Tambahkan "
         "'settlement' ke pemetaan status."],
        ["4", "Webhook wajib HTTPS + daftarkan Notification URL di "
              "dashboard Midtrans",
         "Deploy di VPS + Caddy/Nginx; isi Notification URL "
         "https://<host>/webhooks/midtrans."],
        ["5", "PACKAGES server harus sinkron dengan TOPUP_PACKAGES "
              "game",
         "Jaga keduanya identik (harga & gold) saat menambah paket."],
    ], widths=[8 * mm, 78 * mm, 84 * mm]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Referensi: dokumentasi Midtrans — Handling HTTP Notification "
        "&amp; signature key SHA512(order_id + status_code + "
        "gross_amount + serverkey).<br/>Sumber: "
        "https://docs.midtrans.com/reference/get-transaction-status-1",
        SMALL))
    story.append(PageBreak())

    # ── 6. BUKTI EKSEKUSI ──
    story.append(H1("6. Bukti Eksekusi (log server top up)"))
    story.append(Paragraph(
        "Log di bawah adalah keluaran asli "
        "<font name='Courier'>server/app.py</font> selama screenshot "
        "diambil (docs/workflow_transaksi/_server_log.txt).", BODY))
    story.append(codeblock(LOG.strip(), size=7.0))
    story.append(Spacer(1, 8))
    story.append(H3("Regenerasi dokumen"))
    story.append(codeblock(
        "pip install pygame-ce flask qrcode pillow reportlab\n"
        "python tools/_shot_workflow_topup.py   # screenshot + artefak\n"
        "python tools/build_workflow_pdf.py     # -> docs/"
        "WORKFLOW_TRANSAKSI_MIDTRANS.pdf"))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Screenshot tersimpan di docs/workflow_transaksi/*.png; payload "
        "nyata (invoice, webhook, status) di _artifacts.json.", SMALL))

    doc = SimpleDocTemplate(
        PDF_OUT, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title="Workflow Transaksi Top Up — Mystic Arena",
        author="Mystic Arena (otomatis)")
    doc.build(story)
    print("PDF ditulis:", os.path.relpath(PDF_OUT, ROOT))


if __name__ == "__main__":
    build()
