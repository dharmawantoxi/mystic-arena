#!/usr/bin/env python3
"""particles_lint — cegah properti CPUParticles2D/GPUParticles2D tertukar.

Kenapa ada: keduanya terlihat mirip, tapi API-nya BEDA TOTAL dan salahnya
tidak ketahuan sampai runtime — GDScript hanya melempar

    Invalid assignment of property or key 'process_material' with value of
    type 'ParticleProcessMaterial' on a base object of type 'CPUParticles2D'.

tepat saat FX-nya dipakai (misal proyektil skill membentur target), jadi bisa
lolos dari smoke test dan baru kelihatan di HP pemain.

Aturan yang dijaga:
  GPUParticles2D  -> semua parameter emisi ada di `process_material`
                     (ParticleProcessMaterial), pakai Vector3 + scale_min/max.
  CPUParticles2D  -> TIDAK punya `process_material`; parameter emisi adalah
                     properti node langsung, pakai Vector2 + scale_amount_min/max.

Yang diperiksa:
  1. .tscn : node CPUParticles2D memakai properti khusus GPU (dan sebaliknya)
  2. .tscn : properti vektor node CPUParticles2D ditulis Vector3(...)
  3. .gd   : variabel bertipe/hasil `CPUParticles2D.new()` di-assign properti
             khusus GPU (dan sebaliknya untuk GPUParticles2D)
  4. .gd   : properti Vector2 node CPU diberi Vector3(...) / sebaliknya

Usage: python3 godot/tools/particles_lint.py [root=godot]
Exit 0 = bersih, 1 = ada properti yang akan gagal saat runtime.
"""
import os
import re
import sys

# Properti yang HANYA ada di CPUParticles2D (di GPU pindah ke process_material)
CPU_ONLY = {
    "direction", "spread", "flatness",
    "initial_velocity_min", "initial_velocity_max",
    "angular_velocity_min", "angular_velocity_max",
    "orbit_velocity_min", "orbit_velocity_max",
    "linear_accel_min", "linear_accel_max",
    "radial_accel_min", "radial_accel_max",
    "tangential_accel_min", "tangential_accel_max",
    "damping_min", "damping_max",
    "angle_min", "angle_max",
    "scale_amount_min", "scale_amount_max", "scale_amount_curve",
    "split_scale", "scale_curve_x", "scale_curve_y",
    "color", "color_ramp", "color_initial_ramp",
    "hue_variation_min", "hue_variation_max",
    "anim_speed_min", "anim_speed_max",
    "anim_offset_min", "anim_offset_max",
    "gravity",
    "emission_shape", "emission_sphere_radius", "emission_rect_extents",
    "emission_points", "emission_normals", "emission_colors",
    "particle_flag_align_y", "particle_flag_rotate_y", "particle_flag_disable_z",
}

# Properti yang HANYA ada di GPUParticles2D
GPU_ONLY = {
    "process_material", "amount_ratio", "sub_emitter", "trail_enabled",
    "trail_lifetime", "trail_sections", "trail_section_subdivisions",
    "collision_base_size", "interp_to_end", "interpolate",
    "fract_delta", "visibility_rect", "texture_repeat_disabled",
}

# Properti node CPUParticles2D yang WAJIB Vector2 (di material GPU: Vector3)
CPU_VECTOR2 = {"direction", "gravity", "emission_rect_extents"}

CPU = "CPUParticles2D"
GPU = "GPUParticles2D"

problems = []


def report(path, line_no, msg):
    problems.append("%s:%d: %s" % (path, line_no, msg))


# ------------------------------------------------------------------ .tscn
NODE_RE = re.compile(r'^\[node name="([^"]+)" type="(\w+)"')
TAG_RE = re.compile(r"^\[")
PROP_RE = re.compile(r"^(\w+)\s*=\s*(.*)$")


def lint_tscn(path):
    kind = None
    for i, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if TAG_RE.match(line):
            m = NODE_RE.match(line)
            kind = m.group(2) if m and m.group(2) in (CPU, GPU) else None
            continue
        if kind is None:
            continue
        m = PROP_RE.match(line)
        if not m:
            continue
        prop, value = m.group(1), m.group(2)
        if kind == CPU and prop in GPU_ONLY:
            report(path, i, "node %s tidak punya properti '%s' (itu milik %s)"
                   % (CPU, prop, GPU))
        if kind == GPU and prop in CPU_ONLY:
            report(path, i, "node %s tidak punya properti '%s' — set lewat "
                            "process_material (ParticleProcessMaterial)" % (GPU, prop))
        if kind == CPU and prop in CPU_VECTOR2 and "Vector3(" in value:
            report(path, i, "%s.%s bertipe Vector2, bukan Vector3" % (CPU, prop))


# -------------------------------------------------------------------- .gd
NEW_RE = re.compile(r"\bvar\s+(\w+)\s*:?[\w\s]*=\s*(CPUParticles2D|GPUParticles2D)\.new\(\)")
TYPED_RE = re.compile(r"\bvar\s+(\w+)\s*:\s*(CPUParticles2D|GPUParticles2D)\b")
ASSIGN_RE = re.compile(r"\b(\w+)\.(\w+)\s*=\s*(.*)$")


def lint_gd(path):
    kinds = {}  # nama variabel -> CPU/GPU
    for i, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.split("#")[0].strip()
        if not line:
            continue
        for rx in (NEW_RE, TYPED_RE):
            m = rx.search(line)
            if m:
                kinds[m.group(1)] = m.group(2)
        m = ASSIGN_RE.search(line)
        if not m:
            continue
        var, prop, value = m.group(1), m.group(2), m.group(3)
        kind = kinds.get(var)
        if kind is None:
            continue
        if kind == CPU and prop in GPU_ONLY:
            report(path, i, "%s.%s tidak ada — %s memakai properti node "
                            "langsung, bukan '%s'" % (var, prop, CPU, prop))
        if kind == GPU and prop in CPU_ONLY:
            report(path, i, "%s.%s tidak ada di %s — set lewat "
                            "process_material" % (var, prop, GPU))
        if kind == CPU and prop in CPU_VECTOR2 and "Vector3" in value:
            report(path, i, "%s.%s bertipe Vector2, bukan Vector3" % (var, prop))


def main(argv):
    root = argv[1] if len(argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scanned = 0
    for dirpath, _dirs, files in os.walk(root):
        if ".godot" in dirpath:
            continue
        for fn in sorted(files):
            full = os.path.join(dirpath, fn)
            if fn.endswith((".tscn", ".tres")):
                lint_tscn(full)
                scanned += 1
            elif fn.endswith(".gd"):
                lint_gd(full)
                scanned += 1
    if problems:
        for p in problems:
            print("FAIL " + p)
        print("\n%d masalah partikel di %d berkas." % (len(problems), scanned))
        return 1
    print("OK — %d berkas: properti CPUParticles2D/GPUParticles2D konsisten" % scanned)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
