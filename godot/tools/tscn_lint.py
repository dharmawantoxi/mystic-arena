#!/usr/bin/env python3
"""tscn_lint — strict validator for Godot 4.x text scenes/resources (.tscn/.tres).

Mirrors the engine-side parsers:
  - core/variant/variant_parser.cpp  (tokenizer + parse_value grammar)
  - scene/resources/resource_format_text.cpp  (tag grammar + required fields)

Key rule people trip over when hand-writing scenes:
  constructor arguments in text resources accept ONLY numbers
  (e.g. Transform2D requires 6 plain numbers — Vector2(...) inside is FATAL).

Usage: python3 tscn_lint.py file.tscn [file2.tscn ...]
Exit code 0 = all valid, 1 = at least one error (Godot would refuse to load it).
"""
import re
import sys

# ---------------------------------------------------------------- tokens
TK_EOF, TK_ERROR = "EOF", "ERROR"
TK_NUMBER, TK_STRING, TK_STRING_NAME, TK_COLOR = "NUMBER", "STRING", "STRING_NAME", "COLOR"
TK_IDENTIFIER = "IDENTIFIER"
TK_PAREN_O, TK_PAREN_C = "(", ")"
TK_BRACK_O, TK_BRACK_C = "[", "]"
TK_CURLY_O, TK_CURLY_C = "{", "}"
TK_COLON, TK_COMMA, TK_PERIOD, TK_EQUAL = ":", ",", ".", "="


class ParseError(Exception):
    def __init__(self, line, msg):
        super().__init__(f"line {line}: {msg}")
        self.line = line
        self.msg = msg


class Stream:
    """Char stream with one-char pushback, mirroring VariantParser::Stream."""

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.saved = None

    def get_char(self):
        if self.saved is not None:
            ch, self.saved = self.saved, None
            if ch == "\n":
                self.line += 1
            return ch
        if self.pos >= len(self.text):
            return ""
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def unget(self, ch):
        if ch:
            if ch == "\n":
                self.line -= 1
            self.saved = ch

    def eof(self):
        return self.saved is None and self.pos >= len(self.text)


_HEX = set("0123456789abcdefABCDEF")
_ESCAPES = {"b": "\b", "t": "\t", "n": "\n", "f": "\f", "r": "\r",
            "'": "'", '"': '"', "\\": "\\", "/": "/"}


