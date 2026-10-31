"""Whole-file oracle for `_entity.py` (6.536 lines, five merged entity modules).

`_entity.py` is the entity half of the pygame runtime:

    tower.py (19-1385)     castle.py (1386-3207)   hero.py (3208-5388)
    minion.py (5389-5991)  ai_player.py (5992-6536)

plus a short prelude with the damage-credit and damage-school helpers. The rebuild has
carried these classes for many layers (`structure_state.gd`, `hero_state.gd`,
`minion_battle.gd`, `projectile_state.gd`, `siege_battle.gd`, `ai_policy.gd`, the baked
atlases), so this oracle does three things:

* it inventories the file (five modules, seven classes, 125 `def`s, 38 module-level
  functions, ten module caches) and classifies every symbol with a target file and a
  token that target really contains — including the `bake` rows, where the token is the
  bake script line that executes the very same source function;
* it imports the REAL module (stub `pygame`, `_core` settings namespace, `_system`,
  `_render`) and executes `Tower`, `Castle`, `Minion` and `Bullet`, so the tower table,
  the nexus table, the nexus-scaled minion stats, the sale quotes and the projectile
  impact arms in `tests/fixtures/entity_source.json` are the pygame numbers, not a
  transcription;
* it records the damage-school resolution matrix and the untouched-HP nexus upgrade, the
  two entity rules that are easiest to get subtly wrong.

Run: python godot_rebuild/tests/entity_source_oracle.py --write
"""

import argparse
import ast
import importlib
import json
import math
import random
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTITY = ROOT / "_entity.py"
CORE = ROOT / "_core.py"
GODOT = ROOT / "godot_rebuild"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "entity_source.json"

SECTIONS = [
    ("prelude", 1, 18),
    ("tower", 19, 1385),
    ("castle", 1386, 3207),
    ("hero", 3208, 5388),
    ("minion", 5389, 5991),
    ("ai_player", 5992, 6536),
]
CORE_SETTINGS_BLOCK = (28, 1291)

