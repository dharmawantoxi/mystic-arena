class_name KaizenIdleAura
extends VFXBase
## Subtle wind aura that follows the character.
##
## Three or four small wind streaks orbit slowly at the character's feet.
## Designed to read as "presence", not as a particle effect. The lifetime
## is set high (the manager passes 999 s) and the aura despawns when the
## character frees itself, via the [code]tree_exited[/code] signal.

@export var color: Color = Color(0.847, 0.949, 1.0, 0.6)
@export var color_dark: Color = Color(0.439, 0.698, 0.902, 0.4)
@export var streak_count: int = 4
@export var orbit_radius: float = 36.0

var _parent_char: Node2D = null
var _streaks: Array[Polygon2D] = []
var _time: float = 0.0


func _ready() -> void:
	super._ready()
	# The manager spawned us at the character's position. Move with them.
	# We do that by reparenting under the character — but the VFX manager
	# still owns the lifetime. Trick: set the global position every frame
	# to the character's position.
	# The VFXBase _ready already ran and set up tweens; for the aura, we
	# don't want a one-shot lifetime. We override _on_lifetime_done below.


func _animate() -> void:
	# Build streaks.
	for i in range(streak_count):
		var s := Polygon2D.new()
		var size := 6.0
		s.polygon = PackedVector2Array([
			Vector2(-size, 0),
			Vector2(size, 0),
			Vector2(size * 0.4, -size * 0.7),
		])
		s.color = color if i % 2 == 0 else color_dark
		add_child(s)
		_streaks.append(s)


func _process(delta: float) -> void:
	# Re-position to the parent's global position.
	if _parent_char and is_instance_valid(_parent_char):
		global_position = _parent_char.global_position
	_time += delta
	# Animate streaks in a slow orbit + bob.
	for i in range(_streaks.size()):
		var s := _streaks[i]
		var t := _time + float(i) / float(_streaks.size()) * TAU
		var radius := orbit_radius + sin(t * 1.7) * 4.0
		s.position = Vector2(cos(t * 0.7) * radius, sin(t * 0.5) * radius * 0.5)
		s.rotation = t * 0.5 + PI * 0.5
		s.modulate.a = 0.5 + 0.4 * sin(t * 1.3)


func bind_to(character: Node2D) -> void:
	_parent_char = character
	# Mirror despawn with the character.
	character.tree_exited.connect(queue_free)


func _on_lifetime_done() -> void:
	# Idle aura lives as long as the character does. Don't auto-free.
	pass
