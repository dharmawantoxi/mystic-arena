# UnitSilhouette.gd — renderer MINIMAL ala pygame dulu.
#
# Port visual dari heroes._draw_generic_hero + minion blob:
#   shadow ellipse, badan lingkaran, highlight, mata, senjata sederhana.
# Godot 4.3 TIDAK punya CanvasItem.draw_ellipse (baru 4.6) — ellipse
# pakai draw_colored_polygon. Outline lingkaran pakai draw_arc.
#
# Nanti tiap hero di-upgrade satu-satu lewat RendererRegistry (ganti
# node ini dengan Skeleton2D / SpriteFrames). Jangan tambah shader /
# partikel / tulang di file ini — itu tugas upgrade, bukan baseline.
extends Node2D

enum Kind { HERO, BOSS, MINION }

var kind: int = Kind.HERO
var unit_type: String = ""
var role: String = ""
var team: String = "blue"
var fill: Color = Color("#c8c8c8")
var fill_dark: Color = Color("#646464")
var radius: float = 16.0
var facing: int = 1
var phase: float = 0.0
var action: String = "idle"
var attack_progress: float = 0.0
var flash_amount: float = 0.0:
	set(v):
		flash_amount = clampf(v, 0.0, 1.0)
		queue_redraw()
var dmg_school: String = "physical"
var is_ranged: bool = false
var boss_class: String = "mini" # mini | true  (hanya Kind.BOSS)

# Kit deterministik dari nama — 222 hero tidak boleh identik total.
var _seed: int = 0
var _hat: int = 0 # 0 bare, 1 helm, 2 hood
var _stripe: int = 0
var _kit: String = "sword" # sword | bow | staff | club | spear | axe


func configure(p_kind: int, p_type: String, p_team: String, p_fill: Color,
		p_fill_dark: Color, p_radius: float, p_role: String = "",
		p_school: String = "physical", p_ranged: bool = false,
		p_boss_class: String = "mini") -> void:
	kind = p_kind
	unit_type = p_type
	team = p_team
	fill = p_fill
	fill_dark = p_fill_dark
	radius = maxf(6.0, p_radius)
	role = p_role
	dmg_school = p_school
	is_ranged = p_ranged
	boss_class = p_boss_class
	_seed = p_type.hash()
	_hat = posmod(_seed, 3)
	_stripe = posmod(_seed / 7, 4)
	_kit = _pick_kit()
	queue_redraw()


func drive(p_phase: float, p_action: String, p_attack: float, p_facing: int) -> void:
	phase = p_phase
	action = p_action
	attack_progress = clampf(p_attack, 0.0, 1.0)
	facing = 1 if p_facing >= 0 else -1
	queue_redraw()


func _pick_kit() -> String:
	if kind == Kind.MINION:
		match unit_type:
			"undead":
				return "staff"
			"dark_rider":
				return "spear"
			"troll":
				return "club"
			"orc":
				return "axe"
			_:
				return "club"
	var role_l := role.to_lower()
	if is_ranged or "marksman" in role_l or "ranger" in role_l or "archer" in role_l:
		if dmg_school == "magic" or "mage" in role_l or "sorcer" in role_l:
			return "staff"
		return "bow"
	if dmg_school == "magic" or "mage" in role_l or "witch" in role_l:
		return "staff"
	if "axe" in role_l or "berserker" in role_l:
		return "axe"
	if posmod(_seed, 5) == 0:
		return "spear"
	return "sword"


func _lit(c: Color) -> Color:
	if flash_amount <= 0.001:
		return c
	return c.lerp(Color(1, 1, 1, c.a), flash_amount)


func _team_col() -> Color:
	return Color("#3d8cff") if team == "blue" else Color("#e03c3c")


