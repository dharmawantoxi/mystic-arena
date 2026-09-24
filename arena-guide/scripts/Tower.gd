extends Node2D
class_name TowerUnit
## Menara - diam, tembak minion dulu lalu hero.

signal destroyed(tower: TowerUnit)

var tower_id: String = "archer"
var tower_name: String = "Archer"
var team: String = "blue"
var max_hp: float = 800.0
var hp: float = 800.0
var damage: float = 18.0
var attack_range: float = 260.0
var attack_interval: float = 1.2
var slot_index: int = -1
# L37 — pygame _entity.py:687: armor = 2 + level. Port ini belum punya level
# menara, jadi semua menara dihitung level 1 → armor dasar 3.
const BASE_ARMOR: float = 3.0

var _enemy = null
var _cooldown: float = 0.0
var _shot_to: Vector2 = Vector2.ZERO
var _shot_t: float = 0.0
var _flash: float = 0.0


func _ready() -> void:
	add_to_group("towers")


func setup(data: Dictionary, team_name: String, start_pos: Vector2, p_slot: int) -> void:
	tower_id = str(data.get("id", "archer"))
	tower_name = str(data.get("name", "Archer"))
	max_hp = float(data.get("hp", 800))
	hp = max_hp
	damage = float(data.get("damage", 18))
	attack_range = float(data.get("range", 260.0))
	team = team_name
	position = start_pos
	slot_index = p_slot
	queue_redraw()


func is_alive() -> bool:
	return hp > 0.0


func take_damage(amount: float, school: String = "") -> void:
	if hp <= 0.0:
		return
	# L37: pygame menara HANYA memblok school 'physical' (_entity.py:1066);
	# tanpa school (pukulan minion) atau 'magic' (skill hero) → utuh.
	if school == "physical":
		amount = CombatCalc.mitigate(amount, BASE_ARMOR)
	hp -= amount
	_flash = 0.1
	queue_redraw()
	if hp <= 0.0:
		destroyed.emit(self)
		print("[Combat] Menara %s (%s) hancur." % [tower_name, team])
		queue_free()


func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash -= delta
		modulate = Color(1.0, 0.4, 0.4) if _flash > 0.0 else Color.WHITE
	if _shot_t > 0.0:
		_shot_t -= delta
		queue_redraw()
	if hp <= 0.0:
		return
	if _cooldown > 0.0:
		_cooldown -= delta
	if not is_instance_valid(_enemy) or not _enemy.is_alive():
		_enemy = _find_enemy()
	if _enemy != null and _cooldown <= 0.0:
		_enemy.take_damage(damage)
		Sound.play("shoot")
		_cooldown = attack_interval
		_shot_to = _enemy.position - position
		_shot_t = 0.15
		queue_redraw()


func _find_enemy():
	var best = null
	var best_d: float = attack_range
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m == null or m.team == team or not m.is_alive():
			continue
		var d: float = position.distance_to(m.position)
		if d <= best_d:
			best = m
			best_d = d
	if best == null:
		for n in get_tree().get_nodes_in_group("heroes"):
			var h := n as HeroUnit
			if h == null or h.team == team or not h.is_alive():
				continue
			var d2: float = position.distance_to(h.position)
			if d2 <= attack_range:
				return h
	return best


func _draw() -> void:
	var banner: Color = Color("#3E7CB1") if team == "blue" else Color("#B13E3E")
	draw_circle(Vector2(3, 14), 20.0, Color(0, 0, 0, 0.35))
	draw_rect(Rect2(-16, -16, 32, 36), Color("#6B6F7A"))
	draw_rect(Rect2(-16, -16, 32, 36), Color("#101418"), false, 2.0)
	draw_rect(Rect2(-11, -8, 22, 28), Color("#8A8F9C"))
	draw_colored_polygon(PackedVector2Array([Vector2(-14, -8), Vector2(14, -8), Vector2(0, -26)]), banner)
	if _shot_t > 0.0:
		draw_line(Vector2(0, -10), _shot_to, Color("#FFE28A"), 3.0)
	var ratio: float = clampf(hp / max_hp, 0.0, 1.0)
	draw_rect(Rect2(-20, -34, 40, 5), Color("#101418"))
	draw_rect(Rect2(-20, -34, 40.0 * ratio, 5), Color("#5FD35F"))
