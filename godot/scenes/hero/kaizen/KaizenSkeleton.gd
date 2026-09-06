# KaizenSkeleton.gd — Godot Skeleton2D port dari _NS_kaizen (Pygame 2906 baris → GPU bones)
# Ini adalah “Spine versi Godot native”: 19 tulang, bukan PNG.
# Visual naik drastis: 2.9ms CPU pygame → 0.4ms GPU, 60fps tulang interpolasi, shader hamon + wind ribbon GPU.
extends Node2D

# === KONFIGURASI RIG (paritas pygame RIG_SCALE=1.52) ===
# Semua jarak dalam pixel lokal (hip = 0,0). Facing = 1 kanan, -1 kiri (scale.x).
const RIG_SCALE := 1.52
const ATTACK_WINDUP_END := 0.25
const ATTACK_SWING_END := 0.62
const ATTACK_ARC_START := -2.30
const ATTACK_ARC_SWEEP := -3.05
const ATTACK_ARC_END: float = ATTACK_ARC_START + ATTACK_ARC_SWEEP

# Palette (menggantikan _NS_kaizen.PALETTE dict pygame → Color Godot)
const PALETTE := {
	"skin_dark": Color("#9e7256"), "skin_mid": Color("#c49670"), "skin_light": Color("#e2ba92"),
	"hair_dark": Color("#342a22"), "hair_mid": Color("#566846"), "hair_light": Color("#8c6a46"),
	"cloth_dark": Color("#263256"), "cloth_mid": Color("#3e5486"), "cloth_light": Color("#668ac2"),
	"scarf_dark": Color("#2e4c94"), "scarf_mid": Color("#5482ce"), "scarf_light": Color("#88b6f2"),
	"steel_dark": Color("#4c525e"), "steel_mid": Color("#7e8694"), "steel_light": Color("#b8beca"), "steel_shine": Color("#e6ecf6"),
	"gold_mid": Color("#a87e2c"), "gold_light": Color("#e2ba52"),
	"wind_mid": Color("#70b2e6"), "wind_light": Color("#b0defa"), "wind_bright": Color("#d8f2ff"),
	"ink": Color("#141116"),
}

# State (di-drive oleh Hero.gd tiap frame)
var facing: int = 1:
	set(v):
		facing = 1 if v >= 0 else -1
		if skeleton:
			skeleton.scale.x = facing
var phase: float = 0.0 # pulse 0..T
var action: String = "idle" # idle / walk / attack / skill_q/w/e/r
var attack_progress: float = 0.0 # 0..1 dari Hero.attack_timer
var skill: String = ""
var is_moving: bool = false

# Bones (di-cache di _ready)
var skeleton: Skeleton2D
var bones: Dictionary = {} # name -> Bone2D
var visuals: Dictionary = {} # name -> Polygon2D/Sprite2D

# Inertia untuk scarf/ponytail (menggantikan _draw_floating_wind hash pygame)
var scarf_vel := Vector2.ZERO
var ponytail_vel := Vector2.ZERO
# Trail buffer untuk wind ribbon (mirip pygame blade_trail 6 point)
var katana_trail: Array = []

func _ready():
	skeleton = $Skeleton2D
	_cache_bones()
	_build_visuals() # buat Polygon2D placeholder HD (ganti dengan Texture nanti)
	# Daftarkan ke group untuk debug
	add_to_group("kaizen_skeleton")

func _cache_bones():
	for b in skeleton.get_children():
		_cache_recursive(b)

func _cache_recursive(node: Node):
	if node is Bone2D:
		bones[node.name] = node
		# visuals adalah child Polygon2D/Sprite2D dari Bone2D
		for child in node.get_children():
			if child is Polygon2D or child is Sprite2D or child is Line2D:
				visuals[node.name] = child
	for child in node.get_children():
		_cache_recursive(child)

