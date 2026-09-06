class_name Kaizen
extends Character
## Kaizen — Wind Blade Assassin.
##
## Top-down 2D melee fighter. Wields a katana. Specialises in close-range
## mobility skills that chain into each other (Q combo, E jump-slash, R ult).
##
## Reference benchmark: Yasuo (LoL). We borrow Yasuo's visual hierarchy —
##   * primary effect is a single, readable shape (a crescent slash),
##   * secondary particles orbit / fall off the primary,
##   * accent sparks flash only at the moment of impact.
## We do NOT borrow his identity: Kaizen is a katana-wielding wind mage
## (steel + wind), not a swordless airbender.
##
## Node tree (see Kaizen.tscn):
##   Kaizen (CharacterBody2D)
##   ├── Body (Node2D)                — root for the rig (mirrored by facing)
##   │   ├── Torso
##   │   ├── Head
##   │   ├── SwordArm                 — rotates with the swing animation
##   │   │   ├── UpperArm
##   │   │   ├── LowerArm
##   │   │   └── Sword
##   │   └── Legs
##   ├── AnimationPlayer
##   ├── AnimationTree
##   ├── Hitbox (Area2D)
##   └── Skills/
##       ├── Q  (KaizenSkillQ)
##       ├── W  (KaizenSkillW)
##       ├── E  (KaizenSkillE)
##       └── R  (KaizenSkillR)

## Kaizen-specific stats (overrides the Character defaults).
@export var stats: CharacterStats

## Skill slot auto-discovered from the Skills/Q, Skills/W, etc children.
## Set in _ready, no need to wire in the editor.
var skill_q: KaizenSkillQ
var skill_w: KaizenSkillW
var skill_e: KaizenSkillE
var skill_r: KaizenSkillR

## Speed multiplier while the E jump is happening. Set by the skill itself.
var _e_jump_speed_mult: float = 1.0

## Tracks whether the basic attack is currently swinging.
var _attack_active: bool = false

## Reference to the body root so we can hand it to the builder.
@onready var body_root: Node2D = $Body


func _ready() -> void:
	super._ready()
	# Build the procedural rig.
	if body_root:
		KaizenBodyBuilder.build(body_root)
	# Apply stats if assigned.
	if stats:
		max_hp = stats.max_hp
		hp = stats.max_hp
		speed = stats.speed
		damage = stats.damage
		attack_cooldown_max = stats.attack_cooldown
	# Discover skill children. Their scripts declare the right type, so
	# the cast is safe.
	skill_q = _find_skill(&"Q", KaizenSkillQ) as KaizenSkillQ
	skill_w = _find_skill(&"W", KaizenSkillW) as KaizenSkillW
	skill_e = _find_skill(&"E", KaizenSkillE) as KaizenSkillE
	skill_r = _find_skill(&"R", KaizenSkillR) as KaizenSkillR
	# Wire skills to this character so they can read its state.
	for sk in [skill_q, skill_w, skill_e, skill_r]:
		if sk:
			sk.owner_character = self
	# Add a small wind aura by default — visual only.
	if has_node("/root/VFXManager"):
		VFXManager.spawn(&"kaizen_idle_aura", global_position, 0.0, 999.0)


func _find_skill(child_name: StringName, _type) -> Node:
	var path := "Skills/" + String(child_name)
	if has_node(path):
		return get_node(path)
	return null


func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	# Tick every skill.
	for sk in [skill_q, skill_w, skill_e, skill_r]:
		if sk:
			sk.tick(delta)
	# Input -> movement.
	_handle_movement(delta)
	# Animation state machine.
	_update_animation_state()


