#!/usr/bin/env python3
"""Transpile skill-hero Pygame (hero_skills/_bundle.py) -> GDScript (HeroSkillKit.gd).

    python tools/gen_hero_skill_kit.py           # tulis godot/scenes/hero/HeroSkillKit.gd
    python tools/gen_hero_skill_kit.py --check   # exit 1 kalau file ter-commit basi

Sumber kebenaran: hero_skills/_bundle.py — BaseSkill (guard jangkauan,
cooldown helper, visual duration), ENAM kelas starter (Grimjaw/Kaizen/
Sylara/Thorne/Vex/Zephyr) dan BossHeroSkills (init_state, update_timers,
_SKILL_REGISTRY 66 boss, semua method _cast_*, _fallback_cast). Generator
mem-parse AST dan memancarkan GDScript 4.3 1:1 — koefisien, target, dan
timing TIDAK pernah disalin tangan. Perilaku hasil dijaga oleh
godot/tests/HeroSkillParityTest.tscn vs oracle Pygame
(tools/test_godot_match_parity.py, seksi hero_skills).

KENAPA transpile: 222 hero × 4 skill ≈ 5.000 baris Python. Tulis tangan =
sumber klasik "Godot pakai koefisien lama / boss-hero dapat skill generik
palsu". Regenerasi otomatis menjaga Godot ikut berubah saat bundle berubah
(filosofi sama dengan tools/gen_boss_smart_ai.py).

Aturan pemetaan utama (SATUAN FRAME seperti pygame; konversi detik hanya di
ujung yang menyentuh field Godot yang memang detik):
  * h.x / h.y            -> h.global_position.x/.y
  * h.speed (px/frame)   -> h.move_speed (px/s): tulis *60, baca /60
  * h.attack_cooldown(f) -> h.attack_cooldown (detik): tulis /60, baca *60
  * h.skill_damage (propertY int-chain amp+skill_down di _entity)
                         -> h.kit_skill_damage() (mirror property)
  * h.<state non-inti>   -> h.kit["<nama persis>"] (Dictionary per hero)
  * e.take_damage(d, t[, source=, school=]) -> h.kit_hit(e, d, src, school)
  * e.apply_slow(a, f)   -> h.kit_slow(e, a, f)      (f frame -> detik)
  * e.attack_timer        -> h.kit_atk_timer / kit_lock_attack (frame<->detik)
  * math.hypot(a, b)     -> Vector2(a, b).length()
  * `a / b`              -> float(a) / float(b)      (Python `/` selalu float)
  * blok try/except FX   -> jembatan kit_fx_* (perilaku inti tetap dieksekusi)
  * getattr(h, 'x', d)   -> h.kit.get("x", d) (kecuali nama inti ter-mapping)
  * self._check/trigger_*_cooldown, _set_active_skill, _apply_slow/stun
                         -> helper static kit (inline, durasi visual PER-KIND)
  * inspect.signature dispatch di _generic_cast -> match (hero_type, key)
    dengan arity yang sudah dihitung saat generate (tidak ada introspeksi
    runtime di Godot; registry dibaca langsung dari AST)

BAGIAN YANG TIDAK DITRANSPILE (sengaja, tertulis di docs/GODOT_PARITY.md):
  * BaseSkill._get_enemies/_get_enemies_in_range/_skill_range/_acquire_target/
    _has_target/_deal_aoe_damage/_play_skill_sound/_add_popup/_shake_screen:
    emitter tulis-tangan di header template dengan mirror baris-per-baris
    (memuat try/except float-coercion — bukan pola yang boleh dibuang).
  * Hero.cast_skill (wrapper CDR+spell-vamp) dan pengurangan cooldown per
    frame: hidup di Hero.gd (bukan kit) supaya field-nya tetap terlihat UI.
"""
import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "hero_skills" / "_bundle.py"
OUT = ROOT / "godot" / "scenes" / "hero" / "HeroSkillKit.gd"

STARTERS = ["grimjaw", "kaizen", "sylara", "thorne", "vex", "zephyr"]

# ── field Hero.gd yang dibaca/ditulis LANGSUNG oleh kode kit (bukan h.kit) ──
# Nama pygame -> ekspresi baca (format {r}=recv). Tulis punya tabel sendiri.
HERO_READ = {
    "x": "({r}).global_position.x",
    "y": "({r}).global_position.y",
    "hp": "({r}).hp",
    "max_hp": "({r}).max_hp",
    "damage": "int(({r}).damage)",
    "team": "({r}).team",
    "target": "({r}).target",
    "facing": "({r}).facing",
    "hero_type": "({r}).hero_type",
    "level": "({r}).level",
    "base_damage": "({r}).base_damage",
    "skill_range": "({r}).skill_range",
    "skill_data": "({r}).skill_data",
    "dmg_school": "({r}).dmg_school",
    "active_skill": "({r}).active_skill",
    "active_skill_timer": "({r}).active_skill_timer",
    "skill_timer": "({r}).skill_timer",
    "w_cooldown": "({r}).w_cooldown",
    "e_cooldown": "({r}).e_cooldown",
    "r_cooldown": "({r}).r_cooldown",
    "skill_cooldown_max": "({r}).skill_cooldown_max",
    "w_cooldown_max": "({r}).w_cooldown_max",
    "e_cooldown_max": "({r}).e_cooldown_max",
    "r_cooldown_max": "({r}).r_cooldown_max",
    # properti/frame-conversion:
    "skill_damage": "({r}).kit_skill_damage()",
    "speed": "(float(({r}).move_speed) / 60.0)",
    "attack_cooldown": "int(roundf(float(({r}).attack_cooldown) * 60.0))",
}
HERO_WRITE = {
    "x": "({r}).global_position.x = {v}",
    "y": "({r}).global_position.y = {v}",
    "hp": "({r}).hp = {v}",
    "max_hp": "({r}).max_hp = {v}",
    "damage": "({r}).damage = float({v})",
    "target": "({r}).target = {v}",
    "facing": "({r}).facing = {v}",
    "level": "({r}).level = {v}",
    "base_damage": "({r}).base_damage = {v}",
    "active_skill": "({r}).active_skill = {v}",
    "active_skill_timer": "({r}).active_skill_timer = {v}",
    "skill_timer": "({r}).skill_timer = {v}",
    "w_cooldown": "({r}).w_cooldown = {v}",
    "e_cooldown": "({r}).e_cooldown = {v}",
    "r_cooldown": "({r}).r_cooldown = {v}",
    "speed": "({r}).move_speed = float({v}) * 60.0",
    "attack_cooldown": "({r}).attack_cooldown = float({v}) / 60.0",
}
HERO_AUG = {
    "hp": "({r}).hp {op}= {v}",
    "max_hp": "({r}).max_hp {op}= {v}",
    "damage": "({r}).damage {op}= float({v})",
    "speed": "({r}).move_speed {op}= float({v}) * 60.0",
    "active_skill_timer": "({r}).active_skill_timer {op}= {v}",
}

# Field Hero.gd yang TIDAK boleh dideklarasikan ulang oleh kit.
KIT_NEVER = set(HERO_READ)

# Atribut unit lain (musuh/sekutu) -> ekspresi (format {r}=recv).
UNIT_READ = {
    "x": "({r}).global_position.x",
    "y": "({r}).global_position.y",
    "hp": "({r}).hp",
    "max_hp": "({r}).max_hp",
    "team": "({r}).team",
    "alive": "({r}).kit_unit_alive(({r}))",  # diganti via recv khusus di bawah
    "speed": "(({r}).speed)",
}


class TranspileError(Exception):
    pass


def err(node, method, msg):
    line = getattr(node, "lineno", "?")
    raise TranspileError(f"{method}:L{line}: {msg}")


# ══════════════════════════════════════════════════════════
#  PARSING _bundle.py
# ══════════════════════════════════════════════════════════

