extends Resource
## Tier-1 source stats. Definitions are read-only; current HP/timers belong to UnitState.

@export var id: String = "goblin"
@export var display_name: String = "Goblin"
@export var max_hp: int = 45
@export var damage: int = 5
@export var speed_px_per_tick: float = 1.5
@export var attack_range_px: float = 25.0
@export var attack_cooldown_ticks: int = 45
@export var gold_reward: int = 8
@export var radius_px: float = 9.0
@export var regen_per_tick: float = 0.0
@export var armor: float = 0.0
@export var magic_resist: float = 0.0


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
	)
