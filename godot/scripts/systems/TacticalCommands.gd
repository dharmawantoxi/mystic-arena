# TacticalCommands.gd — FASE 17: port TacticalCommandManager pygame
# (tactical_commands.py, 1051 baris, 28 fungsi) untuk tim biru (pemain).
#
# Perintah: GATHER, PROTECT_TOWER, PROTECT_CASTLE, ATTACK_BOSS,
# ATTACK_DAMAGE_DEALER + mode HOLD (tahan-tombol) + auto-protect tiap
# 90 frame. Semua hitungan memakai FRAME (bukan detik): update() maju
# satu frame per panggilan, dipanggil tiap physics tick produksi (60 Hz)
# atau di-step manual oleh harness paritas.
#
# Akses state (paritas atribut `game` pygame -> Godot):
#   game.state            -> GameManager.state
#   game.heroes (biru)    -> GameManager.owned_heroes("blue")
#   game.ai.heroes (merah)-> GameManager.owned_heroes("red") (query live
#                            yang sama dipakai AIPlayer._red_heroes)
#   game.towers/minions   -> grup "towers" / "minions" (urutan tree =
#                            urutan kreasi, paritas list pygame)
#   game.active_boss      -> Main.active_boss (induk node ini)
#   game.blue/red_base    -> GameManager.blue/red_nexus
#   game.selected_hero    -> GameManager.selected_hero
#   game.mouse_x/y        -> mouse_override (harness) atau mouse viewport
#   game.wave_number      -> GameManager.wave_number
#
# Roll 20% auto-attack-boss lewat ParityRng.next() (produksi = randf,
# harness = script fixture). Satu-satunya situs RNG modul ini.
#
# Nama target (feedback/status/snapshot): menara memakai nama tipe dasar
# ("Archer" — paritas Tower.name pygame; BUKAN "Archer Tower" UI TowerDB
# maupun "Archer Lv1" display_name), castle memakai "Castle" (pygame
# Castle TIDAK punya .name; oracle mem-pin "Castle" supaya status
# deterministik), sisanya display_name.
#
# Visual gather-point + teks feedback + suara BELUM TERUJI (piksel/audio):
# yang di-parity-kan hanya state taktik. Suara ui_click/hero_skill tetap
# diputar produksi via AudioManager (no-op aman bila berkas tak ada).
extends Node

const HOLD_TAP_MAX_FRAMES := 20
const HOLD_RELEASE_TAIL := 30
const GATHER_PUSH_DELAY_FRAMES := 240
const COMMAND_DURATION := 600
const GATHER_POINT_DURATION := 150
const FEEDBACK_DURATION := 180
const AUTO_INTERVAL := 90
const COOLDOWN_MAX := 30
const SCREEN_W := 1280
const SCREEN_H := 720
const RED_BASE := Vector2(1180, 100)

const CMD_GATHER := "gather"
const CMD_PROTECT_TOWER := "protect_tower"
const CMD_PROTECT_CASTLE := "protect_castle"
const CMD_ATTACK_BOSS := "attack_boss"
const CMD_ATTACK_DEALER := "attack_damage_dealer"

var active_command = null
var command_timer := 0
var command_target = null
var command_origin = null
var feedback_timer := 0
var feedback_text := ""
var feedback_color := Color.WHITE

var cooldown := 0
var cooldown_max := COOLDOWN_MAX

var gather_point := Vector2.INF
var gather_point_timer := 0

var held_command = null
var hold_args: Array = []
var hold_kwargs := {}
var hold_follow_mouse := false
var hold_elapsed := 0
var hold_has_fired := false
var gather_push_fired := false
var auto_check_timer := 0

## Harness paritas: Vector2.INF = mouse viewport produksi.
var mouse_override := Vector2.INF
## Harness paritas FASE 18: saat true, setiap hold_start/hold_end produksi
## dicatat ke hold_trace (pola mouse_override — produksi tak terpengaruh).
## Entri hold_start = [nama, args, follow_mouse, hasil_bool]; hold_end =
## [nama]. Dikosongkan reset(). Oracle pygame merekam jejak yang sama lewat
## spy yang mem-wrap metode asli, lalu TacticalInputParityTest
## membandingkannya — itulah yang membuktikan PEMICU UI (hotkey + tombol
## panel) memanggil manajer dengan argumen yang tepat.
var hold_trace_enabled := false
var hold_trace: Array = []


