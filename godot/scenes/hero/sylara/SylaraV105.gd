extends CharacterBody2D

# ==============================================================================
# SYLARA V10.5 - DYNAMIC CAMERA, GHOST TRAILS & HIGH-SPEED WINDRUN SPRINT
# ==============================================================================
# Rig satu file (standalone controller): gerak + kamera dinamis smooth-lag +
# ghost trail windrun + seluruh skill + UI mobile, semuanya di script ini.
# Dipakai scene SylaraV105.tscn dan showcased di scenes/demo/SylaraDemo.tscn.

# --- WARNA PIXEL ART ---
const C_OUTLINE     = Color("0e170d")
const C_HOOD_DARK   = Color("142e12")
const C_HOOD_MID    = Color("235220")
const C_HOOD_LIGHT  = Color("459e3f")
const C_HOOD_HI     = Color("7bf073")
const C_HAIR_DARK   = Color("8a2b12")
const C_HAIR_MID    = Color("d44c24")
const C_HAIR_LIGHT  = Color("f77b3b")
const C_SKIN        = Color("f2b591")
const C_ARMOR_DARK  = Color("2e1d12")
const C_GOLD        = Color("e6b83b")
const C_BOW_WOOD    = Color("6e411b")
const C_GLOW        = Color("66ff33") * 2.5
const C_ARROW_SHAFT = Color("8b5a2b")

# --- SETTINGS ---
@export var move_speed: float = 200.0
@export var windrun_speed: float = 480.0 # Lari sangat cepat!

var joystick_vector: Vector2 = Vector2.ZERO
var aim_direction: Vector2 = Vector2.RIGHT
var is_facing_left: bool = false
var is_windrun: bool = false

# Animation States
var current_anim: String = "idle"
var anim_frame: int = 0
var frame_timer: float = 0.0
var ghost_timer: float = 0.0
var is_busy: bool = false
var is_dead: bool = false

# Collections
var active_arrows: Array = []
var active_particles: Array = []
var active_shackles: Array = []
var ghost_trails: Array = [] # Bayangan Windrun
var world_objects: Array = [] # Pohon & Batu Dunia

@onready var camera: Camera2D

func _ready() -> void:
	# 1. SETUP KAMERA DINAMIS (WITH SMOOTH LAG)
	camera = Camera2D.new()
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 6.0 # Memberi efek Sylara melesat mendahului kamera
	add_child(camera)

	# 2. GLOW ENVIRONMENT
	var env = Environment.new()
	env.background_mode = Environment.BG_CANVAS
	env.glow_enabled = true
	env.glow_intensity = 1.5
	env.glow_bloom = 0.3
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	var world_env = WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)

	# 3. GENERASI DEKORASI DUNIA (POHON, BATU, JALAN)
	generate_world_objects()

	# 4. SETUP MOBILE UI
	setup_mobile_ui()

func generate_world_objects() -> void:
	world_objects.clear()
	# Pohon & Batu tersebar di sekitar peta
	for x in range(-15, 16):
		for y in range(-10, 11):
			if (x % 3 == 0 and y % 3 == 0) and (abs(x) > 1 or abs(y) > 1):
				var pos = Vector2(x * 120 + randf_range(-20, 20), y * 120 + randf_range(-20, 20))
				var type = "tree" if (x + y) % 2 == 0 else "rock"
				world_objects.append({"pos": pos, "type": type})

func _physics_process(delta: float) -> void:
	var key_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var move_dir = joystick_vector if joystick_vector != Vector2.ZERO else key_dir

	if not is_dead:
		var speed = move_speed
		
		# LOGIKA WINDRUN REAL MOVEMENT
		if is_windrun:
			speed = windrun_speed
			if move_dir == Vector2.ZERO:
				move_dir = aim_direction # Otomatis lari ke depan jika analog lepas
			else:
				aim_direction = move_dir.normalized()

		velocity = move_dir * speed
		move_and_slide()

		if move_dir.x != 0:
			is_facing_left = move_dir.x < 0
			if not is_windrun: aim_direction = move_dir.normalized()

		# Controller Animasi
		if not is_busy:
			if is_windrun:
				set_anim("windrun")
			elif move_dir != Vector2.ZERO:
				set_anim("walk")
			else:
				set_anim("idle")
	else:
		velocity = Vector2.ZERO

	update_animation(delta)
	update_vfx(delta)
	queue_redraw()

