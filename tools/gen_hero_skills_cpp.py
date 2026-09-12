#!/usr/bin/env python3
"""
Generate C++ GDExtension for hero_skills from _bundle.py
Paritas 1:1 dengan gen_hero_skill_kit.py tapi output C++ (godot-cpp)
"""
import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "hero_skills" / "_bundle.py"
OUT_H = ROOT / "godot" / "gdext" / "mystic_skills" / "src" / "hero_skills_processor.h"
OUT_CPP = ROOT / "godot" / "gdext" / "mystic_skills" / "src" / "hero_skills_processor.cpp"

STARTERS = ["grimjaw", "kaizen", "sylara", "thorne", "vex", "zephyr"]

HERO_READ = {
    "x": "get_global_pos_x({r})",
    "y": "get_global_pos_y({r})",
    "hp": "get_hp({r})",
    "max_hp": "get_max_hp({r})",
    "damage": "get_damage({r})",
    "team": "get_team({r})",
    "target": "get_target({r})",
    "facing": "get_facing({r})",
    "hero_type": "get_hero_type({r})",
    "level": "get_level({r})",
    "base_damage": "get_base_damage({r})",
    "skill_range": "get_skill_range({r})",
    "skill_data": "get_skill_data({r})",
    "dmg_school": "get_dmg_school({r})",
    "active_skill": "get_active_skill({r})",
    "active_skill_timer": "get_active_skill_timer({r})",
    "skill_timer": "get_skill_timer({r})",
    "w_cooldown": "get_w_cooldown({r})",
    "e_cooldown": "get_e_cooldown({r})",
    "r_cooldown": "get_r_cooldown({r})",
    "skill_cooldown_max": "get_skill_cooldown_max({r})",
    "w_cooldown_max": "get_w_cooldown_max({r})",
    "e_cooldown_max": "get_e_cooldown_max({r})",
    "r_cooldown_max": "get_r_cooldown_max({r})",
    "skill_damage": "kit_skill_damage({r})",
    "speed": "get_speed_frames({r})",
    "attack_cooldown": "get_attack_cooldown_frames({r})",
}

## Properti Hero.gd yang setter-nya numerik (x/y/hp/damage/...). "target" dan
## "active_skill" sengaja di luar: nilainya Object*/String.
NUMERIC_WRITES = {
    "x", "y", "hp", "max_hp", "damage", "base_damage", "level", "facing",
    "active_skill_timer", "skill_timer", "w_cooldown", "e_cooldown",
    "r_cooldown", "speed", "attack_cooldown",
}

HERO_WRITE = {
    "x": "set_global_pos_x({r}, {v})",
    "y": "set_global_pos_y({r}, {v})",
    "hp": "set_hp({r}, {v})",
    "max_hp": "set_max_hp({r}, {v})",
    "damage": "set_damage({r}, {v})",
    "target": "set_target({r}, {v})",
    "facing": "set_facing({r}, {v})",
    "level": "set_level({r}, {v})",
    "base_damage": "set_base_damage({r}, {v})",
    "active_skill": "set_active_skill({r}, {v})",
    "active_skill_timer": "set_active_skill_timer({r}, {v})",
    "skill_timer": "set_skill_timer({r}, {v})",
    "w_cooldown": "set_w_cooldown({r}, {v})",
    "e_cooldown": "set_e_cooldown({r}, {v})",
    "r_cooldown": "set_r_cooldown({r}, {v})",
    "speed": "set_speed_frames({r}, {v})",
    "attack_cooldown": "set_attack_cooldown_frames({r}, {v})",
}

def load_bundle():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    classes = {}
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            if n.name.startswith("_NS_"):
                for m in n.body:
                    if isinstance(m, ast.ClassDef):
                        methods = {f.name: f for f in m.body if isinstance(f, ast.FunctionDef)}
                        consts = {}
                        for s in m.body:
                            if isinstance(s, ast.Assign) and len(s.targets)==1 and isinstance(s.targets[0], ast.Name):
                                consts[s.targets[0].id] = s
                        classes[m.name] = {"node": m, "methods": methods, "consts": consts}
            else:
                methods = {f.name: f for f in n.body if isinstance(f, ast.FunctionDef)}
                consts = {}
                for s in n.body:
                    if isinstance(s, ast.Assign) and len(s.targets)==1 and isinstance(s.targets[0], ast.Name):
                        consts[s.targets[0].id] = s
                classes[n.name] = {"node": n, "methods": methods, "consts": consts}
    return classes

def registry_of(boss_cls):
    node = boss_cls["consts"]["_SKILL_REGISTRY"]
    return ast.literal_eval(node.value)

def visual_durations(classes):
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

