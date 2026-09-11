# EntityPyParityTest — sisa celah `_entity.py` yang belum dikunci harness lain.
#
# Bukan replay fixture pygame: konstanta perilaku 1:1 yang baru diport.
#   1. credit_hero_damage: source.damage_dealt += int(dealt) SETELAH HP
#      (bukan shield); kit_hit TIDAK menambah lagi.
#   2. Archer L5=2 / L6=3 peluru (pad target sama); double_shot hanya L<5.
#   3. Hero.try_attack tidak menyalakan GameManager._hit_stop_active.
#   4. Papan nama = display_name (bukan "LvN"); SkillProjectile zephyr/
#      morgath/ancient_apparition punya kind khusus.
#
# godot --headless --path godot res://tests/EntityPyParityTest.tscn --quit-after 60
# Require "[EntityPyParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const SkillProjectileScript = preload("res://scenes/fx/SkillProjectile.gd")

var _failures: int = 0
var _checks: int = 0
var _done := false
var _error_messages: Array[String] = []
var _prev_dispatch: bool = true


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	_prev_dispatch = CombatSystem.death_dispatch_enabled
	CombatSystem.death_dispatch_enabled = false
	_test_credit()
	_test_archer_volley()
	_test_hit_stop()
	_test_name_and_proj_kind()
	_finish()


func _make_hero(pos: Vector2):
	var h = HeroScene.instantiate()
	h.hero_type = "kaizen"
	h.team = "blue"
	h.position = pos
	add_child(h)
	h.set_physics_process(false)
	h.damage_dealt = 0.0
	return h


func _make_minion(pos: Vector2, team: String = "red"):
	var m = MinionScene.instantiate()
	m.minion_type = "goblin"
	m.team = team
	m.lane = "mid"
	m.lane_path = PackedVector2Array()
	m.position = pos
	add_child(m)
	m.set_physics_process(false)
	m.set_process(false)
	m.max_hp = 8000.0
	m.hp = 8000.0
	m.armor = 0.0
	return m


func _test_credit() -> void:
	var h = _make_hero(Vector2(200, 120))
	var m = _make_minion(Vector2(260, 120))
	h.damage_dealt = 0.0
	var hp0 := float(m.hp)
	var dealt := CombatSystem.apply_damage(m, 10.9, "blue", "normal", h, "")
	_expect(dealt > 0.0, "apply_damage 10.9 harus mendarat")
	_near(h.damage_dealt, float(int(dealt)), "credit = int(dealt)")
	_near(m.hp, hp0 - dealt, "HP berkurang sebesar dealt")
	# kit_hit tidak double-count
	h.damage_dealt = 0.0
	hp0 = float(m.hp)
	h.kit_hit(m, 25.0, "blue", h, "")
	var drop := hp0 - float(m.hp)
	_near(h.damage_dealt, float(int(drop)), "kit_hit kredit sekali (int)")
	_expect(h.damage_dealt < drop + 0.51, "kit_hit tidak 2x dealt")
	# source=null -> hero tidak ter-kredit
	h.damage_dealt = 0.0
	h.kit_hit(m, 12.0, "blue", null, "")
	_near(h.damage_dealt, 0.0, "source=null tidak kredit")
	h.free()
	m.free()


func _test_archer_volley() -> void:
	var t = TowerScene.instantiate()
	t.team = "blue"
	t.tower_type = "archer"
	t.position = Vector2(400, 200)
	add_child(t)
	t.set_physics_process(false)
	var m1 = _make_minion(Vector2(460, 200))
	var m2 = _make_minion(Vector2(470, 220))
	t.target = m1
	t.angle = 0.0
	# L5: 2 peluru (1 target → pad)
	t.level = 5
	t._apply_level_stats()
	t.double_shot = false
	_clear_bullets()
	t._shoot(CombatSystem)
	_expect(_bullet_count() == 2, "archer L5 = 2 peluru (got %d)" % _bullet_count())
	# L6: 3 peluru, double_shot JSON tidak menambah ke-4
	t.level = 6
	t._apply_level_stats()
	_clear_bullets()
	t._shoot(CombatSystem)
	_expect(_bullet_count() == 3, "archer L6 = 3 peluru (got %d)" % _bullet_count())
	# L4 + double_shot + 2 musuh: 2 peluru
	t.level = 4
	t._apply_level_stats()
	t.double_shot = true
	_clear_bullets()
	t._shoot(CombatSystem)
	_expect(_bullet_count() == 2, "archer L4 double_shot = 2 peluru (got %d)" % _bullet_count())
	# L4 tanpa double_shot: 1
	t.double_shot = false
	_clear_bullets()
	t._shoot(CombatSystem)
	_expect(_bullet_count() == 1, "archer L4 = 1 peluru (got %d)" % _bullet_count())
	_clear_bullets()
	t.free()
	m1.free()
	m2.free()


func _test_hit_stop() -> void:
	var h = _make_hero(Vector2(200, 300))
	var m = _make_minion(Vector2(240, 300))
	h.target = m
	h.attack_timer = 0.0
	GameManager._hit_stop_active = false
	h.try_attack()
	_expect(not GameManager._hit_stop_active,
		"try_attack tidak menyalakan hit-stop")
	h.free()
	m.free()


func _test_name_and_proj_kind() -> void:
	var h = _make_hero(Vector2(80, 80))
	h.level = 3
	h.update_ui()
	if h.name_label:
		_expect(h.name_label.text == h.display_name,
			"name_label = display_name (bukan LvN): '%s'" % h.name_label.text)
		_expect(not ("Lv" in h.name_label.text), "name_label tanpa Lv")
	var m = _make_minion(Vector2(120, 80))
	var p = SkillProjectileScript.new()
	p.setup(m, "zephyr", h)
	_expect(str(p._kind) == "bolt", "zephyr kind=bolt (got %s)" % str(p._kind))
	p.setup(m, "morgath", h)
	_expect(str(p._kind) == "lightning", "morgath kind=lightning")
	p.setup(m, "ancient_apparition", h)
	_expect(str(p._kind) == "ice", "aa kind=ice")
	p.free()
	h.free()
	m.free()


func _bullet_count() -> int:
	var n := 0
	if get_tree() == null:
		return 0
	for b in get_tree().get_nodes_in_group("bullets"):
		if is_instance_valid(b):
			n += 1
	return n


func _clear_bullets() -> void:
	if get_tree() == null:
		return
	for b in get_tree().get_nodes_in_group("bullets"):
		if is_instance_valid(b):
			b.free()


func _fail(message: String) -> void:
	_failures += 1
	var line := "[EntityPyParityTest] %s" % message
	_error_messages.append(line)
	if _error_messages.size() <= 40:
		push_error(line)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_fail("%s: %.4f != %.4f" % [message, a, b])


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_fail(message)


func _finish() -> void:
	if _done:
		return
	_done = true
	CombatSystem.death_dispatch_enabled = _prev_dispatch
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print("[EntityPyParityTest] PASS: %d cek credit/archer/hit-stop/visual" % _checks)
		print("[EntityPyParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[EntityPyParityTest] %d failures dari %d checks" % [_failures, _checks])
		print("[EntityPyParityTest] FAIL: %d failures dari %d checks" % [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