# ==============================================================================
# ANIMATION ENGINE
# ==============================================================================
func set_anim(anim_name: String) -> void:
	if current_anim == anim_name: return
	current_anim = anim_name
	anim_frame = 0
	frame_timer = 0.0

func trigger_skill(anim_name: String) -> void:
	if anim_name == "death":
		is_dead = true
		is_busy = true
		set_anim("death")
		return

	if is_dead: return
	is_busy = true
	set_anim(anim_name)

func toggle_windrun() -> void:
	if is_dead: return
	is_windrun = !is_windrun
	if is_windrun:
		set_anim("windrun")
	else:
		set_anim("idle")

func update_animation(delta: float) -> void:
	frame_timer += delta

	# WINDRUN KAKI BERPUTAR 0.04 DETIK (SANGAT KENCANG!)
	var duration = 0.12
	if current_anim == "windrun": duration = 0.04
	elif current_anim == "focus_fire": duration = 0.08
	elif current_anim == "hurt": duration = 0.15

	var max_frames = 4
	match current_anim:
		"walk", "powershot": max_frames = 6
		"attack", "shackle": max_frames = 5
		"hurt": max_frames = 3
		"death": max_frames = 4

	if frame_timer >= duration:
		frame_timer = 0.0
		
		if current_anim == "death" and anim_frame == max_frames - 1:
			pass
		else:
			anim_frame += 1

		# Spawn Panah
		if current_anim == "attack" and anim_frame == 3: shoot_arrow(false, false)
		elif current_anim == "powershot" and anim_frame == 5: shoot_arrow(true, false)
		elif current_anim == "focus_fire" and (anim_frame == 1 or anim_frame == 3): shoot_arrow(false, false)
		elif current_anim == "shackle" and anim_frame == 3: shoot_arrow(false, true)

		if anim_frame >= max_frames:
			if current_anim != "death":
				anim_frame = 0
				if is_busy and current_anim != "windrun":
					is_busy = false
					set_anim("idle")

# ==============================================================================
# PROJECTILE & VFX ENGINE (WITH WINDRUN GHOST TRAILS)
# ==============================================================================
func get_bow_pos() -> Vector2:
	var dir = -1.0 if is_facing_left else 1.0
	return global_position + Vector2(12.0 * dir, -6.0)

func shoot_arrow(is_power: bool, is_shackle: bool) -> void:
	var start = get_bow_pos()
	var dir = aim_direction

	active_arrows.append({
		"pos": start, "dir": dir,
		"speed": 1100.0 if is_power else 820.0,
		"is_power": is_power, "is_shackle": is_shackle, "life": 1.8
	})

	if is_shackle:
		active_shackles.append({
			"pos": start + (dir * 180.0),
			"life": 2.2, "angle": 0.0, "radius": 4.0, "target_radius": 36.0
		})

func update_vfx(delta: float) -> void:
	# 1. WINDRUN GHOST TRAIL (BAYANGAN AURA HIJAU DI BELAKANG)
	if is_windrun and not is_dead:
		ghost_timer += delta
		if ghost_timer >= 0.04:
			ghost_timer = 0.0
			ghost_trails.append({
				"pos": global_position,
				"facing_left": is_facing_left,
				"frame": anim_frame,
				"alpha": 0.7
			})

		var wind_dir = -aim_direction
		spawn_particle(global_position + Vector2(randf_range(-15,15), randf_range(-20,20)), wind_dir * 250.0, C_HOOD_HI, 0.3, randf_range(2.5, 5.0))

	# Update Ghost Trails
	for i in range(ghost_trails.size() - 1, -1, -1):
		var g = ghost_trails[i]
		g.alpha -= delta * 3.0
		if g.alpha <= 0:
			ghost_trails.remove_at(i)

	# 2. Update Arrows
	for i in range(active_arrows.size() - 1, -1, -1):
		var a = active_arrows[i]
		a.pos += a.dir * a.speed * delta; a.life -= delta
		if a.life <= 0: active_arrows.remove_at(i)
		elif a.is_power and randf() > 0.45:
			spawn_particle(a.pos, Vector2(randf_range(-12,12), randf_range(-12,12)), C_GLOW, 0.25, 3.0)

	# 3. Charging Powershot
	if current_anim == "powershot" and anim_frame < 5 and randf() > 0.35:
		var bow = get_bow_pos()
		var ppos = bow + Vector2(randf_range(-45,45), randf_range(-45,45))
		spawn_particle(ppos, (bow - ppos).normalized() * 200.0, C_GLOW, 0.22, 3.5)

	# 4. Tornado Shackle
	for i in range(active_shackles.size() - 1, -1, -1):
		var s = active_shackles[i]
		s.life -= delta; s.angle += delta * 9.0
		s.radius = lerp(s.radius, s.target_radius, delta * 5.0)
		if s.life <= 0: active_shackles.remove_at(i)

	# 5. Particles
	for i in range(active_particles.size() - 1, -1, -1):
		var p = active_particles[i]
		p.pos += p.vel * delta; p.life -= delta
		if p.life <= 0: active_particles.remove_at(i)