## Basic attack: a 0.18 s swing that deals damage via the hitbox.
func basic_attack() -> void:
	if attack_timer > 0.0 or stunned or not alive:
		return
	if _is_any_skill_casting():
		return
	# Briefly flip to face the target if we have one.
	if target != null and is_instance_valid(target):
		face_target(target)
	# Trigger the swing animation; damage is dealt by the hitbox during the
	# active window (see Character.start_attack).
	start_attack(0.18)
	# Play a small slash effect.
	var origin := global_position + Vector2(facing * 40, -10)
	VFXManager.spawn(&"kaizen_basic_slash", origin, 0.0, 0.25)
	GameFeel.shake(0)
	# Update animation state.
	if anim_tree:
		anim_tree.set("parameters/conditions/is_attacking", true)
		await get_tree().create_timer(0.25).timeout
		if anim_tree:
			anim_tree.set("parameters/conditions/is_attacking", false)


func _handle_movement(delta: float) -> void:
	if stunned or not alive:
		velocity = Vector2.ZERO
		move_and_slide()
		return
	var input_vec := Vector2.ZERO
	input_vec.x = Input.get_axis(&"move_left", &"move_right")
	input_vec.y = Input.get_axis(&"move_up", &"move_down")
	if input_vec.length() > 1.0:
		input_vec = input_vec.normalized()
	velocity = input_vec * speed * _e_jump_speed_mult
	move_and_slide()
	# Update facing from horizontal input.
	if abs(input_vec.x) > 0.1:
		facing = 1 if input_vec.x > 0 else -1
		$Body.scale.x = facing


func _update_animation_state() -> void:
	if anim_tree == null:
		return
	# Only set conditions if the AnimationTree has a state machine that
	# actually defines them. A freshly-created state machine has no
	# transitions, so the parameter setters would no-op silently. We still
	# emit the calls (Godot ignores unknown parameters) but guard against
	# the case where the tree is inactive.
	if not anim_tree.active:
		return
	var moving := velocity.length() > 5.0
	# Condition parameters — silently ignored if the state machine doesn't
	# have a transition that reads them. That's fine for a vertical slice
	# where animations are optional polish on top of the procedural rig.
	anim_tree.set("parameters/conditions/is_moving", moving)
	anim_tree.set("parameters/conditions/is_idle", not moving and not _attack_active)
	# Skill states. The AnimationTree blends these back to idle when false.
	if skill_q:
		anim_tree.set("parameters/conditions/is_casting_q", skill_q.is_casting or skill_q.is_active)
	if skill_w:
		anim_tree.set("parameters/conditions/is_casting_w", skill_w.is_casting or skill_w.is_active)
	if skill_e:
		anim_tree.set("parameters/conditions/is_casting_e", skill_e.is_casting or skill_e.is_active)
	if skill_r:
		anim_tree.set("parameters/conditions/is_casting_r", skill_r.is_casting or skill_r.is_active)


func _unhandled_input(event: InputEvent) -> void:
	if not alive:
		return
	if event.is_action_pressed(&"attack"):
		basic_attack()
	elif event.is_action_pressed(&"skill_q") and skill_q:
		skill_q.try_cast(global_position)
	elif event.is_action_pressed(&"skill_w") and skill_w:
		skill_w.try_cast(global_position)
	elif event.is_action_pressed(&"skill_e") and skill_e:
		skill_e.try_cast(global_position)
	elif event.is_action_pressed(&"skill_r") and skill_r:
		skill_r.try_cast(global_position)


func _is_any_skill_casting() -> bool:
	for sk in [skill_q, skill_w, skill_e, skill_r]:
		if sk and (sk.is_casting or sk.is_active):
			return true
	return false


## Apply a slow (e.g. from a debuff). Default: 50% for 1.0 s.
func apply_slow(amount: float, duration: float) -> void:
	# Modulate the speed modifier via a tween. We don't track a base value
	# here because the stats resource is the single source of truth.
	var original := speed
	speed *= (1.0 - amount)
	var t := get_tree().create_timer(duration, false, false)
	t.timeout.connect(func (): speed = original)


## Apply a stun (lock movement + skills). Mirrors the Pygame `attack_timer`
## pattern on the enemy side.
func apply_stun(duration: float) -> void:
	stunned = true
	var t := get_tree().create_timer(duration, false, false)
	t.timeout.connect(func (): stunned = false)