def get_token(s):
    """Mirror VariantParser::get_token (subset used by text resources)."""
    while True:
        c = s.get_char()
        if c == "":
            return (TK_EOF, None)
        if ord(c) <= 32:
            continue
        if c == ";":  # comment (text format uses ';', not '#')
            while True:
                ch = s.get_char()
                if ch in ("", "\n"):
                    break
            continue
        if c == "#":  # TK_COLOR, e.g. #ff00ff
            buf = ["#"]
            while True:
                ch = s.get_char()
                if ch and ch in _HEX:
                    buf.append(ch)
                else:
                    s.unget(ch)
                    break
            return (TK_COLOR, "".join(buf))
        if c in "()[]{},:.=":
            return (c, c)
        if c == '"':  # plain string; '&"..."' (StringName) handled by caller
            buf = []
            while True:
                ch = s.get_char()
                if ch == "":
                    raise ParseError(s.line, "Unterminated String")
                if ch == '"':
                    break
                if ch == "\\":
                    nxt = s.get_char()
                    if nxt == "":
                        raise ParseError(s.line, "Unterminated String")
                    if nxt == "u":  # simplified \uXXXX
                        digits = ""
                        for _ in range(4):
                            d = s.get_char()
                            if not (d and d in _HEX):
                                raise ParseError(s.line, "Malformed hex constant in string")
                            digits += d
                        buf.append(chr(int(digits, 16)))
                    elif nxt in _ESCAPES:
                        buf.append(_ESCAPES[nxt])
                    else:
                        raise ParseError(s.line, f"Invalid escape character '{nxt}' in string")
                else:
                    buf.append(ch)
            return (TK_STRING, "".join(buf))
        if c == "&":
            c2 = s.get_char()
            if c2 != '"':
                raise ParseError(s.line, "Expected '\"' after '&'")
            s.unget(c2)
            tk, val = get_token(s)
            if tk != TK_STRING:
                raise ParseError(s.line, "Expected string after '&'")
            return (TK_STRING_NAME, val)
        if c == "-" or c.isdigit():
            # number: -? digits [. digits] [e[+-]digits]  | 0x hex
            buf = [c]
            if c == "-":
                c = s.get_char()
                buf.append(c)
            if c == "0":
                c = s.get_char()
                if c in ("x", "X"):
                    hexbuf = []
                    while True:
                        ch = s.get_char()
                        if ch and ch in _HEX:
                            hexbuf.append(ch)
                        else:
                            s.unget(ch)
                            break
                    if not hexbuf:
                        raise ParseError(s.line, "Malformed numeric constant")
                    return (TK_NUMBER, int("".join(hexbuf), 16))
                s.unget(c)
            state = "int"
            while True:
                ch = s.get_char()
                if state == "int":
                    if ch.isdigit():
                        buf.append(ch)
                        continue
                    if ch == ".":
                        state = "dec"
                        buf.append(ch)
                        continue
                    if ch == "e":
                        state = "exp_wait"
                        buf.append(ch)
                        continue
                elif state == "dec":
                    if ch.isdigit():
                        buf.append(ch)
                        continue
                    if ch == "e":
                        state = "exp_wait"
                        buf.append(ch)
                        continue
                elif state == "exp_wait":
                    if ch in ("-", "+") or ch.isdigit():
                        state = "exp"
                        buf.append(ch)
                        continue
                elif state == "exp":
                    if ch.isdigit():
                        buf.append(ch)
                        continue
                s.unget(ch)
                break
            text = "".join(buf)
            try:
                return (TK_NUMBER, float(text) if ("." in text or "e" in text) else int(text))
            except ValueError:
                raise ParseError(s.line, f"Malformed numeric constant '{text}'")
        if c.isalpha() or c == "_":
            buf = [c]
            first = True
            while True:
                ch = s.get_char()
                if ch.isalpha() or ch == "_" or (not first and ch.isdigit()):
                    buf.append(ch)
                    first = False
                else:
                    s.unget(ch)
                    break
            return (TK_IDENTIFIER, "".join(buf))
        raise ParseError(s.line, f"Unexpected character {repr(c)}")


# ---------------------------------------------------------------- values
# identifier -> ("numbers constructor", arg count or None)
_CONSTRUCTS = {
    "Vector2": 2, "Vector2i": 2, "Vector3": 3, "Vector3i": 3,
    "Vector4": 4, "Vector4i": 4,
    "Rect2": 4, "Rect2i": 4,
    "Transform2D": 6, "Matrix32": 6,
    "Plane": 4, "Quaternion": 4, "Quat": 4,
    "AABB": 6, "Rect3": 6,
    "Basis": 9, "Matrix3": 9,
    "Transform3D": 12, "Transform": 12,
    "Projection": 16,
    "Color": 4,
}
_PACKED_NUM = {  # packed arrays built from a plain number list
    "PackedByteArray", "PoolByteArray", "ByteArray",
    "PackedInt32Array", "PackedIntArray", "PoolIntArray", "IntArray",
    "PackedInt64Array",
    "PackedFloat32Array", "PackedRealArray", "PoolRealArray", "FloatArray",
    "PackedFloat64Array",
    "PackedVector2Array", "PoolVector2Array", "Vector2Array",
    "PackedVector3Array", "PoolVector3Array", "Vector3Array",
    "PackedVector4Array", "PoolVector4Array", "Vector4Array",
    "PackedColorArray", "PoolColorArray", "ColorArray",
}
_PACKED_STR = {"PackedStringArray", "PoolStringArray", "StringArray"}
_BARE_VALUES = {"true", "false", "null", "nil", "inf", "inf_neg", "nan"}


