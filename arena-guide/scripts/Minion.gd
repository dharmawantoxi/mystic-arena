extends Node2D
class_name MinionUnit
## Minion - ikut waypoint lane diagonal, bertarung, datangi nexus.

var team: String = "blue"
var max_hp: float = 120.0
var hp: float = 120.0
var damage: float = 8.0
var speed: float = 60.0
var attack_range: float = 42.0
var attack_interval: float = 1.0
var arrived: bool = false

var path := PackedVector2Array()
var _path_i: int = 1
var _lateral: float = 0.0
var _enemy = null
var _cooldown: float = 0.0
var _flash: float = 0.0


func _ready() -> void:
	add_to_group("minions")


func setup(team_name: String, lane_path: PackedVector2Array, forward: bool, lateral: float) -> void:
	team = team_name
	if forward:
		path = lane_path
	else:
		path = PackedVector2Array()
		for i in range(lane_path.size() - 1, -1, -1):
			path.append(lane_path[i])
	position = path[0]
	_path_i = 1
	_lateral = lateral
	queue_redraw()


func is_alive() -> bool:
	return hp > 0.0


func take_damage(amount: float) -> void:
	if hp <= 0.0:
		return
	hp -= amount
	_flash = 0.1
	queue_redraw()
	if hp <= 0.0:
		_die()


func _die() -> void:
	print("[Combat] Minion %s mati." % team)
	queue_free()


func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash -= delta
		modulate = Color(1.0, 0.4, 0.4) if _flash > 0.0 else Color.WHITE
	if hp <= 0.0:
		return
	if _cooldown > 0.0:
		_cooldown -= delta
	if not is_instance_valid(_enemy) or not _enemy.is_alive():
		_enemy = _find_enemy()
	if _enemy != null:
		if _cooldown <= 0.0:
			_enemy.take_damage(damage)
			Sound.play("hit")
			_cooldown = attack_interval
		return
	if arrived:
		_march_to_nexus(delta)
		return
	if _path_i >= path.size():
		position = path[path.size() - 1]
		arrived = true
		return
	var tp := _path_target()
	var to: Vector2 = tp - position
	var step: float = speed * delta
	if to.length() <= maxf(step, 6.0):
		_path_i += 1
	else:
		position += to.normalized() * step


func _path_target() -> Vector2:
	var p: Vector2 = path[mini(_path_i, path.size() - 1)]
	var j0 := maxi(0, _path_i - 1)
	var j1 := mini(path.size() - 1, _path_i + 1)
	var d: Vector2 = path[j1] - path[j0]
	if d.length() > 1.0:
		p += Vector2(-d.y, d.x).normalized() * _lateral
	return p


func _find_enemy():
	var best = null
	var best_d: float = attack_range
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m == null or m == self or m.team == team or not m.is_alive():
			continue
		var d: float = position.distance_to(m.position)
		if d <= best_d:
			best = m
			best_d = d
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t == null or t.team == team or not t.is_alive():
			continue
		var d2: float = position.distance_to(t.position)
		if d2 <= best_d + 24.0:
			best = t
			best_d = d2
	for n in get_tree().get_nodes_in_group("heroes"):
		var h := n as HeroUnit
		if h == null or h.team == team or not h.is_alive():
			continue
		var d3: float = position.distance_to(h.position)
		if d3 <= best_d:
			best = h
			best_d = d3
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx == null or nx.team == team or not nx.is_alive():
			continue
		var d4: float = position.distance_to(nx.position)
		if d4 <= best_d + 46.0:
			best = nx
			best_d = d4
	return best


func _march_to_nexus(delta: float) -> void:
	var nx := _find_nexus()
	if nx == null:
		return
	var d: float = position.distance_to(nx.position)
	if d > attack_range + 46.0:
		position += (nx.position - position).normalized() * speed * delta


func _find_nexus() -> NexusUnit:
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx != null and nx.team != team and nx.is_alive():
			return nx
	return null


func _draw() -> void:
	var body: Color = Color("#3E7CB1") if team == "blue" else Color("#B13E3E")
	draw_circle(Vector2(2, 8), 9.0, Color(0, 0, 0, 0.35))
	draw_circle(Vector2.ZERO, 10.0, body)
	draw_arc(Vector2.ZERO, 10.0, 0.0, TAU, 20, Color("#101418"), 2.0)
	draw_circle(Vector2.ZERO, 3.0, Color("#101418"))
	var ratio: float = clampf(hp / max_hp, 0.0, 1.0)
	draw_rect(Rect2(-10, -22, 20, 3), Color("#101418"))
	draw_rect(Rect2(-10, -22, 20.0 * ratio, 3), Color("#5FD35F"))
