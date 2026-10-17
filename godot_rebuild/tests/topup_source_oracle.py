"""Source oracle for the top-up / voucher port (layer 9au).

The source flow lives in three places:

* `topup_currency.py`  - locale -> currency detection, IDR conversion and
  price formatting (pure stdlib, executed as-is).
* `topup_voucher.py`   - `MA-NNNNNN` code format + `voucher_codes.txt`
  allowlist parsing (pure stdlib, executed as-is; the allowlist is read from
  a temporary SAVE_DIR so the repo state does not leak into the fixture).
* `_core.py` Menu      - the dialog state machine. Its top-up methods are
  harvested with `ast` (the module itself needs pygame) and executed on a
  stub menu with recording `SoundManager` / `SaveManager` shims, a frozen
  `time` module and a scripted `urllib.request`, so the simulation purchase,
  the redeem keypad, the grant bookkeeping and the server state machine
  (create -> QR -> poll -> settle / expire / unreachable) all come from the
  REAL source lines.
* `server/app.py`      - the Flask top-up server is imported under a tiny
  Flask shim with an in-memory SQLite DB in MOCK mode, so the JSON contract
  the Godot client speaks (create / status / qr / redeem) is pinned too.

Run: python godot_rebuild/tests/topup_source_oracle.py
"""
import ast
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "topup_source.json"
FROZEN_MS = 1_760_000_000_123  # 2025-10-09T08:53:20.123Z
MENU_METHODS = (
    "_topup_send_create", "_topup_send_poll", "_topup_server_tick",
    "_topup_pay_fail", "_redeem_append", "_redeem_backspace",
    "_redeem_submit", "_redeem_grant", "topup_complete", "_topup_http",
)
MENU_CONSTANTS = ("TOPUP_PACKAGES", "TOPUP_PAYMENT_METHODS",
                  "TOPUP_PROCESSING_SECONDS", "fmt_idr")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _load_module(name, path, extra=None):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__dict__.update(extra or {})
    sys.modules[name] = module
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, module.__dict__)
    return module


# ── topup_currency.py ──────────────────────────────────────────────────────
def currency_fixture(cur):
    amounts = [1, 999, 10_000, 12_345, 49_999, 50_000, 120_000, 1_234_567]
    codes = list(cur.IDR_PER_UNIT) + ["XXX", ""]
    prices = {}
    converts = {}
    for code in codes:
        prices[code] = [cur.format_price(a, code) for a in amounts]
        val, final = cur.convert_idr(10_000, code)
        converts[code] = {"value": repr(val), "currency": final}
    locale_cases = ["id_ID.UTF-8", "en-US", "ind_ID.1252", "C", "C.UTF-8",
                    "POSIX", "", "ja_JP", "zh_Hans_CN", "pt_BR", "EN_gb",
                    "fr", "es_419", "de_DE@euro"]
    parsed = {name: list(cur._parse_locale_name(name)) for name in locale_cases}
    detect_cases = [("id", "ID"), ("en", "US"), ("en", "GB"), ("ja", None),
                    ("ko", "KR"), ("zh", "TW"), ("th", None), ("vi", "VN"),
                    ("ms", "MY"), ("hi", "IN"), ("fr", "FR"), ("en", None),
                    ("xx", "ZZ"), (None, None), ("ID", "id"), ("en", "sg")]
    detects = []
    for lang, region in detect_cases:
        cur._device_locale = lambda lang=lang, region=region: (lang, region)
        detects.append({"lang": lang, "region": region,
                        "currency": cur.detect_currency()})
    return {
        "idr_per_unit": {k: repr(float(v)) for k, v in cur.IDR_PER_UNIT.items()},
        "symbols": dict(cur.CURRENCY_SYMBOLS),
        "no_decimal": list(cur.NO_DECIMAL),
        "region_currency": dict(cur.REGION_CURRENCY),
        "lang_currency": dict(cur.LANG_CURRENCY),
        "default_currency": cur.DEFAULT_CURRENCY,
        "amounts": amounts,
        "prices": prices,
        "convert_10000": converts,
        "parse_locale": parsed,
        "detect": detects,
    }


# ── topup_voucher.py ───────────────────────────────────────────────────────
VOUCHER_TEXT = """# allowlist contoh
MA-123456=75000
ma-000042
MA-999999 = abc
MA-7777=  15000

  MA-555555  
MA-2468=0
"""


