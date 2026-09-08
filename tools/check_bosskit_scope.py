#!/usr/bin/env python3
"""Scope checker GDScript hasil generate — tangkap 'Identifier not declared'
SEBELUM CI.

gdparse hanya mem-PARSE; compiler Godot-lah yang menolak identifier tak
terdeklarasi (kasus nyata: helper mati `stats_full_raw` di BossKit.gd:346
memakai `b` padahal parameternya `boss_type` — hanya ketahuan di CI setelah
~2 menit). Skrip ini memakai pohon token lark dari gdtoolkit untuk
memeriksa scope tiap fungsi: identifier yang DIPAKAI harus

  (1) parameter fungsi,
  (2) var/const lokal,
  (3) variabel for / parameter lambda,
  (4) deklarasi level kelas (const/func/enum/signal),
  (5) nama bawaan Godot yang diizinkan (daftar BUILTINS).

Sengaja hanya menargetkan file HASIL GENERATE (BossKit.gd): semesta
identifier-nya dikontrol generator (param b/enemies/target_dist, lokal,
panggilan bridge lewat titik, konstruktor bawaan). File tulisan tangan
seperti Boss.gd memakai `get_tree()`, `await`, dsb. yang akan false-positive
di checker sederhana ini — untuk itu tetap andalkan langkah import CI.

Pemakaian:
    python3 tools/check_bosskit_scope.py            # default: BossKit.gd
    python3 tools/check_bosskit_scope.py file.gd ...
"""
import sys
import gdtoolkit.parser.parser as gdp

DEFAULT_PATHS = [
    "godot/scenes/boss/BossKit.gd",
]

# Token NAME sah tanpa deklarasi: keyword, tipe primitif, konstanta global,
# dan fungsi bawaan yang dipancarkan generator.
BUILTINS = {
    # keyword / nilai
    "true", "false", "null", "self", "super", "pi", "tau", "inf", "nan",
    # tipe & konstruktor
    "int", "float", "bool", "void", "String", "Dictionary", "Array",
    "Vector2", "Vector2i", "Color", "Rect2", "RefCounted", "Node2D",
    # fungsi umum yang dipancarkan generator
    "minf", "maxf", "mini", "maxi", "absf", "absi", "clampf", "floorf",
    "ceilf", "roundf", "sqrt", "pow", "sin", "cos", "tan", "atan2",
    "randf", "randi", "randfn", "randf_range", "randi_range",
    "is_equal_approx", "is_zero_approx", "sign", "signf", "snapped",
    "lerp", "lerpf", "move_toward", "fmod", "fposmod", "wrapf",
    "deg_to_rad", "rad_to_deg", "range_lerp", "smoothstep", "remap",
    "str", "len", "print", "push_error", "push_warning", "typeof",
    "type_string", "range", "hash", "instance_from_id", "weakref",
    "is_instance_valid", "get_instance_id",
}


def walk(node, out):
    out.append(node)
    for ch in getattr(node, "children", []) or []:
        walk(ch, out)


def is_tree(n):
    return type(n).__name__ == "Tree"


def name_tokens(n):
    return [c for c in getattr(n, "children", []) or []
            if not is_tree(c) and c.type == "NAME"]


def function_header(fn):
    """(nama, {param}) dari func_def; anak pertama = func_header."""
    hdr = fn.children[0]
    name = name_tokens(hdr)[0].value
    params = set()
    for c in hdr.children:
        if is_tree(c) and str(getattr(c, "data", "")) == "func_args":
            for a in c.children:
                if is_tree(a):
                    nt = name_tokens(a)
                    if nt:
                        params.add(nt[0].value)
    return name, params


def collect_functions(nodes):
    return [n for n in nodes
            if is_tree(n) and str(getattr(n, "data", "")) == "func_def"]


def ancestors_of(nodes):
    """id(node) -> id(parent)."""
    parent = {}
    for n in nodes:
        for ch in getattr(n, "children", []) or []:
            parent[id(ch)] = n
    return parent


def collect_globals(nodes):
    """Deklarasi level kelas: nama func + const/enum/signal/class di luar
    semua func_def."""
    funcs = collect_functions(nodes)
    func_ids = {id(f) for f in funcs}
    parent = ancestors_of(nodes)

    def in_func(n):
        while id(n) in parent:
            n = parent[id(n)]
            if id(n) in func_ids:
                return True
        return False

    glob = {function_header(f)[0] for f in funcs}
    for n in nodes:
        if not is_tree(n) or in_func(n):
            continue
        d = str(getattr(n, "data", ""))
        if d.startswith(("var_", "const_", "enum_", "signal_")) or d in (
                "signal_stmt", "enum_def", "class_def", "class_name_stmt"):
            for t in name_tokens(n):
                glob.add(t.value)
    return glob


def check_func(fn, globals_allowed, errors, path):
    fname, params = function_header(fn)
    declared = set(params)
    body = []
    for ch in fn.children[1:]:
        walk(ch, body)

    for n in body:
        if not is_tree(n):
            continue
        d = str(getattr(n, "data", ""))
        if d.startswith(("func_var_", "func_const_")):
            nt = name_tokens(n)
            if nt:
                declared.add(nt[0].value)
        elif d == "for_stmt":
            nt = name_tokens(n)
            if nt:
                declared.add(nt[0].value)
        elif d == "func_def":  # nested func: parameternya visible
            _, lp = function_header(n)
            declared |= lp
        elif d == "lambda_header":  # gdtoolkit 4.5: param lambda bersarang
            # di func_args/func_arg_regular — ambil NAME rekursif; body
            # lambda adalah SIBLING lambda_header, jadi tak ikut tersapu.
            def lam_names(x):
                for c in getattr(x, "children", []) or []:
                    if is_tree(c):
                        yield from lam_names(c)
                    elif c.type == "NAME":
                        yield c.value
            declared |= set(lam_names(n))

    allowed = declared | globals_allowed | BUILTINS

    def visit(n, after_dot):
        if not is_tree(n):
            return
        d = str(getattr(n, "data", ""))
        prev_dot = False
        for c in n.children:
            if is_tree(c):
                # sub-tree setelah titik = sisi atribut (b.kit) — receiver
                # dalam sub-tree itu tidak perlu dideklarasi.
                visit(c, prev_dot or (d == "getattr" and after_dot))
                prev_dot = False
            else:
                if c.type == "DOT":
                    prev_dot = True
                    continue
                if c.type == "NAME" and not after_dot and not prev_dot:
                    if c.value not in allowed:
                        errors.append(
                            "%s:%s: identifier '%s' dipakai tapi tidak "
                            "terdeklarasi di func %s"
                            % (path, getattr(c, "line", "?"), c.value, fname))
                prev_dot = False

    for ch in fn.children[1:]:
        visit(ch, False)


def check_file(path):
    src = open(path).read()
    tree = gdp.parse(src, True) if gdp.parse.__code__.co_argcount > 1 \
        else gdp.parse(src)
    nodes = []
    walk(tree, nodes)
    glob = collect_globals(nodes)
    errors = []
    for fn in collect_functions(nodes):
        check_func(fn, glob, errors, path)
    return errors


def main():
    paths = sys.argv[1:] or DEFAULT_PATHS
    total = 0
    for p in paths:
        errs = check_file(p)
        for e in errs[:40]:
            print(e)
        if len(errs) > 40:
            print("... dan %d lagi di %s" % (len(errs) - 40, p))
        print("[scope-check] %s: %s" % ("PASS" if not errs
               else "FAIL (%d)" % len(errs), p))
        total += len(errs)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
