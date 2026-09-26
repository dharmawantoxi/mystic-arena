extends "res://scripts/data/minion_definition.gd"
## Base hero stats. The inherited L1 numbers (max_hp/damage/speed/range/
## cooldown) are post-catchup/post-normalization finals, the same folding
## convention as tower level .tres files: the source computes them at
## runtime (Hero.__init__ melee norm + hero_balance catch-up) and the
## Kaizen oracle locks the resulting values. HERO_LEVELS is global: one
## table for every hero (_core.py HERO_LEVELS), copied verbatim.

const MAX_HERO_LEVEL := 15
const HERO_LEVELS := [
	{"hp_mult": 1.0, "dmg_mult": 1.0, "skill_mult": 1.0, "upgrade_cost": 300},
	{"hp_mult": 1.3, "dmg_mult": 1.25, "skill_mult": 1.2, "upgrade_cost": 500},
	{"hp_mult": 1.65, "dmg_mult": 1.55, "skill_mult": 1.45, "upgrade_cost": 800},
	{"hp_mult": 2.1, "dmg_mult": 1.9, "skill_mult": 1.75, "upgrade_cost": 1200},
	{"hp_mult": 2.7, "dmg_mult": 2.4, "skill_mult": 2.1, "upgrade_cost": 1800},
	{"hp_mult": 3.35, "dmg_mult": 2.9, "skill_mult": 2.5, "upgrade_cost": 2600},
	{"hp_mult": 4.05, "dmg_mult": 3.45, "skill_mult": 2.95, "upgrade_cost": 3600},
	{"hp_mult": 4.8, "dmg_mult": 4.05, "skill_mult": 3.45, "upgrade_cost": 4800},
	{"hp_mult": 5.6, "dmg_mult": 4.7, "skill_mult": 4.0, "upgrade_cost": 6200},
	{"hp_mult": 6.5, "dmg_mult": 5.4, "skill_mult": 4.6, "upgrade_cost": 8000},
	{"hp_mult": 7.5, "dmg_mult": 6.2, "skill_mult": 5.2, "upgrade_cost": 10200},
	{"hp_mult": 8.6, "dmg_mult": 7.0, "skill_mult": 5.9, "upgrade_cost": 12800},
	{"hp_mult": 9.8, "dmg_mult": 7.9, "skill_mult": 6.6, "upgrade_cost": 15800},
	{"hp_mult": 11.1, "dmg_mult": 8.9, "skill_mult": 7.4, "upgrade_cost": 19200},
	{"hp_mult": 12.5, "dmg_mult": 10.0, "skill_mult": 8.2, "upgrade_cost": 0},
]

@export var title: String = "The Wind Blade"
@export var role: String = "Assassin"
@export var cost: int = 400
@export var unlock_cost: int = 0
@export var base_skill: int = 70
@export var skill_cooldown_max: int = 300
@export var skill_range_px: float = 100.0
@export_enum("physical", "magic") var dmg_school: String = "physical"
@export var is_melee: bool = true
# Kaizen Q numbers. Mechanics are Kaizen's kit; the battle reads the
# numbers from here so later heroes reuse the shape with their own data.
@export var q_reset_ticks: int = 180
@export var q_dash_ticks: int = 15
@export var q2_radius_px: float = 80.0
@export var q2_mult: float = 1.5
@export var q_reach_slack: float = 1.15
@export var q_visual_ticks: int = 60
@export var w_cooldown_max: int = 240
@export var e_cooldown_max: int = 420
@export var r_cooldown_max: int = 900


static func level_data(level: int) -> Dictionary:
	return HERO_LEVELS[clampi(level, 1, MAX_HERO_LEVEL) - 1]


func is_valid() -> bool:
	return (
		not id.is_empty()
		and max_hp > 0
		and damage > 0
		and speed_px_per_tick > 0
		and attack_range_px > 0
		and attack_cooldown_ticks > 0
		and gold_reward >= 0
		and radius_px > 0
		and regen_per_tick >= 0
		and magic_resist >= 0
		and magic_resist <= 1
		and not title.is_empty()
		and not role.is_empty()
		and cost >= 0
		and unlock_cost >= 0
		and base_skill > 0
		and skill_cooldown_max > 0
		and skill_range_px > 0
		and dmg_school in ["physical", "magic"]
		and q_reset_ticks > 0
		and q_dash_ticks > 0
		and q2_radius_px > 0
		and q2_mult > 0
		and q_reach_slack >= 1.0
		and q_visual_ticks > 0
		and w_cooldown_max >= 0
		and e_cooldown_max >= 0
		and r_cooldown_max >= 0
	)