func _draw() -> void:
	# Origin = telapak kaki. Hadap kanan; parent Visual.scale.x membalik.
	var r := radius
	var bob := sin(phase * 0.85) * (1.2 if action != "walk" else 0.0)
	if action == "walk":
		bob = sin(phase * 2.1) * 1.8 - 0.6
	elif action == "attack":
		bob = -attack_progress * r * 0.12
	var lean := 0.0
	if action == "walk":
		lean = sin(phase * 2.1) * r * 0.08
	elif action == "attack":
		lean = _attack_lean() * r
	var cx := lean
	var feet_y := 0.0
	var hip_y := -r * 0.55 + bob
	var head_r := r * (0.62 if kind == Kind.MINION else 0.72)
	if kind == Kind.BOSS:
		head_r = r * 0.68
	var head_y := hip_y - r * (1.15 if kind != Kind.MINION else 0.95) + bob * 0.3
	if kind == Kind.BOSS:
		head_y -= r * 0.15
	_draw_shadow(Vector2(cx, feet_y + 2.0), r)
	_draw_team_ring(Vector2(cx, feet_y + 3.0), r)
	if kind == Kind.MINION and unit_type == "dark_rider":
		_draw_mount(Vector2(cx, feet_y), r)
	_draw_legs(Vector2(cx, hip_y), r)
	_draw_torso(Vector2(cx, hip_y), r)
	_draw_weapon(Vector2(cx, hip_y - r * 0.15), r)
	_draw_head(Vector2(cx, head_y), head_r)
	if kind == Kind.BOSS:
		_draw_horns(Vector2(cx, head_y), head_r)


func _attack_lean() -> float:
	# windup mundur, slash maju — paritas pose pygame 6-frame kasar
	var ap := attack_progress
	if ap < 0.28:
		return -0.18 - ap * 0.4
	if ap < 0.58:
		var t := (ap - 0.28) / 0.30
		return -0.30 + t * 0.72
	return 0.42 * (1.0 - (ap - 0.58) / 0.42)


func _swing() -> float:
	# sudut senjata (radian), 0 = tegak ke atas
	if action != "attack":
		if _kit == "bow":
			return -0.35
		if _kit == "staff":
			return 0.45
		return 0.55
	var ap := attack_progress
	if ap < 0.28:
		return -0.9 - ap * 2.2
	if ap < 0.58:
		var t := (ap - 0.28) / 0.30
		t = t * t * (3.0 - 2.0 * t)
		return -1.5 + t * 3.4
	return 1.9 - (ap - 0.58) / 0.42 * 1.3


func _draw_shadow(center: Vector2, r: float) -> void:
	_ellipse(center, r * 1.15, r * 0.32, Color(0, 0, 0, 0.28))


func _draw_team_ring(center: Vector2, r: float) -> void:
	var col := _team_col()
	col.a = 0.85
	draw_arc(center, r * 0.95, 0.0, TAU, 24, col, 2.0)


func _draw_legs(hip: Vector2, r: float) -> void:
	var stride := 0.0
	var lift_l := 0.0
	var lift_r := 0.0
	if action == "walk":
		stride = sin(phase * 2.1) * r * 0.45
		lift_l = maxf(0.0, cos(phase * 2.1)) * r * 0.22
		lift_r = maxf(0.0, -cos(phase * 2.1)) * r * 0.22
	elif action == "attack":
		stride = r * 0.15
	var leg := _lit(fill_dark.darkened(0.15))
	var thick := r * 0.22
	var left := hip + Vector2(-r * 0.28 + stride, r * 0.55 - lift_l)
	var right := hip + Vector2(r * 0.28 - stride, r * 0.55 - lift_r)
	_capsule(hip + Vector2(-r * 0.12, 0), left, thick, leg)
	_capsule(hip + Vector2(r * 0.12, 0), right, thick, leg)
	# sepatu
	draw_circle(left, thick * 1.15, _lit(fill_dark.darkened(0.35)))
	draw_circle(right, thick * 1.15, _lit(fill_dark.darkened(0.35)))


