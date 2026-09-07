#!/usr/bin/env python3
"""Transpile rantai smart-AI boss Pygame -> GDScript (BossKit.gd).

    python tools/gen_boss_smart_ai.py           # tulis godot/scenes/boss/BossKit.gd
    python tools/gen_boss_smart_ai.py --check   # exit 1 kalau file ter-commit basi

Sumber kebenaran adalah bosses/base_boss.py (versi Pygame). File ini TIDAK
menyalin rumus manual: ia mem-parse AST Python dari rantai smart-AI
(`elif self.boss_type == ...` di Boss.update beserta semua helper yang
direferensikannya) dan memancarkan GDScript 4.3 setara, 1:1, per baris
sumber. Perilaku hasil transpile dijaga oleh oracle Pygame lewat
tools/test_godot_match_parity.py (bagian boss_smart_ai) dan
godot/tests/BossSmartAIParityTest.tscn — bukan oleh kepercayaan pada
transpiler ini saja.

Mengapa transpile, bukan tulis tangan: 79 boss × Q/W/E/R = ±7.400 baris
Python yang sangat teratur. Menyalinnya manual hampir pasti melahirkan
salah ketik koefisien; regenerasi otomatis juga menjaga Godot ikut berubah
kalau kit boss Pygame berubah (filosofi yang sama dengan
tools/convert_to_godot.py).

Aturan transpile yang penting (frame pygame -> detik Godot):
  * self.x/self.y        -> b.global_position.x/.y
  * self.speed (px/f)    -> b.move_speed (px/s): tulis *60, baca /60
  * self.direction       -> b.facing
  * timer kit q/w/e/r    -> b.kit["..."] — tetap SATUAN FRAME, ditick oleh
                            kode kit sendiri (persis pygame)
  * e.take_damage(d, t)  -> b.kit_skill_hit(e, d)  (netral sekolah)
  * e.apply_slow(a, f)   -> b.kit_apply_slow(e, a, f) (frame -> detik)
  * e.attack_timer (f)   -> b.kit_atk_timer/kit_lock_attack (frame <-> detik)
  * math.hypot(a, b)     -> Vector2(a, b).length()
  * min/max/int/float/abs-> minf/maxf/int/float/absf
  * `a // b`             -> int(a / b)   (semua situs positif int//int)
  * `a / b`              -> float(a) / float(b) (Python `/` selalu float)
  * blok try/except FX   -> dibuang (murni visual, diganti jembatan FX Godot)
"""
import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "bosses" / "base_boss.py"
OUT = ROOT / "godot" / "scenes" / "boss" / "BossKit.gd"

# ── anggota Boss.gd (subclass) yang dipakai kode kit — akses dinamik via b ──
SHARED_BOSS_ATTRS = {
    "hp", "max_hp", "damage", "team", "target", "is_enraged", "boss_type",
    # base_damage: diset Boss.__init__/apply_scaling pygame (bukan milik kit)
    # — buff damage boss membaca nilai dasar ini.
    "base_damage",
    # defense_boost: dipakai take_damage pygame (DR 45% Drakar W) dan sudah
    # ada sebagai var Boss.gd — kit harus menulis anggota yang sama.
    "defense_boost", "defense_timer",
}

# Sumbu/properti yang butuh pemetaan nama, BUKAN dideklarasikan ulang.
SPECIAL_SELF_WRITES = {
    "x": lambda v: f"b.global_position.x = {v}",
    "y": lambda v: f"b.global_position.y = {v}",
    "speed": lambda v: f"b.move_speed = ({v}) * 60.0",
    "direction": lambda v: f"b.facing = {v}",
}

# Atribut unit musuh (e/tgt/closest/self.target/...) -> pemetaan Godot.
ENEMY_ATTR_MAP = {"x", "y", "hp", "max_hp", "alive", "attack_timer",
                  "take_damage", "apply_slow", "speed"}

# Nama lokal yang tidak boleh dipakai sebagai deklarasi var (kata kunci dsb.)
GD_RESERVED = {
    "if", "elif", "else", "for", "while", "return", "break", "continue",
    "pass", "and", "or", "not", "in", "is", "as", "class", "func", "var",
    "const", "true", "false", "null", "self", "super", "signal", "enum",
    "match", "when", "static", "void", "int", "float", "bool", "String",
    "breakpoint", "tool", "await", "yield", "assert", "preload",
}


class TranspileError(Exception):
    pass


def err(node, method, msg):
    line = getattr(node, "lineno", "?")
    raise TranspileError(f"{method}:L{line}: {msg}")


# ══════════════════════════════════════════════════════════
#  EKSTRAKSI METODE DARI base_boss.py
# ══════════════════════════════════════════════════════════

def load_closure():
    """Semua method smart-AI + helper yang mereka panggil (transitif).

    `_get_boss_stats` dan `_shake_screen` TIDAK ikut ditranspile: keduanya
    menembus state global (skill_down/enrage/shake) dan di-port sebagai
    jembatan Boss.gd (b.kit_get_stats / b._shake) supaya tetap satu sumber.
    """
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "Boss")
    methods = {n.name: n for n in cls.body if isinstance(n, ast.FunctionDef)}
    roots = sorted(n for n in methods if n.startswith("_smart_ai_"))
    todo = list(roots)
    seen = set()
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        if name not in methods:
            raise TranspileError(f"method hilang: {name}")
        for node in ast.walk(methods[name]):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                    and node.func.attr in methods):
                if node.func.attr not in seen:
                    todo.append(node.func.attr)
    # _get_boss_stats/_shake_screen: jembatan state global di Boss.gd.
    # _l9_stats: lookup data mentah (bukan blok FX) -> bridge manual.
    excluded = {"_get_boss_stats", "_shake_screen", "_l9_stats"}
    ordered = [n for n in methods
               if n in seen and n not in excluded and not n.startswith("_smart_ai_")]
    # urut sesuai kemunculan di sumber supaya diff mudah dibaca
    ordered.sort(key=lambda n: methods[n].lineno)
    smart_sorted = sorted(roots, key=lambda n: methods[n].lineno)
    return methods, smart_sorted, ordered


