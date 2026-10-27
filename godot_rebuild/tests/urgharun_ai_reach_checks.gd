extends RefCounted
## Layer 9bq12 pins the source gap that motivated slice 9bq13: Python has Urgharun skill stats but
## no Urgharun AI recipe. The user later authorized a native R-only extension, whose behavior is
## exercised separately by `urgharun_ai_skill_checks.gd`.

const FIXTURE := "res://tests/fixtures/urgharun_ai_reach_source.json"
const BOSS_AI_PATH := "res://scripts/match/boss_ai.gd"
const BOSS := "urgharun"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Urgharun source reach fixture parses")
	if not (data is Dictionary):
		return
	_check_source(check, data)
	_check_native_extension(check)


func _check_source(check: Callable, data: Dictionary) -> void:
	check.call(
		(
			String(data["subject"]) == BOSS
			and int(data["dispatch_count"]) == 79
			and int(data["smart_ai_method_count"]) == 79
		),
		"Python Boss.update has 79 smart-AI arms and 79 `_smart_ai_*` methods"
	)
	check.call(
		(
			not bool(data["dispatch_has_subject"])
			and not bool(data["smart_ai_has_subject"])
			and (data["subject_writers"] as Array).is_empty()
		),
		"The Python source gap is confirmed: no Urgharun recipe or active_skill writer"
	)
	var keys: Array = data["active_skill_keys"]
	check.call(
		keys.has("q") and keys.has("w") and keys.has("e") and keys.has("r"),
		"Other source recipes write the q/w/e/r keys consumed by Urgharun's skill FX"
	)
	var stats: Dictionary = data["stats"]
	check.call(
		(
			String(stats["boss_class"]) == "mini"
			and int(stats["skill_count"]) == 8
			and int(stats["skill_q_cooldown"]) == 425
			and int(stats["skill_r_damage"]) == 2275
		),
		"Urgharun has skill data in Python despite having no AI recipe"
	)
	var head: Array = data["dispatch_head"]
	var tail: Array = data["dispatch_tail"]
	check.call(
		(
			head.size() == 5
			and tail.size() == 5
			and String(head[0]) == "abaddon"
			and String(tail[4]) == "morthraxis"
		),
		"The harvested Python dispatch chain remains pinned at both ends"
	)


func _check_native_extension(check: Callable) -> void:
	var text := FileAccess.get_file_as_string(BOSS_AI_PATH)
	check.call(
		(
			text.contains(
				'"urgharun":\n\t\t\t_urgharun(world, boss, enemies, target, target_distance)'
			)
			and text.contains("static func _urgharun(")
		),
		"The user-authorized native R extension now fills the source reachability gap"
	)
	check.call(
		text.contains("_:\n\t\t\t_generic(world, boss, enemies)"),
		"The generic fallback remains available for bosses without a dedicated recipe"
	)
