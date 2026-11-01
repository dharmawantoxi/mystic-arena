class_name EntityVisuals
extends RefCounted

## Baked sprite-strip renderer for _entity.py heroes/bosses/minions/towers/nexus.
const MAX_LIT_FRAMES := 128
static var units: Dictionary = {}
static var props: Dictionary = {}
static var textures: Dictionary = {}
static var lit_textures: Dictionary = {}
static var quality: Dictionary = RenderQuality.preset("high")
static var lighting: Lighting = null
static var loaded := false


static func ensure_loaded() -> void:
	if loaded:
		return
	loaded = true
	var unit_file := FileAccess.open("res://data/baked_units.json", FileAccess.READ)
	if unit_file != null:
		var parsed: Variant = JSON.parse_string(unit_file.get_as_text())
		if parsed is Dictionary:
			units = parsed.get("units", {})
	var prop_file := FileAccess.open("res://data/baked_props.json", FileAccess.READ)
	if prop_file != null:
		var parsed: Variant = JSON.parse_string(prop_file.get_as_text())
		if parsed is Dictionary:
			props = parsed


static func configure(preset: Dictionary) -> void:
	var next := preset.duplicate()
	if bool(next.get("hero_lighting", true)) != bool(quality.get("hero_lighting", true)):
		lit_textures.clear()
	quality = next


static func clear_cache() -> void:
	textures.clear()
	lit_textures.clear()
	if lighting != null:
		lighting.clear_cache()
		lighting = null


static func lit_frame_texture(
	tex: Texture2D, source: Rect2, options: Dictionary = {}, enabled := true
) -> Texture2D:
	if tex == null or not enabled:
		return null
	if lighting == null:
		lighting = Lighting.new()
	if not lighting.valid():
		return null
	var resolved := options.duplicate()
	if resolved.get("box") is Array and resolved.box.size() == 4:
		var box: Array = resolved.box
		resolved.box = Rect2i(int(box[0]), int(box[1]), int(box[2]), int(box[3]))
	var key := "%d:%s:%s" % [tex.get_instance_id(), str(source), str(resolved)]
	if lit_textures.has(key):
		return lit_textures[key]
	var image := tex.get_image()
	if image == null:
		return null
	var frame := image.get_region(Rect2i(source))
	if frame == null:
		return null
	lighting.apply_to_rig(frame, true, resolved)
	var result := ImageTexture.create_from_image(frame)
	if lit_textures.size() >= MAX_LIT_FRAMES:
		lit_textures.clear()
	lit_textures[key] = result
	return result


static func _lighting_options(entry: Dictionary, _team: String) -> Dictionary:
	# Existing strips were baked by the Python renderer after its lighting pass.
	# Only explicitly raw imports are lit at runtime, so nobody gets a double rim.
	if bool(entry.get("lighting_baked", true)):
		return {}
	return {
		"enabled":
		bool(quality.get("hero_lighting", true)) and bool(entry.get("lighting_enabled", true)),
		"options": entry.get("lighting", {}),
	}


static func texture(path: String) -> Texture2D:
	if path.is_empty():
		return null
	if not textures.has(path):
		textures[path] = load(path) if ResourceLoader.exists(path) else null
	return textures[path]


