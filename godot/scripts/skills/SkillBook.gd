# SkillBook.gd — port hero_skills/_bundle.py (BaseSkill + 6 hero starter).
#
# pygame: tiap hero punya kelas Skill sendiri (KaizenSkills, GrimjawSkills, ...)
# dengan init_state / update_timers / cast_q..cast_r dan cooldown dalam FRAME:
#   Q = HERO_TYPES[hero]["skill_cooldown"]  (Kaizen 300, Grimjaw 420, Sylara 360, ...)
#   W = 240 frame (4 s) · E = 420 frame (7 s) · R = 900 frame (15 s)   [_entity.py 3444-3449]
# Di sini semua durasi DETIK, dan keenam hero didefinisikan lewat tabel efek
# (bukan 6 kelas terpisah) supaya hero ke-217+ tetap punya skill generik.
#
# Efek yang BELUM diport: proyektil skill terpisah (_spawn_skill_projectile —
# di Godot damage-nya instan + FX partikel), clone visual Bedlam, dan totem
# visual Healing Ward (logika heal-nya jalan, gambarnya menyusul).
extends RefCounted

const FPS := 60.0

# ── Cooldown universal (paritas _entity.Hero 3444-3449) ──
const W_CD := 240.0 / FPS   # 4 s
const E_CD := 420.0 / FPS   # 7 s
const R_CD := 900.0 / FPS   # 15 s
const Q_CD_DEFAULT := 300.0 / FPS

## Toleransi jangkauan (paritas BaseSkill.TARGET_RANGE_SLACK)
const TARGET_RANGE_SLACK := 1.15

## Nama skill untuk UI (skill bar / tooltip toko). Diambil dari docstring
## hero_skills/_bundle.py, jadi sama dengan nama yang muncul di pygame.
const SKILL_NAMES := {
	"grimjaw": {"q": "Blade Fury", "w": "Healing Ward", "e": "Critical Strike", "r": "Omnislash"},
	"kaizen": {"q": "Steel Wind", "w": "Wind Wall", "e": "Sweep", "r": "Tornado"},
	"sylara": {"q": "Focus Fire", "w": "Windrun", "e": "Shackle Shot", "r": "Powershot"},
	"thorne": {"q": "Viscous Nose", "w": "Bristleback", "e": "Quill Spray", "r": "Warpath"},
	"vex": {"q": "Arcane Orb", "w": "Sanity's Eclipse", "e": "Astral Imprisonment", "r": "Essence Flux"},
	"zephyr": {"q": "Bramble Maze", "w": "Shadow Realm", "e": "Casket Curse", "r": "Bedlam"},
}
const GENERIC_SKILL_NAMES := {"q": "Strike", "w": "Surge", "e": "Blink", "r": "Cataclysm"}

var hero = null
var cds: Dictionary = {"q": 0.0, "w": 0.0, "e": 0.0, "r": 0.0}
var cd_max: Dictionary = {"q": Q_CD_DEFAULT, "w": W_CD, "e": E_CD, "r": R_CD}

## Skill yang sedang dipakai (untuk renderer: KaizenSkeleton.drive(skill=...))
var active_skill: String = ""
var active_skill_timer: float = 0.0

## Kaizen Q: Steel Wind -> Dash Strike bergantian
var q_stack: int = 0
var q_reset_timer: float = 0.0

## Sylara R: charge 1 detik lalu lepas
var charge_action: String = ""
var charge_timer: float = 0.0

## Efek berkala (blade fury, omnislash, bramble, curse, bedlam, heal ward, ...)
var tickers: Array = []

var _cs = null


func _init(p_hero = null) -> void:
	hero = p_hero


func setup(p_hero) -> void:
	hero = p_hero
	if hero == null:
		return
	var q_frames := float(hero.get("skill_cooldown_frames")) if "skill_cooldown_frames" in hero else 300.0
	cd_max["q"] = maxf(0.5, q_frames / FPS)
	cds["q"] = 0.0


func _combat():
	if _cs != null and is_instance_valid(_cs):
		return _cs
	var ml := Engine.get_main_loop()
	if ml is SceneTree:
		_cs = (ml as SceneTree).root.get_node_or_null("CombatSystem")
	return _cs