def extract_dispatch_chain(methods):
    """Urutan elif `self.boss_type == "..."` dari Boss.update ASLI.

    Diparse langsung dari update() supaya urutan prioritas dispatch Godot
    tidak pernah beda dengan pygame (else -> ability generik sudah ditangani
    Boss.gd _after_attack untuk boss tanpa smart-AI).
    """
    upd = methods["update"]
    chain = []
    node = None
    for n in ast.walk(upd):
        if (isinstance(n, ast.If)
                and isinstance(n.test, ast.Compare)
                and isinstance(n.test.left, ast.Attribute)
                and n.test.left.attr == "boss_type"):
            node = n
            break
    if node is None:
        raise TranspileError("rantai elif boss_type tidak ditemukan di update()")
    while node is not None:
        test = node.test
        if (isinstance(test, ast.Compare) and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and isinstance(test.left, ast.Attribute)
                and test.left.attr == "boss_type"
                and isinstance(test.comparators[0], ast.Constant)):
            chain.append(test.comparators[0].value)
        else:
            break  # cabang else (ability generik) — bukan bagian dispatch kit
        node = node.orelse[0] if (
            len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)
        ) else None
    return chain


# ══════════════════════════════════════════════════════════
#  EMITTER
# ══════════════════════════════════════════════════════════

def _is_self_name(node):
    return isinstance(node, ast.Name) and node.id == "self"


def is_self_attr(node, name=None):
    return (isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and (name is None or node.attr == name))


