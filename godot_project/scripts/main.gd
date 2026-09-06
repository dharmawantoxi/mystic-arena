class_name Main
extends Node2D
## Demo scene root.
##
## Wires up:
##   * The procedural background (a flat warm-tan colour so the wind
##     effects have something to read against).
##   * One Kaizen character at the origin.
##   * Four EnemyDummies arranged in a row, so all skills can be tested.
##   * The camera rig follows the player.
##   * The HUD binds to the player.
##   * The VFXManager registers all the registered scenes.

@onready var camera_rig: CameraRig = $CameraRig
@onready var kaizen: Kaizen = $Kaizen
@onready var hud: HUD = $HUD


func _ready() -> void:
	# Register VFX scenes.
	VFXManager.register(&"kaizen_basic_slash", preload("res://scenes/KaizenSlash.tscn"))
	VFXManager.register(&"kaizen_q1_slash", preload("res://scenes/KaizenSlash.tscn"))
	VFXManager.register(&"kaizen_q2_slash", preload("res://scenes/KaizenSlash.tscn"))
	VFXManager.register(&"kaizen_e_sweep", preload("res://scenes/KaizenSweep.tscn"))
	VFXManager.register(&"kaizen_r_tornado", preload("res://scenes/KaizenTornado.tscn"))
	VFXManager.register(&"kaizen_wind_puff", preload("res://scenes/KaizenWindPuff.tscn"))
	VFXManager.register(&"kaizen_idle_aura", preload("res://scenes/KaizenIdleAura.tscn"))
	# Wire camera + HUD to the player.
	camera_rig.target = kaizen
	hud.bind(kaizen)
	# Bind the idle aura to the player.
	var aura = VFXManager.spawn(&"kaizen_idle_aura", kaizen.global_position, 0.0, 999.0)
	if aura and aura.has_method("bind_to"):
		aura.bind_to(kaizen)
	# Set up enemy dummies — pick nearest as target.
	_assign_targets()


func _physics_process(_delta: float) -> void:
	# Keep the player's target = nearest live enemy.
	_assign_targets()


func _assign_targets() -> void:
	if kaizen == null:
		return
	var best: Node2D = null
	var best_d := INF
	for c in get_tree().get_nodes_in_group("enemies"):
		if c is Node2D and is_instance_valid(c) and (c as Character).alive:
			var d := (c as Node2D).global_position.distance_to(kaizen.global_position)
			if d < best_d:
				best_d = d
				best = c
	if best:
		kaizen.target = best