def load_bundle():
    """Ambil BaseSkill, 6 kelas starter, dan BossHeroSkills (AST)."""
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    classes = {}

    def walk_collect(node):
        for n in ast.walk(node):
            if isinstance(n, ast.ClassDef):
                methods = {m.name: m for m in n.body if isinstance(m, ast.FunctionDef)}
                consts = {}
                for s in n.body:
                    if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name):
                        consts[s.targets[0].id] = s
                classes[n.name] = {"node": n, "methods": methods, "consts": consts}
            walk_collect_no_recursion(n)

    def walk_collect_no_recursion(n):
        pass

    # top-level + dalam namespace _NS_*
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            if n.name.startswith("_NS_"):
                for m in n.body:
                    if isinstance(m, ast.ClassDef):
                        methods = {f.name: f for f in m.body if isinstance(f, ast.FunctionDef)}
                        consts = {}
                        for s in m.body:
                            if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name):
                                consts[s.targets[0].id] = s
                        classes[m.name] = {"node": m, "methods": methods, "consts": consts}
            else:
                methods = {f.name: f for f in n.body if isinstance(f, ast.FunctionDef)}
                consts = {}
                for s in n.body:
                    if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name):
                        consts[s.targets[0].id] = s
                classes[n.name] = {"node": n, "methods": methods, "consts": consts}
    return classes


def registry_of(boss_cls):
    """_SKILL_REGISTRY -> {hero_type: {key: method_name}} literal dari AST."""
    node = boss_cls["consts"]["_SKILL_REGISTRY"]
    return ast.literal_eval(node.value)


def visual_durations(classes):
    """{kind: {q/w/e/r: frames}} dari SKILL_VISUAL_DURATION tiap kelas."""
    out = {}
    base = classes["BaseSkill"]
    dflt = ast.literal_eval(base["consts"]["_DEFAULT_VISUAL_DURATION"].value)
    for cname, cls in classes.items():
        if cname == "BaseSkill" or "SKILL_VISUAL_DURATION" not in cls["consts"]:
            continue
        try:
            ov = ast.literal_eval(cls["consts"]["SKILL_VISUAL_DURATION"].value)
        except ValueError:
            continue
        if ov:
            out[cname] = {**dflt, **ov}
    return out, dflt


# ══════════════════════════════════════════════════════════
#  EMITTER
# ══════════════════════════════════════════════════════════

def is_h_attr(node, name=None):
    return (isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name) and node.value.id == "h"
            and (name is None or node.attr == name))


def base_name(node):
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


