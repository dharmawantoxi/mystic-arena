class_name TacticalCommands
extends RefCounted

## Hold/tap tactical command semantics from tactical_commands.py.
const HOLD_THRESHOLD := 0.33
const REISSUE_SECONDS := 0.5
const TAIL_SECONDS := 0.5
const GATHER_PUSH_SECONDS := 4.0
const AUTO_PROTECT_INTERVAL := 90
var held: Dictionary = {}
var command_timer := 0.0
var active_command := ""
var gather_pushed := false
var auto_protect_timer := 0
var last_feedback := ""


func hold_begin(command: String, now: float) -> void:
	held[command] = now
	active_command = command
	command_timer = 10.0
	gather_pushed = false
	_issue(command)


func hold_end(command: String, now: float) -> void:
	if not held.has(command):
		return
	var duration := now - float(held[command])
	held.erase(command)
	if duration >= HOLD_THRESHOLD:
		command_timer = minf(command_timer, TAIL_SECONDS)
	if held.is_empty() and command_timer <= 0.0:
		active_command = ""


func release_all() -> void:
	held.clear()
	command_timer = 0.0
	active_command = ""
	gather_pushed = false


func update(delta: float, model: RefCounted) -> void:
	for command: String in held:
		command_timer -= delta
		if command_timer <= 0.0:
			command_timer = 10.0
			_issue(command)
		if (
			command == "gather"
			and not gather_pushed
			and Time.get_ticks_msec() / 1000.0 - float(held[command]) >= GATHER_PUSH_SECONDS
		):
			gather_pushed = true
			_issue("gather_push")
	if held.is_empty():
		command_timer = maxf(0.0, command_timer - delta)
		if command_timer <= 0.0:
			active_command = ""
		auto_protect_timer += 1
		if auto_protect_timer >= AUTO_PROTECT_INTERVAL:
			auto_protect_timer = 0
			_issue("auto_protect")
	if model != null and model.has_method("apply_tactical"):
		model.call("apply_tactical", active_command, delta)


func _issue(command: String) -> void:
	last_feedback = command