def base_name(node):
    """Nama paling dalam dari ekspresi atribut (a.b.c -> a)."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def try_hoist_gencalls(expr, out, indent, method, ctx):
    """`sum(1 for e in X if C)` / `any(...)` -> loop + variabel sementara.

    Dipanggil sebelum emit statement yang memuat ekspresi tersebut
    (If-test atau Assign). `tmps` adalah list tempat nama sementara
    didaftarkan (dibagikan per statement).
    """
    found = []

    def walk(n):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in ("sum", "any")
                and len(n.args) == 1 and isinstance(n.args[0], ast.GeneratorExp)):
            found.append(n)
        for child in ast.iter_child_nodes(n):
            walk(child)

    walk(expr)
    if not found:
        return None
    for call in found:
        gen = call.args[0]
        comp = gen.generators[0]
        if len(gen.generators) != 1 or comp.ifs and len(comp.ifs) > 1:
            err(call, method, "generator ekspresi tidak didukung")
        if call.func.id == "sum":
            # pygame hanya memakai sum(1 for X in ITER if COND)
            if not (isinstance(gen.elt, ast.Constant) and gen.elt.value == 1):
                err(call, method, "sum() non-1 tidak didukung")
        tmp = f"__g{len(ctx.setdefault('gtmp', []))}"
        ctx["gtmp"].append(tmp)
        it = emit_expr(comp.iter, method)
        out.append(indent + f"var {tmp} := 0")
        out.append(indent + f"for {emit_expr(comp.target, method)} in {it}:")
        if comp.ifs:
            out.append(indent + "\tif " + emit_expr(comp.ifs[0], method) + ":")
            out.append(indent + "\t\t" + _gen_body(call, tmp, method))
        else:
            out.append(indent + "\t" + _gen_body(call, tmp, method))
        gen._gd_tmp = tmp  # penanda untuk emitter ekspresi
    # ekspresi aslinya tetap dipancarkan; emitter Call membaca _gd_tmp
    return None


def _gen_body(call, tmp, method):
    if isinstance(call.func, ast.Name) and call.func.id == "sum":
        return f"{tmp} += 1"
    # any(COND for X in ITER) -> early-true
    return f"if {emit_expr(call.args[0].elt, method)}: {tmp} = 1"


def emit_expr(node, method):
    """Ekspresi Python -> ekspresi GDScript (string)."""
    if isinstance(node, ast.Constant):
        v = node.value
        if v is True:
            return "true"
        if v is False:
            return "false"
        if v is None:
            return "null"
        if isinstance(v, (int, float)):
            return repr(v)
        if isinstance(v, str):
            return '"' + v + '"'
        err(node, method, f"konstanta tak didukung: {v!r}")

    if isinstance(node, ast.Name):
        if node.id == "self":
            return "b"
        if node.id in GD_RESERVED:
            err(node, method, f"nama lokal menabrak kata kunci GDScript: {node.id}")
        return node.id

    if isinstance(node, ast.Attribute):
        # self.attr LANGSUNG (bukan self.target.attr) -> pemetaan boss
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            if node.attr in ("x", "y"):
                return f"b.global_position.{node.attr}"
            if node.attr in SHARED_BOSS_ATTRS:
                return f"b.{node.attr}"
            if node.attr in SPECIAL_SELF_WRITES:
                err(node, method, f"baca self.{node.attr} tidak ada di kode kit")
            return f'b.kit["{node.attr}"]'
        if (isinstance(node.value, ast.Name)
                and node.value.id in ("math", "stats", "__main__")):
            # math.hypot/stats.get dibantu di Call; attr telanjang = bug urutan
            err(node, method, f"atribut {ast.unparse(node)} di luar pola")
        # ekspresi unit lain (e, tgt, closest, self.target, enemy)
        recv = emit_expr(node.value, method)
        if node.attr == "x":
            return f"{recv}.global_position.x"
        if node.attr == "y":
            return f"{recv}.global_position.y"
        if node.attr == "alive":
            return f"b.kit_unit_alive({recv})"
        if node.attr == "attack_timer":
            return f"b.kit_atk_timer({recv})"
        return f"{recv}.{node.attr}"

    if isinstance(node, ast.Call):
        return emit_call(node, method)

    if isinstance(node, ast.BinOp):
        a = emit_expr(node.left, method)
        c = emit_expr(node.right, method)
        if isinstance(node.op, ast.Add):
            return f"({a}) + ({c})"
        if isinstance(node.op, ast.Sub):
            return f"({a}) - ({c})"
        if isinstance(node.op, ast.Mult):
            return f"({a}) * ({c})"
        if isinstance(node.op, ast.Div):
            # Python `/` selalu float; GDScript int/int memotong.
            return f"float({a}) / float({c})"
        if isinstance(node.op, ast.FloorDiv):
            # semua situs di kode kit positif int//int
            return f"int(({a}) / ({c}))"
        if isinstance(node.op, ast.Mod):
            return f"(({a}) % ({c}))"
        err(node, method, f"operator biner tak didukung: {type(node.op).__name__}")

    if isinstance(node, ast.UnaryOp):
        v = emit_expr(node.operand, method)
        if isinstance(node.op, ast.Not):
            return f"not ({v})"
        if isinstance(node.op, ast.USub):
            return f"-({v})"
        if isinstance(node.op, ast.UAdd):
            return f"({v})"
        err(node, method, "operator uner tak didukung")

    if isinstance(node, ast.BoolOp):
        op = " and " if isinstance(node.op, ast.And) else " or "
        return op.join(f"({emit_expr(v, method)})" for v in node.values)

    if isinstance(node, ast.Compare):
        m = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
             ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!=",
             ast.In: "in"}
        if type(node.ops[0]) not in m:
            err(node, method, f"operator compare tak didukung: {type(node.ops[0]).__name__}")
        # compare berantai (0 < x < 400) -> and berpasangan (evaluasi kiri
        # ke kanan, short-circuit, persis semantik Python untuk ekspresi
        # tanpa efek samping)
        parts = []
        lhs = node.left
        for op, rhs in zip(node.ops, node.comparators):
            if type(op) not in m:
                err(node, method, f"operator compare tak didukung: {type(op).__name__}")
            parts.append(f"({emit_expr(lhs, method)}) {m[type(op)]} "
                         f"({emit_expr(rhs, method)})")
            lhs = rhs
        return " and ".join(parts)

    if isinstance(node, ast.IfExp):
        return (f"{emit_expr(node.body, method)} "
                f"if {emit_expr(node.test, method)} "
                f"else {emit_expr(node.orelse, method)}")

    if isinstance(node, (ast.List, ast.Tuple)):
        return "[" + ", ".join(emit_expr(e, method) for e in node.elts) + "]"

    if getattr(node, "_gd_tmp", None):
        return node._gd_tmp

    err(node, method, f"ekspresi tak didukung: {type(node).__name__}")


def emit_call(node, method):
    fn = node.func
    # getattr / setattr / hasattr
    if isinstance(fn, ast.Name):
        if fn.id == "getattr":
            return emit_getattr(node, method)
        if fn.id == "setattr":
            if (len(node.args) == 3 and is_self_attr(node.args[0]) is False
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id == "self"
                    and isinstance(node.args[1], ast.Name)):
                val = emit_expr(node.args[2], method)
                return f'b.kit[{emit_expr(node.args[1], method)}] = {val}'
            err(node, method, "setattr di luar pola timer kit")
        if fn.id == "hasattr":
            return emit_hasattr(node, method)
        if fn.id in ("sum", "any") and len(node.args) == 1 \
                and isinstance(node.args[0], ast.GeneratorExp):
            tmp = getattr(node.args[0], "_gd_tmp", None)
            if tmp:
                return tmp
            err(node, method, "sum/any belum di-hoist (bug emitter)")
        if fn.id == "min":
            return ("minf(" + ", ".join(emit_expr(a, method) for a in node.args) + ")")
        if fn.id == "max":
            return ("maxf(" + ", ".join(emit_expr(a, method) for a in node.args) + ")")
        if fn.id == "int":
            return f"int({emit_expr(node.args[0], method)})"
        if fn.id == "float":
            return f"float({emit_expr(node.args[0], method)})"
        if fn.id == "abs":
            return f"absf({emit_expr(node.args[0], method)})"
        err(node, method, f"panggilan global tak didukung: {fn.id}({ast.unparse(node)[:60]})")

    if not isinstance(fn, ast.Attribute):
        err(node, method, "panggilan bentuk lain tak didukung")

    # math.hypot(a, b) -> Vector2(a, b).length()
    if isinstance(fn.value, ast.Name) and fn.value.id == "math" \
            and fn.attr == "hypot":
        a = emit_expr(node.args[0], method)
        c = emit_expr(node.args[1], method)
        return f"Vector2({a}, {c}).length()"

    # stats.get(k, d)
    if isinstance(fn.value, ast.Name) and fn.value.id == "stats" \
            and fn.attr == "get":
        return ("stats.get(" + ", ".join(emit_expr(a, method) for a in node.args) + ")")

    # self.<helper kit>()
    if isinstance(fn.value, ast.Name) and fn.value.id == "self":
        args = [emit_expr(a, method) for a in node.args]
        if fn.attr == "_shake_screen":
            return f"b._shake({args[0]}.0)" if not args[0].endswith(".0") \
                else f"b._shake({args[0]})"
        if fn.attr == "_get_boss_stats":
            return "b.kit_get_stats()"
        args_full = ", ".join(["b"] + args)
        return f"{fn.attr}({args_full})"

    # e.take_damage(d, self.team) -> b.kit_skill_hit(e, d)
    if fn.attr == "take_damage":
        recv = emit_expr(fn.value, method)
        if len(node.args) != 2 or node.keywords:
            err(node, method, "take_damage kit harus 2 argumen tanpa kwargs")
        return f"b.kit_skill_hit({recv}, {emit_expr(node.args[0], method)})"

    # e.apply_slow(a, durasi_frame) -> b.kit_apply_slow(e, a, frame)
    if fn.attr == "apply_slow":
        recv = emit_expr(fn.value, method)
        return (f"b.kit_apply_slow({recv}, {emit_expr(node.args[0], method)}, "
                f"{emit_expr(node.args[1], method)})")

    err(node, method, f"panggilan metode tak didukung: {ast.unparse(node)[:70]}")


def emit_getattr(node, method):
    args = node.args
    if len(args) >= 2 and isinstance(args[0], ast.Name) and args[0].id == "self":
        if isinstance(args[1], ast.Name):
            # getattr(self, attr) dinamis (loop tick timer)
            return f"b.kit[{emit_expr(args[1], method)}]"
        if isinstance(args[1], ast.Constant):
            name = args[1].value
            if name in ("x", "y"):
                return f"b.global_position.{name}"
            if name in SHARED_BOSS_ATTRS:
                return f"b.{name}"
            return f'b.kit["{name}"]'
    if (len(args) == 3 and isinstance(args[1], ast.Constant)
            and args[1].value == "attack_timer"):
        return f"b.kit_atk_timer({emit_expr(args[0], method)})"
    if (len(args) == 3 and isinstance(args[1], ast.Constant)
            and args[1].value == "alive"):
        return f"b.kit_unit_alive({emit_expr(args[0], method)})"
    err(node, method, f"getattr di luar pola: {ast.unparse(node)[:70]}")


def emit_hasattr(node, method):
    args = node.args
    if (len(args) == 2 and isinstance(args[0], ast.Name) and args[0].id == "self"
            and isinstance(args[1], ast.Constant)):
        if args[1].value == "q_timer":
            return 'b.kit["kit_ready"]'  # init-once; lihat emit_stmt(If)
        return f'b.kit["{args[1].value}"] != null'
    if len(args) == 2 and isinstance(args[1], ast.Constant):
        recv = emit_expr(args[0], method)
        k = args[1].value
        if k == "attack_timer":
            return f'"attack_timer" in {recv}'
        if k == "apply_slow":
            return f"b.kit_has_slow({recv})"
        if k == "speed":
            return f"b.kit_can_move({recv})"
        return f'"{k}" in {recv}'
    err(node, method, f"hasattr di luar pola: {ast.unparse(node)[:70]}")


# ── pernyataan ────────────────────────────────────────────

def collect_locals(fn):
    """Nama lokal yang di-assign (bukan target for, bukan parameter)."""
    params = {a.arg for a in fn.args.args} - {"self"}
    names = set()
    fors = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        if isinstance(node, (ast.For, ast.comprehension)):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    fors.add(n.id)
    return sorted(n for n in names if n not in params and n not in fors)


def is_fx_try(stmt):
    """Try/except yang isinya murni FX (import __main__/heroes.*_fx).

    Semua try di rantai smart-AI pygame adalah blok FX visual yang dijaga
    `except Exception: pass`. Apa pun di luar pola itu = logika gameplay dan
    harus GAGAL saat generate, bukan dibuang diam-diam.
    """
    for sub in ast.walk(stmt):
        if isinstance(sub, (ast.Import, ast.ImportFrom)):
            mod = sub.module if isinstance(sub, ast.ImportFrom) else ""
            names = ", ".join(a.name for a in sub.names)
            if not (mod in ("heroes", "__main__") or "fx" in mod
                    or "fx" in names or "__main__" in names):
                return False
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
            txt = ast.unparse(sub.func)
            if not ("fx" in txt or "effects" in txt
                    or "game_instance" in txt or "__main__" in txt):
                return False
        if isinstance(sub, ast.Raise):
            return False
    return True


def emit_stmt(stmt, out, indent, method, ctx):
    pad = "\t" * indent

    if isinstance(stmt, ast.Expr):
        if isinstance(stmt.value, ast.Constant):  # docstring
            return
        out.append(pad + emit_expr(stmt.value, method))
        return

    if isinstance(stmt, ast.Assign):
        target = stmt.targets[0]
        if len(stmt.targets) != 1:
            err(stmt, method, "multi-assign tak didukung")
        try_hoist_gencalls(stmt.value, out, pad, method, ctx)
        value = emit_expr(stmt.value, method)
        if isinstance(target, (ast.Tuple, ast.List)):
            for t, v in zip(target.elts,
                            stmt.value.elts if isinstance(stmt.value, (ast.Tuple, ast.List))
                            else [None] * len(target.elts)):
                if v is None:
                    err(stmt, method, "tuple-assign non-tuple RHS tak didukung")
                emit_assign_one(t, emit_expr(v, method), out, pad, method, stmt, ctx)
            return
        emit_assign_one(target, value, out, pad, method, stmt, ctx)
        return

    if isinstance(stmt, ast.AugAssign):
        try_hoist_gencalls(stmt.value, out, pad, method, ctx)
        value = emit_expr(stmt.value, method)
        op = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
              ast.FloorDiv: "/", ast.Mod: "%"}.get(type(stmt.op))
        if op is None:
            err(stmt, method, "aug-assign operator tak didukung")
        t = stmt.target
        if is_self_attr(t):
            if t.attr in ("x", "y"):
                out.append(pad + f"b.global_position.{t.attr} {op}= {value}")
                return
            if t.attr == "speed":  # px/frame -> px/s
                out.append(pad + f"b.move_speed {op}= ({value}) * 60.0")
                return
            if t.attr == "direction":
                err(stmt, method, "aug-assign self.direction tak didukung")
            if t.attr in SHARED_BOSS_ATTRS:
                out.append(pad + f"b.{t.attr} {op}= {value}")
            else:
                out.append(pad + f'b.kit["{t.attr}"] {op}= {value}')
            return
        if isinstance(stmt.op, ast.Div):
            # Python `/=` selalu true division (float)
            base = emit_expr(t, method)
            out.append(pad + f"{base} = float({base}) / float({value})")
            return
        if isinstance(t, ast.Attribute):
            recv = emit_expr(t.value, method)
            if t.attr == "x":
                out.append(pad + f"{recv}.global_position.x {op}= {value}")
            elif t.attr == "y":
                out.append(pad + f"{recv}.global_position.y {op}= {value}")
            elif t.attr in ("hp", "max_hp"):
                out.append(pad + f"{recv}.{t.attr} {op}= {value}")
            else:
                err(stmt, method, f"aug-assign atribut musuh tak didukung: {t.attr}")
            return
        if isinstance(t, ast.Name):
            out.append(pad + f"{t.id} {op}= {value}")
            return
        err(stmt, method, "aug-assign target tak didukung")

    if isinstance(stmt, ast.If):
        # init-once: if not hasattr(self, 'q_timer'): ... -> kit_ready
        init_once = hasattr_is_qtimer_test(stmt)
        if init_once:
            out.append(pad + 'if not b.kit["kit_ready"]:')
            for s in stmt.body:
                emit_stmt(s, out, indent + 1, method, ctx)
            out.append("\t" * (indent + 1) + 'b.kit["kit_ready"] = true')
            if stmt.orelse:
                err(stmt, method, "init-once dengan else tak didukung")
            return
        try_hoist_gencalls(stmt.test, out, pad, method, ctx)
        out.append(pad + "if " + emit_expr(stmt.test, method) + ":")
        emit_block(stmt.body, out, indent + 1, method, ctx, stmt)
        orelse = stmt.orelse
        while orelse and len(orelse) == 1 and isinstance(orelse[0], ast.If):
            elifn = orelse[0]
            try_hoist_gencalls(elifn.test, out, pad, method, ctx)
            out.append(pad + "elif " + emit_expr(elifn.test, method) + ":")
            emit_block(elifn.body, out, indent + 1, method, ctx, elifn)
            orelse = elifn.orelse
        if orelse:
            out.append(pad + "else:")
            emit_block(orelse, out, indent + 1, method, ctx, stmt)
        return

    if isinstance(stmt, ast.For):
        it = emit_expr(stmt.iter, method)
        target = emit_expr(stmt.target, method)
        out.append(pad + f"for {target} in {it}:")
        emit_block(stmt.body, out, indent + 1, method, ctx, stmt)
        if stmt.orelse:
            err(stmt, method, "for-else tak didukung")
        return

    if isinstance(stmt, ast.Return):
        if stmt.value is None:
            out.append(pad + "return")
        else:
            try_hoist_gencalls(stmt.value, out, pad, method, ctx)
            out.append(pad + "return " + emit_expr(stmt.value, method))
        return

    if isinstance(stmt, ast.Continue):
        out.append(pad + "continue")
        return

    if isinstance(stmt, ast.Pass):
        out.append(pad + "pass")
        return

    if isinstance(stmt, ast.Try):
        if not is_fx_try(stmt):
            err(stmt, method, "try/except berisi logika non-FX — jangan dibuang")
        # Blok FX pygame diterjemahkan, bukan dibuang: panggilan
        # notify_skill_cast/impact + add_damage_number tetap berada di
        # posisi sumbernya supaya timing FX (dan radius impact) sama.
        for sub in stmt.body:
            emit_fx_stmt(sub, out, indent, method)
        return

    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        return  # import di level method hanya milik blok FX (sudah diverifikasi)

    err(stmt, method, f"pernyataan tak didukung: {type(stmt).__name__}")


def emit_hasattr_is_qtimer(call):
    return (len(call.args) == 2
            and isinstance(call.args[0], ast.Name) and call.args[0].id == "self"
            and isinstance(call.args[1], ast.Constant)
            and call.args[1].value == "q_timer")


def emit_assign_one(target, value, out, pad, method, stmt, ctx=None):
    if ctx is None:
        raise TranspileError("emit_assign_one tanpa ctx")
    if is_self_attr(target):
        if target.attr in SPECIAL_SELF_WRITES:
            out.append(pad + SPECIAL_SELF_WRITES[target.attr](value))
        elif target.attr in SHARED_BOSS_ATTRS:
            out.append(pad + f"b.{target.attr} = {value}")
        else:
            out.append(pad + f'b.kit["{target.attr}"] = {value}')
        return
    if isinstance(target, ast.Attribute):
        recv = emit_expr(target.value, method)
        if target.attr == "x":
            out.append(pad + f"{recv}.global_position.x = {value}")
        elif target.attr == "y":
            out.append(pad + f"{recv}.global_position.y = {value}")
        elif target.attr == "attack_timer":
            # pola satu-satunya: e.attack_timer = max(<read>, F)
            if (isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id == "max"):
                out.append(pad + f"b.kit_lock_attack({recv}, {value})")
            else:
                err(stmt, method, "tulis attack_timer non-max tak didukung")
        elif target.attr in ("hp", "max_hp"):
            out.append(pad + f"{recv}.{target.attr} = {value}")
        else:
            err(stmt, method, f"tulis atribut musuh tak didukung: {target.attr}")
        return
    if isinstance(target, ast.Name):
        # semua lokal sudah di-hoist `var x = null` di atas fungsi
        out.append(pad + f"{target.id} = {value}")
        return
    err(stmt, method, "target assign tak didukung")



def emit_fx_stmt(stmt, out, indent, method):
    """Satu pernyataan di dalam blok FX pygame -> jembatan FX Godot.

    Bentuk yang dikenali (hasil inventarisasi seluruh rantai smart-AI):
      _<alias>fx.notify_skill_cast(self, 'q')
      _<alias>fx.notify_skill_impact(self, X, Y, R, 'w')
      game.effects.add_damage_number(X, Y, f"+{n}", is_critical=..., ...)
      game.effects.shake_screen(N)
      if/else annidasi (ghost ship memilih titik impact)
    """
    pad = "\t" * indent
    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        return
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        call = stmt.value
        f = call.func
        if not (isinstance(f, ast.Attribute)):
            err(stmt, method, f"panggilan FX tak dikenali: {ast.unparse(stmt)[:70]}")
        if f.attr == "notify_skill_cast" and len(call.args) == 2 \
                and _is_self_name(call.args[0]):
            out.append(pad + f"b.kit_fx_cast({emit_expr(call.args[1], method)})")
            return
        if f.attr == "notify_skill_impact" and _is_self_name(call.args[0]):
            # dua bentuk: (self, x, y, r, skill) atau (self, x, y, radius=, skill=)
            x = emit_expr(call.args[1], method)
            y = emit_expr(call.args[2], method)
            r = "0.0"
            k = '"q"'
            if len(call.args) >= 4:
                r = emit_expr(call.args[3], method)
            if len(call.args) >= 5:
                k = emit_expr(call.args[4], method)
            for kw in call.keywords:
                if kw.arg == "radius":
                    r = emit_expr(kw.value, method)
                elif kw.arg == "skill":
                    k = emit_expr(kw.value, method)
            out.append(pad + f"b.kit_fx_impact({x}, {y}, {r}, {k})")
            return
        if f.attr == "add_damage_number" and len(call.args) == 3:
            text = emit_fx_text(call.args[2], method)
            crit = "false"
            for kw in call.keywords:
                if kw.arg == "is_critical":
                    crit = emit_expr(kw.value, method)
            out.append(pad + f"b._callout({text}, {crit})")
            return
        if f.attr == "shake_screen" and len(call.args) == 1:
            v = emit_expr(call.args[0], method)
            if not v.endswith(".0"):
                v += ".0"
            out.append(pad + f"b._shake({v})")
            return
        err(stmt, method, f"panggilan FX tak dikenali: {ast.unparse(stmt)[:70]}")
    # `game = __main__.game_instance` — penyalur di blok FX, tak perlu di Godot
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
            and isinstance(stmt.targets[0], ast.Name) \
            and isinstance(stmt.value, ast.Attribute):
        return
    if isinstance(stmt, ast.If):
        # guard `hasattr(__main__, 'game_instance')` selalu benar di Godot
        # (host match selalu ada) -> badan if ditulis tanpa guard.
        if _is_main_guard(stmt.test):
            for sub in stmt.body:
                emit_fx_stmt(sub, out, indent, method)
            return
        out.append(pad + "if " + emit_expr(stmt.test, method) + ":")
        for sub in stmt.body:
            emit_fx_stmt(sub, out, indent + 1, method)
        if stmt.orelse:
            out.append(pad + "else:")
            for sub in stmt.orelse:
                emit_fx_stmt(sub, out, indent + 1, method)
        return
    err(stmt, method, f"pernyataan FX tak dikenali: {type(stmt).__name__}")


def _is_main_guard(test):
    return (isinstance(test, ast.Call)
            and isinstance(test.func, ast.Name)
            and test.func.id == "hasattr"
            and len(test.args) == 2
            and isinstance(test.args[0], ast.Name)
            and test.args[0].id == "__main__")


def emit_fx_text(node, method):
    """Argumen teks add_damage_number: konstanta atau f-string."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return '"' + node.value + '"'
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append('"' + v.value + '"')
            elif isinstance(v, ast.FormattedValue):
                if v.format_spec is not None:
                    err(node, method, "format-spec f-string FX tak didukung")
                parts.append(f"str({emit_expr(v.value, method)})")
            else:
                err(node, method, "bagian f-string FX tak dikenali")
        return " + ".join(parts) if parts else '""'
    err(node, method, f"teks FX tak dikenali: {ast.unparse(node)[:50]}")