# ══════════════════════════════════════════════════════════
#  TICK
# ══════════════════════════════════════════════════════════

func tick(delta: float) -> void:
	for key in cds:
		cds[key] = maxf(0.0, float(cds[key]) - delta)
	if active_skill_timer > 0.0:
		active_skill_timer -= delta
		if active_skill_timer <= 0.0:
			active_skill = ""
	# Kaizen: combo Q reset setelah 3 detik (paritas _q_reset_timer = 180)
	if q_reset_timer > 0.0:
		q_reset_timer -= delta
		if q_reset_timer <= 0.0:
			q_stack = 0
	# Charge (Sylara Powershot)
	if charge_timer > 0.0:
		charge_timer -= delta
		if charge_timer <= 0.0:
			var act := charge_action
			charge_action = ""
			_run_action(act, {}, delta)
	# Ticker efek berkala
	if not tickers.is_empty():
		var done: Array = []
		for i in range(tickers.size()):
			var t: Dictionary = tickers[i]
			t["timer"] = float(t["timer"]) - delta
			var interval := float(t["interval"])
			if interval <= 0.0:
				_run_action(str(t["action"]), t["data"], delta)
			else:
				t["acc"] = float(t["acc"]) + delta
				while float(t["acc"]) >= interval:
					t["acc"] = float(t["acc"]) - interval
					_run_action(str(t["action"]), t["data"], interval)
			if float(t["timer"]) <= 0.0:
				done.append(i)
		for i in range(done.size() - 1, -1, -1):
			tickers.remove_at(int(done[i]))


func is_ready(key: String) -> bool:
	return float(cds.get(key, 0.0)) <= 0.0


## 0 = siap, 1 = baru mulai cooldown (untuk gambar busur di SkillButton)
func cooldown_ratio(key: String) -> float:
	var mx := float(cd_max.get(key, 1.0))
	if mx <= 0.0:
		return 0.0
	return clampf(float(cds.get(key, 0.0)) / mx, 0.0, 1.0)


func cooldown_remaining(key: String) -> float:
	return float(cds.get(key, 0.0))


func set_cooldown(key: String, seconds: float) -> void:
	cds[key] = seconds


## Nama skill untuk UI. Kaizen Q bergantian Steel Wind / Dash Strike
## (paritas q_stack di _bundle.py), hero tanpa tabel memakai nama generik.
func skill_label(key: String) -> String:
	if hero == null:
		return GENERIC_SKILL_NAMES.get(key, key.to_upper())
	var htype := str(hero.get("hero_type"))
	var table: Dictionary = SKILL_NAMES.get(htype, {})
	if key == "q" and htype == "kaizen" and q_stack % 2 == 1:
		return "Dash Strike"
	if table.has(key):
		return str(table[key])
	return str(GENERIC_SKILL_NAMES.get(key, key.to_upper()))


func has_ticker(id: String) -> bool:
	for t in tickers:
		if str(t["id"]) == id:
			return true
	return false


func _add_ticker(id: String, duration: float, interval: float,
		action: String, data: Dictionary = {}) -> void:
	for t in tickers:
		if str(t["id"]) == id:
			t["timer"] = duration
			return
	tickers.append({"id": id, "timer": duration, "interval": interval,
		"acc": 0.0, "action": action, "data": data})


# ══════════════════════════════════════════════════════════
#  CAST
# ══════════════════════════════════════════════════════════

func cast(key: String) -> bool:
	if hero == null or bool(hero.get("is_dead")):
		return false
	if not is_ready(key):
		return false
	# Stun membatalkan cast (paritas Hero.cast_skill: `if self.is_stunned: return`)
	var st = hero.get("status")
	if st != null and st.has_method("is_stunned") and st.is_stunned():
		return false
	var ok := false
	match str(hero.get("hero_type")):
		"kaizen": ok = _cast_kaizen(key)
		"grimjaw": ok = _cast_grimjaw(key)
		"sylara": ok = _cast_sylara(key)
		"thorne": ok = _cast_thorne(key)
		"vex": ok = _cast_vex(key)
		"zephyr": ok = _cast_zephyr(key)
		_: ok = _cast_generic(key)
	if ok:
		_trigger_cooldown(key)
	return ok


