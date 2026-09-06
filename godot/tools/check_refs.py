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
        dirs[:] = [d for d in dirs if d not in (".godot", ".import")]
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
