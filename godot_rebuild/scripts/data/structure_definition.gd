extends "res://scripts/data/minion_definition.gd"
## Same common combat fields, separate stationary validation and shield/regen configuration.

@export_enum("tower", "nexus") var structure_kind: String = "tower"
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