class Emitter:
    def __init__(self, classes, registry, vis, dflt, boss_vis):
        self.classes = classes
        self.registry = registry
        self.vis = vis                       # {ClassName: {key: frames}}
        self.dflt = dflt                     # _DEFAULT_VISUAL_DURATION
        self.boss_vis = boss_vis             # BOSS_HERO_VISUAL_DURATION
        self.kind = "boss"                   # kelas yang lagi ditranspile
        self.aliases = {}                    # ClassName -> alias gd
        for i, cn in enumerate(classes):
            self.aliases[cn] = cn.replace("Skills", "").lower()
        self.helper_calls = set()            # helper static yang direferensikan
        self.state_keys = {}                 # {alias: set(kit keys)} (info)

    # ── nama method global kit ────────────────────────────
    def fname(self, cls_name, mname):
        return f"{self.aliases[cls_name]}_{mname.lstrip('_')}"

    # ── ekspresi ──────────────────────────────────────────
    def expr(self, node, method):
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
                return '"' + v.replace('"', '\\"') + '"'
            err(node, method, f"konstanta tak didukung: {v!r}")

        if isinstance(node, ast.Name):
            if node.id == "HERO_TYPES":
                return "h.kit_catalog_all()"
            if node.id == "HERO_LEVELS":
                return "h.kit_hero_levels()"
            return node.id

        if isinstance(node, ast.Attribute):
            return self.attr_expr(node, method)

        if isinstance(node, ast.Call):
            return self.call(node, method)

        if isinstance(node, ast.BinOp):
            a = self.expr(node.left, method)
            c = self.expr(node.right, method)
            if isinstance(node.op, ast.Add):
                return f"({a}) + ({c})"
            if isinstance(node.op, ast.Sub):
                return f"({a}) - ({c})"
            if isinstance(node.op, ast.Mult):
                return f"({a}) * ({c})"
            if isinstance(node.op, ast.Div):
                return f"float({a}) / float({c})"
            if isinstance(node.op, ast.FloorDiv):
                return f"int(float({a}) / float({c}))"
            if isinstance(node.op, ast.Mod):
                return f"fmod({a}, {c})"
            err(node, method, f"operator biner tak didukung: {type(node.op).__name__}")

        if isinstance(node, ast.UnaryOp):
            v = self.expr(node.operand, method)
            if isinstance(node.op, ast.Not):
                return f"not ({v})"
            if isinstance(node.op, ast.USub):
                return f"-({v})"
            err(node, method, "operator uner tak didukung")

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return " and ".join(f"({self.expr(v, method)})" for v in node.values)
            # `or` di posisi NILAI harus mempertahankan operand (Python),
            # bukan bool (GDScript). Hanya 2 situs tersisa setelah helper
            # tulis-tangan menelan sisanya -> __py_or berantai kanan-ke-kiri.
            acc = self.expr(node.values[-1], method)
            for v in reversed(node.values[:-1]):
                acc = f"__py_or({self.expr(v, method)}, {acc})"
            return acc

        if isinstance(node, ast.Compare):
            m = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=",
                 ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!="}
            if any(type(o) is ast.In for o in node.ops) or any(type(o) is ast.NotIn for o in node.ops):
                return self.in_compare(node, method)
            parts = []
            lhs = node.left
            for op, rhs in zip(node.ops, node.comparators):
                if type(op) not in m:
                    err(node, method, f"compare tak didukung: {type(op).__name__}")
                parts.append(f"({self.expr(lhs, method)}) {m[type(op)]} "
                             f"({self.expr(rhs, method)})")
                lhs = rhs
            return " and ".join(parts)

        if isinstance(node, ast.IfExp):
            return (f"{self.expr(node.body, method)} if {self.expr(node.test, method)} "
                    f"else {self.expr(node.orelse, method)}")

        if isinstance(node, (ast.List, ast.Tuple)):
            return "[" + ", ".join(self.expr(e, method) for e in node.elts) + "]"

        if isinstance(node, ast.Dict):
            items = ", ".join(f"{self.expr(k, method)}: {self.expr(v, method)}"
                              for k, v in zip(node.keys, node.values))
            return "{" + items + "}"

        if isinstance(node, ast.Subscript):
            v = self.expr(node.value, method)
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                # stats["damage"] — Dictionary get literal
                return f'{v}["{sl.value}"]'
            return f"{v}[{self.expr(sl, method)}]"

        if isinstance(node, ast.Set):
            # hit set (vex powershot) -> Dictionary node->true
            return "{}"

        err(node, method, f"ekspresi tak didukung: {type(node).__name__}")

    def in_compare(self, node, method):
        """`skill_key in ('q','w')` dan `id(e) in hit_enemies`."""
        out = []
        lhs = node.left
        for op, rhs in zip(node.ops, node.comparators):
            neg = isinstance(op, ast.NotIn)
            if not (isinstance(op, (ast.In, ast.NotIn))):
                err(node, method, "campuran in/compare lain tak didukung")
            if isinstance(lhs, ast.Call) and isinstance(lhs.func, ast.Name) \
                    and lhs.func.id == "id":
                # id(x) in S  -> S.has(x)
                arg = self.expr(lhs.args[0], method)
                recv = self.expr(rhs, method)
                out.append(f"not ({recv}).has({arg})" if neg else f"({recv}).has({arg})")
            else:
                l = self.expr(lhs, method)
                r = self.expr(rhs, method)
                out.append(f"not ({l} in {r})" if neg else f"({l} in {r})")
            lhs = rhs
        return " and ".join(out)

    # ── atribut ───────────────────────────────────────────
    def attr_expr(self, node, method):
        # self.hero -> h (barekan)
        if (isinstance(node.value, ast.Name) and node.value.id == "self"
                and node.attr == "hero"):
            return "h"
        # self.hero.<x> -> h.<x>
        if (isinstance(node.value, ast.Attribute) and node.value.attr == "hero"
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "self"):
            node = ast.Attribute(value=ast.Name(id="h"), attr=node.attr, ctx=node.ctx)
        recv_name = base_name(node.value) if not isinstance(node.value, ast.Name) else node.value.id
        if isinstance(node.value, ast.Name) and node.value.id == "h":
            return self.hero_read(node.attr, method)
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            # self.<const kelas>
            consts = self.classes[self.cur_class]["consts"]
            if node.attr in consts:
                return self.const_expr(node.attr, method)
            err(node, method, f"self.{node.attr} bukan konstanta kelas")
        if isinstance(node.value, ast.Name) and node.value.id == "math":
            if node.attr == "pi":
                return "__PI"
            err(node, method, "math.<attr> telanjang")
        if node.attr in ("x", "y"):
            return f"({self.expr(node.value, method)}).global_position.{node.attr}"
        if node.attr == "alive":
            return f"h.kit_unit_alive({self.expr(node.value, method)})"
        if node.attr == "attack_timer":
            return f"h.kit_atk_timer({self.expr(node.value, method)})"
        if node.attr in ("hp", "max_hp", "team", "speed", "attack_cooldown"):
            return f"({self.expr(node.value, method)}).{node.attr}"
        return f"({self.expr(node.value, method)}).{node.attr}"

    def hero_read(self, attr, method):
        if attr in HERO_READ:
            return HERO_READ[attr].format(r="h")
        if attr == "alive":
            return "(not h.is_dead)"
        if attr == "projectiles":
            err(None, method, "h.projectiles tidak dipancarkan")
        if attr == "items":
            err(None, method, "h.items hanya lewat wrapper cast_skill (Hero.gd)")
        return f'h.kit.get("{attr}", null)'

    def const_expr(self, name, method):
        consts = self.classes[self.cur_class]["consts"]
        node = consts[name]
        return self.expr(node.value, method)

    # ── panggilan ────────────────────────────────────────
    def call(self, node, method):
        fn = node.func

        if isinstance(fn, ast.Name):
            if fn.id == "getattr":
                return self.getattr_call(node, method)
            if fn.id == "hasattr":
                return self.hasattr_call(node, method)
            if fn.id == "min":
                return "minf(" + ", ".join(self.expr(a, method) for a in node.args) + ")"
            if fn.id == "max":
                return "maxf(" + ", ".join(self.expr(a, method) for a in node.args) + ")"
            if fn.id == "int":
                return f"int({self.expr(node.args[0], method)})"
            if fn.id == "float":
                return f"float({self.expr(node.args[0], method)})"
            if fn.id == "abs":
                return f"absf({self.expr(node.args[0], method)})"
            if fn.id == "len":
                return f"float(({self.expr(node.args[0], method)})).size()"
            if fn.id == "set":
                return "{}"
            if fn.id == "range":
                return "range(" + ", ".join(self.expr(a, method) for a in node.args) + ")"
            if fn.id == "id":
                return self.expr(node.args[0], method)
            if fn.id == "sorted":
                return self.expr(node.args[0], method) + ".duplicate()"
            if fn.id == "get_all_hero_types":
                # settings.get_all_hero_types() -> katalog mentah heroes.json
                return "h.kit_catalog_all()"
            if fn.id == "print":
                return f"push_warning({', '.join(self.expr(a, method) for a in node.args)})"
            err(node, method, f"global call tak didukung: {fn.id}")

        if not isinstance(fn, ast.Attribute):
            err(node, method, "call bentuk lain tak didukung")

        # math.*
        if isinstance(fn.value, ast.Name) and fn.value.id == "math":
            if fn.attr == "hypot":
                a = self.expr(fn and node.args[0], method)
                c = self.expr(node.args[1], method)
                return f"Vector2({a}, {c}).length()"
            if fn.attr in ("cos", "sin", "atan2"):
                return fn.attr + "(" + ", ".join(self.expr(a, method) for a in node.args) + ")"
            if fn.attr == "pi":
                err(node, method, "math.pi telanjang")

        # f.get(...) pada dict lokal (stats, data, recipe, per_hero) — Dictionary.get ✓
        # take_damage
        if fn.attr == "take_damage":
            recv = self.expr(fn.value, method)
            args = node.args
            if len(args) != 2:
                err(node, method, f"take_damage harus 2 positional (dapat {len(args)})")
            src = "null"
            school = '""'
            for kw in node.keywords:
                if kw.arg == "source":
                    src = self.expr(kw.value, method)
                elif kw.arg == "school":
                    school = self.expr(kw.value, method)
                else:
                    err(node, method, f"kw take_damage tak didukung: {kw.arg}")
            return (f"h.kit_hit({recv}, {self.expr(args[0], method)}, "
                    f"{self.expr(args[1], method)}, {src}, {school})")

        if fn.attr == "apply_slow":
            recv = self.expr(fn.value, method)
            if len(node.args) != 2:
                err(node, method, "apply_slow harus 2 argumen")
            return (f"h.kit_slow({recv}, {self.expr(node.args[0], method)}, "
                    f"{self.expr(node.args[1], method)})")

        # self._helper(...) handler internal
        if isinstance(fn.value, ast.Name) and fn.value.id == "self":
            return self.self_call(fn.attr, node, method)

        # metode objek lain: .append / .sort / .add / .get / _fx.notify* / shake / play / signature
        recv = self.expr(fn.value, method)
        if fn.attr == "_spawn_skill_projectile":
            sp = kw = None
            for k in node.keywords:
                if k.arg == "speed":
                    sp = self.expr(k.value, method)
            if len(node.args) > 1:
                sp = self.expr(node.args[1], method)
            return f"__spawn_skill_proj(h, {self.expr(node.args[0], method)}, {sp or '13.0'})"
        if fn.attr == "append":
            return f"{recv}.append({self.expr(node.args[0], method)})"
        if fn.attr == "get":
            args = ", ".join(self.expr(a, method) for a in node.args)
            return f"{recv}.get({args})"
        if fn.attr == "add":
            return f"{recv}[{self.expr(node.args[0], method)}] = true"
        if fn.attr == "sort":
            if node.keywords and node.keywords[0].arg == "key":
                return f"{recv}.sort_custom(func(a, b): return __by_pair0(a, b))"
            err(node, method, "sort tanpa key= tak didukung")
        if fn.attr == "play":  # SoundManager().play
            vol = "0.7"
            for kw in node.keywords:
                if kw.arg == "volume_mult":
                    vol = self.expr(kw.value, method)
            return f"h.kit_sound(float({vol}))"
        if fn.attr in ("notify_skill_cast", "notify_skill_impact"):
            return self.fx_call(fn.attr, node, method)
        if fn.attr == "shake_screen":
            return f"h.kit_shake(float({self.expr(node.args[0], method)}))"
        if fn.attr == "add_damage_number":
            txt = self.fx_text(node.args[2], method)
            crit = "false"
            for kw in node.keywords:
                if kw.arg == "is_critical":
                    crit = self.expr(kw.value, method)
            return f"h.kit_popup({txt}, {crit})"
        err(node, method, f"metode tak didukung: .{fn.attr}")

    def fx_call(self, kind, node, method):
        a = [self.expr(x, method) for x in node.args]
        if kind == "notify_skill_cast":
            return f"h.kit_fx_cast({a[1]})"
        # notify_skill_impact(self, x, y, r, key) / kwargs radius/skill
        x = a[1]; y = a[2]
        r = "0.0"; k = '"q"'
        if len(a) >= 4:
            r = a[3]
        if len(a) >= 5:
            k = a[4]
        for kw in node.keywords:
            if kw.arg == "radius":
                r = self.expr(kw.value, method)
            elif kw.arg == "skill":
                k = self.expr(kw.value, method)
        return f"h.kit_fx_impact({x}, {y}, {r}, {k})"

    def fx_text(self, node, method):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return '"' + node.value + '"'
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append('"' + v.value + '"')
                elif isinstance(v, ast.FormattedValue):
                    parts.append(f"str({self.expr(v.value, method)})")
                else:
                    err(node, method, "f-string FX bagian tak dikenali")
            return " + ".join(parts) if parts else '""'
        return self.expr(node, method)

    def getattr_call(self, node, method):
        args = node.args
        if len(args) < 2:
            err(node, method, "getattr argumen kurang")
        # normalisasi self.hero -> h
        if (isinstance(args[0], ast.Attribute) and args[0].attr == "hero"
                and isinstance(args[0].value, ast.Name)
                and args[0].value.id == "self"):
            args = [ast.Name(id="h")] + list(args[1:])
        base, name_node = args[0], args[1]
        default = self.expr(args[2], method) if len(args) == 3 else "null"
        if isinstance(name_node, ast.Constant):
            name = name_node.value
            if isinstance(base, ast.Name) and base.id == "h":
                if name == "range":
                    # getattr(h, 'range', 0) — h.range = attack range
                    return "float(h.attack_range)"
                if name == "alive":
                    return "(not h.is_dead)"
                if name in HERO_READ:
                    return HERO_READ[name].format(r="h")
                return f'h.kit.get("{name}", {default})'
            if isinstance(base, ast.Name) and base.id == "self":
                err(node, method, "getattr(self, ...) dinamis")
            recv = self.expr(base, method)
            if name == "alive":
                return f"h.kit_unit_alive({recv})"
            if name == "attack_timer":
                return f"h.kit_atk_timer({recv})"
            return f'({recv}).get("{name}", {default})'
        err(node, method, f"getattr nama nonliteral: {ast.unparse(node)[:60]}")

    def hasattr_call(self, node, method):
        args = node.args
        if len(args) != 2 or not isinstance(args[1], ast.Constant):
            err(node, method, "hasattr nonliteral")
        recv = self.expr(args[0], method)
        key = args[1].value
        if key == "apply_slow":
            return f"h.kit_has_slow({recv})"
        if key == "attack_timer":
            return f"h.kit_has_atk_timer({recv})"
        if key == "hp":
            return f"h.kit_has_hp({recv})"
        if key == "game_instance":
            return "false"  # guard __main__ harness
        err(node, method, f"hasattr('{key}') tak didukung")

    # ── self.<method> handler → helper/panggilan static ──
    def self_call(self, attr, node, method):
        args = [self.expr(a, method) for a in node.args]
        kw = {k.arg: self.expr(k.value, method) for k in node.keywords}

        if attr == "_check_q_cooldown":
            return "h.skill_timer <= 0"
        if attr == "_check_w_cooldown":
            return "h.w_cooldown <= 0"
        if attr == "_check_e_cooldown":
            return "h.e_cooldown <= 0"
        if attr == "_check_r_cooldown":
            return "h.r_cooldown <= 0"

        if attr == "_get_enemies":
            return f"h.kit_enemies({', '.join(args)})"

        # helper dengan posisi eksplisit + default (gdparse tidak menerima
        # named-args; pemanggilan disusun posisional persis urutan pygame)
        layout = {
            "_get_enemies_in_range": (
                "__enemies_in_range", 'h',
                ["all_units", "all_towers", "all_bases", "range_val",
                 "center_x", "center_y"],
                {"center_x": "null", "center_y": "null"}),
            "_deal_aoe_damage": (
                "__deal_aoe", 'h',
                ["all_units", "all_towers", "all_bases", "range_val",
                 "damage_multiplier"],
                {"range_val": "0.0", "damage_multiplier": "1.0"}),
            "_acquire_target": (
                "__acquire_target", 'h',
                ["all_units", "all_towers", "all_bases", "range_val"],
                {"range_val": "null"}),
            "_has_target": (
                "__has_target", 'h',
                ["all_units", "all_towers", "all_bases", "range_val"],
                {"range_val": "null"}),
            "_skill_range": ("__skill_range", 'h', ["fallback"], {"fallback": "200.0"}),
            "_set_active_skill": ("__set_active", f'h, "{{kind}}"', ["key", "duration"],
                                  {"duration": "null"}),
            "_trigger_q_cooldown": ("__trigger_q", f'h, "{{kind}}"',
                                    ["shake_amount", "visual_duration"],
                                    {"shake_amount": "8.0", "visual_duration": "null"}),
            "_trigger_w_cooldown": ("__trigger_w", f'h, "{{kind}}"',
                                    ["shake_amount", "visual_duration"],
                                    {"shake_amount": "5.0", "visual_duration": "null"}),
            "_trigger_e_cooldown": ("__trigger_e", f'h, "{{kind}}"',
                                    ["shake_amount", "visual_duration"],
                                    {"shake_amount": "6.0", "visual_duration": "null"}),
            "_trigger_r_cooldown": ("__trigger_r", f'h, "{{kind}}"',
                                    ["shake_amount", "visual_duration"],
                                    {"shake_amount": "15.0", "visual_duration": "null"}),
            "_get_visual_duration": ("__vis_dur", '"{kind}", h', ["key"], {}),
        }
        if attr in layout:
            gname, prefix_t, order, defaults = layout[attr]
            # helper ini milik BaseSkill (diwarisi) — parameternya statis,
            # tercantum di `order` (nama pygame sama persis dengan sumber).
            pypos = order
            slots = {}
            for pname, aval in zip(pypos, args):
                slots[pname] = aval
            for kname, kval in kw.items():
                slots[kname] = kval
            built = []
            for slot_name in order:
                if slot_name in slots:
                    built.append(slots[slot_name])
                elif slot_name in defaults:
                    built.append(defaults[slot_name])
            prefix = prefix_t.replace("{kind}", self.kind)
            return f"{gname}({prefix}, {', '.join(built)})"
        if attr == "_apply_slow":
            return f"h.kit_slow({args[0]}, {args[1]}, {args[2]})"
        if attr == "_apply_stun":
            return f"h.kit_lock({args[0]}, {args[1]})"
        if attr == "_shake_screen":
            return f"h.kit_shake(float({args[0]}))"
        if attr == "_play_skill_sound":
            v = kw.get("volume", args[0] if args else "0.7")
            return f"h.kit_sound(float({v}))"
        if attr == "_add_popup":
            crit = kw.get("is_critical", "false")
            return f"h.kit_popup({args[2]}, {crit})"
        if attr == "_set_active_skill":
            dur = kw.get("duration", args[1] if len(args) > 1 else "null")
            return f"__set_active(h, \"{self.kind}\", {args[0]}, {dur})"
        if attr in ("_trigger_q_cooldown", "_trigger_w_cooldown",
                    "_trigger_e_cooldown", "_trigger_r_cooldown"):
            key = attr[len("_trigger_")]
            shake = kw.get("shake_amount", {"q": "8", "w": "5", "e": "6", "r": "15"}[key])
            vd = kw.get("visual_duration", "null")
            return f"__trigger_{key}(h, \"{self.kind}\", {shake}, {vd})"
        if attr == "_get_visual_duration":
            return f"__vis_dur(\"{self.kind}\", h, {args[0]})"
        if attr == "_spawn_skill_projectile":
            sp = kw.get("speed", args[1] if len(args) > 1 else "13.0")
            return f"__spawn_skill_proj(h, {args[0]}, {sp})"
        if attr == "_generic_cast":
            return f"__boss_generic(h, {args[0]}, {args[1]}, {args[2]}, {args[3]})"
        if attr == "_fallback_cast":
            return f"__fallback_cast({', '.join(args)})"
        if attr == "_cast_steel_wind":
            return f"{self.fname(self.cur_class, attr)}(h)"
        # method milik kelas yang sama. Emiten men-PREPEND param `h` bila
        # def Python tidak punya param h pertama (badannya `h = self.hero`).
        # Call site: argumen 1:1, ditambah "h" di depan bila callee butuh.
        cls_methods = self.classes[self.cur_class]["methods"]
        if attr in cls_methods:
            params = [a.arg for a in cls_methods[attr].args.args if a.arg != "self"]
            takes_h = bool(params) and params[0] == "h"
            call_args = args if takes_h else (["h"] + args)
            arity = len(params) if takes_h else (len(params) + 1)
            if len(call_args) != arity:
                err(node, method, f"self.{attr}() args {len(args)} vs kebutuhan {arity}")
            return f"{self.fname(self.cur_class, attr)}({', '.join(call_args)})"
        # method lintas-registry (hanya mungkin di BossHeroSkills, via getattr
        # yang sudah diganti dispatch) — di sini harusnya tidak pernah:
        err(node, method, f"self.{attr}() tak dikenali")

    # ── pernyataan ────────────────────────────────────────
    def stmt(self, s, out, indent, method):
        pad = "\t" * indent

        # `h = self.hero` — fungsi generated sudah menerima h sebagai argumen.
        if (isinstance(s, ast.Assign) and len(s.targets) == 1
                and isinstance(s.targets[0], ast.Name) and s.targets[0].id == "h"
                and isinstance(s.value, ast.Attribute) and s.value.attr == "hero"
                and isinstance(s.value.value, ast.Name) and s.value.value.id == "self"):
            return

        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Constant):
                return
            out.append(pad + self.expr(s.value, method))
            return

        if isinstance(s, ast.Assign):
            if len(s.targets) != 1:
                err(s, method, "multi-target assign")
            tgt = s.targets[0]
            val = self.expr(s.value, method)
            if isinstance(tgt, (ast.Tuple, ast.List)):
                if isinstance(s.value, (ast.Tuple, ast.List)) and \
                        len(tgt.elts) == len(s.value.elts):
                    for t, v in zip(tgt.elts, s.value.elts):
                        self.assign_one(t, self.expr(v, method), out, pad, method, s)
                    return
                # tuple-assign dari sumber runtime (mis. h.x, h.y = h._shadow_return)
                # -> simpan ke var sementara, indeks berurutan (list pygame == Array)
                n = len(tgt.elts)
                for i, t in enumerate(tgt.elts):
                    if isinstance(t, ast.Name):
                        out.append(pad + f'{t.id} = {val}[{i}]')
                    else:
                        sub = ast.Subscript(value=ast.Name(id="__ta"),
                                            slice=ast.Constant(value=i),
                                            ctx=ast.Load())
                        self.assign_one(t, self.expr(sub, method), out, pad, method, s)
                if not all(isinstance(t, ast.Name) for t in tgt.elts):
                    out.insert(len(out) - n, pad + f"var __ta = {val}")
                return
            self.assign_one(tgt, val, out, pad, method, s)
            return

        if isinstance(s, ast.AugAssign):
            val = self.expr(s.value, method)
            op = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
                  ast.FloorDiv: "/", ast.Mod: "%"}.get(type(s.op))
            if op is None:
                err(s, method, "aug-assign operator tak didukung")
            t = s.target
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "h":
                if t.attr in HERO_AUG:
                    out.append(pad + HERO_AUG[t.attr].format(r="h", op=op, v=val))
                    return
                if t.attr in HERO_WRITE:
                    cur = self.expr(t, method)
                    if op == "/":
                        out.append(pad + f"{cur if False else self.hero_read(t.attr, method)} = float({self.hero_read(t.attr, method)}) / float({val})")
                    else:
                        out.append(pad + HERO_WRITE[t.attr].format(r="h", v=f"({self.hero_read(t.attr, method)}) {op} ({val})"))
                    return
                out.append(pad + f'h.kit["{t.attr}"] = ({self.hero_read(t.attr, method)}) {op} ({val})')
                return
            if isinstance(t, ast.Attribute):
                recv = self.expr(t.value, method)
                if t.attr in ("x", "y"):
                    out.append(pad + f"{recv}.global_position.{t.attr} {op}= {val}")
                    return
                if t.attr in ("hp", "max_hp"):
                    out.append(pad + f"{recv}.{t.attr} {op}= {val}")
                    return
                err(s, method, f"aug-assign unit.{t.attr}")
            if isinstance(t, ast.Name):
                out.append(pad + f"{t.id} {op}= {val}")
                return
            err(s, method, "aug-assign target tak dikenal")
            return

        if isinstance(s, ast.If):
            out.append(pad + "if " + self.expr(s.test, method) + ":")
            self.block(s.body, out, indent + 1, method, s)
            orelse = s.orelse
            while orelse and len(orelse) == 1 and isinstance(orelse[0], ast.If):
                e2 = orelse[0]
                out.append(pad + "elif " + self.expr(e2.test, method) + ":")
                self.block(e2.body, out, indent + 1, method, e2)
                orelse = e2.orelse
            if orelse:
                out.append(pad + "else:")
                self.block(orelse, out, indent + 1, method, s)
            return

        if isinstance(s, ast.For):
            it = s.iter
            # nearby.sort sudah di handle; `for e in self._get_enemies(...)` biasa
            out.append(pad + f"for {self.expr(s.target, method)} in {self.expr(it, method)}:")
            self.block(s.body, out, indent + 1, method, s)
            if s.orelse:
                err(s, method, "for-else")
            return

        if isinstance(s, ast.Return):
            if s.value is None:
                out.append(pad + "return null")
            else:
                out.append(pad + "return " + self.expr(s.value, method))
            return

        if isinstance(s, ast.Continue):
            out.append(pad + "continue")
            return
        if isinstance(s, ast.Break):
            out.append(pad + "break")
            return
        if isinstance(s, ast.Pass):
            out.append(pad + "pass")
            return

        if isinstance(s, ast.Try):
            # 16 try: SEMUA blok FX (shake/popup/sound/notify) kecuali dua di
            # yang sudah dipindah ke emitter tulisan tangan (coercion
            # _skill_range + dispatch signature _generic_cast — tak ditranspile).
            if not self.is_fx_try(s):
                err(s, method, "try non-FX: perlu penanganan eksplisit generator")
            for sub in s.body:
                self.fx_stmt(sub, out, indent, method)
            # handler `except Exception as e: pass` = FX gagal senyap -> tak ada
            if s.finalbody:
                err(s, method, "try/finally")
            return

        if isinstance(s, (ast.Import, ast.ImportFrom)):
            return  # import in-function settings/inspect — dipetakan ke bridge

        err(s, method, f"pernyataan tak didukung: {type(s).__name__}")

    def is_fx_try(self, stmt):
        for sub in ast.walk(stmt):
            if isinstance(sub, (ast.Import, ast.ImportFrom)):
                mod = sub.module if isinstance(sub, ast.ImportFrom) else ""
                names = ", ".join(a.name for a in sub.names)
                if not (mod in ("heroes", "__main__") or "fx" in (mod or "")
                        or "fx" in names or "__main__" in names):
                    return False
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                txt = ast.unparse(sub.func)
                if not ("fx" in txt or "effects" in txt or "game_instance" in txt
                        or "__main__" in txt):
                    return False
        return True

    def fx_stmt(self, s, out, indent, method):
        pad = "\t" * indent
        if isinstance(s, (ast.Import, ast.ImportFrom)):
            return
        if isinstance(s, ast.Assign) and isinstance(s.value, ast.Attribute) \
                and isinstance(s.value.value, ast.Attribute) \
                and base_name(s.value) == "__main__":
            return  # game = __main__.game_instance
        if isinstance(s, ast.If):
            t = s.test
            if (isinstance(t, ast.Call) and isinstance(t.func, ast.Name)
                    and t.func.id == "hasattr"):
                for sub in s.body:
                    self.fx_stmt(sub, out, indent, method)
                return
            out.append(pad + "if " + self.expr(t, method) + ":")
            for sub in s.body:
                self.fx_stmt(sub, out, indent + 1, method)
            if s.orelse:
                out.append(pad + "else:")
                for sub in s.orelse:
                    self.fx_stmt(sub, out, indent + 1, method)
            return
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
            out.append(pad + self.call(s.value, method))
            return
        err(s, method, f"FX stmt tak dikenali: {type(s).__name__}")

    def assign_one(self, target, value, out, pad, method, s):
        if isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name) and target.value.id == "h":
                a = target.attr
                if a in HERO_WRITE:
                    out.append(pad + HERO_WRITE[a].format(r="h", v=value))
                    return
                if a in ("skill_damage", "speed_guard"):
                    if a == "skill_damage":
                        out.append(pad + f"h._skill_damage_value_set({value})")
                        return
                if a == "_spawn_skill_projectile":
                    err(s, method, "tulis method?")
                out.append(pad + f'h.kit["{a}"] = {value}')
                return
            # tulis via self.hero.<a>
            if isinstance(target.value, ast.Attribute) and target.value.attr == "hero":
                return self.assign_one(
                    ast.Attribute(value=ast.Name(id="h"), attr=target.attr,
                                  ctx=target.ctx), value, out, pad, method, s)
            recv = self.expr(target.value, method)
            if target.attr in ("x", "y"):
                out.append(pad + f"{recv}.global_position.{target.attr} = {value}")
                return
            if target.attr == "attack_timer":
                if (isinstance(s, ast.Assign) and isinstance(s.value, ast.Call)
                        and isinstance(s.value.func, ast.Name)
                        and s.value.func.id == "max"):
                    out.append(pad + f"h.kit_lock({recv}, {value})")
                    return
                out.append(pad + f"{recv}.attack_timer = float({value}) / 60.0")
                return
            if target.attr in ("hp", "max_hp", "alive", "team", "facing",
                               "speed", "stun_timer", "armor", "damage"):
                out.append(pad + f"{recv}.{target.attr} = {value}")
                return
            err(s, method, f"tulis unit.{target.attr} tak didukung")
        if isinstance(target, ast.Name):
            out.append(pad + f"{target.id} = {value}")
            return
        if isinstance(target, ast.Subscript):
            err(s, method, "subscript assign — cek")
        err(s, method, "target assign tak didukung")

    def block(self, body, out, indent, method, owner):
        if not body:
            out.append("\t" * indent + "pass")
            return
        for s in body:
            self.stmt(s, out, indent, method)

    # ── level method ──────────────────────────────────────
    def collect_locals(self, fn):
        # "h" selalu parameter (h = self.hero yang di-skip tidak boleh jadi var)
        params = {a.arg for a in fn.args.args} - {"self"} | {"h"}
        names, fors = set(), set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
            if isinstance(node, ast.For):
                for n2 in ast.walk(node.target):
                    if isinstance(n2, ast.Name):
                        fors.add(n2.id)
            if isinstance(node, (ast.Tuple,)) and node.elts:
                pass
        return sorted(n for n in names if n not in params and n not in fors)

    def emit_func(self, cls_name, fn):
        self.cur_class = cls_name
        self.kind = "boss" if cls_name == "BossHeroSkills" else self.aliases[cls_name]
        params = [a.arg for a in fn.args.args if a.arg != "self"]
        name = self.fname(cls_name, fn.name)
        args = (["h"] if "h" not in params else []) + params
        out = [f"## hero_skills/_bundle.py:{fn.lineno}-{fn.end_lineno} [{cls_name}.{fn.name}]",
               f"static func {name}({', '.join(args)}):"]
        locs = self.collect_locals(fn)
        # nama yang ditarget tuple-assign (best, best_dist) juga lokal
        for nm in locs:
            out.append(f"\tvar {nm} = null")
        if locs:
            out.append("")
        for s in fn.body:
            if isinstance(s, ast.Expr) and isinstance(s.value, (ast.Constant,)):
                continue
            self.stmt(s, out, 1, fn.name)
        if not locs:
            pass
        return "\n".join(out)

    # ── per-class pipeline ────────────────────────────────
    def transpile_class(self, cls_name, skip=()):
        cls = self.classes[cls_name]
        parts = []
        for mname, fn in cls["methods"].items():
            if mname in skip or mname in ("__init__",):
                continue
            if mname.startswith(("cast_q", "cast_w", "cast_e", "cast_r",
                                 "_cast_", "update_timers")) or \
                    (cls_name == "BaseSkill" and mname.startswith("_")):
                parts.append(self.emit_func(cls_name, fn))
        return parts