func _draw_torso(hip: Vector2, r: float) -> void:
	var body := _lit(fill)
	var dark := _lit(fill_dark)
	var w := r * (1.05 if kind == Kind.BOSS else 0.92)
	var h := r * (1.15 if kind != Kind.MINION else 0.9)
	var top := hip + Vector2(0, -h)
	# outline gelap (pygame circle + 2px dark ring)
	_capsule(top, hip + Vector2(0, h * 0.15), w * 0.55 + 1.6, Color(0.05, 0.04, 0.06, 1))
	_capsule(top, hip + Vector2(0, h * 0.15), w * 0.55, body)
	# perut lebih gelap
	draw_circle(hip + Vector2(0, h * 0.05), w * 0.42, dark)
	# highlight kiri-atas (generic hero pygame)
	var hl := _lit(Color(
		minf(1.0, fill.r + 0.22), minf(1.0, fill.g + 0.22), minf(1.0, fill.b + 0.22), 1))
	draw_circle(top + Vector2(-w * 0.18, h * 0.15), w * 0.22, hl)
	# stripe dada (beda per hero_type)
	if _stripe == 1:
		draw_line(top + Vector2(-w * 0.25, h * 0.45), top + Vector2(w * 0.25, h * 0.45),
			_lit(_team_col()), 2.0)
	elif _stripe == 2:
		draw_circle(top + Vector2(0, h * 0.4), w * 0.12, _lit(_team_col()))
	elif _stripe == 3:
		draw_colored_polygon(PackedVector2Array([
			top + Vector2(0, h * 0.22),
			top + Vector2(w * 0.18, h * 0.55),
			top + Vector2(-w * 0.18, h * 0.55),
		]), _lit(fill_dark.lightened(0.1)))


func _draw_head(center: Vector2, head_r: float) -> void:
	var skin := _lit(fill.lightened(0.18))
	var ink := Color(0.08, 0.06, 0.07, 1)
	draw_circle(center + Vector2(1, 1), head_r + 1.6, ink)
	draw_circle(center, head_r, skin)
	draw_arc(center, head_r, 0.0, TAU, 24, _lit(fill_dark), 1.6)
	# highlight
	draw_circle(center + Vector2(-head_r * 0.32, -head_r * 0.32), head_r * 0.38,
		_lit(skin.lightened(0.25)))
	# mata (pygame generic: hitam + iris tim)
	var eye := _team_col()
	if kind == Kind.MINION and unit_type == "undead":
		eye = Color("#b4ff9a")
	var eye_y := -head_r * 0.12
	var eye_x := head_r * 0.32
	var er := maxf(1.6, head_r * 0.16)
	draw_circle(center + Vector2(-eye_x, eye_y), er + 1.1, ink)
	draw_circle(center + Vector2(eye_x, eye_y), er + 1.1, ink)
	draw_circle(center + Vector2(-eye_x, eye_y), er, eye)
	draw_circle(center + Vector2(eye_x, eye_y), er, eye)
	draw_circle(center + Vector2(-eye_x - 0.6, eye_y - 0.6), maxf(0.8, er * 0.35), Color(1, 1, 1, 0.9))
	draw_circle(center + Vector2(eye_x - 0.6, eye_y - 0.6), maxf(0.8, er * 0.35), Color(1, 1, 1, 0.9))
	if kind == Kind.MINION:
		_draw_minion_face(center, head_r, ink)
	_draw_hat(center, head_r)