## Paritas _trigger_*_cooldown: set timer + tandai skill aktif + screenshake
func _trigger_cooldown(key: String) -> void:
	cds[key] = float(cd_max.get(key, 1.0))
	# Cooldown reduction item (Octarine Core) — paritas Hero.cast_skill
	var inv = hero.get("items")
	if inv != null:
		var cdr := float(inv.get_cooldown_reduction())
		if cdr > 0.0:
			cds[key] = maxf(0.0, float(cds[key]) * (1.0 - cdr))
	active_skill = key
	active_skill_timer = _visual_duration(key)
	var shake: float = {"q": 8.0, "w": 5.0, "e": 6.0, "r": 15.0}[key]
	_shake(shake)
	# Spell vamp (Octarine Core): heal instan sebesar % skill_damage
	if inv != null:
		var sv := float(inv.get_spell_vamp())
		if sv > 0.0:
			_heal(float(hero.get("skill_damage")) * sv)
	_fx_burst()


func _visual_duration(key: String) -> float:
	# SKILL_VISUAL_DURATION pygame (frame) -> detik
	match str(hero.get("hero_type")):
		"kaizen":
			return {"q": 60.0, "w": 90.0, "e": 60.0, "r": 100.0}[key] / FPS
		"grimjaw":
			return {"q": 180.0, "w": 90.0, "e": 60.0, "r": 90.0}[key] / FPS
		"zephyr":
			return {"q": 240.0, "w": 180.0, "e": 180.0, "r": 240.0}[key] / FPS
	return {"q": 0.6, "w": 0.5, "e": 0.6, "r": 1.0}[key]


# ══════════════════════════════════════════════════════════
#  KAIZEN — Wind Blade Assassin
#  Q Steel Wind / Dash Strike (bergantian) · W Wind Wall · E Sweep · R Tornado
# ══════════════════════════════════════════════════════════

func _cast_kaizen(key: String) -> bool:
	match key:
		"q":
			if not _acquire_target():
				return false
			q_reset_timer = 180.0 / FPS
			if q_stack == 0:
				_aoe(_skill_range(), 1.0)
				q_stack = 1
			else:
				# Dash 70% jarak ke target lalu AOE 80px ×1.5
				var t = hero.get("target")
				if t != null and is_instance_valid(t):
					var to: Vector2 = (t as Node2D).global_position - hero.global_position
					hero.global_position += to * 0.7
				_aoe(80.0, 1.5)
				q_stack = 0
			return true
		"w":
			# Wind Wall: memblokir projectile selama 3 detik
			_buff("wind_wall", 180.0 / FPS)
			return true
		"e":
			if not _acquire_target():
				return false
			_aoe(100.0, 1.0)
			return true
		"r":
			if not _acquire_target():
				return false
			_buff("tornado", 90.0 / FPS)
			_aoe(150.0, 2.0)
			return true
	return false


# ══════════════════════════════════════════════════════════
#  GRIMJAW — Berserker
#  Q Blade Fury (spin 3 s) · W Healing Ward · E Critical Strike · R Omnislash
# ══════════════════════════════════════════════════════════

func _cast_grimjaw(key: String) -> bool:
	match key:
		"q":
			if not _acquire_target():
				return false
			_buff("blade_fury", 180.0 / FPS)
			# tick tiap 15 frame = 0.25 s, damage = skill_damage ×1 di radius skill_range
			_add_ticker("blade_fury", 180.0 / FPS, 15.0 / FPS, "spin_tick",
				{"range": _skill_range(), "mult": 1.0})
			return true
		"w":
			_buff("heal_ward", 360.0 / FPS)
			_heal(30.0)
			# ward mengikuti posisi cast; heal 2/frame diri + 1/frame sekutu radius 100
			_add_ticker("heal_ward", 360.0 / FPS, 0.0, "heal_ward_tick",
				{"origin": hero.global_position, "self_per_sec": 120.0,
					"ally_per_sec": 60.0, "radius": 100.0})
			return true
		"e":
			if not _acquire_target():
				return false
			_buff("crit", 300.0 / FPS, {"mult": 2.0})
			_aoe(60.0, 1.5)
			return true
		"r":
			if not _acquire_target():
				return false
			var t = hero.get("target")
			if t != null and is_instance_valid(t) and not bool(t.get("is_dead")):
				_damage(t, 2.5)
				_add_ticker("omnislash", 90.0 / FPS, 8.0 / FPS, "single_tick",
					{"target": t, "mult": 0.6})
			else:
				_aoe(150.0, 2.0)
			_buff("omnislash", 90.0 / FPS)
			return true
	return false