# ══════════════════════════════════════════════════════════
#  HEADER TULIS-TANGAN (helper BaseSkill yang memuat try/except logika)
# ══════════════════════════════════════════════════════════

HEADER = r'''## ── helper setara BaseSkill (emitter tulis-tangan; mirror baris per baris
##    BaseSkill._skill_range/_acquire_target/_has_target/_get_enemies_in_range/
##    _deal_aoe_damage/_get_visual_duration/_set_active_skill/_trigger_*) ──

static func __truthy(v) -> bool:
	## Semantik truthiness Python untuk nilai Variant.
	if v == null:
		return false
	if v is bool:
		return v
	if v is int or v is float:
		return float(v) != 0.0
	if v is String:
		return v != ""
	if v is Array:
		return not (v as Array).is_empty()
	if v is Dictionary:
		return not (v as Dictionary).is_empty()
	return true


static func __py_or(a, b):
	## `a or b` di posisi NILAI (Python mengembalikan operand, bukan bool).
	return a if __truthy(a) else b

static func __skill_range(h, fallback := 200.0) -> float:
	## BaseSkill._skill_range: max(h.range, skill_range) dengan koersi float
	## dan fallback lewat skill_data kalau skill_range kosong (L195-208).
	var rng = h.skill_range
	if rng == null or float(rng) == 0.0:
		var data = h.skill_data
		rng = data.get("skill_range", fallback) if data != null else fallback
	var r := 0.0
	if rng != null:
		r = float(rng) if (rng is float or rng is int) else float(fallback)
	else:
		r = float(fallback)
	return maxf(float(h.attack_range), r)


static func __enemies_in_range(h, all_units, all_towers, all_bases, range_val: float = 0.0,
		center_x = null, center_y = null):
	## BaseSkill._get_enemies_in_range -> list [[e, dist], ...] ( urutan sama).
	var cx = float(h.global_position.x) if center_x == null else float(center_x)
	var cy = float(h.global_position.y) if center_y == null else float(center_y)
	var enemies = h.kit_enemies(all_units, all_towers, all_bases)
	var in_range := []
	for e in enemies:
		var dx = float(e.global_position.x) - cx
		var dy = float(e.global_position.y) - cy
		var dist := Vector2(dx, dy).length()
		if dist <= range_val:
			in_range.append([e, dist])
	return in_range


static func __deal_aoe(h, all_units, all_towers, all_bases,
		range_val := 0.0, damage_multiplier := 1.0):
	## BaseSkill._deal_aoe_damage — return hit_count.
	var enemies = h.kit_enemies(all_units, all_towers, all_bases)
	var hit_count := 0
	for e in enemies:
		var dist := Vector2(float(e.global_position.x) - float(h.global_position.x),
			float(e.global_position.y) - float(h.global_position.y)).length()
		if dist <= float(range_val):
			var damage := int(float(h.kit_skill_damage()) * float(damage_multiplier))
			h.kit_hit(e, damage, h.team, h, h.dmg_school)
			hit_count += 1
	return hit_count


static func __acquire_target(h, all_units, all_towers, all_bases, range_val = null):
	## BaseSkill._acquire_target — slack 1.15, retarget h.target.
	if range_val == null:
		range_val = __skill_range(h)
	var reach: float = float(range_val) * 1.15
	var cur = h.target
	if cur != null and is_instance_valid(cur) and h.kit_unit_alive(cur):
		if Vector2(float(cur.global_position.x) - float(h.global_position.x),
				float(cur.global_position.y) - float(h.global_position.y)).length() <= reach:
			return cur
	var best = null
	var best_dist: float = reach
	for e in h.kit_enemies(all_units, all_towers, all_bases):
		if not h.kit_unit_alive(e):
			continue
		var d = Vector2(float(e.global_position.x) - float(h.global_position.x),
			float(e.global_position.y) - float(h.global_position.y)).length()
		if d <= best_dist:
			best = e
			best_dist = d
	if best != null:
		h.target = best
	return best


static func __has_target(h, all_units, all_towers, all_bases, range_val = null) -> bool:
	## BaseSkill._has_target + REQUIRE_TARGET. Generator MEMVALIDASI tidak ada
	## kelas yang meng-override REQUIRE_TARGET (semua True) — kalau someday
	## ada yang False, generate gagal dan helper ini perlu param kind.
	return __acquire_target(h, all_units, all_towers, all_bases, range_val) != null


static func __vis_dur(kind: String, h, key) -> int:
	## BaseSkill._get_visual_duration + override per kelas/boss.
	var per_hero: Dictionary = BOSS_HERO_VISUAL_DURATION.get(str(h.hero_type), {})
	if kind == "boss":
		if per_hero.has(key):
			return int(per_hero[key])
		return int(DEFAULT_VISUAL_DURATION[key])
	if VISUAL_DURATION.has(kind) and VISUAL_DURATION[kind].has(key):
		return int(VISUAL_DURATION[kind][key])
	return int(DEFAULT_VISUAL_DURATION[key])


static func __set_active(h, kind: String, key, duration = null) -> void:
	## BaseSkill._set_active_skill
	if duration == null:
		duration = __vis_dur(kind, h, key)
	h.active_skill = key
	h.active_skill_timer = int(duration)


static func __trigger_q(h, kind: String, shake_amount = 8.0, visual_duration = null) -> void:
	h.skill_timer = h.skill_cooldown_max
	__set_active(h, kind, "q", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(0.7)


static func __trigger_w(h, kind: String, shake_amount = 5.0, visual_duration = null) -> void:
	h.w_cooldown = h.w_cooldown_max
	__set_active(h, kind, "w", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(0.6)


static func __trigger_e(h, kind: String, shake_amount = 6.0, visual_duration = null) -> void:
	h.e_cooldown = h.e_cooldown_max
	__set_active(h, kind, "e", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(0.7)


static func __trigger_r(h, kind: String, shake_amount = 15.0, visual_duration = null) -> void:
	h.r_cooldown = h.r_cooldown_max
	__set_active(h, kind, "r", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(1.0)


static func __by_pair0(a, b) -> bool:
	## nearby.sort(key=lambda t: t[0]) + tie-break indeks (stabilitas sort
	## Python ditiru lewat elemen [d, e, idx]).
	if float(a[0]) == float(b[0]):
		return int(a[2]) < int(b[2])
	return float(a[0]) < float(b[0])


static func __spawn_skill_proj(h, target, speed := 13.0) -> void:
	## Hero._spawn_skill_projectile: visual homing TANPA damage (damage skill
	## sudah instan). Di harness replay (hero.kit_no_projectiles) dilewati.
	h.kit_skill_proj(target)


static func __fallback_cast(h, enemies, skill_key) -> void:
	## BossHeroSkills._fallback_cast — satu-satunya jalan untuk boss-hero tanpa
	## resep registry. Damage: int(skill_damage * mult) dengan mult
	## q1.0/w1.2/e1.5/r2.5, AOE 150/200, sekolah = dmg_school hero.
	h.active_skill = skill_key
	h.active_skill_timer = 40
	var mults := {"q": 1.0, "w": 1.2, "e": 1.5, "r": 2.5}
	var mult: float = float(mults.get(skill_key, 1.0))
	var _school = h.dmg_school
	if skill_key == "q" or skill_key == "w":
		if h.target != null and is_instance_valid(h.target) and h.kit_unit_alive(h.target):
			h.kit_hit(h.target, int(float(h.kit_skill_damage()) * mult), h.team, h, _school)
	else:
		var aoe_range := 150.0 if skill_key == "e" else 200.0
		for e in enemies:
			var dist := Vector2(float(e.global_position.x) - float(h.global_position.x),
				float(e.global_position.y) - float(h.global_position.y)).length()
			if dist <= aoe_range:
				h.kit_hit(e, int(float(h.kit_skill_damage()) * mult), h.team, h, _school)
'''


