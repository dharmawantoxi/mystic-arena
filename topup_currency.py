# ================================
# topup_currency.py
# Multi-currency untuk tampilan Top Up Hero Gold.
#
# Harga paket disimpan dalam IDR (base currency). Ke pemain
# ditampilkan dalam mata uang lokal berdasarkan deteksi region
# perangkat:
#   - Android : pyjnius (Locale sistem, pola sama seperti
#               bridge di mobile/cloud_save.py)
#   - PC      : modul `locale` Python (var lingkungan LANG/LC_*)
# Jika region tidak terdeteksi, fallback ke USD.
#
# Tabel kurs STATIS (pendekatan) dan hanya untuk TAMPILAN.
# Saat disambungkan ke gateway pembayaran nyata (Midtrans/Xendit/
# Stripe), lewati currency yang terdeteksi saat membuat invoice —
# gateway yang memakai kurs riil saat checkout.
# ================================

# 1 unit currency = X rupiah (pendekatan, bisa di-update kapan saja
# cukup di tabel ini).
IDR_PER_UNIT = {
    "IDR": 1.0,
    "USD": 16200,
    "EUR": 17800,
    "GBP": 20900,
    "SGD": 12200,
    "MYR": 3950,
    "THB": 480,
    "VND": 0.62,
    "PHP": 270,
    "JPY": 108,
    "KRW": 11.5,
    "CNY": 2240,
    "AUD": 10400,
    "CAD": 11900,
    "BRL": 3050,
    "INR": 190,
    "MXN": 830,
    "ZAR": 900,
    "AED": 4400,
    "SAR": 4300,
}

# Simbol display (prefix).
CURRENCY_SYMBOLS = {
    "IDR": "Rp ",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "SGD": "S$",
    "MYR": "RM ",
    "THB": "฿",
    "VND": "₫",
    "PHP": "₱",
    "JPY": "¥",
    "KRW": "₩",
    "CNY": "C$",
    "AUD": "A$",
    "CAD": "C$",
    "BRL": "R$",
    "INR": "₹",
    "MXN": "MX$",
    "ZAR": "R ",
    "AED": "AED ",
    "SAR": "SAR ",
}

# Currency tanpa digit desimal.
NO_DECIMAL = ("IDR", "JPY", "KRW", "VND")

# Region (ISO 3166-1 alpha-2) -> currency. Hanya currency yang ada di
# tabel kurs; region lain fallback ke DEFAULT_CURRENCY.
REGION_CURRENCY = {
    "ID": "IDR",
    "US": "USD",
    "CA": "CAD",
    "GB": "GBP",
    "DE": "EUR", "FR": "EUR", "NL": "EUR", "BE": "EUR", "IE": "EUR",
    "ES": "EUR", "IT": "EUR", "PT": "EUR", "AT": "EUR", "FI": "EUR",
    "SG": "SGD",
    "MY": "MYR",
    "TH": "THB",
    "VN": "VND",
    "PH": "PHP",
    "JP": "JPY",
    "KR": "KRW",
    "CN": "CNY",
    "AU": "AUD",
    "BR": "BRL",
    "IN": "INR",
    "MX": "MXN",
    "ZA": "ZAR",
    "AE": "AED",
    "SA": "SAR",
}

# Bahasa -> currency, dipakai HANYA kalau region tidak diketahui.
# Sekalinya yang dominan satu region (en/es/pt/fr ambigu, jadi
# disengaja tidak ada di sini).
LANG_CURRENCY = {
    "ja": "JPY",
    "ko": "KRW",
    "zh": "CNY",
    "th": "THB",
    "vi": "VND",
    "id": "IDR",
    "ms": "MYR",
    "hi": "INR",
}

# Fallback global saat region tidak bisa dideteksi.
DEFAULT_CURRENCY = "USD"