func _physics_process(_delta: float) -> void:
	update()


## Kembalikan ke kondisi awal (match/arena baru, atau skenario harness).
func reset() -> void:
	active_command = null
	command_timer = 0
	command_target = null
	command_origin = null
	feedback_timer = 0
	feedback_text = ""
	feedback_color = Color.WHITE
	cooldown = 0
	gather_point = Vector2.INF
	gather_point_timer = 0
	held_command = null
	hold_args = []
	hold_kwargs = {}
	hold_follow_mouse = false
	hold_elapsed = 0
	hold_has_fired = false
	gather_push_fired = false
	auto_check_timer = 0
	mouse_override = Vector2.INF
	hold_trace.clear()


func _main():
	return get_parent()


func _mouse_pos() -> Vector2:
	if mouse_override != Vector2.INF:
		return mouse_override
	if get_viewport() != null:
		return get_viewport().get_mouse_position()
	return Vector2.ZERO


# ═══════════════════════════════════════
# CORE COMMAND ISSUERS
# ═══════════════════════════════════════

func can_issue() -> bool:
	return cooldown <= 0 and GameManager.state == "playing"


func _set_feedback(text: String, color: Color) -> void:
	feedback_text = text
	feedback_timer = FEEDBACK_DURATION
	feedback_color = color


func _get_alive_blue_heroes() -> Array:
	var out: Array = []
	for h in GameManager.owned_heroes("blue"):
		if is_instance_valid(h) and not bool(h.get("is_dead")):
			out.append(h)
	return out


func _get_alive_red_heroes() -> Array:
	var out: Array = []
	for h in GameManager.owned_heroes("red"):
		if is_instance_valid(h) and not bool(h.get("is_dead")):
			out.append(h)
	return out


func _clear_hero_retreat(heroes: Array) -> void:
	for h in heroes:
		h.set("is_retreating", false)
		h.set("destination_auto", false)


func _has_gather_point() -> bool:
	return gather_point != Vector2.INF


# ═══════════════════════════════════════
# HOLD
# ═══════════════════════════════════════

func _is_known_command(cmd_name: String) -> bool:
	return cmd_name == CMD_GATHER or cmd_name == CMD_PROTECT_TOWER \
		or cmd_name == CMD_PROTECT_CASTLE or cmd_name == CMD_ATTACK_BOSS \
		or cmd_name == CMD_ATTACK_DEALER


func hold_start(cmd_name: String, args: Array = [], follow_mouse: bool = false) -> bool:
	# Jejak harness dicatat di ENTRI metode (sebelum validasi) — cermin
	# spy oracle yang mem-wrap hold_start pygame: panggilan dengan nama
	# asing pun terekam (dan tetap ditolak).
	var _trace_args: Array = []
	for a in args:
		_trace_args.append(a)
	if hold_trace_enabled:
		hold_trace.append(["hold_start", cmd_name, _trace_args,
			bool(follow_mouse), null])
	if not _is_known_command(cmd_name):
		if hold_trace_enabled:
			hold_trace[hold_trace.size() - 1][4] = false
		return false
	if cmd_name == held_command and hold_elapsed > 0:
		# Key-repeat hold yang sama: masih menahan, jangan reset waktu
		# dan jangan terbitkan ulang bersuara (anti spam).
		if hold_trace_enabled:
			hold_trace[hold_trace.size() - 1][4] = true
		return true
	held_command = cmd_name
	hold_args = args.duplicate()
	hold_kwargs = {}
	hold_follow_mouse = bool(follow_mouse)
	hold_elapsed = 0
	hold_has_fired = false
	gather_push_fired = false
	var ok := _issue_held(true)
	if ok:
		hold_has_fired = true
	if hold_trace_enabled:
		hold_trace[hold_trace.size() - 1][4] = ok
	return ok