GENERIC_CAST = r'''## BossHeroSkills._generic_cast — COOLDOWN CHECK DULU, lalu guard anti-buang
## (cast_range = max(int(skill_range or 100), 140) TANPA slack 1.15), retarget
## ke musuh terdekat, dispatch registry, fallback tanpa resep (cooldown tetap
## terbakar), lalu trigger. Urutan dan angka mirror persis (L888-962);
## dispatch inspect.signature diganti match yang dibangkitkan (arity
## dihitung dari AST — hasil identik).
static func __boss_generic(h, skill_key, all_units, all_towers, all_bases) -> bool:
	match skill_key:
		"q":
			if not (h.skill_timer <= 0):
				return false
		"w":
			if not (h.w_cooldown <= 0):
				return false
		"e":
			if not (h.e_cooldown <= 0):
				return false
		"r":
			if not (h.r_cooldown <= 0):
				return false
		_:
			return false
	var enemies = h.kit_enemies(all_units, all_towers, all_bases)
	var cast_range: float = float(maxi(int(float(h.skill_range)) if int(h.skill_range or 100) else 100, 140))
	var nearby := []
	for e in enemies:
		var d = Vector2(float(e.global_position.x) - float(h.global_position.x),
			float(e.global_position.y) - float(h.global_position.y)).length()
		if d <= cast_range:
			nearby.append([d, e, nearby.size()])
	if nearby.is_empty():
		return false
	nearby.sort_custom(func(a, b): return __by_pair0(a, b))
	var tgt = h.target
	if not (tgt != null and is_instance_valid(tgt) and h.kit_unit_alive(tgt)
			and Vector2(float(tgt.global_position.x) - float(h.global_position.x),
				float(tgt.global_position.y) - float(h.global_position.y)).length() <= cast_range):
		h.target = nearby[0][1]
	if not RECIPE_TYPES.has(str(h.hero_type)):
		__fallback_cast(h, enemies, skill_key)
		match skill_key:
			"q": __trigger_q(h, "boss", 10.0)
			"w": __trigger_w(h, "boss", 8.0)
			"e": __trigger_e(h, "boss", 8.0)
			"r": __trigger_r(h, "boss", 15.0)
		return true
	var ok := __registry_dispatch(h, skill_key, nearby[0][1] if false else enemies)
	if not ok:
		return false
	match skill_key:
		"q": __trigger_q(h, "boss", 10.0)
		"w": __trigger_w(h, "boss", 8.0)
		"e": __trigger_e(h, "boss", 8.0)
		"r": __trigger_r(h, "boss", 15.0)
	return true
'''


