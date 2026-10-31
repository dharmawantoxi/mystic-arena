extends "res://scripts/ui/effect_manager.gd"
## Records the presentation calls the tactical manager makes, mirroring the
## `Effects` stub in `tests/tactical_command_source_oracle.py`. The source wraps
## every effect call in `try/except`, so a missing marker burst is invisible from
## the outside; recording the calls makes them part of the checked contract.

var calls: Array = []


func add_damage_number(
	x: float,
	y: float,
	damage: Variant,
	is_critical: bool = false,
	_damage_type: String = "normal",
	_offset_x: float = NAN,
	_offset_y: float = NAN,
	_drift: float = NAN
) -> void:
	calls.append({
		"kind": "damage_number",
		"x": snappedf(x, 0.001),
		"y": snappedf(y, 0.001),
		"text": String(damage),
		"critical": is_critical,
	})


func add_death_explosion(
	x: float,
	y: float,
	team: String = "red",
	size: String = "medium",
	_particle_specs: Array = []
) -> void:
	calls.append({
		"kind": "death_explosion",
		"x": snappedf(x, 0.001),
		"y": snappedf(y, 0.001),
		"team": team,
		"size": size,
	})