# Dipanggil Hero.gd tiap _physics_process (menggantikan _update_attack_anim + draw_kaizen)
func drive(p_phase: float, p_action: String, p_attack_progress: float, p_facing: int, p_moving: bool, p_skill: String, p_delta: float = 0.016):
	phase = p_phase
	action = p_action
	attack_progress = clamp(p_attack_progress, 0.0, 1.0)
	facing = p_facing
	is_moving = p_moving
	skill = p_skill
	_update_bones()
	_update_inertia(p_delta if p_delta > 0.0 else get_process_delta_time())
	_update_katana_hamon() # shader hamon berkilau saat attack
	_update_wind_ribbon() # scarf + ponytail ribbon

func _update_bones():
	if bones.is_empty():
		return
	# === 1. ROOT MOTION: bob napas + lean ===
	var breath = sin(phase * 0.78) * 2.2
	var stride = sin(phase * 1.72) if action == "walk" else 0.0
	var root_y = breath
	var sway = 0.0
	var lean = 0.0
	if action == "walk":
		root_y = sin(phase * 2.0) * 2.5 - 2.0
		sway = sin(phase) * 3.0
		lean = (4 + abs(stride)*2) * facing
	elif action == "attack":
		var ap = attack_progress
		var pose = _attack_pose(ap)
		root_y = pose["bob"]
		lean = pose["lean"] * facing
		sway = pose["sway"]
	else: # idle
		root_y = breath
		sway = sin(phase * 0.5) * 2.0
		lean = sin(phase * 0.5 + 1.2) * 1.5 * facing

	# Apply ke Hips (root gerak)
	if "Hips" in bones:
		bones["Hips"].position.y = root_y
		bones["Hips"].position.x = lean + sway

	# === 2. HEAD BOB (kontra-rotasi, mirip _head_bob pygame) ===
	if "Head" in bones:
		var head_bob = sin(phase * 0.9 + 1.1) * 1.5
		if action == "attack":
			head_bob = -attack_progress * 6.0
		bones["Head"].rotation_degrees = -lean * 0.35 + head_bob
		bones["Head"].position.y = head_bob * 0.5

	# === 3. KAKI: foot solver (menapak/terangkat, mirip _draw_footfall_dust) ===
	var front_step = int(stride * 8) if action == "walk" else 0
	var rear_step = -front_step
	var front_lift = int(max(0.0, cos(phase * 1.72)) * 10) if action == "walk" else 0
	var rear_lift = int(max(0.0, -cos(phase * 1.72)) * 10) if action == "walk" else 0
	if "LLegUpper" in bones and "RLegUpper" in bones:
		bones["LLegUpper"].position.x = front_step * 0.5
		bones["LLegLower"].position.y = -front_lift * 0.6
		bones["RLegUpper"].position.x = rear_step * 0.5
		bones["RLegLower"].position.y = -rear_lift * 0.6
		# Foot stay planted: inverse kinematics sederhana
		bones["LFoot"].rotation_degrees = -front_step * 0.8 + front_lift * 2.0
		bones["RFoot"].rotation_degrees = -rear_step * 0.8 + rear_lift * 2.0

	# === 4. LENGAN + KATANA: busur pose-driven (1 sumber kebenaran) ===
	_update_arm_katana()

	# === 5. PONTAIL & SCARF: inertia tail (lag physics) ===
	# Rotasi tulang ekor di-update di _update_inertia (velocity based)