def dispatch_and_funcs(em, registry, boss_cls):
    """Match dispatch (hero_type,key)->panggilan static + aritas eksplisit."""
    methods = boss_cls["methods"]
    lines = ["static func __registry_dispatch(h, skill_key, enemies) -> bool:",
             "\tmatch str(h.hero_type):"]
    for hero_type in sorted(registry):
        recipe = registry[hero_type]
        lines.append(f'\t\t"{hero_type}":')
        for key in ("q", "w", "e", "r"):
            if key not in recipe:
                # pygame: recipe.get(key) None -> return False TANPA burn cd
                lines.append(f'\t\t\tif skill_key == "{key}":')
                lines.append("\t\t\t\treturn false")
                continue
            mname = recipe[key]
            fn = methods.get(mname)
            if fn is None:
                raise TranspileError(f"registry {hero_type}.{key} -> {mname} tidak ada")
            arity = len(fn.args.args) - 1
            call = f"{em.fname('BossHeroSkills', mname)}(h)" if arity == 1 \
                else f"{em.fname('BossHeroSkills', mname)}(h, enemies)"
            if arity not in (1, 2):
                raise TranspileError(f"arity {arity} {mname}")
            lines.append(f'\t\t\tif skill_key == "{key}":')
            lines.append(f"\t\t\t\t{call}")
            lines.append("\t\t\t\treturn true")
        lines.append("\t\t\treturn false")
    lines.append("\t\t_:")
    lines.append("\t\t\treturn false")
    lines.append("\treturn false")
    body = "\n".join(lines)
    # RECIPE_TYPES: daftar tipe yang punya resep
    rec = ", ".join(f'"{t}"' for t in sorted(registry))
    const = f"const RECIPE_TYPES := {{}}\nconst RECIPE_LIST := [{rec}]\n"
    # versi Dictionary lebih hemat: pakai Dictionary<string,bool>
    d = "const RECIPE_TYPES := {\n"
    for t in sorted(registry):
        d += f'\t"{t}": true,\n'
    d += "}"
    return d + "\n\n" + body, len(registry)