func hold_end(cmd_name = null) -> void:
	if hold_trace_enabled:
		hold_trace.append(["hold_end",
			str(cmd_name) if cmd_name != null else null])
	if held_command == null:
		return
	if cmd_name != null and str(cmd_name) != str(held_command):
		return
	var elapsed := hold_elapsed
	held_command = null
	hold_args = []
	hold_kwargs = {}
	hold_follow_mouse = false
	hold_elapsed = 0
	hold_has_fired = false
	if elapsed >= HOLD_TAP_MAX_FRAMES and command_timer > 0:
		command_timer = mini(command_timer, HOLD_RELEASE_TAIL)


func hold_active() -> bool:
	return held_command != null


func _issue_held(loud: bool) -> bool:
	var cmd_name = held_command
	if cmd_name == null:
		return false
	if str(cmd_name) == CMD_GATHER and not loud and gather_push_fired:
		var push_ok := _gather_hold_push()
		cooldown = cooldown_max
		return push_ok
	var args := hold_args.duplicate()
	if str(cmd_name) == CMD_GATHER and hold_follow_mouse:
		var m := _mouse_pos()
		if m.x >= 0.0 and m.x < float(SCREEN_W) \
				and m.y >= 0.0 and m.y < float(SCREEN_H):
			args = [m.x, m.y]
		else:
			args = []
	var ok := _call_issuer(str(cmd_name), args, not loud)
	if not ok:
		cooldown = maxi(cooldown, cooldown_max / 2)
	return ok


func _call_issuer(cmd_name: String, args: Array, silent: bool) -> bool:
	match cmd_name:
		CMD_GATHER:
			if args.size() >= 2:
				return command_gather(float(args[0]), float(args[1]), silent)
			return command_gather(INF, INF, silent)
		CMD_PROTECT_TOWER:
			var tower = null
			if args.size() >= 1 and args[0] != null:
				tower = args[0]
			return command_protect_tower(tower, silent)
		CMD_PROTECT_CASTLE:
			return command_protect_castle(silent)
		CMD_ATTACK_BOSS:
			return command_attack_boss(silent)
		CMD_ATTACK_DEALER:
			return command_attack_damage_dealer(silent)
	return false


func _gather_hold_push() -> bool:
	var heroes := _get_alive_blue_heroes()
	if heroes.is_empty() or not _has_gather_point():
		return false
	var target = _find_nearest_enemy_target(gather_point.x, gather_point.y)
	if target == null:
		var args := hold_args.duplicate()
		if args.is_empty():
			args = [gather_point.x, gather_point.y]
		if args.size() >= 2:
			return command_gather(float(args[0]), float(args[1]), true)
		return command_gather(INF, INF, true)
	for hero in heroes:
		hero.set("follow_target", target)
		hero.set("destination", Vector2.INF)
		hero.set("destination_auto", false)
		hero.set("is_retreating", false)
		hero.set("target", target)
	command_timer = COMMAND_DURATION
	gather_point_timer = GATHER_POINT_DURATION
	return true


func _try_gather_push() -> bool:
	var heroes := _get_alive_blue_heroes()
	if heroes.is_empty() or not _has_gather_point():
		return false
	var arrived := 0
	for h in heroes:
		if (h as Node2D).global_position.distance_to(gather_point) < 100.0:
			arrived += 1
	if float(arrived) < float(heroes.size()) * 0.6:
		return false
	var target = _find_nearest_enemy_target(gather_point.x, gather_point.y)
	if target == null:
		return false
	for hero in heroes:
		hero.set("follow_target", target)
		hero.set("destination", Vector2.INF)
	gather_push_fired = true
	_set_feedback("GATHER ATTACK! %d heroes push together!" % heroes.size(),
		Color(100.0 / 255.0, 220.0 / 255.0, 1.0))
	return true