CLASS_TARGETS = {
    "_DummyBulletTarget": ("bake", "godot_rebuild/bake/bake_bullet_atlas.py",
                           "entity._DummyBulletTarget",
                           "target palsu untuk bake atlas peluru"),
    "Bullet": ("ported", "godot_rebuild/scripts/combat/projectile_state.gd",
               "var hit_radius := 4.0", "satu tembakan logis; renderer hanya membaca posisi"),
    "Tower": ("ported", "godot_rebuild/scripts/combat/structure_state.gd",
              "func activate_regen_shield()", "model struktur dipakai tower dan nexus"),
    "Castle": ("ported", "godot_rebuild/scripts/combat/structure_state.gd",
               "func can_activate_castle_shield()", "nexus = struktur kind \"nexus\""),
    "Hero": ("ported", "godot_rebuild/scripts/combat/hero_state.gd",
             "func recalc_item_stats()", "state hero native + arm skill di scripts/combat"),
    "Minion": ("ported", "godot_rebuild/scripts/combat/minion_battle.gd",
               "func apply_slow(target_id", "minion battle + definition"),
    "AIPlayer": ("ported", "godot_rebuild/scripts/match/ai_policy.gd",
                 "func brain()", "AI dipecah ke ai_policy/ai_controller/ai_hero_control"),
}
MODULE_TARGETS = {
    "prelude": ("ported", "godot_rebuild/scripts/match/prototype_battle.gd",
                "func _deliver_hit(", "kredit damage & sekolah ada di jalur _deliver_hit"),
    "tower": CLASS_TARGETS["Tower"],
    "castle": CLASS_TARGETS["Castle"],
    "hero": CLASS_TARGETS["Hero"],
    "minion": CLASS_TARGETS["Minion"],
    "ai_player": CLASS_TARGETS["AIPlayer"],
}
# Source hook -> (target file, the Godot function that does the same job).
METHOD_ALIASES = {
    "Bullet": {
        "__init__": ("godot_rebuild/scripts/combat/projectile_state.gd",
                     "var speed := 8.0"),
        "update": ("godot_rebuild/scripts/combat/siege_battle.gd",
                   "func _update_projectiles("),
        "_on_hit": ("godot_rebuild/scripts/combat/siege_battle.gd",
                    "func _cannon_impact("),
        "draw": ("godot_rebuild/bake/bake_bullet_atlas.py", "entity._get_bullet_sprite("),
        "_draw_hd_arrow": ("godot_rebuild/bake/bake_bullet_atlas.py",
                           "entity._get_bullet_sprite("),
    },
    "Tower": {
        "__init__": ("godot_rebuild/scripts/combat/structure_state.gd",
                     "var regen_shield_active := false"),
        "_apply_level_stats": ("godot_rebuild/scripts/match/prototype_battle.gd",
                               "func _build_tower_for("),
        "can_upgrade": ("godot_rebuild/scripts/match/prototype_battle.gd",
                        "func upgrade_price("),
        "upgrade_cost": ("godot_rebuild/scripts/match/prototype_battle.gd",
                         "func upgrade_price("),
        "upgrade": ("godot_rebuild/scripts/match/prototype_battle.gd",
                    "func upgrade_tower("),
        "sell_value": ("godot_rebuild/scripts/combat/structure_state.gd",
                       "func sale_value()"),
        "can_activate_regen_shield": ("godot_rebuild/scripts/combat/structure_state.gd",
                                      "func can_activate_regen_shield()"),
        "regen_shield_cost": ("godot_rebuild/scripts/combat/structure_state.gd",
                              "const REGEN_SHIELD_COST := 850"),
        "activate_regen_shield": ("godot_rebuild/scripts/combat/structure_state.gd",
                                  "func activate_regen_shield()"),
        "update": ("godot_rebuild/scripts/match/prototype_battle.gd", "func step_tick("),
        "_update_regen": ("godot_rebuild/scripts/combat/structure_state.gd",
                          "func tick_regen()"),
        "_find_target": ("godot_rebuild/scripts/combat/siege_battle.gd",
                         "func _structure_target("),
        "_shoot": ("godot_rebuild/scripts/combat/siege_battle.gd", "func fire_projectile("),
        "_shoot_archer": ("godot_rebuild/scripts/combat/siege_battle.gd",
                          "func _append_volley_targets("),
        "_shoot_cannon": ("godot_rebuild/scripts/combat/siege_battle.gd",
                          "func _cannon_splash("),
        "_shoot_ice": ("godot_rebuild/scripts/combat/siege_battle.gd", "func _ice_aoe("),
        "_shoot_mage": ("godot_rebuild/scripts/combat/siege_battle.gd",
                        "func _mage_impact("),
        "take_damage": ("godot_rebuild/scripts/combat/siege_battle.gd", "func apply_hit("),
        "draw": ("godot_rebuild/scenes/siege/siege_view.gd", "func _draw_structure("),
        "_draw_shield_crest": ("godot_rebuild/scenes/siege/siege_view.gd",
                               "StructureArt.crest_frame(14"),
        "_draw_regen_indicator": ("godot_rebuild/scenes/siege/siege_view.gd",
                                  "func _draw_regen_plus("),
        "_draw_tower_body": ("godot_rebuild/bake/bake_structure_atlas.py", "tower_sheet("),
    },
    "Castle": {
        "__init__": ("godot_rebuild/scripts/combat/structure_state.gd",
                     "var castle_shield_purchased := false"),
        "_apply_level_stats": ("godot_rebuild/scripts/match/prototype_battle.gd",
                               "func _apply_nexus_stats("),
        "upgrade": ("godot_rebuild/scripts/match/prototype_battle.gd",
                    "func upgrade_nexus("),
        "upgrade_cost": ("godot_rebuild/scripts/match/prototype_battle.gd",
                         "func nexus_upgrade_price("),
        "can_activate_castle_shield": ("godot_rebuild/scripts/combat/structure_state.gd",
                                       "func can_activate_castle_shield()"),
        "castle_shield_cost": ("godot_rebuild/scripts/combat/structure_state.gd",
                               "const CASTLE_SHIELD_COST"),
        "activate_castle_shield": ("godot_rebuild/scripts/combat/structure_state.gd",
                                   "func activate_castle_shield()"),
        "update": ("godot_rebuild/scripts/match/prototype_battle.gd", "func step_tick("),
        "_update_castle_shield": ("godot_rebuild/scripts/combat/structure_state.gd",
                                  "func tick_regen()"),
        "set_wave": ("godot_rebuild/scripts/combat/structure_state.gd", "func set_wave("),
        "_find_target": ("godot_rebuild/scripts/combat/siege_battle.gd",
                         "func _structure_target("),
        "_shoot": ("godot_rebuild/scripts/combat/siege_battle.gd", "func fire_projectile("),
        "take_damage": ("godot_rebuild/scripts/combat/siege_battle.gd", "func apply_hit("),
        "apply_slow": ("godot_rebuild/scripts/combat/unit_state.gd", "func apply_slow("),
        "draw": ("godot_rebuild/scenes/siege/siege_view.gd", "func _draw_structure("),
        "_draw_castle_shield": ("godot_rebuild/scripts/ui/structure_art.gd",
                                "func castle_frame("),
        "_draw_hp_bar": ("godot_rebuild/scenes/siege/siege_view.gd",
                         "func _draw_structure_selection("),
    },
    "Hero": {
        "__init__": ("godot_rebuild/scripts/combat/hero_state.gd",
                     "func apply_level_stats()"),
        "_recalc_item_stats": ("godot_rebuild/scripts/combat/hero_state.gd",
                               "func recalc_item_stats()"),
        "_apply_level_stats": ("godot_rebuild/scripts/combat/hero_state.gd",
                               "func apply_level_stats()"),
        "upgrade": ("godot_rebuild/scripts/combat/hero_state.gd", "func upgrade()"),
        "upgrade_cost": ("godot_rebuild/scripts/combat/hero_state.gd",
                         "func upgrade_cost()"),
        "skill_damage": ("godot_rebuild/scripts/combat/hero_state.gd",
                         "func skill_damage()"),
        "move_to": ("godot_rebuild/scripts/match/prototype_battle.gd",
                    "func set_hero_destination("),
        "cast_skill": ("godot_rebuild/scripts/match/prototype_battle.gd",
                       "func try_auto_cast("),
        "is_skill_ready": ("godot_rebuild/scripts/ui/hero_panel_layout.gd",
                           "var ready := cooldown <= 0"),
        "_get_all_enemies": ("godot_rebuild/scripts/match/prototype_battle.gd",
                             "func _hero_enemy_list("),
        "_find_attack_target": ("godot_rebuild/scripts/match/prototype_battle.gd",
                                "func hero_basic_attack("),
        "_eff_attack_cd": ("godot_rebuild/scripts/combat/hero_state.gd",
                           "func eff_attack_cd("),
        "_eff_attack_range": ("godot_rebuild/scripts/combat/hero_state.gd",
                              "func eff_attack_range()"),
        "_find_hunt_target": ("godot_rebuild/scripts/match/prototype_battle.gd",
                              "func _hero_pick_target("),
        "_find_aggro_target": ("godot_rebuild/scripts/match/prototype_battle.gd",
                               "func hero_aggro_target("),
        "_get_base_pos": ("godot_rebuild/scripts/match/prototype_battle.gd",
                          "func _hero_home("),
        "_is_near_base": ("godot_rebuild/scripts/match/prototype_battle.gd",
                          "func _hero_near_own_base("),
        "_heal_at_base": ("godot_rebuild/scripts/match/prototype_battle.gd",
                          "func _hero_near_own_base("),
        "_passive_heal": ("godot_rebuild/scripts/match/prototype_battle.gd",
                          "func _hero_passive_heal("),
        "_move_toward": ("godot_rebuild/scripts/match/prototype_battle.gd",
                         "func move_to("),
        "update": ("godot_rebuild/scripts/match/prototype_battle.gd",
                   "func _step_one_hero("),
        "_try_auto_cast": ("godot_rebuild/scripts/match/prototype_battle.gd",
                           "func try_auto_cast("),
        "_collect_onhit_units": ("godot_rebuild/scripts/match/battle_item_effects.gd",
                                 "Hero._collect_onhit_units()"),
        "_do_attack": ("godot_rebuild/scripts/match/prototype_battle.gd",
                       "func hero_basic_attack("),
        "_spawn_projectile": ("godot_rebuild/scripts/combat/hero_projectiles.gd",
                              "static func spawn("),
        "_spawn_skill_projectile": ("godot_rebuild/scripts/combat/hero_projectiles.gd",
                                    "static func spawn("),
        "take_damage": ("godot_rebuild/scripts/match/prototype_battle.gd",
                        "func _deliver_hit("),
        "respawn": ("godot_rebuild/scripts/match/prototype_battle.gd",
                    "func _step_hero_respawn("),
        "draw": ("godot_rebuild/bake/bake_hero_atlas.py", "hero.draw(surface)"),
        "_build_name_badge": ("godot_rebuild/bake/bake_hero_atlas.py",
                              "hero.draw(surface)"),
        "_draw_hero_shape": ("godot_rebuild/bake/bake_hero_atlas.py", "hero.draw(surface)"),
        "_draw_projectile": ("godot_rebuild/bake/bake_hero_projectiles.py", "entity."),
        "_draw_arrow_projectile": ("godot_rebuild/bake/bake_hero_projectiles.py", "entity."),
        "_draw_magic_orb_projectile": ("godot_rebuild/bake/bake_hero_projectiles.py",
                                       "entity."),
        "_draw_magic_bolt_projectile": ("godot_rebuild/bake/bake_hero_projectiles.py",
                                        "entity."),
        "_draw_lightning_projectile": ("godot_rebuild/bake/bake_hero_projectiles.py",
                                       "entity."),
        "_draw_ice_shard_projectile": ("godot_rebuild/bake/bake_hero_projectiles.py",
                                       "entity."),
        "direction": ("godot_rebuild/scripts/combat/hero_state.gd",
                      "var attack_facing := 1.0"),
        "timer": ("godot_rebuild/scripts/combat/hero_state.gd", "var attack_timer := 0"),
        "attack_cooldown": ("godot_rebuild/scripts/combat/hero_state.gd",
                            "var attack_cd_base := 0"),
        "boss_type": ("godot_rebuild/scripts/data/hero_definition.gd",
                      "var is_boss_hero"),
    },
    "Minion": {
        "__init__": ("godot_rebuild/scripts/match/prototype_battle.gd",
                     "func scaled_minion_definition("),
        "update": ("godot_rebuild/scripts/combat/minion_battle.gd", "func step_tick()"),
        "apply_slow": ("godot_rebuild/scripts/combat/minion_battle.gd",
                       "func apply_slow(target_id"),
        "_spawn_slash_effect": ("godot_rebuild/bake/bake_minion_combat_fx.py", "slash"),
        "_get_enemies": ("godot_rebuild/scripts/combat/minion_battle.gd",
                         "func _find_target(unit"),
        "_find_target_smart": ("godot_rebuild/scripts/combat/minion_battle.gd",
                               "func _select_ai_target("),
        "_distance_to": ("godot_rebuild/scripts/combat/minion_battle.gd",
                         "func _move_toward(unit"),
        "_move_forward": ("godot_rebuild/scripts/combat/minion_battle.gd",
                          "func _follow_lane("),
        "_move_toward": ("godot_rebuild/scripts/combat/minion_battle.gd",
                         "func _move_toward(unit"),
        "take_damage": ("godot_rebuild/scripts/combat/minion_battle.gd", "func apply_hit("),
        "draw": ("godot_rebuild/bake/bake_minion_atlas.py", "minion.draw("),
        "_draw_death_animation": ("godot_rebuild/bake/bake_minion_atlas.py", "minion.draw("),
    },
    "AIPlayer": {
        "__init__": ("godot_rebuild/scripts/match/ai_policy.gd", "func reset()"),
        "_ai_brain": ("godot_rebuild/scripts/match/ai_policy.gd", "func brain()"),
        "_ai_elite": ("godot_rebuild/scripts/match/ai_policy.gd", "func elite()"),
        "_ai_reserve": ("godot_rebuild/scripts/match/ai_controller.gd", "func reserve("),
        "update": ("godot_rebuild/scripts/match/ai_policy.gd", "func advance("),
        "_ai_step": ("godot_rebuild/scripts/match/ai_controller.gd", "func tick("),
        "_try_build_tower": ("godot_rebuild/scripts/match/ai_build.gd", "func try_build("),
        "_try_upgrade_tower_new": ("godot_rebuild/scripts/match/ai_upgrades.gd",
                                   "func try_tower("),
        "_try_activate_regen_shield": ("godot_rebuild/scripts/match/ai_shields.gd",
                                       "func try_regen("),
        "_control_heroes": ("godot_rebuild/scripts/match/ai_hero_control.gd",
                            "func control_heroes("),
        "_assign_hero_lane": ("godot_rebuild/scripts/match/ai_hero_control.gd",
                              "func assign_hero_lane("),
        "_get_hero_pool": ("godot_rebuild/scripts/match/ai_draft.gd", "func hero_pool()"),
        "_choose_hero_purchase_target": ("godot_rebuild/scripts/match/ai_draft.gd",
                                         "func choose_target("),
        "_try_buy_hero": ("godot_rebuild/scripts/match/ai_recruitment.gd",
                          "func try_buy("),
        "_try_upgrade_hero": ("godot_rebuild/scripts/match/ai_upgrades.gd",
                              "func try_hero("),
        "_try_buy_item": ("godot_rebuild/scripts/match/ai_items.gd", "func try_buy("),
        "_try_activate_castle_shield": ("godot_rebuild/scripts/match/ai_shields.gd",
                                        "func try_castle("),
        "_try_upgrade_nexus": ("godot_rebuild/scripts/match/ai_upgrades.gd",
                               "func try_nexus("),
    },
}
# Methods the pygame tree never reaches, each with the reason it is unreachable.
DEAD_METHODS = {
    "_DummyBulletTarget.__init__": "target palsu; hanya dipakai bake atlas",
    "Castle.get_minion_composition": "tidak ada call site; komposisi wave dari tabel level",
    "Hero.count_enemies_in_range": "tidak ada call site; skill memakai query scoped",
    "Hero.end_damage_scope": "tidak ada call site; scope damage = satu arm skill",
    "Hero.get_skill_cooldowns": "tidak ada call site; HUD memakai cooldowns/cooldown_max",
}
TOP_TARGETS = {
    "credit_hero_damage": ("ported", "godot_rebuild/scripts/match/prototype_battle.gd",
                           "(attacker as HeroState).damage_dealt += dealt",
                           "kredit damage hero di _deliver_hit"),
    "set_damage_school": ("folded", "godot_rebuild/scripts/combat/hero_state.gd",
                          "var dmg_school := \"physical\"",
                          "konteks _ACTIVE_HERO tidak perlu: arm skill mengirim hero.dmg_school"),
    "get_damage_school": ("folded", "godot_rebuild/scripts/combat/hero_projectiles.gd",
                          '"school": hero.dmg_school',
                          "sekolah selalu dibaca dari hero yang menyerang"),
    "_is_physical_hit": ("ported", "godot_rebuild/scripts/combat/unit_state.gd",
                         "physical hit misses", "gate evasi/blind hanya untuk hit fisik"),
    "resolve_damage_school": ("ported", "godot_rebuild/scripts/combat/prototype_battle.gd"
                             if False else "godot_rebuild/scripts/match/prototype_battle.gd",
                              "func _deliver_hit(", "sekolah dikirim eksplisit ke _deliver_hit"),
    "_get_bullet_sprite": ("bake", "godot_rebuild/bake/bake_bullet_atlas.py",
                           "entity._get_bullet_sprite(", "16 arah peluru dibakar ke atlas"),
    "_build_armor_crest": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                           "entity._build_armor_crest(", "crest dibakar per (size, warna, rasio)"),
    "_draw_armor_crest": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                          "entity._build_armor_crest(", "versi gambar dari crest yang sama"),
    "_get_palette": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                     "palette = entity._get_palette(", "palet kastil dipakai saat bake"),
    "_render_castle_full": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                            "entity._render_castle_full(", "kastil utuh dibakar jadi sprite"),
    "_draw_castle_ground": ("dead", "", "", "dimatikan di sumber (komentar \"disabled\")"),
    "_render_castle_lvl6": ("dead", "godot_rebuild/data/art/structures.json", '"castles"',
                            "MAX_NEXUS_LEVEL = 5, cabang level 6 tidak pernah tercapai"),
    "_draw_center_royal_tower": ("dead", "", "",
                                 "hanya dipanggil _render_castle_lvl6 yang tidak tercapai"),
    "_render_dynamic_effects_direct": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                                       "entity._render_dynamic_effects(",
                                       "obor gerbang ikut dibakar sebagai frame flicker"),
    "_render_dynamic_effects": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                                "entity._render_dynamic_effects(", "frame flicker obor"),
    "_draw_gate_torch": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                         "entity._render_dynamic_effects(", "flame obor jadi 5 frame"),
    "_draw_castle_magic_aura": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                                "entity._render_dynamic_effects(", "aura ikut frame bake"),
}
CASTLE_DRAW_TARGET = ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                      "entity._render_castle_full(",
                      "digambar ulang jadi sprite atlas oleh bake_structure_atlas.py")