def starter_entry(em, classes):
    """cast_/update_timers/init_state dispatcher per hero_type."""
    lines = []
    lines.append("## Entry point setara Hero.cast_skill delegasi: pilih kelas")
    lines.append("## per hero_type (6 starter), selainnya BossHeroSkills.")
    lines.append("static func hero_kind(h) -> String:")
    lines.append("\tmatch str(h.hero_type):")
    for s in STARTERS:
        lines.append(f'\t\t"{s}":')
        lines.append(f'\t\t\treturn "{s}"')
    lines.append('\t\t_:')
    lines.append('\t\t\treturn "boss"')
    return "\n".join(lines)


def key_entry(em, classes):
    per = {"q": "cast_q", "w": "cast_w", "e": "cast_e", "r": "cast_r"}
    out = []
    for key, meth in per.items():
        out.append(f"## {key.upper()} — delegasi cast_{key} kelas handler "
                   f"persis Hero.cast_skill pygame.")
        out.append(f"static func cast_{key}(h, all_units, all_towers, all_bases) -> bool:")
        out.append(f"\tmatch hero_kind(h):")
        for s in STARTERS:
            cls = f"{s.capitalize()}Skills"
            fn = em.fname(cls, meth)
            out.append(f'\t\t"{s}":')
            out.append(f"\t\t\treturn {fn}(h, all_units, all_towers, all_bases)")
        out.append('\t\t_:')
        out.append(f'\t\t\treturn __boss_generic(h, "{key}", all_units, all_towers, all_bases)')
        out.append("")
    out.append("static func update_timers(h, all_units, all_towers, all_bases) -> void:")
    out.append("\tmatch hero_kind(h):")
    for s in STARTERS:
        cls = f"{s.capitalize()}Skills"
        out.append(f'\t\t"{s}":')
        out.append(f"\t\t\t{em.fname(cls, 'update_timers')}(h, all_units, all_towers, all_bases)")
    out.append('\t\t"boss":')
    out.append(f"\t\t\t{em.fname('BossHeroSkills', 'update_timers')}(h, all_units, all_towers, all_bases)")
    out.append("\t\t_:")
    out.append("\t\t\tpass")
    out.append("")
    out.append("static func init_state(h) -> void:")
    out.append("\th.kit = {}")
    out.append("\tmatch hero_kind(h):")
    for s in STARTERS:
        cls = f"{s.capitalize()}Skills"
        out.append(f'\t\t"{s}":')
        out.append(f"\t\t\t{em.fname(cls, 'init_state')}(h)")
    out.append('\t\t"boss":')
    out.append(f"\t\t\t{em.fname('BossHeroSkills', 'init_state')}(h)")
    out.append("\treturn h.kit")
    return "\n".join(out)