func spawn_particle(pos: Vector2, vel: Vector2, col: Color, life: float, size: float) -> void:
	active_particles.append({"pos": pos, "vel": vel, "color": col, "life": life, "max_life": life, "size": size})

# ==============================================================================
# DRAWING ENGINE (DUNIA + GHOST TRAILS + SYLARA)
# ==============================================================================
func _draw() -> void:
	# 1. GAMBAR OBJEK DUNIA (POHON & BATU AGAR MOVEMENT SANGAT JELAS)
	draw_world_environment_objects()

	# 2. GAMBAR GHOST TRAILS (BAYANGAN WINDRUN)
	for g in ghost_trails:
		var rel_pos = to_local(g.pos)
		draw_sylara_sprite(rel_pos, g.facing_left, "windrun", g.frame, Color(C_HOOD_HI.r, C_HOOD_HI.g, C_HOOD_HI.b, g.alpha))

	# 3. GAMBAR PANAH & SKILL
	for a in active_arrows: draw_arrow(to_local(a.pos), a.dir, a.is_power, a.is_shackle)

	for s in active_shackles:
		var p = to_local(s.pos)
		var alpha = clamp(s.life / 2.2, 0.0, 1.0)
		for r in range(3):
			draw_arc(p, s.radius * (0.45 + r * 0.28), s.angle, s.angle + TAU, 22, Color(C_GLOW.r, C_GLOW.g, C_GLOW.b, alpha * (0.7 - r * 0.18)), 2.2)

	for p in active_particles:
		var alpha = clamp(p.life / p.max_life, 0.0, 1.0)
		draw_rect(Rect2(to_local(p.pos), Vector2(p.size, p.size)), Color(p.color.r, p.color.g, p.color.b, alpha))

	# 4. GAMBAR SPRITE SYLARA UTAMA
	draw_sylara_sprite(Vector2.ZERO, is_facing_left, current_anim, anim_frame, Color.WHITE)

func draw_world_environment_objects() -> void:
	# Grid Rumput
	var grid_size = 64.0
	var offset_x = fmod(global_position.x, grid_size)
	var offset_y = fmod(global_position.y, grid_size)
	for x in range(-12, 13):
		var lx = (x * grid_size) - offset_x
		draw_line(Vector2(lx, -400), Vector2(lx, 400), Color(0.18, 0.28, 0.18, 0.3), 1.0)
	for y in range(-8, 9):
		var ly = (y * grid_size) - offset_y
		draw_line(Vector2(-600, ly), Vector2(600, ly), Color(0.18, 0.28, 0.18, 0.3), 1.0)

	# Pohon & Batu
	for obj in world_objects:
		var rel_pos = to_local(obj.pos)
		if abs(rel_pos.x) < 600 and abs(rel_pos.y) < 400:
			if obj["type"] == "tree":
				draw_rect(Rect2(rel_pos.x - 4, rel_pos.y - 6, 8, 16), C_ARMOR_DARK)
				draw_circle(rel_pos + Vector2(0, -18), 16, C_HOOD_DARK)
				draw_circle(rel_pos + Vector2(0, -22), 12, C_HOOD_MID)
			else:
				draw_circle(rel_pos, 10, Color("2d3d2c"))
				draw_circle(rel_pos + Vector2(-2, -2), 7, Color("455e43"))