def _parse_locale_name(lang_code):
    """'id_ID.UTF-8' / 'en-US' / 'ind_ID.1252' -> ('id', 'ID').
    Kode 'C*' (locale netral) dianggap tidak terdeteksi."""
    if not lang_code or lang_code.startswith("C"):
        return None, None
    first = lang_code.split(".")[0].replace("-", "_")
    parts = first.split("_")
    language = parts[0].lower() or None
    region = None
    if len(parts) > 1 and len(parts[1]) == 2 and parts[1].isalpha():
        region = parts[1].upper()
    return language, region


def _device_locale():
    """Return (language, region) dari perangkat. Aman: tidak pernah
    raise; (None, None) kalau tidak bisa dideteksi.

    - Android : Locale sistem via pyjnius (PythonActivity), pola sama
                seperti bridge di mobile/cloud_save.py.
    - PC      : (1) modul locale Python setelah setlocale(LC_ALL, ""),
                (2) fallback: var lingkungan LC_ALL/LC_CTYPE/LANG.
    Catatan POSIX: C-locale proses masih "C" sampai setlocale dipanggil,
    jadi LANG tidak terbaca kalau langkah (1) dilewati.
    """
    # ── Android (harus dicoba dulu; di PC import jnius gagal) ──
    try:
        from jnius import autoclass
        act = autoclass("org.kivy.android.PythonActivity").mActivity
        loc = act.getResources().getConfiguration().locale
        lang = loc.getLanguage()
        region = loc.getCountry()
        return (lang.lower() if lang else None,
                region.upper() if region else None)
    except Exception:
        pass

    # ── PC: locale sistem ──
    lang_code = ""
    try:
        import locale
        try:
            locale.setlocale(locale.LC_ALL, "")  # baca locale sistem
        except locale.Error:
            pass
        lang_code = locale.setlocale(locale.LC_CTYPE) or ""
    except Exception:
        pass
    if lang_code and not lang_code.startswith("C"):
        return _parse_locale_name(lang_code)

    # ── PC: fallback env (mis. locale tak terinstall di sistem) ──
    try:
        import os
        for var in ("LC_ALL", "LC_CTYPE", "LANG"):
            lang_code = (os.environ.get(var) or "").strip()
            if lang_code and not lang_code.startswith("C"):
                return _parse_locale_name(lang_code)
    except Exception:
        pass

    return None, None


def detect_currency():
    """Deteksi currency pemain dari region perangkat. Aman: tidak
    pernah raise; selalu return kode currency yang didukung."""
    try:
        lang, region = _device_locale()
    except Exception:
        lang, region = None, None

    if region:
        cur = REGION_CURRENCY.get(region.upper())
        if cur:
            return cur
    if lang:
        cur = LANG_CURRENCY.get(lang.lower())
        if cur:
            return cur
    return DEFAULT_CURRENCY


def convert_idr(amount_idr, currency):
    """Konversi jumlah IDR ke currency. Currency tidak dikenal
    fallback ke DEFAULT_CURRENCY. Return (nilai, currency_final)."""
    rate = IDR_PER_UNIT.get(currency)
    if not rate:
        currency = DEFAULT_CURRENCY
        rate = IDR_PER_UNIT[DEFAULT_CURRENCY]
    return amount_idr / rate, currency


def format_price(amount_idr, currency):
    """Format harga ke currency pemain:
    10000 IDR -> 'Rp 10.000' (ID), '$0.62' (US), '¥93' (JP),
    'S$0.82' (SG), '₩870' (KR).
    IDR memakai pemisah titik (gaya Indonesia) agar konsisten
    dengan fmt_idr() lama."""
    val, cur = convert_idr(amount_idr, currency)
    if cur in NO_DECIMAL:
        num = f"{int(round(val)):,}"
        if cur == "IDR":
            num = num.replace(",", ".")
    else:
        num = f"{val:,.2f}"
    return CURRENCY_SYMBOLS.get(cur, cur + " ") + num