HERO_DRAW_TARGET = ("bake", "godot_rebuild/bake/bake_hero_atlas.py", "hero.draw(surface)",
                    "pose hero dibakar ke atlas hero")
MINION_DRAW_TARGET = ("bake", "godot_rebuild/bake/bake_minion_atlas.py", "minion.draw(",
                      "minion dibakar ke atlas minion")
ASSIGN_TARGETS = {
    "_BULLET_SPRITE_CACHE": ("bake", "godot_rebuild/bake/bake_bullet_atlas.py",
                             "entity._BULLET_SPRITE_CACHE.clear()", "cache sumber dipakai saat bake"),
    "_TOWER_SPRITE_CACHE": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                            "entity._TOWER_SPRITE_CACHE", "cache tower dipakai saat bake"),
    "_CASTLE_SCALED_CACHE": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                             "entity._render_castle_full(", "cache kastil diskalakan saat bake"),
    "_HERO_UI_CACHE": ("bake", "godot_rebuild/bake/bake_hero_atlas.py",
                       "hero.draw(surface)", "badge/nama hero ikut atlas"),
    "PAL_OUTLINE_C": ("bake", "godot_rebuild/bake/bake_structure_atlas.py",
                      "palette = entity._get_palette(", "warna outline palet kastil"),
    "_ACTIVE_HERO": ("folded", "godot_rebuild/scripts/combat/hero_state.gd",
                     "var dmg_school := \"physical\"", "tidak perlu konteks global"),
}
HERO_PROJECTILE_ASSIGN = ("bake", "godot_rebuild/bake/bake_hero_projectiles.py",
                          "hero._draw_projectile(surface, projectile)",
                          "proyektil hero dibakar terpisah")
