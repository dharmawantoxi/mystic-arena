#!/usr/bin/env python3
"""check_refs — verifier statis untuk project Godot, tanpa perlu engine.

Dipakai karena "F5 layar hitam" sering BUKAN crash, tapi scene yang kosong:
path resource salah tulis, preload ke file yang tidak ada, atau
@onready $Node/Path yang tidak ada di .tscn (semuanya gagal senyap / cuma
menyisakan clear color). Checks:

  1. tiap [ext_resource] path di .tscn/.tres harus ada di disk
  2. tiap preload("res://...") / "res://..." literal di .gd harus ada di disk
  3. tiap $A/B (onready) dan get_node*(^"A/B") literal harus ada di scene
     yang memasang script itu (dilewati kalau script dipakai >1 scene)
  4. [connection] from/to harus merujuk node yang ada
  5. SceneTree method dipanggil di self tanpa get_tree() (Parser Error
     "Function get_nodes_in_group() not found in base self." — Autoload
     yang extends Node tidak punya method SceneTree)
  6. draw_ellipse() tidak ada di Godot 4.3 (baru di 4.6 dengan signature
     (Vector2, float, float, Color)); project target 4.3 harus pakai
     draw_colored_polygon / draw_circle fallback
  7. fungsi matematika bersuffiks "f" yang tidak ada di Godot 4 (sqrtf,
     sinf, atan2f, ...) — Parser Error "Function not found in base self",
     dan `var x := sqrtf(...)` ikut "Cannot infer the type of x"

Usage: python3 godot/tools/check_refs.py godot
Exit 0 = bersih, 1 = ada masalah.
"""
import os
import re
import sys

RES_RE = re.compile(r'res://[A-Za-z0-9_%./-]*')
PRELOAD_RE = re.compile(r'(?:preload|load)\(\s*"(res://[^"]+)"')
TAG_RE = re.compile(r'^\[(\w+)([^\]]*)\]', re.M)
ATTR_RE = re.compile(r'(\w+)=(".*?"|[^,]+)')
ONREADY_RE = re.compile(r'@onready\s+var\s+\w+(?:\s*:\s*[\w.\[\]]+)?\s*=\s*\$([A-Za-z0-9_/.%]+)')
GETNODE_RE = re.compile(r'get_node(?:_or_null)?\(\s*\^?"([^"]+)"')
DYNAMIC = re.compile(r'[%{}()]')

# 5 — SceneTree methods yang hanya ada di SceneTree, bukan di Node/self
SCENE_TREE_METHODS = [
    "get_nodes_in_group",
    "get_first_node_in_group",
    "call_group",
    "create_timer",
    "quit",
    "change_scene_to_file",
    "reload_current_scene",
]
# pre-compile bare-call regex: not preceded by '.' or alphanum/_
SCENE_TREE_RE = [
    (m, re.compile(r'(?<![A-Za-z0-9_\.])' + re.escape(m) + r'\s*\('))
    for m in SCENE_TREE_METHODS
]
DRAW_ELLIPSE_RE = re.compile(r'(?<![A-Za-z0-9_\.])draw_ellipse\s*\(')
# Fungsi matematika bersuffiks "f" yang TIDAK ADA di Godot 4. Godot hanya
# punya bentuk tanpa suffiks untuk keluarga ini (sqrt/exp/log/sin/cos/tan/
# atan/acos/asin) — memakai `sqrtf()` menghasilkan Parse Error dua kali
# sekaligus: 'Function "sqrtf()" not found in base self.' LALU
# 'Cannot infer the type of ... variable' karena nilai RHS jadi tanpa tipe.
# (Yang ADA: absf ceilf floorf roundf fmodf powf signf snappedf wrapf
#  lerpf maxf minf — jangan ikut diflag.)
NO_F_SUFFIX_MATH = (
    "sqrtf", "hypotf", "expf", "logf",
    "sinf", "cosf", "tanf", "atanf", "atan2f", "acosf", "asinf",
)
NO_F_SUFFIX_MATH_RE = [
    (fn, re.compile(r'(?<![A-Za-z0-9_\.])' + fn + r'\s*\('))
    for fn in NO_F_SUFFIX_MATH
]


def res_to_fs(root, res_path):
    return os.path.normpath(os.path.join(root, res_path[len("res://"):]))

def parse_tags(text):
    out = []
    for m in TAG_RE.finditer(text):
        attrs = {}
        for name, raw in ATTR_RE.findall(m.group(2)):
            attrs[name] = raw.strip('"')
        out.append((m.group(1), attrs))
    return out

