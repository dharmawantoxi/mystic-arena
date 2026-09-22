extends Node2D
class_name NexusUnit
## Langkah 9: markas. Hancur = menang/kalah.

signal destroyed(nexus: NexusUnit)

var team: String = "blue"
var max_hp: float = 1500.0
var hp: float = 1500.0

var _flash: float = 0.0


func _ready() -> void:
	add_to_group("nexus")


func setup(team_name: String, start_pos: Vector2, p_hp: float) -> void:
	team = team_name
	position = start_pos
	max_hp = p_hp
	hp = p_hp
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
		destroyed.emit(self)
		queue_free()


func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash -= delta
		modulate = Color(1.0, 0.4, 0.4) if _flash > 0.0 else Color.WHITE


func _draw() -> void:
	var body: Color = Color("#3E7CB1") if team == "blue" else Color("#B13E3E")
	draw_circle(Vector2(4, 20), 44.0, Color(0, 0, 0, 0.35))
	draw_rect(Rect2(-40, -10, 80, 34), Color("#5A5E6B"))
	draw_rect(Rect2(-40, -10, 80, 34), Color("#101418"), false, 3.0)
	draw_rect(Rect2(-26, -44, 52, 40), Color("#8A8F9C"))
	draw_rect(Rect2(-26, -44, 52, 40), Color("#101418"), false, 3.0)
	draw_colored_polygon(PackedVector2Array([Vector2(-32, -44), Vector2(32, -44), Vector2(0, -72)]), body)
	draw_circle(Vector2(0, -58), 8.0, Color("#C9A227"))
	var ratio: float = clampf(hp / max_hp, 0.0, 1.0)
	draw_rect(Rect2(-46, -92, 92, 8), Color("#101418"))
	draw_rect(Rect2(-46, -92, 92.0 * ratio, 8), Color("#5FD35F"))
