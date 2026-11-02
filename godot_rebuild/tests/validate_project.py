#!/usr/bin/env python3
"""Dependency-free guardrails for the native main.py migration."""
from __future__ import annotations

import ast
import hashlib
import json
import operator
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "godot_rebuild"
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


def constant(path: Path, name: str):
    """Read literals or the simple arithmetic used by the source constants."""
    def evaluate(node: ast.AST):
        if isinstance(node, ast.BinOp):
            operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
            return operations[type(node.op)](evaluate(node.left), evaluate(node.right))
        return ast.literal_eval(node)

    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                return evaluate(node.value)
    raise AssertionError(f"Missing source constant: {path}:{name}")


def gd_constant(path: Path, name: str) -> float:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^const {name} := ([0-9.]+)$", text, re.MULTILINE)
    check(match is not None, f"Missing GDScript constant: {path}:{name}")
    return float(match.group(1))


def main() -> int:
    project = (PROJECT / "project.godot").read_text(encoding="utf-8")
    presets = (PROJECT / "export_presets.cfg").read_text(encoding="utf-8")
    check('package/unique_name="io.github.dharmawantoxi.mysticarena"' in presets, "Android application ID parity")
    check('architectures/arm64-v8a=true' in presets, "Android ARM64 enabled")
    check('keystore/release_password' not in presets, "No exported signing secrets")
    for key, expected in {
        "config/name": "Mystic Arena",
        "run/main_scene": "res://scenes/Main.tscn",
        "window/size/viewport_width": "1280",
        "window/size/viewport_height": "720",
        'window/stretch/mode': "canvas_items",
        'window/stretch/aspect': "keep",
        "pointing/emulate_touch_from_mouse": "false",
        "pointing/emulate_mouse_from_touch": "false",
        "config/auto_accept_quit": "false",
        "config/quit_on_go_back": "false",
    }.items():
        quoted = not (expected in ("true", "false") or re.fullmatch(r"-?\d+(\.\d+)?", expected))
        pattern = f"{key}=" + (f'"{expected}"' if quoted else expected)
        check(pattern in project, f"Project setting: {key}")
    for scene in PROJECT.rglob("*.tscn"):
        for resource in re.findall(r'path="(res://[^"]+)"', scene.read_text(encoding="utf-8")):
            check((PROJECT / resource[6:]).is_file(), f"Missing scene resource: {resource}")
    main_source = ROOT / "main.py"
    clock = PROJECT / "scripts/core/FixedClock.gd"
    check(abs(1000.0 / gd_constant(clock, "HZ") - constant(main_source, "FIXED_DT_MS")) < 1e-12, "60 Hz source parity")
    check(gd_constant(clock, "MAX_CATCHUP") == constant(main_source, "MAX_CATCHUP"), "Catch-up source parity")
    check(gd_constant(clock, "MAX_FRAME_DELTA") == 0.250, "250 ms stall clamp")
    touch = ROOT / "mobile/touch.py"
    gestures = PROJECT / "scripts/core/GestureTracker.gd"
    for python_name, gd_name, scale in [
        ("TAP_SLOP", "TAP_SLOP", 1),
        ("LONG_PRESS_MS", "LONG_PRESS_SECONDS", 0.001),
        ("DOUBLE_TAP_MS", "DOUBLE_TAP_SECONDS", 0.001),
        ("SCROLL_STEP", "SCROLL_STEP", 1),
        ("FLING_FRICTION", "FLING_FRICTION", 1),
        ("FLING_MIN_SPEED", "FLING_MIN_SPEED", 1),
        ("TAP_SLOP", "TAP_SLOP", 1),
    ]:
        check(abs(gd_constant(gestures, gd_name) - constant(touch, python_name) * scale) < 1e-9,
              f"Gesture source parity: {python_name}")
    catalog = json.loads((PROJECT / "data/levels.json").read_text(encoding="utf-8"))
    check(len(catalog) == 54, "54 level metadata entries")
    check([row["level_number"] for row in catalog] == list(range(1, 55)), "Stable level order")
    check(catalog[0]["name"] == constant(ROOT / "levels/level_data.py", "LEVEL_1")["name"], "Level name parity")
    for path in PROJECT.rglob("*.gd"):
        source = path.read_text(encoding="utf-8")
        check("Engine.has_singleton(\"Python\"" not in source, "No embedded Python assumption")
        for resource in re.findall(r'"(res://[^"]+)"', source):
            if "%" not in resource and not resource.endswith("voucher_codes.txt"):
                check((PROJECT / resource[6:]).exists(), f"Missing literal resource in {path.name}: {resource}")
    core = json.loads((PROJECT / "data/core_data.json").read_text(encoding="utf-8"))
    check(core["schema"] == 1 and core["source"] == "_core.py", "Core data schema/source")
    check(len(core["levels"]) == 54, "Core data 54 levels")
    check(len(core["heroes"]) >= 222, "Core data hero catalog")
    check(len(core["bosses"]["mini"]) == 162 and len(core["bosses"]["true"]) == 54, "Core data boss catalog")
    check(len(core["items"]) == 33, "Core data item catalog")
    check(set(core["lanes"]) == {"top", "mid", "bot", "river"}, "Core data lanes")
    check(core["rules"]["MINION_WAVE_INTERVAL"] == constant(ROOT / "_core.py", "MINION_WAVE_INTERVAL"), "Wave interval parity")
    check(core["rules"]["CASTLE_SHIELD_FREE_WAVES"] == constant(ROOT / "_core.py", "CASTLE_SHIELD_FREE_WAVES"), "Castle shield parity")
    check((PROJECT / "scenes/CoreGame.tscn").is_file(), "Native CoreGame scene exists")
    check((PROJECT / "tests/fixtures/cloud_payload.json").is_file(), "Cloud checksum fixture exists")
    topup = (PROJECT / "scripts/ports/TopupPort.gd").read_text(encoding="utf-8")
    check("MYSTIC_TOPUP_URL" in topup and "unavailable" in topup, "Top-up requires configured server")
    cloud = (PROJECT / "scripts/ports/CloudSavePort.gd").read_text(encoding="utf-8")
    check("Play Games plugin not configured" in cloud, "Cloud default is explicitly unavailable")
    check((PROJECT / "scripts/Main.gd").is_file(), "Canonical Main.gd entry point exists")
    entities = PROJECT / "scripts/entities"
    for name in ["EntityCombat.gd", "EntityMovement.gd", "EntityProjectiles.gd", "EntityAI.gd", "EntityItems.gd", "EntityVisuals.gd"]:
        check((entities / name).is_file(), f"Native entity module: {name}")
    check((entities / "generated/HeroSkillKit.gd").is_file(), "Generated hero skill kit exists")
    check((entities / "generated/BossKit.gd").is_file(), "Generated boss AI kit exists")
    baked_units = json.loads((PROJECT / "data/baked_units.json").read_text(encoding="utf-8"))
    baked_props = json.loads((PROJECT / "data/baked_props.json").read_text(encoding="utf-8"))
    check(len(baked_units["units"]) >= 222, "Baked hero/boss sprite manifest")
    check(len(baked_props["minions"]) == 10, "Baked minion sprite manifest")
    check(len(baked_props["towers"]) == 8, "Baked tiered tower sprite manifest")
    check(len(baked_props["nexus"]) == 2, "Baked nexus sprite manifest")
    check("EntityProjectiles.update(self)" in (PROJECT / "scripts/core/MatchModel.gd").read_text(encoding="utf-8"), "Match model updates traveling projectiles")
    check("EntityVisuals.draw_unit" in (PROJECT / "scripts/game/ArenaView.gd").read_text(encoding="utf-8"), "Arena renderer uses baked entity sprites")
    render_dir = PROJECT / "scripts/render"
    for name in ("RenderCache.gd", "RenderQuality.gd", "RenderEasing.gd", "MapView.gd", "CombatEffects.gd", "RenderCinematics.gd"):
        check((render_dir / name).is_file(), f"Native render module: {name}")
    render_data = json.loads((PROJECT / "data/render_data.json").read_text(encoding="utf-8"))
    map_bakes = json.loads((PROJECT / "data/map_bakes.json").read_text(encoding="utf-8"))["maps"]
    check(len(render_data["map_themes"]) == 54, "Render contract covers 54 themes")
    check(len(map_bakes) == 54, "54 baked map textures")
    check(len(list((PROJECT / "assets/maps").glob("*.png"))) == 54, "54 map PNG assets")
    check(render_data["effect_caps"] == {"MAX_FLOATING": 300, "MAX_PARTICLES": 500, "MAX_EXPLOSIONS": 80}, "EffectManager caps parity")
    arena_text = (PROJECT / "scripts/game/ArenaView.gd").read_text(encoding="utf-8")
    check("game.map_view.draw_static" in arena_text, "Arena renderer uses baked map")
    check("game.effects.draw" in arena_text, "Arena renderer uses native EffectManager")
    check("game.cinematics.draw" in arena_text, "Arena renderer draws cinematics")
    core_game_text = (PROJECT / "scripts/game/CoreGame.gd").read_text(encoding="utf-8")
    check("func cinematic_active() -> bool:" in core_game_text, "CoreGame implements cinematic pause contract")
    check("signal render_event" in (PROJECT / "scripts/core/MatchModel.gd").read_text(encoding="utf-8"), "MatchModel emits render events")
    system_dir = PROJECT / "scripts/system"
    for name in ("SpatialGrid.gd", "FrustumCuller.gd", "FpsCounter.gd", "AdaptiveQuality.gd"):
        check((system_dir / name).is_file(), f"Native system module: {name}")
    system_data = json.loads((PROJECT / "data/system_data.json").read_text(encoding="utf-8"))
    check(system_data["performance"]["spatial_cell_size"] == 60, "SpatialGrid cell size parity")
    check(system_data["performance"]["frustum_margin"] == 80, "FrustumCuller margin parity")
    check(len(system_data["audio"]["manifest"]) == 17, "SoundManager 17-sound manifest")
    check(system_data["save"]["num_slots"] == 3, "SaveManager 3 slots")
    check("var spatial := SpatialGrid.new()" in (PROJECT / "scripts/core/MatchModel.gd").read_text(encoding="utf-8"), "MatchModel uses spatial grid")
    check("FrustumCuller.is_visible" in (PROJECT / "scripts/game/ArenaView.gd").read_text(encoding="utf-8"), "Arena renderer frustum culling")
    check("func play_positional(" in (PROJECT / "scripts/audio/AudioDirector.gd").read_text(encoding="utf-8"), "AudioDirector positional audio")
    check("func migrate_legacy_save(" in (PROJECT / "scripts/core/SaveRepository.gd").read_text(encoding="utf-8"), "SaveRepository legacy migration")
    check("var adaptive_quality := AdaptiveQuality.new()" in (PROJECT / "scripts/Main.gd").read_text(encoding="utf-8"), "Main adaptive quality wired")
    archetype_path = PROJECT / "scripts/core/HeroArchetypes.gd"
    check(archetype_path.is_file(), "Native HeroArchetypes module exists")
    archetypes = json.loads((PROJECT / "data/hero_archetypes.json").read_text(encoding="utf-8"))
    oracle = json.loads((PROJECT / "tests/fixtures/hero_archetypes_parity.json").read_text(encoding="utf-8"))
    check(archetypes["schema"] == 1 and archetypes["source"] == "hero_archetypes.py", "Archetype contract schema/source")
    check(archetypes["source_sha256"] == hashlib.sha256((ROOT / "hero_archetypes.py").read_bytes()).hexdigest(), "Archetype source hash current")
    check(oracle["source_sha256"] == archetypes["source_sha256"], "Archetype oracle hash current")
    check(len(archetypes["archetypes"]) == 222 and len(archetypes["boss_resistances"]) == 216, "Archetype 222/216 coverage")
    check(set(archetypes["archetypes"]) == set(core["heroes"]), "Archetypes cover the playable hero catalog exactly")
    boss_keys = set(core["bosses"]["mini"]) | set(core["bosses"]["true"])
    check(set(archetypes["boss_resistances"]) == boss_keys, "Boss resistances cover the boss catalog exactly")
    check(set(oracle["heroes"]) == set(core["heroes"]) and set(oracle["bosses"]) == boss_keys, "Python oracle covers every runtime row")
    for name in ("ARMOR_FACTOR", "ARMOR_MAX", "MR_MAX"):
        check(gd_constant(archetype_path, name) == constant(ROOT / "hero_archetypes.py", name), f"Archetype source constant: {name}")
    core_data_text = (PROJECT / "scripts/core/CoreData.gd").read_text(encoding="utf-8")
    check("var archetypes: HeroArchetypes" in core_data_text and "archetypes.valid()" in core_data_text, "CoreData loads and validates archetypes")
    unit_text = (PROJECT / "scripts/core/BattleUnit.gd").read_text(encoding="utf-8")
    check("data.archetypes.get_archetype(hero_type, stats)" in unit_text, "Hero setup uses analyzed archetype/manual override")
    check("data.archetypes.boss_resistances_for(boss_type, boss_class, stats)" in unit_text, "Boss setup uses calibrated resistance/clamp helper")
    check("intentionally separate from the analyzed damage school" in unit_text, "Role-based item Magic attribute stays separate from damage school")
    combat_text = (PROJECT / "scripts/entities/EntityCombat.gd").read_text(encoding="utf-8")
    check("HeroArchetypes.physical_mitigation(unit.armor)" in combat_text, "Boss combat uses source armor curve")
    check("unit.status.armor_shred_amount * HeroArchetypes.ARMOR_FACTOR" in combat_text, "Boss armor shred subtracts after curve")
    check("minf(HeroArchetypes.MR_MAX, unit.magic_resist)" in combat_text, "Boss magic resistance uses source cap")
    menu_text = (PROJECT / "scripts/ui/MenuView.gd").read_text(encoding="utf-8")
    check("arch.short_label(hero_type, stats)" in menu_text and "arch.detail_label(hero_type, stats)" in menu_text, "Hero shop displays school/tier/power")
    arena_text = (PROJECT / "scripts/game/ArenaView.gd").read_text(encoding="utf-8")
    check("func _draw_boss_resistances(" in arena_text and "boss.resist_profile" in arena_text, "Arena displays boss resistance profile")
    check("_test_archetypes()" in (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native suite runs archetype parity")
    for workflow in ("godot-check.yml", "godot-rebuild.yml"):
        workflow_text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
        check("tools/prepare_godot_archetypes.py --check" in workflow_text, f"CI archetype staleness gate: {workflow}")
        check("tools/test_godot_archetypes_prepare.py" in workflow_text, f"CI archetype exporter tests: {workflow}")
    balance_path = PROJECT / "scripts/core/HeroBalance.gd"
    check(balance_path.is_file(), "Native HeroBalance module exists")
    balance = json.loads((PROJECT / "data/hero_balance.json").read_text(encoding="utf-8"))
    balance_oracle = json.loads((PROJECT / "tests/fixtures/hero_balance_parity.json").read_text(encoding="utf-8"))
    check(balance["schema"] == 1 and balance["source"] == "hero_balance.py", "Balance contract schema/source")
    check(balance["source_sha256"] == hashlib.sha256((ROOT / "hero_balance.py").read_bytes()).hexdigest(), "Balance source hash current")
    check(balance_oracle["source_sha256"] == balance["source_sha256"], "Balance oracle hash current")
    check(len(balance["pristine_boss_stats"]) == 216 and len(balance["starter_heroes"]) == 6, "Balance 216 pristine bosses / six starters")
    check(len(balance_oracle["raw_catalog"]) == 222 and len(balance_oracle["final_stats"]) == 216, "Balance oracle catalog coverage")
    check(balance["constants"]["starter_catchup_max"] == constant(ROOT / "hero_balance.py", "STARTER_CATCHUP_MAX"), "Starter catch-up source constant")
    check(balance["constants"]["final_corr_cap"] == constant(ROOT / "hero_balance.py", "FINAL_CORR_CAP"), "Final correction cap source constant")
    check("def raw_hero_catalog(" in (ROOT / "tools/prepare_godot_core.py").read_text(encoding="utf-8"), "Core exporter exposes pre-balance catalog")
    core_data_text = (PROJECT / "scripts/core/CoreData.gd").read_text(encoding="utf-8")
    check("var balance: HeroBalance" in core_data_text and "balance.valid()" in core_data_text, "CoreData loads and validates hero balance")
    unit_text = (PROJECT / "scripts/core/BattleUnit.gd").read_text(encoding="utf-8")
    check("data.balance.is_starter(hero_type)" in unit_text and "data.balance.starter_catchup_stats(" in unit_text, "Hero setup applies starter catch-up at creation")
    check("data.balance.boss_unlocks_for_purchases(purchased_heroes)" in (PROJECT / "scripts/core/MatchModel.gd").read_text(encoding="utf-8"), "MatchModel feeds roster unlocks to catch-up")
    check("model.data.balance.boss_unlocks_for_purchases(model.purchased_heroes)" in (PROJECT / "scripts/entities/EntityAI.gd").read_text(encoding="utf-8"), "Enemy AI uses the same roster unlock count")
    check("BalanceParity.run(self)" in (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native suite runs balance parity")
    check((PROJECT / "tests/HeroBalanceParityTest.gd").is_file(), "Balance parity test module exists")
    for workflow in ("godot-check.yml", "godot-rebuild.yml"):
        workflow_text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
        check("tools/prepare_godot_balance.py --check" in workflow_text, f"CI balance staleness gate: {workflow}")
        check("tools/test_godot_balance_prepare.py" in workflow_text, f"CI balance exporter tests: {workflow}")
    items_path = PROJECT / "scripts/core/HeroItems.gd"
    check(items_path.is_file(), "Native HeroItems module exists")
    items = json.loads((PROJECT / "data/hero_items.json").read_text(encoding="utf-8"))
    items_oracle = json.loads((PROJECT / "tests/fixtures/hero_items_parity.json").read_text(encoding="utf-8"))
    check(items["schema"] == 1 and items["source"] == "hero_items.py", "Items contract schema/source")
    check(items["source_sha256"] == hashlib.sha256((ROOT / "hero_items.py").read_bytes()).hexdigest(), "Items source hash current")
    check(items_oracle["source_sha256"] == items["source_sha256"], "Items oracle hash current")
    check(len(items["catalog"]) == 33 and len(items["shop_pages"]) == 6 and len(items["item_shop_order"]) == 33, "Items 33 catalog / six class pages")
    check(items["max_item_slots"] == constant(ROOT / "hero_items.py", "MAX_ITEM_SLOTS"), "Items slot source constant")
    check(items["item_flat_cost"] == constant(ROOT / "hero_items.py", "ITEM_FLAT_COST"), "Items flat cost source constant")
    check(items["catalog"] == core.get("items", {}), "Items contract matches core catalog")
    check("var items: HeroItems" in core_data_text and "items.valid()" in core_data_text, "CoreData loads and validates hero items")
    inventory_text = (PROJECT / "scripts/core/UnitInventory.gd").read_text(encoding="utf-8")
    check("func skill_amp()" in inventory_text and "func roll_block(" in inventory_text, "Inventory ports skill amp and block roll")
    entity_items_text = (PROJECT / "scripts/entities/EntityItems.gd").read_text(encoding="utf-8")
    check("static func update_auras(" in entity_items_text and "static func apply_miasma(" in entity_items_text, "EntityItems ports auras and miasma")
    check("EntityItems.update_auras(self)" in (PROJECT / "scripts/core/MatchModel.gd").read_text(encoding="utf-8"), "MatchModel updates item auras each frame")
    check("items.hero = self" in unit_text and "status.silence_timer" in (PROJECT / "scripts/core/BattleUnit.gd").read_text(encoding="utf-8"), "BattleUnit binds inventory and silence gate")
    check("ItemsParity.run(self)" in (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native suite runs items parity")
    check((PROJECT / "tests/HeroItemsParityTest.gd").is_file(), "Items parity test module exists")
    for workflow in ("godot-check.yml", "godot-rebuild.yml"):
        workflow_text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
        check("tools/prepare_godot_items.py --check" in workflow_text, f"CI items staleness gate: {workflow}")
        check("tools/test_godot_items_prepare.py" in workflow_text, f"CI items exporter tests: {workflow}")
    lighting_path = PROJECT / "scripts/render/Lighting.gd"
    check(lighting_path.is_file(), "Native Lighting module exists")
    check((PROJECT / "scripts/render/LightingResampler.gd").is_file(), "Native lighting resampler exists")
    lighting = json.loads((PROJECT / "data/lighting.json").read_text(encoding="utf-8"))
    lighting_oracle = json.loads((PROJECT / "tests/fixtures/lighting_parity.json").read_text(encoding="utf-8"))
    check(lighting["schema"] == 1 and lighting["source"] == "lighting.py", "Lighting contract schema/source")
    check(lighting["source_sha256"] == hashlib.sha256((ROOT / "lighting.py").read_bytes()).hexdigest(), "Lighting source hash current")
    check(lighting_oracle["source_sha256"] == lighting["source_sha256"], "Lighting oracle hash current")
    check(lighting["light_dir"] == list(constant(ROOT / "lighting.py", "LIGHT_DIR")), "Lighting direction source constant")
    check(lighting["rim_add"] == list(constant(ROOT / "lighting.py", "RIM_ADD")), "Lighting rim source constant")
    check(lighting["shade_mul"] == constant(ROOT / "lighting.py", "SHADE_MUL"), "Lighting shade source constant")
    check(lighting["mask_alpha"] == constant(ROOT / "lighting.py", "MASK_ALPHA"), "Lighting mask source constant")
    check(lighting["grad_steps"] == constant(ROOT / "lighting.py", "_GRAD_STEPS"), "Lighting gradient steps source constant")
    check(len(lighting["canonical_mul_rgb"]) == lighting["grad_steps"] ** 2 * 3, "Lighting canonical mul grid size")
    check(len(lighting_oracle["contour_cases"]) == 8 and len(lighting_oracle["gradient_cases"]) == 40 and len(lighting_oracle["apply_cases"]) == 19, "Lighting oracle coverage")
    quality_text = (PROJECT / "scripts/render/RenderQuality.gd").read_text(encoding="utf-8")
    check('"hero_lighting": false' in quality_text and '"hero_lighting": true' in quality_text, "RenderQuality exposes hero lighting gate")
    visuals_text = (PROJECT / "scripts/entities/EntityVisuals.gd").read_text(encoding="utf-8")
    check('entry.get("lighting_baked", true)' in visuals_text and "lit_frame_texture" in visuals_text, "EntityVisuals only lights raw imports")
    check("EntityVisuals.configure(" in (PROJECT / "scripts/game/CoreGame.gd").read_text(encoding="utf-8"), "CoreGame propagates render quality to lighting")
    check("LightingParity.run(self)" in (PROJECT / "tests/run_all.gd").read_text(encoding="utf-8"), "Native suite runs lighting parity")
    check((PROJECT / "tests/LightingParityTest.gd").is_file(), "Lighting parity test module exists")
    for workflow in ("godot-check.yml", "godot-rebuild.yml"):
        workflow_text = (ROOT / ".github/workflows" / workflow).read_text(encoding="utf-8")
        check("pygame==2.6.1" in workflow_text, f"CI pins pygame oracle: {workflow}")
        check("tools/prepare_godot_lighting.py --check" in workflow_text, f"CI lighting staleness gate: {workflow}")
        check("tools/test_godot_lighting_prepare.py" in workflow_text, f"CI lighting exporter tests: {workflow}")
    print(f"PASS: {checks} native project/source checks")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, ValueError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