class CppEmitter:
    def __init__(self, classes, registry, vis, dflt, boss_vis):
        self.classes = classes
        self.registry = registry
        self.vis = vis
        self.dflt = dflt
        self.boss_vis = boss_vis
        self.aliases = {}
        for cn in classes:
            self.aliases[cn] = cn.replace("Skills","").lower()
        self.cur_class = "BaseSkill"
        self.kind = "boss"

    def fname(self, cls_name, mname):
        # e.g. GrimjawSkills.cast_q -> grimjaw_cast_q
        alias = self.aliases.get(cls_name, cls_name.lower())
        clean = mname.lstrip("_")
        return f"{alias}_{clean}"

    # ── Konversi numerik AMAN dari Variant ────────────────────────────────
    # Variant::operator double() godot-cpp memanggil to_type_constructor[FLOAT]
    # ke buffer `double result;` yang TIDAK DIINISIALISASI: kalau sumber bukan
    # tipe numerik (mis. NIL karena key Dictionary tidak ada), constructor gagal
    # dan buffer dibiarkan apa adanya -> angka acak dari stack (terbukti di CI:
    # base_damage jadi 100.0 = sisa skill_range, damage buff 186 -> 150).
    # var_num()/var_int() deterministik dan cocok dengan GDScript (null -> 0).
    def _is_variant_expr(self, x):
        t = x.strip()
        if "get_kit_value" in t or "dict_at" in t or "py_or" in t:
            return True
        return t in getattr(self, "_current_locals_set", set())

    def num_cast(self, x):
        t = x.strip()
        for pre in ("(double)(", "(int)(", "(int64_t)(", "var_num(", "var_int("):
            if t.startswith(pre):
                return t
        try:
            float(t)
            return t
        except Exception:
            pass
        if self._is_variant_expr(t):
            return f"var_num({t})"
        return f"(double)({t})"

    def int_cast(self, x):
        t = x.strip()
        for pre in ("(int64_t)(", "(int)(", "var_int("):
            if t.startswith(pre):
                return t
        try:
            float(t)
            return f"(int64_t)({t})"
        except Exception:
            pass
        if self._is_variant_expr(t):
            return f"var_int({t})"
        return f"(int64_t)({t})"

    def expr(self, node, method):
        if isinstance(node, ast.Constant):
            v = node.value
            if v is True:
                return "true"
            if v is False:
                return "false"
            if v is None:
                return "Variant()"
            if isinstance(v, int):
                return str(v)
            if isinstance(v, float):
                return f"{v}"
            if isinstance(v, str):
                # escape
                esc = v.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{esc}"'
            raise Exception(f"const unsupported {v!r}")

        if isinstance(node, ast.Name):
            if node.id == "HERO_TYPES":
                return "kit_catalog_all(h)"
            if node.id == "HERO_LEVELS":
                return "kit_hero_levels(h)"
            if node.id == "math":
                return "Math"
            return node.id

        if isinstance(node, ast.Attribute):
            return self.attr_expr(node, method)

        if isinstance(node, ast.Call):
            return self.call(node, method)

        if isinstance(node, ast.BinOp):
            a = self.expr(node.left, method)
            b = self.expr(node.right, method)
            # Always cast to double for arithmetic to avoid Variant ambiguity
            # Except for cases where both are clearly numeric literals or known double-returning funcs, we still cast to be safe
            def _d(x):
                return self.num_cast(x)
            a_d = _d(a)
            b_d = _d(b)
            if isinstance(node.op, ast.Add):
                return f"({a_d} + {b_d})"
            if isinstance(node.op, ast.Sub):
                return f"({a_d} - {b_d})"
            if isinstance(node.op, ast.Mult):
                return f"({a_d} * {b_d})"
            if isinstance(node.op, ast.Div):
                return f"({a_d} / {b_d})"
            if isinstance(node.op, ast.FloorDiv):
                return f"(int64_t)({a_d} / {b_d})"
            if isinstance(node.op, ast.Mod):
                return f"Math::fmod({self.num_cast(a)}, {self.num_cast(b)})"
            raise Exception(f"binop {type(node.op)}")

        if isinstance(node, ast.UnaryOp):
            v = self.expr(node.operand, method)
            if isinstance(node.op, ast.Not):
                return f"!({v})"
            if isinstance(node.op, ast.USub):
                # cast Variant to double for unary minus
                if self._is_variant_expr(v):
                    return f"-({self.num_cast(v)})"
                return f"-({v})"
            raise Exception("unary")

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return " && ".join(f"({self.expr(v, method)})" for v in node.values)
            # or -> __py_or chain
            acc = self.expr(node.values[-1], method)
            for v in reversed(node.values[:-1]):
                acc = f"py_or({self.expr(v, method)}, {acc})"
            return acc

        if isinstance(node, ast.Compare):
            has_in = any(isinstance(o, (ast.In, ast.NotIn)) for o in node.ops)
            if has_in:
                return self.in_compare(node, method)
            parts = []
            lhs = node.left
            op_map = {ast.Eq: "==", ast.NotEq: "!=", ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Is: "==", ast.IsNot: "!="}
            for op, rhs in zip(node.ops, node.comparators):
                if type(op) not in op_map:
                    raise Exception(f"compare {type(op)}")
                left_expr = self.expr(lhs, method)
                right_expr = self.expr(rhs, method)
                if isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    def _cd(x):
                        return self.num_cast(x)
                    left_expr = _cd(left_expr)
                    right_expr = _cd(right_expr)
                elif isinstance(op, (ast.Eq, ast.NotEq, ast.Is, ast.IsNot)):
                    # If comparing kit values or Variant locals to int, cast
                    def _c_eq(x):
                        if "get_kit_value" in x:
                            # check if other side is int literal
                            other = right_expr if x==left_expr else left_expr
                            # if other is numeric literal, cast to int/double
                            if other.strip().lstrip("-").isdigit():
                                return self.int_cast(x)
                            # if other is 0, 1 etc, cast to int
                            try:
                                float(other)
                                return self.num_cast(x)
                            except:
                                pass
                        if x in getattr(self, "_current_locals_set", set()):
                            # local Variant compared to int -> cast
                            try:
                                float(right_expr if x==left_expr else left_expr)
                                return self.num_cast(x)
                            except:
                                pass
                        return x
                    # apply
                    left_expr = _c_eq(left_expr)
                    # right_expr similarly but need to check left
                    if "get_kit_value" in right_expr or right_expr in getattr(self, "_current_locals_set", set()):
                        try:
                            float(left_expr)
                            right_expr = self.num_cast(right_expr) if "." in left_expr or "double" in left_expr else self.int_cast(right_expr)
                        except:
                            pass
                parts.append(f"({left_expr} {op_map[type(op)]} {right_expr})")
                lhs = rhs
            return " && ".join(parts)

        if isinstance(node, ast.IfExp):
            return f"({self.expr(node.test, method)} ? {self.expr(node.body, method)} : {self.expr(node.orelse, method)})"

        if isinstance(node, (ast.List, ast.Tuple)):
            els = [self.expr(e, method) for e in node.elts]
            if not els:
                return "Array()"
            # Use make_array helper for 1-4 elements, otherwise build via Array
            if len(els)==1:
                return f"make_array({els[0]})"
            if len(els)==2:
                return f"make_array({els[0]}, {els[1]})"
            if len(els)==3:
                return f"make_array({els[0]}, {els[1]}, {els[2]})"
            if len(els)==4:
                return f"make_array({els[0]}, {els[1]}, {els[2]}, {els[3]})"
            # for more, create Array and append
            # We'll generate via lambda: ([](){ Array a; a.append(...); return a; }())
            inner = "; ".join(f"a.append({e})" for e in els)
            return f"[](){{ Array a; {inner}; return a; }}()"

        if isinstance(node, ast.Dict):
            # generate Dictionary
            items = []
            for k, v in zip(node.keys, node.values):
                items.append(f"{self.expr(k, method)}, {self.expr(v, method)}")
            if not items:
                return "Dictionary()"
            # We'll create dict via helper: make_dict
            # For simplicity, generate Dictionary with set
            # We'll emit as: [] but we need builder
            # We'll use lambda: Dictionary d; d[k]=v;
            # For inline, we can use Dictionary::make? In godot-cpp, Dictionary doesn't have make like Array.
            # We'll generate via helper function dict_make
            # For now, return Dictionary() and handle via statement generation?
            # We'll produce a helper call: create_dict(...)
            # Simpler: we generate Array of pairs and then convert, but let's just emit Dictionary()
            # and we will handle dict literals in statement context separately.
            # For expression context, we need actual dict.
            # We'll generate as Dictionary() and then set via temp variable in stmt.
            # For now, return "Dictionary()" and let caller handle?
            # We'll actually generate via helper: Dictionary({{k:v}})
            # We'll use a helper function make_dict that we define.
            # Let's emit make_dict helper.
            pairs = ", ".join(f"{self.expr(k, method)}, {self.expr(v, method)}" for k, v in zip(node.keys, node.values))
            return f"make_dict({pairs})"

        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name) and node.value.value.id=="h" and node.value.attr=="kit":
                sl = node.slice
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                    return f'get_kit_value(h, "{sl.value}")'
                idx = self.expr(sl, method)
                return f'get_kit_value(h, {idx})'
            v = self.expr(node.value, method)
            sl = node.slice
            # If v is Variant holding Array/Dictionary, cast to appropriate type for indexing
            is_variant_array = "get_kit_value" in v or "py_or" in v or v in getattr(self, "_current_locals_set", set())
            # Kontainer Dictionary dari helper: JANGAN pakai operator[] (non-const,
            # ptrw/detach COW + menyisipkan NIL kalau key tidak ada, dan berantai
            # pada temporary menghasilkan Variant kosong). dict_at() = .get() const.
            is_dict_expr = (v.strip().startswith("dict_at(")
                            or any(v.strip().startswith(pre) for pre in
                                   ("kit_catalog_all(", "kit_hero_levels(", "get_skill_data(", "make_dict(")))
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                if is_variant_array or is_dict_expr:
                    return f'dict_at({v}, "{sl.value}")'
                return f'{v}["{sl.value}"]'
            idx = self.expr(sl, method)
            if is_dict_expr and not v.strip().startswith("dict_at(") is False:
                pass
            if v.strip().startswith("dict_at(") or (is_dict_expr and not is_variant_array):
                return f"dict_at({v}, {idx})"
            if is_variant_array:
                # assume Array indexing
                return f'((Array)({v}))[{idx}]'
            return f"{v}[{idx}]"

        if isinstance(node, ast.Set):
            return "Dictionary()"

        raise Exception(f"expr unsupported {type(node).__name__} {ast.dump(node)[:200]}")

    def in_compare(self, node, method):
        out = []
        lhs = node.left
        for op, rhs in zip(node.ops, node.comparators):
            neg = isinstance(op, ast.NotIn)
            if not isinstance(op, (ast.In, ast.NotIn)):
                raise Exception("mixed in compare")
            if isinstance(lhs, ast.Call) and isinstance(lhs.func, ast.Name) and lhs.func.id == "id":
                arg = self.expr(lhs.args[0], method)
                recv = self.expr(rhs, method)
                # recv is Dictionary (hit_enemies) -> has
                out.append(f"!{recv}.has({arg})" if neg else f"{recv}.has({arg})")
            else:
                l = self.expr(lhs, method)
                r = self.expr(rhs, method)
                # For skill_key in ('q','w') etc: r is Array, check has
                # We can generate: Array.has? In godot-cpp, Array has method has?
                # We'll use: r.has(l) or custom helper in_array
                if isinstance(rhs, (ast.Tuple, ast.List)):
                    # rhs is literal tuple/list of strings
                    vals = [self.expr(e, method) for e in rhs.elts]
                    conds = " || ".join(f"({l} == {v})" for v in vals)
                    if neg:
                        conds = f"!({conds})"
                    out.append(f"({conds})")
                else:
                    out.append(f"!in_array({r}, {l})" if neg else f"in_array({r}, {l})")
            lhs = rhs
        return " && ".join(out)

    def attr_expr(self, node, method):
        # self.hero -> h
        if isinstance(node.value, ast.Name) and node.value.id == "self" and node.attr == "hero":
            return "h"
        # self.hero.<x> -> h.<x>
        if isinstance(node.value, ast.Attribute) and node.value.attr == "hero" and isinstance(node.value.value, ast.Name) and node.value.value.id == "self":
            node = ast.Attribute(value=ast.Name(id="h"), attr=node.attr, ctx=node.ctx)
        if isinstance(node.value, ast.Name) and node.value.id == "h":
            return self.hero_read(node.attr, method)
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            consts = self.classes[self.cur_class]["consts"]
            if node.attr in consts:
                return self.const_expr(node.attr, method)
            raise Exception(f"self.{node.attr} not const")
        if isinstance(node.value, ast.Name) and node.value.id == "math":
            if node.attr == "pi":
                return "Math_PI"
            return f"Math::{node.attr}"
        if node.attr in ("x", "y"):
            recv = self.expr(node.value, method)
            if node.attr == "x":
                return f"get_global_pos_x({recv})"
            else:
                return f"get_global_pos_y({recv})"
        if node.attr == "alive":
            recv = self.expr(node.value, method)
            return f"kit_unit_alive(h, {recv})"
        if node.attr == "attack_timer":
            recv = self.expr(node.value, method)
            return f"kit_atk_timer(h, {recv})"
        if node.attr in ("hp", "max_hp", "team", "speed", "attack_cooldown", "facing", "hero_type", "level", "base_damage", "skill_range", "skill_data", "dmg_school", "active_skill", "active_skill_timer", "skill_timer", "w_cooldown", "e_cooldown", "r_cooldown", "skill_cooldown_max", "w_cooldown_max", "e_cooldown_max", "r_cooldown_max", "damage"):
            recv = self.expr(node.value, method)
            # map to getter
            if node.attr == "hp":
                return f"get_hp({recv})"
            if node.attr == "max_hp":
                return f"get_max_hp({recv})"
            if node.attr == "team":
                return f"get_team({recv})"
            if node.attr == "damage":
                return f"get_damage({recv})"
            if node.attr == "facing":
                return f"get_facing({recv})"
            if node.attr == "hero_type":
                return f"get_hero_type({recv})"
            if node.attr == "level":
                return f"get_level({recv})"
            if node.attr == "base_damage":
                return f"get_base_damage({recv})"
            if node.attr == "skill_range":
                return f"get_skill_range({recv})"
            if node.attr == "skill_data":
                return f"get_skill_data({recv})"
            if node.attr == "dmg_school":
                return f"get_dmg_school({recv})"
            if node.attr == "active_skill":
                return f"get_active_skill({recv})"
            if node.attr == "active_skill_timer":
                return f"get_active_skill_timer({recv})"
            if node.attr == "skill_timer":
                return f"get_skill_timer({recv})"
            if node.attr == "w_cooldown":
                return f"get_w_cooldown({recv})"
            if node.attr == "e_cooldown":
                return f"get_e_cooldown({recv})"
            if node.attr == "r_cooldown":
                return f"get_r_cooldown({recv})"
            if node.attr == "speed":
                return f"get_speed_frames({recv})"
            if node.attr == "attack_cooldown":
                return f"get_attack_cooldown_frames({recv})"
        # generic
        recv = self.expr(node.value, method)
        return f"{recv}.get(\"{node.attr}\")"

    def hero_read(self, attr, method):
        if attr in HERO_READ:
            return HERO_READ[attr].format(r="h")
        if attr == "alive":
            return "is_alive(h)"
        if attr == "projectiles":
            raise Exception("h.projectiles not emitted")
        if attr == "items":
            raise Exception("h.items only via wrapper")
        # kit dict access
        return f'get_kit_value(h, "{attr}")'

    def const_expr(self, name, method):
        consts = self.classes[self.cur_class]["consts"]
        node = consts[name]
        return self.expr(node.value, method)

    def call(self, node, method):
        fn = node.func
        if isinstance(fn, ast.Name):
            if fn.id == "getattr":
                return self.getattr_call(node, method)
            if fn.id == "hasattr":
                return self.hasattr_call(node, method)
            if fn.id == "min":
                args = [self.num_cast(self.expr(a, method)) for a in node.args]
                if len(args)==2:
                    return f"MIN({', '.join(args)})"
                return f"min_n({', '.join(args)})"
            if fn.id == "max":
                args = [self.num_cast(self.expr(a, method)) for a in node.args]
                if len(args)==2:
                    return f"MAX({', '.join(args)})"
                return f"max_n({', '.join(args)})"
            if fn.id == "int":
                return self.int_cast(self.expr(node.args[0], method))
            if fn.id == "float":
                return self.num_cast(self.expr(node.args[0], method))
            if fn.id == "abs":
                return f"Math::abs({self.num_cast(self.expr(node.args[0], method))})"
            if fn.id == "len":
                return f"(int64_t)({self.expr(node.args[0], method)}.size())"
            if fn.id == "set":
                return "Dictionary()"
            if fn.id == "range":
                # range(n) -> for loop handling elsewhere, but expr: generate Array from 0..n-1
                if len(node.args)==1:
                    return f"range_array({self.expr(node.args[0], method)})"
                else:
                    raise Exception("range with 2 args not supported in expr")
            if fn.id == "id":
                return self.expr(node.args[0], method)
            if fn.id == "sorted":
                return f"{self.expr(node.args[0], method)}.duplicate()"
            if fn.id == "get_all_hero_types":
                return "kit_catalog_all(h)"
            if fn.id == "print":
                args = ", ".join(self.expr(a, method) for a in node.args)
                return f"UtilityFunctions::print({args})"
            raise Exception(f"global call {fn.id}")

        if not isinstance(fn, ast.Attribute):
            raise Exception("call not attribute")

        # math.*
        if isinstance(fn.value, ast.Name) and fn.value.id == "math":
            if fn.attr == "hypot":
                a = self.expr(node.args[0], method)
                b = self.expr(node.args[1], method)
                return f"Vector2({a}, {b}).length()"
            if fn.attr in ("cos", "sin", "atan2", "sqrt", "pow", "floor", "ceil"):
                args = ", ".join(self.num_cast(self.expr(a, method)) for a in node.args)
                return f"Math::{fn.attr}({args})"
            if fn.attr == "pi":
                return "Math_PI"

        if fn.attr == "take_damage":
            recv = self.expr(fn.value, method)
            if len(node.args)!=2:
                raise Exception("take_damage 2 args")
            src = "Variant()"
            school = '""'
            for kw in node.keywords:
                if kw.arg == "source":
                    src = self.expr(kw.value, method)
                elif kw.arg == "school":
                    school = self.expr(kw.value, method)
            return f"kit_hit(h, {recv}, {self.int_cast(self.expr(node.args[0], method))}, get_team(h), {src}, {school})"

        if fn.attr == "apply_slow":
            recv = self.expr(fn.value, method)
            return f"kit_slow(h, {recv}, {self.expr(node.args[0], method)}, {self.expr(node.args[1], method)})"

        if isinstance(fn.value, ast.Name) and fn.value.id == "self":
            return self.self_call(fn.attr, node, method)

        recv = self.expr(fn.value, method)
        if fn.attr == "_spawn_skill_projectile":
            speed = "13.0"
            for k in node.keywords:
                if k.arg == "speed":
                    speed = self.expr(k.value, method)
            if len(node.args)>1:
                speed = self.expr(node.args[1], method)
            return f"kit_skill_proj(h, {self.expr(node.args[0], method)}, {speed})"
        if fn.attr == "append":
            return f"{recv}.append({self.expr(node.args[0], method)})"
        if fn.attr == "get":
            exprs = [self.expr(a, method) for a in node.args]
            if len(exprs)>=1:
                exprs[0] = f"Variant({exprs[0]})"
            if len(exprs)==1:
                exprs.append("Variant()")
            return f"{recv}.get({', '.join(exprs)})"
        if fn.attr == "add":
            return f"{recv}[Variant({self.expr(node.args[0], method)})] = true"
        if fn.attr == "sort":
            if node.keywords and node.keywords[0].arg == "key":
                return f"{recv}.sort_custom(Callable()) /* sorted by pair0 - handled */"
            raise Exception("sort without key")
        if fn.attr == "play":
            vol = "0.7"
            for kw in node.keywords:
                if kw.arg == "volume_mult":
                    vol = self.expr(kw.value, method)
            return f"kit_sound(h, {vol})"
        if fn.attr in ("notify_skill_cast", "notify_skill_impact"):
            return self.fx_call(fn.attr, node, method)
        if fn.attr == "shake_screen":
            return f"kit_shake(h, {self.expr(node.args[0], method)})"
        if fn.attr == "add_damage_number":
            txt = self.expr(node.args[2], method)
            crit = "false"
            for kw in node.keywords:
                if kw.arg == "is_critical":
                    crit = self.expr(kw.value, method)
            return f"kit_popup(h, {txt}, {crit})"
        # generic method call
        args = ", ".join(self.expr(a, method) for a in node.args)
        return f"{recv}.call(\"{fn.attr}\", {args})" if args else f"{recv}.call(\"{fn.attr}\")"

    def fx_call(self, kind, node, method):
        a = [self.expr(x, method) for x in node.args]
        if kind == "notify_skill_cast":
            return f"kit_fx_cast(h, {a[1]})"
        x = a[1]; y = a[2]
        r = "0.0"; k = '"q"'
        if len(a)>=4:
            r = a[3]
        if len(a)>=5:
            k = a[4]
        for kw in node.keywords:
            if kw.arg == "radius":
                r = self.expr(kw.value, method)
            elif kw.arg == "skill":
                k = self.expr(kw.value, method)
        return f"kit_fx_impact(h, {x}, {y}, {r}, {k})"

    def getattr_call(self, node, method):
        args = node.args
        if len(args)<2:
            raise Exception("getattr")
        if isinstance(args[0], ast.Attribute) and args[0].attr=="hero" and isinstance(args[0].value, ast.Name) and args[0].value.id=="self":
            args = [ast.Name(id="h")] + list(args[1:])
        base = args[0]
        name_node = args[1]
        default = self.expr(args[2], method) if len(args)==3 else "Variant()"
        if isinstance(name_node, ast.Constant):
            name = name_node.value
            if isinstance(base, ast.Name) and base.id=="h":
                if name=="range":
                    return "get_attack_range(h)"
                if name=="alive":
                    return "is_alive(h)"
                if name in HERO_READ:
                    return HERO_READ[name].format(r="h")
                return f'get_kit_value(h, "{name}", {default})'
            recv = self.expr(base, method)
            if name=="alive":
                return f"kit_unit_alive(h, {recv})"
            if name=="attack_timer":
                return f"kit_atk_timer(h, {recv})"
            return f'{recv}.get("{name}", {default})'
        raise Exception("getattr nonliteral")

    def hasattr_call(self, node, method):
        args = node.args
        if len(args)!=2 or not isinstance(args[1], ast.Constant):
            raise Exception("hasattr nonliteral")
        recv = self.expr(args[0], method)
        key = args[1].value
        if key=="apply_slow":
            return f"kit_has_slow(h, {recv})"
        if key=="attack_timer":
            return f"kit_has_atk_timer(h, {recv})"
        if key=="hp":
            return f"kit_has_hp(h, {recv})"
        if key=="game_instance":
            return "false"
        raise Exception(f"hasattr {key}")

    def self_call(self, attr, node, method):
        args = [self.expr(a, method) for a in node.args]
        kw = {k.arg: self.expr(k.value, method) for k in node.keywords}
        if attr=="_check_q_cooldown":
            return "get_skill_timer(h) <= 0"
        if attr=="_check_w_cooldown":
            return "get_w_cooldown(h) <= 0"
        if attr=="_check_e_cooldown":
            return "get_e_cooldown(h) <= 0"
        if attr=="_check_r_cooldown":
            return "get_r_cooldown(h) <= 0"
        if attr=="_get_enemies":
            return f"kit_enemies(h, {', '.join(args)})"
        layout = {
            "_get_enemies_in_range": ("enemies_in_range", 'h', ["all_units","all_towers","all_bases","range_val","center_x","center_y"], {"center_x":"Variant()","center_y":"Variant()"}),
            "_deal_aoe_damage": ("deal_aoe", 'h', ["all_units","all_towers","all_bases","range_val","damage_multiplier"], {"range_val":"0.0","damage_multiplier":"1.0"}),
            "_acquire_target": ("acquire_target", 'h', ["all_units","all_towers","all_bases","range_val"], {"range_val":"Variant()"}),
            "_has_target": ("has_target", 'h', ["all_units","all_towers","all_bases","range_val"], {"range_val":"Variant()"}),
            "_skill_range": ("skill_range", 'h', ["fallback"], {"fallback":"200.0"}),
            "_set_active_skill": ("set_active_skill", 'h, "{kind}"', ["key","duration"], {"duration":"Variant()"}),
            "_trigger_q_cooldown": ("trigger_q", 'h, "{kind}"', ["shake_amount","visual_duration"], {"shake_amount":"8.0","visual_duration":"Variant()"}),
            "_trigger_w_cooldown": ("trigger_w", 'h, "{kind}"', ["shake_amount","visual_duration"], {"shake_amount":"5.0","visual_duration":"Variant()"}),
            "_trigger_e_cooldown": ("trigger_e", 'h, "{kind}"', ["shake_amount","visual_duration"], {"shake_amount":"6.0","visual_duration":"Variant()"}),
            "_trigger_r_cooldown": ("trigger_r", 'h, "{kind}"', ["shake_amount","visual_duration"], {"shake_amount":"15.0","visual_duration":"Variant()"}),
            "_get_visual_duration": ("visual_duration", '"{kind}", h', ["key"], {}),
        }
        if attr in layout:
            gname, prefix_t, order, defaults = layout[attr]
            slots = {}
            for pname, aval in zip(order, args):
                slots[pname]=aval
            for kname, kval in kw.items():
                slots[kname]=kval
            built=[]
            for slot_name in order:
                if slot_name in slots:
                    built.append(slots[slot_name])
                elif slot_name in defaults:
                    built.append(defaults[slot_name])
            prefix = prefix_t.replace("{kind}", self.kind)
            # for C++ we have functions with prefix already includes h
            if prefix.startswith('h,'):
                # gname already expects h as first? Let's construct
                # Our helpers are: skill_range(h, fallback) etc.
                # For set_active_skill we have set_active_skill(h, kind, key, duration)
                # So we need to handle prefix
                if "{kind}" in prefix_t:
                    kind_str = self.kind
                    # for visual_duration, prefix is '"{kind}", h' -> actually visual_duration(hero_type, key) but we have wrapper
                    # We'll simplify: call visual_duration with hero_type
                    if gname=="visual_duration":
                        return f"visual_duration_kind(\"{kind_str}\", get_hero_type(h), {', '.join(built)})"
                    # for set_active_skill etc, kind is second param
                    return f"{gname}({prefix}, {', '.join(built)})"
                else:
                    return f"{gname}({prefix}, {', '.join(built)})"
            else:
                # prefix is 'h' alone
                return f"{gname}({prefix}, {', '.join(built)})"
        if attr=="_apply_slow":
            return f"kit_slow(h, {args[0]}, {args[1]}, {args[2]})"
        if attr=="_apply_stun":
            return f"kit_lock(h, {args[0]}, {args[1]})"
        if attr=="_shake_screen":
            return f"kit_shake(h, {args[0]})"
        if attr=="_play_skill_sound":
            v = kw.get("volume", args[0] if args else "0.7")
            return f"kit_sound(h, {v})"
        if attr=="_add_popup":
            crit = kw.get("is_critical","false")
            return f"kit_popup(h, {args[2]}, {crit})"
        if attr=="_set_active_skill":
            dur = kw.get("duration", args[1] if len(args)>1 else "Variant()")
            return f'set_active_skill(h, "{self.kind}", {args[0]}, {dur})'
        if attr in ("_trigger_q_cooldown","_trigger_w_cooldown","_trigger_e_cooldown","_trigger_r_cooldown"):
            key = attr[len("_trigger_")]
            shake = kw.get("shake_amount", {"q":"8","w":"5","e":"6","r":"15"}[key])
            vd = kw.get("visual_duration","Variant()")
            return f"trigger_{key}(h, \"{self.kind}\", {shake}, {vd})"
        if attr=="_get_visual_duration":
            return f'visual_duration_kind("{self.kind}", get_hero_type(h), {args[0]})'
        if attr=="_spawn_skill_projectile":
            sp = kw.get("speed", args[1] if len(args)>1 else "13.0")
            return f"kit_skill_proj(h, {args[0]}, {sp})"
        if attr=="_generic_cast":
            return f"boss_generic(h, {args[0]}, {args[1]}, {args[2]}, {args[3]})"
        if attr=="_fallback_cast":
            return f"fallback_cast(h, {args[1]}, {args[2]})"  # args[0] is h already?
        # method milik kelas yang sama
        cls_methods = self.classes[self.cur_class]["methods"]
        if attr in cls_methods:
            params = [a.arg for a in cls_methods[attr].args.args if a.arg!="self"]
            takes_h = bool(params) and params[0]=="h"
            call_args = args if takes_h else (["h"]+args)
            return f"{self.fname(self.cur_class, attr)}({', '.join(call_args)})"
        raise Exception(f"self.{attr}() not recognized")

    def stmt(self, s, out, indent, method):
        pad = "    " * indent
        if isinstance(s, ast.Assign) and len(s.targets)==1 and isinstance(s.targets[0], ast.Name) and s.targets[0].id=="h" and isinstance(s.value, ast.Attribute) and s.value.attr=="hero" and isinstance(s.value.value, ast.Name) and s.value.value.id=="self":
            return
        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Constant):
                return
            out.append(pad + self.expr(s.value, method) + ";")
            return
        if isinstance(s, ast.Assign):
            if len(s.targets)==1 and isinstance(s.targets[0], (ast.Tuple, ast.List)):
                tgt_tuple = s.targets[0]
                if isinstance(s.value, (ast.Tuple, ast.List)) and len(tgt_tuple.elts)==len(s.value.elts):
                    for t,v in zip(tgt_tuple.elts, s.value.elts):
                        self.assign_one(t, self.expr(v, method), out, pad, method, s)
                    return
                val = self.expr(s.value, method)
                # For Variant holding Array, need to cast to Array for indexing
                val_array = f"((Array)({val}))" if ("get_kit_value" in val or "py_or" in val or "make_array" in val) else val
                for i, t in enumerate(tgt_tuple.elts):
                    if isinstance(t, ast.Name):
                        out.append(pad + f"{t.id} = {val_array}[{i}];")
                    else:
                        self.assign_one(t, f"{val_array}[{i}]", out, pad, method, s)
                return
            if len(s.targets)!=1:
                # multi-target assign (unlikely)
                if isinstance(s.targets[0], (ast.Tuple, ast.List)) and isinstance(s.value, (ast.Tuple, ast.List)) and len(s.targets[0].elts)==len(s.value.elts):
                    for t,v in zip(s.targets[0].elts, s.value.elts):
                        self.assign_one(t, self.expr(v, method), out, pad, method, s)
                    return
                if isinstance(s.targets[0], (ast.Tuple, ast.List)):
                    val = self.expr(s.value, method)
                    for i, t in enumerate(s.targets[0].elts):
                        if isinstance(t, ast.Name):
                            out.append(pad + f"{t.id} = {val}[{i}];")
                        else:
                            self.assign_one(t, f"{val}[{i}]", out, pad, method, s)
                    return
            tgt = s.targets[0]
            val = self.expr(s.value, method)
            self.assign_one(tgt, val, out, pad, method, s)
            return
        if isinstance(s, ast.AugAssign):
            val = self.expr(s.value, method)
            op_map = {ast.Add:"+", ast.Sub:"-", ast.Mult:"*", ast.Div:"/", ast.FloorDiv:"/", ast.Mod:"%"}
            op = op_map.get(type(s.op))
            if op is None:
                raise Exception("aug op")
            t = s.target
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id=="h":
                if t.attr in HERO_WRITE:
                    cur = self.hero_read(t.attr, method)
                    rhs = f"({cur}) / ({val})" if op=="/" else f"({cur}) {op} ({val})"
                    out.append(pad + HERO_WRITE[t.attr].format(r="h", v=rhs) + ";")
                    return
                out.append(pad + f'set_kit_value(h, "{t.attr}", var_int(get_kit_value(h, "{t.attr}")) {op} {self.int_cast(val)});')
                return
            if isinstance(t, ast.Subscript):
                # h.kit["key"] -= 1
                if isinstance(t.value, ast.Attribute) and isinstance(t.value.value, ast.Name) and t.value.value.id=="h" and t.value.attr=="kit":
                    sl = t.slice
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        key = sl.value
                        out.append(pad + f'set_kit_value(h, "{key}", var_int(get_kit_value(h, "{key}")) {op} {self.int_cast(val)});')
                        return
                    idx = self.expr(sl, method)
                    out.append(pad + f'set_kit_value(h, {idx}, var_int(get_kit_value(h, {idx})) {op} {self.int_cast(val)});')
                    return
                # generic dict/array augassign
                recv = self.expr(t.value, method)
                idx = self.expr(t.slice, method)
                out.append(pad + f"{recv}[{idx}] = {recv}[{idx}] {op} {val};")
                return
            if isinstance(t, ast.Attribute):
                recv = self.expr(t.value, method)
                if t.attr in ("x","y"):
                    if t.attr=="x":
                        out.append(pad + f"{{ Vector2 gp = get_global_pos({recv}); gp.x {op}= {val}; set_global_pos({recv}, gp); }}")
                    else:
                        out.append(pad + f"{{ Vector2 gp = get_global_pos({recv}); gp.y {op}= {val}; set_global_pos({recv}, gp); }}")
                    return
                if t.attr in ("hp","max_hp"):
                    out.append(pad + f"{recv}->set(\"{t.attr}\", {recv}->get(\"{t.attr}\") {op} {val});")
                    return
                raise Exception(f"aug unit {t.attr}")
            if isinstance(t, ast.Name):
                # local Variant augassign needs cast
                if t.id in getattr(self, "_current_locals_set", set()):
                    out.append(pad + f"{t.id} = (double)({t.id}) {op} (double)({val});")
                else:
                    out.append(pad + f"{t.id} = {t.id} {op} {val};")
                return
            raise Exception(f"aug target {type(t).__name__} {ast.dump(t)[:200]}")
        if isinstance(s, ast.If):
            out.append(pad + f"if ({self.expr(s.test, method)}) {{")
            self.block(s.body, out, indent+1, method, s)
            orelse = s.orelse
            while orelse and len(orelse)==1 and isinstance(orelse[0], ast.If):
                e2 = orelse[0]
                out.append(pad + f"}} else if ({self.expr(e2.test, method)}) {{")
                self.block(e2.body, out, indent+1, method, e2)
                orelse = e2.orelse
            if orelse:
                out.append(pad + "} else {")
                self.block(orelse, out, indent+1, method, s)
            out.append(pad + "}")
            return
        if isinstance(s, ast.For):
            target = self.expr(s.target, method)
            it = self.expr(s.iter, method)
            # Cast it to Array for size() to handle Variant holding Array
            it_array = f"((Array)({it}))" if "get_kit_value" in it or it in getattr(self, "_current_locals_set", set()) else it
            # For range_array, it is already Array
            if "range_array" in it:
                out.append(pad + f"for (int {target}=0; {target}< (int)({it}.size()); ++{target}) {{")
            else:
                if isinstance(s.target, ast.Name):
                    out.append(pad + f"for (int __i=0; __i< (int)({it_array}.size()); ++__i) {{")
                    out.append(pad + f"    Variant __v_{target} = {it_array}[__i];")
                    out.append(pad + f"    Object* {target} = nullptr; if (__v_{target}.get_type()==Variant::OBJECT) {target} = Object::cast_to<Object>(__v_{target}); if (!{target}) continue;")
                else:
                    out.append(pad + f"for (int __i=0; __i< (int)({it_array}.size()); ++__i) {{")
                    out.append(pad + f"    Variant {target} = {it_array}[__i];")
            self.block(s.body, out, indent+1, method, s)
            out.append(pad + "}")
            return
        if isinstance(s, ast.Return):
            ret_type = getattr(self, "_current_ret_type", "void")
            if s.value is None:
                if ret_type=="void":
                    out.append(pad + "return;")
                else:
                    out.append(pad + "return false;")
            else:
                expr_val = self.expr(s.value, method)
                if ret_type=="void":
                    # void function returning value -> just return
                    out.append(pad + f"return; // {expr_val}")
                else:
                    out.append(pad + f"return {expr_val};")
            return
        if isinstance(s, ast.Continue):
            out.append(pad + "continue;")
            return
        if isinstance(s, ast.Break):
            out.append(pad + "break;")
            return
        if isinstance(s, ast.Pass):
            return
        if isinstance(s, ast.Try):
            # only FX try -> just emit body
            for sub in s.body:
                self.stmt(sub, out, indent, method)
            return
        if isinstance(s, (ast.Import, ast.ImportFrom)):
            return
        raise Exception(f"stmt unsupported {type(s).__name__}")

    def assign_one(self, target, value, out, pad, method, s):
        if isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name) and target.value.id=="h":
                a = target.attr
                if a in HERO_WRITE:
                    # Setter numerik menerima double/int; kalau nilainya Variant
                    # (kit/dict) konversi lewat var_num() — (double)(Variant) atas
                    # NIL menghasilkan garbage stack (lihat komentar num_cast).
                    v_expr = self.num_cast(value) if a in NUMERIC_WRITES else value
                    out.append(pad + HERO_WRITE[a].format(r="h", v=v_expr) + ";")
                    return
                if a=="skill_damage":
                    out.append(pad + f"/* skill_damage set ignored: {value} */")
                    return
                out.append(pad + f'set_kit_value(h, "{a}", {value});')
                return
            if isinstance(target.value, ast.Attribute) and target.value.attr=="hero":
                # self.hero.x -> h.x
                return self.assign_one(ast.Attribute(value=ast.Name(id="h"), attr=target.attr, ctx=target.ctx), value, out, pad, method, s)
            recv = self.expr(target.value, method)
            if target.attr in ("x","y"):
                if target.attr=="x":
                    out.append(pad + f"{{ Vector2 gp = get_global_pos({recv}); gp.x = {value}; set_global_pos({recv}, gp); }}")
                else:
                    out.append(pad + f"{{ Vector2 gp = get_global_pos({recv}); gp.y = {value}; set_global_pos({recv}, gp); }}")
                return
            if target.attr=="attack_timer":
                # `X.attack_timer = max(X.attack_timer, N)` -> Hero.kit_lock (semantik max) == GDScript.
                # `X.attack_timer = N` (assign langsung; 1 situs: Sylara shackle) -> set detik apa adanya.
                #   kit_lock akan menahan nilai lama yang lebih besar (maxf) -> divergensi vs Python.
                src_val = getattr(s, "value", None)
                is_max = (isinstance(src_val, ast.Call)
                          and isinstance(src_val.func, ast.Name)
                          and src_val.func.id == "max")
                if is_max:
                    out.append(pad + f"kit_lock(h, {recv}, {value});")
                else:
                    out.append(pad + f"set_atk_timer_frames(h, {recv}, {value});")
                return
            # For Object* (e, u, tgt, etc.) use ->set
            # For Dictionary/Array use .set? But hp/max_hp are Object* properties
            # We'll use ->set for all Object* cases
            out.append(pad + f"{recv}->set(\"{target.attr}\", {value});")
            return
        if isinstance(target, ast.Name):
            out.append(pad + f"{target.id} = {value};")
            return
        if isinstance(target, ast.Subscript):
            # h.kit["key"] = value -> set_kit_value
            if isinstance(target.value, ast.Attribute) and isinstance(target.value.value, ast.Name) and target.value.value.id=="h" and target.value.attr=="kit":
                sl = target.slice
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                    out.append(pad + f'set_kit_value(h, "{sl.value}", {value});')
                    return
                idx = self.expr(sl, method)
                out.append(pad + f'set_kit_value(h, {idx}, {value});')
                return
            recv = self.expr(target.value, method)
            idx = self.expr(target.slice, method)
            out.append(pad + f"{recv}[{idx}] = {value};")
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            # unpack: target is (a,b) = value (Array)
            for i, elt in enumerate(target.elts):
                if isinstance(elt, ast.Name):
                    out.append(pad + f"{elt.id} = {value}[{i}];")
                else:
                    self.assign_one(elt, f"{value}[{i}]", out, pad, method, s)
            return
        raise Exception(f"assign target unsupported {type(target).__name__} {ast.dump(target)[:200]}")

    def block(self, body, out, indent, method, owner):
        if not body:
            return
        for s in body:
            if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant):
                continue
            self.stmt(s, out, indent, method)

    def collect_locals(self, fn):
        params = {a.arg for a in fn.args.args} - {"self"} | {"h"}
        names=set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
            if isinstance(node, ast.For):
                for n2 in ast.walk(node.target):
                    if isinstance(n2, ast.Name):
                        names.add(n2.id)
        return sorted(n for n in names if n not in params)

    def emit_func(self, cls_name, fn):
        self.cur_class = cls_name
        self.kind = "boss" if cls_name=="BossHeroSkills" else self.aliases[cls_name]
        params = [a.arg for a in fn.args.args if a.arg!="self"]
        # ensure h is first
        if "h" not in params:
            params = ["h"] + params
        name = self.fname(cls_name, fn.name)
        # return type: bool for cast_*, void otherwise
        ret_type = "bool" if fn.name.startswith("cast_") else "void"
        if fn.name in ("_generic_cast","_fallback_cast"):
            ret_type = "bool" if fn.name=="_generic_cast" else "void"
        # args with types: Object* h, Array all_units etc, or Variant for generic
        arg_list=[]
        for p in params:
            if p=="h":
                arg_list.append("Object* h")
            elif p in ("all_units","all_towers","all_bases","enemies"):
                arg_list.append(f"const Array& {p}")
            else:
                arg_list.append(f"Variant {p}")
        out=[]
        out.append(f"// {cls_name}.{fn.name} L{fn.lineno}")
        out.append(f"{ret_type} MysticHeroSkills::{name}({', '.join(arg_list)}) {{")
        locs = self.collect_locals(fn)
        self._current_locals = locs
        self._current_locals_set = set(locs)
        self._current_ret_type = ret_type
        # infer Array locals: those assigned from kit_enemies, enemies_in_range, range_array, etc.
        array_locals = set()
        dict_locals = set()
        for s in fn.body:
            if isinstance(s, ast.Assign) and len(s.targets)==1 and isinstance(s.targets[0], ast.Name):
                tname = s.targets[0].id
                if tname not in locs:
                    continue
                # check RHS
                rhs = s.value
                if isinstance(rhs, ast.Call):
                    func = rhs.func
                    if isinstance(func, ast.Attribute) and func.attr in ("_get_enemies", "_get_enemies_in_range", "_deal_aoe_damage"):
                        array_locals.add(tname)
                    if isinstance(func, ast.Name) and func.id in ("range", "sorted"):
                        array_locals.add(tname)
                # also check if RHS is Call to self._get_enemies etc - we already handle via expr containing kit_enemies
                # We'll also check if assignment value string contains kit_enemies after expr translation? We'll approximate via AST
                # For simplicity, if var name is enemies, make it Array
                if tname in ("enemies", "in_range", "nearby", "clones_positions"):
                    array_locals.add(tname)
                if tname in ("stats", "hit_enemies", "hit_enemies_set"):
                    dict_locals.add(tname)
        for l in locs:
            if l in params:
                continue
            if l in array_locals:
                out.append(f"    Array {l};")
            elif l in dict_locals:
                out.append(f"    Dictionary {l};")
            else:
                out.append(f"    Variant {l};")
        if locs:
            out.append("")
        for s in fn.body:
            if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant):
                continue
            self.stmt(s, out, 1, fn.name)
        # if bool function and no return at end, return true? In Python, cast returns True/False, but some _cast_* return None -> we should return void? For cast_q etc they return bool.
        if ret_type=="bool":
            # check if last stmt is return, else return false? Actually most cast_* return True at end via trigger, but _cast_* that are void should return void. For safety, if function is cast_q etc, they already have return.
            # For _cast_* (boss skills) they are void in original, but we made bool? In our earlier declaration they are void. So we keep as void for _cast_*.
            # For cast_q/w/e/r they return bool, ensure return
            if not any(isinstance(s, ast.Return) for s in fn.body):
                out.append("    return true;")
        out.append("}")
        out.append("")
        return "\n".join(out)