def voucher_fixture(voucher, save_dir):
    formats = ["MA-123456", "ma-123456", " MA-1234 ", "MA-12345678",
               "MA-123", "MA-123456789", "MA123456", "MA-12A456", "",
               None, "XX-123456", "MA-", "MA-000000"]
    out = {
        "code_prefix": voucher.CODE_PREFIX,
        "max_digits": voucher.MAX_DIGITS,
        "code_re": voucher.CODE_RE.pattern,
        "voucher_file": voucher.VOUCHER_FILE,
        "formats": [{"code": c, "valid": voucher.is_valid_format(c)}
                    for c in formats],
        "allowlist_text": VOUCHER_TEXT,
    }
    out["missing_allowlist"] = voucher.load_vouchers()
    path = Path(save_dir) / voucher.VOUCHER_FILE
    path.write_text(VOUCHER_TEXT, encoding="utf-8")
    out["parsed_allowlist"] = voucher.load_vouchers()
    path.write_text("# only comments\n\n", encoding="utf-8")
    out["empty_allowlist"] = voucher.load_vouchers()
    path.unlink()
    return out


# ── _core.py Menu top-up methods ───────────────────────────────────────────
def harvest_menu(source_text):
    tree = ast.parse(source_text)
    pieces = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.FunctionDef)):
            names = [node.name] if isinstance(node, ast.FunctionDef) else [
                t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(n in MENU_CONSTANTS for n in names):
                pieces.append(ast.get_source_segment(source_text, node))
        if isinstance(node, ast.ClassDef) and node.name == "Menu":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name in MENU_METHODS:
                    seg = ast.get_source_segment(source_text, item)
                    pieces.append("def " + seg.split("def ", 1)[1]
                                  if seg.startswith("def ") else seg)
    return pieces


class SoundRecorder:
    plays = []

    def play(self, name, volume_mult=1.0, **_):
        SoundRecorder.plays.append([name, volume_mult])


class SaveRecorder:
    saves = 0

    @staticmethod
    def save(_data):
        SaveRecorder.saves += 1


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeUrllib:
    """Scripted urllib.request: `script` is a list of (ok, status, body)."""
    script = []
    requests = []

    class Request:
        def __init__(self, url, data=None, method=None):
            self.url, self.data, self.method, self.headers = url, data, method, {}

        def add_header(self, k, v):
            self.headers[k] = v

    @staticmethod
    def urlopen(req, timeout=None):
        FakeUrllib.requests.append({
            "method": req.method, "url": req.url,
            "body": req.data.decode() if req.data else None,
            "json": req.headers.get("Content-Type") == "application/json",
            "timeout": timeout})
        ok, status, body = FakeUrllib.script.pop(0)
        if not ok:
            raise OSError(body.decode() if isinstance(body, bytes) else body)
        return FakeResponse(status, body)


def build_menu_class(pieces, sound, save):
    ns = {"SoundManager": lambda: sound, "SaveManager": save,
          "DEV_TOPUP_ENABLED": False, "globals": globals}
    body = "\n".join(p for p in pieces if not p.startswith("def _topup")
                     and not p.startswith("def _redeem")
                     and not p.startswith("def topup_complete"))
    methods = [p for p in pieces if p.startswith("def ")
               and not p.startswith("def fmt_idr")]
    exec(body, ns)
    cls_src = "class Menu:\n" + "\n".join(
        "\n".join("    " + line for line in m.splitlines()) for m in methods)
    exec(cls_src, ns)
    return ns


def new_menu(ns, server_url="", currency="IDR", meta_gold=1000, save_data=None):
    menu = ns["Menu"]()
    menu.meta_gold = meta_gold
    menu.save_data = save_data if save_data is not None else {}
    menu.animation_time = 0
    menu.topup_open = True
    menu.topup_phase = "select"
    menu.topup_pkg_idx = 0
    menu.topup_method_idx = 0
    menu.topup_progress = 0.0
    menu.topup_tx_id = None
    menu.topup_last_total = 0
    menu.topup_currency = currency
    menu.topup_redeem_input = ""
    menu.topup_redeem_msg = None
    menu.topup_redeem_code = None
    menu.topup_last_method = None
    menu.topup_server_url = server_url
    menu.topup_pay_state = "idle"
    menu.topup_pay_msg = None
    menu.topup_invoice = None
    menu._topup_http_thread = None
    menu._topup_http_result = None
    menu._topup_http_purpose = None
    menu._topup_poll_next = 0
    menu._topup_qr_bytes = None
    menu._topup_qr_surf = None
    return menu


def snapshot(menu):
    return {
        "phase": menu.topup_phase,
        "pay_state": menu.topup_pay_state,
        "pay_msg": menu.topup_pay_msg,
        "invoice": menu.topup_invoice,
        "poll_next": menu._topup_poll_next,
        "purpose": menu._topup_http_purpose,
        "qr_len": len(menu._topup_qr_bytes) if menu._topup_qr_bytes else 0,
        "meta_gold": menu.meta_gold,
        "tx_id": menu.topup_tx_id,
        "last_total": menu.topup_last_total,
        "redeem_input": menu.topup_redeem_input,
        "redeem_msg": list(menu.topup_redeem_msg[0:1]) + [
            list(menu.topup_redeem_msg[1])] if menu.topup_redeem_msg else None,
        "redeem_code": menu.topup_redeem_code,
        "last_method": menu.topup_last_method,
        "save_data": json.loads(json.dumps(menu.save_data)),
        "sounds": list(SoundRecorder.plays),
        "saves": SaveRecorder.saves,
    }


def _reset():
    SoundRecorder.plays = []
    SaveRecorder.saves = 0
    FakeUrllib.requests = []
    FakeUrllib.script = []


def _tick_until_idle(menu, max_ticks=50):
    """Run `_topup_server_tick` until the worker thread is consumed."""
    for _ in range(max_ticks):
        th = menu._topup_http_thread
        if th is not None:
            th.join(timeout=2)
        menu._topup_server_tick()
        if menu._topup_http_thread is None:
            return
    raise RuntimeError("http thread never settled")


def menu_fixture(ns, voucher, save_dir):
    out = {
        "packages": list(ns["TOPUP_PACKAGES"]),
        "payment_methods": list(ns["TOPUP_PAYMENT_METHODS"]),
        "processing_seconds": ns["TOPUP_PROCESSING_SECONDS"],
        "progress_step": repr(1.0 / max(1, int(60 * ns["TOPUP_PROCESSING_SECONDS"]))),
        "fmt_idr": {str(a): ns["fmt_idr"](a) for a in (0, 999, 10_000, 120_000, 1_234_567)},
        "frozen_ms": FROZEN_MS,
    }
    progress, frames = 0.0, 0
    while progress < 1.0:  # the Menu.update() accumulation, 60 fps assumed
        progress += 1.0 / max(1, int(60 * ns["TOPUP_PROCESSING_SECONDS"]))
        frames += 1
    out["simulation_frames"] = frames
    # simulation purchases (one per currency / method) ────────────────────
    sims = []
    for cur, method_idx, gold in (("IDR", 0, 1000), ("USD", 1, 0),
                                  ("JPY", 4, 25), ("XXX", 2, 7)):
        _reset()
        menu = new_menu(ns, currency=cur, meta_gold=gold)
        menu.topup_method_idx = method_idx
        menu.topup_phase = "processing"
        menu.topup_complete()
        sims.append({"currency": cur, "method_idx": method_idx,
                     "gold_before": gold, "after": snapshot(menu)})
    out["simulation"] = sims
    # history cap: 52 purchases keep the last 50 ─────────────────────────
    _reset()
    menu = new_menu(ns)
    for _ in range(52):
        menu.topup_complete()
    out["history_cap"] = {"len": len(menu.save_data["topup_history"]),
                          "meta_gold": menu.meta_gold}
    # redeem keypad ───────────────────────────────────────────────────────
    _reset()
    menu = new_menu(ns)
    menu.topup_phase = "redeem"
    keys = []
    for op in ["1", "2", "del", "del", "del", "3", "4", "5", "6", "7", "8",
               "9", "0", "del", "1"]:
        if op == "del":
            menu._redeem_backspace()
        else:
            menu._redeem_append(op)
        keys.append({"op": op, "input": menu.topup_redeem_input})
    out["keypad"] = keys
    out["keypad_sounds"] = list(SoundRecorder.plays)
    _reset()
    menu = new_menu(ns)
    menu.topup_phase = "select"
    menu._redeem_append("5")
    menu._redeem_backspace()
    out["keypad_wrong_phase"] = menu.topup_redeem_input
    # redeem submit outcomes ───────────────────────────────────────────────
    path = Path(save_dir) / voucher.VOUCHER_FILE
    submits = []

    def submit(label, text, allowlist, save_data, gold=500):
        _reset()
        if allowlist is None:
            if path.exists():
                path.unlink()
        else:
            path.write_text(allowlist, encoding="utf-8")
        menu = new_menu(ns, meta_gold=gold, save_data=save_data)
        menu.topup_phase = "redeem"
        menu.topup_redeem_input = text
        menu._redeem_submit()
        submits.append({"label": label, "input": text,
                        "allowlist": allowlist, "after": snapshot(menu)})

    submit("invalid_format", "MA-12", None, {})
    submit("invalid_empty", "", None, {})
    submit("already_redeemed", "MA-123456", None,
           {"redeemed_codes": ["MA-123456"]})
    submit("unknown_with_allowlist", "MA-888888", VOUCHER_TEXT, {})
    submit("allowlist_text_amount", "MA-123456", VOUCHER_TEXT, {})
    submit("allowlist_amount", "MA-123456", "MA-123456=75000\n", {})
    submit("allowlist_no_amount", "MA-000042", "MA-000042\n", {})
    submit("allowlist_zero_amount", "MA-2468", "MA-2468=0\n", {})
    submit("demo_mode", "ma-654321", None, {"topup_history": [{"tx": "x"}]})
    submit("lowercase_allowlist", "MA-000042", "ma-000042=12\n", {})
    if path.exists():
        path.unlink()
    out["submits"] = submits
    # redeemed_codes cap ──────────────────────────────────────────────────
    _reset()
    menu = new_menu(ns)
    for i in range(53):
        menu.topup_phase = "redeem"
        menu._redeem_grant("MA-%06d" % i, 10)
    out["redeem_cap"] = {"codes": menu.save_data["redeemed_codes"],
                         "history_len": len(menu.save_data["topup_history"]),
                         "meta_gold": menu.meta_gold}
    out["grant_duplicate"] = menu._redeem_grant("MA-000052", 10)
    # server flow ─────────────────────────────────────────────────────────
    out["server"] = server_flows(ns)
    return out


def server_flows(ns):
    flows = {}
    url = "http://127.0.0.1:8321/"
    png = PNG_MAGIC + b"fakepngbody"
    create_body = json.dumps({"id": "mock-abc", "pkg": "PAKET 50K",
                              "amount": 10000, "gold": 50000,
                              "status": "pending",
                              "qr_url": "/api/topup/qr/mock-abc",
                              "mock": True}).encode()

    def start(script, anim=100):
        _reset()
        FakeUrllib.script = list(script)
        menu = new_menu(ns, server_url=url, meta_gold=10)
        menu.animation_time = anim
        menu.topup_phase = "paying"
        menu.topup_pay_state = "creating"
        menu._topup_send_create()
        return menu

    # create ok -> awaiting + QR fetched -> pending poll -> settled
    menu = start([
        (True, 200, create_body),
        (True, 200, png),
        (True, 200, json.dumps({"id": "mock-abc", "status": "pending",
                                "gold": 50000, "amount": 10000}).encode()),
        (True, 200, json.dumps({"id": "mock-abc", "status": "settled",
                                "gold": 50000, "amount": 10000,
                                "code": "MA-424242"}).encode()),
    ])
    steps = []
    _tick_until_idle(menu)  # create consumed, qr request in flight
    steps.append(["after_create", snapshot(menu)])
    _tick_until_idle(menu)  # qr consumed
    steps.append(["after_qr", snapshot(menu)])
    menu.animation_time = 159
    menu._topup_server_tick()  # before poll_next: nothing
    steps.append(["before_poll_due", snapshot(menu),
                  len(FakeUrllib.requests)])
    menu.animation_time = 160
    menu._topup_server_tick()  # poll sent
    _tick_until_idle(menu)
    steps.append(["after_pending_poll", snapshot(menu)])
    menu.animation_time = menu._topup_poll_next
    menu._topup_server_tick()
    _tick_until_idle(menu)
    steps.append(["after_settled_poll", snapshot(menu)])
    flows["happy"] = {"steps": steps, "requests": list(FakeUrllib.requests)}

    # create unreachable
    menu = start([(False, None, b"connection refused")])
    _tick_until_idle(menu)
    flows["create_unreachable"] = {"after": snapshot(menu),
                                   "requests": list(FakeUrllib.requests)}
    # create http 400 (unknown package) -> same failure path
    menu = start([(True, 400, json.dumps({"error": "unknown_package"}).encode())])
    _tick_until_idle(menu)
    flows["create_rejected"] = snapshot(menu)
    # create ok, QR not a PNG, poll expired
    menu = start([
        (True, 200, create_body),
        (True, 404, b"not found"),
        (True, 200, json.dumps({"id": "mock-abc", "status": "expired",
                                "gold": 50000, "amount": 10000}).encode()),
    ])
    _tick_until_idle(menu)
    _tick_until_idle(menu)
    menu.animation_time = menu._topup_poll_next
    menu._topup_server_tick()
    _tick_until_idle(menu)
    flows["expired"] = snapshot(menu)
    # poll cancel
    menu = start([
        (True, 200, create_body), (True, 200, png),
        (True, 200, json.dumps({"id": "mock-abc", "status": "cancel"}).encode()),
    ])
    _tick_until_idle(menu)
    _tick_until_idle(menu)
    menu.animation_time = menu._topup_poll_next
    menu._topup_server_tick()
    _tick_until_idle(menu)
    flows["cancel"] = snapshot(menu)
    # poll network error -> treated as "still pending" (+120 frames)
    menu = start([
        (True, 200, create_body), (True, 200, png),
        (False, None, b"timed out"),
    ])
    _tick_until_idle(menu)
    _tick_until_idle(menu)
    menu.animation_time = menu._topup_poll_next
    menu._topup_server_tick()
    _tick_until_idle(menu)
    flows["poll_error"] = snapshot(menu)
    # settled without gold field -> package gold; settled code already used
    menu = start([
        (True, 200, create_body), (True, 200, png),
        (True, 200, json.dumps({"id": "mock-abc", "status": "settled",
                                "code": "MA-111111"}).encode()),
    ])
    _tick_until_idle(menu)
    _tick_until_idle(menu)
    menu.animation_time = menu._topup_poll_next
    menu._topup_server_tick()
    _tick_until_idle(menu)
    flows["settled_default_gold"] = snapshot(menu)
    menu = start([
        (True, 200, create_body), (True, 200, png),
        (True, 200, json.dumps({"id": "mock-abc", "status": "settled",
                                "gold": 50000, "code": "MA-111111"}).encode()),
    ])
    menu.save_data["redeemed_codes"] = ["MA-111111"]
    _tick_until_idle(menu)
    _tick_until_idle(menu)
    menu.animation_time = menu._topup_poll_next
    menu._topup_server_tick()
    _tick_until_idle(menu)
    flows["settled_duplicate_code"] = snapshot(menu)
    # manual "I have paid" while a request is in flight is ignored by the
    # click handler (thread is not None) - pinned as a constant here.
    flows["poll_delay_first"] = 60
    flows["poll_delay_repeat"] = 120
    flows["http_timeout"] = 6
    return flows


# ── server/app.py contract (Flask shim, MOCK mode, in-memory DB) ───────────
class _Req:
    json_body = None
    raw = b""
    headers = {}

    def get_json(self, silent=False):
        return self.json_body

    def get_data(self):
        return self.raw


def _flask_shim():
    flask = types.ModuleType("flask")
    routes = {}

    class Flask:
        def __init__(self, _name):
            pass

        def _reg(self, method, rule):
            def deco(fn):
                routes[(method, rule)] = fn
                return fn
            return deco

        def get(self, rule):
            return self._reg("GET", rule)

        def post(self, rule):
            return self._reg("POST", rule)

        def run(self, **_):
            pass

    class Response:
        def __init__(self, body=b"", mimetype=None, status=200):
            self.body, self.mimetype, self.status = body, mimetype, status

    def jsonify(*args, **kwargs):
        if args:
            return dict(args[0])
        return dict(kwargs)

    flask.Flask, flask.Response, flask.jsonify = Flask, Response, jsonify
    flask.request = _Req()
    return flask, routes


def _norm(resp):
    if isinstance(resp, tuple):
        body, status = resp
    else:
        body, status = resp, 200
    if hasattr(body, "mimetype"):
        return {"status": status, "mimetype": body.mimetype,
                "png": body.body[:8] == PNG_MAGIC}
    return {"status": status, "body": body}


def server_fixture(tmp_dir):
    flask, routes = _flask_shim()
    qrcode = types.ModuleType("qrcode")

    class _Img:
        def save(self, buf, format="PNG"):
            buf.write(PNG_MAGIC + b"\x00" * 16)

    qrcode.make = lambda text: _Img()
    sys.modules["flask"], sys.modules["qrcode"] = flask, qrcode
    os.environ["TOPUP_DB_PATH"] = os.path.join(tmp_dir, "topup.db")
    os.environ.pop("TOPUP_MIDTRANS_SERVER_KEY", None)
    app = _load_module("topup_server_app", ROOT / "server" / "app.py")
    app.init_db()
    req = flask.request
    out = {"routes": sorted("%s %s" % k for k in routes),
           "packages": {k: list(v) for k, v in app.PACKAGES.items()},
           "mock_mode": app.MOCK_MODE, "default_port": app.PORT}
    out["healthz"] = _norm(app.healthz())
    req.json_body = {"pkg": "PAKET 99K"}
    out["create_unknown"] = _norm(app.create_topup())
    req.json_body = None
    out["create_no_body"] = _norm(app.create_topup())
    req.json_body = {"pkg": "PAKET 50K"}
    created = _norm(app.create_topup())
    inv = created["body"]["id"]
    created["body"]["id"] = "<id>"
    created["body"]["qr_url"] = created["body"]["qr_url"].replace(inv, "<id>")
    out["create_ok"] = created
    out["create_id_re"] = r"^mock-[0-9a-f]{16}$"
    out["create_id_ok"] = bool(re.match(out["create_id_re"], inv))
    pending = _norm(app.topup_status(inv))
    pending["body"]["id"] = "<id>"
    out["status_pending"] = pending
    out["status_missing"] = _norm(app.topup_status("nope"))
    out["qr_ok"] = _norm(app.topup_qr(inv))
    out["qr_missing"] = _norm(app.topup_qr("nope"))
    settle = _norm(app.mock_settle(inv))
    code = settle["body"]["code"]
    settle["body"]["code"] = "<code>"
    out["settle_ok"] = settle
    out["code_re"] = r"^MA-\d{6}$"
    out["code_ok"] = bool(re.match(out["code_re"], code))
    settle_again = _norm(app.mock_settle(inv))
    out["settle_idempotent"] = settle_again["body"]["code"] == code
    out["settle_missing"] = _norm(app.mock_settle("nope"))
    settled = _norm(app.topup_status(inv))
    settled["body"]["id"] = "<id>"
    settled["body"]["code"] = "<code>" if settled["body"].get("code") == code else "?"
    out["status_settled"] = settled
    req.json_body = {"code": "bad"}
    out["redeem_bad_format"] = _norm(app.api_redeem())
    req.json_body = {"code": "MA-000000"}
    out["redeem_unknown"] = _norm(app.api_redeem())
    req.json_body = {"code": code.lower()}
    out["redeem_ok"] = _norm(app.api_redeem())
    out["redeem_again"] = _norm(app.api_redeem())
    out["webhook_mock"] = _norm(app.webhook_midtrans())
    return out


def source_fixture():
    with contextlib.redirect_stdout(io.StringIO()):
        return _source_fixture()


def _source_fixture():
    tmp_dir = tempfile.mkdtemp(prefix="mystic_topup_oracle_")
    saved_modules = dict(sys.modules)
    try:
        storage = types.ModuleType("storage_paths")
        storage.SAVE_DIR = tmp_dir
        sys.modules["storage_paths"] = storage
        frozen = types.ModuleType("time")
        frozen.time = lambda: FROZEN_MS / 1000.0
        frozen.sleep = lambda *_: None
        cur = _load_module("topup_currency", ROOT / "topup_currency.py")
        voucher = _load_module("topup_voucher", ROOT / "topup_voucher.py")
        fixture = {
            "currency": currency_fixture(cur),
            "voucher": voucher_fixture(voucher, tmp_dir),
        }
        import time as real_time
        real_time_time = real_time.time
        real_time.time = frozen.time
        try:
            pieces = harvest_menu((ROOT / "_core.py").read_text(encoding="utf-8"))
            fake_urllib = types.ModuleType("urllib.request")
            fake_urllib.Request, fake_urllib.urlopen = FakeUrllib.Request, FakeUrllib.urlopen
            import urllib
            saved_request = getattr(urllib, "request", None)
            sys.modules["urllib.request"] = fake_urllib
            urllib.request = fake_urllib
            try:
                ns = build_menu_class(pieces, SoundRecorder(), SaveRecorder)
                fixture["menu"] = menu_fixture(ns, voucher, tmp_dir)
            finally:
                if saved_request is not None:
                    urllib.request = saved_request
        finally:
            real_time.time = real_time_time
        fixture["server"] = server_fixture(tmp_dir)
    finally:
        sys.modules.clear()
        sys.modules.update(saved_modules)
    return fixture


def main():
    fixture = source_fixture()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print("wrote", FIXTURE)


if __name__ == "__main__":
    main()