# ══════════════════════════════════════════════════════════
#  SYLARA — Wind Ranger
#  Q Focus Fire · W Windrun · E Shackle Shot · R Powershot
# ══════════════════════════════════════════════════════════

func _cast_sylara(key: String) -> bool:
	match key:
		"q":
			if not _acquire_target():
				return false
			# attack_cooldown /= 1.7 (min 20 frame) selama 3 detik
			var as_mult := 1.7
			var base_cd := float(hero.get("attack_cooldown"))
			if base_cd / as_mult < 20.0 / FPS:
				as_mult = base_cd / maxf(0.01, 20.0 / FPS)
			_buff("focus_fire", 180.0 / FPS)
			_buff("attack_speed", 180.0 / FPS, {"mult": maxf(1.0, as_mult)})
			# piercing shot: musuh segaris (perp < 15) sampai skill_range, falloff 15%/hit
			_line(_aim_dir(), _skill_range(), 15.0, 1.0, 0.15, 0.5)
			return true
		"w":
			_buff("windrun", 180.0 / FPS)
			_buff("speed", 180.0 / FPS, {"mult": 2.0})
			_heal(30.0)
			return true
		"e":
			# Shackle: target dalam 200px, damage ×0.7, tick ×0.4 tiap 0.25 s + stun attack
			var t = _nearest(200.0)
			if t == null:
				return false
			hero.target = t
			_damage(t, 0.7)
			_apply_stun(t, 45.0 / FPS)
			_buff("shackle", 150.0 / FPS)
			_add_ticker("shackle", 150.0 / FPS, 15.0 / FPS, "shackle_tick",
				{"target": t, "mult": 0.4})
			return true
		"r":
			if not _acquire_target():
				return false
			# charge 1 detik, lalu 5 panah kerucut 30° sampai 300px
			charge_action = "powershot"
			charge_timer = 60.0 / FPS
			_buff("powershot_charge", 60.0 / FPS)
			return true
	return false


# ══════════════════════════════════════════════════════════
#  THORNE — Bruiser/Quill
#  Q Viscous Nose · W Bristleback · E Quill Spray · R Warpath
# ══════════════════════════════════════════════════════════

func _cast_thorne(key: String) -> bool:
	match key:
		"q":
			if not _acquire_target():
				return false
			# cone 60px, lebar 60°, ×0.8 + slow 40% 3 detik
			_cone(60.0, PI / 3.0, 0.8, 0.4, 180.0 / FPS)
			_buff("viscous_nose", 30.0 / FPS)
			return true
		"w":
			# Bristleback: tahan 30% fisik / 15% sihir + reflect 25% selama 4 detik
			_buff("bristleback", 240.0 / FPS)
			_aoe(60.0, 0.5)
			_heal(20.0)
			return true
		"e":
			if not _acquire_target():
				return false
			_aoe(100.0, 1.2)
			_buff("quill_spray", 30.0 / FPS)
			return true
		"r":
			if not _acquire_target():
				return false
			# Warpath: damage ×1.5 + attack speed ×1.5 selama 5 detik
			_buff("warpath", 300.0 / FPS)
			_buff("damage", 300.0 / FPS, {"mult": 1.5})
			_buff("attack_speed", 300.0 / FPS, {"mult": 1.5})
			_aoe(120.0, 1.5)
			_heal(50.0)
			return true
	return false


# ══════════════════════════════════════════════════════════
#  VEX — Mage
#  Q Arcane Orb · W Sanity's Eclipse · E Astral Imprisonment · R Essence Flux
# ══════════════════════════════════════════════════════════