# ───────────────────────────────────────
# GATHER
# ───────────────────────────────────────
func command_gather(gather_x: float = INF, gather_y: float = INF,
		silent: bool = false) -> bool:
	if not can_issue():
		return false
	var heroes := _get_alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", Color(1.0, 100.0 / 255.0, 100.0 / 255.0))
		return false
	var gx := gather_x
	var gy := gather_y
	if is_inf(gx) or is_inf(gy):
		var sel = GameManager.selected_hero
		if sel != null and is_instance_valid(sel) \
				and not bool(sel.get("is_dead")) and str(sel.get("team")) == "blue":
			gx = (sel as Node2D).global_position.x
			gy = (sel as Node2D).global_position.y
		elif heroes.size() >= 2:
			var ax := 0.0
			var ay := 0.0
			for h in heroes:
				ax += (h as Node2D).global_position.x
				ay += (h as Node2D).global_position.y
			ax /= float(heroes.size())
			ay /= float(heroes.size())
			var mid_mix := 0.35
			gx = ax * (1.0 - mid_mix) + RED_BASE.x * mid_mix
			gy = ay * (1.0 - mid_mix) + RED_BASE.y * mid_mix
			gx = clampf(gx, 200.0, 1080.0)
			gy = clampf(gy, 100.0, 620.0)
		else:
			gx = 640.0
			gy = 360.0
	active_command = CMD_GATHER
	command_timer = COMMAND_DURATION
	gather_point = Vector2(gx, gy)
	gather_point_timer = GATHER_POINT_DURATION
	cooldown = cooldown_max
	if not silent:
		gather_push_fired = false
	_clear_hero_retreat(heroes)
	var n := heroes.size()
	for i in range(n):
		var hero = heroes[i]
		var angle := (float(i) / float(maxi(1, n))) * TAU
		var spread := 35.0 + float(i % 3) * 15.0
		hero.call("move_to", gx + cos(angle) * spread,
			gy + sin(angle) * spread, false)
		hero.set("follow_target", null)
		hero.set("target", null)
	if not silent:
		AudioManager.play_sfx("ui_click", 0.8)
		_set_feedback("GATHER! %d heroes regrouping!" % n,
			Color(100.0 / 255.0, 220.0 / 255.0, 1.0))
		print("[TACTICAL] GATHER at (%d, %d) - %d heroes" % [int(gx), int(gy), n])
	return true


# ───────────────────────────────────────
# PROTECT TOWER
# ───────────────────────────────────────
func command_protect_tower(tower = null, silent: bool = false) -> bool:
	if not can_issue():
		return false
	var heroes := _get_alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", Color(1.0, 100.0 / 255.0, 100.0 / 255.0))
		return false
	var target_tower = tower
	if target_tower != null and not _is_alive_unit(target_tower):
		target_tower = null
	if target_tower == null:
		target_tower = _find_most_threatened_tower()
	if target_tower == null:
		var blue_towers := _blue_towers()
		if blue_towers.is_empty():
			if not silent:
				_set_feedback("No tower to protect!",
					Color(1.0, 150.0 / 255.0, 100.0 / 255.0))
			return false
		# Paritas sort pygame key=(-x, hp_ratio) STABIL: indeks kreasi
		# sebagai tiebreak (urutan grup == urutan kreasi).
		var decorated: Array = []
		for i in range(blue_towers.size()):
			decorated.append([blue_towers[i], i])
		decorated.sort_custom(func(a, b):
			return _tower_fallback_less(a, b))
		target_tower = decorated[0][0]
	active_command = CMD_PROTECT_TOWER
	command_timer = COMMAND_DURATION
	command_target = target_tower
	var tp := (target_tower as Node2D).global_position
	gather_point = Vector2(tp.x, tp.y)
	gather_point_timer = GATHER_POINT_DURATION
	cooldown = cooldown_max
	var protectors: Array
	if heroes.size() <= 3:
		protectors = heroes
	else:
		var by_dist: Array = []
		for i in range(heroes.size()):
			var d := (heroes[i] as Node2D).global_position.distance_to(tp)
			by_dist.append([heroes[i], d, i])
		by_dist.sort_custom(func(a, b):
			return _dist_less(a, b))
		var threat := _count_enemies_near(tp.x, tp.y, 250.0)
		var num_to_send := 3 if threat >= 3 else 2
		protectors = []
		for k in range(mini(num_to_send, by_dist.size())):
			protectors.append(by_dist[k][0])
	_clear_hero_retreat(protectors)
	var pn := protectors.size()
	for i in range(pn):
		var hero = protectors[i]
		var angle := (float(i) / float(pn)) * TAU if pn > 1 else 0.0
		var spread := 30.0 + float(i) * 10.0
		hero.call("move_to", tp.x + cos(angle) * spread,
			tp.y + sin(angle) * spread, false)
		hero.set("follow_target", null)
		hero.set("target", null)
	if not silent:
		AudioManager.play_sfx("ui_click", 0.8)
		_set_feedback("PROTECT TOWER! %d heroes defending %s!" % [pn, target_name(target_tower)],
			Color(100.0 / 255.0, 1.0, 100.0 / 255.0))
		print("[TACTICAL] PROTECT TOWER %s at (%d, %d) - %d heroes, threat=%d"
			% [target_name(target_tower), int(tp.x), int(tp.y), pn,
			_count_enemies_near(tp.x, tp.y, 250.0)])
	return true


