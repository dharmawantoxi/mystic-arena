class_name RenderQuality
extends RefCounted

## Native equivalent of mobile.perf.Quality budgets used by _render.py.
## LOW/MEDIUM/HIGH keep the same damage-number budget and particle ratio.
const PRESETS := {
	"low":
	{
		"max_damage_numbers": 8,
		"particle_ratio": 0.35,
		"particles": true,
		"fog": false,
		"cheap_alpha": true,
		"floating_decor": false,
	},
	"medium":
	{
		"max_damage_numbers": 16,
		"particle_ratio": 0.65,
		"particles": true,
		"fog": true,
		"cheap_alpha": true,
		"floating_decor": false,
	},
	"high":
	{
		"max_damage_numbers": 32,
		"particle_ratio": 1.0,
		"particles": true,
		"fog": true,
		"cheap_alpha": false,
		"floating_decor": true,
	},
}


static func preset(level: String) -> Dictionary:
	var result: Dictionary = PRESETS.get(level, PRESETS.high).duplicate()
	result["level"] = level if PRESETS.has(level) else "high"
	return result


static func from_settings(values: Dictionary) -> Dictionary:
	return preset(str(values.get("render_quality", "high")))