func _draw_minion_face(center: Vector2, head_r: float, ink: Color) -> void:
	match unit_type:
		"goblin":
			# telinga runcing
			var ear := _lit(fill.darkened(0.1))
			draw_colored_polygon(PackedVector2Array([
				center + Vector2(-head_r * 0.7, -head_r * 0.1),
				center + Vector2(-head_r * 1.25, -head_r * 0.7),
				center + Vector2(-head_r * 0.45, -head_r * 0.45),
			]), ear)
			draw_colored_polygon(PackedVector2Array([
				center + Vector2(head_r * 0.7, -head_r * 0.1),
				center + Vector2(head_r * 1.25, -head_r * 0.7),
				center + Vector2(head_r * 0.45, -head_r * 0.45),
			]), ear)
		"orc":
			# taring
			draw_colored_polygon(PackedVector2Array([
				center + Vector2(-head_r * 0.28, head_r * 0.35),
				center + Vector2(-head_r * 0.12, head_r * 0.72),
				center + Vector2(-head_r * 0.05, head_r * 0.32),
			]), Color("#f2efe4"))
			draw_colored_polygon(PackedVector2Array([
				center + Vector2(head_r * 0.28, head_r * 0.35),
				center + Vector2(head_r * 0.12, head_r * 0.72),
				center + Vector2(head_r * 0.05, head_r * 0.32),
			]), Color("#f2efe4"))
		"troll":
			draw_circle(center + Vector2(0, head_r * 0.15), head_r * 0.18, _lit(fill.darkened(0.25)))
		"undead":
			# mata hollow sudah diiris hijau; tambah rahang
			draw_line(center + Vector2(-head_r * 0.35, head_r * 0.4),
				center + Vector2(head_r * 0.35, head_r * 0.4), ink, 1.5)
		"dark_rider":
			draw_rect(Rect2(center + Vector2(-head_r * 0.55, -head_r * 0.15),
				Vector2(head_r * 1.1, head_r * 0.22)), ink, true)


func _draw_hat(center: Vector2, head_r: float) -> void:
	if kind == Kind.MINION:
		return
	var dark := _lit(fill_dark.darkened(0.2))
	if _kit == "staff" or _hat == 2:
		# hood
		draw_colored_polygon(PackedVector2Array([
			center + Vector2(-head_r * 1.05, -head_r * 0.15),
			center + Vector2(0, -head_r * 1.35),
			center + Vector2(head_r * 1.05, -head_r * 0.15),
			center + Vector2(head_r * 0.7, head_r * 0.35),
			center + Vector2(-head_r * 0.7, head_r * 0.35),
		]), dark)
		return
	if _hat == 1 or kind == Kind.BOSS:
		# helm
		draw_arc(center + Vector2(0, -head_r * 0.15), head_r * 1.02, PI, TAU, 16,
			_lit(fill_dark.lightened(0.05)), head_r * 0.35)
		draw_line(center + Vector2(-head_r * 0.9, -head_r * 0.05),
			center + Vector2(head_r * 0.9, -head_r * 0.05), _lit(_team_col()), 2.0)


func _draw_horns(center: Vector2, head_r: float) -> void:
	var horn := _lit(fill_dark.lightened(0.1))
	var h := head_r * (1.35 if boss_class == "true" else 0.95)
	draw_colored_polygon(PackedVector2Array([
		center + Vector2(-head_r * 0.55, -head_r * 0.55),
		center + Vector2(-head_r * 0.95, -head_r - h * 0.35),
		center + Vector2(-head_r * 0.15, -head_r * 0.75),
	]), horn)
	draw_colored_polygon(PackedVector2Array([
		center + Vector2(head_r * 0.55, -head_r * 0.55),
		center + Vector2(head_r * 0.95, -head_r - h * 0.35),
		center + Vector2(head_r * 0.15, -head_r * 0.75),
	]), horn)
	if boss_class == "true":
		# mahkota kecil
		draw_colored_polygon(PackedVector2Array([
			center + Vector2(-head_r * 0.55, -head_r * 0.7),
			center + Vector2(-head_r * 0.35, -head_r * 1.35),
			center + Vector2(0, -head_r * 0.85),
			center + Vector2(head_r * 0.35, -head_r * 1.35),
			center + Vector2(head_r * 0.55, -head_r * 0.7),
		]), _lit(Color("#e2ba52")))