func draw_arrow(pos: Vector2, dir: Vector2, is_power: bool, is_shackle: bool) -> void:
	var mult = 1.45 if is_power else 1.0
	var shaft = 21.0 * mult; var head_l = 8.0 * mult; var head_w = 5.0 * mult
	var end = pos + dir * shaft; var tip = end + dir * head_l; var perp = Vector2(-dir.y, dir.x)

	draw_line(pos, end, C_OUTLINE, 4.0 * mult)
	draw_line(pos, end, C_ARROW_SHAFT if not is_shackle else C_HOOD_LIGHT, 2.2 * mult)

	var poly = PackedVector2Array([tip, end + perp * head_w, end - perp * head_w])
	draw_colored_polygon(poly, C_GLOW * (2.6 if is_power or is_shackle else 1.6))
	draw_polyline(poly, C_OUTLINE, 1.6)
	draw_circle(tip, 2.2 * mult, Color.WHITE)

# RENDER SPRITE SYLARA DENGAN POSE WINDRUN SPRINT EKSTREM
func draw_sylara_sprite(origin: Vector2, flip_left: bool, anim_name: String, frame_idx: int, tint: Color) -> void:
	var s = 2.6
	var sx = -1.0 if flip_left else 1.0

	var yo = 0; var xo = 0; var leg = 0; var pull = 0
	var show_arr = false; var p_glow = false; var is_sh = false; var flash = false; var dead = false

	match anim_name:
		"idle": yo = 1 if frame_idx % 2 == 1 else 0
		"walk": yo = 1 if frame_idx % 2 == 1 else 0; leg = frame_idx % 4
		"attack":
			if frame_idx == 1: pull = 2
			elif frame_idx == 2: pull = 5; show_arr = true
			elif frame_idx == 3: pull = 0
		"powershot":
			pull = mini(frame_idx * 2, 7)
			p_glow = frame_idx >= 2
			show_arr = frame_idx >= 1 and frame_idx < 5
		"windrun":
			# BADAN MEMBUNGKUK KE DEPAN 4 PIXELS (LEAN FORWARD SPRINT)
			xo = 4
			yo = 2 if frame_idx % 2 == 1 else 0
			leg = frame_idx % 4
		"focus_fire":
			pull = (frame_idx % 2) * 4; show_arr = true
		"hurt":
			flash = true; yo = -2 if frame_idx == 1 else 0
		"death":
			if frame_idx == 0: flash = true
			elif frame_idx == 1: yo = 8
			elif frame_idx == 2: yo = 16
			elif frame_idx == 3: dead = true
		"shackle":
			is_sh = true
			if frame_idx == 1: pull = 3
			elif frame_idx == 2: pull = 6; show_arr = true
			elif frame_idx == 3: pull = 1; show_arr = true

	var final_tint = (Color(1.0, 0.35, 0.35) if flash else Color.WHITE) * tint

	var R = func(x: float, y: float, w: float, h: float, col: Color):
		var rx = origin.x + (((x + xo) - 24.0) * s * sx) - (w * s if flip_left else 0.0)
		var ry = origin.y + ((y + yo - 24.0) * s)
		draw_rect(Rect2(rx, ry, w * s, h * s), col * final_tint)

	var RO = func(x: float, y: float, w: float, h: float, col: Color):
		R.call(x-1, y-1, w+2, h+2, C_OUTLINE)
		R.call(x, y, w, h, col)

	if dead:
		RO.call(10, 40, 28, 6, C_HOOD_DARK); R.call(12, 42, 24, 4, C_HOOD_MID)
		RO.call(10, 42, 8, 4, C_HAIR_DARK); R.call(11, 43, 6, 2, C_HAIR_LIGHT)
		RO.call(36, 42, 6, 4, C_ARMOR_DARK); RO.call(14, 45, 18, 2, C_BOW_WOOD)
		return

	# Jubah Melayang Horizontal Saat Windrun
	if anim_name == "windrun":
		RO.call(2, 16, 12, 12, C_HOOD_DARK)
		R.call(0, 18, 10, 10, C_HOOD_MID)
	else:
		RO.call(8, 16, 10, 20, C_HOOD_DARK)
		R.call(6, 20, 6, 18, C_HOOD_MID)
		R.call(4, 26, 5, 14, C_HOOD_LIGHT)

	# POSE KAKI SPRINT WINDRUN EKSTREM
	if anim_name == "windrun":
		if leg == 0:
			RO.call(26, 32, 6, 12, C_ARMOR_DARK) # Kaki Depan Melangkah Far Right
			RO.call(10, 32, 6, 12, C_ARMOR_DARK) # Kaki Belakang Far Left
		elif leg == 1:
			RO.call(20, 28, 6, 12, C_ARMOR_DARK) # High Knee Sprint (Melayang)
			RO.call(16, 30, 6, 10, C_ARMOR_DARK)
		elif leg == 2:
			RO.call(10, 32, 6, 12, C_ARMOR_DARK)
			RO.call(26, 32, 6, 12, C_ARMOR_DARK)
		elif leg == 3:
			RO.call(16, 30, 6, 10, C_ARMOR_DARK)
			RO.call(20, 28, 6, 12, C_ARMOR_DARK)
	else:
		if leg == 0 or leg == 2:
			RO.call(18, 34, 5, 11, C_ARMOR_DARK); RO.call(26, 34, 5, 11, C_ARMOR_DARK)
		elif leg == 1:
			RO.call(14, 34, 5, 11, C_ARMOR_DARK); RO.call(28, 34, 5, 11, C_ARMOR_DARK)
		elif leg == 3:
			RO.call(20, 34, 5, 11, C_ARMOR_DARK); RO.call(24, 34, 5, 11, C_ARMOR_DARK)

	RO.call(16, 20, 17, 15, C_ARMOR_DARK); R.call(18, 22, 13, 9, C_HOOD_MID)
	R.call(20, 24, 9, 5, C_HOOD_LIGHT); RO.call(16, 30, 17, 4, C_GOLD)

	RO.call(12, 6, 23, 13, C_HAIR_DARK); R.call(14, 4, 19, 11, C_HAIR_MID); R.call(16, 3, 15, 8, C_HAIR_LIGHT)
	RO.call(18, 10, 14, 9, C_SKIN)

	if anim_name in ["hurt", "death"]:
		R.call(25, 14, 5, 2, C_OUTLINE)
	else:
		R.call(26, 13, 4, 4, C_OUTLINE); R.call(27, 14, 3, 3, Color.BLACK)
		R.call(28, 14, 2, 2, C_GLOW if not p_glow else Color.WHITE)

	RO.call(13, 2, 20, 7, C_HOOD_MID); R.call(15, 1, 16, 5, C_HOOD_LIGHT)

	var bx = 33 - pull
	RO.call(bx, 8, 3, 5, C_BOW_WOOD); RO.call(bx+3, 13, 3, 6, C_BOW_WOOD)
	RO.call(bx+4, 19, 3, 10, C_BOW_WOOD); RO.call(bx+3, 29, 3, 6, C_BOW_WOOD); RO.call(bx, 35, 3, 5, C_BOW_WOOD)

	if show_arr:
		var ax = bx - 6
		RO.call(ax, 22, 16, 2, C_HOOD_LIGHT if is_sh else C_BOW_WOOD)
		R.call(ax+14, 20, 6, 6, C_GLOW * (2.5 if p_glow or is_sh else 1.3))