func _cast_vex(key: String) -> bool:
	match key:
		"q":
			var t = hero.get("target")
			if t == null or not is_instance_valid(t) or bool(t.get("is_dead")):
				t = _nearest(_skill_range())
			if t == null:
				return false
			hero.target = t
			_damage(t, 1.2)
			# musuh lain di sepanjang garis (perp < 18) kena ×0.5
			var dir: Vector2 = ((t as Node2D).global_position - hero.global_position)
			var length := dir.length()
			if length > 0.0:
				_line(dir / length, length, 18.0, 0.5, 0.0, 1.0, t)
			return true
		"w":
			if not _acquire_target():
				return false
			_buff("sanity_eclipse", 180.0 / FPS)
			for e in _enemies_in_radius(60.0):
				_damage(e, 0.8)
				_apply_slow(e, 0.5, 180.0 / FPS)
			return true
		"e":
			var t = _nearest(200.0)
			if t == null:
				return false
			hero.target = t
			_buff("astral_prison", 150.0 / FPS)
			_apply_stun(t, 150.0 / FPS)
			_damage(t, 0.6)
			return true
		"r":
			if not _acquire_target():
				return false
			_buff("essence_flux", 60.0 / FPS)
			_aoe(180.0, 2.5)
			return true
	return false


# ══════════════════════════════════════════════════════════
#  ZEPHYR — Fey Trickster
#  Q Bramble Maze · W Shadow Realm · E Casket Curse · R Bedlam
# ══════════════════════════════════════════════════════════

func _cast_zephyr(key: String) -> bool:
	match key:
		"q":
			if not _acquire_target():
				return false
			_buff("bramble", 240.0 / FPS)
			for e in _enemies_in_radius(60.0):
				_damage(e, 0.8)
				_apply_slow(e, 0.5, 180.0 / FPS)
			# trap duri di titik cast: ring 40-60px, ×0.3 + slow tiap 20 frame
			_add_ticker("bramble", 240.0 / FPS, 20.0 / FPS, "bramble_tick",
				{"origin": hero.global_position, "inner": 40.0, "outer": 60.0,
					"mult": 0.3, "slow": 0.5, "slow_dur": 60.0 / FPS})
			return true
		"w":
			# Shadow Realm: tidak bisa ditarget 3 detik + heal 2/frame
			_buff("shadow_realm", 180.0 / FPS)
			_buff("invis", 180.0 / FPS)
			_heal(40.0)
			_add_ticker("shadow_realm", 180.0 / FPS, 0.0, "self_heal_tick",
				{"per_sec": 120.0})
			return true
		"e":
			var t = _nearest(200.0)
			if t == null:
				return false
			hero.target = t
			_buff("curse", 180.0 / FPS)
			_damage(t, 0.6)
			_add_ticker("curse", 180.0 / FPS, 20.0 / FPS, "single_tick",
				{"target": t, "mult": 0.35})
			return true
		"r":
			if not _acquire_target():
				return false
			_buff("bedlam", 240.0 / FPS)
			_aoe(80.0, 1.8)
			_add_ticker("bedlam", 240.0 / FPS, 15.0 / FPS, "spin_tick",
				{"range": 80.0, "mult": 0.5})
			return true
	return false


# ══════════════════════════════════════════════════════════
#  FALLBACK GENERIK (216 hero lain yang belum punya handler khusus)
#  Memakai skill_name/skill_damage/skill_range dari HERO_TYPES apa adanya.
# ══════════════════════════════════════════════════════════

func _cast_generic(key: String) -> bool:
	match key:
		"q":
			if not _acquire_target():
				return false
			_aoe(_skill_range(), 1.0)
			return true
		"w":
			_heal(float(hero.get("max_hp")) * 0.15)
			_buff("speed", 180.0 / FPS, {"mult": 1.3})
			return true
		"e":
			if not _acquire_target():
				return false
			var t = hero.get("target")
			if t != null and is_instance_valid(t):
				var to: Vector2 = (t as Node2D).global_position - hero.global_position
				if to.length() > 40.0:
					hero.global_position += to.normalized() * 60.0
			_aoe(90.0, 1.2)
			return true
		"r":
			if not _acquire_target():
				return false
			_aoe(160.0, 2.0)
			return true
	return false