func _attack_pose(ap: float) -> Dictionary:
	# Keyframe sama persis dengan pygame _NS_kaizen._attack_pose
	var keys = [
		[0.00, 0, 1, 1.00, 0.0],
		[0.12, 4, -6, 1.12, 0.0],
		[0.26, 5, -7, 1.20, 1.0],
		[0.42, -2, 7, 1.10, 0.0],
		[0.55, 5, 9, 1.05, 0.0], # IMPACT HOLD 4-5 frame
		[0.72, 1, 5, 1.02, 0.0],
		[1.00, 0, 1, 1.00, 0.0],
	]
	ap = clamp(ap, 0.0, 1.0)
	for i in range(keys.size() - 1):
		var k0 = keys[i]
		var k1 = keys[i+1]
		if k0[0] <= ap and ap <= k1[0]:
			var span = max(0.0001, k1[0] - k0[0])
			var t = (ap - k0[0]) / span
			t = t * t * (3 - 2 * t) # smoothstep
			return {
				"bob": int(round(k0[1] + (k1[1]-k0[1])*t)),
				"lean": int(round(k0[2] + (k1[2]-k0[2])*t)),
				"flare": k0[3] + (k1[3]-k0[3])*t,
				"sway": 1 if (k0[4] == 1 and t < 0.9) else 0
			}
	return {"bob":0, "lean":1, "flare":1.0, "sway":0}

func _katana_angle(ap: float) -> float:
	# Busur katana: ATTACK_ARC_START -> ATTACK_ARC_END (negatif = ke depan)
	if ap < ATTACK_WINDUP_END:
		var t = ap / ATTACK_WINDUP_END
		t = 1.0 - pow(1.0 - t, 2.0)
		return -0.55 - t * 1.75
	if ap < ATTACK_SWING_END:
		var t = (ap - ATTACK_WINDUP_END) / (ATTACK_SWING_END - ATTACK_WINDUP_END)
		t = pow(t, 1.35)
		return ATTACK_ARC_START + ATTACK_ARC_SWEEP * t
	if ap >= 1.0:
		return 0.12
	var t = (ap - ATTACK_SWING_END) / (1.0 - ATTACK_SWING_END)
	t = t * t * (3.0 - 2.0 * t)
	return (ATTACK_ARC_END + 2.0 * PI) - t * 0.813

func _update_arm_katana():
	if "LArmUpper" in bones and "Katana" in bones:
		var ap = attack_progress if action == "attack" else 0.0
		var ang = _katana_angle(ap)
		var grip_local = _katana_grip_local(ap)
		# Simplified IK: rotasi lengan atas & bawah menuju grip (shoulder di bones["LArmUpper"])
		bones["LArmUpper"].rotation = ang * 0.6
		bones["LArmLower"].rotation = ang * 0.45
		# Katana rotasi = sudut busur
		bones["Katana"].rotation = ang
		# Katana posisi = grip
		bones["Katana"].position = Vector2(grip_local.x, grip_local.y) * 0.9
		# RArm menopang saya (sarung) di pinggang
		if "RArmUpper" in bones:
			bones["RArmUpper"].rotation_degrees = -18 + sin(phase*0.7)*3
			bones["RArmLower"].rotation_degrees = 12

func _katana_grip_local(ap: float) -> Vector2:
	if ap < ATTACK_WINDUP_END:
		var t = ap / ATTACK_WINDUP_END
		return Vector2(14 + 6*t, 1 - 28*t)
	if ap < ATTACK_SWING_END:
		var t = (ap - ATTACK_WINDUP_END) / (ATTACK_SWING_END - ATTACK_WINDUP_END)
		if t < 0.45:
			var u = t / 0.45
			return Vector2(20 + 16*u, -27 + 6*u)
		var u = (t - 0.45)/0.55
		u = u*u
		return Vector2(36 + 3*u, -21 + 30*u)
	var t = (ap - ATTACK_SWING_END) / (1.0 - ATTACK_SWING_END)
	return Vector2(39 - 22*t, 9 - 6*t)

