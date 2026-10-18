extends RefCounted
## Layer 9bm: the baked build-slot markers (`bake/bake_slot_atlas.py`). The pulse picker
## is replayed against the source formula's answers recorded by the bake.

const SlotArt = preload("res://scripts/ui/slot_art.gd")
const PrototypeView = preload("res://scenes/prototype/prototype_view.gd")
const PROTOTYPE_VIEW := "res://scenes/prototype/prototype_view.gd"


func run(check: Callable) -> void:
	var manifest := SlotArt.manifest()
	check.call(not manifest.is_empty(), "Slot atlas manifest parses")
	_check_sheet(check, manifest)
	_check_pulse(check, manifest)
	_check_frames(check)
	_check_view_wiring(check)


func _check_sheet(check: Callable, manifest: Dictionary) -> void:
	var sheet: Dictionary = manifest.get("sheet", {})
	var size: Array = sheet.get("size", [0, 0])
	check.call(FileAccess.file_exists(SlotArt.SHEET), "The slot sheet exists")
	var image := Image.load_from_file(SlotArt.SHEET)
	check.call(
		image != null and image.get_size() == Vector2i(int(size[0]), int(size[1])),
		"The slot sheet decodes at its size"
	)
	var rows := SlotArt.frames()
	check.call(rows.size() == 6, "Five blue pulse frames and one red: %d" % rows.size())
	var inside := true
	for key in rows:
		var row: Array = rows[key]
		inside = inside and float(row[0]) + float(row[2]) <= float(size[0])
		inside = inside and float(row[1]) + float(row[3]) <= float(size[1])
		inside = inside and int(row[4]) == 20 and int(row[5]) == 17
	check.call(inside, "Every slot frame lies inside the sheet and anchors at (20, 17)")


func _check_pulse(check: Callable, manifest: Dictionary) -> void:
	var cases: Array = manifest.get("pulse_cases", [])
	check.call(cases.size() >= 50, "The bake recorded the source pulse: %d" % cases.size())
	var wrong: Array = []
	for row in cases:
		if SlotArt.pulse(int(row[0])) != int(row[1]):
			wrong.append(row)
	check.call(wrong.is_empty(), "The pulse picker matches the source formula: %s" % str(wrong))
	var seen := {}
	for row in cases:
		seen[int(row[1])] = true
	check.call(seen.size() == 5, "The recorded run reaches every glow size")


func _check_frames(check: Callable) -> void:
	check.call(SlotArt.frame_key(1, 40) == "red", "Red slots are static")
	check.call(SlotArt.frame_key(0, 0) == "blue:0", "Blue starts at the middle glow")
	var blue := SlotArt.frame(0, 20)
	check.call(not blue.is_empty(), "A blue slot frame loads from the imported sheet")
	check.call(not SlotArt.frame(1, 20).is_empty(), "A red slot frame loads")
	if not blue.is_empty():
		var src: Rect2 = blue["src"]
		check.call(src.size == Vector2(40, 38), "A slot frame is the source 40x38 surface")
		check.call((blue["texture"] as Texture2D).get_width() == 240, "The sheet is 240 px wide")


func _check_view_wiring(check: Callable) -> void:
	var view := PrototypeView.new()
	check.call(view.has_method("_draw_build_slots"), "The prototype view draws the slot art")
	check.call(view.has_method("_draw_structures"), "Slots are painted from the structure layer")
	view.free()
	var text := FileAccess.get_file_as_string(PROTOTYPE_VIEW)
	var layer := text.find("func _draw_structures() -> void:")
	var slots := text.find("_draw_build_slots(", layer)
	var towers := text.find("super._draw_structures()", slots)
	check.call(layer != -1 and layer < slots and slots < towers, "Slots go under the towers")
	check.call(text.count("for slot in world.slots:") == 1, "The slot loop lives in one place")
