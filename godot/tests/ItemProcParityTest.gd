# ItemProcParityTest — paritas ITEM TEMPUR vs oracle pygame (FASE 19).
#
# Fixture `match_parity.json["item_procs"]` (STRING JSON kompak) dihasilkan
# tools/test_godot_match_parity.py dengan menjalankan kode pygame ASLI
# (Hero._do_attack / take_damage / HeroItemInventory.update) dan
# random.random DI-MONKEYPATCH per situs roll combat — nilai roll
# ditentukan skenario, jadi hasilnya deterministik penuh. Cakupan yang
# dikunci:
#
#   • SOUL REND (Sanguine Thorn): auto-trigger lewat inv.update (silence +
#     amp 30% + PENANDAAN rend_target), serangan ke target bertanda crit
#     PASTI 1.5x TANPA roll dan MEN-DISKIP roll crit item (Dead Edge),
#     rend_cd menahan re-trigger; ikut vs defender BOSS.
#   • PROC ON-ATTACK: bash Abyss Breaker (roll 22%, damage NETRAL kena
#     armor, cd 140 menahan roll), Arc Chain Fenrir/Thunder (roll; dict
#     chain dari SLOT PERTAMA), Piercing Bash Sundering Cudgel (roll 28%,
#     magic, situs SETELAH chain), Frostbite (tanpa roll), Miasma (racun
#     tanpa roll + tick 30f) dan multishot Polycephaly (roll HANYA ranged,
#     int(damage×70%)), Empower Strike (charge 540 penuh sejak init —
#     serangan pertama TIDAK proc), Entangle vine_rod (root slow 1.0, cd
#     internal 540, slow korban ikut dikunci lewat flag slow_on).
#   • PROC ON-DAMAGE: Static Charge Thunder Coil — roll 20% saat PEMILIK
#     kena damage, static_cd menahan roll, zap berkala (quirk pygame:
#     static_tick berkurang 2x per frame -> zap efektif tiap 15 frame).
#   • ROLL BLIND BOSS (base_boss.take_damage): hanya damage_type 'normal'
#     bersource; 0.40 persis kena (strict); True Strike tanpa roll.
#
# Tes ini memutar ulang skenario pada node Hero/Boss/Minion ASLI +
# CombatSystem.apply_damage / ItemInventory yang sebenarnya. Roll
# direplay lewat hook ParityRng (produksi tetap randf() global). Frame
# pygame di-step manual lewat jalur produksi yang sama: status.tick() +
# items.tick() tiap unit (mirror urutan _tick_tower_debuffs ->
# inv.update di Hero.update pygame). Dibandingkan per event:
#   1. HP semua unit (+ damage/school proyektil saat spawn),
#   2. daftar nilai roll yang BENAR-BENAR dikonsumsi — jumlah, nilai,
#      urutan; roll yang hilang/bertambah/tertukar = gagal,
#   3. flag state internal: rend_on/rend_marked/rend_cd_on/static_on/
#      slow_on.
#
# godot --headless --path godot res://tests/ItemProcParityTest.tscn --quit-after 120
# Require "[ItemProcParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const HeroScene = preload("res://scenes/hero/Hero.tscn")
const BossScene = preload("res://scenes/boss/Boss.tscn")
const MinionScene = preload("res://scenes/minion/Minion.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

# Posisi persis oracle (tools/test_godot_match_parity.py BA_*_XY).
const ATK_MELEE := Vector2(240.0, 100.0)
const ATK_RANGED := Vector2(200.0, 100.0)
const DEF_POS := Vector2(300.0, 100.0)
const EXTRA_POS := Vector2(340.0, 100.0)

## 1 frame pygame @60 FPS -> detik Godot.
const FRAME := 1.0 / 60.0

## Durasi debuff harness "selamanya" (pola HeroRngGuardParityTest).
const BIG_T := 10.0 ** 6

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done := false
var _error_messages: Array[String] = []
var _scenario_count := 0
var _event_checks := 0
var _roll_checks := 0
var _flag_checks := 0
# DEBUG SEMENTARA: jejak decrement _miasma per (frame, unit).
var _dbg_trace: Array[String] = []


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if _fixture == null or not _fixture.has("item_procs"):
		push_error("[ItemProcParityTest] fixture item_procs belum ada — "
				+ "jalankan tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	var ip: Dictionary = JSON.parse_string(str(_fixture["item_procs"]))
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	for sc in ip["scenarios"]:
		await _replay(sc)
		if _failures > 40:
			_error_messages.append("[ItemProcParityTest] berhenti awal: "
				+ "terlalu banyak kegagalan")
			break
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
	if kind == "boss":
		var b = BossScene.instantiate()
		b.boss_type = str(cfg["boss_type"])
		b.team = team
		b.position = pos
		add_child(b)
		await get_tree().process_frame
		b.set_physics_process(false)
		return b
	if kind == "minion":
		var m = MinionScene.instantiate()
		m.minion_type = str(cfg["minion_type"])
		m.team = team
		m.lane = "mid"
		m.lane_path = PackedVector2Array()
		m.position = pos
		add_child(m)
		await get_tree().process_frame
		m.set_physics_process(false)
		return m
	_fail("unit kind tak dikenal: %s" % kind)
	return null


## Injeksi state harness hero — urutan sama dengan oracle pygame
## (_ba_inject_hero_state): item (via buy_item asli) -> kit -> aura ->
## items_state -> debuff -> blind -> hp.
func _inject_hero(h, cfg: Dictionary) -> void:
	for item_id in cfg.get("items", []):
		_expect(h.buy_item(str(item_id)), "beli item %s utk %s" % [item_id, h.hero_type])
	for key in cfg.get("kit", {}):
		h.kit[key] = cfg["kit"][key]
	if cfg.has("aura"):
		for key in cfg["aura"]:
			_set_inv_attr(h.items, str(key), float(cfg["aura"][key]))
	for key in cfg.get("items_state", {}):
		_set_inv_attr(h.items, str(key), float(cfg["items_state"][key]))
	var deb: Dictionary = cfg.get("debuff", {})
	if deb.has("armor_shred"):
		h.status.apply_armor_shred(float(deb["armor_shred"]), BIG_T)
	if deb.has("dmg_amp"):
		h.status.apply_damage_amp(float(deb["dmg_amp"]), BIG_T)
	if cfg.get("blind") != null and float(cfg["blind"]) > 0.0:
		h.status.apply_blind(float(cfg["blind"]), BIG_T)
	if cfg.get("hp_frac") != null:
		h.hp = h.max_hp * float(cfg["hp_frac"])


## Patch per-hit defender (mirror _ba_patch oracle).
func _patch_defender(dfn, patch: Dictionary) -> void:
	if dfn == null:
		return
	if dfn.get("items") != null and patch.has("aura"):
		for key in patch["aura"]:
			_set_inv_attr(dfn.items, str(key), float(patch["aura"][key]))
	var deb: Dictionary = patch.get("debuff", {})
	if deb.has("armor_shred"):
		dfn.status.apply_armor_shred(float(deb["armor_shred"]), BIG_T)
	if deb.has("dmg_amp"):
		dfn.status.apply_damage_amp(float(deb["dmg_amp"]), BIG_T)
	for key in patch.get("kit", {}):
		dfn.kit[key] = patch["kit"][key]
	if patch.has("hp_frac"):
		dfn.hp = dfn.max_hp * float(patch["hp_frac"])


## Attr inventory pygame bernama FRAME (static_timer/static_cd/static_tick,
## empower_charge); Godot menyimpannya per-item-id dalam DETIK. Pemetaan
## satu-tempat ini menghindari duplikasi state kedua di harness.
func _set_inv_attr(inv, key: String, frames: float) -> void:
	match key:
		"static_timer":
			inv._active_timer["thunder_coil"] = frames / 60.0
		"static_cd":
			inv._active_cd["thunder_coil"] = frames / 60.0
		"static_tick":
			inv._tick_cd["thunder_coil"] = frames / 60.0
		"empower_charge":
			inv._empower_charge = frames / 60.0
		_:
			inv.set(key, frames)


# ══════════════════════════════════════════════════════════
#  REPLAY SKENARIO
# ══════════════════════════════════════════════════════════

func _replay(sc: Dictionary) -> void:
	var name := str(sc["name"])
	var mode := str(sc["mode"])
	var units := {}
	var extra_i := 0
	for u in sc["units"]:
		var tag := str(u["tag"])
		var cfg: Dictionary = u["cfg"]
		var pos := DEF_POS
		if tag == "atk":
			pos = ATK_RANGED if mode == "ranged" else ATK_MELEE
		elif tag != "def":
			pos = EXTRA_POS + Vector2(0.0, 20.0 * float(extra_i))
			extra_i += 1
		var node = await _make_unit(cfg, pos,
			"blue" if tag == "atk" else "red")
		if node == null:
			return
		units[tag] = node

	# Stat awal identik (max_hp termasuk bonus item; hp0 setelah injeksi).
	for u in sc["units"]:
		var tag := str(u["tag"])
		var node = units[tag]
		_near(float(node.max_hp), float(u["max_hp"]),
			"%s/%s max_hp" % [name, tag])
		_near(float(node.hp), float(u["hp0"]), "%s/%s hp0" % [name, tag])

	var atk = units["atk"]
	var dfn = units["def"]
	atk.target = dfn
	# _MIASMA adalah global pygame — di-clear antar skenario oleh oracle;
	# di Godot static juga, clear dari salah satu inventory (mirror).
	for tag in units:
		var inv2 = units[tag].get("items")
		if inv2 != null:
			inv2._miasma.clear()

	var events: Array = sc["events"]
	var ei := 0
	if mode == "direct":
		for hit in sc["hits"]:
			if hit.has("set"):
				_patch_defender(dfn, hit["set"])
			_pre_updates(units, int(hit.get("pre_item_updates", 0)))
			var src = atk if str(hit.get("source", "attacker")) == "attacker" else null
			var sch := "" if hit.get("school") == null else str(hit["school"])
			ParityRng.begin(hit.get("rolls", []))
			dfn.take_damage(float(hit["damage"]), "blue",
				str(hit["dmg_type"]), src, sch)
			var consumed: Array = ParityRng.end()
			_compare_event(name, events[ei], units)
			_compare_flags(name, events[ei], atk, dfn)
			_compare_rolls(name, int(hit["damage"]), events[ei], consumed)
			ei += 1
	elif mode == "melee":
		for attack in sc["attacks"]:
			if attack.has("set"):
				_patch_defender(dfn, attack["set"])
			_dbg_trace = []
			_pre_updates(units, int(attack.get("pre_item_updates", 0)))
			ParityRng.begin(attack.get("rolls", []))
			atk.attack_timer = 0.0
			atk.try_attack()
			var consumed: Array = ParityRng.end()
			_compare_event(name, events[ei], units)
			_compare_flags(name, events[ei], atk, dfn)
			_compare_rolls(name, 0, events[ei], consumed)
			ei += 1
	elif mode == "ranged":
		for attack in sc["attacks"]:
			if attack.has("set"):
				_patch_defender(dfn, attack["set"])
			_dbg_trace = []
			_pre_updates(units, int(attack.get("pre_item_updates", 0)))
			ParityRng.begin(attack.get("rolls", []))
			atk.attack_timer = 0.0
			atk.try_attack()
			# Spawn: roll crit/proc sudah dikonsumsi di calc_damage +
			# on_attack_hit (try_attack), persis pygame _do_attack.
			var bullet = _find_bullet(atk)
			_expect(bullet != null, "%s: proyektil ter-spawn" % name)
			if bullet == null:
				ParityRng.end()
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
			var consumed: Array = ParityRng.end()
			_compare_event(name, events[ei], units)
			_compare_flags(name, events[ei], atk, dfn)
			_compare_rolls(name, 0, events[ei], consumed)
			ei += 1

	_scenario_count += 1
	# free() sinkron (bukan queue_free): node lama tidak boleh mencemari
	# skenario berikutnya (pola HeroRngGuardParityTest).
	for tag in units:
		if is_instance_valid(units[tag]):
			units[tag].free()


## Step frame produksi pygame: tick debuff dulu lalu inventory, per unit
## (mirror urutan Hero.update pygame _entity.py:3794 -> items.update
## 3801). Di sinilah Soul Rend terpicu, zap Static Charge menyala dari
## PEMILIK thunder_coil, cd proc kadaluarsa, dan racun Miasma bertick.
func _pre_updates(units: Dictionary, count: int) -> void:
	for _i in range(count):
		for tag in units:
			var u = units[tag]
			var st = u.get("status")
			if st != null and st.has_method("tick"):
				st.tick(FRAME)
			var inv = u.get("items")
			if inv != null:
				var had := inv._miasma.size() > 0
				var cd0 := -1.0
				if had:
					cd0 = float(inv._miasma[0][2])
				inv.tick(FRAME)
				# DEBUG SEMENTARA (diagnosa CI): siapa men-decrement.
				if had and inv._miasma.size() > 0:
					_dbg_trace.append("%s%d:%.4f" % [tag.substr(0, 1), _i,
						float(inv._miasma[0][2])])
				elif had:
					_dbg_trace.append("%s%d:EMPTY" % [tag.substr(0, 1), _i])
				elif cd0 >= 0.0:
					pass


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
		# DEBUG SEMENTARA (diagnosa CI): sertakan trace decrement miasma
		# per frame pada pesan gagal skenario miasma, agar terlihat di
		# anotasi CI siapa yang me-decrement dan kapan tick terjadi.
		if not is_equal_approx(got, float(want[tag])) and sc_name.contains("miasma_melee"):
			_expect(false, "%s e%d %s hp TRACE %s"
				% [sc_name, int(ev["i"]), tag, " | ".join(_dbg_trace)])
			return
		_near(got, float(want[tag]),
			"%s e%d %s hp" % [sc_name, int(ev["i"]), tag], 0.51)


## Flag state internal per event: penandaan Soul Rend + CD-nya, aura
## Static Charge, dan slow korban (root Entangle). Nilai oracle direkam
## _ip_state_flags pygame.
func _compare_flags(sc_name: String, ev: Dictionary, atk, dfn) -> void:
	_flag_checks += 1
	var inv_a = atk.get("items")
	var inv_d = dfn.get("items")
	var marked: bool = inv_a.rend_target != null \
			and is_instance_valid(inv_a.rend_target) \
			and inv_a.rend_target == dfn
	_flag(sc_name, ev, "rend_on", inv_a.active_running("sanguine_thorn"))
	_flag(sc_name, ev, "rend_marked", marked)
	_flag(sc_name, ev, "rend_cd_on",
		float(inv_a._active_cd.get("sanguine_thorn", 0.0)) > 0.0)
	_flag(sc_name, ev, "static_on",
		inv_d != null and inv_d.active_running("thunder_coil"))
	var st = dfn.get("status")
	_flag(sc_name, ev, "slow_on", st != null and float(st.slow_timer) > 0.0)


func _flag(sc_name: String, ev: Dictionary, key: String, got: bool) -> void:
	_checks += 1
	var want := bool(ev.get(key, false))
	if want != got:
		_failures += 1
		var line := "[ItemProcParityTest] %s e%d %s: %s != oracle %s" \
				% [sc_name, int(ev["i"]), key, got, want]
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


## Bandingkan roll yang dikonsumsi Godot dengan roll yang dikonsumsi
## oracle pygame pada event yang sama: JUMLAH, nilai, dan (karena queue
## FIFO) urutan. Selisih jumlah = ada roll yang hilang/bertambah di
## salah satu engine — kegagalan yang ingin ditangkap harness ini.
func _compare_rolls(sc_name: String, dmg: int, ev: Dictionary, consumed: Array) -> void:
	_roll_checks += 1
	var want: Array = ev.get("rolls", [])
	if want.size() != consumed.size():
		_expect(false, "%s e%d (dmg %d): jumlah roll terkonsumsi %d != oracle %d"
			% [sc_name, int(ev["i"]), dmg, consumed.size(), want.size()])
	for i in range(min(want.size(), consumed.size())):
		_near(float(consumed[i]), float(want[i]),
			"%s e%d roll[%d]" % [sc_name, int(ev["i"]), i], 0.000000001)


func _fail(message: String) -> void:
	_failures += 1
	var line := "[ItemProcParityTest] %s" % message
	_error_messages.append(line)
	if _error_messages.size() <= 60:
		push_error(line)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_failures += 1
		var line := "[ItemProcParityTest] %s: %.4f != %.4f" % [message, a, b]
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		var line := "[ItemProcParityTest] " + message
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
		print(("[ItemProcParityTest] PASS: %d skenario item tempur (Soul "
			+ "Rend / bash / chain / pierce / frostbite / miasma+multishot / "
			+ "empower / entangle / static charge / blind boss)")
			% _scenario_count)
		print(("[ItemProcParityTest] PASS: %d event HP + %d daftar roll + "
			+ "%d flag state dibandingkan (%d nilai roll)")
			% [_event_checks, _roll_checks, _flag_checks, _checks])
		print("[ItemProcParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[ItemProcParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[ItemProcParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