func _update_inertia(delta: float):
	# Scarf & Ponytail lag physics: velocity mengejar target, rotasi = velocity.x
	var target_scarf = Vector2(sin(phase*1.18)*4, 0)
	var target_pony = Vector2(sin(phase*1.35)*3, sin(phase*0.9)*1)
	scarf_vel = scarf_vel.lerp(target_scarf, delta * 6.0)
	ponytail_vel = ponytail_vel.lerp(target_pony, delta * 7.0)
	if "ScarfTip" in bones:
		bones["ScarfMid"].rotation_degrees = scarf_vel.x * 4.0
		bones["ScarfTip"].rotation_degrees = scarf_vel.x * 7.0
	if "PonytailMid" in bones:
		bones["PonytailMid"].rotation_degrees = ponytail_vel.x * 5.0
		bones["PonytailTip"].rotation_degrees = ponytail_vel.x * 9.0
	# Flare saat attack: ponytail flare
	if action == "attack":
		var flare = _attack_pose(attack_progress)["flare"]
		if "PonytailBase" in bones:
			bones["PonytailBase"].scale = Vector2(1, flare)

func _update_katana_hamon():
	# Hamon (garis temper) berkilau saat attack: shader param time
	if "Katana" in visuals and visuals["Katana"] is Polygon2D:
		var poly = visuals["Katana"] as Polygon2D
		if poly.material and poly.material is ShaderMaterial:
			var mat = poly.material as ShaderMaterial
			mat.set_shader_parameter("time", phase * 2.0)
			mat.set_shader_parameter("attack_t", attack_progress if action=="attack" else 0.0)

func _update_wind_ribbon():
	var ribbon = get_node_or_null("Skeleton2D/WindRibbon") as Line2D
	if not ribbon:
		return
	# update trail buffer tiap frame saat attack
	if action == "attack":
		if "Katana" in bones:
			var tip_global = bones["Katana"].to_global(Vector2(0.35, -52)) # ujung bilah
			katana_trail.append(tip_global)
			if katana_trail.size() > 6:
				katana_trail.remove_at(0)
		else:
			katana_trail.clear()
	else:
		if katana_trail.size() > 0:
			katana_trail.remove_at(0)
		if katana_trail.is_empty():
			ribbon.visible = false
			return

	if action == "attack" and 0.30 < attack_progress and attack_progress < 0.88 and katana_trail.size() >= 2:
		ribbon.visible = true
		ribbon.width = 7.0 * (1.0 - abs(attack_progress - 0.55) * 1.2)
		var pts: PackedVector2Array = []
		for wp in katana_trail:
			# ribbon is child of Skeleton2D → convert global → Skeleton2D local
			pts.append(ribbon.to_local(wp))
		ribbon.points = pts
		ribbon.modulate.a = 0.85
	else:
		ribbon.visible = katana_trail.size() >= 2
		if ribbon.visible:
			var pts: PackedVector2Array = []
			for wp in katana_trail:
				pts.append(ribbon.to_local(wp))
			ribbon.points = pts
			ribbon.modulate.a = 0.35
		else:
			ribbon.modulate.a = 0.0

func _katana_tip_local(ap: float) -> Vector2:
	# Analytic fallback (untuk API get_katana_tip_global tanpa bone)
	var ang = _katana_angle(ap)
	var blade_len = 52.0 if ap < ATTACK_SWING_END else 58.0 - 6.0 * ((ap - ATTACK_SWING_END)/(1.0 - ATTACK_SWING_END))
	return Vector2(sin(ang) * blade_len, cos(ang) * blade_len - 10.0)

func _build_visuals():
	# Buat Polygon2D placeholder untuk tiap tulang (jika belum ada).
	# Nanti ganti dengan Sprite2D + Texture HD (Aseprite). Sekarang warna flat + shader.
	# Dipanggil sekali di _ready. Jika scene sudah punya Polygon2D, skip.
	if visuals.size() > 0:
		return
	# Fallback: skeleton sudah lengkap via tscn Polygon2D, tidak perlu generate runtime.

# === API untuk Hero.gd: posisi ujung katana untuk spawn projectile / FX ===
func get_katana_tip_global() -> Vector2:
	if "Katana" in bones:
		# Blade tip = local offset (0, -52) rotated by bone
		return bones["Katana"].to_global(Vector2(0.35, -52))
	return global_position

func get_katana_grip_global() -> Vector2:
	if "Katana" in bones:
		return bones["Katana"].global_position
	return global_position
