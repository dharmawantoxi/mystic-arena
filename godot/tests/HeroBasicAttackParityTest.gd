# HeroBasicAttackParityTest — paritas JALUR DAMAGE BASIC HERO vs oracle pygame.
#
# Fixture `match_parity.json["hero_basic_attack"]` (STRING JSON kompak)
# dihasilkan tools/test_godot_match_parity.py dengan menjalankan kode pygame
# ASLI: Hero._do_attack (melee/ranged: bonus item, crit buff int(x*2), crit
# item, lifesteal float vs int() saat spawn, cleave netral) DAN blok
# mitigasi take_damage tiap jenis target:
#   hero   = amp int(round) -> armor ITEM utk SEMUA damage non-'fire'
#            (live dari inventory + aura, dikikis shred, negatif = bonus)
#            -> block SETELAH armor (floor 0, amount milik defender,
#            aura guard menimpa tanpa roll) -> Bristleback 0.70/0.85
#            + reflect 'normal' kena armor penyerang; TANPA magic_resist.
#   minion = amp -> shred bonus (double-dip) -> armor-shred / MR.
#   boss   = amp -> shred bonus -> reduction - shred*0.06 (cap 0.60) / MR
#            -> resilience + anti-burst; blind hanya 'normal' bersource.
#   tower  = armor / MR sekolah saja (shield dinolkan oracle).
#   nexus  = tanpa mitigasi sekolah; shield int(x*(1-0.88)) truncation.
# + reflect thornmail int(dmg*0.85) 'magic', wind wall gate, blind di
#   PENYERANG, dan probe get_block (amount milik defender, bukan serangan).
#
# Tes ini memutar ulang skenario yang sama pada node Hero/Minion/Boss/Tower/
# Nexus ASLI + CombatSystem.apply_damage yang sebenarnya, lalu membandingkan
# HP semua unit tiap event + damage proyektil + stat awal (max_hp/hp0).
#
# Batas cakupan yang sengaja (lihat docs/GODOT_PARITY.md): skenario oracle
# bebas RNG — roll block item 55%, crit item, evasion item, windrun, dan
# shadow realm TIDAK teruji di sini (windrun/shadow realm = milestone
# tersendiri). Sanguine Thorn (rend crit) belum ada di item Godot.
#
# godot --headless --path godot res://tests/HeroBasicAttackParityTest.tscn --quit-after 120
# Require "[HeroBasicAttackParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const HeroScene = preload("res://scenes/hero/Hero.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const BossScene = preload("res://scenes/boss/Boss.tscn")
const TowerScene = preload("res://scenes/tower/Tower.tscn")
const NexusScene = preload("res://scenes/base/Nexus.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

# Posisi persis oracle (tools/test_godot_match_parity.py BA_*_XY).
const ATK_MELEE := Vector2(240.0, 100.0)
const ATK_RANGED := Vector2(200.0, 100.0)
const DEF_POS := Vector2(300.0, 100.0)
const EXTRA_XY := Vector2(340.0, 100.0)

const BIG_T := 10.0 ** 6

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done := false
var _error_messages: Array[String] = []
var _scenario_count := 0
var _event_checks := 0


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if _fixture == null or not _fixture.has("hero_basic_attack"):
		push_error("[HeroBasicAttackParityTest] fixture hero_basic_attack belum "
			+ "ada — jalankan tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	var ba: Dictionary = JSON.parse_string(str(_fixture["hero_basic_attack"]))
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	for sc in ba["scenarios"]:
		_replay(sc)
		if _failures > 40:
			_error_messages.append("[HeroBasicAttackParityTest] berhenti awal: "
				+ "terlalu banyak kegagalan")
			break
	_probe_get_block(ba["get_block_probe"])
	_finish()


# ══════════════════════════════════════════════════════════
#  PEMBANGUNAN UNIT (node asli + injeksi state harness)
# ══════════════════════════════════════════════════════════

func _make_unit(cfg: Dictionary, pos: Vector2, team: String):
	var kind := str(cfg.get("kind", "hero"))
	if kind == "hero":
		var h = HeroScene.instantiate()
		h.hero_type = str(cfg["hero_type"])
		h.team = team
		h.position = pos
		add_child(h) # _ready sinkron: stat + kit default + SkillBook facade
		h.set_physics_process(false)
		_inject_hero(h, cfg)
		return h
	if kind == "minion":
		var m = MinionScene.instantiate()
		m.minion_type = str(cfg["minion_type"])
		m.team = team
		m.lane = "mid"
		m.lane_path = PackedVector2Array()
		m.position = pos
		add_child(m)
		m.set_physics_process(false)
		_apply_debuff(m, cfg)
		return m
	if kind == "boss":
		var b = BossScene.instantiate()
		b.boss_type = str(cfg["boss_type"])
		b.team = team
		b.position = pos
		add_child(b)
		b.set_physics_process(false)
		_apply_debuff(b, cfg)
		return b
	if kind == "tower":
		var t = TowerScene.instantiate()
		t.team = team
		t.position = pos
		add_child(t)
		t.set_physics_process(false)
		t.shield = 0.0 # oracle menolkan shield menara (isolasi blok armor)
		return t
	if kind == "castle":
		var n = NexusScene.instantiate()
		n.team = team
		n.position = pos
		add_child(n)
		n.set_physics_process(false)
		if cfg.get("shield") != null:
			n.shield = float(cfg["shield"])
			n.shield_active = true
		return n
	_fail("unit kind tak dikenal: %s" % kind)
	return null


## Debuff defender non-hero (minion/boss) — mirror _ba_apply_debuff
## oracle: lewat API StatusEffects (apply_*), bukan set atribut mentah.
func _apply_debuff(unit, cfg: Dictionary) -> void:
	var deb: Dictionary = cfg.get("debuff", {})
	if deb.has("armor_shred"):
		unit.status.apply_armor_shred(float(deb["armor_shred"]), BIG_T)
	if deb.has("dmg_amp"):
		unit.status.apply_damage_amp(float(deb["dmg_amp"]), BIG_T)


## Injeksi state harness hero — urutan sama dengan oracle pygame:
## item (via buy_item asli) -> kit -> aura -> debuff -> blind -> thorn -> hp.
func _inject_hero(h, cfg: Dictionary) -> void:
	for item_id in cfg.get("items", []):
		_expect(h.buy_item(str(item_id)), "beli item %s utk %s" % [item_id, h.hero_type])
	for key in cfg.get("kit", {}):
		h.kit[key] = cfg["kit"][key]
	if cfg.has("aura"):
		for key in cfg["aura"]:
			h.items.set(key, float(cfg["aura"][key]))
	var deb: Dictionary = cfg.get("debuff", {})
	if deb.has("armor_shred"):
		h.status.apply_armor_shred(float(deb["armor_shred"]), BIG_T)
	if deb.has("dmg_amp"):
		h.status.apply_damage_amp(float(deb["dmg_amp"]), BIG_T)
	if cfg.get("blind") != null and float(cfg["blind"]) > 0.0:
		h.status.apply_blind(float(cfg["blind"]), BIG_T)
	if cfg.get("thorn") != null:
		h.items._active_timer["razor_carapace"] = float(cfg["thorn"])
	if cfg.get("hp_frac") != null:
		h.hp = h.max_hp * float(cfg["hp_frac"])


## Patch per-hit defender (mirror _ba_patch oracle).
func _patch_defender(dfn, patch: Dictionary) -> void:
	if dfn == null:
		return
	if dfn.get("items") != null and patch.has("aura"):
		for key in patch["aura"]:
			dfn.items.set(key, float(patch["aura"][key]))
	var deb: Dictionary = patch.get("debuff", {})
	if deb.has("armor_shred"):
		dfn.status.apply_armor_shred(float(deb["armor_shred"]), BIG_T)
	if deb.has("dmg_amp"):
		dfn.status.apply_damage_amp(float(deb["dmg_amp"]), BIG_T)
	for key in patch.get("kit", {}):
		dfn.kit[key] = patch["kit"][key]
	if patch.has("thorn") and dfn.get("items") != null:
		dfn.items._active_timer["razor_carapace"] = float(patch["thorn"])
	if patch.has("hp_frac"):
		dfn.hp = dfn.max_hp * float(patch["hp_frac"])


# ══════════════════════════════════════════════════════════
#  REPLAY SKENARIO
# ══════════════════════════════════════════════════════════

func _replay(sc: Dictionary) -> void:
	var name := str(sc["name"])
	var mode := str(sc["mode"])
	var units := {}
	var cfgs := {}
	for u in sc["units"]:
		var tag := str(u["tag"])
		cfgs[tag] = u["cfg"]
		var pos := DEF_POS
		if tag == "atk":
			pos = ATK_RANGED if mode == "ranged" else ATK_MELEE
		elif tag.begins_with("u"):
			var idx := int(tag.substr(1)) if tag.substr(1).is_valid_int() else 0
			pos = EXTRA_XY + Vector2(0.0, 20.0 * float(idx))
		units[tag] = _make_unit(u["cfg"], pos,
			"blue" if tag == "atk" else "red")

	# Stat awal identik (max_hp termasuk bonus item; hp0 setelah injeksi).
	for u in sc["units"]:
		var tag := str(u["tag"])
		var node = units[tag]
		_near(float(node.max_hp), float(u["max_hp"]),
			"%s/%s max_hp" % [name, tag])
		_near(float(node.hp), float(u["hp0"]), "%s/%s hp0" % [name, tag])

	var events: Array = sc["events"]
	var ei := 0
	if mode == "direct":
		var atk = units["atk"]
		var dfn = units["def"]
		for hit in sc["hits"]:
			if hit.has("set"):
				_patch_defender(dfn, hit["set"])
			var src = atk if str(hit.get("source", "attacker")) == "attacker" else null
			var sch := "" if hit.get("school") == null else str(hit["school"])
			dfn.take_damage(float(hit["damage"]), "blue",
				str(hit["dmg_type"]), src, sch)
			_compare_event(name, events[ei], units)
			ei += 1
	elif mode == "melee":
		var atk = units["atk"]
		atk.target = units["def"]
		var attacks := int(sc.get("attacks", 1))
		for i in attacks:
			atk.attack_timer = 0.0
			atk.try_attack()
			_compare_event(name, events[ei], units)
			ei += 1
	elif mode == "ranged":
		var atk = units["atk"]
		atk.target = units["def"]
		var attacks := int(sc.get("attacks", 1))
		for i in attacks:
			atk.attack_timer = 0.0
			atk.try_attack()
			# Spawn: lifesteal int(dmg*ls) dibayar di try_attack (paritas
			# pygame saat proyektil dilepas) + damage proyektil.
			var bullet = _find_bullet(atk)
			_expect(bullet != null, "%s: proyektil ter-spawn" % name)
			if bullet == null:
				return
			_expect(int(bullet.damage) == int(events[ei]["proj_damage"]),
				"%s: proj_damage %d != %d" % [name, int(bullet.damage),
					int(events[ei]["proj_damage"])])
			_expect(str(bullet.school) == str(events[ei]["proj_school"]),
				"%s: proj_school %s != %s" % [name, str(bullet.school),
					str(events[ei]["proj_school"])])
			_compare_event(name, events[ei], units)
			ei += 1
			bullet._on_hit() # hit persis jalur proyektil pygame
			_compare_event(name, events[ei], units)
			ei += 1

	_scenario_count += 1
	# free() sinkron (bukan queue_free): node lama tidak boleh mencemari
	# skenario berikutnya (pola HeroSkillParityTest/BossSmartAIParityTest).
	for tag in units:
		if is_instance_valid(units[tag]):
			units[tag].free()


## Peluru milik `atk` yang paling baru ter-spawn (satu per serangan pada
## skenario ini; peluru skenario lama sudah queue_free atau bersumber
## attacker lain).
func _find_bullet(atk):
	var found = null
	for b in get_tree().get_nodes_in_group("bullets"):
		if not is_instance_valid(b):
			continue
		if b.get("source") != atk:
			continue
		found = b
	return found


func _probe_get_block(rows: Array) -> void:
	for row in rows:
		var cfg: Dictionary = row["defender"]
		var h = HeroScene.instantiate()
		h.hero_type = str(cfg["hero_type"])
		h.team = "red"
		h.position = DEF_POS
		add_child(h)
		h.set_physics_process(false)
		for item_id in cfg.get("items", []):
			h.buy_item(str(item_id))
		var blk: Array = h.items.get_block()
		var expect: Array = row["expect"]
		_near(float(blk[0]), float(expect[0]),
			"get_block chance %s" % str(cfg["hero_type"]))
		_near(float(blk[1]), float(expect[1]),
			"get_block amount %s" % str(cfg["hero_type"]))
		h.free()


# ══════════════════════════════════════════════════════════
#  PERBANDINGAN
# ══════════════════════════════════════════════════════════

func _compare_event(sc_name: String, ev: Dictionary, units: Dictionary) -> void:
	_event_checks += 1
	var want: Dictionary = ev["hp"]
	if want.size() != units.size():
		_expect(false, "%s e%d: jumlah unit beda (oracle %d vs %d)"
			% [sc_name, int(ev["i"]), want.size(), units.size()])
		return
	for tag in want:
		if not units.has(tag):
			_expect(false, "%s e%d: unit %s tidak ada" % [sc_name, int(ev["i"]), tag])
			continue
		var got := float(units[tag].hp)
		_near(got, float(want[tag]),
			"%s e%d %s hp" % [sc_name, int(ev["i"]), tag], 0.51)


func _fail(message: String) -> void:
	_failures += 1
	var line := "[HeroBasicAttackParityTest] %s" % message
	_error_messages.append(line)
	if _error_messages.size() <= 60:
		push_error(line)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_failures += 1
		var line := "[HeroBasicAttackParityTest] %s: %.4f != %.4f" % [message, a, b]
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		var line := "[HeroBasicAttackParityTest] " + message
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _finish() -> void:
	if _done:
		return
	_done = true
	get_tree().paused = false
	GameManager.set_paused(false)
	GameManager.in_menu = true
	GameManager.state = "idle"
	if _failures == 0:
		print(("[HeroBasicAttackParityTest] PASS: %d skenario jalur damage "
			+ "basic hero (melee/ranged/direct × hero/minion/boss/tower/nexus)")
			% _scenario_count)
		print(("[HeroBasicAttackParityTest] PASS: %d event HP + %d stat/probe "
			+ "dibandingkan") % [_event_checks, _checks])
		print("[HeroBasicAttackParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[HeroBasicAttackParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[HeroBasicAttackParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