# ══════════════════════════════════════════════════════════
#  AKSI TICKER
# ══════════════════════════════════════════════════════════

func _run_action(action: String, data: Dictionary, delta: float) -> void:
	if hero == null or bool(hero.get("is_dead")):
		return
	match action:
		"spin_tick":
			_aoe(float(data.get("range", 80.0)), float(data.get("mult", 1.0)))
		"single_tick":
			var t = data.get("target")
			if t != null and is_instance_valid(t) and not bool(t.get("is_dead")):
				_damage(t, float(data.get("mult", 0.5)))
		"shackle_tick":
			var t = data.get("target")
			if t == null or not is_instance_valid(t) or bool(t.get("is_dead")):
				return
			_damage(t, float(data.get("mult", 0.4)))
			_apply_stun(t, 30.0 / FPS)
		"bramble_tick":
			var origin: Vector2 = data.get("origin", hero.global_position)
			var inner := float(data.get("inner", 40.0))
			var outer := float(data.get("outer", 60.0))
			for e in _enemies():
				var d: float = origin.distance_to((e as Node2D).global_position)
				if d > inner and d <= outer:
					_damage(e, float(data.get("mult", 0.3)))
					_apply_slow(e, float(data.get("slow", 0.5)),
						float(data.get("slow_dur", 1.0)))
		"heal_ward_tick":
			var cs = _combat()
			if cs == null:
				return
			var origin: Vector2 = data.get("origin", hero.global_position)
			var radius := float(data.get("radius", 100.0))
			if hero.global_position.distance_to(origin) <= radius:
				_heal(float(data.get("self_per_sec", 120.0)) * delta)
			for ally in cs.units_of(str(hero.get("team"))):
				if ally == hero or not is_instance_valid(ally):
					continue
				if (ally as Node2D).global_position.distance_to(origin) <= radius:
					cs.heal_unit(ally, float(data.get("ally_per_sec", 60.0)) * delta)
		"self_heal_tick":
			_heal(float(data.get("per_sec", 120.0)) * delta)
		"powershot":
			_release_powershot()


## Sylara R — 5 panah, kerucut 30°, jangkauan 300, tiap musuh kena sekali,
## falloff jarak max(0.6, 1 - proj/300 × 0.4). Paritas _release_powershot.
func _release_powershot() -> void:
	if hero == null or bool(hero.get("is_dead")):
		return
	var dir := _aim_dir()
	var base_angle := dir.angle()
	var num_arrows := 5
	var cone_angle := PI / 6.0
	var max_range := 300.0
	var hit: Array = []
	var enemies := _enemies()
	for i in range(num_arrows):
		var spread: float = (float(i) / float(num_arrows - 1) - 0.5) * cone_angle
		var a := base_angle + spread
		var adir := Vector2(cos(a), sin(a))
		for e in enemies:
			if hit.has(e) or not is_instance_valid(e):
				continue
			var rel: Vector2 = (e as Node2D).global_position - hero.global_position
			var proj: float = rel.dot(adir)
			if proj <= 0.0 or proj >= max_range:
				continue
			if absf(rel.dot(adir.orthogonal())) >= 20.0:
				continue
			var falloff := maxf(0.6, 1.0 - (proj / max_range) * 0.4)
			_damage(e, 1.0 * falloff)
			hit.append(e)


# ══════════════════════════════════════════════════════════
#  PRIMITIF EFEK
# ══════════════════════════════════════════════════════════

func _enemies() -> Array:
	var cs = _combat()
	if cs == null:
		return []
	return cs.enemies_of(str(hero.get("team")))


func _enemies_in_radius(radius: float, center: Vector2 = Vector2.INF) -> Array:
	var c: Vector2 = hero.global_position if center == Vector2.INF else center
	var out: Array = []
	for e in _enemies():
		if (e as Node2D).global_position.distance_to(c) <= radius:
			out.append(e)
	return out


