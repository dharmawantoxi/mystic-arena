# HeroSkillKit.gd — DIHASILKAN OTOMATIS. JANGAN EDIT TANGAN.
#
# Sumber: hero_skills/_bundle.py (BaseSkill helper + 6 starter skill class +
# BossHeroSkills: init_state/update_timers/_SKILL_REGISTRY/_cast_*/_fallback_cast),
# ditranspile 1:1 oleh tools/gen_hero_skill_kit.py. Regenerasi:
#
#     python tools/gen_hero_skill_kit.py
#
# Semua fungsi STATIC dan menerima `h` = node Hero (Hero.gd). State kustom
# handler hidup di `h.kit` (Dictionary, key = nama atribut pygame persis);
# cooldown frame (skill_timer/w/e/r), active_skill(+timer), stat hero, dan
# jembatan combat ada di Hero.gd. SATUAN TIMER = FRAME seperti pygame —
# Hero.gd men-decrement-nya dalam urutan Hero.update.
#
# Jembatan yang disediakan Hero.gd (persis pola BossKit.gd):
#   h.kit_enemies(units,towers,bases)     — saring tim+alive (BaseSkill)
#   h.kit_skill_damage()                  — mirror property skill_damage pygame
#                                           (int(round) berantai amp + skill_down)
#   h.kit_catalog_all()                   — salinan heroes.json (get_all_hero_types)
#   h.kit_hit(e, dmg, team, src, school)  — take_damage dengan kwargs persis
#   h.kit_slow / kit_lock / kit_atk_timer / kit_unit_alive / kit_has_slow
#   h.kit_shake / kit_sound / kit_popup / kit_skill_proj(target)
#   h.kit_fx_cast / kit_fx_impact         — pengganti blok try/notify FX pygame
#
# Regresi dijaga godot/tests/HeroSkillParityTest.tscn vs oracle Pygame
# (tools/test_godot_match_parity.py seksi hero_skills).
extends RefCounted

const __PI := 3.141592653589793


const DEFAULT_VISUAL_DURATION := {"q": 60, "w": 90, "e": 60, "r": 100}

const VISUAL_DURATION := {
	"grimjaw": {"q": 180, "w": 90, "e": 60, "r": 90},
	"kaizen": {"q": 60, "w": 90, "e": 60, "r": 100},
	"sylara": {"q": 180, "w": 180, "e": 150, "r": 60},
	"thorne": {"q": 40, "w": 100, "e": 60, "r": 120},
	"vex": {"q": 40, "w": 100, "e": 60, "r": 80},
	"zephyr": {"q": 240, "w": 180, "e": 180, "r": 240},
}
const BOSS_HERO_VISUAL_DURATION := {"nyzrak": {"q": 50, "w": 50, "e": 70, "r": 90}, "vhalzun": {"q": 60, "w": 80, "e": 60, "r": 100}}

## ── helper setara BaseSkill (emitter tulis-tangan; mirror baris per baris
##    BaseSkill._skill_range/_acquire_target/_has_target/_get_enemies_in_range/
##    _deal_aoe_damage/_get_visual_duration/_set_active_skill/_trigger_*) ──

static func __truthy(v) -> bool:
	## Semantik truthiness Python untuk nilai Variant.
	if v == null:
		return false
	if v is bool:
		return v
	if v is int or v is float:
		return float(v) != 0.0
	if v is String:
		return v != ""
	if v is Array:
		return not (v as Array).is_empty()
	if v is Dictionary:
		return not (v as Dictionary).is_empty()
	return true


static func __py_or(a, b):
	## `a or b` di posisi NILAI (Python mengembalikan operand, bukan bool).
	return a if __truthy(a) else b

static func __skill_range(h, fallback := 200.0) -> float:
	## BaseSkill._skill_range: max(h.range, skill_range) dengan koersi float
	## dan fallback lewat skill_data kalau skill_range kosong (L195-208).
	var rng = h.skill_range
	if rng == null or float(rng) == 0.0:
		var data = h.skill_data
		rng = data.get("skill_range", fallback) if data != null else fallback
	var r := 0.0
	if rng != null:
		r = float(rng) if (rng is float or rng is int) else float(fallback)
	else:
		r = float(fallback)
	return maxf(float(h.attack_range), r)


static func __enemies_in_range(h, all_units, all_towers, all_bases, range_val: float = 0.0,
		center_x = null, center_y = null):
	## BaseSkill._get_enemies_in_range -> list [[e, dist], ...] ( urutan sama).
	var cx = float(h.global_position.x) if center_x == null else float(center_x)
	var cy = float(h.global_position.y) if center_y == null else float(center_y)
	var enemies = h.kit_enemies(all_units, all_towers, all_bases)
	var in_range := []
	for e in enemies:
		var dx = float(e.global_position.x) - cx
		var dy = float(e.global_position.y) - cy
		var dist := Vector2(dx, dy).length()
		if dist <= range_val:
			in_range.append([e, dist])
	return in_range


static func __deal_aoe(h, all_units, all_towers, all_bases,
		range_val := 0.0, damage_multiplier := 1.0):
	## BaseSkill._deal_aoe_damage — return hit_count.
	var enemies = h.kit_enemies(all_units, all_towers, all_bases)
	var hit_count := 0
	for e in enemies:
		var dist := Vector2(float(e.global_position.x) - float(h.global_position.x),
			float(e.global_position.y) - float(h.global_position.y)).length()
		if dist <= float(range_val):
			var damage := int(float(h.kit_skill_damage()) * float(damage_multiplier))
			h.kit_hit(e, damage, h.team, h, h.dmg_school)
			hit_count += 1
	return hit_count


static func __acquire_target(h, all_units, all_towers, all_bases, range_val = null):
	## BaseSkill._acquire_target — slack 1.15, retarget h.target.
	if range_val == null:
		range_val = __skill_range(h)
	var reach: float = float(range_val) * 1.15
	var cur = h.target
	if cur != null and is_instance_valid(cur) and h.kit_unit_alive(cur):
		if Vector2(float(cur.global_position.x) - float(h.global_position.x),
				float(cur.global_position.y) - float(h.global_position.y)).length() <= reach:
			return cur
	var best = null
	var best_dist: float = reach
	for e in h.kit_enemies(all_units, all_towers, all_bases):
		if not h.kit_unit_alive(e):
			continue
		var d = Vector2(float(e.global_position.x) - float(h.global_position.x),
			float(e.global_position.y) - float(h.global_position.y)).length()
		if d <= best_dist:
			best = e
			best_dist = d
	if best != null:
		h.target = best
	return best


static func __has_target(h, all_units, all_towers, all_bases, range_val = null) -> bool:
	## BaseSkill._has_target + REQUIRE_TARGET. Generator MEMVALIDASI tidak ada
	## kelas yang meng-override REQUIRE_TARGET (semua True) — kalau someday
	## ada yang False, generate gagal dan helper ini perlu param kind.
	return __acquire_target(h, all_units, all_towers, all_bases, range_val) != null


static func __vis_dur(kind: String, h, key) -> int:
	## BaseSkill._get_visual_duration + override per kelas/boss.
	var per_hero: Dictionary = BOSS_HERO_VISUAL_DURATION.get(str(h.hero_type), {})
	if kind == "boss":
		if per_hero.has(key):
			return int(per_hero[key])
		return int(DEFAULT_VISUAL_DURATION[key])
	if VISUAL_DURATION.has(kind) and VISUAL_DURATION[kind].has(key):
		return int(VISUAL_DURATION[kind][key])
	return int(DEFAULT_VISUAL_DURATION[key])


static func __set_active(h, kind: String, key, duration = null) -> void:
	## BaseSkill._set_active_skill
	if duration == null:
		duration = __vis_dur(kind, h, key)
	h.active_skill = key
	h.active_skill_timer = int(duration)


