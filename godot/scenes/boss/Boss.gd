# Boss.gd — Port dari bosses/base_boss.py
# Visual sama seperti Hero.tscn tapi scale 1.4x + aura + boss bar
extends CharacterBody2D

@export var boss_type: String = "abaddon"
@export var team: String = "red"

var max_hp: float = 30000
var hp: float = 30000
var damage: float = 120
var move_speed: float = 60.0
var is_dead: bool = false

@onready var visual: Node2D = $Visual
@onready var sprite: AnimatedSprite2D = $Visual/AnimatedSprite2D
@onready var aura: GPUParticles2D = $FX/Aura
@onready var hp_bar: ProgressBar = $UI/HPBar

func _ready():
	var s = BossDB.get_boss(boss_type)
	if not s.is_empty():
		max_hp = s["hp"]
		hp = max_hp
		damage = s["damage"]
		move_speed = s["speed"] * 60.0
	add_to_group("bosses")
	# Boss scale lebih besar (menggantikan SCALE=1.32 di pygame)
	visual.scale = Vector2(1.4, 1.4)

func take_damage(amount: float, from_team: String, dmg_type: String = "normal", source = null, school: String = ""):
	if is_dead: return
	hp -= amount
	if hp_bar: hp_bar.value = hp / max_hp * 100.0
	# hit flash via shader sama seperti Hero
	var mat = sprite.material as ShaderMaterial
	if mat:
		mat.set_shader_parameter("flash_amount", 1.0)
		create_tween().tween_property(mat, "shader_parameter/flash_amount", 0.0, 0.12)
	if hp <= 0:
		die()

func die():
	is_dead = true
	# Death: scale squash + fade (GPU, bukan ellipse manual)
	var tw = create_tween()
	tw.parallel().tween_property(visual, "scale", Vector2(1.6, 0.15), 0.45).set_trans(Tween.TRANS_BACK)
	tw.parallel().tween_property(self, "modulate:a", 0.0, 0.5)
	tw.tween_callback(queue_free)
	# Drop hero unlock (SaveManager)
	SaveManager.unlock_hero(boss_type)