# ==============================================================================
# RESPONSIVE MOBILE UI
# ==============================================================================
func setup_mobile_ui() -> void:
	var ui = CanvasLayer.new()
	add_child(ui)

	# 1. JOYSTICK VIRTUAL
	var joy_control = Control.new()
	joy_control.anchor_left = 0.0
	joy_control.anchor_top = 1.0
	joy_control.anchor_right = 0.0
	joy_control.anchor_bottom = 1.0
	joy_control.offset_left = 150
	joy_control.offset_top = -150
	ui.add_child(joy_control)

	var joy_script = TouchJoystick.new()
	joy_script.player_ref = self
	joy_control.add_child(joy_script)

	# 2. PANEL TOMBOL KANAN BAWAH
	var right_panel = Control.new()
	right_panel.anchor_left = 1.0
	right_panel.anchor_top = 1.0
	right_panel.anchor_right = 1.0
	right_panel.anchor_bottom = 1.0
	ui.add_child(right_panel)

	var btn_attack = Button.new()
	btn_attack.position = Vector2(-120, -120)
	btn_attack.size = Vector2(100, 100)
	btn_attack.text = "ATTACK"
	btn_attack.pressed.connect(func(): trigger_skill("attack"))
	right_panel.add_child(btn_attack)

	var skill_data = [
		{"name": "Q\nFocus", "anim": "focus_fire", "pos": Vector2(-220, -80)},
		{"name": "W\nWindrun", "anim": "windrun", "pos": Vector2(-190, -160)},
		{"name": "E\nShackle", "anim": "shackle", "pos": Vector2(-120, -210)},
		{"name": "R\nPower", "anim": "powershot", "pos": Vector2(-220, -230)}
	]

	for s_info in skill_data:
		var btn = Button.new()
		btn.position = s_info["pos"]
		btn.size = Vector2(65, 65)
		btn.text = s_info["name"]
		
		var a_name = s_info["anim"]
		btn.pressed.connect(func():
			if a_name == "windrun":
				toggle_windrun()
			else:
				trigger_skill(a_name)
		)
		right_panel.add_child(btn)

	# 3. TOMBOL TES (KIRI ATAS)
	var top_panel = Control.new()
	top_panel.anchor_left = 0.0
	top_panel.anchor_top = 0.0
	ui.add_child(top_panel)

	var btn_hurt = Button.new()
	btn_hurt.position = Vector2(20, 20)
	btn_hurt.size = Vector2(80, 40)
	btn_hurt.text = "HURT"
	btn_hurt.pressed.connect(func(): trigger_skill("hurt"))
	top_panel.add_child(btn_hurt)

	var btn_death = Button.new()
	btn_death.position = Vector2(110, 20)
	btn_death.size = Vector2(80, 40)
	btn_death.text = "DEATH"
	btn_death.pressed.connect(func(): trigger_skill("death"))
	top_panel.add_child(btn_death)

	var btn_revive = Button.new()
	btn_revive.position = Vector2(200, 20)
	btn_revive.size = Vector2(90, 40)
	btn_revive.text = "REVIVE"
	btn_revive.pressed.connect(func():
		is_dead = false
		is_busy = false
		is_windrun = false
		set_anim("idle")
	)
	top_panel.add_child(btn_revive)