def emit_block(body, out, indent, method, ctx, owner=None):
    if not body:
        out.append("\t" * indent + "pass")
        return
    for s in body:
        emit_stmt(s, out, indent, method, ctx)


def transpile_method(fn):
    ctx = {"declared": set()}
    out = []
    params = [a.arg for a in fn.args.args if a.arg != "self"]
    header = f"static func {fn.name}({', '.join(['b'] + params)}):"
    out.append(f"## bosses/base_boss.py:{fn.lineno}-{fn.end_lineno}")
    out.append(header)
    # deklarasi lokal di atas fungsi (GDScript block-scoped, Python tidak)
    for name in collect_locals(fn):
        out.append("\tvar " + name + " = null")
    if collect_locals(fn):
        out.append("")
    for stmt in fn.body:
        emit_stmt(stmt, out, 1, fn.name, ctx)
    return "\n".join(out)


# ══════════════════════════════════════════════════════════
#  KIT STATE (variabel b.kit)
# ══════════════════════════════════════════════════════════

def collect_kit_state(methods, order):
    """Semua self.<attr> yang ditulis kode kit (kecuali pemetaan khusus),
    lengkap dengan default yang akurat: literal dari blok init-once
    `if not hasattr(self, 'q_timer'):` pygame, heuristik jenis nilai untuk
    sisanya (bool -> false, list -> [], objek/None -> null, angka -> 0)."""
    written = {}
    samples = {}  # attr -> contoh nilai Python yang pernah ditulis
    all_names = order + [n for n in methods if n.startswith("_smart_ai_")]
    for name in all_names:
        fn = methods[name]
        for node in ast.walk(fn):
            if (isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and is_self_attr(node.targets[0])):
                a = node.targets[0].attr
                if a in SPECIAL_SELF_WRITES or a in SHARED_BOSS_ATTRS:
                    continue
                written.setdefault(a, 0)
                written[a] += 1
                if isinstance(node.value, ast.Constant):
                    samples.setdefault(a, node.value.value)
                elif isinstance(node.value, (ast.List, ast.Tuple)):
                    samples.setdefault(a, "__list__")
                elif isinstance(node.value, ast.Name) and node.value.id == "self":
                    samples.setdefault(a, "__self__")
                elif isinstance(node.value, ast.Constant) and node.value.value is None:
                    samples.setdefault(a, None)
    # blok init-once menentukan default (python: hasattr gate pertama kali)
    for name in [n for n in methods if n.startswith("_smart_ai_")]:
        for node in ast.walk(methods[name]):
            if isinstance(node, ast.If) and hasattr_is_qtimer_test(node):
                for sub in node.body:
                    if (isinstance(sub, ast.Assign)
                            and len(sub.targets) == 1
                            and is_self_attr(sub.targets[0])
                            and isinstance(sub.value, ast.Constant)):
                        samples.setdefault(sub.targets[0].attr, sub.value.value)
                break
    lines = []
    for a in sorted(written):
        v = samples.get(a, 0)
        if v == "__list__":
            d = "[]"
        elif v == "__self__":
            d = "null"
        elif v is None:
            d = "null"
        elif v is True:
            d = "false"  # default pra-buff (init pygame: False)
        elif v is False:
            d = "false"
        elif isinstance(v, (int, float)):
            d = repr(v)
        elif isinstance(v, str):
            d = "null"
        else:
            d = "0"
        lines.append(f'\t"{a}": {d},')
    lines.append('\t"kit_ready": false,')
    return lines