func _tower_fallback_less(a: Array, b: Array) -> bool:
	var pa := (a[0] as Node2D).global_position
	var pb := (b[0] as Node2D).global_position
	if pa.x != pb.x:
		return pa.x > pb.x
	var ra := float(a[0].get("hp")) / maxf(1.0, float(a[0].get("max_hp")))
	var rb := float(b[0].get("hp")) / maxf(1.0, float(b[0].get("max_hp")))
	if ra != rb:
		return ra < rb
	return int(a[1]) < int(b[1])


func _dist_less(a: Array, b: Array) -> bool:
	if float(a[1]) != float(b[1]):
		return float(a[1]) < float(b[1])
	return int(a[2]) < int(b[2])


# ───────────────────────────────────────
# PROTECT CASTLE
# ───────────────────────────────────────
func command_protect_castle(silent: bool = false) -> bool:
	if not can_issue():
		return false
	var heroes := _get_alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", Color(1.0, 100.0 / 255.0, 100.0 / 255.0))
		return false
	var castle = GameManager.blue_nexus
	if castle == null or not _is_alive_unit(castle):
		if not silent:
			_set_feedback("Castle destroyed!", Color(1.0, 100.0 / 255.0, 100.0 / 255.0))
		return false
	active_command = CMD_PROTECT_CASTLE
	command_timer = COMMAND_DURATION
	command_target = castle
	var cp := (castle as Node2D).global_position
	gather_point = Vector2(cp.x, cp.y)
	gather_point_timer = GATHER_POINT_DURATION
	cooldown = cooldown_max
	_clear_hero_retreat(heroes)
	var n := heroes.size()
	for i in range(n):
		var hero = heroes[i]
		var angle := (float(i) / float(n)) * TAU
		var radius := 80.0 + float(i % 2) * 30.0
		var tx := clampf(cp.x + cos(angle) * radius, 50.0, 1230.0)
		var ty := clampf(cp.y + sin(angle) * radius, 50.0, 670.0)
		hero.call("move_to", tx, ty, false)
		hero.set("follow_target", null)
		hero.set("target", null)
	if not silent:
		AudioManager.play_sfx("ui_click", 0.8)
		_set_feedback("PROTECT CASTLE! %d heroes defending base!" % n,
			Color(1.0, 220.0 / 255.0, 50.0 / 255.0))
		print("[TACTICAL] PROTECT CASTLE at (%d, %d) - %d heroes" % [int(cp.x), int(cp.y), n])
	return true


# ───────────────────────────────────────
# ATTACK BOSS
# ───────────────────────────────────────
func command_attack_boss(silent: bool = false) -> bool:
	if not can_issue():
		return false
	var heroes := _get_alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", Color(1.0, 100.0 / 255.0, 100.0 / 255.0))
		return false
	var boss = _main().get("active_boss") if _main() != null else null
	if boss == null or not _is_alive_unit(boss):
		if not silent:
			_set_feedback("No boss active!", Color(1.0, 150.0 / 255.0, 100.0 / 255.0))
			print("[TACTICAL] ATTACK BOSS - No active boss found")
		return false
	active_command = CMD_ATTACK_BOSS
	command_timer = COMMAND_DURATION
	command_target = boss
	var bp := (boss as Node2D).global_position
	gather_point = Vector2(bp.x, bp.y)
	gather_point_timer = GATHER_POINT_DURATION
	cooldown = cooldown_max
	_clear_hero_retreat(heroes)
	_order_focus(heroes, boss)
	if not silent:
		AudioManager.play_sfx("hero_skill", 0.9)
		_set_feedback("ATTACK BOSS! All heroes attack %s!" % target_name(boss),
			Color(1.0, 100.0 / 255.0, 100.0 / 255.0))
		print("[TACTICAL] ATTACK BOSS %s at (%d, %d) - %d heroes"
			% [target_name(boss), int(bp.x), int(bp.y), heroes.size()])
	return true