# CLASS TOUCH JOYSTICK
class TouchJoystick extends Control:
	var player_ref: CharacterBody2D
	var is_dragging: bool = false
	var touch_pos: Vector2 = Vector2.ZERO
	var max_radius: float = 65.0

	func _ready() -> void:
		custom_minimum_size = Vector2(max_radius * 2, max_radius * 2)
		size = custom_minimum_size

	func _input(event: InputEvent) -> void:
		var center = global_position
		if event is InputEventScreenTouch or event is InputEventMouseButton:
			if event.pressed:
				if center.distance_to(event.position) <= max_radius * 2.0:
					is_dragging = true
					touch_pos = event.position - center
					update_joystick()
			else:
				is_dragging = false
				touch_pos = Vector2.ZERO
				player_ref.joystick_vector = Vector2.ZERO
				queue_redraw()

		elif (event is InputEventScreenDrag or (event is InputEventMouseMotion and is_dragging)):
			if is_dragging:
				touch_pos = event.position - center
				update_joystick()

	func update_joystick() -> void:
		var dir = touch_pos
		if dir.length() > max_radius:
			dir = dir.normalized() * max_radius
		player_ref.joystick_vector = dir / max_radius
		queue_redraw()

	func _draw() -> void:
		draw_circle(Vector2.ZERO, max_radius, Color(0.2, 0.4, 0.2, 0.5))
		draw_arc(Vector2.ZERO, max_radius, 0, TAU, 32, Color("77ff33"), 3.0)
		var knob_pos = touch_pos.limit_length(max_radius) if is_dragging else Vector2.ZERO
		draw_circle(knob_pos, 25.0, Color("77ff33", 0.9))
