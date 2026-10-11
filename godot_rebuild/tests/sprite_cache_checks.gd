extends RefCounted
## Replays the source SpriteCache oracle through the state-only Godot port.
## The source Surface callback is represented by Dictionary metadata; no pixels
## or pygame drawing are reproduced here.

const SpriteCache = preload("res://scripts/ui/sprite_cache.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const FIXTURE := "res://tests/fixtures/sprite_cache_source.json"

var _render_calls := 0
var _render_marker := ""
var _render_bounds: Array = [0, 0, 0, 0]


func run(check: Callable) -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(parsed is Dictionary, "Sprite cache fixture parses")
	if not (parsed is Dictionary):
		return
	var data: Dictionary = parsed
	check.call(
		int(data["default_max_cache"]) == SpriteCache.DEFAULT_MAX_CACHE,
		"Sprite cache capacity matches source"
	)
	check.call(bool(data["singleton_same_instance"]), "Source singleton construction is stable")
	SpriteCache.reset_shared()
	var shared_one: SpriteCache = SpriteCache.get_shared()
	var shared_two: SpriteCache = SpriteCache.get_shared()
	check.call(shared_one == shared_two, "Godot shared sprite cache returns one instance")
	check.call(
		int(shared_one.get_state()["max_cache"]) == SpriteCache.DEFAULT_MAX_CACHE,
		"Godot shared sprite cache uses source capacity"
	)
	for case_value in data["cases"]:
		_replay_case(case_value as Dictionary, check)
	_check_shortcuts(check)
	_check_runtime_wiring(check)


func _replay_case(case_data: Dictionary, check: Callable) -> void:
	var cache: SpriteCache = SpriteCache.new()
	cache.set_max_cache(int(case_data["max_cache"]))
	_render_calls = 0
	var operations: Array = case_data["operations"]
	var outputs: Array = case_data["outputs"]
	var label: String = String(case_data["name"])
	check.call(
		int(cache.get_state()["max_cache"]) == int(case_data["max_cache"]),
		"Configured sprite cache capacity matches fixture: %s" % label
	)
	for index in range(operations.size()):
		var operation: Dictionary = operations[index]
		var expected: Dictionary = outputs[index]
		var operation_label := "%s operation %d" % [label, index]
		var op: String = String(operation["op"])
		if op == "full":
			_render_marker = String(operation["marker"])
			_render_bounds = (operation.get("bounds", [0, 0, 0, 0]) as Array).duplicate()
			var surface: Variant = cache.get_or_render(
				operation["key"],
				int(operation["width"]),
				int(operation["height"]),
				Callable(self, "_render_surface")
			)
			_check_surface(
				cache.get_surface_snapshot(surface),
				expected["surface"] as Dictionary,
				check,
				operation_label
			)
		elif op == "cropped":
			_render_marker = String(operation["marker"])
			_render_bounds = (operation.get("bounds", [0, 0, 0, 0]) as Array).duplicate()
			var cropped_result: Array = cache.get_or_render_cropped(
				operation["key"],
				int(operation["width"]),
				int(operation["height"]),
				Callable(self, "_render_surface"),
				operation.get("anchor", null)
			)
			_check_surface(
				cache.get_surface_snapshot(cropped_result[0]),
				expected["surface"] as Dictionary,
				check,
				operation_label
			)
			var expected_anchor: Array = expected["anchor"] as Array
			check.call(
				(
					int(cropped_result[1]) == int(expected_anchor[0])
					and int(cropped_result[2]) == int(expected_anchor[1])
				),
				"Cropped anchor matches source: %s" % operation_label
			)
		elif op == "invalidate":
			cache.invalidate(operation.get("prefix", null))
		elif op == "clear":
			cache.clear()
		elif op == "stats":
			pass
		else:
			check.call(false, "Unknown sprite cache operation: %s" % op)
		_check_render_calls(expected, check, operation_label)
		_check_stats(cache, expected["stats"] as Dictionary, check, operation_label)


func _render_surface(surface: Variant) -> void:
	_render_calls += 1
	var value: Dictionary = surface
	value["marker"] = _render_marker
	value["bounds"] = _render_bounds.duplicate()


func _check_surface(got: Dictionary, expected: Dictionary, check: Callable, label: String) -> void:
	check.call(
		(
			int(got["width"]) == int(expected["width"])
			and int(got["height"]) == int(expected["height"])
		),
		"Cached surface size matches source: %s" % label
	)
	check.call(
		got.get("marker", null) == expected.get("marker", null),
		"Cached surface callback state matches source: %s" % label
	)


func _check_render_calls(expected: Dictionary, check: Callable, label: String) -> void:
	check.call(
		_render_calls == int(expected["render_calls"]),
		"Render callback count matches source: %s" % label
	)


func _check_stats(cache: SpriteCache, expected: Dictionary, check: Callable, label: String) -> void:
	var got: Dictionary = cache.get_stats()
	check.call(
		(
			int(got["cached"]) == int(expected["cached"])
			and int(got["hits"]) == int(expected["hits"])
			and int(got["misses"]) == int(expected["misses"])
			and String(got["hit_rate"]) == String(expected["hit_rate"])
		),
		"Cache statistics match source: %s" % label
	)


func _check_shortcuts(check: Callable) -> void:
	SpriteCache.reset_shared()
	_render_calls = 0
	_render_marker = "shortcut"
	_render_bounds = [1, 2, 3, 4]
	var callback := Callable(self, "_render_surface")
	var first: Variant = SpriteCache.get_cached_sprite("shortcut", 20, 21, callback)
	var second: Variant = SpriteCache.get_cached_sprite("shortcut", 1, 1, callback)
	var shared: SpriteCache = SpriteCache.get_shared()
	check.call(
		(
			shared.get_surface_snapshot(first)["width"] == 20
			and shared.get_surface_snapshot(second)["width"] == 20
			and _render_calls == 1
		),
		"Global full-surface shortcuts share the source cache"
	)
	var cropped: Array = SpriteCache.get_cached_sprite_cropped(
		"shortcut-cropped", 30, 40, callback, [3, 4]
	)
	check.call(
		int(cropped[1]) == 2 and int(cropped[2]) == 2 and _render_calls == 2,
		"Global cropped shortcut preserves anchor adjustment"
	)
	SpriteCache.clear_sprite_cache()
	var stats: Dictionary = shared.get_stats()
	check.call(
		int(stats["cached"]) == 0 and int(stats["hits"]) == 1 and int(stats["misses"]) == 2,
		"Global clear shortcut clears entries without resetting counters"
	)


func _check_runtime_wiring(check: Callable) -> void:
	SpriteCache.reset_shared()
	var world := Prototype.new()
	var shared: SpriteCache = SpriteCache.get_shared()
	var initial_state: Dictionary = world.sprite_cache.get_state()
	check.call(
		(
			world.sprite_cache == shared
			and world.effects.sprite_cache == shared
			and int(initial_state["cached"]) == 3
			and int(initial_state["misses"]) == 3
		),
		"Prototype wires shared SpriteCache and caches map/shop assets on init"
	)
	world._configure_map_renderer()
	var reconfigured_state: Dictionary = world.sprite_cache.get_state()
	check.call(
		int(reconfigured_state["cached"]) == 3 and int(reconfigured_state["hits"]) == 3,
		"Re-configuring same map theme reuses cached SpriteCache surfaces"
	)
	check.call(world.setup_arena(), "Arena setup succeeds for SpriteCache hero wiring")
	var after_arena: Dictionary = world.sprite_cache.get_state()
	check.call(
		int(after_arena["cached"]) == 5 and int(after_arena["misses"]) == 5,
		"Arena setup caches blue and red hero sprites in SpriteCache"
	)
	var boss = world._spawn_boss("gornak")
	world.effects.add_death_explosion(200.0, 200.0, "red", "large")
	world.effects.add_death_explosion(220.0, 220.0, "red", "large")
	var after_boss_and_fx: Dictionary = world.cache_stats()["sprite_cache"]
	check.call(
		(
			boss != null
			and int(after_boss_and_fx["cached"]) == 7
			and int(after_boss_and_fx["hits"]) == 4
		),
		"Boss spawn and repeated death explosion reuse SpriteCache entries"
	)