# ───────────────────────────────────────
# ATTACK DAMAGE DEALER
# ───────────────────────────────────────
func _find_enemy_damage_dealer():
	var candidates := _get_alive_red_heroes()
	if candidates.is_empty():
		return null
	# Paritas max() Python: yang PERTAMA menang bila seri (ganti hanya
	# bila strikt lebih besar).
	var best = candidates[0]
	var best_dmg := float(best.get("damage_dealt"))
	for h in candidates:
		var dmg := float(h.get("damage_dealt"))
		if dmg > best_dmg:
			best = h
			best_dmg = dmg
	return best


func command_attack_damage_dealer(silent: bool = false) -> bool:
	if not can_issue():
		return false
	var heroes := _get_alive_blue_heroes()
	if heroes.is_empty():
		if not silent:
			_set_feedback("No heroes alive!", Color(1.0, 100.0 / 255.0, 100.0 / 255.0))
		return false
	var dealer = _find_enemy_damage_dealer()
	if dealer == null:
		if not silent:
			_set_feedback("No enemy heroes!", Color(1.0, 150.0 / 255.0, 100.0 / 255.0))
			print("[TACTICAL] ATTACK DAMAGE DEALER - no enemy hero")
		return false
	active_command = CMD_ATTACK_DEALER
	command_timer = COMMAND_DURATION
	command_target = dealer
	var dp := (dealer as Node2D).global_position
	gather_point = Vector2(dp.x, dp.y)
	gather_point_timer = GATHER_POINT_DURATION
	cooldown = cooldown_max
	_clear_hero_retreat(heroes)
	_order_focus(heroes, dealer)
	if not silent:
		AudioManager.play_sfx("hero_skill", 0.9)
		var dmg := int(float(dealer.get("damage_dealt")))
		_set_feedback("ATTACK DAMAGE DEALER! Focus %s (%d dmg)!" % [target_name(dealer), dmg],
			Color(1.0, 130.0 / 255.0, 1.0))
		print("[TACTICAL] ATTACK DAMAGE DEALER %s (%d dmg) at (%d, %d) - %d heroes"
			% [target_name(dealer), dmg, int(dp.x), int(dp.y), heroes.size()])
	return true


## Kunci fokus serang bersama (attack_boss & attack_dealer): follow +
## spread range*0.5+i*8. move_to MENGHAPUS follow_target (paritas
## Hero.move_to pygame) sehingga dipasang ulang sesudahnya.
func _order_focus(heroes: Array, foe) -> void:
	var fp := (foe as Node2D).global_position
	var n := heroes.size()
	for i in range(n):
		var hero = heroes[i]
		hero.set("follow_target", foe)
		hero.set("destination", Vector2.INF)
		hero.set("destination_auto", false)
		hero.set("target", foe)
		var angle := (float(i) / float(n)) * TAU
		var spread := float(hero.get("attack_range")) * 0.5 + float(i) * 8.0
		hero.call("move_to", fp.x + cos(angle) * spread,
			fp.y + sin(angle) * spread, false)
		hero.set("follow_target", foe)


# ═══════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════

func _is_alive_unit(unit) -> bool:
	if unit == null or not is_instance_valid(unit):
		return false
	return not bool(unit.get("is_dead"))


func _blue_towers() -> Array:
	var out: Array = []
	for t in get_tree().get_nodes_in_group("towers"):
		if is_instance_valid(t) and str(t.get("team")) == "blue" \
				and not bool(t.get("is_dead")):
			out.append(t)
	return out


