class_name HUD
extends CanvasLayer
## Minimal HUD: HP bar, skill buttons, control hints.
##
## All UI lives inside a CanvasLayer so it stays screen-space regardless of
## the world camera. The character / autoload connections are made in
## [method _ready].

@onready var hp_bar: ProgressBar = $Root/HP/Bar
@onready var hp_label: Label = $Root/HP/Label
@onready var skill_q: Button = $Root/Skills/Q
@onready var skill_w: Button = $Root/Skills/W
@onready var skill_e: Button = $Root/Skills/E
@onready var skill_r: Button = $Root/Skills/R
@onready var hint_label: Label = $Root/Hint

## Reference to the player character. Set by [method bind].
var _player: Character = null
## Skill nodes cached after binding.
var _skills: Dictionary = {}


func _ready() -> void:
	# Make the HUD ignore world input.
	process_mode = Node.PROCESS_MODE_ALWAYS


## Bind the HUD to a player character. The HUD will track HP and skill
## cooldowns from then on.
func bind(player: Character) -> void:
	_player = player
	player.hp_changed.connect(_on_hp_changed)
	_on_hp_changed(player.hp, player.max_hp)
	# Discover skills.
	for n in ["Q", "W", "E", "R"]:
		var path := "Skills/" + n
		if player.has_node(path):
			var sk: Node = player.get_node(path)
			_skills[n.to_lower()] = sk
			sk.cooldown_set.connect(_on_skill_cooldown_set.bind(n.to_lower()))
			_update_cooldown(n.to_lower(), sk.cooldown_remaining, sk.cooldown_max)
	# Button click handling.
	skill_q.pressed.connect(_on_skill_button.bind("q"))
	skill_w.pressed.connect(_on_skill_button.bind("w"))
	skill_e.pressed.connect(_on_skill_button.bind("e"))
	skill_r.pressed.connect(_on_skill_button.bind("r"))


func _process(_delta: float) -> void:
	# Update cooldown overlays every frame.
	for key in _skills:
		var sk: Node = _skills[key]
		_update_cooldown(key, sk.cooldown_remaining, sk.cooldown_max)


func _on_hp_changed(new_hp: int, max_hp: int) -> void:
	hp_bar.max_value = max_hp
	hp_bar.value = new_hp
	hp_label.text = "%d / %d" % [new_hp, max_hp]


func _on_skill_cooldown_set(sk: Node, key: String) -> void:
	_update_cooldown(key, sk.cooldown_remaining, sk.cooldown_max)


func _update_cooldown(key: String, remaining: float, max: float) -> void:
	var btn: Button = _btn_for(key)
	if btn == null:
		return
	if remaining > 0.0 and max > 0.0:
		var t := int(ceil(remaining))
		btn.text = "[%s]\n%ds" % [key.to_upper(), t]
		btn.disabled = true
		btn.modulate = Color(0.5, 0.5, 0.5, 0.7)
	else:
		btn.text = "[%s]" % key.to_upper()
		btn.disabled = false
		btn.modulate = Color(1, 1, 1, 1)


func _on_skill_button(key: String) -> void:
	# The button just relays to the character's skill. The character's
	# _unhandled_input will ALSO fire — but skill.try_cast() is idempotent
	# and checks cooldown, so it is fine.
	if _player == null:
		return
	var sk: Node = _skills.get(key)
	if sk and sk.has_method("try_cast"):
		sk.try_cast(_player.global_position)


func _btn_for(key: String) -> Button:
	match key:
		"q": return skill_q
		"w": return skill_w
		"e": return skill_e
		"r": return skill_r
	return null