HISTOGRAM_KEYS = ("bake", "dead", "deviation", "folded", "meta", "native", "ported")


def source_lines():
    return ENTITY.read_text(encoding="utf-8").splitlines()


def source_tree():
    return ast.parse("\n".join(source_lines()))


def section_of(line):
    for name, start, end in SECTIONS:
        if start <= line <= end:
            return name
    return "unknown"


# ── import the real module ───────────────────────────────────────────────
def _stub_pygame():
    pygame = types.ModuleType("pygame")
    pygame.SRCALPHA = 1

    class _Surface:
        def __init__(self, *args, **kwargs):
            self.width = 8
            self.height = 8

        def get_width(self):
            return self.width

        def get_height(self):
            return self.height

        def get_rect(self, **kwargs):
            return types.SimpleNamespace(x=0, y=0, w=8, h=8)

        def blit(self, *args, **kwargs):
            return None

        def fill(self, *args, **kwargs):
            return None

        def copy(self):
            return self

        def convert(self):
            return self

        def convert_alpha(self):
            return self

        def set_colorkey(self, *args, **kwargs):
            return None

        def set_alpha(self, *args, **kwargs):
            return None

        def subsurface(self, *args, **kwargs):
            return self

    pygame.Surface = _Surface
    for name in ("draw", "transform", "font", "time", "mixer", "gfxdraw", "image"):
        module = types.ModuleType("pygame." + name)
        setattr(pygame, name, module)
        sys.modules["pygame." + name] = module
    pygame.transform.smoothscale = lambda surface, size: surface
    pygame.transform.scale = lambda surface, size: surface
    pygame.transform.rotate = lambda surface, angle: surface
    pygame.transform.flip = lambda surface, *a, **k: surface
    pygame.font.get_init = lambda: True
    pygame.font.SysFont = lambda *a, **k: types.SimpleNamespace(render=lambda *a, **k: _Surface())
    pygame.font.Font = lambda *a, **k: types.SimpleNamespace(render=lambda *a, **k: _Surface())
    sys.modules["pygame"] = pygame