func _find_most_threatened_tower():
	var blue_towers := _blue_towers()
	if blue_towers.is_empty():
		return null
	var scored: Array = []
	for i in range(blue_towers.size()):
		var tower = blue_towers[i]
		var tp := (tower as Node2D).global_position
		var enemies_near := _count_enemies_near(tp.x, tp.y, 220.0)
		var hp_ratio := float(tower.get("hp")) / maxf(1.0, float(tower.get("max_hp")))
		var threat_score := float(enemies_near) * 10.0 + (1.0 - hp_ratio) * 15.0
		if tp.x < 400.0:
			threat_score += 2.0
		scored.append([threat_score, tower, i])
	scored.sort_custom(func(a, b):
		return _threat_less(a, b))
	if float(scored[0][0]) == 0.0:
		var by_hp: Array = []
		for i in range(blue_towers.size()):
			var t = blue_towers[i]
			by_hp.append([t,
				float(t.get("hp")) / maxf(1.0, float(t.get("max_hp"))), i])
		by_hp.sort_custom(func(a, b):
			return _dist_less(a, b))
		return by_hp[0][0]
	return scored[0][1]


func _threat_less(a: Array, b: Array) -> bool:
	if float(a[0]) != float(b[0]):
		return float(a[0]) > float(b[0])
	return int(a[2]) < int(b[2])


func _count_enemies_near(x: float, y: float, radius: float) -> int:
	var count := 0
	var at := Vector2(x, y)
	for m in get_tree().get_nodes_in_group("minions"):
		if is_instance_valid(m) and str(m.get("team")) == "red" \
				and not bool(m.get("is_dead")):
			if (m as Node2D).global_position.distance_to(at) <= radius:
				count += 1
	for h in _get_alive_red_heroes():
		if (h as Node2D).global_position.distance_to(at) <= radius:
			count += 1
	var boss = _main().get("active_boss") if _main() != null else null
	if boss != null and _is_alive_unit(boss) and str(boss.get("team")) == "red":
		if (boss as Node2D).global_position.distance_to(at) <= radius:
			count += 2
	return count


func _find_nearest_enemy_target(x: float, y: float):
	var at := Vector2(x, y)
	var best = null
	var best_dist := 9999.0
	var boss = _main().get("active_boss") if _main() != null else null
	if boss != null and _is_alive_unit(boss):
		var d := (boss as Node2D).global_position.distance_to(at)
		if d < best_dist:
			best_dist = d
			best = boss
	for t in get_tree().get_nodes_in_group("towers"):
		if is_instance_valid(t) and str(t.get("team")) == "red" \
				and not bool(t.get("is_dead")):
			var d := (t as Node2D).global_position.distance_to(at)
			if d < best_dist:
				best_dist = d
				best = t
	for h in _get_alive_red_heroes():
		var d := (h as Node2D).global_position.distance_to(at)
		if d < best_dist:
			best_dist = d
			best = h
	if best == null:
		for m in get_tree().get_nodes_in_group("minions"):
			if is_instance_valid(m) and str(m.get("team")) == "red" \
					and not bool(m.get("is_dead")):
				var d := (m as Node2D).global_position.distance_to(at)
				if d < best_dist:
					best_dist = d
					best = m
	if best == null:
		var red_base = GameManager.red_nexus
		if red_base != null and _is_alive_unit(red_base):
			best = red_base
	return best


# ═══════════════════════════════════════
# UPDATE (satu frame)
# ═══════════════════════════════════════

func update() -> void:
	if cooldown > 0:
		cooldown -= 1
	if command_timer > 0:
		command_timer -= 1
		if command_timer <= 0:
			active_command = null
			command_target = null
	if gather_point_timer > 0:
		gather_point_timer -= 1
		if gather_point_timer <= 0:
			gather_point = Vector2.INF
	if feedback_timer > 0:
		feedback_timer -= 1

	if held_command != null and GameManager.state == "playing":
		hold_elapsed += 1
		if cooldown <= 0:
			var ok := _issue_held(false)
			if ok and not hold_has_fired:
				cooldown = 0
				_issue_held(true)
			if ok:
				hold_has_fired = true

	if str(active_command) == CMD_GATHER and _has_gather_point():
		if str(held_command) == CMD_GATHER:
			if not gather_push_fired \
					and hold_elapsed >= GATHER_PUSH_DELAY_FRAMES:
				_try_gather_push()
		elif command_timer == 300:
			_try_gather_push()

	if active_command == null and cooldown <= 0:
		auto_check_timer += 1
		if auto_check_timer >= AUTO_INTERVAL:
			auto_check_timer = 0
			_auto_evaluate_protect()


