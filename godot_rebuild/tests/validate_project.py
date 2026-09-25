"""Static guardrails only; this does not replace native Godot runtime tests.

Run with Python 3, no dependencies: python godot_rebuild/tests/validate_project.py
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        errors.append(message)


project = (ROOT / "project.godot").read_text(encoding="utf-8")
for setting in (
    'run/main_scene="res://app/App.tscn"',
    'renderer/rendering_method="gl_compatibility"',
    'window/size/viewport_width=1280',
    'window/size/viewport_height=720',
    'common/physics_ticks_per_second=60',
    'config/custom_user_dir_name="MysticArenaRebuildDev"',
):
    check(setting in project, f"Missing project contract: {setting}")

source_files = [ROOT / "project.godot", *ROOT.rglob("*.gd"), *ROOT.rglob("*.tscn"), *ROOT.rglob("*.tres")]
for path in source_files:
    if ".godot" in path.parts:
        continue
    text = path.read_text(encoding="utf-8")
    for relative in re.findall(r'res://([^"\s]+)', text):
        target = (ROOT / relative).resolve()
        check(target.is_relative_to(ROOT), f"Reference escapes project: {path}: {relative}")
        check(target.is_file(), f"Missing reference: {path}: {relative}")
        # Linux CI is case sensitive, unlike many Windows filesystems.
        check(
            target.parent.is_dir() and target.name in [p.name for p in target.parent.iterdir()],
            f"Wrong path case or missing directory: {relative}",
        )
    check(".gdextension" not in text and "res://../" not in text, f"Unexpected external dependency: {path}")

for path in (ROOT / "scenes").rglob("*.tscn"):
    text = path.read_text(encoding="utf-8")
    names = re.findall(r'\[node name="([^"]+)"[^\n]*\]\nunique_name_in_owner = true', text)
    check(len(names) == len(set(names)), f"Duplicate scene-unique names: {path}")
    scripts = re.findall(r'\[ext_resource type="Script" path="res://([^"]+)"', text)
    for script in scripts:
        source = (ROOT / script).read_text(encoding="utf-8")
        for name in re.findall(r'%([A-Z][A-Za-z0-9_]*)', source):
            check(name in names, f"Missing unique node %{name} used by {script} in {path}")

sim = (ROOT / "scripts/simulation/sandbox_simulation.gd").read_text(encoding="utf-8")
check("func _physics_process(" in sim, "Simulation must own fixed ticks")
check("func _process(" not in sim, "Simulation must not tick on render frames")
check("PROCESS_MODE_PAUSABLE" in sim, "Simulation must pause")
app = (ROOT / "app/app.gd").read_text(encoding="utf-8")
check("queue_free()" in app and "remove_child" in app, "Navigation must clean up screens")
check("call_deferred" in app, "Navigation must leave input callback before replacing screens")

for error in errors:
    print("FAIL:", error, file=sys.stderr)
print(f"{'FAIL' if errors else 'PASS'}: {checks} static checks; runtime testing still required.")
sys.exit(bool(errors))