static func __trigger_q(h, kind: String, shake_amount = 8.0, visual_duration = null) -> void:
	h.skill_timer = h.skill_cooldown_max
	__set_active(h, kind, "q", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(0.7)


static func __trigger_w(h, kind: String, shake_amount = 5.0, visual_duration = null) -> void:
	h.w_cooldown = h.w_cooldown_max
	__set_active(h, kind, "w", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(0.6)


static func __trigger_e(h, kind: String, shake_amount = 6.0, visual_duration = null) -> void:
	h.e_cooldown = h.e_cooldown_max
	__set_active(h, kind, "e", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(0.7)


static func __trigger_r(h, kind: String, shake_amount = 15.0, visual_duration = null) -> void:
	h.r_cooldown = h.r_cooldown_max
	__set_active(h, kind, "r", visual_duration)
	h.kit_shake(float(shake_amount))
	h.kit_sound(1.0)


static func __by_pair0(a, b) -> bool:
	## nearby.sort(key=lambda t: t[0]) + tie-break indeks (stabilitas sort
	## Python ditiru lewat elemen [d, e, idx]).
	if float(a[0]) == float(b[0]):
		return int(a[2]) < int(b[2])
	return float(a[0]) < float(b[0])


static func __spawn_skill_proj(h, target, speed := 13.0) -> void:
	## Hero._spawn_skill_projectile: visual homing TANPA damage (damage skill
	## sudah instan). Di harness replay (hero.kit_no_projectiles) dilewati.
	h.kit_skill_proj(target)


static func __fallback_cast(h, enemies, skill_key) -> void:
	## BossHeroSkills._fallback_cast — satu-satunya jalan untuk boss-hero tanpa
	## resep registry. Damage: int(skill_damage * mult) dengan mult
	## q1.0/w1.2/e1.5/r2.5, AOE 150/200, sekolah = dmg_school hero.
	h.active_skill = skill_key
	h.active_skill_timer = 40
	var mults := {"q": 1.0, "w": 1.2, "e": 1.5, "r": 2.5}
	var mult: float = float(mults.get(skill_key, 1.0))
	var _school = h.dmg_school
	if skill_key == "q" or skill_key == "w":
		if h.target != null and is_instance_valid(h.target) and h.kit_unit_alive(h.target):
			h.kit_hit(h.target, int(float(h.kit_skill_damage()) * mult), h.team, h, _school)
	else:
		var aoe_range := 150.0 if skill_key == "e" else 200.0
		for e in enemies:
			var dist := Vector2(float(e.global_position.x) - float(h.global_position.x),
				float(e.global_position.y) - float(h.global_position.y)).length()
			if dist <= aoe_range:
				h.kit_hit(e, int(float(h.kit_skill_damage()) * mult), h.team, h, _school)



## BossHeroSkills._generic_cast — COOLDOWN CHECK DULU, lalu guard anti-buang
## (cast_range = max(int(skill_range or 100), 140) TANPA slack 1.15), retarget
## ke musuh terdekat, dispatch registry, fallback tanpa resep (cooldown tetap
## terbakar), lalu trigger. Urutan dan angka mirror persis (L888-962);
## dispatch inspect.signature diganti match yang dibangkitkan (arity
## dihitung dari AST — hasil identik).
static func __boss_generic(h, skill_key, all_units, all_towers, all_bases) -> bool:
	match skill_key:
		"q":
			if not (h.skill_timer <= 0):
				return false
		"w":
			if not (h.w_cooldown <= 0):
				return false
		"e":
			if not (h.e_cooldown <= 0):
				return false
		"r":
			if not (h.r_cooldown <= 0):
				return false
		_:
			return false
	var enemies = h.kit_enemies(all_units, all_towers, all_bases)
	var cast_range: float = float(maxi(int(float(h.skill_range)) if int(h.skill_range or 100) else 100, 140))
	var nearby := []
	for e in enemies:
		var d = Vector2(float(e.global_position.x) - float(h.global_position.x),
			float(e.global_position.y) - float(h.global_position.y)).length()
		if d <= cast_range:
			nearby.append([d, e, nearby.size()])
	if nearby.is_empty():
		return false
	nearby.sort_custom(func(a, b): return __by_pair0(a, b))
	var tgt = h.target
	if not (tgt != null and is_instance_valid(tgt) and h.kit_unit_alive(tgt)
			and Vector2(float(tgt.global_position.x) - float(h.global_position.x),
				float(tgt.global_position.y) - float(h.global_position.y)).length() <= cast_range):
		h.target = nearby[0][1]
	if not RECIPE_TYPES.has(str(h.hero_type)):
		__fallback_cast(h, enemies, skill_key)
		match skill_key:
			"q": __trigger_q(h, "boss", 10.0)
			"w": __trigger_w(h, "boss", 8.0)
			"e": __trigger_e(h, "boss", 8.0)
			"r": __trigger_r(h, "boss", 15.0)
		return true
	var ok := __registry_dispatch(h, skill_key, nearby[0][1] if false else enemies)
	if not ok:
		return false
	match skill_key:
		"q": __trigger_q(h, "boss", 10.0)
		"w": __trigger_w(h, "boss", 8.0)
		"e": __trigger_e(h, "boss", 8.0)
		"r": __trigger_r(h, "boss", 15.0)
	return true



const RECIPE_TYPES := {
	"abaddon": true,
	"aeralith": true,
	"akahime": true,
	"akashari": true,
	"alchemist": true,
	"ancient_apparition": true,
	"astraelion": true,
	"aurelion": true,
	"aurelix": true,
	"aurelyssa": true,
	"aurethzar": true,
	"aurex": true,
	"auroth": true,
	"azureth": true,
	"cryssalia": true,
	"drakar": true,
	"gornak": true,
	"gravewake": true,
	"ignirus": true,
	"ignis_drachorn": true,
	"kaeldris": true,
	"kaelthar": true,
	"kaelthorn": true,
	"kenshiro": true,
	"khazan": true,
	"krobellus": true,
	"krognarr": true,
	"kunkka": true,
	"leoric": true,
	"luminar": true,
	"malzareth": true,
	"morgath": true,
	"morkhaera": true,
	"morthraxis": true,
	"morvaenthir": true,
	"morvein": true,
	"naraka": true,
	"nazulmor": true,
	"nyxarath": true,
	"nyxareth": true,
	"nyxareva": true,
	"nyxthrael": true,
	"nyzrak": true,
	"pyraethis": true,
	"pyraklos": true,
	"raz": true,
	"seiryukong": true,
	"shirotaka": true,
	"solara": true,
	"solvanth": true,
	"solvarin": true,
	"sylvantheros": true,
	"syrentha": true,
	"thalakryon": true,
	"thalgryn": true,
	"thornvaegrim": true,
	"thorvak": true,
	"vaelindra": true,
	"vargrath": true,
	"velmyrth": true,
	"vhalzun": true,
	"vorenmarr": true,
	"vraskhan": true,
	"wiro": true,
	"xyrael": true,
	"yamako": true,
}

static func __registry_dispatch(h, skill_key, enemies) -> bool:
	match str(h.hero_type):
		"abaddon":
			if skill_key == "q":
				bosshero_cast_q_mist_coil(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_aphotic_shield(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_darkness_gale(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_death_sever(h, enemies)
				return true
			return false
		"aeralith":
			if skill_key == "q":
				bosshero_cast_q_aeralith_tailwind(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_aeralith_windblade(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_aeralith_vacuum(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_aeralith_skyrider(h, enemies)
				return true
			return false
		"akahime":
			if skill_key == "q":
				bosshero_cast_q_akahime_petalbarrage(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_akahime_soulscroll(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_akahime_shadow(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_akahime_higanbana(h, enemies)
				return true
			return false
		"akashari":
			if skill_key == "q":
				bosshero_cast_q_akashari_strike(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_akashari_blink(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_akashari_scream(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_akashari_sonic(h, enemies)
				return true
			return false
		"alchemist":
			if skill_key == "q":
				bosshero_cast_q_acid_spray(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_unstable_concoction(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_chemical_rage(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_greevils_greed(h, enemies)
				return true
			return false
		"ancient_apparition":
			if skill_key == "q":
				bosshero_cast_q_ice_vortex(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_chilling_touch(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_ice_blast(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_cold_feet(h, enemies)
				return true
			return false
		"astraelion":
			if skill_key == "q":
				bosshero_cast_q_astraelion_swordfall(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_astraelion_spiritblade(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_astraelion_forceescape(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_astraelion_zeroreturn(h, enemies)
				return true
			return false
		"aurelion":
			if skill_key == "q":
				bosshero_cast_q_aurelion_callcourage(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_aurelion_guardianassault(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_aurelion_kingscommand(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_aurelion_kingssummon(h, enemies)
				return true
			return false
		"aurelix":
			if skill_key == "q":
				bosshero_cast_q_aurelix_timebomb(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_aurelix_will(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_aurelix_shockwave(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_aurelix_transcend(h, enemies)
				return true
			return false
		"aurelyssa":
			if skill_key == "q":
				bosshero_cast_q_aurelyssa_whirlwind(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_aurelyssa_sweep(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_aurelyssa_wings(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_aurelyssa_phantom(h, enemies)
				return true
			return false
		"aurethzar":
			if skill_key == "q":
				bosshero_cast_q_aurethzar_marksman(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_aurethzar_piercing(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_aurethzar_frost(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_aurethzar_thunder(h, enemies)
				return true
			return false
		"aurex":
			if skill_key == "q":
				bosshero_cast_q_aurex_shieldcrash(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_aurex_voltblast(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_aurex_aegis(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_aurex_spin(h, enemies)
				return true
			return false
		"auroth":
			if skill_key == "q":
				bosshero_cast_q_auroth_ionicedge(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_auroth_ward(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_auroth_consecration(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_auroth_guardian(h, enemies)
				return true
			return false
		"azureth":
			if skill_key == "q":
				bosshero_cast_q_azureth_arcanebolt(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_azureth_concussive(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_azureth_ancientseal(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_azureth_mysticflare(h, enemies)
				return true
			return false
		"cryssalia":
			if skill_key == "q":
				bosshero_cast_q_cryssalia_frostshock(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_cryssalia_bitterfrost(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_cryssalia_frostbites(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_cryssalia_coldest(h, enemies)
				return true
			return false
		"drakar":
			if skill_key == "q":
				bosshero_cast_q_battle_hunger(h)
				return true
			if skill_key == "w":
				bosshero_cast_w_counter_helix(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_berserkers_call(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_culling_blade(h)
				return true
			return false
		"gornak":
			if skill_key == "q":
				bosshero_cast_q_mana_break(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_blink(h)
				return true
			if skill_key == "e":
				bosshero_cast_e_counterspell(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_mana_void(h, enemies)
				return true
			return false
		"gravewake":
			if skill_key == "q":
				bosshero_cast_q_gravewake_anchor(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_gravewake_tide(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_gravewake_shell(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_gravewake_ravage(h, enemies)
				return true
			return false
		"ignirus":
			if skill_key == "q":
				bosshero_cast_q_ignirus_searingtorrent(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_ignirus_flameshot(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_ignirus_burstfireball(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_ignirus_vengeance(h, enemies)
				return true
			return false
		"ignis_drachorn":
			if skill_key == "q":
				bosshero_cast_q_dragon_breath(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_dragon_tail(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_dragon_blood(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_elder_dragon_form(h, enemies)
				return true
			return false
		"kaeldris":
			if skill_key == "q":
				bosshero_cast_q_kaeldris_overwhelming(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_kaeldris_press(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_kaeldris_moment(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_kaeldris_duel(h, enemies)
				return true
			return false
		"kaelthar":
			if skill_key == "q":
				bosshero_cast_q_kaelthar_chargingfist(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_kaelthar_quake(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_kaelthar_fistcrack(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_kaelthar_fistbreak(h, enemies)
				return true
			return false
		"kaelthorn":
			if skill_key == "q":
				bosshero_cast_q_kaelthorn_bravestfighter(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_kaelthorn_justiceblade(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_kaelthorn_defendersassault(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_kaelthorn_chivalryfists(h, enemies)
				return true
			return false
		"kenshiro":
			if skill_key == "q":
				bosshero_cast_q_kenshiro_swiftslash(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_kenshiro_assault(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_kenshiro_gale(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_kenshiro_supremacy(h, enemies)
				return true
			return false
		"khazan":
			if skill_key == "q":
				bosshero_cast_q_khazan_chained(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_khazan_leap(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_khazan_spin(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_khazan_vanish(h, enemies)
				return true
			return false
		"krobellus":
			if skill_key == "q":
				bosshero_cast_q_krobellus_exorcism(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_krobellus_silence(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_krobellus_siphon(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_krobellus_crypt(h, enemies)
				return true
			return false
		"krognarr":
			if skill_key == "q":
				bosshero_cast_q_krognarr_strike(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_krognarr_seismic(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_krognarr_rampart(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_krognarr_eruption(h, enemies)
				return true
			return false
		"kunkka":
			if skill_key == "q":
				bosshero_cast_q_kunkka_tide(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_kunkka_xmark(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_kunkka_ghost(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_kunkka_torrent(h, enemies)
				return true
			return false
		"leoric":
			if skill_key == "q":
				bosshero_cast_q_leoric_fearlesscharge(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_leoric_sacredhammer(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_leoric_concealblast(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_leoric_immortality(h, enemies)
				return true
			return false
		"luminar":
			if skill_key == "q":
				bosshero_cast_q_luminar_illuminate(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_luminar_blindinglight(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_luminar_wisp(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_luminar_spiritform(h, enemies)
				return true
			return false
		"malzareth":
			if skill_key == "q":
				bosshero_cast_q_malzareth_disruption(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_malzareth_soul(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_malzareth_poison(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_malzareth_disillusion(h, enemies)
				return true
			return false
		"morgath":
			if skill_key == "q":
				bosshero_cast_q_spark_wraith(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_flux(h)
				return true
			if skill_key == "e":
				bosshero_cast_e_magnetic_field(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_tempest_double(h)
				return true
			return false
		"morkhaera":
			if skill_key == "q":
				bosshero_cast_q_morkhaera_spiritburst(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_morkhaera_airstrike(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_morkhaera_energyimpact(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_morkhaera_ethereal(h, enemies)
				return true
			return false
		"morthraxis":
			if skill_key == "q":
				bosshero_cast_q_morthraxis_batimpale(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_morthraxis_sanguine(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_morthraxis_phantommob(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_morthraxis_baleful(h, enemies)
				return true
			return false
		"morvaenthir":
			if skill_key == "q":
				bosshero_cast_q_morvaenthir_soulfragment(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_morvaenthir_spiritbind(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_morvaenthir_essence(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_morvaenthir_shadowrealm(h, enemies)
				return true
			return false
		"morvein":
			if skill_key == "q":
				bosshero_cast_q_morvein_puncture(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_morvein_violentstrike(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_morvein_spectralcharge(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_morvein_phantomform(h, enemies)
				return true
			return false
		"naraka":
			if skill_key == "q":
				bosshero_cast_q_naraka_chaos(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_naraka_shadowstep(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_naraka_hammer(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_naraka_execution(h, enemies)
				return true
			return false
		"nazulmor":
			if skill_key == "q":
				bosshero_cast_q_nazulmor_typhoon(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_nazulmor_aquashield(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_nazulmor_tidalrage(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_nazulmor_chaotic(h, enemies)
				return true
			return false
		"nyxarath":
			if skill_key == "q":
				bosshero_cast_q_nyxarath_shadowraze(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_nyxarath_necro(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_nyxarath_presence(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_nyxarath_requiem(h, enemies)
				return true
			return false
		"nyxareth":
			if skill_key == "q":
				bosshero_cast_q_nyxareth_starsplit(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_nyxareth_realworld(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_nyxareth_spacetime(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_nyxareth_astrorealm(h, enemies)
				return true
			return false
		"nyxareva":
			if skill_key == "q":
				bosshero_cast_q_nyxareva_darkslash(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_nyxareva_mortalwound(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_nyxareva_sacrifice(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_nyxareva_avatar(h, enemies)
				return true
			return false
		"nyxthrael":
			if skill_key == "q":
				bosshero_cast_q_nyxthrael_ambush(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_nyxthrael_nightfall(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_nyxthrael_darknightfall(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_nyxthrael_shadowbringer(h, enemies)
				return true
			return false
		"nyzrak":
			if skill_key == "q":
				bosshero_cast_q_arctic_burn(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_splinter_blast(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_winters_curse(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_cold_embrace(h, enemies)
				return true
			return false
		"pyraethis":
			if skill_key == "q":
				bosshero_cast_q_pyraethis_icarusdive(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_pyraethis_firespirits(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_pyraethis_sunray(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_pyraethis_supernova(h, enemies)
				return true
			return false
		"pyraklos":
			if skill_key == "q":
				bosshero_cast_q_pyraklos_spearmars(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_pyraklos_rebuke(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_pyraklos_bulwark(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_pyraklos_arena(h, enemies)
				return true
			return false
		"raz":
			if skill_key == "q":
				bosshero_cast_q_raz_overdrive(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_raz_searing(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_raz_surge(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_raz_gloom(h, enemies)
				return true
			return false
		"seiryukong":
			if skill_key == "q":
				bosshero_cast_q_seiryukong_boundless(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_seiryukong_treedance(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_seiryukong_jingusoldiers(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_seiryukong_wukong(h, enemies)
				return true
			return false
		"shirotaka":
			if skill_key == "q":
				bosshero_cast_q_shirotaka_hiraishin(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_shirotaka_waterboundary(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_shirotaka_shadowclones(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_shirotaka_paperbomb(h, enemies)
				return true
			return false
		"solara":
			if skill_key == "q":
				bosshero_cast_q_solara_starbreaker(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_solara_celestialhammer(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_solara_luminosity(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_solara_solarguardian(h, enemies)
				return true
			return false
		"solvanth":
			if skill_key == "q":
				bosshero_cast_q_solvanth_ringpunishment(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_solvanth_gloriouspathway(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_solvanth_laworder(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_solvanth_wrath(h, enemies)
				return true
			return false
		"solvarin":
			if skill_key == "q":
				bosshero_cast_q_solvarin_purification(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_solvarin_repel(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_solvarin_degen(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_solvarin_guardian(h, enemies)
				return true
			return false
		"sylvantheros":
			if skill_key == "q":
				bosshero_cast_q_sylvantheros_sprout(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_sylvantheros_teleport(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_sylvantheros_treants(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_sylvantheros_wrath(h, enemies)
				return true
			return false
		"syrentha":
			if skill_key == "q":
				bosshero_cast_q_syrentha_riptide(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_syrentha_song(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_syrentha_mirror(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_syrentha_siren(h, enemies)
				return true
			return false
		"thalakryon":
			if skill_key == "q":
				bosshero_cast_q_thalakryon_bolt(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_thalakryon_aquashield(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_thalakryon_tidalrage(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_thalakryon_metamorph(h, enemies)
				return true
			return false
		"thalgryn":
			if skill_key == "q":
				bosshero_cast_q_thalgryn_waveform(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_thalgryn_adaptive(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_thalgryn_morph(h)
				return true
			if skill_key == "r":
				bosshero_cast_r_thalgryn_replicate(h, enemies)
				return true
			return false
		"thornvaegrim":
			if skill_key == "q":
				bosshero_cast_q_thornvaegrim_bramble(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_thornvaegrim_twistedadvance(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_thornvaegrim_saplingthrow(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_thornvaegrim_grasp(h, enemies)
				return true
			return false
		"thorvak":
			if skill_key == "q":
				bosshero_cast_q_thorvak_seed(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_thorvak_natureswrath(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_thorvak_vengeance(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_thorvak_dryad(h, enemies)
				return true
			return false
		"vaelindra":
			if skill_key == "q":
				bosshero_cast_q_vaelindra_energywave(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_vaelindra_spacering(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_vaelindra_violetrequiem(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_vaelindra_realm(h, enemies)
				return true
			return false
		"vargrath":
			if skill_key == "q":
				bosshero_cast_q_vargrath_bloodthirst(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_vargrath_charge(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_vargrath_devilstrike(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_vargrath_souldom(h, enemies)
				return true
			return false
		"velmyrth":
			if skill_key == "q":
				bosshero_cast_q_velmyrth_dagger(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_velmyrth_strike(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_velmyrth_blur(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_velmyrth_coup(h, enemies)
				return true
			return false
		"vhalzun":
			if skill_key == "q":
				bosshero_cast_q_vhalzun_death_pulse(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_vhalzun_heartstopper(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_vhalzun_reapers_scythe(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_vhalzun_ghost_shroud(h, enemies)
				return true
			return false
		"vorenmarr":
			if skill_key == "q":
				bosshero_cast_q_vorenmarr_bonds(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_vorenmarr_power(h)
				return true
			if skill_key == "e":
				bosshero_cast_e_vorenmarr_upheaval(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_vorenmarr_golem(h, enemies)
				return true
			return false
		"vraskhan":
			if skill_key == "q":
				bosshero_cast_q_vraskhan_thorned(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_vraskhan_leap(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_vraskhan_deathslash(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_vraskhan_omni(h, enemies)
				return true
			return false
		"wiro":
			if skill_key == "q":
				bosshero_cast_q_wiro_windcut(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_wiro_whirl(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_wiro_dash(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_wiro_typhoon(h, enemies)
				return true
			return false
		"xyrael":
			if skill_key == "q":
				bosshero_cast_q_xyrael_finch(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_xyrael_defiant(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_xyrael_tempest(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_xyrael_lightness(h, enemies)
				return true
			return false
		"yamako":
			if skill_key == "q":
				bosshero_cast_q_yamako_deepforest(h, enemies)
				return true
			if skill_key == "w":
				bosshero_cast_w_yamako_woodcreation(h, enemies)
				return true
			if skill_key == "e":
				bosshero_cast_e_yamako_woodgolem(h, enemies)
				return true
			if skill_key == "r":
				bosshero_cast_r_yamako_kannon(h, enemies)
				return true
			return false
		_:
			return false
	return false


## Entry point setara Hero.cast_skill delegasi: pilih kelas
## per hero_type (6 starter), selainnya BossHeroSkills.
static func hero_kind(h) -> String:
	match str(h.hero_type):
		"grimjaw":
			return "grimjaw"
		"kaizen":
			return "kaizen"
		"sylara":
			return "sylara"
		"thorne":
			return "thorne"
		"vex":
			return "vex"
		"zephyr":
			return "zephyr"
		_:
			return "boss"


## Q — delegasi cast_q kelas handler persis Hero.cast_skill pygame.
static func cast_q(h, all_units, all_towers, all_bases) -> bool:
	match hero_kind(h):
		"grimjaw":
			return grimjaw_cast_q(h, all_units, all_towers, all_bases)
		"kaizen":
			return kaizen_cast_q(h, all_units, all_towers, all_bases)
		"sylara":
			return sylara_cast_q(h, all_units, all_towers, all_bases)
		"thorne":
			return thorne_cast_q(h, all_units, all_towers, all_bases)
		"vex":
			return vex_cast_q(h, all_units, all_towers, all_bases)
		"zephyr":
			return zephyr_cast_q(h, all_units, all_towers, all_bases)
		_:
			return __boss_generic(h, "q", all_units, all_towers, all_bases)

## W — delegasi cast_w kelas handler persis Hero.cast_skill pygame.
static func cast_w(h, all_units, all_towers, all_bases) -> bool:
	match hero_kind(h):
		"grimjaw":
			return grimjaw_cast_w(h, all_units, all_towers, all_bases)
		"kaizen":
			return kaizen_cast_w(h, all_units, all_towers, all_bases)
		"sylara":
			return sylara_cast_w(h, all_units, all_towers, all_bases)
		"thorne":
			return thorne_cast_w(h, all_units, all_towers, all_bases)
		"vex":
			return vex_cast_w(h, all_units, all_towers, all_bases)
		"zephyr":
			return zephyr_cast_w(h, all_units, all_towers, all_bases)
		_:
			return __boss_generic(h, "w", all_units, all_towers, all_bases)

## E — delegasi cast_e kelas handler persis Hero.cast_skill pygame.
static func cast_e(h, all_units, all_towers, all_bases) -> bool:
	match hero_kind(h):
		"grimjaw":
			return grimjaw_cast_e(h, all_units, all_towers, all_bases)
		"kaizen":
			return kaizen_cast_e(h, all_units, all_towers, all_bases)
		"sylara":
			return sylara_cast_e(h, all_units, all_towers, all_bases)
		"thorne":
			return thorne_cast_e(h, all_units, all_towers, all_bases)
		"vex":
			return vex_cast_e(h, all_units, all_towers, all_bases)
		"zephyr":
			return zephyr_cast_e(h, all_units, all_towers, all_bases)
		_:
			return __boss_generic(h, "e", all_units, all_towers, all_bases)

## R — delegasi cast_r kelas handler persis Hero.cast_skill pygame.
static func cast_r(h, all_units, all_towers, all_bases) -> bool:
	match hero_kind(h):
		"grimjaw":
			return grimjaw_cast_r(h, all_units, all_towers, all_bases)
		"kaizen":
			return kaizen_cast_r(h, all_units, all_towers, all_bases)
		"sylara":
			return sylara_cast_r(h, all_units, all_towers, all_bases)
		"thorne":
			return thorne_cast_r(h, all_units, all_towers, all_bases)
		"vex":
			return vex_cast_r(h, all_units, all_towers, all_bases)
		"zephyr":
			return zephyr_cast_r(h, all_units, all_towers, all_bases)
		_:
			return __boss_generic(h, "r", all_units, all_towers, all_bases)

static func update_timers(h, all_units, all_towers, all_bases) -> void:
	match hero_kind(h):
		"grimjaw":
			grimjaw_update_timers(h, all_units, all_towers, all_bases)
		"kaizen":
			kaizen_update_timers(h, all_units, all_towers, all_bases)
		"sylara":
			sylara_update_timers(h, all_units, all_towers, all_bases)
		"thorne":
			thorne_update_timers(h, all_units, all_towers, all_bases)
		"vex":
			vex_update_timers(h, all_units, all_towers, all_bases)
		"zephyr":
			zephyr_update_timers(h, all_units, all_towers, all_bases)
		"boss":
			bosshero_update_timers(h, all_units, all_towers, all_bases)
		_:
			pass

static func init_state(h) -> void:
	h.kit = {}
	match hero_kind(h):
		"grimjaw":
			grimjaw_init_state(h)
		"kaizen":
			kaizen_init_state(h)
		"sylara":
			sylara_init_state(h)
		"thorne":
			thorne_init_state(h)
		"vex":
			vex_init_state(h)
		"zephyr":
			zephyr_init_state(h)
		"boss":
			bosshero_init_state(h)
	return h.kit


## hero_skills/_bundle.py:345-381 [BossHeroSkills.init_state]
static func bosshero_init_state(h):
	(h).active_skill = null
	(h).active_skill_timer = 0
	h.kit["flux_target"] = null
	h.kit["flux_active_timer"] = 0
	h.kit["vortex_x"] = 0
	h.kit["vortex_y"] = 0
	h.kit["vortex_active_timer"] = 0
	h.kit["mana_void_x"] = 0
	h.kit["mana_void_y"] = 0
	h.kit["blink_from_x"] = 0
	h.kit["blink_from_y"] = 0
	h.kit["rage_active"] = false
	h.kit["rage_timer"] = 0
	h.kit["defense_boost"] = false
	h.kit["defense_timer"] = 0
	h.kit["clones_active_timer"] = 0
	h.kit["clones_positions"] = []
	h.kit["w_target_x"] = 0
	h.kit["w_target_y"] = 0
	h.kit["w_dir_x"] = 1
	h.kit["w_dir_y"] = 0
	h.kit["r_dir_x"] = 1
	h.kit["r_dir_y"] = 0
	h.kit["cold_feet_target_x"] = 0
	h.kit["cold_feet_target_y"] = 0
	h.kit["dragon_form_active"] = false
	h.kit["dragon_form_timer"] = 0
	h.kit["dragon_blood_active"] = false
	h.kit["dragon_blood_timer"] = 0


## hero_skills/_bundle.py:383-454 [BossHeroSkills.update_timers]
static func bosshero_update_timers(h, all_units, all_towers, all_bases):
	var clone_damage = null
	var dist = null
	var enemies = null
	var stats = null

	if h.kit.get("rage_active", null):
		h.kit["rage_timer"] = (h.kit.get("rage_timer", null)) - (1)
		if (h.kit.get("rage_timer", null)) <= (0):
			h.kit["rage_active"] = false
			stats = h.kit_catalog_all()[(h).hero_type]
			(h).damage = float(stats["damage"])
	if h.kit.get("defense_boost", null):
		h.kit["defense_timer"] = (h.kit.get("defense_timer", null)) - (1)
		if (h.kit.get("defense_timer", null)) <= (0):
			h.kit["defense_boost"] = false
	if (h.kit.get("vortex_active_timer", null)) > (0):
		h.kit["vortex_active_timer"] = (h.kit.get("vortex_active_timer", null)) - (1)
		if (fmod(h.kit.get("vortex_active_timer", null), 20)) == (0):
			enemies = h.kit_enemies(all_units, all_towers, all_bases)
			for e in enemies:
				dist = Vector2(((e).global_position.x) - (h.kit.get("vortex_x", null)), ((e).global_position.y) - (h.kit.get("vortex_y", null))).length()
				if (dist) <= (80):
					h.kit_hit(e, int(((h).kit_skill_damage()) * (0.3)), (h).team, null, "")
					if h.kit_has_slow(e):
						h.kit_slow(e, 0.5, 60)
	if (h.kit.get("flux_active_timer", null)) > (0):
		h.kit["flux_active_timer"] = (h.kit.get("flux_active_timer", null)) - (1)
		if (fmod(h.kit.get("flux_active_timer", null), 30)) == (0):
			if (h.kit.get("flux_target", null)) and (h.kit_unit_alive(h.kit.get("flux_target", null))):
				h.kit_hit(h.kit.get("flux_target", null), int(((h).kit_skill_damage()) * (0.3)), (h).team, null, "")
				if h.kit_has_slow(h.kit.get("flux_target", null)):
					h.kit_slow(h.kit.get("flux_target", null), 0.4, 60)
	if (h.kit.get("clones_active_timer", null)) > (0):
		h.kit["clones_active_timer"] = (h.kit.get("clones_active_timer", null)) - (1)
		if (fmod(h.kit.get("clones_active_timer", null), 40)) == (0):
			if ((h).target) and (h.kit_unit_alive((h).target)):
				clone_damage = int((int((h).damage)) * (0.5))
				h.kit_hit((h).target, clone_damage, (h).team, null, "")
	if h.kit.get("dragon_form_active", false):
		h.kit["dragon_form_timer"] = (h.kit.get("dragon_form_timer", null)) - (1)
		if (h.kit.get("dragon_form_timer", null)) <= (0):
			h.kit["dragon_form_active"] = false
			stats = h.kit_catalog_all()[(h).hero_type]
			(h).damage = float(stats["damage"])
	if h.kit.get("dragon_blood_active", false):
		h.kit["dragon_blood_timer"] = (h.kit.get("dragon_blood_timer", null)) - (1)
		if (h.kit.get("dragon_blood_timer", null)) <= (0):
			h.kit["dragon_blood_active"] = false


## hero_skills/_bundle.py:1031-1036 [BossHeroSkills._cast_q_mana_break]
static func bosshero_cast_q_mana_break(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:1038-1050 [BossHeroSkills._cast_w_blink]
static func bosshero_cast_w_blink(h):
	var dist = null
	var dx = null
	var dy = null
	var offset = null

	(h).active_skill = "w"
	(h).active_skill_timer = 25
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit["blink_from_x"] = (h).global_position.x
		h.kit["blink_from_y"] = (h).global_position.y
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			offset = maxf(0, (dist) - (60))
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(dist)) * (offset))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(dist)) * (offset))


## hero_skills/_bundle.py:1052-1060 [BossHeroSkills._cast_e_counterspell]
static func bosshero_cast_e_counterspell(h, enemies):
	var dist = null

	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (100):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:1062-1072 [BossHeroSkills._cast_r_mana_void]
static func bosshero_cast_r_mana_void(h, enemies):
	var dist = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	h.kit["mana_void_x"] = (h).global_position.x
	h.kit["mana_void_y"] = (h).global_position.y
	for e in enemies:
		dist = Vector2(((e).global_position.x) - (h.kit.get("mana_void_x", null)), ((e).global_position.y) - (h.kit.get("mana_void_y", null))).length()
		if (dist) <= (180):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")


## hero_skills/_bundle.py:1078-1083 [BossHeroSkills._cast_q_spark_wraith]
static func bosshero_cast_q_spark_wraith(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:1085-1094 [BossHeroSkills._cast_w_flux]
static func bosshero_cast_w_flux(h):
	(h).active_skill = "w"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit["flux_target"] = (h).target
		h.kit["flux_active_timer"] = 240
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (0.5)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.5, 240)


## hero_skills/_bundle.py:1096-1106 [BossHeroSkills._cast_e_magnetic_field]
static func bosshero_cast_e_magnetic_field(h, enemies):
	var dist = null
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 90
	for e in enemies:
		dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (90):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.7)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 45))
	heal = int(((h).max_hp) * (0.08))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1108-1113 [BossHeroSkills._cast_r_tempest_double]
static func bosshero_cast_r_tempest_double(h):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 60
	h.kit["clones_active_timer"] = 480
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1119-1131 [BossHeroSkills._cast_q_battle_hunger]
static func bosshero_cast_q_battle_hunger(h):
	var base_damage = null
	var heal = null

	(h).active_skill = "q"
	(h).active_skill_timer = 90
	h.kit["rage_active"] = true
	h.kit["rage_timer"] = 300
	base_damage = h.kit_catalog_all()[(h).hero_type]["damage"]
	(h).damage = float(int((base_damage) * (1.5)))
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1133-1140 [BossHeroSkills._cast_w_counter_helix]
static func bosshero_cast_w_counter_helix(h, enemies):
	var dist = null

	(h).active_skill = "w"
	(h).active_skill_timer = 45
	for e in enemies:
		dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (100):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")


## hero_skills/_bundle.py:1142-1153 [BossHeroSkills._cast_e_berserkers_call]
static func bosshero_cast_e_berserkers_call(h, enemies):
	var dist = null

	(h).active_skill = "e"
	(h).active_skill_timer = 60
	h.kit["defense_boost"] = true
	h.kit["defense_timer"] = 180
	for e in enemies:
		dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (120):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 30))


## hero_skills/_bundle.py:1155-1163 [BossHeroSkills._cast_r_culling_blade]
static func bosshero_cast_r_culling_blade(h):
	var damage = null

	(h).active_skill = "r"
	(h).active_skill_timer = 60
	if ((h).target) and (h.kit_unit_alive((h).target)):
		damage = int(((h).kit_skill_damage()) * (2.5))
		if (float(((h).target).hp) / float(((h).target).max_hp)) < (0.3):
			damage = int((damage) * (2))
		h.kit_hit((h).target, damage, (h).team, null, "")


## hero_skills/_bundle.py:1169-1174 [BossHeroSkills._cast_q_mist_coil]
static func bosshero_cast_q_mist_coil(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 30
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:1176-1183 [BossHeroSkills._cast_w_aphotic_shield]
static func bosshero_cast_w_aphotic_shield(h, enemies):
	var shield_hp = null

	(h).active_skill = "w"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (100):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")
	shield_hp = int(((h).max_hp) * (0.25))
	(h).hp = minf((h).max_hp, ((h).hp) + (shield_hp))


## hero_skills/_bundle.py:1185-1196 [BossHeroSkills._cast_e_darkness_gale]
static func bosshero_cast_e_darkness_gale(h):
	var dist = null
	var dx = null
	var dy = null

	(h).active_skill = "e"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(dist)) * (80))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(dist)) * (80))
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:1198-1203 [BossHeroSkills._cast_r_death_sever]
static func bosshero_cast_r_death_sever(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (180):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.5)), (h).team, null, "")


## hero_skills/_bundle.py:1209-1214 [BossHeroSkills._cast_q_acid_spray]
static func bosshero_cast_q_acid_spray(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:1216-1234 [BossHeroSkills._cast_w_unstable_concoction]
static func bosshero_cast_w_unstable_concoction(h, enemies):
	var target_x = null
	var target_y = null

	(h).active_skill = "w"
	(h).active_skill_timer = 60
	if ((h).target) and (h.kit_unit_alive((h).target)):
		target_x = ((h).target).global_position.x
		target_y = ((h).target).global_position.y
	else:
		target_x = (h).global_position.x
		target_y = (h).global_position.y
	for e in enemies:
		if (Vector2(((e).global_position.x) - (target_x), ((e).global_position.y) - (target_y)).length()) <= (100):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 180)
	h.kit["w_target_x"] = target_x
	h.kit["w_target_y"] = target_y


## hero_skills/_bundle.py:1236-1247 [BossHeroSkills._cast_e_chemical_rage]
static func bosshero_cast_e_chemical_rage(h):
	var base_damage = null
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 60
	h.kit["rage_active"] = true
	h.kit["rage_timer"] = 360
	base_damage = h.kit_catalog_all()[(h).hero_type]["damage"]
	(h).damage = float(int((base_damage) * (1.5)))
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1249-1261 [BossHeroSkills._cast_r_greevils_greed]
static func bosshero_cast_r_greevils_greed(h, enemies):
	var heal = null
	var kills = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	kills = 0
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.5)), (h).team, null, "")
			if not (h.kit_unit_alive(e)):
				kills += 1
	if (kills) > (0):
		heal = (kills) * (100)
		(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1267-1283 [BossHeroSkills._cast_q_ice_vortex]
static func bosshero_cast_q_ice_vortex(h, enemies):
	var dist = null

	(h).active_skill = "q"
	(h).active_skill_timer = 60
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit["vortex_x"] = ((h).target).global_position.x
		h.kit["vortex_y"] = ((h).target).global_position.y
	else:
		h.kit["vortex_x"] = ((h).global_position.x) + (100)
		h.kit["vortex_y"] = (h).global_position.y
	h.kit["vortex_active_timer"] = 180
	for e in enemies:
		dist = Vector2(((e).global_position.x) - (h.kit.get("vortex_x", null)), ((e).global_position.y) - (h.kit.get("vortex_y", null))).length()
		if (dist) <= (80):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.6)), (h).team, null, "")


## hero_skills/_bundle.py:1285-1317 [BossHeroSkills._cast_w_chilling_touch]
static func bosshero_cast_w_chilling_touch(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null

	(h).active_skill = "w"
	(h).active_skill_timer = 45
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	max_range = 400
	line_width = 30
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")
				if h.kit_has_slow(e):
					h.kit_slow(e, 0.6, 180)
	h.kit["w_dir_x"] = dx
	h.kit["w_dir_y"] = dy


## hero_skills/_bundle.py:1319-1327 [BossHeroSkills._cast_e_ice_blast]
static func bosshero_cast_e_ice_blast(h):
	(h).active_skill = "e"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (2.5)), (h).team, null, "")
		if h.kit_has_atk_timer((h).target):
			h.kit_lock((h).target, maxf(h.kit_atk_timer((h).target), 90))


## hero_skills/_bundle.py:1329-1361 [BossHeroSkills._cast_r_cold_feet]
static func bosshero_cast_r_cold_feet(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	max_range = 500
	line_width = 60
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (3.0)), (h).team, null, "")
				if h.kit_has_slow(e):
					h.kit_slow(e, 0.7, 240)
	h.kit["r_dir_x"] = dx
	h.kit["r_dir_y"] = dy


## hero_skills/_bundle.py:1370-1394 [BossHeroSkills._cast_q_arctic_burn]
static func bosshero_cast_q_arctic_burn(h, enemies):
	var ex = null
	var ey = null
	var line_width = null
	var ln = null
	var max_range = null
	var proj = null
	var sx = null
	var sy = null
	var tx = null
	var ty = null
	var ux = null
	var uy = null

	(h).active_skill = "q"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		tx = ((h).target).global_position.x
		ty = ((h).target).global_position.y
	else:
		tx = (h).global_position.x
		ty = (h).global_position.y
	sx = (h).global_position.x
	sy = (h).global_position.y
	max_range = 240.0
	line_width = 26.0
	ln = __py_or(Vector2((tx) - (sx), (ty) - (sy)).length(), 1.0)
	ux = float((tx) - (sx)) / float(ln)
	uy = float((ty) - (sy)) / float(ln)
	for e in enemies:
		ex = ((e).global_position.x) - (sx)
		ey = ((e).global_position.y) - (sy)
		proj = ((ex) * (ux)) + ((ey) * (uy))
		if (0) < (proj) and (proj) < (max_range):
			if (absf(((ex) * (-(uy))) + ((ey) * (ux)))) < (line_width):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
				if h.kit_has_slow(e):
					h.kit_slow(e, 0.4, 120)
	h.kit_fx_impact(tx, ty, 60, "q")


## hero_skills/_bundle.py:1396-1413 [BossHeroSkills._cast_w_splinter_blast]
static func bosshero_cast_w_splinter_blast(h, enemies):
	var tx = null
	var ty = null

	(h).active_skill = "w"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		tx = ((h).target).global_position.x
		ty = ((h).target).global_position.y
	else:
		tx = (h).global_position.x
		ty = (h).global_position.y
	for e in enemies:
		if (Vector2(((e).global_position.x) - (tx), ((e).global_position.y) - (ty)).length()) <= (80):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.3, 60)
	h.kit_fx_impact(tx, ty, 80, "w")


## hero_skills/_bundle.py:1415-1432 [BossHeroSkills._cast_e_winters_curse]
static func bosshero_cast_e_winters_curse(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 70
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")
		if h.kit_has_atk_timer((h).target):
			h.kit_lock((h).target, maxf(h.kit_atk_timer((h).target), 90))
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.7, 180)
		h.kit_fx_impact(((h).target).global_position.x, ((h).target).global_position.y, 44, "e")


## hero_skills/_bundle.py:1434-1451 [BossHeroSkills._cast_r_cold_embrace]
static func bosshero_cast_r_cold_embrace(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	h.kit["shield_active"] = true
	h.kit["shield_timer"] = 240
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 180)
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))
	h.kit_fx_impact((h).global_position.x, (h).global_position.y, 200, "r")


## hero_skills/_bundle.py:1457-1488 [BossHeroSkills._cast_q_dragon_breath]
static func bosshero_cast_q_dragon_breath(h, enemies):
	var allowed_width = null
	var cone_width = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var max_range = null
	var perp = null
	var proj = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	max_range = 250
	cone_width = 60
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			allowed_width = (cone_width) * ((0.3) + ((float(proj) / float(max_range)) * (0.7)))
			if (perp) < (allowed_width):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.6)), (h).team, null, "")
				if h.kit_has_atk_timer(e):
					h.kit_lock(e, maxf(h.kit_atk_timer(e), 45))


## hero_skills/_bundle.py:1490-1500 [BossHeroSkills._cast_w_dragon_tail]
static func bosshero_cast_w_dragon_tail(h, enemies):
	var dist = null

	(h).active_skill = "w"
	(h).active_skill_timer = 40
	for e in enemies:
		dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (130):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:1502-1514 [BossHeroSkills._cast_e_dragon_blood]
static func bosshero_cast_e_dragon_blood(h):
	var base_damage = null
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 60
	h.kit["dragon_blood_active"] = true
	h.kit["dragon_blood_timer"] = 480
	base_damage = h.kit_catalog_all()[(h).hero_type]["damage"]
	(h).damage = float(int((base_damage) * (1.3)))
	heal = int(((h).max_hp) * (0.2))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1516-1535 [BossHeroSkills._cast_r_elder_dragon_form]
static func bosshero_cast_r_elder_dragon_form(h, enemies):
	var base_damage = null
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	h.kit["dragon_form_active"] = true
	h.kit["dragon_form_timer"] = 600
	base_damage = h.kit_catalog_all()[(h).hero_type]["damage"]
	(h).damage = float(int((base_damage) * (1.8)))
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (3.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 90))
	heal = int(((h).max_hp) * (0.25))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1541-1552 [BossHeroSkills._cast_q_krobellus_exorcism]
static func bosshero_cast_q_krobellus_exorcism(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 50
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")
	h.kit_fx_cast("q")
	h.kit_fx_impact((h).global_position.x, (h).global_position.y, 150, "q")


## hero_skills/_bundle.py:1554-1567 [BossHeroSkills._cast_w_krobellus_silence]
static func bosshero_cast_w_krobellus_silence(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (120):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))
	h.kit_fx_cast("w")
	h.kit_fx_impact((h).global_position.x, (h).global_position.y, 120, "w")


## hero_skills/_bundle.py:1569-1582 [BossHeroSkills._cast_e_krobellus_siphon]
static func bosshero_cast_e_krobellus_siphon(h):
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")
		heal = int(((h).kit_skill_damage()) * (0.5))
		(h).hp = minf((h).max_hp, ((h).hp) + (heal))
		h.kit_fx_cast("e")
		h.kit_fx_impact(((h).target).global_position.x, ((h).target).global_position.y, 44, "e")


## hero_skills/_bundle.py:1584-1596 [BossHeroSkills._cast_r_krobellus_crypt]
static func bosshero_cast_r_krobellus_crypt(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.5)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))
	h.kit_fx_cast("r")
	h.kit_fx_impact((h).global_position.x, (h).global_position.y, 200, "r")


## hero_skills/_bundle.py:1606-1617 [BossHeroSkills._cast_q_vhalzun_death_pulse]
static func bosshero_cast_q_vhalzun_death_pulse(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (130):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")
	h.kit_fx_cast("q")
	h.kit_fx_impact((h).global_position.x, (h).global_position.y, 130, "q")


## hero_skills/_bundle.py:1619-1632 [BossHeroSkills._cast_w_vhalzun_heartstopper]
static func bosshero_cast_w_vhalzun_heartstopper(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))
	h.kit_fx_cast("w")
	h.kit_fx_impact((h).global_position.x, (h).global_position.y, 150, "w")


## hero_skills/_bundle.py:1634-1643 [BossHeroSkills._cast_e_vhalzun_reapers_scythe]
static func bosshero_cast_e_vhalzun_reapers_scythe(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
	h.kit_fx_cast("e")


## hero_skills/_bundle.py:1645-1657 [BossHeroSkills._cast_r_vhalzun_ghost_shroud]
static func bosshero_cast_r_vhalzun_ghost_shroud(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 100
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.4)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.18))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))
	h.kit_fx_cast("r")
	h.kit_fx_impact((h).global_position.x, (h).global_position.y, 150, "r")


## hero_skills/_bundle.py:1663-1673 [BossHeroSkills._cast_q_kunkka_tide]
static func bosshero_cast_q_kunkka_tide(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var perp = null
	var proj = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (250):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (70):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")


## hero_skills/_bundle.py:1675-1683 [BossHeroSkills._cast_w_kunkka_xmark]
static func bosshero_cast_w_kunkka_xmark(h, enemies):
	var tx = null
	var ty = null

	(h).active_skill = "w"
	(h).active_skill_timer = 80
	if ((h).target) and (h.kit_unit_alive((h).target)):
		tx = ((h).target).global_position.x
		ty = ((h).target).global_position.y
		for e in enemies:
			if (Vector2(((e).global_position.x) - (tx), ((e).global_position.y) - (ty)).length()) <= (120):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")
				if h.kit_has_atk_timer(e):
					h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:1685-1699 [BossHeroSkills._cast_e_kunkka_ghost]
static func bosshero_cast_e_kunkka_ghost(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var heal = null
	var perp = null
	var proj = null

	(h).active_skill = "e"
	(h).active_skill_timer = 90
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (300):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (80):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (2.2)), (h).team, null, "")
				if h.kit_has_atk_timer(e):
					h.kit_lock(e, maxf(h.kit_atk_timer(e), 90))
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1701-1712 [BossHeroSkills._cast_r_kunkka_torrent]
static func bosshero_cast_r_kunkka_torrent(h, enemies):
	var heal = null
	var tx = null
	var ty = null

	(h).active_skill = "r"
	(h).active_skill_timer = 100
	if ((h).target) and (h.kit_unit_alive((h).target)):
		tx = ((h).target).global_position.x
		ty = ((h).target).global_position.y
	else:
		tx = (h).global_position.x
		ty = (h).global_position.y
	for e in enemies:
		if (Vector2(((e).global_position.x) - (tx), ((e).global_position.y) - (ty)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (3.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 120))
	heal = int(((h).max_hp) * (0.2))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1718-1736 [BossHeroSkills._cast_q_nyxarath_shadowraze]
static func bosshero_cast_q_nyxarath_shadowraze(h, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var perp = null
	var proj = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if __py_or(not (closest), (closest_dist) > (300)):
		return null
	dx = ((closest).global_position.x) - ((h).global_position.x)
	dy = ((closest).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (280):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (50):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
				if h.kit_has_atk_timer(e):
					h.kit_lock(e, maxf(h.kit_atk_timer(e), 45))


## hero_skills/_bundle.py:1738-1750 [BossHeroSkills._cast_w_nyxarath_necro]
static func bosshero_cast_w_nyxarath_necro(h, enemies):
	var base_damage = null
	var heal = null
	var kills = null

	(h).active_skill = "w"
	(h).active_skill_timer = 70
	kills = 0
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (180):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.7)), (h).team, null, "")
			if not (h.kit_unit_alive(e)):
				kills += 1
	base_damage = h.kit_catalog_all()[(h).hero_type]["damage"]
	(h).damage = float(int((base_damage) * (1.4)))
	h.kit["rage_active"] = true
	h.kit["rage_timer"] = 480
	heal = (int(((h).max_hp) * (0.08))) + ((kills) * (30))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1752-1760 [BossHeroSkills._cast_e_nyxarath_presence]
static func bosshero_cast_e_nyxarath_presence(h, enemies):
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 90))
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 240)
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1762-1769 [BossHeroSkills._cast_r_nyxarath_requiem]
static func bosshero_cast_r_nyxarath_requiem(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 110
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (3.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 120))
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1775-1788 [BossHeroSkills._cast_q_gravewake_anchor]
static func bosshero_cast_q_gravewake_anchor(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var perp = null
	var proj = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (200):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (60):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.4)), (h).team, null, "")
				if h.kit_has_slow(e):
					h.kit_slow(e, 0.5, 180)


## hero_skills/_bundle.py:1790-1800 [BossHeroSkills._cast_w_gravewake_tide]
static func bosshero_cast_w_gravewake_tide(h, enemies):
	var tx = null
	var ty = null

	(h).active_skill = "w"
	(h).active_skill_timer = 80
	if ((h).target) and (h.kit_unit_alive((h).target)):
		tx = ((h).target).global_position.x
		ty = ((h).target).global_position.y
	else:
		tx = (h).global_position.x
		ty = (h).global_position.y
	for e in enemies:
		if (Vector2(((e).global_position.x) - (tx), ((e).global_position.y) - (ty)).length()) <= (120):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:1802-1805 [BossHeroSkills._cast_e_gravewake_shell]
static func bosshero_cast_e_gravewake_shell(h):
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 70
	h.kit["defense_boost"] = true
	h.kit["defense_timer"] = 300
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1807-1814 [BossHeroSkills._cast_r_gravewake_ravage]
static func bosshero_cast_r_gravewake_ravage(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 180)
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1820-1833 [BossHeroSkills._cast_q_syrentha_riptide]
static func bosshero_cast_q_syrentha_riptide(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var perp = null
	var proj = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (250):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (70):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")
				if h.kit_has_slow(e):
					h.kit_slow(e, 0.5, 180)


## hero_skills/_bundle.py:1835-1843 [BossHeroSkills._cast_w_syrentha_song]
static func bosshero_cast_w_syrentha_song(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 120))
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.7, 240)


## hero_skills/_bundle.py:1845-1851 [BossHeroSkills._cast_e_syrentha_mirror]
static func bosshero_cast_e_syrentha_mirror(h):
	var base_damage = null
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 70
	h.kit["rage_active"] = true
	h.kit["rage_timer"] = 360
	base_damage = h.kit_catalog_all()[(h).hero_type]["damage"]
	(h).damage = float(int((base_damage) * (1.4)))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1853-1860 [BossHeroSkills._cast_r_syrentha_siren]
static func bosshero_cast_r_syrentha_siren(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.2)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 150))
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1866-1877 [BossHeroSkills._cast_q_thalgryn_waveform]
static func bosshero_cast_q_thalgryn_waveform(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var perp = null
	var proj = null
	var surge = null

	(h).active_skill = "q"
	(h).active_skill_timer = 60
	if __py_or(not ((h).target), not (h.kit_unit_alive((h).target))):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return null
	dx /= dist
	dy /= dist
	for e in enemies:
		ex = ((e).global_position.x) - ((h).global_position.x)
		ey = ((e).global_position.y) - ((h).global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (250):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (50):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.6)), (h).team, null, "")
	surge = minf(dist, 200)
	(h).global_position.x = ((h).global_position.x) + ((dx) * (surge))
	(h).global_position.y = ((h).global_position.y) + ((dy) * (surge))


## hero_skills/_bundle.py:1879-1885 [BossHeroSkills._cast_w_thalgryn_adaptive]
static func bosshero_cast_w_thalgryn_adaptive(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
		for e in enemies:
			if ((e) != ((h).target)) and ((Vector2(((e).global_position.x) - (((h).target).global_position.x), ((e).global_position.y) - (((h).target).global_position.y)).length()) <= (60)):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (0.7)), (h).team, null, "")


## hero_skills/_bundle.py:1887-1893 [BossHeroSkills._cast_e_thalgryn_morph]
static func bosshero_cast_e_thalgryn_morph(h):
	var base_damage = null
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 60
	h.kit["rage_active"] = true
	h.kit["rage_timer"] = 300
	base_damage = h.kit_catalog_all()[(h).hero_type]["damage"]
	(h).damage = float(int((base_damage) * (1.35)))
	heal = int(((h).max_hp) * (0.14))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1895-1902 [BossHeroSkills._cast_r_thalgryn_replicate]
static func bosshero_cast_r_thalgryn_replicate(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.4, 180)
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1908-1916 [BossHeroSkills._cast_q_malzareth_disruption]
static func bosshero_cast_q_malzareth_disruption(h, enemies):
	var tx = null
	var ty = null

	(h).active_skill = "q"
	(h).active_skill_timer = 60
	if ((h).target) and (h.kit_unit_alive((h).target)):
		tx = ((h).target).global_position.x
		ty = ((h).target).global_position.y
	else:
		tx = ((h).global_position.x) + (100)
		ty = (h).global_position.y
	for e in enemies:
		if (Vector2(((e).global_position.x) - (tx), ((e).global_position.y) - (ty)).length()) <= (100):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")


## hero_skills/_bundle.py:1918-1924 [BossHeroSkills._cast_w_malzareth_soul]
static func bosshero_cast_w_malzareth_soul(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.4)), (h).team, null, "")
		for e in enemies:
			if ((e) != ((h).target)) and ((Vector2(((e).global_position.x) - (((h).target).global_position.x), ((e).global_position.y) - (((h).target).global_position.y)).length()) <= (60)):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (0.7)), (h).team, null, "")


## hero_skills/_bundle.py:1926-1931 [BossHeroSkills._cast_e_malzareth_poison]
static func bosshero_cast_e_malzareth_poison(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.5, 180)


## hero_skills/_bundle.py:1933-1940 [BossHeroSkills._cast_r_malzareth_disillusion]
static func bosshero_cast_r_malzareth_disillusion(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 90))
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1946-1951 [BossHeroSkills._cast_q_akashari_strike]
static func bosshero_cast_q_akashari_strike(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.6)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.4, 120)


## hero_skills/_bundle.py:1953-1962 [BossHeroSkills._cast_w_akashari_blink]
static func bosshero_cast_w_akashari_blink(h, enemies):
	var dist = null
	var dx = null
	var dy = null
	var heal = null

	(h).active_skill = "w"
	(h).active_skill_timer = 55
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(dist)) * (minf(dist, 150)))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(dist)) * (minf(dist, 150)))
		for e in enemies:
			if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (80):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.08))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1964-1968 [BossHeroSkills._cast_e_akashari_scream]
static func bosshero_cast_e_akashari_scream(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.5)), (h).team, null, "")


## hero_skills/_bundle.py:1970-1977 [BossHeroSkills._cast_r_akashari_sonic]
static func bosshero_cast_r_akashari_sonic(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.3)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 240)
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1983-1989 [BossHeroSkills._cast_q_vorenmarr_bonds]
static func bosshero_cast_q_vorenmarr_bonds(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 70
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")
		for e in enemies:
			if ((e) != ((h).target)) and ((Vector2(((e).global_position.x) - (((h).target).global_position.x), ((e).global_position.y) - (((h).target).global_position.y)).length()) <= (80)):
				h.kit_hit(e, int(((h).kit_skill_damage()) * (0.6)), (h).team, null, "")


## hero_skills/_bundle.py:1991-1993 [BossHeroSkills._cast_w_vorenmarr_power]
static func bosshero_cast_w_vorenmarr_power(h):
	var heal = null

	(h).active_skill = "w"
	(h).active_skill_timer = 70
	heal = int(((h).max_hp) * (0.14))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:1995-2005 [BossHeroSkills._cast_e_vorenmarr_upheaval]
static func bosshero_cast_e_vorenmarr_upheaval(h, enemies):
	var tx = null
	var ty = null

	(h).active_skill = "e"
	(h).active_skill_timer = 80
	if ((h).target) and (h.kit_unit_alive((h).target)):
		tx = ((h).target).global_position.x
		ty = ((h).target).global_position.y
	else:
		tx = (h).global_position.x
		ty = (h).global_position.y
	for e in enemies:
		if (Vector2(((e).global_position.x) - (tx), ((e).global_position.y) - (ty)).length()) <= (120):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2007-2014 [BossHeroSkills._cast_r_vorenmarr_golem]
static func bosshero_cast_r_vorenmarr_golem(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 100
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.2)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 90))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2021-2025 [BossHeroSkills._cast_q_kenshiro_swiftslash]
static func bosshero_cast_q_kenshiro_swiftslash(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2027-2039 [BossHeroSkills._cast_w_kenshiro_assault]
static func bosshero_cast_w_kenshiro_assault(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "w"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 90)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.4)), (h).team, null, "")


## hero_skills/_bundle.py:2041-2046 [BossHeroSkills._cast_e_kenshiro_gale]
static func bosshero_cast_e_kenshiro_gale(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2048-2053 [BossHeroSkills._cast_r_kenshiro_supremacy]
static func bosshero_cast_r_kenshiro_supremacy(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 70
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")


## hero_skills/_bundle.py:2056-2060 [BossHeroSkills._cast_q_khazan_chained]
static func bosshero_cast_q_khazan_chained(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2062-2076 [BossHeroSkills._cast_w_khazan_leap]
static func bosshero_cast_w_khazan_leap(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "w"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 110)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (90):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2078-2083 [BossHeroSkills._cast_e_khazan_spin]
static func bosshero_cast_e_khazan_spin(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (160):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2085-2092 [BossHeroSkills._cast_r_khazan_vanish]
static func bosshero_cast_r_khazan_vanish(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 75
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.08))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2095-2099 [BossHeroSkills._cast_q_wiro_windcut]
static func bosshero_cast_q_wiro_windcut(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 30
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2101-2106 [BossHeroSkills._cast_w_wiro_whirl]
static func bosshero_cast_w_wiro_whirl(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 45
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (140):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2108-2120 [BossHeroSkills._cast_e_wiro_dash]
static func bosshero_cast_e_wiro_dash(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "e"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 100)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2122-2129 [BossHeroSkills._cast_r_wiro_typhoon]
static func bosshero_cast_r_wiro_typhoon(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 90)


## hero_skills/_bundle.py:2132-2136 [BossHeroSkills._cast_q_naraka_chaos]
static func bosshero_cast_q_naraka_chaos(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2138-2150 [BossHeroSkills._cast_w_naraka_shadowstep]
static func bosshero_cast_w_naraka_shadowstep(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "w"
	(h).active_skill_timer = 50
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 120)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2152-2159 [BossHeroSkills._cast_e_naraka_hammer]
static func bosshero_cast_e_naraka_hammer(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (180):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 30))


## hero_skills/_bundle.py:2161-2172 [BossHeroSkills._cast_r_naraka_execution]
static func bosshero_cast_r_naraka_execution(h, enemies):
	var dmg = null
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (230):
			dmg = int(((h).kit_skill_damage()) * (1.8))
			if (float((e).hp) / float(maxf(1, (e).max_hp))) < (0.3):
				dmg = int((dmg) * (1.6))
			h.kit_hit(e, dmg, (h).team, null, "")
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2179-2183 [BossHeroSkills._cast_q_krognarr_strike]
static func bosshero_cast_q_krognarr_strike(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2185-2192 [BossHeroSkills._cast_w_krognarr_seismic]
static func bosshero_cast_w_krognarr_seismic(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 30))


## hero_skills/_bundle.py:2194-2201 [BossHeroSkills._cast_e_krognarr_rampart]
static func bosshero_cast_e_krognarr_rampart(h, enemies):
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (120):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.9)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.08))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2203-2210 [BossHeroSkills._cast_r_krognarr_eruption]
static func bosshero_cast_r_krognarr_eruption(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 85
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2213-2217 [BossHeroSkills._cast_q_raz_overdrive]
static func bosshero_cast_q_raz_overdrive(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2219-2231 [BossHeroSkills._cast_w_raz_searing]
static func bosshero_cast_w_raz_searing(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "w"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 100)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.4)), (h).team, null, "")


## hero_skills/_bundle.py:2233-2238 [BossHeroSkills._cast_e_raz_surge]
static func bosshero_cast_e_raz_surge(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (160):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2240-2247 [BossHeroSkills._cast_r_raz_gloom]
static func bosshero_cast_r_raz_gloom(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 50))


## hero_skills/_bundle.py:2250-2262 [BossHeroSkills._cast_q_vraskhan_thorned]
static func bosshero_cast_q_vraskhan_thorned(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 90)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2264-2271 [BossHeroSkills._cast_w_vraskhan_leap]
static func bosshero_cast_w_vraskhan_leap(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		(h).global_position.x = float(((h).target).global_position.x)
		(h).global_position.y = float((((h).target).global_position.y) - (20))
		(h).facing = 1 if (((h).target).global_position.x) > ((h).global_position.x) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2273-2278 [BossHeroSkills._cast_e_vraskhan_deathslash]
static func bosshero_cast_e_vraskhan_deathslash(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2280-2287 [BossHeroSkills._cast_r_vraskhan_omni]
static func bosshero_cast_r_vraskhan_omni(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 85
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2290-2294 [BossHeroSkills._cast_q_aurethzar_marksman]
static func bosshero_cast_q_aurethzar_marksman(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2296-2301 [BossHeroSkills._cast_w_aurethzar_piercing]
static func bosshero_cast_w_aurethzar_piercing(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2303-2309 [BossHeroSkills._cast_e_aurethzar_frost]
static func bosshero_cast_e_aurethzar_frost(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.5, 90)


## hero_skills/_bundle.py:2311-2318 [BossHeroSkills._cast_r_aurethzar_thunder]
static func bosshero_cast_r_aurethzar_thunder(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:2325-2329 [BossHeroSkills._cast_q_aeralith_tailwind]
static func bosshero_cast_q_aeralith_tailwind(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2331-2336 [BossHeroSkills._cast_w_aeralith_windblade]
static func bosshero_cast_w_aeralith_windblade(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 45
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2338-2346 [BossHeroSkills._cast_e_aeralith_vacuum]
static func bosshero_cast_e_aeralith_vacuum(h, enemies):
	var d = null

	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		d = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (d) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 90)


## hero_skills/_bundle.py:2348-2353 [BossHeroSkills._cast_r_aeralith_skyrider]
static func bosshero_cast_r_aeralith_skyrider(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (240):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")


## hero_skills/_bundle.py:2356-2360 [BossHeroSkills._cast_q_aurex_shieldcrash]
static func bosshero_cast_q_aurex_shieldcrash(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2362-2366 [BossHeroSkills._cast_w_aurex_voltblast]
static func bosshero_cast_w_aurex_voltblast(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.4)), (h).team, null, "")


## hero_skills/_bundle.py:2368-2375 [BossHeroSkills._cast_e_aurex_aegis]
static func bosshero_cast_e_aurex_aegis(h, enemies):
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (130):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.9)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2377-2384 [BossHeroSkills._cast_r_aurex_spin]
static func bosshero_cast_r_aurex_spin(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 75
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2387-2391 [BossHeroSkills._cast_q_nyxareva_darkslash]
static func bosshero_cast_q_nyxareva_darkslash(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2393-2399 [BossHeroSkills._cast_w_nyxareva_mortalwound]
static func bosshero_cast_w_nyxareva_mortalwound(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.4)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.5, 90)


## hero_skills/_bundle.py:2401-2406 [BossHeroSkills._cast_e_nyxareva_sacrifice]
static func bosshero_cast_e_nyxareva_sacrifice(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2408-2415 [BossHeroSkills._cast_r_nyxareva_avatar]
static func bosshero_cast_r_nyxareva_avatar(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 85
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2418-2422 [BossHeroSkills._cast_q_thalakryon_bolt]
static func bosshero_cast_q_thalakryon_bolt(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2424-2431 [BossHeroSkills._cast_w_thalakryon_aquashield]
static func bosshero_cast_w_thalakryon_aquashield(h, enemies):
	var heal = null

	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.8)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2433-2440 [BossHeroSkills._cast_e_thalakryon_tidalrage]
static func bosshero_cast_e_thalakryon_tidalrage(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 40))


## hero_skills/_bundle.py:2442-2451 [BossHeroSkills._cast_r_thalakryon_metamorph]
static func bosshero_cast_r_thalakryon_metamorph(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (260):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2458-2462 [BossHeroSkills._cast_q_aurelix_timebomb]
static func bosshero_cast_q_aurelix_timebomb(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2464-2468 [BossHeroSkills._cast_w_aurelix_will]
static func bosshero_cast_w_aurelix_will(h, enemies):
	var heal = null

	(h).active_skill = "w"
	(h).active_skill_timer = 60
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2470-2477 [BossHeroSkills._cast_e_aurelix_shockwave]
static func bosshero_cast_e_aurelix_shockwave(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 40))


## hero_skills/_bundle.py:2479-2486 [BossHeroSkills._cast_r_aurelix_transcend]
static func bosshero_cast_r_aurelix_transcend(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 85
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (240):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 90)


## hero_skills/_bundle.py:2489-2494 [BossHeroSkills._cast_q_aurelyssa_whirlwind]
static func bosshero_cast_q_aurelyssa_whirlwind(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (140):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2496-2501 [BossHeroSkills._cast_w_aurelyssa_sweep]
static func bosshero_cast_w_aurelyssa_sweep(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 45
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (160):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2503-2517 [BossHeroSkills._cast_e_aurelyssa_wings]
static func bosshero_cast_e_aurelyssa_wings(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "e"
	(h).active_skill_timer = 55
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 100)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (120):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2519-2526 [BossHeroSkills._cast_r_aurelyssa_phantom]
static func bosshero_cast_r_aurelyssa_phantom(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2529-2533 [BossHeroSkills._cast_q_vargrath_bloodthirst]
static func bosshero_cast_q_vargrath_bloodthirst(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2535-2549 [BossHeroSkills._cast_w_vargrath_charge]
static func bosshero_cast_w_vargrath_charge(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "w"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 110)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (100):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2551-2556 [BossHeroSkills._cast_e_vargrath_devilstrike]
static func bosshero_cast_e_vargrath_devilstrike(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2558-2565 [BossHeroSkills._cast_r_vargrath_souldom]
static func bosshero_cast_r_vargrath_souldom(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 85
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (230):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2568-2573 [BossHeroSkills._cast_q_nazulmor_typhoon]
static func bosshero_cast_q_nazulmor_typhoon(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2575-2582 [BossHeroSkills._cast_w_nazulmor_aquashield]
static func bosshero_cast_w_nazulmor_aquashield(h, enemies):
	var heal = null

	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (150):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.8)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2584-2591 [BossHeroSkills._cast_e_nazulmor_tidalrage]
static func bosshero_cast_e_nazulmor_tidalrage(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 40))


## hero_skills/_bundle.py:2593-2602 [BossHeroSkills._cast_r_nazulmor_chaotic]
static func bosshero_cast_r_nazulmor_chaotic(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (270):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2609-2613 [BossHeroSkills._cast_q_kaeldris_overwhelming]
static func bosshero_cast_q_kaeldris_overwhelming(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2615-2627 [BossHeroSkills._cast_w_kaeldris_press]
static func bosshero_cast_w_kaeldris_press(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "w"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 110)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2629-2634 [BossHeroSkills._cast_e_kaeldris_moment]
static func bosshero_cast_e_kaeldris_moment(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2636-2643 [BossHeroSkills._cast_r_kaeldris_duel]
static func bosshero_cast_r_kaeldris_duel(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2646-2650 [BossHeroSkills._cast_q_pyraklos_spearmars]
static func bosshero_cast_q_pyraklos_spearmars(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2652-2657 [BossHeroSkills._cast_w_pyraklos_rebuke]
static func bosshero_cast_w_pyraklos_rebuke(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2659-2666 [BossHeroSkills._cast_e_pyraklos_bulwark]
static func bosshero_cast_e_pyraklos_bulwark(h, enemies):
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (130):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.7)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2668-2675 [BossHeroSkills._cast_r_pyraklos_arena]
static func bosshero_cast_r_pyraklos_arena(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 85
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (230):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.8)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 60))


## hero_skills/_bundle.py:2678-2684 [BossHeroSkills._cast_q_velmyrth_dagger]
static func bosshero_cast_q_velmyrth_dagger(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 35
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.5, 90)


## hero_skills/_bundle.py:2686-2693 [BossHeroSkills._cast_w_velmyrth_strike]
static func bosshero_cast_w_velmyrth_strike(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		(h).global_position.x = float(((h).target).global_position.x)
		(h).global_position.y = float((((h).target).global_position.y) - (20))
		(h).facing = 1 if (((h).target).global_position.x) > ((h).global_position.x) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2695-2700 [BossHeroSkills._cast_e_velmyrth_blur]
static func bosshero_cast_e_velmyrth_blur(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")


## hero_skills/_bundle.py:2702-2711 [BossHeroSkills._cast_r_velmyrth_coup]
static func bosshero_cast_r_velmyrth_coup(h, enemies):
	var dmg = null

	(h).active_skill = "r"
	(h).active_skill_timer = 80
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			dmg = int(((h).kit_skill_damage()) * (1.8))
			if (float((e).hp) / float(maxf(1, (e).max_hp))) < (0.3):
				dmg = int((dmg) * (1.6))
			h.kit_hit(e, dmg, (h).team, null, "")


## hero_skills/_bundle.py:2714-2718 [BossHeroSkills._cast_q_solvarin_purification]
static func bosshero_cast_q_solvarin_purification(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:2720-2727 [BossHeroSkills._cast_w_solvarin_repel]
static func bosshero_cast_w_solvarin_repel(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (180):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 40))


## hero_skills/_bundle.py:2729-2736 [BossHeroSkills._cast_e_solvarin_degen]
static func bosshero_cast_e_solvarin_degen(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.9)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.4, 90)


## hero_skills/_bundle.py:2738-2747 [BossHeroSkills._cast_r_solvarin_guardian]
static func bosshero_cast_r_solvarin_guardian(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (280):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2750-2754 [BossHeroSkills._cast_q_azureth_arcanebolt]
static func bosshero_cast_q_azureth_arcanebolt(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2756-2761 [BossHeroSkills._cast_w_azureth_concussive]
static func bosshero_cast_w_azureth_concussive(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (170):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:2763-2770 [BossHeroSkills._cast_e_azureth_ancientseal]
static func bosshero_cast_e_azureth_ancientseal(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 100)


## hero_skills/_bundle.py:2772-2779 [BossHeroSkills._cast_r_azureth_mysticflare]
static func bosshero_cast_r_azureth_mysticflare(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 85
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (240):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 65))


## hero_skills/_bundle.py:2782-2786 [BossHeroSkills._cast_q_luminar_illuminate]
static func bosshero_cast_q_luminar_illuminate(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2788-2795 [BossHeroSkills._cast_w_luminar_blindinglight]
static func bosshero_cast_w_luminar_blindinglight(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 45))


## hero_skills/_bundle.py:2797-2802 [BossHeroSkills._cast_e_luminar_wisp]
static func bosshero_cast_e_luminar_wisp(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:2804-2811 [BossHeroSkills._cast_r_luminar_spiritform]
static func bosshero_cast_r_luminar_spiritform(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (280):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2814-2818 [BossHeroSkills._cast_q_solara_starbreaker]
static func bosshero_cast_q_solara_starbreaker(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:2820-2825 [BossHeroSkills._cast_w_solara_celestialhammer]
static func bosshero_cast_w_solara_celestialhammer(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (185):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:2827-2834 [BossHeroSkills._cast_e_solara_luminosity]
static func bosshero_cast_e_solara_luminosity(h, enemies):
	var heal = null

	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.95)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2836-2843 [BossHeroSkills._cast_r_solara_solarguardian]
static func bosshero_cast_r_solara_solarguardian(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (240):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:2846-2853 [BossHeroSkills._cast_q_pyraethis_icarusdive]
static func bosshero_cast_q_pyraethis_icarusdive(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.5))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:2855-2860 [BossHeroSkills._cast_w_pyraethis_firespirits]
static func bosshero_cast_w_pyraethis_firespirits(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2862-2869 [BossHeroSkills._cast_e_pyraethis_sunray]
static func bosshero_cast_e_pyraethis_sunray(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.05)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.35, 90)


## hero_skills/_bundle.py:2871-2880 [BossHeroSkills._cast_r_pyraethis_supernova]
static func bosshero_cast_r_pyraethis_supernova(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (300):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.1)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 80))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2883-2887 [BossHeroSkills._cast_q_auroth_ionicedge]
static func bosshero_cast_q_auroth_ionicedge(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:2889-2896 [BossHeroSkills._cast_w_auroth_ward]
static func bosshero_cast_w_auroth_ward(h, enemies):
	var heal = null

	(h).active_skill = "w"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (185):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.1)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2898-2905 [BossHeroSkills._cast_e_auroth_consecration]
static func bosshero_cast_e_auroth_consecration(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.4, 90)


## hero_skills/_bundle.py:2907-2914 [BossHeroSkills._cast_r_auroth_guardian]
static func bosshero_cast_r_auroth_guardian(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (240):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:2917-2924 [BossHeroSkills._cast_q_morvein_puncture]
static func bosshero_cast_q_morvein_puncture(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.5))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:2926-2931 [BossHeroSkills._cast_w_morvein_violentstrike]
static func bosshero_cast_w_morvein_violentstrike(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:2933-2938 [BossHeroSkills._cast_e_morvein_spectralcharge]
static func bosshero_cast_e_morvein_spectralcharge(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.05)), (h).team, null, "")


## hero_skills/_bundle.py:2940-2947 [BossHeroSkills._cast_r_morvein_phantomform]
static func bosshero_cast_r_morvein_phantomform(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2950-2956 [BossHeroSkills._cast_q_thorvak_seed]
static func bosshero_cast_q_thorvak_seed(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.4, 90)


## hero_skills/_bundle.py:2958-2963 [BossHeroSkills._cast_w_thorvak_natureswrath]
static func bosshero_cast_w_thorvak_natureswrath(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:2965-2970 [BossHeroSkills._cast_e_thorvak_vengeance]
static func bosshero_cast_e_thorvak_vengeance(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:2972-2981 [BossHeroSkills._cast_r_thorvak_dryad]
static func bosshero_cast_r_thorvak_dryad(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))
	heal = int(((h).max_hp) * (0.1))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:2984-2991 [BossHeroSkills._cast_q_yamako_deepforest]
static func bosshero_cast_q_yamako_deepforest(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.4))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:2993-2998 [BossHeroSkills._cast_w_yamako_woodcreation]
static func bosshero_cast_w_yamako_woodcreation(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3000-3007 [BossHeroSkills._cast_e_yamako_woodgolem]
static func bosshero_cast_e_yamako_woodgolem(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 50))


## hero_skills/_bundle.py:3009-3018 [BossHeroSkills._cast_r_yamako_kannon]
static func bosshero_cast_r_yamako_kannon(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (300):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.1)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 80))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3021-3025 [BossHeroSkills._cast_q_ignirus_searingtorrent]
static func bosshero_cast_q_ignirus_searingtorrent(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:3027-3032 [BossHeroSkills._cast_w_ignirus_flameshot]
static func bosshero_cast_w_ignirus_flameshot(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3034-3041 [BossHeroSkills._cast_e_ignirus_burstfireball]
static func bosshero_cast_e_ignirus_burstfireball(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.35, 90)


## hero_skills/_bundle.py:3043-3050 [BossHeroSkills._cast_r_ignirus_vengeance]
static func bosshero_cast_r_ignirus_vengeance(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (280):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:3053-3065 [BossHeroSkills._cast_q_leoric_fearlesscharge]
static func bosshero_cast_q_leoric_fearlesscharge(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 100)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:3067-3072 [BossHeroSkills._cast_w_leoric_sacredhammer]
static func bosshero_cast_w_leoric_sacredhammer(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3074-3081 [BossHeroSkills._cast_e_leoric_concealblast]
static func bosshero_cast_e_leoric_concealblast(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 50))


## hero_skills/_bundle.py:3083-3090 [BossHeroSkills._cast_r_leoric_immortality]
static func bosshero_cast_r_leoric_immortality(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.2))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3093-3103 [BossHeroSkills._cast_q_shirotaka_hiraishin]
static func bosshero_cast_q_shirotaka_hiraishin(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		(h).global_position.x = float(((h).target).global_position.x)
		(h).global_position.y = float((((h).target).global_position.y) - (20))
		(h).facing = 1 if (((h).target).global_position.x) > ((h).global_position.x) else -(1)
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.5))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3105-3112 [BossHeroSkills._cast_w_shirotaka_waterboundary]
static func bosshero_cast_w_shirotaka_waterboundary(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 90)


## hero_skills/_bundle.py:3114-3119 [BossHeroSkills._cast_e_shirotaka_shadowclones]
static func bosshero_cast_e_shirotaka_shadowclones(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3121-3128 [BossHeroSkills._cast_r_shirotaka_paperbomb]
static func bosshero_cast_r_shirotaka_paperbomb(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:3131-3138 [BossHeroSkills._cast_q_seiryukong_boundless]
static func bosshero_cast_q_seiryukong_boundless(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.4))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3140-3145 [BossHeroSkills._cast_w_seiryukong_treedance]
static func bosshero_cast_w_seiryukong_treedance(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:3147-3154 [BossHeroSkills._cast_e_seiryukong_jingusoldiers]
static func bosshero_cast_e_seiryukong_jingusoldiers(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 55))


## hero_skills/_bundle.py:3156-3165 [BossHeroSkills._cast_r_seiryukong_wukong]
static func bosshero_cast_r_seiryukong_wukong(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (300):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.15)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 80))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3168-3180 [BossHeroSkills._cast_q_kaelthorn_bravestfighter]
static func bosshero_cast_q_kaelthorn_bravestfighter(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 110)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:3182-3187 [BossHeroSkills._cast_w_kaelthorn_justiceblade]
static func bosshero_cast_w_kaelthorn_justiceblade(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3189-3194 [BossHeroSkills._cast_e_kaelthorn_defendersassault]
static func bosshero_cast_e_kaelthorn_defendersassault(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3196-3203 [BossHeroSkills._cast_r_kaelthorn_chivalryfists]
static func bosshero_cast_r_kaelthorn_chivalryfists(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.9)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:3206-3210 [BossHeroSkills._cast_q_solvanth_ringpunishment]
static func bosshero_cast_q_solvanth_ringpunishment(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:3212-3219 [BossHeroSkills._cast_w_solvanth_gloriouspathway]
static func bosshero_cast_w_solvanth_gloriouspathway(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.4, 90)


## hero_skills/_bundle.py:3221-3226 [BossHeroSkills._cast_e_solvanth_laworder]
static func bosshero_cast_e_solvanth_laworder(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3228-3235 [BossHeroSkills._cast_r_solvanth_wrath]
static func bosshero_cast_r_solvanth_wrath(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (260):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:3238-3248 [BossHeroSkills._cast_q_xyrael_finch]
static func bosshero_cast_q_xyrael_finch(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		(h).global_position.x = float(((h).target).global_position.x)
		(h).global_position.y = float((((h).target).global_position.y) - (20))
		(h).facing = 1 if (((h).target).global_position.x) > ((h).global_position.x) else -(1)
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.5))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3250-3255 [BossHeroSkills._cast_w_xyrael_defiant]
static func bosshero_cast_w_xyrael_defiant(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3257-3262 [BossHeroSkills._cast_e_xyrael_tempest]
static func bosshero_cast_e_xyrael_tempest(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3264-3271 [BossHeroSkills._cast_r_xyrael_lightness]
static func bosshero_cast_r_xyrael_lightness(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))


## hero_skills/_bundle.py:3276-3280 [BossHeroSkills._cast_q_nyxareth_starsplit]
static func bosshero_cast_q_nyxareth_starsplit(h, enemies):
	(h).active_skill = "1"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:3282-3287 [BossHeroSkills._cast_w_nyxareth_realworld]
static func bosshero_cast_w_nyxareth_realworld(h, enemies):
	(h).active_skill = "2"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:3289-3296 [BossHeroSkills._cast_e_nyxareth_spacetime]
static func bosshero_cast_e_nyxareth_spacetime(h, enemies):
	(h).active_skill = "3"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.05)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 55))


## hero_skills/_bundle.py:3298-3307 [BossHeroSkills._cast_r_nyxareth_astrorealm]
static func bosshero_cast_r_nyxareth_astrorealm(h, enemies):
	var heal = null

	(h).active_skill = "4"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (300):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.2)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 80))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3310-3314 [BossHeroSkills._cast_q_cryssalia_frostshock]
static func bosshero_cast_q_cryssalia_frostshock(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:3316-3323 [BossHeroSkills._cast_w_cryssalia_bitterfrost]
static func bosshero_cast_w_cryssalia_bitterfrost(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 90)


## hero_skills/_bundle.py:3325-3330 [BossHeroSkills._cast_e_cryssalia_frostbites]
static func bosshero_cast_e_cryssalia_frostbites(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (215):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3332-3339 [BossHeroSkills._cast_r_cryssalia_coldest]
static func bosshero_cast_r_cryssalia_coldest(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (280):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 120)


## hero_skills/_bundle.py:3342-3354 [BossHeroSkills._cast_q_kaelthar_chargingfist]
static func bosshero_cast_q_kaelthar_chargingfist(h, enemies):
	var d = null
	var dx = null
	var dy = null
	var step = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		d = Vector2(dx, dy).length()
		if (d) > (1):
			step = minf(d, 110)
			(h).global_position.x = ((h).global_position.x) + ((float(dx) / float(d)) * (step))
			(h).global_position.y = ((h).global_position.y) + ((float(dy) / float(d)) * (step))
			(h).facing = 1 if (dx) > (0) else -(1)
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.3)), (h).team, null, "")


## hero_skills/_bundle.py:3356-3361 [BossHeroSkills._cast_w_kaelthar_quake]
static func bosshero_cast_w_kaelthar_quake(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (190):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:3363-3368 [BossHeroSkills._cast_e_kaelthar_fistcrack]
static func bosshero_cast_e_kaelthar_fistcrack(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.05)), (h).team, null, "")


## hero_skills/_bundle.py:3370-3377 [BossHeroSkills._cast_r_kaelthar_fistbreak]
static func bosshero_cast_r_kaelthar_fistbreak(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (250):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))


## hero_skills/_bundle.py:3380-3384 [BossHeroSkills._cast_q_morkhaera_spiritburst]
static func bosshero_cast_q_morkhaera_spiritburst(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:3386-3391 [BossHeroSkills._cast_w_morkhaera_airstrike]
static func bosshero_cast_w_morkhaera_airstrike(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3393-3400 [BossHeroSkills._cast_e_morkhaera_energyimpact]
static func bosshero_cast_e_morkhaera_energyimpact(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (215):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 55))


## hero_skills/_bundle.py:3402-3409 [BossHeroSkills._cast_r_morkhaera_ethereal]
static func bosshero_cast_r_morkhaera_ethereal(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (280):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3412-3419 [BossHeroSkills._cast_q_aurelion_callcourage]
static func bosshero_cast_q_aurelion_callcourage(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.4))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3421-3426 [BossHeroSkills._cast_w_aurelion_guardianassault]
static func bosshero_cast_w_aurelion_guardianassault(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:3428-3435 [BossHeroSkills._cast_e_aurelion_kingscommand]
static func bosshero_cast_e_aurelion_kingscommand(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (225):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.35, 90)


## hero_skills/_bundle.py:3437-3446 [BossHeroSkills._cast_r_aurelion_kingssummon]
static func bosshero_cast_r_aurelion_kingssummon(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (300):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.2)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 80))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3449-3453 [BossHeroSkills._cast_q_akahime_petalbarrage]
static func bosshero_cast_q_akahime_petalbarrage(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:3455-3462 [BossHeroSkills._cast_w_akahime_soulscroll]
static func bosshero_cast_w_akahime_soulscroll(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.4, 90)


## hero_skills/_bundle.py:3464-3469 [BossHeroSkills._cast_e_akahime_shadow]
static func bosshero_cast_e_akahime_shadow(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3471-3478 [BossHeroSkills._cast_r_akahime_higanbana]
static func bosshero_cast_r_akahime_higanbana(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (270):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:3481-3488 [BossHeroSkills._cast_q_nyxthrael_ambush]
static func bosshero_cast_q_nyxthrael_ambush(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.5))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3490-3495 [BossHeroSkills._cast_w_nyxthrael_nightfall]
static func bosshero_cast_w_nyxthrael_nightfall(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3497-3504 [BossHeroSkills._cast_e_nyxthrael_darknightfall]
static func bosshero_cast_e_nyxthrael_darknightfall(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 55))


## hero_skills/_bundle.py:3506-3513 [BossHeroSkills._cast_r_nyxthrael_shadowbringer]
static func bosshero_cast_r_nyxthrael_shadowbringer(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (260):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))


## hero_skills/_bundle.py:3516-3522 [BossHeroSkills._cast_q_sylvantheros_sprout]
static func bosshero_cast_q_sylvantheros_sprout(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.4, 90)


## hero_skills/_bundle.py:3524-3529 [BossHeroSkills._cast_w_sylvantheros_teleport]
static func bosshero_cast_w_sylvantheros_teleport(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3531-3536 [BossHeroSkills._cast_e_sylvantheros_treants]
static func bosshero_cast_e_sylvantheros_treants(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (215):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3538-3545 [BossHeroSkills._cast_r_sylvantheros_wrath]
static func bosshero_cast_r_sylvantheros_wrath(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (280):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:3548-3555 [BossHeroSkills._cast_q_vaelindra_energywave]
static func bosshero_cast_q_vaelindra_energywave(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.4))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3557-3562 [BossHeroSkills._cast_w_vaelindra_spacering]
static func bosshero_cast_w_vaelindra_spacering(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (215):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")


## hero_skills/_bundle.py:3564-3571 [BossHeroSkills._cast_e_vaelindra_violetrequiem]
static func bosshero_cast_e_vaelindra_violetrequiem(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (230):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.05)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.35, 90)


## hero_skills/_bundle.py:3573-3582 [BossHeroSkills._cast_r_vaelindra_realm]
static func bosshero_cast_r_vaelindra_realm(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (310):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.25)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 80))
	heal = int(((h).max_hp) * (0.12))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3585-3592 [BossHeroSkills._cast_q_astraelion_swordfall]
static func bosshero_cast_q_astraelion_swordfall(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.5))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3594-3599 [BossHeroSkills._cast_w_astraelion_spiritblade]
static func bosshero_cast_w_astraelion_spiritblade(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (195):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3601-3608 [BossHeroSkills._cast_e_astraelion_forceescape]
static func bosshero_cast_e_astraelion_forceescape(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 55))


## hero_skills/_bundle.py:3610-3617 [BossHeroSkills._cast_r_astraelion_zeroreturn]
static func bosshero_cast_r_astraelion_zeroreturn(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (260):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))


## hero_skills/_bundle.py:3620-3624 [BossHeroSkills._cast_q_morvaenthir_soulfragment]
static func bosshero_cast_q_morvaenthir_soulfragment(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")


## hero_skills/_bundle.py:3626-3633 [BossHeroSkills._cast_w_morvaenthir_spiritbind]
static func bosshero_cast_w_morvaenthir_spiritbind(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (205):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")
			if h.kit_has_slow(e):
				h.kit_slow(e, 0.5, 100)


## hero_skills/_bundle.py:3635-3640 [BossHeroSkills._cast_e_morvaenthir_essence]
static func bosshero_cast_e_morvaenthir_essence(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (220):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3642-3649 [BossHeroSkills._cast_r_morvaenthir_shadowrealm]
static func bosshero_cast_r_morvaenthir_shadowrealm(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (290):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 75))


## hero_skills/_bundle.py:3652-3658 [BossHeroSkills._cast_q_thornvaegrim_bramble]
static func bosshero_cast_q_thornvaegrim_bramble(h, enemies):
	(h).active_skill = "q"
	(h).active_skill_timer = 40
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.25)), (h).team, null, "")
		if h.kit_has_slow((h).target):
			h.kit_slow((h).target, 0.4, 90)


## hero_skills/_bundle.py:3660-3665 [BossHeroSkills._cast_w_thornvaegrim_twistedadvance]
static func bosshero_cast_w_thornvaegrim_twistedadvance(h, enemies):
	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (200):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.15)), (h).team, null, "")


## hero_skills/_bundle.py:3667-3672 [BossHeroSkills._cast_e_thornvaegrim_saplingthrow]
static func bosshero_cast_e_thornvaegrim_saplingthrow(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 60
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (215):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.0)), (h).team, null, "")


## hero_skills/_bundle.py:3674-3681 [BossHeroSkills._cast_r_thornvaegrim_grasp]
static func bosshero_cast_r_thornvaegrim_grasp(h, enemies):
	(h).active_skill = "r"
	(h).active_skill_timer = 90
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (270):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.95)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 70))


## hero_skills/_bundle.py:3684-3691 [BossHeroSkills._cast_q_morthraxis_batimpale]
static func bosshero_cast_q_morthraxis_batimpale(h, enemies):
	var dmg = null

	(h).active_skill = "q"
	(h).active_skill_timer = 45
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dmg = int(((h).kit_skill_damage()) * (1.3))
		if (float(((h).target).hp) / float(maxf(1, ((h).target).max_hp))) < (0.3):
			dmg = int((dmg) * (1.4))
		h.kit_hit((h).target, dmg, (h).team, null, "")


## hero_skills/_bundle.py:3693-3700 [BossHeroSkills._cast_w_morthraxis_sanguine]
static func bosshero_cast_w_morthraxis_sanguine(h, enemies):
	var heal = null

	(h).active_skill = "w"
	(h).active_skill_timer = 55
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (210):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
	heal = int(((h).max_hp) * (0.08))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3702-3709 [BossHeroSkills._cast_e_morthraxis_phantommob]
static func bosshero_cast_e_morthraxis_phantommob(h, enemies):
	(h).active_skill = "e"
	(h).active_skill_timer = 65
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (225):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (1.05)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 55))


## hero_skills/_bundle.py:3711-3720 [BossHeroSkills._cast_r_morthraxis_baleful]
static func bosshero_cast_r_morthraxis_baleful(h, enemies):
	var heal = null

	(h).active_skill = "r"
	(h).active_skill_timer = 95
	for e in enemies:
		if (Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()) <= (310):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (2.25)), (h).team, null, "")
			if h.kit_has_atk_timer(e):
				h.kit_lock(e, maxf(h.kit_atk_timer(e), 80))
	heal = int(((h).max_hp) * (0.15))
	(h).hp = minf((h).max_hp, ((h).hp) + (heal))


## hero_skills/_bundle.py:3753-3778 [GrimjawSkills.init_state]
static func grimjaw_init_state(h):
	h.kit["_blade_fury_active"] = false
	h.kit["_blade_fury_timer"] = 0
	h.kit["_heal_ward_active"] = false
	h.kit["_heal_ward_timer"] = 0
	h.kit["_heal_ward_pos"] = [0, 0]
	h.kit["_omnislash_active"] = false
	h.kit["_omnislash_timer"] = 0
	h.kit["_omnislash_target"] = null
	h.kit["_crit_buff_active"] = false
	h.kit["_crit_buff_timer"] = 0
	h.kit["_rage_active"] = false
	h.kit["_rage_timer"] = 0
	h.kit["_war_cry_timer"] = 0


## hero_skills/_bundle.py:3780-3842 [GrimjawSkills.update_timers]
static func grimjaw_update_timers(h, all_units, all_towers, all_bases):
	var d = null
	var dist = null
	var dist_ward = null
	var enemies = null
	var spin_range = null

	if (h.kit.get("_blade_fury_timer", null)) > (0):
		h.kit["_blade_fury_timer"] = (h.kit.get("_blade_fury_timer", null)) - (1)
		if (fmod(h.kit.get("_blade_fury_timer", null), 15)) == (0):
			enemies = h.kit_enemies(all_units, all_towers, all_bases)
			spin_range = (h).skill_data.get("skill_range", 80)
			for e in enemies:
				dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
				if (dist) <= (spin_range):
					h.kit_hit(e, (h).kit_skill_damage(), (h).team, h, "")
		if (h.kit.get("_blade_fury_timer", null)) <= (0):
			h.kit["_blade_fury_active"] = false
	if (h.kit.get("_heal_ward_timer", null)) > (0):
		h.kit["_heal_ward_timer"] = (h.kit.get("_heal_ward_timer", null)) - (1)
		dist_ward = Vector2(((h).global_position.x) - (h.kit.get("_heal_ward_pos", null)[0]), ((h).global_position.y) - (h.kit.get("_heal_ward_pos", null)[1])).length()
		if ((dist_ward) <= (100)) and (((h).hp) < ((h).max_hp)):
			(h).hp = minf((h).max_hp, ((h).hp) + (2))
		for u in all_units:
			if (((u).team) == ((h).team)) and (h.kit_unit_alive(u)) and ((u) != (h)):
				d = Vector2(((u).global_position.x) - (h.kit.get("_heal_ward_pos", null)[0]), ((u).global_position.y) - (h.kit.get("_heal_ward_pos", null)[1])).length()
				if ((d) <= (100)) and (h.kit_has_hp(u)):
					u.hp = minf((u).max_hp, ((u).hp) + (1))
		if (h.kit.get("_heal_ward_timer", null)) <= (0):
			h.kit["_heal_ward_active"] = false
	if (h.kit.get("_omnislash_timer", null)) > (0):
		h.kit["_omnislash_timer"] = (h.kit.get("_omnislash_timer", null)) - (1)
		if (fmod(h.kit.get("_omnislash_timer", null), 8)) == (0):
			if (h.kit.get("_omnislash_target", null)) and (h.kit_unit_alive(h.kit.get("_omnislash_target", null))):
				h.kit_hit(h.kit.get("_omnislash_target", null), int(((h).kit_skill_damage()) * (0.6)), (h).team, h, "")
		if (h.kit.get("_omnislash_timer", null)) <= (0):
			h.kit["_omnislash_active"] = false
			h.kit["_omnislash_target"] = null
	if (h.kit.get("_crit_buff_timer", null)) > (0):
		h.kit["_crit_buff_timer"] = (h.kit.get("_crit_buff_timer", null)) - (1)
		if (h.kit.get("_crit_buff_timer", null)) <= (0):
			h.kit["_crit_buff_active"] = false


## hero_skills/_bundle.py:3848-3863 [GrimjawSkills.cast_q]
static func grimjaw_cast_q(h, all_units, all_towers, all_bases):
	if not (h.skill_timer <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_blade_fury_active"] = true
	h.kit["_blade_fury_timer"] = 180
	__trigger_q(h, "grimjaw", 8, null)
	return true


## hero_skills/_bundle.py:3869-3883 [GrimjawSkills.cast_w]
static func grimjaw_cast_w(h, all_units, all_towers, all_bases):
	if not (h.w_cooldown <= 0):
		return false
	h.kit["_heal_ward_active"] = true
	h.kit["_heal_ward_timer"] = 360
	h.kit["_heal_ward_pos"] = [(h).global_position.x, (h).global_position.y]
	(h).hp = minf((h).max_hp, ((h).hp) + (30))
	__trigger_w(h, "grimjaw", 5, null)
	return true


## hero_skills/_bundle.py:3889-3911 [GrimjawSkills.cast_e]
static func grimjaw_cast_e(h, all_units, all_towers, all_bases):
	if not (h.e_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_crit_buff_active"] = true
	h.kit["_crit_buff_timer"] = 300
	__deal_aoe(h, all_units, all_towers, all_bases, 60, 1.5)
	__trigger_e(h, "grimjaw", 6, null)
	return true


## hero_skills/_bundle.py:3917-3949 [GrimjawSkills.cast_r]
static func grimjaw_cast_r(h, all_units, all_towers, all_bases):
	if not (h.r_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	if ((h).target) and (h.kit_unit_alive((h).target)):
		h.kit["_omnislash_active"] = true
		h.kit["_omnislash_timer"] = 90
		h.kit["_omnislash_target"] = (h).target
		h.kit_hit((h).target, int(((h).kit_skill_damage()) * (2.5)), (h).team, null, "")
	else:
		__deal_aoe(h, all_units, all_towers, all_bases, 150, 2.0)
		h.kit["_omnislash_active"] = true
		h.kit["_omnislash_timer"] = 90
	__trigger_r(h, "grimjaw", 15, null)
	return true


## hero_skills/_bundle.py:3981-3990 [KaizenSkills.init_state]
static func kaizen_init_state(h):
	h.kit["_q_stack"] = 0
	h.kit["_q_reset_timer"] = 0
	h.kit["_is_dashing"] = false
	h.kit["_dash_timer"] = 0
	h.kit["_wind_wall_timer"] = 0
	h.kit["_ulti_active"] = false
	h.kit["_ulti_timer"] = 0


## hero_skills/_bundle.py:3992-4016 [KaizenSkills.update_timers]
static func kaizen_update_timers(h, all_units, all_towers, all_bases):
	if (h.kit.get("_q_reset_timer", null)) > (0):
		h.kit["_q_reset_timer"] = (h.kit.get("_q_reset_timer", null)) - (1)
		if (h.kit.get("_q_reset_timer", null)) <= (0):
			h.kit["_q_stack"] = 0
	if (h.kit.get("_dash_timer", null)) > (0):
		h.kit["_dash_timer"] = (h.kit.get("_dash_timer", null)) - (1)
		if (h.kit.get("_dash_timer", null)) <= (0):
			h.kit["_is_dashing"] = false
	if (h.kit.get("_wind_wall_timer", null)) > (0):
		h.kit["_wind_wall_timer"] = (h.kit.get("_wind_wall_timer", null)) - (1)
	if (h.kit.get("_ulti_timer", null)) > (0):
		h.kit["_ulti_timer"] = (h.kit.get("_ulti_timer", null)) - (1)
		if (h.kit.get("_ulti_timer", null)) <= (0):
			h.kit["_ulti_active"] = false


## hero_skills/_bundle.py:4022-4046 [KaizenSkills.cast_q]
static func kaizen_cast_q(h, all_units, all_towers, all_bases):
	if not (h.skill_timer <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_q_reset_timer"] = 180
	if (h.kit.get("_q_stack", null)) == (0):
		kaizen_cast_steel_wind(h)
		h.kit["_q_stack"] = 1
	else:
		kaizen_cast_dash_strike(h, all_units, all_towers, all_bases)
		h.kit["_q_stack"] = 0
	__trigger_q(h, "kaizen", 8, null)
	return true


## hero_skills/_bundle.py:4048-4054 [KaizenSkills._cast_steel_wind]
static func kaizen_cast_steel_wind(h, all_units, all_towers, all_bases):
	var skill_range = null

	skill_range = (h).skill_data["skill_range"]
	__deal_aoe(h, all_units, all_towers, all_bases, skill_range, 1.0)


## hero_skills/_bundle.py:4056-4079 [KaizenSkills._cast_dash_strike]
static func kaizen_cast_dash_strike(h, all_units, all_towers, all_bases):
	var dist = null
	var dx = null
	var dy = null

	if not ((h).target):
		return null
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) > (0):
		(h).global_position.x = ((h).global_position.x) + ((dx) * (0.7))
		(h).global_position.y = ((h).global_position.y) + ((dy) * (0.7))
		h.kit["_is_dashing"] = true
		h.kit["_dash_timer"] = 15
		__deal_aoe(h, all_units, all_towers, all_bases, 80, 1.5)


## hero_skills/_bundle.py:4085-4092 [KaizenSkills.cast_w]
static func kaizen_cast_w(h, all_units, all_towers, all_bases):
	if not (h.w_cooldown <= 0):
		return false
	h.kit["_wind_wall_timer"] = 180
	__trigger_w(h, "kaizen", 5, null)
	return true


## hero_skills/_bundle.py:4098-4115 [KaizenSkills.cast_e]
static func kaizen_cast_e(h, all_units, all_towers, all_bases):
	if not (h.e_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	__deal_aoe(h, all_units, all_towers, all_bases, 100, 1.0)
	__trigger_e(h, "kaizen", 6, null)
	return true


## hero_skills/_bundle.py:4121-4142 [KaizenSkills.cast_r]
static func kaizen_cast_r(h, all_units, all_towers, all_bases):
	if not (h.r_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_ulti_active"] = true
	h.kit["_ulti_timer"] = 90
	__deal_aoe(h, all_units, all_towers, all_bases, 150, 2.0)
	__trigger_r(h, "kaizen", 15, null)
	return true


## hero_skills/_bundle.py:4173-4193 [SylaraSkills.init_state]
static func sylara_init_state(h):
	h.kit["_focus_fire_active"] = false
	h.kit["_focus_fire_timer"] = 0
	h.kit["_windrun_active"] = false
	h.kit["_windrun_timer"] = 0
	h.kit["_original_speed"] = (float((h).move_speed) / 60.0)
	h.kit["_shackle_active"] = false
	h.kit["_shackle_timer"] = 0
	h.kit["_shackle_target"] = null
	h.kit["_powershot_charging"] = false
	h.kit["_powershot_timer"] = 0


## hero_skills/_bundle.py:4195-4244 [SylaraSkills.update_timers]
static func sylara_update_timers(h, all_units, all_towers, all_bases):
	var stats = null

	if (h.kit.get("_focus_fire_timer", null)) > (0):
		h.kit["_focus_fire_timer"] = (h.kit.get("_focus_fire_timer", null)) - (1)
		if (h.kit.get("_focus_fire_timer", null)) <= (0):
			h.kit["_focus_fire_active"] = false
			stats = h.kit_catalog_all()[(h).hero_type]
			(h).attack_cooldown = float(stats["attack_cooldown"]) / 60.0
	if (h.kit.get("_windrun_timer", null)) > (0):
		h.kit["_windrun_timer"] = (h.kit.get("_windrun_timer", null)) - (1)
		if (h.kit.get("_windrun_timer", null)) <= (0):
			h.kit["_windrun_active"] = false
			(h).move_speed = float(h.kit.get("_original_speed", null)) * 60.0
	if (h.kit.get("_shackle_timer", null)) > (0):
		h.kit["_shackle_timer"] = (h.kit.get("_shackle_timer", null)) - (1)
		if (h.kit.get("_shackle_target", null)) and (h.kit_unit_alive(h.kit.get("_shackle_target", null))):
			if (fmod(h.kit.get("_shackle_timer", null), 15)) == (0):
				h.kit_hit(h.kit.get("_shackle_target", null), int(((h).kit_skill_damage()) * (0.4)), (h).team, null, "")
				if h.kit_has_atk_timer(h.kit.get("_shackle_target", null)):
					h.kit.get("_shackle_target", null).attack_timer = float(30) / 60.0
		else:
			h.kit["_shackle_active"] = false
			h.kit["_shackle_target"] = null
		if (h.kit.get("_shackle_timer", null)) <= (0):
			h.kit["_shackle_active"] = false
			h.kit["_shackle_target"] = null
	if (h.kit.get("_powershot_timer", null)) > (0):
		h.kit["_powershot_timer"] = (h.kit.get("_powershot_timer", null)) - (1)
		if (h.kit.get("_powershot_timer", null)) <= (0):
			h.kit["_powershot_charging"] = false
			sylara_release_powershot(h, all_units, all_towers, all_bases)


## hero_skills/_bundle.py:4250-4306 [SylaraSkills.cast_q]
static func sylara_cast_q(h, all_units, all_towers, all_bases):
	var damage_falloff = null
	var dist = null
	var dx = null
	var dy = null
	var enemies = null
	var ex = null
	var ey = null
	var hit_count = null
	var perp_dist = null
	var proj = null
	var skill_range = null

	if not (h.skill_timer <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_focus_fire_active"] = true
	h.kit["_focus_fire_timer"] = 180
	(h).attack_cooldown = float(maxf(20, int(float(int(roundf(float((h).attack_cooldown) * 60.0))) / float(1.7)))) / 60.0
	if (h).target:
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			dx /= dist
			dy /= dist
			skill_range = (h).skill_data["skill_range"]
			enemies = h.kit_enemies(all_units, all_towers, all_bases)
			hit_count = 0
			for e in enemies:
				ex = ((e).global_position.x) - ((h).global_position.x)
				ey = ((e).global_position.y) - ((h).global_position.y)
				proj = ((ex) * (dx)) + ((ey) * (dy))
				if (0) < (proj) and (proj) < (skill_range):
					perp_dist = absf(((ex) * (-(dy))) + ((ey) * (dx)))
					if (perp_dist) < (15):
						damage_falloff = maxf(0.5, (1.0) - ((hit_count) * (0.15)))
						h.kit_hit(e, int(((h).kit_skill_damage()) * (damage_falloff)), (h).team, null, "")
						hit_count += 1
	__trigger_q(h, "sylara", 8, null)
	return true


## hero_skills/_bundle.py:4312-4328 [SylaraSkills.cast_w]
static func sylara_cast_w(h, all_units, all_towers, all_bases):
	if not (h.w_cooldown <= 0):
		return false
	h.kit["_windrun_active"] = true
	h.kit["_windrun_timer"] = 180
	h.kit["_original_speed"] = (float((h).move_speed) / 60.0)
	(h).move_speed *= float(2.0) * 60.0
	if h.kit_has_hp(h):
		(h).hp = minf((h).max_hp, ((h).hp) + (30))
	__trigger_w(h, "sylara", 5, null)
	return true


## hero_skills/_bundle.py:4334-4385 [SylaraSkills.cast_e]
static func sylara_cast_e(h, all_units, all_towers, all_bases):
	var dist = null
	var enemies = null
	var nearest_dist = null
	var shackle_range = null
	var target = null

	if not (h.e_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	shackle_range = 200
	target = null
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dist = Vector2((((h).target).global_position.x) - ((h).global_position.x), (((h).target).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (shackle_range):
			target = (h).target
	if not (target):
		enemies = h.kit_enemies(all_units, all_towers, all_bases)
		nearest_dist = shackle_range
		for e in enemies:
			dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
			if (dist) < (nearest_dist):
				target = e
				nearest_dist = dist
	if target:
		h.kit["_shackle_active"] = true
		h.kit["_shackle_timer"] = 150
		h.kit["_shackle_target"] = target
		h.kit_hit(target, int(((h).kit_skill_damage()) * (0.7)), (h).team, null, "")
		h.kit_lock(target, 45)
		__trigger_e(h, "sylara", 6, null)
		return true
	else:
		return false


## hero_skills/_bundle.py:4391-4407 [SylaraSkills.cast_r]
static func sylara_cast_r(h, all_units, all_towers, all_bases):
	if not (h.r_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_powershot_charging"] = true
	h.kit["_powershot_timer"] = 60
	__trigger_r(h, "sylara", 15, null)
	return true


## hero_skills/_bundle.py:4409-4461 [SylaraSkills._release_powershot]
static func sylara_release_powershot(h, all_units, all_towers, all_bases):
	var arrow_angle = null
	var arrow_dx = null
	var arrow_dy = null
	var base_angle = null
	var cone_angle = null
	var damage = null
	var dist = null
	var distance_falloff = null
	var dx = null
	var dy = null
	var enemies = null
	var ex = null
	var ey = null
	var hit_enemies = null
	var max_range = null
	var num_arrows = null
	var perp_dist = null
	var proj = null
	var spread = null

	enemies = h.kit_enemies(all_units, all_towers, all_bases)
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dx = (((h).target).global_position.x) - ((h).global_position.x)
		dy = (((h).target).global_position.y) - ((h).global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			dx /= dist
			dy /= dist
		else:
			dx = (h).facing
			dy = 0
	else:
		dx = (h).facing
		dy = 0
	num_arrows = 5
	cone_angle = float(__PI) / float(6)
	max_range = 300
	hit_enemies = {}
	for arrow_i in range(num_arrows):
		spread = ((float(arrow_i) / float((num_arrows) - (1))) - (0.5)) * (cone_angle)
		base_angle = atan2(dy, dx)
		arrow_angle = (base_angle) + (spread)
		arrow_dx = cos(arrow_angle)
		arrow_dy = sin(arrow_angle)
		for e in enemies:
			if (hit_enemies).has(e):
				continue
			ex = ((e).global_position.x) - ((h).global_position.x)
			ey = ((e).global_position.y) - ((h).global_position.y)
			proj = ((ex) * (arrow_dx)) + ((ey) * (arrow_dy))
			if (0) < (proj) and (proj) < (max_range):
				perp_dist = absf(((ex) * (-(arrow_dy))) + ((ey) * (arrow_dx)))
				if (perp_dist) < (20):
					distance_falloff = maxf(0.6, (1.0) - ((float(proj) / float(max_range)) * (0.4)))
					damage = int((((h).kit_skill_damage()) * (1.0)) * (distance_falloff))
					h.kit_hit(e, damage, (h).team, null, "")
					hit_enemies[e] = true
					__spawn_skill_proj(h, e, 13.0)


## hero_skills/_bundle.py:4493-4519 [ThorneSkills.init_state]
static func thorne_init_state(h):
	h.kit["_viscous_nose_active"] = false
	h.kit["_viscous_nose_timer"] = 0
	h.kit["_bristleback_active"] = false
	h.kit["_bristleback_timer"] = 0
	h.kit["_spraying_quills"] = false
	h.kit["_spray_timer"] = 0
	h.kit["_warpath_active"] = false
	h.kit["_warpath_timer"] = 0
	h.kit["_original_damage"] = int((h).damage)
	h.kit["_original_attack_cd"] = int(roundf(float((h).attack_cooldown) * 60.0))
	h.kit["_fortify_active"] = false
	h.kit["_fortify_timer"] = 0
	h.kit["_holy_shield_active"] = false
	h.kit["_holy_shield_timer"] = 0


## hero_skills/_bundle.py:4521-4557 [ThorneSkills.update_timers]
static func thorne_update_timers(h, all_units, all_towers, all_bases):
	var _lvl = null

	if (h.kit.get("_viscous_nose_timer", null)) > (0):
		h.kit["_viscous_nose_timer"] = (h.kit.get("_viscous_nose_timer", null)) - (1)
		if (h.kit.get("_viscous_nose_timer", null)) <= (0):
			h.kit["_viscous_nose_active"] = false
	if (h.kit.get("_bristleback_timer", null)) > (0):
		h.kit["_bristleback_timer"] = (h.kit.get("_bristleback_timer", null)) - (1)
		if (h.kit.get("_bristleback_timer", null)) <= (0):
			h.kit["_bristleback_active"] = false
	if (h.kit.get("_spray_timer", null)) > (0):
		h.kit["_spray_timer"] = (h.kit.get("_spray_timer", null)) - (1)
		if (h.kit.get("_spray_timer", null)) <= (0):
			h.kit["_spraying_quills"] = false
	if (h.kit.get("_warpath_timer", null)) > (0):
		h.kit["_warpath_timer"] = (h.kit.get("_warpath_timer", null)) - (1)
		if (h.kit.get("_warpath_timer", null)) <= (0):
			h.kit["_warpath_active"] = false
			_lvl = h.kit_hero_levels().get((h).level)
			if _lvl:
				(h).damage = float(int(((h).base_damage) * (_lvl["dmg_mult"])))
			(h).attack_cooldown = float(h.kit.get("_original_attack_cd", null)) / 60.0


## hero_skills/_bundle.py:4563-4606 [ThorneSkills.cast_q]
static func thorne_cast_q(h, all_units, all_towers, all_bases):
	var angle_diff = null
	var cone_length = null
	var cone_width = null
	var dist = null
	var dx = null
	var dy = null
	var enemies = null
	var enemy_angle = null
	var facing_angle = null

	if not (h.skill_timer <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_viscous_nose_active"] = true
	h.kit["_viscous_nose_timer"] = 30
	cone_length = 60
	cone_width = float(__PI) / float(3)
	enemies = h.kit_enemies(all_units, all_towers, all_bases)
	for e in enemies:
		dx = ((e).global_position.x) - ((h).global_position.x)
		dy = ((e).global_position.y) - ((h).global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (cone_length):
			continue
		enemy_angle = atan2(dy, dx)
		facing_angle = 0 if ((h).facing) > (0) else __PI
		angle_diff = absf((enemy_angle) - (facing_angle))
		if (angle_diff) > (__PI):
			angle_diff = ((2) * (__PI)) - (angle_diff)
		if (angle_diff) < (float(cone_width) / float(2)):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.8)), (h).team, null, "")
			h.kit_slow(e, 0.4, 180)
	__trigger_q(h, "thorne", 6, null)
	return true


## hero_skills/_bundle.py:4612-4632 [ThorneSkills.cast_w]
static func thorne_cast_w(h, all_units, all_towers, all_bases):
	if not (h.w_cooldown <= 0):
		return false
	h.kit["_bristleback_active"] = true
	h.kit["_bristleback_timer"] = 240
	__deal_aoe(h, all_units, all_towers, all_bases, 60, 0.5)
	if h.kit_has_hp(h):
		(h).hp = minf((h).max_hp, ((h).hp) + (20))
	__trigger_w(h, "thorne", 5, null)
	return true


## hero_skills/_bundle.py:4638-4660 [ThorneSkills.cast_e]
static func thorne_cast_e(h, all_units, all_towers, all_bases):
	if not (h.e_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_spraying_quills"] = true
	h.kit["_spray_timer"] = 30
	__deal_aoe(h, all_units, all_towers, all_bases, 100, 1.2)
	__trigger_e(h, "thorne", 8, null)
	return true


## hero_skills/_bundle.py:4666-4700 [ThorneSkills.cast_r]
static func thorne_cast_r(h, all_units, all_towers, all_bases):
	if not (h.r_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_warpath_active"] = true
	h.kit["_warpath_timer"] = 300
	h.kit["_original_damage"] = int((h).damage)
	h.kit["_original_attack_cd"] = int(roundf(float((h).attack_cooldown) * 60.0))
	(h).damage = float(int((int((h).damage)) * (1.5)))
	(h).attack_cooldown = float(maxf(15, int(float(int(roundf(float((h).attack_cooldown) * 60.0))) / float(1.5)))) / 60.0
	__deal_aoe(h, all_units, all_towers, all_bases, 120, 1.5)
	if h.kit_has_hp(h):
		(h).hp = minf((h).max_hp, ((h).hp) + (50))
	__trigger_r(h, "thorne", 15, null)
	return true


## hero_skills/_bundle.py:4732-4749 [VexSkills.init_state]
static func vex_init_state(h):
	h.kit["_sanity_eclipse_active"] = false
	h.kit["_sanity_eclipse_timer"] = 0
	h.kit["_astral_prison_active"] = false
	h.kit["_astral_prison_timer"] = 0
	h.kit["_astral_prison_target"] = null
	h.kit["_essence_flux_active"] = false
	h.kit["_essence_flux_timer"] = 0


## hero_skills/_bundle.py:4751-4795 [VexSkills.update_timers]
static func vex_update_timers(h, all_units, all_towers, all_bases):
	var dist = null
	var enemies = null

	if (h.kit.get("_sanity_eclipse_timer", null)) > (0):
		h.kit["_sanity_eclipse_timer"] = (h.kit.get("_sanity_eclipse_timer", null)) - (1)
		if (fmod(h.kit.get("_sanity_eclipse_timer", null), 20)) == (0):
			enemies = h.kit_enemies(all_units, all_towers, all_bases)
			for e in enemies:
				dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
				if (30) < (dist) and (dist) <= (55):
					h.kit_hit(e, int(((h).kit_skill_damage()) * (0.4)), (h).team, h, "")
		if (h.kit.get("_sanity_eclipse_timer", null)) <= (0):
			h.kit["_sanity_eclipse_active"] = false
	if (h.kit.get("_astral_prison_timer", null)) > (0):
		h.kit["_astral_prison_timer"] = (h.kit.get("_astral_prison_timer", null)) - (1)
		if (h.kit.get("_astral_prison_target", null)) and (h.kit_unit_alive(h.kit.get("_astral_prison_target", null))):
			h.kit_lock(h.kit.get("_astral_prison_target", null), 15)
			if (fmod(h.kit.get("_astral_prison_timer", null), 10)) == (0):
				h.kit_hit(h.kit.get("_astral_prison_target", null), int(((h).kit_skill_damage()) * (0.3)), (h).team, h, "")
		else:
			h.kit["_astral_prison_active"] = false
			h.kit["_astral_prison_target"] = null
		if (h.kit.get("_astral_prison_timer", null)) <= (0):
			h.kit["_astral_prison_active"] = false
			h.kit["_astral_prison_target"] = null
	if (h.kit.get("_essence_flux_timer", null)) > (0):
		h.kit["_essence_flux_timer"] = (h.kit.get("_essence_flux_timer", null)) - (1)
		if (h.kit.get("_essence_flux_timer", null)) <= (0):
			h.kit["_essence_flux_active"] = false


## hero_skills/_bundle.py:4801-4848 [VexSkills.cast_q]
static func vex_cast_q(h, all_units, all_towers, all_bases):
	var dist = null
	var dx = null
	var dy = null
	var enemies = null
	var ex = null
	var ey = null
	var perp_dist = null
	var proj = null

	if not (h.skill_timer <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	if not ((h).target):
		return false
	if h.kit_unit_alive((h).target):
		__spawn_skill_proj(h, (h).target, 13.0)
	h.kit_hit((h).target, int(((h).kit_skill_damage()) * (1.2)), (h).team, null, "")
	dx = (((h).target).global_position.x) - ((h).global_position.x)
	dy = (((h).target).global_position.y) - ((h).global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) > (0):
		dx /= dist
		dy /= dist
		enemies = h.kit_enemies(all_units, all_towers, all_bases)
		for e in enemies:
			if (e) == ((h).target):
				continue
			ex = ((e).global_position.x) - ((h).global_position.x)
			ey = ((e).global_position.y) - ((h).global_position.y)
			proj = ((ex) * (dx)) + ((ey) * (dy))
			if (0) < (proj) and (proj) < (dist):
				perp_dist = absf(((ex) * (-(dy))) + ((ey) * (dx)))
				if (perp_dist) < (18):
					h.kit_hit(e, int(((h).kit_skill_damage()) * (0.5)), (h).team, null, "")
	__trigger_q(h, "vex", 8, null)
	return true


## hero_skills/_bundle.py:4854-4880 [VexSkills.cast_w]
static func vex_cast_w(h, all_units, all_towers, all_bases):
	var dist = null
	var enemies = null

	if not (h.w_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_sanity_eclipse_active"] = true
	h.kit["_sanity_eclipse_timer"] = 180
	enemies = h.kit_enemies(all_units, all_towers, all_bases)
	for e in enemies:
		dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (60):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.8)), (h).team, null, "")
			h.kit_slow(e, 0.5, 180)
	__trigger_w(h, "vex", 5, null)
	return true


## hero_skills/_bundle.py:4886-4933 [VexSkills.cast_e]
static func vex_cast_e(h, all_units, all_towers, all_bases):
	var dist = null
	var enemies = null
	var nearest_dist = null
	var prison_range = null
	var target = null

	if not (h.e_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	target = null
	prison_range = 200
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dist = Vector2((((h).target).global_position.x) - ((h).global_position.x), (((h).target).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (prison_range):
			target = (h).target
	if not (target):
		enemies = h.kit_enemies(all_units, all_towers, all_bases)
		nearest_dist = prison_range
		for e in enemies:
			dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
			if (dist) < (nearest_dist):
				target = e
				nearest_dist = dist
	if target:
		h.kit["_astral_prison_active"] = true
		h.kit["_astral_prison_timer"] = 150
		h.kit["_astral_prison_target"] = target
		__spawn_skill_proj(h, target, 13.0)
		h.kit_hit(target, int(((h).kit_skill_damage()) * (0.6)), (h).team, null, "")
		__trigger_e(h, "vex", 6, null)
		return true
	else:
		return false


## hero_skills/_bundle.py:4939-4961 [VexSkills.cast_r]
static func vex_cast_r(h, all_units, all_towers, all_bases):
	if not (h.r_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_essence_flux_active"] = true
	h.kit["_essence_flux_timer"] = 60
	__deal_aoe(h, all_units, all_towers, all_bases, 180, 2.5)
	__trigger_r(h, "vex", 15, null)
	return true


## hero_skills/_bundle.py:4992-5014 [ZephyrSkills.init_state]
static func zephyr_init_state(h):
	h.kit["_bramble_active"] = false
	h.kit["_bramble_timer"] = 0
	h.kit["_bramble_origin"] = null
	h.kit["_shadow_realm_active"] = false
	h.kit["_shadow_realm_timer"] = 0
	h.kit["_curse_active"] = false
	h.kit["_curse_timer"] = 0
	h.kit["_curse_target"] = null
	h.kit["_bedlam_active"] = false
	h.kit["_bedlam_timer"] = 0


## hero_skills/_bundle.py:5016-5080 [ZephyrSkills.update_timers]
static func zephyr_update_timers(h, all_units, all_towers, all_bases):
	var dist = null
	var enemies = null
	var ox = null
	var oy = null

	if (h.kit.get("_bramble_timer", null)) > (0):
		h.kit["_bramble_timer"] = (h.kit.get("_bramble_timer", null)) - (1)
		if (fmod(h.kit.get("_bramble_timer", null), 20)) == (0):
			enemies = h.kit_enemies(all_units, all_towers, all_bases)
			ox = __py_or(h.kit.get("_bramble_origin", null), [(h).global_position.x, (h).global_position.y])[0]
			oy = __py_or(h.kit.get("_bramble_origin", null), [(h).global_position.x, (h).global_position.y])[1]
			for e in enemies:
				dist = Vector2(((e).global_position.x) - (ox), ((e).global_position.y) - (oy)).length()
				if (40) < (dist) and (dist) <= (60):
					h.kit_hit(e, int(((h).kit_skill_damage()) * (0.3)), (h).team, h, "")
					h.kit_slow(e, 0.5, 60)
		if (h.kit.get("_bramble_timer", null)) <= (0):
			h.kit["_bramble_active"] = false
			h.kit["_bramble_origin"] = null
	if (h.kit.get("_shadow_realm_timer", null)) > (0):
		h.kit["_shadow_realm_timer"] = (h.kit.get("_shadow_realm_timer", null)) - (1)
		if ((h).hp) < ((h).max_hp):
			(h).hp = minf((h).max_hp, ((h).hp) + (2))
		if (h.kit.get("_shadow_realm_timer", null)) <= (0):
			h.kit["_shadow_realm_active"] = false
	if (h.kit.get("_curse_timer", null)) > (0):
		h.kit["_curse_timer"] = (h.kit.get("_curse_timer", null)) - (1)
		if (h.kit.get("_curse_target", null)) and (h.kit_unit_alive(h.kit.get("_curse_target", null))):
			if (fmod(h.kit.get("_curse_timer", null), 20)) == (0):
				h.kit_hit(h.kit.get("_curse_target", null), int(((h).kit_skill_damage()) * (0.35)), (h).team, h, "")
		else:
			h.kit["_curse_active"] = false
			h.kit["_curse_target"] = null
		if (h.kit.get("_curse_timer", null)) <= (0):
			h.kit["_curse_active"] = false
			h.kit["_curse_target"] = null
	if (h.kit.get("_bedlam_timer", null)) > (0):
		h.kit["_bedlam_timer"] = (h.kit.get("_bedlam_timer", null)) - (1)
		if (fmod(h.kit.get("_bedlam_timer", null), 15)) == (0):
			enemies = h.kit_enemies(all_units, all_towers, all_bases)
			for e in enemies:
				dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
				if (dist) <= (80):
					h.kit_hit(e, int(((h).kit_skill_damage()) * (0.5)), (h).team, h, "")
		if (h.kit.get("_bedlam_timer", null)) <= (0):
			h.kit["_bedlam_active"] = false


## hero_skills/_bundle.py:5086-5118 [ZephyrSkills.cast_q]
static func zephyr_cast_q(h, all_units, all_towers, all_bases):
	var dist = null
	var enemies = null
	var ox = null
	var oy = null
	var target = null

	if not (h.skill_timer <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	target = __acquire_target(h, all_units, all_towers, all_bases, null)
	if (target) == (null):
		return false
	h.kit["_bramble_origin"] = [float((target).global_position.x), float((target).global_position.y)]
	h.kit["_bramble_active"] = true
	h.kit["_bramble_timer"] = 240
	ox = h.kit.get("_bramble_origin", null)[0]
	oy = h.kit.get("_bramble_origin", null)[1]
	enemies = h.kit_enemies(all_units, all_towers, all_bases)
	for e in enemies:
		dist = Vector2(((e).global_position.x) - (ox), ((e).global_position.y) - (oy)).length()
		if (dist) <= (60):
			h.kit_hit(e, int(((h).kit_skill_damage()) * (0.8)), (h).team, null, "")
			h.kit_slow(e, 0.5, 180)
	__trigger_q(h, "zephyr", 8, null)
	return true


## hero_skills/_bundle.py:5124-5138 [ZephyrSkills.cast_w]
static func zephyr_cast_w(h, all_units, all_towers, all_bases):
	if not (h.w_cooldown <= 0):
		return false
	h.kit["_shadow_realm_active"] = true
	h.kit["_shadow_realm_timer"] = 180
	if h.kit_has_hp(h):
		(h).hp = minf((h).max_hp, ((h).hp) + (40))
	__trigger_w(h, "zephyr", 5, null)
	return true


## hero_skills/_bundle.py:5144-5191 [ZephyrSkills.cast_e]
static func zephyr_cast_e(h, all_units, all_towers, all_bases):
	var curse_range = null
	var dist = null
	var enemies = null
	var nearest_dist = null
	var target = null

	if not (h.e_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	target = null
	curse_range = 200
	if ((h).target) and (h.kit_unit_alive((h).target)):
		dist = Vector2((((h).target).global_position.x) - ((h).global_position.x), (((h).target).global_position.y) - ((h).global_position.y)).length()
		if (dist) <= (curse_range):
			target = (h).target
	if not (target):
		enemies = h.kit_enemies(all_units, all_towers, all_bases)
		nearest_dist = curse_range
		for e in enemies:
			dist = Vector2(((e).global_position.x) - ((h).global_position.x), ((e).global_position.y) - ((h).global_position.y)).length()
			if (dist) < (nearest_dist):
				target = e
				nearest_dist = dist
	if target:
		h.kit["_curse_active"] = true
		h.kit["_curse_timer"] = 180
		h.kit["_curse_target"] = target
		h.kit_hit(target, int(((h).kit_skill_damage()) * (0.6)), (h).team, null, "")
		__trigger_e(h, "zephyr", 6, null)
		return true
	else:
		return false


## hero_skills/_bundle.py:5197-5219 [ZephyrSkills.cast_r]
static func zephyr_cast_r(h, all_units, all_towers, all_bases):
	if not (h.r_cooldown <= 0):
		return false
	if not (__has_target(h, all_units, all_towers, all_bases, null)):
		return false
	h.kit["_bedlam_active"] = true
	h.kit["_bedlam_timer"] = 240
	__deal_aoe(h, all_units, all_towers, all_bases, 80, 1.8)
	__trigger_r(h, "zephyr", 15, null)
	return true