func _auto_evaluate_protect() -> void:
	if GameManager.state != "playing":
		return
	var castle = GameManager.blue_nexus
	if castle != null and _is_alive_unit(castle):
		var hp_ratio := float(castle.get("hp")) / maxf(1.0, float(castle.get("max_hp")))
		var cp := (castle as Node2D).global_position
		if hp_ratio < 0.4 and _count_enemies_near(cp.x, cp.y, 300.0) >= 2:
			command_protect_castle()
			return
	var threatened: Array = []
	var idx := 0
	for tower in _blue_towers():
		var tp := (tower as Node2D).global_position
		var hp_ratio := float(tower.get("hp")) / maxf(1.0, float(tower.get("max_hp")))
		var enemies_near := _count_enemies_near(tp.x, tp.y, 250.0)
		if (hp_ratio < 0.6 and enemies_near >= 2) or enemies_near >= 4:
			threatened.append([enemies_near, hp_ratio, tower, idx])
		idx += 1
	if not threatened.is_empty():
		threatened.sort_custom(func(a, b):
			return _auto_threat_less(a, b))
		command_protect_tower(threatened[0][2])
		return
	var boss = _main().get("active_boss") if _main() != null else null
	if boss != null and _is_alive_unit(boss):
		var boss_hp_ratio := float(boss.get("hp")) / maxf(1.0, float(boss.get("max_hp")))
		if boss_hp_ratio < 0.8 and GameManager.wave_number >= 11:
			if ParityRng.next() < 0.2:
				command_attack_boss()


func _auto_threat_less(a: Array, b: Array) -> bool:
	if int(a[0]) != int(b[0]):
		return int(a[0]) > int(b[0])
	if float(a[1]) != float(b[1]):
		return float(a[1]) < float(b[1])
	return int(a[3]) < int(b[3])


# ═══════════════════════════════════════
# NAMA / WARNA / STATUS
# ═══════════════════════════════════════

## Nama tampil target untuk feedback & status (paritas .name pygame).
## Dipakai juga harness untuk kolom "name" snapshot.
func target_name(unit) -> String:
	if unit == null or not is_instance_valid(unit):
		return ""
	if (unit as Node).is_in_group("nexus"):
		return "Castle"
	if (unit as Node).is_in_group("towers"):
		# Paritas Tower.name pygame (_entity.py:695-697): NAMA TIPE DASAR
		# ("Archer") — BUKAN nama UI TowerDB ("Archer Tower") maupun
		# display_name ("Archer Lv1").
		return str(unit.get("tower_type")).capitalize()
	if "display_name" in unit:
		return str(unit.get("display_name"))
	return (unit as Node).name


func _get_command_color() -> Color:
	match str(active_command):
		CMD_GATHER:
			return Color(100.0 / 255.0, 220.0 / 255.0, 1.0)
		CMD_PROTECT_TOWER:
			return Color(100.0 / 255.0, 1.0, 100.0 / 255.0)
		CMD_PROTECT_CASTLE:
			return Color(1.0, 220.0 / 255.0, 50.0 / 255.0)
		CMD_ATTACK_BOSS:
			return Color(1.0, 100.0 / 255.0, 100.0 / 255.0)
		CMD_ATTACK_DEALER:
			return Color(1.0, 130.0 / 255.0, 1.0)
	return Color(1.0, 220.0 / 255.0, 100.0 / 255.0)


func get_status_text() -> String:
	var hold_tag := " [HOLD]" if held_command != null else ""
	if active_command != null:
		var target_label := ""
		if command_target != null and is_instance_valid(command_target):
			target_label = target_name(command_target).left(15)
		return "%s %s (%ds)%s" % [str(active_command).to_upper(),
			target_label, command_timer / 60, hold_tag]
	if held_command != null:
		return "%s [HOLD] (menunggu syarat)" % str(held_command).to_upper()
	return "No tactical command"
