extends RefCounted
## Kill feed, ported from `_render.py::KillFeed`. `add_kill` stacks older
## entries downward, caps the list and stamps a fresh lifetime; `update`
## counts down and eases `y_offset` toward `target_y`. Presentation only:
## the entries carry text/colour for whoever draws them.

const MAX_ENTRIES := 5
const LIFETIME := 180
const STACK_OFFSET := 20.0
const Y_LERP := 0.2

const BLUE_ARROW := ">>"
const RED_ARROW := "<<"
const BLUE_TINT := Color8(100, 200, 255)
const RED_TINT := Color8(255, 100, 100)

var entries: Array[Dictionary] = []


func add_kill(killer_name: String, victim_name: String, killer_team: String = "blue") -> void:
	var is_blue := killer_team == "blue"
	var arrow := BLUE_ARROW if is_blue else RED_ARROW
	var entry := {
		"text": "%s %s %s" % [killer_name, arrow, victim_name],
		"color": BLUE_TINT if is_blue else RED_TINT,
		"lifetime": LIFETIME,
		"max_lifetime": LIFETIME,
		"y_offset": 0.0,
		"target_y": 0.0,
	}
	for existing in entries:
		existing["target_y"] = float(existing["target_y"]) + STACK_OFFSET
	entries.append(entry)
	if entries.size() > MAX_ENTRIES:
		entries.remove_at(0)


func update() -> void:
	for entry in entries:
		entry["lifetime"] = int(entry["lifetime"]) - 1
		entry["y_offset"] = (
			float(entry["y_offset"])
			+ (float(entry["target_y"]) - float(entry["y_offset"])) * Y_LERP
		)
	var standing: Array[Dictionary] = []
	for entry in entries:
		if int(entry["lifetime"]) > 0:
			standing.append(entry)
	entries = standing