def scene_nodes(path):
    """NodePaths yang ada di scene ini (root = ""), termasuk node instanced."""
    text = open(path, encoding="utf-8").read()
    names = set()
    for tag, a in parse_tags(text):
        if tag != "node" or "name" not in a:
            continue
        name = a["name"]
        parent = a.get("parent", "")
        if parent in (".", ""):
            names.add("")
            names.add(name)
        else:
            names.add(f"{parent}/{name}")
            names.add(name)  # sering diakses pakai nama saja
    return names, text

def script_of_scene(text):
    for tag, a in parse_tags(text):
        if tag == "node" and not a.get("parent") and "script" in a:
            return a["script"]
    return None


def check(root):
    problems = []
    scenes, scripts = [], []
    for dirpath, dirs, files in os.walk(root):
        # "godot-cpp" = checkout sumber GDExtension (di-gitignore, ada hanya di
        # mesin yang membuild lib / di CI godot-gdext.yml). Ia membawa project
        # contoh sendiri (test/project/*.tscn -> res://main.gd) yang res://-nya
        # relatif ke project ITU, bukan ke project ini, jadi selalu tampak
        # sebagai ext_resource hilang. Bukan bug repo -> dilewati.
        dirs[:] = [d for d in dirs if d not in (".godot", ".import", "godot-cpp")]
        for f in files:
            p = os.path.join(dirpath, f)
            if f.endswith((".tscn", ".tres")):
                scenes.append(p)
            elif f.endswith(".gd"):
                scripts.append(p)

    # res:// -> path .gd (buat mapping script->scene)
    res_of = {os.path.normpath(p): "res://" + os.path.relpath(p, root).replace(os.sep, "/")
              for p in scenes + scripts}
    script_scenes = {}
    for sc in scenes:
        _n, text = scene_nodes(sc)
        for tag, a in parse_tags(text):
            if tag == "ext_resource" and a.get("type") == "Script":
                gd = os.path.normpath(res_to_fs(root, a["path"]))
                script_scenes.setdefault(gd, []).append(sc)

    # 1 + 4: scenes
    for sc in scenes:
        names, text = scene_nodes(sc)
        rel = os.path.relpath(sc, root)
        for tag, a in parse_tags(text):
            if tag == "ext_resource":
                target = res_to_fs(root, a.get("path", ""))
                if not os.path.exists(target):
                    problems.append(f"{rel}: ext_resource tidak ada -> {a.get('path')}")
            elif tag == "connection":
                for key in ("from", "to"):
                    ref = a.get(key, "")
                    if not ref or ref.startswith("[") or not ref[0].isalpha():
                        continue
                    head = ref.split("/")[0]
                    if head not in names:
                        problems.append(f"{rel}: [connection] {key}='{ref}' node '{head}' tidak ada")
        # script root harus ada
        entry = script_of_scene(text)
        if entry:
            pass

    for gd in scripts:
        rel = os.path.relpath(gd, root)
        text = open(gd, encoding="utf-8").read()
        # 2: preload/load + literal res://
        for res in sorted(set(PRELOAD_RE.findall(text)) | set(RES_RE.findall(text))):
            if DYNAMIC.search(res):
                continue  # path dibentuk runtime, tidak bisa dicek statis
            if not res.endswith((".tres", ".tscn", ".png", ".jpg", ".svg", ".wav", ".ogg",
                                 ".gd", ".json", ".ttf", ".gdshader", ".otf")):
                continue
            if not os.path.exists(res_to_fs(root, res)):
                problems.append(f"{rel}: path resource tidak ada -> {res}")
        # 3: node path literal
        scenes_for = script_scenes.get(os.path.normpath(gd), [])
        if len(scenes_for) == 1:
            names, _t = scene_nodes(scenes_for[0])
            for pat in sorted(set(ONREADY_RE.findall(text)) | set(GETNODE_RE.findall(text))):
                pat = pat.rstrip("/")
                if not pat or DYNAMIC.search(pat):
                    continue
                if pat not in names:
                    problems.append(f"{rel}: node '{pat}' tidak ada di {os.path.relpath(scenes_for[0], root)}")

        # 5 & 6: static GDScript checks (tanpa engine) — kelas bug Parser Error
        # a) count_alive() harus lewat get_tree() dengan guard tree == null
        if re.search(r'\bfunc\s+count_alive\s*\(', text):
            # guard harus ada: get_tree() dan pengecekan null di fungsi tersebut
            # Ekstrak block fungsi count_alive (hingga func berikutnya atau akhir file)
            m = re.search(r'func\s+count_alive\s*\(.*?\)\s*(?:->\s*\w+\s*)?:\s*\n(.*?)(?=\nfunc\s|\Z)', text, re.S)
            block = m.group(1) if m else ""
            if 'get_tree()' not in block:
                problems.append(
                    f"{rel}: count_alive() harus lewat get_tree() (contoh: var tree := get_tree(); if tree == null: return 0; tree.get_nodes_in_group(...)) — "
                    f"tanpa get_tree() akan Parser Error 'Function \"get_nodes_in_group()\" not found in base self.'"
                )
            elif '== null' not in block and '==null' not in block and 'tree == null' not in block:
                problems.append(
                    f"{rel}: count_alive() harus guard kalau tree == null (autoload bisa terpanggil sebelum SceneTree siap) — "
                    f"tambahkan 'var tree := get_tree(); if tree == null: return 0'"
                )
            elif 'get_nodes_in_group' in block and 'tree.get_nodes_in_group' not in block and 'get_tree().get_nodes_in_group' not in block:
                problems.append(
                    f"{rel}: count_alive() masih memanggil get_nodes_in_group() di self — ganti dengan tree.get_nodes_in_group() / get_tree().get_nodes_in_group()"
                )
        # b) baris-per-baris: SceneTree method di self + draw_ellipse 4.3
        # Strip string literals dulu supaya pola di dalam string tidak ke-flag,
        # lalu buang komentar '#' supaya tidak false positive di comment.
        lines = text.splitlines()
        for idx, raw_line in enumerate(lines, start=1):
            # hapus string literals " ... " dan ' ... ' (ganti dengan "")
            no_str = re.sub(r'"(?:\\.|[^"\\])*"', '""', raw_line)
            no_str = re.sub(r"'(?:\\.|[^'\\])*'", "''", no_str)
            code = no_str.split('#', 1)[0]
            if not code.strip():
                continue
            # 5: SceneTree method dipanggil di self (tanpa get_tree() / tree.)
            # Deteksi bare call: tidak diawali '.' (artinya bukan tree.get_nodes... atau get_tree().get_nodes...)
            # Jika ada get_tree() di baris yang sama tapi panggilan tetap bare (tanpa dot), itu tetap bug.
            for method, pat in SCENE_TREE_RE:
                if not pat.search(code):
                    continue
                # skip kalau ini definisi fungsi: "func get_nodes_in_group(...)"
                if re.search(r'\bfunc\s+' + re.escape(method) + r'\b', code):
                    continue
                # skip kalau ada prefix yang sah: "get_tree().method" sudah tidak match karena dot,
                # tapi "tree.method" juga tidak match. Jadi bare match = error.
                # Untuk pesan yang lebih jelas, tambahkan hint.
                # Khusus quit: bare quit() -> harus get_tree().quit(), jangan flag Engine.quit()
                # Engine.quit() punya dot, jadi sudah ter-filter.
                problems.append(
                    f"{rel}:{idx}: SceneTree.{method}() dipanggil di self (tanpa get_tree()) — "
                    f"Parser Error 'Function \"{method}()\" not found in base self.' "
                    f"(Autoload extends Node, method ada di SceneTree -> pakai get_tree().{method}() atau var tree := get_tree(); if tree == null: return)"
                )
            # 7: fungsi matematika bersuffiks "f" yang tidak ada di Godot 4
            for fn, pat in NO_F_SUFFIX_MATH_RE:
                if not pat.search(code):
                    continue
                if re.search(r'\bfunc\s+' + re.escape(fn) + r'\b', code):
                    continue
                problems.append(
                    f"{rel}:{idx}: {fn}() tidak ada di Godot 4 (hanya {fn[:-1]}() yang ada) "
                    f"— Parser Error 'Function \"{fn}()\" not found in base self.' dan, kalau hasilnya "
                    f"dipakai `var x := {fn}(...)`, ikut 'Cannot infer the type of \"x\" variable'"
                )
            # 6: draw_ellipse() kompatibilitas Godot 4.3
            if DRAW_ELLIPSE_RE.search(code):
                # skip definisi func draw_ellipse jika ada (tidak ada di project, tapi jaga)
                if re.search(r'\bfunc\s+draw_ellipse\b', code):
                    continue
                problems.append(
                    f"{rel}:{idx}: draw_ellipse() tidak ada di Godot 4.3 (baru di 4.6 dengan signature (Vector2, float, float, Color)) "
                    f"— ganti dengan draw_colored_polygon/draw_arc fallback (contoh: PackedVector2Array 32 titik + draw_colored_polygon) "
                    f"atau upgrade project ke 4.6"
                )
    return problems


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    root = argv[1].rstrip("/")
    if not os.path.exists(os.path.join(root, "project.godot")):
        print(f"{root}: tidak ada project.godot di sini")
        return 2
    problems = check(root)
    for p in problems:
        print("ERROR", p)
    if not problems:
        print("OK — semua ext_resource, preload, dan node path konsisten dengan .tscn")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