static func draw_unit(canvas: CanvasItem, unit: BattleUnit, frame: int) -> bool:
	ensure_loaded()
	var entry: Dictionary = {}
	var scale := 1.0
	var fps := 6.0
	var anims: Dictionary = {}
	var anchor := Vector2.ZERO
	var frame_size := Vector2.ZERO
	var per_row := 8
	var anim := "idle"
	if unit.kind == BattleUnit.Kind.HERO or unit.kind == BattleUnit.Kind.BOSS:
		entry = units.get(unit.unit_type, {})
		if entry.is_empty():
			return false
		scale = (
			float(entry.get("hero_scale", 1.0))
			if unit.kind == BattleUnit.Kind.HERO
			else float(entry.get("boss_scale", 1.0))
		)
		fps = (
			float(entry.get("fps_hero", 6.0))
			if unit.kind == BattleUnit.Kind.HERO
			else float(entry.get("fps_boss", 12.0))
		)
		anims = entry.get("anims", {})
		anchor = Vector2(float(entry.anchor[0]), float(entry.anchor[1]))
		frame_size = Vector2(float(entry.frame_w), float(entry.frame_h))
		per_row = int(entry.get("frames_per_row", 8))
		if not unit.active_skill.is_empty() and entry.has("skills_png"):
			var skill_anims: Dictionary = entry.get("skill_anims", {})
			if skill_anims.has(unit.active_skill):
				var tex := texture(str(entry.skills_png))
				if tex != null:
					var range_arr: Array = skill_anims[unit.active_skill]
					var count := int(range_arr[1])
					var index := int(range_arr[0]) + int(frame * fps / 60.0) % maxi(1, count)
					var sanchor := Vector2(
						float(entry.skill_anchor[0]), float(entry.skill_anchor[1])
					)
					var ssize := Vector2(float(entry.skill_frame_w), float(entry.skill_frame_h))
					_draw_frame(
						canvas,
						tex,
						unit.pos,
						sanchor * scale,
						ssize * scale,
						index,
						int(entry.get("skill_frames_per_row", 8)),
						ssize,
						unit.facing,
						_lighting_options(entry, unit.team)
					)
					return true
		if unit.attack_anim_timer > 0:
			anim = "attack"
		elif unit.is_moving:
			anim = "walk"
	elif unit.kind == BattleUnit.Kind.MINION:
		entry = props.get("minions", {}).get("%s_%s" % [unit.unit_type, unit.team], {})
		if entry.is_empty():
			return false
		anims = entry.get("anims", {})
		var fps_map: Dictionary = entry.get("fps", {})
		fps = float(fps_map.get("idle", 6.0))
		anchor = Vector2(float(entry.anchor[0]), float(entry.anchor[1]))
		frame_size = Vector2(float(entry.frame_w), float(entry.frame_h))
		per_row = int(entry.get("frames_per_row", 8))
		if unit.attack_anim_timer > 0:
			anim = "attack"
			fps = float(fps_map.get("attack", 20.0))
		elif unit.is_moving:
			anim = "walk"
			fps = float(fps_map.get("walk", 12.0))
	elif unit.kind == BattleUnit.Kind.TOWER:
		entry = props.get("towers", {}).get("%s_%s" % [unit.tower_type, unit.team], {})
		if entry.is_empty():
			return false
		var levels: Dictionary = entry.get("levels", {})
		var level: Dictionary = levels.get(str(clampi(unit.level, 1, 6)), {})
		var frames: Array = level.get("shoot" if unit.shoot_flash_timer > 0 else "idle", [0])
		var index := int(
			frames[int(frame * float(entry.get("fps_shoot", 12.0)) / 60.0) % frames.size()]
		)
		anchor = Vector2(float(entry.anchor[0]), float(entry.anchor[1]))
		frame_size = Vector2(float(entry.frame_w), float(entry.frame_h))
		var tex := texture(str(entry.png))
		if tex == null:
			return false
		_draw_frame(
			canvas,
			tex,
			unit.pos,
			anchor,
			frame_size,
			index,
			int(entry.get("frames_per_row", 8)),
			frame_size,
			unit.facing
		)
		return true
	elif unit.kind == BattleUnit.Kind.CASTLE:
		entry = props.get("nexus", {}).get(unit.team, {})
		if entry.is_empty():
			return false
		var levels: Dictionary = entry.get("levels", {})
		var index := int(levels.get(str(clampi(unit.level, 1, 5)), 0))
		anchor = Vector2(float(entry.anchor[0]), float(entry.anchor[1]))
		frame_size = Vector2(float(entry.frame_w), float(entry.frame_h))
		var tex := texture(str(entry.png))
		if tex == null:
			return false
		_draw_frame(
			canvas,
			tex,
			unit.pos,
			anchor,
			frame_size,
			index,
			int(entry.get("frames_per_row", 8)),
			frame_size,
			1
		)
		return true
	else:
		return false
	var tex := texture(str(entry.get("png", "")))
	if tex == null or not anims.has(anim):
		return false
	var range_arr: Array = anims[anim]
	var count := maxi(1, int(range_arr[1]))
	var index := int(range_arr[0]) + int(frame * fps / 60.0) % count
	_draw_frame(
		canvas,
		tex,
		unit.pos,
		anchor * scale,
		frame_size * scale,
		index,
		per_row,
		frame_size,
		unit.facing,
		(
			_lighting_options(entry, unit.team)
			if unit.kind in [BattleUnit.Kind.HERO, BattleUnit.Kind.BOSS]
			else {}
		)
	)
	return true