def collect_state_keys(em, classes):
    """Inventaris semua h.<attr> non-inti yang ditulis kit (untuk CHECK)."""
    keys = set()
    for cn, cls in classes.items():
        for mname, fn in cls["methods"].items():
            for n in ast.walk(fn):
                if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) \
                        and n.value.id == "h" and n.attr not in KIT_NEVER \
                        and n.attr not in ("alive", "projectiles", "items", "range"):
                    keys.add(n.attr)
    return keys


def emit_all():
    classes = load_bundle()
    # VALIDASI: __has_target di header mengasumsikan REQUIRE_TARGET True di
    # SEMUA kelas. Kalau pygame menambah override, generator harus berhenti.
    for cn, cls in classes.items():
        if "REQUIRE_TARGET" in cls["consts"]:
            val = ast.literal_eval(cls["consts"]["REQUIRE_TARGET"].value)
            if val is not True:
                raise TranspileError(
                    f"{cn}.REQUIRE_TARGET={val} — perbarui __has_target generator")
    boss_cls = classes["BossHeroSkills"]
    registry = registry_of(boss_cls)
    vis, dflt = visual_durations(classes)
    bvis = ast.literal_eval(boss_cls["consts"]["BOSS_HERO_VISUAL_DURATION"].value)
    em = Emitter(classes, registry, {k.replace("Skills", "").lower(): v for k, v in vis.items()},
                 dflt, bvis)

    body = []
    # BaseSkill internal yang dipanggil sebagai helper static
    for mname in ("_acquire_target", "_has_target", "_skill_range",
                  "_get_enemies_in_range", "_deal_aoe_damage"):
        pass  # ditangani emitter tulis-tangan di HEADER (memuat pola non-literal)
    skip_common = {"cast_q", "cast_w", "cast_e", "cast_r"}

    for cn, cls in classes.items():
        if cn == "BaseSkill":
            # update_timers/init_state base = pass — tidak dipancarkan.
            continue
        for mname, fn in sorted(cls["methods"].items(), key=lambda kv: kv[1].lineno):
            if mname == "__init__":
                continue
            skip = set()
            if cn == "BossHeroSkills":
                skip = {"_generic_cast", "_fallback_cast", "cooldown_check",
                        "cooldown_trigger", "_get_visual_duration"}
            # cast_q..cast_r BossHeroSkills = pembungkus _generic_cast — diganti
            # __boss_generic; starter cast_q dst TETAP ditranspile (punya logika).
            if cn == "BossHeroSkills" and mname in skip_common:
                continue
            if mname in skip:
                continue
            body.append(em.emit_func(cn, fn))

    dispatch, n_recipes = dispatch_and_funcs(em, registry, boss_cls)

    parts = []
    parts.append(HEADER)
    parts.append(GENERIC_CAST)
    parts.append(dispatch)
    parts.append(starter_entry(em, classes))
    parts.append(key_entry(em, classes))
    parts.append("\n\n\n".join(body))
    text = "\n\n\n".join(p for p in parts if p)

    vis_const = "const DEFAULT_VISUAL_DURATION := " + repr(
        {k: int(v) for k, v in dflt.items()}).replace("'", '"') + "\n"
    vmap = "const VISUAL_DURATION := {\n"
    for kind, d in sorted({k.replace("Skills", "").lower(): v for k, v in vis.items()}.items()):
        vmap += f'\t"{kind}": ' + repr({kk: int(vv) for kk, vv in d.items()}).replace("'", '"') + ",\n"
    vmap += "}"
    bvis_c = "const BOSS_HERO_VISUAL_DURATION := " + repr(
        {k: {kk: int(vv) for kk, vv in v.items()} for k, v in bvis.items()}).replace("'", '"')

    # sanity: semua state keys harus lewat kit (tidak menabrak var Hero.gd)
    state_keys = collect_state_keys(em, classes)
    warn = "\n".join(f"## STATE-KEY {k}" for k in sorted(state_keys))

    header_txt = """# HeroSkillKit.gd — DIHASILKAN OTOMATIS. JANGAN EDIT TANGAN.
#
# Sumber: hero_skills/_bundle.py (BaseSkill helper + 6 starter skill class +
# BossHeroSkills: init_state/update_timers/_SKILL_REGISTRY/_cast_*/_fallback_cast),
# ditranspile 1:1 oleh tools/gen_hero_skill_kit.py. Regenerasi:
#
#     python tools/gen_hero_skill_kit.py
#
# Semua fungsi STATIC dan menerima `h` = node Hero (Hero.gd). State kustom
# handler hidup di `h.kit` (Dictionary, key = nama atribut pygame persis);
# cooldown frame (skill_timer/w/e/r), active_skill(+timer), stat hero, dan
# jembatan combat ada di Hero.gd. SATUAN TIMER = FRAME seperti pygame —
# Hero.gd men-decrement-nya dalam urutan Hero.update.
#
# Jembatan yang disediakan Hero.gd (persis pola BossKit.gd):
#   h.kit_enemies(units,towers,bases)     — saring tim+alive (BaseSkill)
#   h.kit_skill_damage()                  — mirror property skill_damage pygame
#                                           (int(round) berantai amp + skill_down)
#   h.kit_catalog_all()                   — salinan heroes.json (get_all_hero_types)
#   h.kit_hit(e, dmg, team, src, school)  — take_damage dengan kwargs persis
#   h.kit_slow / kit_lock / kit_atk_timer / kit_unit_alive / kit_has_slow
#   h.kit_shake / kit_sound / kit_popup / kit_skill_proj(target)
#   h.kit_fx_cast / kit_fx_impact         — pengganti blok try/notify FX pygame
#
# Regresi dijaga godot/tests/HeroSkillParityTest.tscn vs oracle Pygame
# (tools/test_godot_match_parity.py seksi hero_skills).
extends RefCounted

const __PI := 3.141592653589793

"""
    tail_vars = f"""
{vis_const}
{vmap}
{bvis_c}
"""
    text = header_txt + tail_vars + "\n" + text
    return text, state_keys, len(registry)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text, keys, nreg = emit_all()
    if args.check:
        old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if old != text:
            print("HeroSkillKit.gd basi — jalankan tools/gen_hero_skill_kit.py")
            sys.exit(1)
        print("[gen_hero_skill_kit] PASS: file ter-commit == hasil transpile")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"[gen_hero_skill_kit] {OUT.relative_to(ROOT)}: "
          f"{text.count(chr(10))} baris, {text.count('static func')} fungsi, "
          f"{nreg} resep registry, {len(keys)} key state kit")


if __name__ == "__main__":
    main()