def _core_namespace():
    lines = CORE.read_text(encoding="utf-8").splitlines()
    block = "\n".join(["pass"] * (CORE_SETTINGS_BLOCK[0] - 1) + lines[
        CORE_SETTINGS_BLOCK[0] - 1:CORE_SETTINGS_BLOCK[1]
    ])
    namespace = {"__name__": "_core", "sys": sys, "types": types, "_types": types,
                 "_globals_before_settings": set()}
    exec(compile(block, str(CORE), "exec"), namespace)  # noqa: S102 - source oracle
    module = types.ModuleType("_core")
    module.__dict__.update(namespace)
    sys.modules["_core"] = module
    return module


def _stub_system():
    class SoundManager:
        def play(self, *args, **kwargs):
            return None

    system = types.ModuleType("_system")
    system.SoundManager = SoundManager
    system.FrustumCuller = type("FrustumCuller", (), {"__init__": lambda self, *a, **k: None})
    system.query_enemies_in_range = lambda *a, **k: []
    sys.modules["_system"] = system

    render = types.ModuleType("_render")
    render.get_font = lambda *a, **k: types.SimpleNamespace(
        render=lambda *args, **kwargs: sys.modules["pygame"].Surface()
    )
    render.title_font = render.get_font
    render.MapRenderer = type("MapRenderer", (), {})
    render.EffectManager = type("EffectManager", (), {"__init__": lambda self, *a, **k: None})
    render.clear_cache = lambda *a, **k: None
    sys.modules["_render"] = render


def entity_module():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    _stub_pygame()
    _core_namespace()
    _stub_system()
    sys.modules.pop("_entity", None)
    return importlib.import_module("_entity")


