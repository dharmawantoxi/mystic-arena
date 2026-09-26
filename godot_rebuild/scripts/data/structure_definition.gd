extends "res://scripts/data/minion_definition.gd"
## Same common combat fields, separate stationary validation and shield/regen configuration.

@export var level: int = 1
@export var volley_count: int = 1
@export var bow_platform_height: float = 38.0
@export var upgrade_price: int = 0
@export var sale_refund: int = 50
@export_enum("tower", "nexus") var structure_kind: String = "tower"
@export_enum("archer", "cannon", "ice", "mage") var tower_path: String = "archer"
@export var splash_radius_px: float = 0.0
@export var burn_dps: float = 0.0
@export var burn_duration_ticks: int = 0
@export var slow_amount: float = 0.0
@export var slow_duration_ticks: int = 0
@export var atk_slow_amount: float = 0.0
@export var slow_aoe_px: float = 0.0
@export var skill_down_amount: float = 0.0
@export var anti_heal_amount: float = 0.0
@export var debuff_duration_ticks: int = 0
@export var chain_count: int = 1
@export var shield_capacity: float = 800.0
@export var hp_regen_delay_ticks: int = 300
@export var shield_regen_enabled: bool = false
@export var shield_regen_delay_ticks: int = 180
@export var shield_regen_per_tick: float = 1.8
@export var shield_damage_reduction: float = 0.0
@export var free_shield_waves: int = 10
@export var projectile_speed_px_per_tick: float = 8.0
@export var projectile_hit_radius_px: float = 4.0


func is_valid() -> bool:
	return (
		structure_kind in ["tower", "nexus"]
		and tower_path in ["archer", "cannon", "ice", "mage"]
		and splash_radius_px >= 0
		and burn_dps >= 0
		and burn_duration_ticks >= 0
		and slow_amount >= 0
		and slow_amount <= 1
		and slow_duration_ticks >= 0
		and atk_slow_amount >= 0
		and atk_slow_amount <= 1
		and slow_aoe_px >= 0
		and skill_down_amount >= 0
		and skill_down_amount <= 1
		and anti_heal_amount >= 0
		and anti_heal_amount <= 1
		and debuff_duration_ticks >= 0
		and chain_count >= 1
		and level >= 1
		and level <= 6
		and volley_count >= 1
		and volley_count <= 3
		and bow_platform_height > 0
		and upgrade_price >= 0
		and sale_refund >= 0
		and not id.is_empty()
		and max_hp > 0
		and damage > 0
		and attack_range_px > 0
		and attack_cooldown_ticks > 0
		and gold_reward >= 0
		and radius_px > 0
		and shield_capacity >= 0
		and regen_per_tick >= 0
		and hp_regen_delay_ticks >= 0
		and shield_regen_delay_ticks >= 0
		and shield_regen_per_tick >= 0
		and magic_resist >= 0
		and magic_resist <= 1
		and free_shield_waves >= 0
		and shield_damage_reduction >= 0
		and shield_damage_reduction <= 1
		and projectile_speed_px_per_tick > 0
		and projectile_hit_radius_px > 0
	)