def hasattr_is_qtimer_test(node):
    """Deteksi `if not hasattr(self, 'q_timer'):` pada If node."""
    return (isinstance(node.test, ast.UnaryOp)
            and isinstance(node.test.op, ast.Not)
            and isinstance(node.test.operand, ast.Call)
            and isinstance(node.test.operand.func, ast.Name)
            and node.test.operand.func.id == "hasattr"
            and len(node.test.operand.args) == 2
            and isinstance(node.test.operand.args[0], ast.Name)
            and node.test.operand.args[0].id == "self"
            and isinstance(node.test.operand.args[1], ast.Constant)
            and node.test.operand.args[1].value == "q_timer")


# ══════════════════════════════════════════════════════════
#  FILE HEADER + JEMBATAN
# ══════════════════════════════════════════════════════════

HEADER = '''\
# BossKit.gd — DIHASILKAN OTOMATIS. JANGAN EDIT TANGAN.
#
# Sumber: rantai smart-AI boss di bosses/base_boss.py (metode _smart_ai_*
# beserta helper Q/W/E/R yang mereka panggil), ditranspile 1:1 oleh
# tools/gen_boss_smart_ai.py. Regenerasi:
#
#     python tools/gen_boss_smart_ai.py
#
# Semua fungsi di sini STATIC dan menerima `b` = node Boss (Boss.gd).
# State kit hidup di `b.kit` (Dictionary) supaya tidak perlu deklarasi
# ulang di Boss.gd dan tetap satu instans per boss. Timer Q/W/E/R tetap
# SATUAN FRAME seperti pygame (di-tick oleh kode kit sendiri).
#
# Jembatan yang disediakan Boss.gd (semua netral sekolah / frame->detik):
#   b.kit_get_stats()          — _get_boss_stats (skill_down/dmg_scaling/enrage)
#   b.kit_stats_full()         — boss_data mentah (dipakai _l9_stats)
#   b.kit_skill_hit(e, dmg)    — e.take_damage(dmg, self.team)
#   b.kit_apply_slow(e, a, f)  — e.apply_slow(a, f)  (f frame)
#   b.kit_lock_attack(e, f)    — e.attack_timer = max(e.attack_timer, f)
#   b.kit_atk_timer(e)         — baca attack_timer musuh dalam frame
#   b.kit_unit_alive(e)        — e.alive
#   b.kit_has_slow(e)          — hasattr(e, 'apply_slow')
#   b.kit_can_move(e)          — hasattr(e, 'speed')
#   b.kit_fx_cast/kit_fx_impact— pengganti blok FX heroes/*_fx pygame
#
# Blok `try: from heroes import <boss>_fx ...` pygame sengaja dibuang
# generator: itu lapisan visual. Godot memakai kit_fx_cast/kit_fx_impact
# (panggilan cast/impact tetap dipertahankan pada posisi yang sama).
# Paritas yang dijamin file ini adalah PERILAKU (koefisien, target, timing,
# frame) — diverifikasi BossSmartAIParityTest terhadap oracle Pygame.
extends RefCounted


## Dictionary state default untuk b.kit — salin di Boss.gd._ready().
const DEFAULT_KIT := {
__KIT_STATE__
}


## Dispatch rantai `elif self.boss_type == ...` — URUTAN PERSIS
## Boss.update pygame (tools/gen_boss_smart_ai.py meng-ekstrak urutannya).
static func dispatch(b, boss_type: String, enemies: Array, target_dist: float) -> void:
__DISPATCH__
	return


## Stat mentah boss_data (pemetaan _l9_stats pygame: TANPA pengali
## enrage/skill_down — beda dengan kit_get_stats).
static func stats_full_raw(boss_type: String) -> Dictionary:
	return b.kit_stats_full()


# ══════════════════════════════════════════════════════════
#  SMART AI PER BOSS — transpile 1:1 dari bosses/base_boss.py
# ══════════════════════════════════════════════════════════
'''