def _parse_construct_numbers(s):
    """VariantParser::_parse_construct — numbers ONLY; identifiers/nesting are FATAL."""
    tk, val = get_token(s)
    if tk != "(":
        raise ParseError(s.line, "Expected '(' in constructor")
    first = True
    n = 0
    while True:
        if not first:
            tk, val = get_token(s)
            if tk == ")":
                break
            if tk != ",":
                raise ParseError(s.line, "Expected ',' or ')' in constructor")
        tk, val = get_token(s)
        if first and tk == ")":
            break
        if tk != TK_NUMBER:
            if tk == TK_IDENTIFIER and val in ("inf", "inf_neg", "nan"):
                pass  # stor_fix() special cases
            else:
                # THE KaizenSkeleton bug lands here: Vector2 inside Transform2D().
                raise ParseError(s.line, "Expected float in constructor")
        n += 1
        first = False
    return n


def parse_value(s, tk=None, val=None):
    """VariantParser::parse_value."""
    if tk is None:
        tk, val = get_token(s)
    if tk == "{":
        while True:
            tk2, v2 = get_token(s)
            if tk2 == "}":
                return
            if len(_dict_items(s, tk2, v2)) and False:
                pass
            _dict_key(s, tk2, v2)
            tk3, _ = get_token(s)
            if tk3 != ":":
                raise ParseError(s.line, "Expected ':'")
            parse_value(s)
            tk4, _ = get_token(s)
            if tk4 == "}":
                return
            if tk4 != ",":
                raise ParseError(s.line, "Expected '}' or ','")
    elif tk == "[":
        first = True
        while True:
            tk2, _ = get_token(s)
            if tk2 == "]":
                return
            if not first:
                if tk2 != ",":
                    raise ParseError(s.line, "Expected ']' or ','")
                tk3, v3 = get_token(s)
                if tk3 == "]":
                    raise ParseError(s.line, "Not expecting ']'")
                parse_value(s, tk3, v3)
            else:
                parse_value(s, tk2, _)
            first = False
    elif tk == TK_IDENTIFIER:
        if val in _BARE_VALUES:
            return
        if val in _CONSTRUCTS:
            n = _parse_construct_numbers(s)
            if n != _CONSTRUCTS[val]:
                raise ParseError(
                    s.line, f"Expected {_CONSTRUCTS[val]} arguments for constructor")
            return
        if val in _PACKED_NUM:
            _parse_construct_numbers(s)
            return
        if val in _PACKED_STR:
            tk2, _ = get_token(s)
            if tk2 != "(":
                raise ParseError(s.line, "Expected '('")
            first = True
            while True:
                if not first:
                    tk2, _ = get_token(s)
                    if tk2 == ")":
                        break
                    if tk2 != ",":
                        raise ParseError(s.line, "Expected ',' or ')'")
                tk2, _ = get_token(s)
                if tk2 == ")":
                    break
                if tk2 != TK_STRING:
                    raise ParseError(s.line, "Expected string")
                first = False
            return
        if val in ("ExtResource", "SubResource"):
            tk2, _ = get_token(s)
            if tk2 != "(":
                raise ParseError(s.line, "Expected '('")
            tk3, _ = get_token(s)
            if tk3 != TK_STRING:
                raise ParseError(s.line, "Expected string")
            tk4, _ = get_token(s)
            if tk4 != ")":
                raise ParseError(s.line, "Expected ')'")
            return
        if val in ("NodePath", "StringName", "RID", "Signal", "Callable", "Resource"):
            _parse_one_paren_value(s)
            return
        raise ParseError(s.line, f"Unexpected identifier: '{val}'.")
    elif tk in (TK_NUMBER, TK_STRING, TK_STRING_NAME, TK_COLOR):
        return
    else:
        raise ParseError(s.line, f"Expected value, got {tk}.")


