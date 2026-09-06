class_name Character
extends CharacterBody2D
## Base class for every controllable / AI-driven combatant.
##
## Replaces the Pygame Hero / Enemy classes. Subclasses (Kaizen, EnemyDummy,
## future bosses) extend this and override the virtual hooks.
##
## Coordinate convention: this is a top-down 2D fighter. Y+ is "down" on
## screen. The character faces left/right (facing = -1 / +1) and rotates its
## sword arm only — the body itself does NOT rotate, which keeps the
## silhouette readable.
##

## Emitted when HP drops to zero. Listeners should remove the node.
signal died
## Emitted whenever HP changes (after application, not before).
signal hp_changed(new_hp: int, max_hp: int)
## Emitted when the character is hit (after damage is applied).
signal hit_taken(amount: int, source: Node)
## Emitted whenever damage is dealt. Used by FloatingDamage / VFX / analytics.
signal damage_dealt(amount: int, target: Node)

@export var team: StringName = "blue"
@export var max_hp: int = 1000:
	set(v):
		max_hp = v
		if hp > max_hp:
			hp = max_hp

@export var hp: int = 1000:
	set(v):
		hp = clampi(v, 0, max_hp)
		hp_changed.emit(hp, max_hp)

@export var speed: float = 180.0
@export var attack_cooldown_max: float = 0.55
@export var damage: int = 80

## Current attack timer (counts DOWN to zero). When zero, the character can
## perform an attack; immediately after, it is set to attack_cooldown_max.
var attack_timer: float = 0.0
## Facing direction. -1 = left, +1 = right. Flips automatically from input.
var facing: int = 1
## True when the character is alive. Set false on death.
var alive: bool = true
## True while in a "cannot act" state (stunned, casting an uninterruptible
## skill, etc). Subclasses set this from their skill logic.
var stunned: bool = false

## Optional target. Subclasses can use it for auto-aim. May be null.
var target: Node = null

## Hitbox area — used to deal damage on attack. Disables itself when not
## attacking so the character cannot hurt enemies with their body.
@onready var hitbox: Area2D = $Hitbox

## AnimationTree — subclasses build their own state machine.
@onready var anim_tree: AnimationTree = $AnimationTree
@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var body_sprite: Node2D = $Body


func _ready() -> void:
	add_to_group("characters")
	# Hitbox disabled by default — only on during attack frames.
	if hitbox:
		hitbox.monitoring = false
		hitbox.area_entered.connect(_on_hitbox_area_entered)


func _physics_process(delta: float) -> void:
	if not alive:
		return
	attack_timer = max(0.0, attack_timer - delta)


## Deal damage to another character. Returns the actual amount applied
## (after reductions, immunities, etc — subclasses can override).
func take_damage(amount: int, source_team: StringName = "", source: Node = null) -> int:
	if not alive or amount <= 0:
		return 0
	# Friendly fire off (default).
	if source_team != "" and source_team == team:
		return 0
	hp -= amount
	hit_taken.emit(amount, source)
	if hp <= 0:
		alive = false
		died.emit()
		_on_death()
	return amount


## Deal a hit. Called by the attack pipeline. Default implementation
## forwards to [code]target.take_damage[/code] and emits damage_dealt.
func deal_damage(target_node: Node, amount: int) -> int:
	if target_node == null or not is_instance_valid(target_node):
		return 0
	if not target_node.has_method("take_damage"):
		return 0
	# Don't hurt friendlies.
	if target_node is Character and (target_node as Character).team == team:
		return 0
	var actual := target_node.call("take_damage", amount, team, self)
	if actual > 0:
		damage_dealt.emit(actual, target_node)
	return actual


## Begin a melee swing. The hitbox becomes active for [param duration]
## seconds; during that window anything entering the hitbox takes damage.
func start_attack(duration: float = 0.18) -> void:
	attack_timer = attack_cooldown_max
	if hitbox:
		hitbox.monitoring = true
		var t := get_tree().create_timer(duration, false, false)
		t.timeout.connect(_end_attack)


func _end_attack() -> void:
	if hitbox:
		hitbox.monitoring = false


func _on_hitbox_area_entered(area: Area2D) -> void:
	if not area.owner or area.owner == self:
		return
	if not area.owner.has_method("take_damage"):
		return
	var owner_node: Node = area.owner
	# Damage is dealt by the Character, but the Area is what the engine
	# dispatches. We forward the call to deal_damage.
	deal_damage(owner_node, damage)


## Override for death animation, sound, loot drop, etc.
func _on_death() -> void:
	# Default: hide after 1.5s and queue_free.
	var t := get_tree().create_timer(1.5, false, false)
	t.timeout.connect(queue_free)


## Flip facing towards the target (if any), else to mouse position.
func face_target(tgt: Node) -> void:
	if tgt == null or not is_instance_valid(tgt):
		return
	if tgt.global_position.x > global_position.x:
		facing = 1
	elif tgt.global_position.x < global_position.x:
		facing = -1
	if body_sprite:
		body_sprite.scale.x = facing