static func _draw_frame(
	canvas: CanvasItem,
	tex: Texture2D,
	pos: Vector2,
	anchor: Vector2,
	size: Vector2,
	index: int,
	per_row: int,
	source_size: Vector2,
	facing: int,
	lighting_options: Dictionary = {}
) -> void:
	var source := Rect2(
		Vector2((index % per_row) * source_size.x, int(index / per_row) * source_size.y),
		source_size
	)
	var flip := -1.0 if facing < 0 else 1.0
	canvas.draw_set_transform(pos, 0.0, Vector2(flip, 1.0))
	var lit := lit_frame_texture(
		tex,
		source,
		lighting_options.get("options", {}),
		bool(lighting_options.get("enabled", false))
	)
	if lit != null:
		canvas.draw_texture_rect(lit, Rect2(-anchor, size), false)
	else:
		canvas.draw_texture_rect_region(tex, Rect2(-anchor, size), source)
	canvas.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


static func draw_projectiles(canvas: CanvasItem, model: RefCounted) -> void:
	for proj: Dictionary in model.projectiles:
		if not bool(proj.get("alive", true)):
			continue
		var pos: Vector2 = proj.pos
		var angle := float(proj.get("angle", 0.0))
		var color: Color = proj.get("color", Color("ffd27a"))
		if proj.kind == "tower":
			match str(proj.get("bullet_type", "normal")):
				"cannon":
					canvas.draw_circle(pos, 6.0, Color("ff8844"))
				"ice":
					canvas.draw_circle(pos, 5.0, Color("88ddff"))
				"mage":
					canvas.draw_circle(pos, 5.0, Color("cc88ff"))
				_:
					canvas.draw_line(
						pos - Vector2.from_angle(angle) * 8.0, pos, Color("ffeeaa"), 2.0
					)
		else:
			var tip := pos + Vector2.from_angle(angle) * 8.0
			canvas.draw_line(pos - Vector2.from_angle(angle) * 8.0, tip, color, 2.5)
			canvas.draw_circle(tip, 3.0, color)


static func draw_effects(canvas: CanvasItem, model: RefCounted, font: Font) -> void:
	for effect: Dictionary in model.effects:
		var t := float(effect.age) / float(effect.ttl)
		var color: Color = effect.color
		color.a = 1.0 - t
		var radius := float(effect.radius) * (0.4 + 0.6 * t)
		canvas.draw_arc(effect.pos, radius, 0, TAU, 24, color, 2.0)
	for popup: Dictionary in model.popups:
		var t := float(popup.age) / float(popup.ttl)
		var color: Color = popup.color
		color.a = 1.0 - t
		var pos: Vector2 = popup.pos + Vector2(0, -30.0 * t)
		canvas.draw_string(font, pos, str(popup.text), HORIZONTAL_ALIGNMENT_CENTER, -1, 14, color)
