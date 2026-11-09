#!/usr/bin/env python3
"""Validate and fingerprint heroes/ and its existing baked Godot renderer assets.

No pygame dependency. Re-bake with prepare_godot_entities.py --bake when changing
renderers; this contract detects drift, it does not claim pixel/FX parity.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot_rebuild"
OUTPUT = PROJECT / "data/heroes_renderers.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atlas(entry, skill=False):
    prefix = "skill_" if skill else ""
    path = PROJECT / entry["skills_png" if skill else "png"].removeprefix("res://")
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not PNG: {path}")
    width, height = struct.unpack(">II", raw[16:24])
    fw, fh = entry[prefix + "frame_w"], entry[prefix + "frame_h"]
    columns = entry.get(prefix + "frames_per_row", 8)
    if min(fw, fh, columns) <= 0 or width % fw or height % fh or width != columns * fw:
        raise ValueError(f"Invalid atlas geometry: {path}")
    capacity = width // fw * (height // fh)
    for name, (start, count) in entry[prefix + "anims"].items():
        if start < 0 or count <= 0 or start + count > capacity:
            raise ValueError(f"Invalid animation {name}: {path}")
    return {"sha256": digest(path), "width": width, "height": height}


def module_status():
    """Closed-world inventory: never label hashed/baked Python as native FX."""
    result = {}
    for path in sorted((ROOT / "heroes").glob("*.py")):
        tree = ast.parse(path.read_text())
        row = {
            "classes": sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree)),
            "functions": sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree)),
            "status": "pending_native_port",
            "native": [],
        }
        if path.name == "combat_feel.py":
            row.update(status="native_port_runtime_test_pending",
                       native=["res://scripts/entities/HeroCombatFeel.gd"],
                       oracle="res://tests/fixtures/hero_combat_feel.json")
        elif path.stem in {"grimjaw_fx", "kaizen_fx", "sylara_fx", "vex_fx", "zephyr_fx"}:
            row.update(status="native_feedback_only_visual_director_pending",
                       native=["res://scripts/entities/generated/HeroFeedback.gd"],
                       oracle="res://tests/fixtures/hero_feedback.json")
        elif path.name in ("__init__.py", "_bundle.py"):
            row.update(status="sampled_atlas_only_procedural_port_pending",
                       native=["res://scripts/entities/EntityVisuals.gd",
                               "res://scripts/entities/HeroVisuals.gd"])
        if path.stem == "grimjaw_fx":
            row["status"] = "native_feedback_hurt_death_slices_full_director_pending"
            row["native"].extend(["res://scripts/entities/GrimjawHurt.gd", "res://scripts/entities/GrimjawParticle.gd", "res://scripts/entities/GrimjawParticlePool.gd", "res://scripts/entities/GrimjawSkill.gd",
                                  "res://scripts/entities/HeroLiveFx.gd"])
            row["skill_oracle"] = "res://tests/fixtures/grimjaw_skill.json"
            row["hurt_oracle"] = "res://tests/fixtures/grimjaw_hurt.json"
            row["particle_oracle"] = "res://tests/fixtures/grimjaw_hurt.json"
        if path.stem == "zephyr_fx":
            row["status"] = "native_zephyr_live_slices_full_director_pending"
            row["native"].extend([
                "res://scripts/entities/ZephyrBolt.gd", "res://scripts/entities/ZephyrParticle.gd",
                "res://scripts/entities/ZephyrParticlePool.gd", "res://scripts/entities/HeroLiveFx.gd",
                "res://scripts/entities/ZephyrSwingTrail.gd", "res://scripts/entities/ZephyrImpact.gd", "res://scripts/entities/ZephyrHurt.gd", "res://scripts/entities/ZephyrSkill.gd", "res://scripts/entities/ZephyrDirectorState.gd", "res://scripts/entities/ZephyrVisualProjectile.gd", "res://scripts/entities/ZephyrVisualProjectileSystem.gd"])
            row["visual_projectile_oracle"] = "res://tests/fixtures/zephyr_projectile.json"
            row["director_state_oracle"] = "res://tests/fixtures/zephyr_director.json"
            row["skill_oracle"] = "res://tests/fixtures/zephyr_skill.json"
            row["impact_oracle"] = "res://tests/fixtures/zephyr_impact.json"
            row["trail_oracle"] = "res://tests/fixtures/zephyr_trail.json"
            row["staff_attachments"] = "res://data/zephyr_trail.json"
            row["particle_oracle"] = "res://tests/fixtures/zephyr_particles.json"
            row["geometry_oracle"] = "res://tests/fixtures/zephyr_bolt.json"
            row["known_difference"] = "CanvasItem compositing/rasterization differs from pygame scratch surfaces and RGB_ADD"
        result[path.name] = row
    return result


def build():
    manifest = PROJECT / "data/baked_units.json"
    units = json.loads(manifest.read_text())["units"]
    rows = {}
    for name, entry in sorted(units.items()):
        if not {"idle", "walk", "attack"} <= entry["anims"].keys():
            raise ValueError(f"Missing poses: {name}")
        row = {"renderer": entry["renderer"], "body": atlas(entry)}
        if "skills_png" in entry:
            row["skills"] = atlas(entry, True)
        rows[name] = row
    return {
        "schema": 1,
        "scope": "baked bodies and sampled skill poses; not procedural rig/live FX parity",
        "sources": {str(p.relative_to(ROOT)): digest(p)
                    for p in sorted((ROOT / "heroes").rglob("*.py"))},
        "migration": module_status(),
        "manifest_sha256": digest(manifest),
        "units": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            parser.exit(1, "heroes renderer contract drift; prepare/bake then regenerate\n")
    else:
        OUTPUT.write_text(text)
    print("heroes renderer contract OK")


if __name__ == "__main__":
    main()