func _skill_range() -> float:
	# paritas BaseSkill._skill_range: max(range hero, skill_range)
	return maxf(float(hero.get("attack_range")), float(hero.get("skill_range")))


func _damage(target, mult: float) -> void:
	var cs = _combat()
	if cs == null or target == null or not is_instance_valid(target):
		return
	var amount: float = cs.calc_skill_damage(hero, mult)
	if amount <= 0.0:
		return
	cs.apply_damage(target, amount, str(hero.get("team")), "normal", hero,
		str(hero.get("dmg_school")))


func _heal(amount: float) -> void:
	var cs = _combat()
	if cs != null:
		cs.heal_unit(hero, amount)


func _aoe(radius: float, mult: float) -> int:
	var hits := 0
	for e in _enemies_in_radius(radius):
		_damage(e, mult)
		hits += 1
	return hits


## Garis lurus: musuh dengan jarak tegak-lurus < half_width, falloff per hit
func _line(dir: Vector2, length: float, half_width: float, mult: float,
		falloff_per_hit: float = 0.0, min_falloff: float = 0.5,
		skip = null) -> int:
	var hits := 0
	for e in _enemies():
		if e == skip or not is_instance_valid(e):
			continue
		var rel: Vector2 = (e as Node2D).global_position - hero.global_position
		var proj: float = rel.dot(dir)
		if proj <= 0.0 or proj >= length:
			continue
		if absf(rel.dot(dir.orthogonal())) >= half_width:
			continue
		var falloff := maxf(min_falloff, 1.0 - float(hits) * falloff_per_hit)
		_damage(e, mult * falloff)
		hits += 1
	return hits


## Kerucut menghadap `facing` (paritas Viscous Nose Thorne)
func _cone(length: float, width_rad: float, mult: float,
		slow_amount: float = 0.0, slow_duration: float = 0.0) -> int:
	var face_angle := 0.0 if int(hero.get("facing")) > 0 else PI
	var hits := 0
	for e in _enemies():
		var rel: Vector2 = (e as Node2D).global_position - hero.global_position
		var dist := rel.length()
		if dist > length:
			continue
		var diff := absf(wrapf(rel.angle() - face_angle, -PI, PI))
		if diff > width_rad * 0.5:
			continue
		_damage(e, mult)
		if slow_amount > 0.0:
			_apply_slow(e, slow_amount, slow_duration)
		hits += 1
	return hits


func _apply_slow(target, amount: float, duration: float) -> void:
	var st = target.get("status") if target != null else null
	if st != null:
		st.apply_slow(amount, duration)


func _apply_stun(target, duration: float) -> void:
	var st = target.get("status") if target != null else null
	if st != null:
		st.apply_stun(duration)


func _buff(id: String, duration: float, data: Dictionary = {}) -> void:
	var st = hero.get("status")
	if st != null:
		st.add_buff(id, duration, data)


func _nearest(max_distance: float):
	var t = hero.get("target")
	if t != null and is_instance_valid(t) and not bool(t.get("is_dead")):
		if hero.global_position.distance_to((t as Node2D).global_position) \
				<= max_distance * TARGET_RANGE_SLACK:
			return t
	var cs = _combat()
	if cs == null:
		return null
	return cs.nearest_enemy(hero, max_distance * TARGET_RANGE_SLACK)


## Guard "jangan buang skill ke tempat kosong" (paritas BaseSkill._has_target)
func _acquire_target() -> bool:
	var t = _nearest(_skill_range())
	if t == null:
		return false
	hero.target = t
	return true


func _aim_dir() -> Vector2:
	var t = hero.get("target")
	if t != null and is_instance_valid(t):
		var d: Vector2 = (t as Node2D).global_position - hero.global_position
		if d.length_squared() > 0.01:
			return d.normalized()
	return Vector2(float(hero.get("facing")), 0.0)


func _shake(amount: float) -> void:
	var tree := Engine.get_main_loop()
	if tree is SceneTree:
		(tree as SceneTree).call_group("camera", "add_trauma", amount / 60.0)


func _fx_burst() -> void:
	if hero == null or not hero.has_method("play_skill_fx"):
		return
	hero.play_skill_fx(active_skill)
