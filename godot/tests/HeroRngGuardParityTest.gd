# HeroRngGuardParityTest — paritas ROLL RNG guard hero vs oracle pygame.
#
# Fixture `match_parity.json["hero_rng_guards"]` (STRING JSON kompak)
# dihasilkan tools/test_godot_match_parity.py dengan menjalankan kode pygame
# ASLI (Hero.take_damage / Hero._do_attack / hero_items.roll_crit) dan
# random.random DI-MONKEYPATCH per situs roll combat — nilai roll ditentukan
# skenario, jadi hasilnya deterministik penuh. Cakupan yang dikunci:
#
#   • WINDRUN (Sylara W): roll < 0.75 meleset utk hit fisik
#     (normal/projectile, sekolah bukan magic — termasuk netral tanpa
#     source); sihir/fire tidak me-roll; 0.75 persis TIDAK meleset.
#   • SHADOW REALM (Zephyr W): kebal total SEMUA damage > 0 tanpa roll,
#     dipotong paling awal — bahkan sebelum windrun/wall/veil.
#   • URUTAN GUARD: shadow → windrun (roll) → wind wall → Tempest Veil →
#     evasion item; urutan roll terkunci lewat jumlah konsumsi.
#   • ROLL ITEM: block Scarlet Bulwark 55% (setelah armor, non-fire,
#     floor 0), crit Dead Edge 25% (di calc_damage, SEBELUM mitigasi
#     target; crit buff kit men-diskip roll), evasion Monarch Wings 28%,
#     blind < 1.0 di penyerang (max(ev, blind), True Strike menembus),
#     roll crit ranged saat spawn lalu roll block saat mendarat, dan
#     windrun pada reflect Bristleback (nested take_damage).
#
# Tes ini memutar ulang skenario yang sama pada node Hero ASLI +
# CombatSystem.apply_damage / ItemInventory.roll_crit yang sebenarnya.
# Roll direplay lewat hook ParityRng (CombatSystem/ItemInventory memakai
# ParityRng.next(); produksi tetap randf() global). Dibandingkan:
#   1. HP semua unit tiap event (+ damage/school proyektil saat spawn),
#   2. daftar nilai roll yang BENAR-BENAR dikonsumsi per event — jumlah,
#      nilai, dan urutan; roll yang hilang/bertambah/tertukar = gagal.
#
# Yang tetap TERBUKA (lihat docs/GODOT_PARITY.md): blind boss (pygame-nya
# di bosses/base_boss.py, roll tetap randf()), proc item on-attack/
# on-damage (bash/chain/frostbite/miasma/empower/entangle/static charge),
# rend crit Sanguine Thorn (belum ada di item Godot).
#
# godot --headless --path godot res://tests/HeroRngGuardParityTest.tscn --quit-after 120
# Require "[HeroRngGuardParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends Node

const HeroScene = preload("res://scenes/hero/Hero.tscn")
const FIXTURE := "res://tests/fixtures/match_parity.json"

# Posisi persis oracle (tools/test_godot_match_parity.py BA_*_XY).
const ATK_MELEE := Vector2(240.0, 100.0)
const ATK_RANGED := Vector2(200.0, 100.0)
const DEF_POS := Vector2(300.0, 100.0)

const BIG_T := 10.0 ** 6

var _fixture: Dictionary = {}
var _failures: int = 0
var _checks: int = 0
var _done := false
var _error_messages: Array[String] = []
var _scenario_count := 0
var _event_checks := 0
var _roll_checks := 0


func _ready() -> void:
	_boot.call_deferred()