# ── executed cases ───────────────────────────────────────────────────────
def tower_cases(entity, core):
    paths = core.TOWER_UPGRADE_PATHS
    rows = []
    for path in sorted(paths):
        for level in sorted(int(key) for key in paths[path]):
            tower = entity.Tower(0.0, 0.0, "blue")
            tower.tower_type = path
            tower.level = level
            tower._apply_level_stats()
            rows.append({
                "path": path,
                "level": level,
                "max_hp": int(tower.max_hp),
                "damage": int(tower.damage),
                "range": int(tower.range),
                "cd": int(tower.attack_cooldown),
                "shield_max": int(tower.shield_max),
                "armor": int(tower.armor),
                "magic_resist": float(tower.magic_resist),
                "splash": int(tower.splash),
                "slow": float(tower.slow),
                "atk_slow": float(tower.atk_slow),
                "skill_down": float(tower.skill_down),
                "anti_heal": float(tower.anti_heal),
                "burn_dps": float(tower.burn_dps),
                "upgrade_cost": int(tower.upgrade_cost()),
                "sell_value": int(tower.sell_value()),
                # `_core.py` sell path: `sell_val = tower.sell_value()` then
                # `if sell_val == 0: sell_val = 50  # refund 50% dari 100G`
                "transaction_refund": int(tower.sell_value()) or 50,
            })
    switch = {}
    for path in sorted(paths):
        tower = entity.Tower(0.0, 0.0, "blue")
        switch[path] = int(tower.upgrade_cost(path))
    red = entity.Tower(0.0, 0.0, "red")
    red.level = 3
    red._apply_level_stats()
    shield_sale = entity.Tower(0.0, 0.0, "blue")
    shield_sale.level = 4
    shield_sale._apply_level_stats()
    plain_sale = int(shield_sale.sell_value())
    shield_sale.regen_shield_active = True
    return {
        "levels": rows,
        "path_switch_cost": switch,
        "red_sell_value": int(red.sell_value()),
        "sell_value_without_shield": plain_sale,
        "sell_value_with_shield": int(shield_sale.sell_value()),
        "transaction_refund_with_shield": int(shield_sale.sell_value()) or 50,
    }


def nexus_cases(entity, core):
    levels = []
    for level in range(1, len(core.NEXUS_LEVELS) + 1):
        castle = entity.Castle(0.0, 0.0, "blue")
        for _ in range(level - 1):
            castle.upgrade()
        levels.append({
            "level": castle.level,
            "max_hp": int(castle.max_hp),
            "hp": int(castle.hp),
            "damage": int(castle.damage),
            "range": int(castle.range),
            "cd": int(castle.attack_cooldown),
            "shield_max": int(castle.shield_max),
            "upgrade_cost": int(castle.upgrade_cost()),
            "shield_cost": int(castle.castle_shield_cost()),
        })
    damaged = entity.Castle(0.0, 0.0, "blue")
    damaged.hp = int(damaged.max_hp * 0.4)
    before = damaged.hp
    damaged.upgrade()
    shielded = entity.Castle(0.0, 0.0, "blue")
    shielded.castle_shield_purchased = True
    shielded.shield = int(shielded.shield_max * 0.5)
    shielded.upgrade()
    waves = {}
    for wave in (9, 10, 11):
        castle = entity.Castle(0.0, 0.0, "blue")
        castle.set_wave(wave)
        waves[str(wave)] = {
            "free": bool(castle.free_shield_active),
            "active": bool(castle.shield_active),
            "shield": int(castle.shield),
        }
    return {
        "levels": levels,
        "damaged_upgrade": {"before": before, "after": int(damaged.hp),
                            "max_hp": int(damaged.max_hp)},
        "shield_ratio_upgrade": {
            "ratio_before": 0.5,
            "shield_max": int(shielded.shield_max),
            "shield": int(shielded.shield),
        },
        "waves": waves,
    }


def minion_cases(entity, core):
    rows = []
    for minion_type in sorted(core.MINION_TYPES):
        for nexus in range(1, len(core.NEXUS_LEVELS) + 1):
            random.seed("entity:%s:%d" % (minion_type, nexus))
            minion = entity.Minion(minion_type, "blue", "mid", nexus)
            rows.append({
                "type": minion_type,
                "nexus": nexus,
                "max_hp": int(minion.max_hp),
                "damage": int(minion.damage),
                "speed": round(float(minion.speed), 6),
                "cd": int(minion.attack_cooldown),
                "gold": int(minion.gold_reward),
                "regen": round(float(minion.regen), 6),
                "armor": float(minion.armor),
                "magic_resist": float(minion.magic_resist),
            })
    return rows


class _FakeUnit:
    def __init__(self, x, y, team, name):
        self.x = float(x)
        self.y = float(y)
        self.team = team
        self.alive = True
        self.name = name
        self.hits = []
        self.debuffs = []
        self.slows = []

    def take_damage(self, amount, team, damage_type=None):
        self.hits.append({"amount": int(amount), "team": team, "type": damage_type})

    def apply_debuff(self, kind, amount, duration, source_team=None):
        self.debuffs.append({"kind": kind, "amount": amount, "duration": int(duration)})

    def apply_slow(self, amount, duration):
        self.slows.append({"amount": float(amount), "duration": int(duration)})


