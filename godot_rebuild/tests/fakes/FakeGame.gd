class_name FakeGame
extends GameplayPort

var ticks := 0
var holds: Array[String] = []
var events: Array[String] = []
var cinematic := false
var ready_for_combat := true


func combat_ready() -> bool:
	return ready_for_combat


func simulation_step() -> void:
	ticks += 1


func hold_begin(action: String, _follow_mouse := false) -> void:
	holds.append(action)
	events.append("start:" + action)


func hold_end(action: String) -> void:
	holds.erase(action)
	events.append("end:" + action)


func release_all_holds() -> void:
	for action: String in holds.duplicate():
		hold_end(action)


func cinematic_active() -> bool:
	return cinematic


func skip_cinematic() -> void:
	cinematic = false
	events.append("skip")


func pointer_action(action: Dictionary) -> void:
	events.append("pointer:" + action.kind)


func key_pressed(key: Key) -> void:
	events.append("key:%d" % key)


func key_released(key: Key) -> void:
	events.append("keyup:%d" % key)


func hud_action(action: String) -> void:
	events.append("hud:" + action)


func toggle_review(hero: String) -> void:
	events.append("review:" + hero)
