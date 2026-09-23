# L33 — TACTICAL COMMANDS FULL (G/T/C/B/D) — SNIPPET
# ============================================================
# Dari stub print() di L31 → jadi perintah gerak hero beneran.
# 5 tombol di panel kanan + hotkey G T C B D + klik panel.
#
# A) SidePanel.gd — ganti _issue_tactical stub → switch 5 aksi
# B) Main.gd — tambah 5 func tactical_* + helper + hotkey
# Urutan: B dulu (Main punya fungsi), baru A (panel manggil).
# Test: klik GATHER / tekan G → hero lari ke base biru, dst.

# ═══════════════════════════════════════════
# B — TAMBAH DI Main.gd (di bawah _on_nexus_destroyed, di atas toggle_pause)
# ═══════════════════════════════════════════
# --- TACTICAL COMMANDS (L33) ---
const BOSS_POS := Vector2(640, 360) # tengah sungai, spot Roshan

func tactical_gather() -> void:
	if hero == null or not hero.is_alive():
		print("[Tactical] GATHER gagal — hero gugur/belum spawn.")
		return
	hero.move_to(Vector2(250, 580))
	Sound.play("move")
	print("[Tactical] GATHER → hero kumpul di base (250,580)")

func tactical_protect_tower() -> void:
	if hero == null or not hero.is_alive():
		return
	var t := _nearest_blue_tower()
	if t != null:
		hero.move_to(t.position)
		print("[Tactical] PROTECT TOWER → %s di (%d,%d)" % [t.tower_name, int(t.position.x), int(t.position.y)])
	else:
		# belum ada tower biru → jaga slot biru terdekat (mid lane slot biru pertama)
		var p := _nearest_blue_slot_pos()
		hero.move_to(p)
		print("[Tactical] PROTECT TOWER → slot biru (%d,%d) (belum ada tower)" % [int(p.x), int(p.y)])
	Sound.play("move")

func tactical_protect_castle() -> void:
	if hero == null or not hero.is_alive():
		return
	hero.move_to(BASE_BLUE)
	Sound.play("move")
	print("[Tactical] PROTECT CASTLE → %s" % str(BASE_BLUE))

func tactical_attack_boss() -> void:
	if hero == null or not hero.is_alive():
		return
	hero.move_to(BOSS_POS)
	Sound.play("move")
	print("[Tactical] ATTACK BOSS → tengah sungai %s" % str(BOSS_POS))

func tactical_attack_dd() -> void:
	if hero == null or not hero.is_alive():
		return
	var target = _nearest_enemy_for_dd()
	if target != null:
		hero.move_to(target.position)
		print("[Tactical] ATTACK DD → kejar %s (%s) di (%d,%d)" % [str(target.name if "name" in target else target.tower_name if "tower_name" in target else "musuh"), str(target.team), int(target.position.x), int(target.position.y)])
	else:
		# fallback → nexus merah
		hero.move_to(BASE_RED)
		print("[Tactical] ATTACK DD → fallback nexus merah")
	Sound.play("move")

func _nearest_blue_tower() -> TowerUnit:
	var best = null
	var best_d := 999999.0
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t == null or t.team != "blue" or not t.is_alive():
			continue
		var d := hero.position.distance_to(t.position) if hero != null else 0.0
		if d < best_d:
			best = t
			best_d = d
	return best

func _nearest_blue_slot_pos() -> Vector2:
	var best := BASE_BLUE
	var best_d := 999999.0
	for s in slots:
		if str(s["team"]) != "blue":
			continue
		var p: Vector2 = s["pos"]
		var d := hero.position.distance_to(p) if hero != null else p.distance_to(BASE_BLUE)
		if d < best_d:
			best = p
			best_d = d
	return best

func _nearest_enemy_for_dd():
	# prioritas: hero musuh (kalau ada) → minion merah → tower merah → nexus merah
	var best = null
	var best_d := 999999.0
	for n in get_tree().get_nodes_in_group("heroes"):
		var h := n as HeroUnit
		if h == null or h.team == "blue" or not h.is_alive():
			continue
		var d := hero.position.distance_to(h.position)
		if d < best_d:
			best = h
			best_d = d
	if best != null:
		return best
	for n in get_tree().get_nodes_in_group("minions"):
		var m := n as MinionUnit
		if m == null or m.team == "blue" or not m.is_alive():
			continue
		var d := hero.position.distance_to(m.position)
		if d < best_d:
			best = m
			best_d = d
	if best != null:
		return best
	for n in get_tree().get_nodes_in_group("towers"):
		var t := n as TowerUnit
		if t == null or t.team == "blue" or not t.is_alive():
			continue
		var d := hero.position.distance_to(t.position)
		if d < best_d:
			best = t
			best_d = d
	for n in get_tree().get_nodes_in_group("nexus"):
		var nx := n as NexusUnit
		if nx == null or nx.team == "blue" or not nx.is_alive():
			continue
		var d := hero.position.distance_to(nx.position)
		if d < best_d:
			best = nx
			best_d = d
	return best
# --- END TACTICAL ---

# dan di _unhandled_input, di DALAM if k.pressed and not k.echo (setelah ESC, sebelum tutup blok), TAMBAHKAN:
#			if k.keycode == KEY_G:
#				tactical_gather()
#				return
#			if k.keycode == KEY_T:
#				tactical_protect_tower()
#				return
#			if k.keycode == KEY_C:
#				tactical_protect_castle()
#				return
#			if k.keycode == KEY_B:
#				tactical_attack_boss()
#				return
#			if k.keycode == KEY_D:
#				tactical_attack_dd()
#				return

# ═══════════════════════════════════════════
# A — GANTI DI scripts/SidePanel.gd
# ═══════════════════════════════════════════
# HAPUS:
# func _issue_tactical(action: String) -> void:
#	_feedback = "CMD: " + action.to_upper()
#	...
#	_main.hero.move_to(Vector2(250, 580))
#
# GANTI:
# func _issue_tactical(action: String) -> void:
#	match action:
#		"gather": _main.tactical_gather()
#		"protect_tower": _main.tactical_protect_tower()
#		"protect_castle": _main.tactical_protect_castle()
#		"attack_boss": _main.tactical_attack_boss()
#		"attack_dd": _main.tactical_attack_dd()
#		_: print("[SidePanel] unknown tactical %s" % action)
#	_feedback = "CMD: " + action.to_upper()
#	_feedback_t = 2.0

# CARA PASANG:
# 1. Main.gd → Ctrl+F "_on_nexus_destroyed" → di bawah func itu, paste blok B (sampai return best)
# 2. Main.gd → Ctrl+F "cast_hero_skill(3)" → di bawahnya paste 5x if KEY_G/B/C/T/D
# 3. SidePanel.gd → Ctrl+F "_issue_tactical" → ganti full func jadi match di atas
# 4. Save All → F5 → klik/G/T/C/B/D harus gerakkan hero sesuai print