def bullet_cases(entity):
    rows = []
    cases = [
        ("normal", "normal", {}, []),
        ("cannon", "cannon", {"splash": 40, "burn_dps": 7, "burn_duration": 90}, []),
        ("ice", "ice", {"slow": 0.35, "slow_duration": 90, "atk_slow": 0.25,
                        "slow_aoe": 60}, []),
        ("mage", "mage", {"skill_down": 0.2, "anti_heal": 0.3, "debuff_duration": 120}, []),
    ]
    for label, bullet_type, special, _ in cases:
        target = _FakeUnit(0, 0, "red", "target")
        near = _FakeUnit(20, 0, "red", "near")
        far = _FakeUnit(200, 0, "red", "far")
        ally = _FakeUnit(10, 0, "blue", "ally")
        units = [target, near, far, ally]
        bullet = entity.Bullet(0.0, 100.0, target, 50, "blue", bullet_type, dict(special))
        start = {"x": bullet.x, "y": bullet.y}
        bullet.update(units)
        after_one = {"x": round(bullet.x, 6), "y": round(bullet.y, 6)}
        travel = 0
        while bullet.active and travel < 40:
            bullet.update(units)
            travel += 1
        rows.append({
            "bullet": label,
            "speed": float(bullet.speed),
            "start": start,
            "after_one_tick": after_one,
            "ticks_to_hit": travel,
            "units": {
                unit.name: {
                    "hits": unit.hits,
                    "debuffs": unit.debuffs,
                    "slows": unit.slows,
                }
                for unit in units
            },
        })
    return rows


def school_cases(entity):
    rows = []
    cases = [
        ("explicit physical", dict(damage_type="normal", school="physical")),
        ("fire ignores school", dict(damage_type="fire", school="physical")),
        ("crit ignores school", dict(damage_type="crit")),
        ("attacker magic", dict(damage_type="normal", source_school="magic")),
        ("context hero magic on hero", dict(damage_type="normal", target_is_hero=True,
                                           active_school="magic")),
        ("context hero magic on structure", dict(damage_type="normal",
                                                 target_is_hero=False,
                                                 active_school="magic")),
        ("no context", dict(damage_type="normal")),
    ]

    class _Src:
        def __init__(self, school):
            self.dmg_school = school

    for label, case in cases:
        active = _FakeUnit(0, 0, "blue", "active")
        active.dmg_school = case.get("active_school", "physical")
        entity.set_damage_school(active if case.get("active_school") else None)
        source = _Src(case["source_school"]) if case.get("source_school") else None
        result = entity.resolve_damage_school(
            case.get("damage_type", "normal"), source, case.get("school"),
            case.get("target_is_hero"),
        )
        rows.append({"case": label, "school": result,
                     "physical_hit": bool(entity._is_physical_hit(
                         case.get("damage_type", "normal"), result))})
    entity.set_damage_school(None)
    physical = []
    for damage_type in ("normal", "projectile", "fire", "ice", "heal", "crit"):
        for school in ("physical", "magic", None):
            physical.append({"damage_type": damage_type, "school": school,
                             "physical": bool(entity._is_physical_hit(damage_type, school))})
    return {"resolution": rows, "physical_gate": physical}


# ── inventory ────────────────────────────────────────────────────────────
def inventory():
    lines = source_lines()
    tree = source_tree()
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    methods = sum(len([m for m in node.body if isinstance(m, ast.FunctionDef)])
                  for node in classes)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    assigns = [node for node in tree.body if isinstance(node, ast.Assign)]
    return {
        "file": "_entity.py",
        "lines": len(lines),
        "sections": len(SECTIONS),
        "classes": len(classes),
        "methods": methods,
        "top_functions": len(functions),
        "assigns": len(assigns),
    }


def section_ranges():
    rows = []
    for index, (name, start, end) in enumerate(SECTIONS):
        rows.append({"name": name, "start": start, "end": end, "lines": end - start + 1})
        if index + 1 < len(SECTIONS) and SECTIONS[index + 1][1] != end + 1:
            raise AssertionError("sections are not contiguous at %s" % name)
    return rows


def _called_names():
    found = set()
    for path in sorted(ROOT.rglob("*.py")):
        relative = str(path.relative_to(ROOT))
        if relative.startswith(("godot_rebuild", "bake")) or "__pycache__" in relative:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name:
                    found.add(name)
            elif isinstance(node, ast.Attribute):
                found.add(node.attr)
    return found


def _func_names(target):
    text = (ROOT / target).read_text(encoding="utf-8")
    import re
    return set(re.findall(r"^(?:static )?func ([a-zA-Z0-9_]+)\(", text, re.M)), text