func _draw_mount(origin: Vector2, r: float) -> void:
	var body := _lit(fill_dark.darkened(0.25))
	_ellipse(origin + Vector2(-r * 0.2, -r * 0.15), r * 1.35, r * 0.55, body)
	draw_circle(origin + Vector2(r * 0.95, -r * 0.35), r * 0.42, body)
	# kaki kuda
	var leg := body.darkened(0.15)
	draw_rect(Rect2(origin + Vector2(-r * 0.9, -r * 0.05), Vector2(r * 0.22, r * 0.7)), leg, true)
	draw_rect(Rect2(origin + Vector2(r * 0.35, -r * 0.05), Vector2(r * 0.22, r * 0.7)), leg, true)


func _draw_weapon(grip: Vector2, r: float) -> void:
	var ang := _swing()
	var dir := Vector2(sin(ang), -cos(ang))
	var steel := _lit(Color("#c5c9d4"))
	var steel_d := _lit(Color("#5a6270"))
	var wood := _lit(Color("#6b4423"))
	match _kit:
		"bow":
			var tip := grip + dir * r * 1.6
			var n := dir.orthogonal()
			draw_arc(grip + dir * r * 0.4, r * 0.95, ang - 1.1, ang + 1.1, 12,
				_lit(Color("#8b5a2b")), 2.2)
			draw_line(grip + n * r * 0.7, grip - n * r * 0.7, Color("#e8dcc8"), 1.0)
			if action == "attack" and attack_progress < 0.55:
				draw_line(grip, tip, _lit(fill), 1.5)
		"staff":
			var tip := grip + dir * r * 2.1
			draw_line(grip - dir * r * 0.6, tip, wood, 3.0)
			draw_circle(tip, r * 0.28, _lit(fill.lightened(0.2)))
			draw_circle(tip, r * 0.14, Color(1, 1, 1, 0.85))
			if action == "attack":
				draw_arc(tip, r * 0.55, 0.0, TAU, 16, _lit(fill), 1.2)
		"axe":
			var tip := grip + dir * r * 1.55
			draw_line(grip, tip, wood, 3.0)
			var n := dir.orthogonal()
			draw_colored_polygon(PackedVector2Array([
				tip + n * r * 0.75, tip + dir * r * 0.2, tip - n * r * 0.35, tip - dir * r * 0.15,
			]), steel)
			draw_colored_polygon(PackedVector2Array([
				tip + n * r * 0.75, tip + dir * r * 0.2, tip - dir * r * 0.05,
			]), steel_d)
		"spear":
			var tip := grip + dir * r * 2.3
			draw_line(grip - dir * r * 0.4, tip, wood, 2.2)
			draw_colored_polygon(PackedVector2Array([
				tip, tip - dir * r * 0.45 + dir.orthogonal() * r * 0.18,
				tip - dir * r * 0.45 - dir.orthogonal() * r * 0.18,
			]), steel)
		"club":
			var tip := grip + dir * r * 1.4
			draw_line(grip, tip, wood, 3.5)
			draw_circle(tip, r * 0.32, wood.lightened(0.1))
		_:
			# sword
			var tip := grip + dir * r * 1.85
			draw_line(grip, tip, steel_d, 4.0)
			draw_line(grip, tip, steel, 2.2)
			draw_line(grip + dir.orthogonal() * r * 0.35, grip - dir.orthogonal() * r * 0.35,
				steel_d, 2.4)
			draw_circle(grip, r * 0.12, _lit(Color("#c9a227")))


# ═══ primitif (paritas pygame.draw, Godot 4.3-safe) ═══
func _ellipse(center: Vector2, rx: float, ry: float, color: Color, n: int = 24) -> void:
	var pts := PackedVector2Array()
	pts.resize(n)
	for i in n:
		var a := TAU * float(i) / float(n)
		pts[i] = center + Vector2(cos(a) * rx, sin(a) * ry)
	draw_colored_polygon(pts, color)


func _capsule(a: Vector2, b: Vector2, rad: float, color: Color) -> void:
	draw_circle(a, rad, color)
	draw_circle(b, rad, color)
	var d := b - a
	if d.length_squared() < 0.0001:
		return
	var n := d.normalized().orthogonal() * rad
	draw_colored_polygon(PackedVector2Array([a + n, b + n, b - n, a - n]), color)