def _dict_key(s, tk, val):
    if tk in (TK_STRING, TK_NUMBER, TK_STRING_NAME, TK_COLOR):
        return
    raise ParseError(s.line, "Expected dictionary key")


def _parse_one_paren_value(s):
    tk, _ = get_token(s)
    if tk != "(":
        raise ParseError(s.line, "Expected '('")
    tk, val = get_token(s)
    if tk == ")":  # RID(), Signal(), Callable() permit empty
        return
    if tk not in (TK_STRING, TK_NUMBER, TK_STRING_NAME, TK_IDENTIFIER):
        raise ParseError(s.line, "Expected value in constructor")
    tk, _ = get_token(s)
    if tk != ")":
        raise ParseError(s.line, "Expected ')'")


# ---------------------------------------------------------------- tags
def parse_tag(s):
    """VariantParser::parse_tag -> (name, fields); '[' already consumed."""
    name_tk, name = get_token(s)
    if name_tk != TK_IDENTIFIER:
        raise ParseError(s.line, "Expected tag name")
    fields = {}
    while True:
        tk, val = get_token(s)
        if tk == "]":
            break
        if tk not in (TK_IDENTIFIER, TK_STRING):
            raise ParseError(s.line, "Expected tag field name")
        key = val
        tk, _ = get_token(s)
        if tk != "=":
            raise ParseError(s.line, "Expected '=' after tag field")
        parse_value(s)
        fields[key] = True
    return name, fields


def lint(text, path):
    """Scene-level checks per ResourceLoaderText::load()."""
    s = Stream(text)
    tk, _ = get_token(s)
    if tk != "[":
        raise ParseError(1, "Expected '[gd_scene ...]' header tag")
    name, fields = parse_tag(s)
    if name not in ("gd_scene", "gd_resource"):
        raise ParseError(1, f"Unrecognized file type: {name}")

    required = {"ext_resource": ("path", "type", "id"),
                "sub_resource": ("type", "id"),
                "node": ("name",),
                "connection": ("from", "to", "signal", "method"),
                "editable": ("path",)}
    allowed_order = {"gd_scene": ("ext_resource", "sub_resource", "node", "connection", "editable"),
                     "gd_resource": ("ext_resource", "sub_resource", "resource")}
    order = allowed_order[name]
    stage = 0
    while True:
        # skip blank space/comments until next tag or assign or EOF
        tk, _ = get_token(s)
        if tk == TK_EOF:
            return []  # EOF terminates a scene/resource normally
        if tk == TK_COLOR:
            raise ParseError(
                s.line, "'#' does not start a comment in .tscn files "
                        "(use ';' — '#' starts a color literal and swallows "
                        "the following lines)")
        if tk == "[":
            tname, tfields = parse_tag(s)
            if tname not in order:
                raise ParseError(s.line, f"Unexpected tag '{tname}'")
            idx = order.index(tname)
            if idx < stage:
                raise ParseError(s.line, f"Tag '{tname}' out of order")
            stage = idx
            for req in required.get(tname, ()):
                if req not in tfields:
                    raise ParseError(
                        s.line, f"Missing '{req}' in {tname} tag")
            if tname == "node":
                stage = 2  # allow connection/editable afterwards
            continue
        # otherwise: an assign line "name = value" (name may contain '/', '.', etc.)
        if tk in (TK_IDENTIFIER,):
            # read raw until '=' — mirrors parse_tag_assign_eof
            while True:
                ch = s.get_char()
                if ch == "":
                    raise ParseError(s.line, "Unexpected end of file")
                if ch == "=":
                    break
                if ch == "\n" and False:
                    break
            parse_value(s)
            continue
        raise ParseError(s.line, f"Unexpected token {tk}")


def main(argv):
    problems = 0
    for path in argv[1:]:
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"{path}: cannot read: {e}")
            problems += 1
            continue
        try:
            lint(text, path)
            print(f"OK    {path}")
        except ParseError as e:
            print(f"ERROR {path}:{e.line}: {e.msg}")
            problems += 1
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv))