def symbol_rows():
    tree = source_tree()
    called = _called_names()
    rows = []

    for name, _, _ in SECTIONS:
        kind, target, token, note = MODULE_TARGETS[name]
        rows.append({"symbol": "module:%s" % name, "kind": kind, "target": target,
                     "token": token, "note": note})

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        kind, target, token, note = CLASS_TARGETS[node.name]
        rows.append({"symbol": "class:%s" % node.name, "kind": kind, "target": target,
                     "token": token, "note": note})
        names, _ = _func_names(target) if not target else (set(), "")
        for method in node.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            symbol = "class:%s.%s" % (node.name, method.name)
            reason = DEAD_METHODS.get(symbol)
            if reason:
                rows.append({"symbol": symbol, "kind": "dead", "target": "",
                             "token": "", "note": reason})
                continue
            alias = METHOD_ALIASES.get(node.name, {}).get(method.name)
            if alias:
                alias_target, alias_token = alias
                alias_kind = "bake" if alias_target.startswith("godot_rebuild/bake/") \
                    else "ported"
                rows.append({"symbol": symbol, "kind": alias_kind, "target": alias_target,
                             "token": alias_token,
                             "note": "hook %s.%s" % (node.name, method.name)})
                continue
            if node.name == "Castle" and method.name.startswith("_draw"):
                rows.append({"symbol": symbol, "kind": "bake",
                             "target": CASTLE_DRAW_TARGET[1], "token": CASTLE_DRAW_TARGET[2],
                             "note": "visual %s.%s dibakar ke atlas" % (node.name,
                                                                        method.name)})
                continue
            if method.name in names:
                rows.append({"symbol": symbol, "kind": "ported", "target": target,
                             "token": "func %s(" % method.name, "note": ""})
                continue
            if method.name not in called:
                rows.append({"symbol": symbol, "kind": "dead", "target": "", "token": "",
                             "note": "tidak ada call-site di pohon pygame"})
                continue
            rows.append({"symbol": symbol, "kind": "folded", "target": target, "token": token,
                         "note": "dijalankan alur %s tanpa fungsi 1:1"
                                 % target.split("/")[-1]})

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name in TOP_TARGETS:
            kind, target, token, note = TOP_TARGETS[node.name]
        elif node.name.startswith(("_draw_", "_render_", "_overlay_")):
            kind, target, token, note = CASTLE_DRAW_TARGET
            note = "%s digambar ulang jadi sprite atlas" % node.name
        else:
            raise AssertionError("unmapped module function: %s" % node.name)
        rows.append({"symbol": "top:%s@%d" % (node.name, node.lineno), "kind": kind,
                     "target": target, "token": token, "note": note})

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for assign_target in node.targets:
            if not isinstance(assign_target, ast.Name):
                continue
            name = assign_target.id
            if name.startswith("_HERO_PROJ_"):
                kind, target, token, note = HERO_PROJECTILE_ASSIGN
            elif name in ASSIGN_TARGETS:
                kind, target, token, note = ASSIGN_TARGETS[name]
            else:
                raise AssertionError("unmapped module assign: %s" % name)
            rows.append({"symbol": "assign:%s" % name, "kind": kind, "target": target,
                         "token": token, "note": note})
    return _dedupe(rows)


def _dedupe(rows):
    unique = {}
    order = []
    for row in rows:
        name = row["symbol"]
        if name in unique:
            merged = [text for text in (unique[name]["note"], row["note"]) if text]
            unique[name]["note"] = ", ".join(dict.fromkeys(merged))
            continue
        unique[name] = row
        order.append(name)
    return [unique[name] for name in order]


def duplicates():
    tree = source_tree()
    found = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            found.setdefault(node.name, []).append(node.lineno)
        elif isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef):
                    key = "class:%s.%s" % (node.name, member.name)
                    found.setdefault(key, []).append(member.lineno)
    return {name: {"lines": lines, "copies": len(lines)}
            for name, lines in found.items() if len(lines) > 1}


# ── fixture ──────────────────────────────────────────────────────────────
def source_fixture():
    entity = entity_module()
    core = sys.modules["_core"]
    rows = symbol_rows()
    histogram = {}
    for row in rows:
        histogram[row["kind"]] = histogram.get(row["kind"], 0) + 1
    return {
        "file": inventory(),
        "sections": section_ranges(),
        "symbols": {"count": len(rows), "kinds": histogram},
        "classification": {row["symbol"]: {"kind": row["kind"], "target": row["target"],
                                           "token": row["token"], "note": row["note"]}
                           for row in rows},
        "dead_helpers": sorted(row["symbol"] for row in rows if row["kind"] == "dead"),
        "duplicates": duplicates(),
        "towers": tower_cases(entity, core),
        "nexus": nexus_cases(entity, core),
        "minions": minion_cases(entity, core),
        "bullets": bullet_cases(entity),
        "school": school_cases(entity),
        "constants": {
            "BULLET_SPEED": int(core.BULLET_SPEED),
            "BULLET_RADIUS": int(core.BULLET_RADIUS),
            "TOWER_MAX_LEVEL": int(core.TOWER_MAX_LEVEL),
            "MAX_NEXUS_LEVEL": int(core.MAX_NEXUS_LEVEL),
            "TOWER_REGEN_SHIELD_COST": int(core.TOWER_REGEN_SHIELD_COST),
            "CASTLE_SHIELD_COST": int(core.CASTLE_SHIELD_COST),
            "CASTLE_SHIELD_FREE_WAVES": int(core.CASTLE_SHIELD_FREE_WAVES),
            "CASTLE_SHIELD_DAMAGE_REDUCTION": float(core.CASTLE_SHIELD_DAMAGE_REDUCTION),
            "CASTLE_SHIELD_HP_RATIO": float(core.CASTLE_SHIELD_HP_RATIO),
            "TOWER_HP_MULTIPLIER": float(core.TOWER_HP_MULTIPLIER),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    data = source_fixture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        print("wrote %s (%d symbols, %d tower rows, %d nexus rows, %d minion rows)" % (
            FIXTURE, data["symbols"]["count"], len(data["towers"]["levels"]),
            len(data["nexus"]["levels"]), len(data["minions"])))
        return 0
    existing = json.loads(FIXTURE.read_text(encoding="utf-8")) if FIXTURE.exists() else None
    if args.check and existing != data:
        print("FAIL: fixture is stale; rerun with --write")
        return 1
    print(json.dumps({"file": data["file"], "kinds": data["symbols"]["kinds"],
                      "dead": len(data["dead_helpers"])}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