func _boot() -> void:
	_fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	if _fixture == null or not _fixture.has("hero_rng_guards"):
		push_error("[HeroRngGuardParityTest] fixture hero_rng_guards belum "
			+ "ada — jalankan tools/test_godot_match_parity.py --write-fixture")
		_failures += 1
		_finish()
		return
	var rg: Dictionary = JSON.parse_string(str(_fixture["hero_rng_guards"]))
	GameManager.in_menu = true
	GameManager.state = "idle"
	GameManager.set_paused(false)
	for sc in rg["scenarios"]:
		_replay(sc)
		if _failures > 40:
			_error_messages.append("[HeroRngGuardParityTest] berhenti awal: "
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
	_fail("unit kind tak dikenal: %s" % kind)
	return null


## Injeksi state harness hero — urutan sama dengan oracle pygame
## (_ba_inject_hero_state): item (via buy_item asli) -> kit -> aura ->
## debuff -> blind -> thorn -> veil -> hp.
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
	if cfg.get("veil") != null and float(cfg["veil"]) > 0.0:
		# Tempest Veil (tempest_vane): oracle menyetel items.veil_timer;
		# Godot menyimpan timer aktif item dalam detik di _active_timer
		# (is_veiled() = active_running). Nilai > 0 cukup — harness tidak
		# men-tick timer (physics process dimatikan).
		h.items._active_timer["tempest_vane"] = float(cfg["veil"])
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
	if patch.has("veil") and dfn.get("items") != null:
		# 0 = matikan veil (paritas veil_timer = 0 pygame).
		dfn.items._active_timer["tempest_vane"] = float(patch["veil"])
	if patch.has("hp_frac"):
		dfn.hp = dfn.max_hp * float(patch["hp_frac"])


# ══════════════════════════════════════════════════════════
#  REPLAY SKENARIO
# ══════════════════════════════════════════════════════════

func _replay(sc: Dictionary) -> void:
	var name := str(sc["name"])
	var mode := str(sc["mode"])
	var units := {}
	for u in sc["units"]:
		var tag := str(u["tag"])
		var pos := DEF_POS
		if tag == "atk":
			pos = ATK_RANGED if mode == "ranged" else ATK_MELEE
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
			ParityRng.begin(hit.get("rolls", []))
			dfn.take_damage(float(hit["damage"]), "blue",
				str(hit["dmg_type"]), src, sch)
			var consumed: Array = ParityRng.end()
			_compare_rolls(name, int(hit["damage"]), events[ei], consumed)
			_compare_event(name, events[ei], units)
			ei += 1
	elif mode == "melee":
		var atk = units["atk"]
		atk.target = units["def"]
		for attack in sc["attacks"]:
			ParityRng.begin(attack.get("rolls", []))
			atk.attack_timer = 0.0
			atk.try_attack()
			var consumed: Array = ParityRng.end()
			_compare_rolls(name, 0, events[ei], consumed)
			_compare_event(name, events[ei], units)
			ei += 1
	elif mode == "ranged":
		var atk = units["atk"]
		atk.target = units["def"]
		for attack in sc["attacks"]:
			ParityRng.begin(attack.get("rolls", []))
			atk.attack_timer = 0.0
			atk.try_attack()
			# Spawn: roll crit sudah dikonsumsi di calc_damage (try_attack).
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
			_compare_rolls(name, 0, events[ei], consumed)
			_compare_event(name, events[ei], units)
			ei += 1

	_scenario_count += 1
	# free() sinkron (bukan queue_free): node lama tidak boleh mencemari
	# skenario berikutnya (pola HeroBasicAttackParityTest).
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
	var line := "[HeroRngGuardParityTest] %s" % message
	_error_messages.append(line)
	if _error_messages.size() <= 60:
		push_error(line)


func _near(a: float, b: float, message: String, eps: float = 0.02) -> void:
	_checks += 1
	if absf(a - b) > eps:
		_failures += 1
		var line := "[HeroRngGuardParityTest] %s: %.4f != %.4f" % [message, a, b]
		_error_messages.append(line)
		if _error_messages.size() <= 60:
			push_error(line)


func _expect(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		var line := "[HeroRngGuardParityTest] " + message
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
		print(("[HeroRngGuardParityTest] PASS: %d skenario guard RNG hero "
			+ "(windrun 75%% / shadow realm / block / crit / evasion / blind)")
			% _scenario_count)
		print(("[HeroRngGuardParityTest] PASS: %d event HP + %d daftar roll "
			+ "dibandingkan (%d nilai roll)") % [_event_checks, _roll_checks, _checks])
		print("[HeroRngGuardParityTest] PASS")
	else:
		for msg in _error_messages:
			print(msg)
		push_error("[HeroRngGuardParityTest] %d failures dari %d checks"
			% [_failures, _checks])
		print("[HeroRngGuardParityTest] FAIL: %d failures dari %d checks"
			% [_failures, _checks])
	get_tree().quit(0 if _failures == 0 else 1)