def generate(check: bool = False):
    classes = load_bundle()
    boss_cls = classes["BossHeroSkills"]
    registry = registry_of(boss_cls)
    vis, dflt = visual_durations(classes)
    bvis = ast.literal_eval(boss_cls["consts"]["BOSS_HERO_VISUAL_DURATION"].value)
    em = CppEmitter(classes, registry, {k.replace("Skills","").lower():v for k,v in vis.items()}, dflt, bvis)

    # Generate header
    header = []
    header.append("#ifndef MYSTIC_HERO_SKILLS_PROCESSOR_H")
    header.append("#define MYSTIC_HERO_SKILLS_PROCESSOR_H")
    header.append("")
    header.append("#include <godot_cpp/classes/ref_counted.hpp>")
    header.append("#include <godot_cpp/classes/node2d.hpp>")
    header.append("#include <godot_cpp/classes/object.hpp>")
    header.append("#include <godot_cpp/variant/dictionary.hpp>")
    header.append("#include <godot_cpp/variant/array.hpp>")
    header.append("#include <godot_cpp/variant/vector2.hpp>")
    header.append("#include <godot_cpp/variant/utility_functions.hpp>")
    header.append("#include <godot_cpp/core/math.hpp>")
    header.append("#include <godot_cpp/core/class_db.hpp>")
    header.append("#include <godot_cpp/variant/callable.hpp>")
    header.append("#include <unordered_map>")
    header.append("#include <string>")
    header.append("")
    header.append("namespace godot {")
    header.append("")
    header.append("class MysticHeroSkills : public RefCounted {")
    header.append("    GDCLASS(MysticHeroSkills, RefCounted);")
    header.append("")
    header.append("public:")
    header.append("    // helpers")
    header.append("    static Vector2 get_global_pos(Object* obj);")
    header.append("    static double get_global_pos_x(Object* obj);")
    header.append("    static double get_global_pos_y(Object* obj);")
    header.append("    static void set_global_pos(Object* obj, Vector2 pos);")
    header.append("    static void set_global_pos_x(Object* obj, double x);")
    header.append("    static void set_global_pos_y(Object* obj, double y);")
    header.append("    static double get_hp(Object* obj);")
    header.append("    static double get_max_hp(Object* obj);")
    header.append("    static void set_hp(Object* obj, double v);")
    header.append("    static void set_max_hp(Object* obj, double v);")
    header.append("    static double get_damage(Object* obj);")
    header.append("    static void set_damage(Object* obj, double v);")
    header.append("    static String get_team(Object* obj);")
    header.append("    static String get_hero_type(Object* obj);")
    header.append("    static String get_dmg_school(Object* obj);")
    header.append("    static int get_facing(Object* obj);")
    header.append("    static void set_facing(Object* obj, int v);")
    header.append("    static int get_level(Object* obj);")
    header.append("    static void set_level(Object* obj, int v);")
    header.append("    static double get_base_damage(Object* obj);")
    header.append("    static void set_base_damage(Object* obj, double v);")
    header.append("    static double get_skill_range(Object* obj);")
    header.append("    static double get_attack_range(Object* obj);")
    header.append("    static Dictionary get_skill_data(Object* obj);")
    header.append("    static Variant get_active_skill(Object* obj);")
    header.append("    static void set_active_skill(Object* obj, Variant v);")
    header.append("    static int get_active_skill_timer(Object* obj);")
    header.append("    static void set_active_skill_timer(Object* obj, int v);")
    header.append("    static int get_skill_timer(Object* obj);")
    header.append("    static void set_skill_timer(Object* obj, int v);")
    header.append("    static int get_w_cooldown(Object* obj);")
    header.append("    static void set_w_cooldown(Object* obj, int v);")
    header.append("    static int get_e_cooldown(Object* obj);")
    header.append("    static void set_e_cooldown(Object* obj, int v);")
    header.append("    static int get_r_cooldown(Object* obj);")
    header.append("    static void set_r_cooldown(Object* obj, int v);")
    header.append("    static int get_skill_cooldown_max(Object* obj);")
    header.append("    static int get_w_cooldown_max(Object* obj);")
    header.append("    static int get_e_cooldown_max(Object* obj);")
    header.append("    static int get_r_cooldown_max(Object* obj);")
    header.append("    static double get_speed_frames(Object* obj);")
    header.append("    static void set_speed_frames(Object* obj, double v);")
    header.append("    static double get_attack_cooldown_frames(Object* obj);")
    header.append("    static void set_attack_cooldown_frames(Object* obj, double v);")
    header.append('    // Assign langsung `X.attack_timer = N` (frame) -> detik; bukan max seperti kit_lock.')
    header.append("    static void set_atk_timer_frames(Object* h, Object* target, double frames);")
    header.append('    // Baca Dictionary const-safe + konversi numerik deterministik (lihat komentar definisi).')
    header.append("    static Variant dict_at(const Variant& container, const Variant& key);")
    header.append("    static double var_num(const Variant& v);")
    header.append("    static int64_t var_int(const Variant& v);")
    header.append("    static bool is_alive(Object* obj);")
    header.append("    static Variant get_kit_value(Object* obj, const String& key, Variant def = Variant());")
    header.append("    static void set_kit_value(Object* obj, const String& key, Variant value);")
    header.append("    static Dictionary get_kit(Object* obj);")
    header.append("    static void set_kit(Object* obj, const Dictionary& d);")
    header.append("    static Object* get_target(Object* obj);")
    header.append("    static void set_target(Object* obj, Variant v);")
    header.append("    static Variant py_or(Variant a, Variant b);")
    header.append("    static bool truthy(Variant v);")
    header.append("    static Array range_array(int n);")
    header.append("    static Dictionary make_dict();")
    header.append("    static Dictionary make_dict(Variant k1, Variant v1);")
    header.append("    static Dictionary make_dict(Variant k1, Variant v1, Variant k2, Variant v2);")
    header.append("    static Dictionary make_dict(Variant k1, Variant v1, Variant k2, Variant v2, Variant k3, Variant v3);")
    header.append("    static Dictionary make_dict(Variant k1, Variant v1, Variant k2, Variant v2, Variant k3, Variant v3, Variant k4, Variant v4);")
    header.append("    static bool in_array(const Array& arr, Variant v);")
    header.append("    static Array make_array();")
    header.append("    static Array make_array(Variant a);")
    header.append("    static Array make_array(Variant a, Variant b);")
    header.append("    static Array make_array(Variant a, Variant b, Variant c);")
    header.append("    static Array make_array(Variant a, Variant b, Variant c, Variant d);")
    header.append("")
    header.append("    // BaseSkill helpers")
    header.append("    static double skill_range(Object* h, double fallback = 200.0);")
    header.append("    static Array enemies_in_range(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, double range_val, Variant center_x = Variant(), Variant center_y = Variant());")
    header.append("    static int deal_aoe(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, double range_val, double damage_multiplier = 1.0);")
    header.append("    static Object* acquire_target(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, Variant range_val = Variant());")
    header.append("    static bool has_target(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, Variant range_val = Variant());")
    header.append("    static int visual_duration(const String& hero_type, const String& key);")
    header.append("    static int visual_duration_kind(const String& kind, const String& hero_type, const String& key);")
    header.append("    static int default_visual_duration(const String& key);")
    header.append("    static bool is_starter_kind(const String& hero_type);")
    header.append("    static void set_active_skill(Object* h, const String& kind, const String& key, Variant duration);")
    header.append("    static void trigger_q(Object* h, const String& kind, double shake_amount = 8.0, Variant visual_duration = Variant());")
    header.append("    static void trigger_w(Object* h, const String& kind, double shake_amount = 5.0, Variant visual_duration = Variant());")
    header.append("    static void trigger_e(Object* h, const String& kind, double shake_amount = 6.0, Variant visual_duration = Variant());")
    header.append("    static void trigger_r(Object* h, const String& kind, double shake_amount = 15.0, Variant visual_duration = Variant());")
    header.append("")
    header.append("    // kit bridges")
    header.append("    static Array kit_enemies(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases);")
    header.append("    static int kit_skill_damage(Object* h);")
    header.append("    static Dictionary kit_catalog_all(Object* h);")
    header.append("    static Dictionary kit_hero_levels(Object* h);")
    header.append("    static void kit_hit(Object* h, Object* target, int dmg, const String& team, Variant src = Variant(), const String& school = \"\");")
    header.append("    static void kit_slow(Object* h, Object* target, double amount, double dur_frames);")
    header.append("    static void kit_lock(Object* h, Object* target, double frames);")
    header.append("    static double kit_atk_timer(Object* h, Object* target);")
    header.append("    static bool kit_unit_alive(Object* h, Object* target);")
    header.append("    static bool kit_has_slow(Object* h, Object* target);")
    header.append("    static bool kit_has_atk_timer(Object* h, Object* target);")
    header.append("    static bool kit_has_hp(Object* h, Object* target);")
    header.append("    static void kit_shake(Object* h, double amount);")
    header.append("    static void kit_sound(Object* h, double volume);")
    header.append("    static void kit_popup(Object* h, const String& text, bool critical = false);")
    header.append("    static void kit_skill_proj(Object* h, Object* target, double speed = 13.0);")
    header.append("    static void kit_fx_cast(Object* h, const String& skill);")
    header.append("    static void kit_fx_impact(Object* h, double x, double y, double r, const String& skill);")
    header.append("")
    header.append("    static String hero_kind(Object* h);")
    header.append("")
    header.append("    static void init_state(Object* h);")
    header.append("    static void update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases);")
    header.append("    static bool cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases);")
    header.append("    static bool cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases);")
    header.append("    static bool cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases);")
    header.append("    static bool cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases);")
    header.append("")
    header.append("    static bool boss_generic(Object* h, const String& skill_key, const Array& all_units, const Array& all_towers, const Array& all_bases);")
    header.append("    static bool registry_dispatch(Object* h, const String& skill_key, const Array& enemies);")
    header.append("    static void fallback_cast(Object* h, const Array& enemies, const String& skill_key);")
    header.append("    static bool by_pair0(Variant a, Variant b);")
    header.append("    static bool __by_pair0(Variant a, Variant b);")
    header.append("")

    # Declare all skill methods
    for cls_name, cls in classes.items():
        if cls_name=="BaseSkill":
            continue
        for mname in cls["methods"]:
            if mname=="__init__":
                continue
            if cls_name=="BossHeroSkills" and mname in ("_generic_cast","_fallback_cast","_get_visual_duration"):
                continue
            if cls_name=="BossHeroSkills" and mname in ("cast_q","cast_w","cast_e","cast_r"):
                continue
            fname = em.fname(cls_name, mname)
            params = [a.arg for a in cls["methods"][mname].args.args if a.arg!="self"]
            if "h" not in params:
                params = ["h"]+params
            # determine signature
            arg_list=[]
            for p in params:
                if p=="h":
                    arg_list.append("Object* h")
                elif p in ("all_units","all_towers","all_bases","enemies"):
                    arg_list.append(f"const Array& {p}")
                else:
                    arg_list.append(f"Variant {p}")
            ret = "bool" if mname.startswith("cast_") else "void"
            # boss _cast_* are void in Python but we keep void
            if mname.startswith("_cast_"):
                ret="void"
            header.append(f"    static {ret} {fname}({', '.join(arg_list)});")

    header.append("")
    header.append("protected:")
    header.append("    static void _bind_methods();")
    header.append("};")
    header.append("")
    header.append("} // namespace godot")
    header.append("")
    header.append("#endif // MYSTIC_HERO_SKILLS_PROCESSOR_H")

    header_text = "\n".join(header)

    # Generate cpp
    cpp = []
    cpp.append('#include "hero_skills_processor.h"')
    cpp.append("")
    cpp.append('#include <godot_cpp/classes/node2d.hpp>')
    cpp.append('#include <godot_cpp/variant/utility_functions.hpp>')
    cpp.append('#include <godot_cpp/core/math.hpp>')
    cpp.append('#include <cmath>')
    cpp.append("")
    cpp.append("using namespace godot;")
    cpp.append("")
    cpp.append("// helpers for property access")
    cpp.append("Vector2 MysticHeroSkills::get_global_pos(Object* obj) { Variant v = obj->get(\"global_position\"); if (v.get_type()==Variant::VECTOR2) return v; return Vector2(); }")
    cpp.append("double MysticHeroSkills::get_global_pos_x(Object* obj) { return get_global_pos(obj).x; }")
    cpp.append("double MysticHeroSkills::get_global_pos_y(Object* obj) { return get_global_pos(obj).y; }")
    cpp.append("void MysticHeroSkills::set_global_pos(Object* obj, Vector2 pos) { obj->set(\"global_position\", pos); }")
    cpp.append("void MysticHeroSkills::set_global_pos_x(Object* obj, double x) { Vector2 p = get_global_pos(obj); p.x = x; set_global_pos(obj, p); }")
    cpp.append("void MysticHeroSkills::set_global_pos_y(Object* obj, double y) { Vector2 p = get_global_pos(obj); p.y = y; set_global_pos(obj, p); }")
    cpp.append("double MysticHeroSkills::get_hp(Object* obj) { Variant v = obj->get(\"hp\"); return (double)v; }")
    cpp.append("double MysticHeroSkills::get_max_hp(Object* obj) { Variant v = obj->get(\"max_hp\"); return (double)v; }")
    cpp.append("void MysticHeroSkills::set_hp(Object* obj, double v) { obj->set(\"hp\", v); }")
    cpp.append("void MysticHeroSkills::set_max_hp(Object* obj, double v) { obj->set(\"max_hp\", v); }")
    cpp.append("double MysticHeroSkills::get_damage(Object* obj) { Variant v = obj->get(\"damage\"); return (double)v; }")
    cpp.append("void MysticHeroSkills::set_damage(Object* obj, double v) { obj->set(\"damage\", (double)v); }")
    cpp.append("String MysticHeroSkills::get_team(Object* obj) { Variant v = obj->get(\"team\"); return v; }")
    cpp.append("String MysticHeroSkills::get_hero_type(Object* obj) { Variant v = obj->get(\"hero_type\"); return v; }")
    cpp.append("String MysticHeroSkills::get_dmg_school(Object* obj) { Variant v = obj->get(\"dmg_school\"); return v; }")
    cpp.append("int MysticHeroSkills::get_facing(Object* obj) { Variant v = obj->get(\"facing\"); return (int)v; }")
    cpp.append("void MysticHeroSkills::set_facing(Object* obj, int v) { obj->set(\"facing\", v); }")
    cpp.append("int MysticHeroSkills::get_level(Object* obj) { Variant v = obj->get(\"level\"); return (int)v; }")
    cpp.append("void MysticHeroSkills::set_level(Object* obj, int v) { obj->set(\"level\", v); }")
    cpp.append("double MysticHeroSkills::get_base_damage(Object* obj) { Variant v = obj->get(\"base_damage\"); return (double)v; }")
    cpp.append("void MysticHeroSkills::set_base_damage(Object* obj, double v) { obj->set(\"base_damage\", v); }")
    cpp.append("double MysticHeroSkills::get_skill_range(Object* obj) { Variant v = obj->get(\"skill_range\"); return (double)v; }")
    cpp.append("double MysticHeroSkills::get_attack_range(Object* obj) { Variant v = obj->get(\"attack_range\"); return (double)v; }")
    cpp.append("Dictionary MysticHeroSkills::get_skill_data(Object* obj) { Variant v = obj->get(\"skill_data\"); if (v.get_type()==Variant::DICTIONARY) return v; return Dictionary(); }")
    cpp.append("Variant MysticHeroSkills::get_active_skill(Object* obj) { return obj->get(\"active_skill\"); }")
    cpp.append("void MysticHeroSkills::set_active_skill(Object* obj, Variant v) { obj->set(\"active_skill\", v); }")
    cpp.append("int MysticHeroSkills::get_active_skill_timer(Object* obj) { Variant v = obj->get(\"active_skill_timer\"); return (int)v; }")
    cpp.append("void MysticHeroSkills::set_active_skill_timer(Object* obj, int v) { obj->set(\"active_skill_timer\", v); }")
    cpp.append("int MysticHeroSkills::get_skill_timer(Object* obj) { Variant v = obj->get(\"skill_timer\"); return (int)v; }")
    cpp.append("void MysticHeroSkills::set_skill_timer(Object* obj, int v) { obj->set(\"skill_timer\", v); }")
    cpp.append("int MysticHeroSkills::get_w_cooldown(Object* obj) { Variant v = obj->get(\"w_cooldown\"); return (int)v; }")
    cpp.append("void MysticHeroSkills::set_w_cooldown(Object* obj, int v) { obj->set(\"w_cooldown\", v); }")
    cpp.append("int MysticHeroSkills::get_e_cooldown(Object* obj) { Variant v = obj->get(\"e_cooldown\"); return (int)v; }")
    cpp.append("void MysticHeroSkills::set_e_cooldown(Object* obj, int v) { obj->set(\"e_cooldown\", v); }")
    cpp.append("int MysticHeroSkills::get_r_cooldown(Object* obj) { Variant v = obj->get(\"r_cooldown\"); return (int)v; }")
    cpp.append("void MysticHeroSkills::set_r_cooldown(Object* obj, int v) { obj->set(\"r_cooldown\", v); }")
    cpp.append("int MysticHeroSkills::get_skill_cooldown_max(Object* obj) { Variant v = obj->get(\"skill_cooldown_max\"); return (int)v; }")
    cpp.append("int MysticHeroSkills::get_w_cooldown_max(Object* obj) { Variant v = obj->get(\"w_cooldown_max\"); return (int)v; }")
    cpp.append("int MysticHeroSkills::get_e_cooldown_max(Object* obj) { Variant v = obj->get(\"e_cooldown_max\"); return (int)v; }")
    cpp.append("int MysticHeroSkills::get_r_cooldown_max(Object* obj) { Variant v = obj->get(\"r_cooldown_max\"); return (int)v; }")
    cpp.append("double MysticHeroSkills::get_speed_frames(Object* obj) { Variant v = obj->get(\"move_speed\"); return (double)v / 60.0; }")
    cpp.append("void MysticHeroSkills::set_speed_frames(Object* obj, double v) { obj->set(\"move_speed\", (double)v * 60.0); }")
    # GDScript: int(roundf(float(h.attack_cooldown) * 60.0)) -> frame BULAT.
    # Tanpa round, nilai kit (mis. _original_attack_cd) menyimpan 49.99998 alih-alih 50.
    cpp.append('// GDScript membaca int(roundf(float(h.attack_cooldown) * 60.0)) -> frame bulat.')
    cpp.append('double MysticHeroSkills::get_attack_cooldown_frames(Object* obj) { Variant v = obj->get("attack_cooldown"); return (double)(int64_t)round((double)v * 60.0); }')
    cpp.append("void MysticHeroSkills::set_attack_cooldown_frames(Object* obj, double v) { obj->set(\"attack_cooldown\", (double)v / 60.0); }")
    cpp.append('// Assign langsung `X.attack_timer = N` (frame) -> detik apa adanya; Hero.kit_lock memakai maxf().')
    cpp.append('void MysticHeroSkills::set_atk_timer_frames(Object* h, Object* target, double frames) { if (!target) { return; } if (!kit_has_atk_timer(h, target)) { return; } target->set("attack_timer", frames / 60.0); }')
    cpp.append("// Baca Dictionary TANPA operator[] non-const: operator[] memanggil ptrw()")
    cpp.append("// (detach COW) dan MENYISIPKAN entri NIL kalau key tidak ada; dipakai berantai")
    cpp.append("// pada temporary (kit_catalog_all(h)[type][\"damage\"]) hasilnya Variant kosong.")
    cpp.append("Variant MysticHeroSkills::dict_at(const Variant& container, const Variant& key) { if (container.get_type()!=Variant::DICTIONARY) { return Variant(); } Dictionary d = container; return d.get(key, Variant()); }")
    cpp.append("// Variant::operator double() godot-cpp menulis ke `double result;` TANPA inisialisasi")
    cpp.append("// lewat to_type_constructor[FLOAT]; kalau sumber bukan numerik (NIL/Dictionary),")
    cpp.append("// buffer dibiarkan -> angka acak dari stack. var_num/var_int deterministik")
    cpp.append("// dan sama dengan GDScript (null diperlakukan 0).")
    cpp.append("double MysticHeroSkills::var_num(const Variant& v) { switch (v.get_type()) { case Variant::INT: return (double)(int64_t)v; case Variant::FLOAT: return (double)v; case Variant::BOOL: return ((bool)v) ? 1.0 : 0.0; case Variant::STRING: { String s = v; return s.is_valid_float() ? (double)s.to_float() : 0.0; } default: return 0.0; } }")
    cpp.append("int64_t MysticHeroSkills::var_int(const Variant& v) { switch (v.get_type()) { case Variant::INT: return (int64_t)v; case Variant::FLOAT: return (int64_t)(double)v; case Variant::BOOL: return ((bool)v) ? 1 : 0; case Variant::STRING: { String s = v; return s.is_valid_float() ? (int64_t)s.to_float() : 0; } default: return 0; } }")
    cpp.append("bool MysticHeroSkills::is_alive(Object* obj) { Variant v = obj->get(\"is_dead\"); bool dead = (bool)v; return !dead; }")
    cpp.append("Dictionary MysticHeroSkills::get_kit(Object* obj) { Variant v = obj->get(\"kit\"); if (v.get_type()==Variant::DICTIONARY) return v; return Dictionary(); }")
    cpp.append("void MysticHeroSkills::set_kit(Object* obj, const Dictionary& d) { obj->set(\"kit\", d); }")
    cpp.append("Variant MysticHeroSkills::get_kit_value(Object* obj, const String& key, Variant def) { Dictionary d = get_kit(obj); if (d.has(key)) return d[key]; return def; }")
    cpp.append("void MysticHeroSkills::set_kit_value(Object* obj, const String& key, Variant value) { Dictionary d = get_kit(obj); d[key]=value; set_kit(obj, d); }")
    cpp.append("Object* MysticHeroSkills::get_target(Object* obj) { Variant v = obj->get(\"target\"); if (v.get_type()==Variant::OBJECT) return Object::cast_to<Object>(v); return nullptr; }")
    cpp.append("void MysticHeroSkills::set_target(Object* obj, Variant v) { obj->set(\"target\", v); }")
    cpp.append("bool MysticHeroSkills::truthy(Variant v) { if (v.get_type()==Variant::NIL) return false; if (v.get_type()==Variant::BOOL) return (bool)v; if (v.get_type()==Variant::INT) return (int64_t)v !=0; if (v.get_type()==Variant::FLOAT) return (double)v !=0.0; if (v.get_type()==Variant::STRING) { String s=v; return s.length()>0; } if (v.get_type()==Variant::ARRAY) { Array a=v; return a.size()>0; } if (v.get_type()==Variant::DICTIONARY) { Dictionary d=v; return d.size()>0; } return true; }")
    cpp.append("Variant MysticHeroSkills::py_or(Variant a, Variant b) { return truthy(a) ? a : b; }")
    cpp.append("Array MysticHeroSkills::range_array(int n) { Array a; for(int i=0;i<n;++i) a.append(i); return a; }")
    cpp.append("Dictionary MysticHeroSkills::make_dict() { return Dictionary(); }")
    cpp.append("Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1) { Dictionary d; d[k1]=v1; return d; }")
    cpp.append("Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1, Variant k2, Variant v2) { Dictionary d; d[k1]=v1; d[k2]=v2; return d; }")
    cpp.append("Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1, Variant k2, Variant v2, Variant k3, Variant v3) { Dictionary d; d[k1]=v1; d[k2]=v2; d[k3]=v3; return d; }")
    cpp.append("Dictionary MysticHeroSkills::make_dict(Variant k1, Variant v1, Variant k2, Variant v2, Variant k3, Variant v3, Variant k4, Variant v4) { Dictionary d; d[k1]=v1; d[k2]=v2; d[k3]=v3; d[k4]=v4; return d; }")
    cpp.append("bool MysticHeroSkills::in_array(const Array& arr, Variant v) { for(int i=0;i<arr.size();++i) if (arr[i]==v) return true; return false; }")
    cpp.append("Array MysticHeroSkills::make_array() { return Array(); }")
    cpp.append("Array MysticHeroSkills::make_array(Variant a) { Array arr; arr.append(a); return arr; }")
    cpp.append("Array MysticHeroSkills::make_array(Variant a, Variant b) { Array arr; arr.append(a); arr.append(b); return arr; }")
    cpp.append("Array MysticHeroSkills::make_array(Variant a, Variant b, Variant c) { Array arr; arr.append(a); arr.append(b); arr.append(c); return arr; }")
    cpp.append("Array MysticHeroSkills::make_array(Variant a, Variant b, Variant c, Variant d) { Array arr; arr.append(a); arr.append(b); arr.append(c); arr.append(d); return arr; }")
    cpp.append("")

    # BaseSkill helpers - write manually with parity
    cpp.append("// BaseSkill helpers - mirror GDScript header")
    cpp.append("double MysticHeroSkills::skill_range(Object* h, double fallback) {")
    cpp.append("    double rng = get_skill_range(h);")
    cpp.append("    if (rng==0.0) { Dictionary data = get_skill_data(h); Variant v = data.get(\"skill_range\", fallback); rng = (double)v; if (rng==0.0) rng=fallback; }")
    cpp.append("    double ar = get_attack_range(h);")
    cpp.append("    return MAX(ar, rng);")
    cpp.append("}")
    cpp.append("")
    cpp.append("Array MysticHeroSkills::kit_enemies(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {")
    cpp.append("    Variant ret = h->call(\"kit_enemies\", all_units, all_towers, all_bases);")
    cpp.append("    if (ret.get_type()==Variant::ARRAY) return ret; return Array();")
    cpp.append("}")
    cpp.append("int MysticHeroSkills::kit_skill_damage(Object* h) { Variant ret = h->call(\"kit_skill_damage\"); return (int)ret; }")
    cpp.append("Dictionary MysticHeroSkills::kit_catalog_all(Object* h) { Variant ret = h->call(\"kit_catalog_all\"); if (ret.get_type()==Variant::DICTIONARY) return ret; return Dictionary(); }")
    cpp.append("Dictionary MysticHeroSkills::kit_hero_levels(Object* h) { Variant ret = h->call(\"kit_hero_levels\"); if (ret.get_type()==Variant::DICTIONARY) return ret; return Dictionary(); }")
    cpp.append("void MysticHeroSkills::kit_hit(Object* h, Object* target, int dmg, const String& team, Variant src, const String& school) { if (!target) return; h->call(\"kit_hit\", target, dmg, team, src, school); }")
    cpp.append("void MysticHeroSkills::kit_slow(Object* h, Object* target, double amount, double dur_frames) { if (!target) return; h->call(\"kit_slow\", target, amount, dur_frames); }")
    cpp.append("void MysticHeroSkills::kit_lock(Object* h, Object* target, double frames) { if (!target) return; h->call(\"kit_lock\", target, frames); }")
    cpp.append("double MysticHeroSkills::kit_atk_timer(Object* h, Object* target) { if (!target) return 0; Variant ret = h->call(\"kit_atk_timer\", target); return (double)ret; }")
    cpp.append("bool MysticHeroSkills::kit_unit_alive(Object* h, Object* target) { if (!target) return false; Variant ret = h->call(\"kit_unit_alive\", target); return (bool)ret; }")
    cpp.append("bool MysticHeroSkills::kit_has_slow(Object* h, Object* target) { if (!target) return false; Variant ret = h->call(\"kit_has_slow\", target); return (bool)ret; }")
    cpp.append("bool MysticHeroSkills::kit_has_atk_timer(Object* h, Object* target) { if (!target) return false; Variant ret = h->call(\"kit_has_atk_timer\", target); return (bool)ret; }")
    cpp.append("bool MysticHeroSkills::kit_has_hp(Object* h, Object* target) { if (!target) return false; Variant ret = h->call(\"kit_has_hp\", target); return (bool)ret; }")
    cpp.append("void MysticHeroSkills::kit_shake(Object* h, double amount) { h->call(\"kit_shake\", amount); }")
    cpp.append("void MysticHeroSkills::kit_sound(Object* h, double volume) { h->call(\"kit_sound\", volume); }")
    cpp.append("void MysticHeroSkills::kit_popup(Object* h, const String& text, bool critical) { h->call(\"kit_popup\", text, critical); }")
    cpp.append("void MysticHeroSkills::kit_skill_proj(Object* h, Object* target, double speed) { if (!target) return; h->call(\"kit_skill_proj\", target, speed); }")
    cpp.append("void MysticHeroSkills::kit_fx_cast(Object* h, const String& skill) { h->call(\"kit_fx_cast\", skill); }")
    cpp.append("void MysticHeroSkills::kit_fx_impact(Object* h, double x, double y, double r, const String& skill) { h->call(\"kit_fx_impact\", x, y, r, skill); }")
    cpp.append("")

    cpp.append("Array MysticHeroSkills::enemies_in_range(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, double range_val, Variant center_x, Variant center_y) {")
    cpp.append("    double cx = center_x.get_type()==Variant::NIL ? get_global_pos_x(h) : (double)center_x;")
    cpp.append("    double cy = center_y.get_type()==Variant::NIL ? get_global_pos_y(h) : (double)center_y;")
    cpp.append("    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);")
    cpp.append("    Array in_range;")
    cpp.append("    for (int i=0;i<enemies.size();++i) {")
    cpp.append("        Variant vv = enemies[i]; if (vv.get_type()!=Variant::OBJECT) continue; Object* e = Object::cast_to<Object>(vv); if (!e) continue;")
    cpp.append("        double dx = get_global_pos_x(e) - cx; double dy = get_global_pos_y(e) - cy; double dist = Vector2(dx, dy).length();")
    cpp.append("        if (dist <= range_val) { Array pair; pair.append(e); pair.append(dist); in_range.append(pair); }")
    cpp.append("    }")
    cpp.append("    return in_range;")
    cpp.append("}")
    cpp.append("int MysticHeroSkills::deal_aoe(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, double range_val, double damage_multiplier) {")
    cpp.append("    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);")
    cpp.append("    int hit_count=0;")
    cpp.append("    for (int i=0;i<enemies.size();++i) { Variant vv=enemies[i]; if (vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if (!e) continue;")
    cpp.append("        double dx = get_global_pos_x(e) - get_global_pos_x(h); double dy = get_global_pos_y(e) - get_global_pos_y(h); double dist = Vector2(dx,dy).length();")
    cpp.append("        if (dist <= range_val) { int dmg = (int)((double)kit_skill_damage(h) * damage_multiplier); kit_hit(h, e, dmg, get_team(h), h, get_dmg_school(h)); ++hit_count; }")
    cpp.append("    }")
    cpp.append("    return hit_count;")
    cpp.append("}")
    cpp.append("Object* MysticHeroSkills::acquire_target(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, Variant range_val) {")
    cpp.append("    double rng = range_val.get_type()==Variant::NIL ? skill_range(h) : (double)range_val;")
    cpp.append("    double reach = rng * 1.15;")
    cpp.append("    Object* cur = get_target(h);")
    cpp.append("    if (cur && kit_unit_alive(h, cur)) { double dx = get_global_pos_x(cur) - get_global_pos_x(h); double dy = get_global_pos_y(cur) - get_global_pos_y(h); if (Vector2(dx,dy).length() <= reach) return cur; }")
    cpp.append("    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);")
    cpp.append("    Object* best=nullptr; double best_dist=reach;")
    cpp.append("    for (int i=0;i<enemies.size();++i) { Variant vv=enemies[i]; if (vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if (!e) continue; if (!kit_unit_alive(h,e)) continue; double dx=get_global_pos_x(e)-get_global_pos_x(h); double dy=get_global_pos_y(e)-get_global_pos_y(h); double d=Vector2(dx,dy).length(); if (d<=best_dist) { best=e; best_dist=d; } }")
    cpp.append("    if (best) set_target(h, best);")
    cpp.append("    return best;")
    cpp.append("}")
    cpp.append("bool MysticHeroSkills::has_target(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases, Variant range_val) {")
    cpp.append("    return acquire_target(h, all_units, all_towers, all_bases, range_val)!=nullptr;")
    cpp.append("}")
    # ── durasi visual ──
    # Semantik BaseSkill._get_visual_duration (== HeroSkillKit.__vis_dur):
    #   kind "boss"  -> BOSS_HERO_VISUAL_DURATION[hero_type][key], else default
    #   kind starter -> SKILL_VISUAL_DURATION[kelas][key],        else default
    # Tabelnya DIBANGKITKAN dari data Python (vis/bvis/dflt) — bukan angka
    # yang disalin tangan, supaya override baru tidak membuat C++ basi.
    vis_map = {k.replace("Skills", "").lower(): v for k, v in vis.items()}

    def _chain(tbl):
        return " ".join('if (key=="%s") return %d;' % (k, int(tbl[k]))
                        for k in ("q", "w", "e", "r") if k in tbl)

    dflt_chain = _chain(dflt)
    dflt_fallback = int(dflt.get("q", 60))
    starter_chain = " || ".join('hero_type=="%s"' % k for k in STARTERS)

    cpp.append("int MysticHeroSkills::default_visual_duration(const String& key) {")
    cpp.append("    " + dflt_chain + " return %d;" % dflt_fallback)
    cpp.append("}")
    cpp.append("bool MysticHeroSkills::is_starter_kind(const String& hero_type) {")
    cpp.append("    return " + starter_chain + ";")
    cpp.append("}")
    cpp.append("int MysticHeroSkills::visual_duration_kind(const String& kind, const String& hero_type, const String& key) {")
    cpp.append("    if (kind==\"boss\") {")
    for _ht in sorted(bvis.keys()):
        cpp.append("        if (hero_type==\"%s\") { %s }" % (_ht, _chain(bvis[_ht])))
    cpp.append("        return default_visual_duration(key);")
    cpp.append("    }")
    for _kind in sorted(vis_map.keys()):
        cpp.append("    if (kind==\"%s\") { %s }" % (_kind, _chain(vis_map[_kind])))
    cpp.append("    return default_visual_duration(key);")
    cpp.append("}")
    cpp.append("int MysticHeroSkills::visual_duration(const String& hero_type, const String& key) {")
    cpp.append("    // API tanpa kind (dipakai HeroSkillKitLoader.get_visual_duration):")
    cpp.append("    // kind diturunkan dari hero_type — 6 starter punya kelas handler")
    cpp.append("    // sendiri, sisanya lewat BossHeroSkills (kind \"boss\").")
    cpp.append("    return visual_duration_kind(is_starter_kind(hero_type) ? hero_type : String(\"boss\"), hero_type, key);")
    cpp.append("}")
    cpp.append("void MysticHeroSkills::set_active_skill(Object* h, const String& kind, const String& key, Variant duration) {")
    cpp.append("    int dur = duration.get_type()==Variant::NIL ? visual_duration_kind(kind, get_hero_type(h), key) : (int)duration;")
    cpp.append("    set_active_skill(h, Variant(key)); set_active_skill_timer(h, dur);")
    cpp.append("}")
    cpp.append("void MysticHeroSkills::trigger_q(Object* h, const String& kind, double shake_amount, Variant visual_duration) {")
    cpp.append("    set_skill_timer(h, get_skill_cooldown_max(h)); set_active_skill(h, kind, \"q\", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 0.7);")
    cpp.append("}")
    cpp.append("void MysticHeroSkills::trigger_w(Object* h, const String& kind, double shake_amount, Variant visual_duration) {")
    cpp.append("    set_w_cooldown(h, get_w_cooldown_max(h)); set_active_skill(h, kind, \"w\", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 0.6);")
    cpp.append("}")
    cpp.append("void MysticHeroSkills::trigger_e(Object* h, const String& kind, double shake_amount, Variant visual_duration) {")
    cpp.append("    set_e_cooldown(h, get_e_cooldown_max(h)); set_active_skill(h, kind, \"e\", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 0.7);")
    cpp.append("}")
    cpp.append("void MysticHeroSkills::trigger_r(Object* h, const String& kind, double shake_amount, Variant visual_duration) {")
    cpp.append("    set_r_cooldown(h, get_r_cooldown_max(h)); set_active_skill(h, kind, \"r\", visual_duration); kit_shake(h, shake_amount); kit_sound(h, 1.0);")
    cpp.append("}")
    cpp.append("")

    cpp.append("String MysticHeroSkills::hero_kind(Object* h) {")
    cpp.append("    String ht = get_hero_type(h);")
    cpp.append("    if (ht==\"grimjaw\" || ht==\"kaizen\" || ht==\"sylara\" || ht==\"thorne\" || ht==\"vex\" || ht==\"zephyr\") return ht;")
    cpp.append("    return \"boss\";")
    cpp.append("}")
    cpp.append("")

    # Generate functions for each class
    for cls_name, cls in classes.items():
        if cls_name=="BaseSkill":
            continue
        for mname, fn in sorted(cls["methods"].items(), key=lambda kv: kv[1].lineno):
            if mname=="__init__":
                continue
            if cls_name=="BossHeroSkills" and mname in ("_generic_cast","_fallback_cast","_get_visual_duration"):
                continue
            if cls_name=="BossHeroSkills" and mname in ("cast_q","cast_w","cast_e","cast_r"):
                continue
            cpp.append(em.emit_func(cls_name, fn))

    # Generate boss generic, fallback, registry dispatch, init_state, update_timers, cast_q etc
    cpp.append("// boss generic helpers")
    cpp.append("void MysticHeroSkills::fallback_cast(Object* h, const Array& enemies, const String& skill_key) {")
    cpp.append("    set_active_skill(h, Variant(skill_key)); set_active_skill_timer(h, 40);")
    cpp.append("    double mult=1.0; if (skill_key==\"q\") mult=1.0; else if (skill_key==\"w\") mult=1.2; else if (skill_key==\"e\") mult=1.5; else if (skill_key==\"r\") mult=2.5;")
    cpp.append("    String school = get_dmg_school(h);")
    # src = h (BUKAN Variant()): Hero.kit_hit meneruskan src ke
    # CombatSystem.apply_damage untuk atribusi damage/reflect (bristleback).
    # GDScript __fallback_cast mengirim h; nil di sini = kredit damage hilang.
    cpp.append("    if (skill_key==\"q\" || skill_key==\"w\") { Object* tgt=get_target(h); if (tgt && kit_unit_alive(h,tgt)) { int dmg=(int)((double)kit_skill_damage(h)*mult); kit_hit(h,tgt,dmg,get_team(h),h,school); } }")
    cpp.append("    else { double aoe_range = skill_key==\"e\" ? 150.0 : 200.0; for(int i=0;i<enemies.size();++i){ Variant vv=enemies[i]; if(vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if(!e) continue; double dx=get_global_pos_x(e)-get_global_pos_x(h); double dy=get_global_pos_y(e)-get_global_pos_y(h); if(Vector2(dx,dy).length()<=aoe_range){ int dmg=(int)((double)kit_skill_damage(h)*mult); kit_hit(h,e,dmg,get_team(h),h,school); } } }")
    cpp.append("}")
    cpp.append("")

    cpp.append("bool MysticHeroSkills::boss_generic(Object* h, const String& skill_key, const Array& all_units, const Array& all_towers, const Array& all_bases) {")
    cpp.append("    // cooldown check")
    cpp.append("    if (skill_key==\"q\" && get_skill_timer(h)>0) return false;")
    cpp.append("    if (skill_key==\"w\" && get_w_cooldown(h)>0) return false;")
    cpp.append("    if (skill_key==\"e\" && get_e_cooldown(h)>0) return false;")
    cpp.append("    if (skill_key==\"r\" && get_r_cooldown(h)>0) return false;")
    cpp.append("    Array enemies = kit_enemies(h, all_units, all_towers, all_bases);")
    cpp.append("    double sr = get_skill_range(h); if (sr==0) sr=100; double cast_range = MAX((int)sr, 140);")
    cpp.append("    Array nearby; for(int i=0;i<enemies.size();++i){ Variant vv=enemies[i]; if(vv.get_type()!=Variant::OBJECT) continue; Object* e=Object::cast_to<Object>(vv); if(!e) continue; double dx=get_global_pos_x(e)-get_global_pos_x(h); double dy=get_global_pos_y(e)-get_global_pos_y(h); double d=Vector2(dx,dy).length(); if(d<=cast_range){ Array t; t.append(d); t.append(e); t.append(nearby.size()); nearby.append(t);} }")
    cpp.append("    if (nearby.size()==0) return false;")
    cpp.append("    // nearby.sort_custom(__by_pair0) di GDScript == Python nearby.sort(key=t[0])")
    cpp.append("    // yang STABIL: urutkan (dist, idx) dengan insertion sort — idx unik dan")
    cpp.append("    // naik, jadi hasilnya identik dengan sort stabil by-dist. (Sort tukar")
    cpp.append("    // pasangan ala bubble TIDAK stabil: musuh berjarak sama bisa tertukar,")
    cpp.append("    // target skill boss jadi beda dari pygame.)")
    cpp.append("    for (int i=1; i<nearby.size(); ++i) {")
    cpp.append("        Variant keyv = nearby[i]; Array ka = keyv; double kd = (double)ka[0]; int64_t ki = (int64_t)ka[2];")
    cpp.append("        int j = i - 1;")
    cpp.append("        while (j >= 0) {")
    cpp.append("            Array ja = nearby[j]; double jd = (double)ja[0]; int64_t ji = (int64_t)ja[2];")
    cpp.append("            if (!(kd < jd || (kd == jd && ki < ji))) break;")
    cpp.append("            nearby[j+1] = nearby[j]; --j;")
    cpp.append("        }")
    cpp.append("        nearby[j+1] = keyv;")
    cpp.append("    }")
    cpp.append("    Object* tgt=get_target(h); bool valid=false; if(tgt && kit_unit_alive(h,tgt)){ double dx=get_global_pos_x(tgt)-get_global_pos_x(h); double dy=get_global_pos_y(tgt)-get_global_pos_y(h); if(Vector2(dx,dy).length()<=cast_range) valid=true; }")
    cpp.append("    if(!valid){ Object* best = Object::cast_to<Object>(((Array)nearby[0])[1]); set_target(h, best); }")
    cpp.append("    // check recipe")
    cpp.append("    String ht = get_hero_type(h);")
    cpp.append("    bool has_recipe = false;")
    cpp.append("    // list of recipe types")
    cpp.append("    const char* recipes[] = {")
    for rt in sorted(registry.keys()):
        cpp.append(f'        "{rt}",')
    cpp.append("        nullptr")
    cpp.append("    };")
    cpp.append("    for(int i=0;recipes[i]!=nullptr;++i) if (ht==recipes[i]) { has_recipe=true; break; }")
    cpp.append("    if (!has_recipe) { fallback_cast(h, enemies, skill_key); if (skill_key==\"q\") trigger_q(h,\"boss\",10); else if (skill_key==\"w\") trigger_w(h,\"boss\",8); else if (skill_key==\"e\") trigger_e(h,\"boss\",8); else trigger_r(h,\"boss\",15); return true; }")
    cpp.append("    bool ok = registry_dispatch(h, skill_key, enemies); if (!ok) return false;")
    cpp.append("    if (skill_key==\"q\") trigger_q(h,\"boss\",10); else if (skill_key==\"w\") trigger_w(h,\"boss\",8); else if (skill_key==\"e\") trigger_e(h,\"boss\",8); else trigger_r(h,\"boss\",15); return true;")
    cpp.append("}")
    cpp.append("")

    # registry dispatch
    cpp.append("bool MysticHeroSkills::registry_dispatch(Object* h, const String& skill_key, const Array& enemies) {")
    cpp.append("    String ht = get_hero_type(h);")
    for hero_type in sorted(registry.keys()):
        recipe = registry[hero_type]
        cpp.append(f'    if (ht=="{hero_type}") {{')
        for key in ("q","w","e","r"):
            if key not in recipe:
                cpp.append(f'        if (skill_key=="{key}") return false;')
                continue
            mname = recipe[key]
            fname = em.fname("BossHeroSkills", mname)
            # arity
            fn_node = boss_cls["methods"][mname]
            arity = len(fn_node.args.args)-1
            if arity==1:
                cpp.append(f'        if (skill_key=="{key}") {{ {fname}(h); return true; }}')
            else:
                cpp.append(f'        if (skill_key=="{key}") {{ {fname}(h, enemies); return true; }}')
        cpp.append("        return false;")
        cpp.append("    }")
    cpp.append("    return false;")
    cpp.append("}")
    cpp.append("")

    cpp.append("void MysticHeroSkills::init_state(Object* h) {")
    cpp.append("    String kind = hero_kind(h);")
    cpp.append("    // reset kit")
    cpp.append("    set_kit(h, Dictionary());")
    cpp.append("    if (kind==\"grimjaw\") grimjaw_init_state(h);")
    cpp.append("    else if (kind==\"kaizen\") kaizen_init_state(h);")
    cpp.append("    else if (kind==\"sylara\") sylara_init_state(h);")
    cpp.append("    else if (kind==\"thorne\") thorne_init_state(h);")
    cpp.append("    else if (kind==\"vex\") vex_init_state(h);")
    cpp.append("    else if (kind==\"zephyr\") zephyr_init_state(h);")
    cpp.append("    else bosshero_init_state(h);")
    cpp.append("}")
    cpp.append("void MysticHeroSkills::update_timers(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {")
    cpp.append("    String kind = hero_kind(h);")
    cpp.append("    if (kind==\"grimjaw\") grimjaw_update_timers(h, all_units, all_towers, all_bases);")
    cpp.append("    else if (kind==\"kaizen\") kaizen_update_timers(h, all_units, all_towers, all_bases);")
    cpp.append("    else if (kind==\"sylara\") sylara_update_timers(h, all_units, all_towers, all_bases);")
    cpp.append("    else if (kind==\"thorne\") thorne_update_timers(h, all_units, all_towers, all_bases);")
    cpp.append("    else if (kind==\"vex\") vex_update_timers(h, all_units, all_towers, all_bases);")
    cpp.append("    else if (kind==\"zephyr\") zephyr_update_timers(h, all_units, all_towers, all_bases);")
    cpp.append("    else bosshero_update_timers(h, all_units, all_towers, all_bases);")
    cpp.append("}")
    cpp.append("bool MysticHeroSkills::cast_q(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {")
    cpp.append("    String kind = hero_kind(h);")
    cpp.append("    if (kind==\"grimjaw\") return grimjaw_cast_q(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"kaizen\") return kaizen_cast_q(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"sylara\") return sylara_cast_q(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"thorne\") return thorne_cast_q(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"vex\") return vex_cast_q(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"zephyr\") return zephyr_cast_q(h, all_units, all_towers, all_bases);")
    cpp.append("    return boss_generic(h, \"q\", all_units, all_towers, all_bases);")
    cpp.append("}")
    cpp.append("bool MysticHeroSkills::cast_w(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {")
    cpp.append("    String kind = hero_kind(h);")
    cpp.append("    if (kind==\"grimjaw\") return grimjaw_cast_w(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"kaizen\") return kaizen_cast_w(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"sylara\") return sylara_cast_w(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"thorne\") return thorne_cast_w(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"vex\") return vex_cast_w(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"zephyr\") return zephyr_cast_w(h, all_units, all_towers, all_bases);")
    cpp.append("    return boss_generic(h, \"w\", all_units, all_towers, all_bases);")
    cpp.append("}")
    cpp.append("bool MysticHeroSkills::cast_e(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {")
    cpp.append("    String kind = hero_kind(h);")
    cpp.append("    if (kind==\"grimjaw\") return grimjaw_cast_e(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"kaizen\") return kaizen_cast_e(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"sylara\") return sylara_cast_e(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"thorne\") return thorne_cast_e(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"vex\") return vex_cast_e(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"zephyr\") return zephyr_cast_e(h, all_units, all_towers, all_bases);")
    cpp.append("    return boss_generic(h, \"e\", all_units, all_towers, all_bases);")
    cpp.append("}")
    cpp.append("bool MysticHeroSkills::cast_r(Object* h, const Array& all_units, const Array& all_towers, const Array& all_bases) {")
    cpp.append("    String kind = hero_kind(h);")
    cpp.append("    if (kind==\"grimjaw\") return grimjaw_cast_r(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"kaizen\") return kaizen_cast_r(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"sylara\") return sylara_cast_r(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"thorne\") return thorne_cast_r(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"vex\") return vex_cast_r(h, all_units, all_towers, all_bases);")
    cpp.append("    if (kind==\"zephyr\") return zephyr_cast_r(h, all_units, all_towers, all_bases);")
    cpp.append("    return boss_generic(h, \"r\", all_units, all_towers, all_bases);")
    cpp.append("}")
    cpp.append("")

    # Elemen pembanding = [dist, entity, idx] (dibangun boss_generic, sama
    # dengan nearby.append([d, e, nearby.size()]) di GDScript). Python
    # `nearby.sort(key=lambda t: t[0])` STABIL; GDScript meniru lewat
    # tie-break idx di HeroSkillKit.__by_pair0 — C++ harus sama, kalau tidak
    # musuh berjarak sama bisa terpilih dalam urutan berbeda (target skill
    # beda = damage beda).
    cpp.append("bool MysticHeroSkills::by_pair0(Variant a, Variant b) {")
    cpp.append("    Array aa = a; Array bb = b;")
    cpp.append("    if (aa.size() < 3 || bb.size() < 3) { double av = aa.size() > 0 ? (double)aa[0] : 0.0; double bv = bb.size() > 0 ? (double)bb[0] : 0.0; return av < bv; }")
    cpp.append("    double ad = (double)aa[0]; double bd = (double)bb[0];")
    cpp.append("    if (ad == bd) return (int64_t)aa[2] < (int64_t)bb[2];")
    cpp.append("    return ad < bd;")
    cpp.append("}")
    cpp.append("bool MysticHeroSkills::__by_pair0(Variant a, Variant b) { return by_pair0(a,b); }")
    cpp.append("")
    cpp.append("void MysticHeroSkills::_bind_methods() {")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"init_state\", \"hero\"), &MysticHeroSkills::init_state);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"update_timers\", \"hero\", \"all_units\", \"all_towers\", \"all_bases\"), &MysticHeroSkills::update_timers);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"cast_q\", \"hero\", \"all_units\", \"all_towers\", \"all_bases\"), &MysticHeroSkills::cast_q);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"cast_w\", \"hero\", \"all_units\", \"all_towers\", \"all_bases\"), &MysticHeroSkills::cast_w);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"cast_e\", \"hero\", \"all_units\", \"all_towers\", \"all_bases\"), &MysticHeroSkills::cast_e);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"cast_r\", \"hero\", \"all_units\", \"all_towers\", \"all_bases\"), &MysticHeroSkills::cast_r);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"hero_kind\", \"hero\"), &MysticHeroSkills::hero_kind);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"skill_range\", \"hero\", \"fallback\"), &MysticHeroSkills::skill_range, DEFVAL(200.0));")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"has_target\", \"hero\", \"all_units\", \"all_towers\", \"all_bases\", \"range_val\"), &MysticHeroSkills::has_target, DEFVAL(Variant()));")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"visual_duration\", \"hero_type\", \"key\"), &MysticHeroSkills::visual_duration);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"boss_generic\", \"hero\", \"skill_key\", \"all_units\", \"all_towers\", \"all_bases\"), &MysticHeroSkills::boss_generic);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"by_pair0\", \"a\", \"b\"), &MysticHeroSkills::by_pair0);")
    cpp.append("    ClassDB::bind_static_method(\"MysticHeroSkills\", D_METHOD(\"__by_pair0\", \"a\", \"b\"), &MysticHeroSkills::__by_pair0);")
    cpp.append("}")

    cpp_text = "\n".join(cpp)

    if check:
        # Mode --check: JANGAN tulis apa pun. Bandingkan hasil transpile dengan
        # berkas yang ter-commit supaya CI tahu kapan hero_skills/_bundle.py
        # berubah tanpa C++ GDExtension ikut dibangkitkan ulang (pola sama
        # dengan tools/gen_hero_skill_kit.py --check).
        stale = []
        for path, text in ((OUT_H, header_text), (OUT_CPP, cpp_text)):
            old = path.read_text(encoding="utf-8") if path.exists() else ""
            if old != text:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            for rel in stale:
                print(f"[gen_cpp] BASI: {rel} != hasil transpile hero_skills/_bundle.py")
            print("[gen_cpp] regenerasi: python3 tools/gen_hero_skills_cpp.py")
            sys.exit(1)
        print("[gen_cpp] PASS: hero_skills_processor.h/.cpp ter-commit == hasil transpile "
              f"({cpp_text.count(chr(10)) + 1} baris cpp, "
              f"{cpp_text.count('MysticHeroSkills::')} definisi)")
        return

    OUT_H.parent.mkdir(parents=True, exist_ok=True)
    OUT_H.write_text(header_text, encoding="utf-8")
    OUT_CPP.write_text(cpp_text, encoding="utf-8")
    print(f"[gen_cpp] wrote {OUT_H.relative_to(ROOT)} ({header_text.count(chr(10)) + 1} baris)")
    print(f"[gen_cpp] wrote {OUT_CPP.relative_to(ROOT)} ({cpp_text.count(chr(10)) + 1} baris, "
          f"{cpp_text.count('MysticHeroSkills::')} definisi, "
          f"{len(registry)} resep registry boss)")


def main():
    ap = argparse.ArgumentParser(
        description="Transpile hero_skills/_bundle.py -> C++ GDExtension (godot++)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 kalau hero_skills_processor.h/.cpp ter-commit basi")
    args = ap.parse_args()
    generate(check=args.check)


if __name__=="__main__":
    main()