def generate():
    methods, smart_sorted, helper_order = load_closure()
    chain = extract_dispatch_chain(methods)

    # dispatch dalam urutan update() pygame
    disp = []
    for bt in chain:
        disp.append(f'\tif boss_type == "{bt}":')
        disp.append(f'\t\t_smart_ai_{bt}(b, enemies, target_dist)')
        disp.append('\t\treturn')
    disp.append('\t# boss tanpa smart-AI: ability generik ditangani Boss.gd')

    kit_state = collect_kit_state(methods, helper_order)

    parts = [(
        "## bosses/base_boss.py:6450-6455 — stat mentah boss_data TANPA\n"
        "## pengali enrage/skill_down (beda dengan kit_get_stats).\n"
        "static func _l9_stats(b):\n"
        "\treturn b.kit_stats_full()"
    )]
    for name in smart_sorted + helper_order:
        parts.append(transpile_method(methods[name]))
        parts.append("")
        parts.append("")

    header = (HEADER
              .replace("__KIT_STATE__", "\n".join(kit_state))
              .replace("__DISPATCH__", "\n".join(disp)))
    body = "\n".join(parts)
    text = header + body
    # jitak Python `; ` di akhir pernyataan (stylistic di base_boss)
    text = re.sub(r";\s*\n", "\n", text)
    # `recv.global_position.x += v` pada receiver Variant (b/e) hanya
    # mengubah SALINAN Vector2 lalu dibuang — harus lewat penugasan
    # properti penuh. Tulis ulang ke bentuk aman:
    #   .x += v  ->  global_position += Vector2(v, 0.0)
    #   .y += v  ->  global_position += Vector2(0.0, v)
    #   .x = v   ->  global_position = Vector2(v, global_position.y)
    #   .y = v   ->  global_position = Vector2(global_position.x, v)
    text = re.sub(r"(?m)^(\s*)(\w+)\.global_position\.x \+= (.*)$",
                  r"\1\2.global_position += Vector2(\3, 0.0)", text)
    text = re.sub(r"(?m)^(\s*)(\w+)\.global_position\.y \+= (.*)$",
                  r"\1\2.global_position += Vector2(0.0, \3)", text)
    text = re.sub(r"(?m)^(\s*)(\w+)\.global_position\.x = (.*)$",
                  r"\1\2.global_position = Vector2(\3, \2.global_position.y)", text)
    text = re.sub(r"(?m)^(\s*)(\w+)\.global_position\.y = (.*)$",
                  r"\1\2.global_position = Vector2(\2.global_position.x, \3)", text)
    return text, len(smart_sorted), len(helper_order)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="gagal kalau BossKit.gd ter-commit berbeda")
    args = ap.parse_args()
    try:
        text, n_smart, n_helper = generate()
    except TranspileError as e:
        print(f"[gen_boss_smart_ai] GAGAL: {e}", file=sys.stderr)
        sys.exit(2)
    text = text.rstrip("\n") + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("[gen_boss_smart_ai] STALE: BossKit.gd beda dengan "
                  "base_boss.py — jalankan tools/gen_boss_smart_ai.py",
                  file=sys.stderr)
            sys.exit(1)
        print(f"[gen_boss_smart_ai] PASS: BossKit.gd segar "
              f"({n_smart} smart-AI + {n_helper} helper)")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"[gen_boss_smart_ai] menulis {OUT.relative_to(ROOT)} "
          f"({n_smart} smart-AI, {n_helper} helper, "
          f"{text.count(chr(10))} baris)")


if __name__ == "__main__":
    main()
