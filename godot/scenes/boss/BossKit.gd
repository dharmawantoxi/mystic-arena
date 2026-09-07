# BossKit.gd — DIHASILKAN OTOMATIS. JANGAN EDIT TANGAN.
#
# Sumber: rantai smart-AI boss di bosses/base_boss.py (metode _smart_ai_*
# beserta helper Q/W/E/R yang mereka panggil), ditranspile 1:1 oleh
# tools/gen_boss_smart_ai.py. Regenerasi:
#
#     python tools/gen_boss_smart_ai.py
#
# Semua fungsi di sini STATIC dan menerima `b` = node Boss (Boss.gd).
# State kit hidup di `b.kit` (Dictionary) supaya tidak perlu deklarasi
# ulang di Boss.gd dan tetap satu instans per boss. Timer Q/W/E/R tetap
# SATUAN FRAME seperti pygame (di-tick oleh kode kit sendiri).
#
# Jembatan yang disediakan Boss.gd (semua netral sekolah / frame->detik):
#   b.kit_get_stats()          — _get_boss_stats (skill_down/dmg_scaling/enrage)
#   b.kit_stats_full()         — boss_data mentah (dipakai _l9_stats)
#   b.kit_skill_hit(e, dmg)    — e.take_damage(dmg, self.team)
#   b.kit_apply_slow(e, a, f)  — e.apply_slow(a, f)  (f frame)
#   b.kit_lock_attack(e, f)    — e.attack_timer = max(e.attack_timer, f)
#   b.kit_atk_timer(e)         — baca attack_timer musuh dalam frame
#   b.kit_unit_alive(e)        — e.alive
#   b.kit_has_slow(e)          — hasattr(e, 'apply_slow')
#   b.kit_can_move(e)          — hasattr(e, 'speed')
#   b.kit_fx_cast/kit_fx_impact— pengganti blok FX heroes/*_fx pygame
#
# Blok `try: from heroes import <boss>_fx ...` pygame sengaja dibuang
# generator: itu lapisan visual. Godot memakai kit_fx_cast/kit_fx_impact
# (panggilan cast/impact tetap dipertahankan pada posisi yang sama).
# Paritas yang dijamin file ini adalah PERILAKU (koefisien, target, timing,
# frame) — diverifikasi BossSmartAIParityTest terhadap oracle Pygame.
extends RefCounted


## Dictionary state default untuk b.kit — salin di Boss.gd._ready().
const DEFAULT_KIT := {
	"active_skill": null,
	"active_skill_timer": 30,
	"arcane_buff_active": false,
	"arcane_buff_timer": 360,
	"blink_from_x": 0,
	"blink_from_y": 0,
	"blink_target_x": 0,
	"blink_target_y": 0,
	"blink_to_x": 0,
	"blink_to_y": 0,
	"clones_active_timer": 480,
	"clones_positions": [],
	"cold_feet_target_x": 0,
	"cold_feet_target_y": 0,
	"corrosive_active": false,
	"corrosive_timer": 360,
	"dragon_blood_active": false,
	"dragon_blood_timer": 480,
	"dragon_form_active": false,
	"dragon_form_timer": 600,
	"e_timer": 300,
	"flux_active_timer": 240,
	"flux_target": null,
	"mana_void_x": 0,
	"mana_void_y": 0,
	"mirror_buff_active": false,
	"mirror_buff_timer": 360,
	"morph_buff_active": false,
	"morph_buff_timer": 300,
	"necro_buff_active": false,
	"necro_buff_timer": 480,
	"presence_active": false,
	"presence_timer": 360,
	"q_timer": 240,
	"r_dir_x": 0,
	"r_dir_y": 0,
	"r_timer": 600,
	"rage_active": false,
	"rage_timer": 360,
	"rum_buff_active": false,
	"rum_buff_timer": 480,
	"shell_active": false,
	"shell_timer": 300,
	"shield_active": false,
	"shield_timer": 240,
	"shukuchi_active": false,
	"shukuchi_timer": 180,
	"timelapse_hp_mark": null,
	"timelapse_mark_timer": 0,
	"vortex_active_timer": 180,
	"vortex_x": 0,
	"vortex_y": 0,
	"w_dir_x": 0,
	"w_dir_y": 0,
	"w_target_x": 0,
	"w_target_y": 0,
	"w_timer": 360,
	"x_mark_target": null,
	"x_mark_timer": 120,
	"kit_ready": false,
}


## Dispatch rantai `elif self.boss_type == ...` — URUTAN PERSIS
## Boss.update pygame (tools/gen_boss_smart_ai.py meng-ekstrak urutannya).
static func dispatch(b, boss_type: String, enemies: Array, target_dist: float) -> void:
	if boss_type == "abaddon":
		_smart_ai_abaddon(b, enemies, target_dist)
		return
	if boss_type == "alchemist":
		_smart_ai_alchemist(b, enemies, target_dist)
		return
	if boss_type == "ancient_apparition":
		_smart_ai_ancient_apparition(b, enemies, target_dist)
		return
	if boss_type == "ignis_drachorn":
		_smart_ai_ignis_drachorn(b, enemies, target_dist)
		return
	if boss_type == "gornak":
		_smart_ai_gornak(b, enemies, target_dist)
		return
	if boss_type == "morgath":
		_smart_ai_morgath(b, enemies, target_dist)
		return
	if boss_type == "drakar":
		_smart_ai_drakar(b, enemies, target_dist)
		return
	if boss_type == "razak":
		_smart_ai_razak(b, enemies, target_dist)
		return
	if boss_type == "khalros":
		_smart_ai_khalros(b, enemies, target_dist)
		return
	if boss_type == "gorath":
		_smart_ai_gorath(b, enemies, target_dist)
		return
	if boss_type == "varkul":
		_smart_ai_varkul(b, enemies, target_dist)
		return
	if boss_type == "xerathis":
		_smart_ai_xerathis(b, enemies, target_dist)
		return
	if boss_type == "nyzrak":
		_smart_ai_nyzrak(b, enemies, target_dist)
		return
	if boss_type == "zharok":
		_smart_ai_zharok(b, enemies, target_dist)
		return
	if boss_type == "pyrenth":
		_smart_ai_pyrenth(b, enemies, target_dist)
		return
	if boss_type == "vokrahn":
		_smart_ai_vokrahn(b, enemies, target_dist)
		return
	if boss_type == "nyxara":
		_smart_ai_nyxara(b, enemies, target_dist)
		return
	if boss_type == "gravefang":
		_smart_ai_gravefang(b, enemies, target_dist)
		return
	if boss_type == "vhalzun":
		_smart_ai_vhalzun(b, enemies, target_dist)
		return
	if boss_type == "kunkka":
		_smart_ai_kunkka(b, enemies, target_dist)
		return
	if boss_type == "gravewake":
		_smart_ai_gravewake(b, enemies, target_dist)
		return
	if boss_type == "syrentha":
		_smart_ai_syrentha(b, enemies, target_dist)
		return
	if boss_type == "thalgryn":
		_smart_ai_thalgryn(b, enemies, target_dist)
		return
	if boss_type == "nyxarath":
		_smart_ai_nyxarath(b, enemies, target_dist)
		return
	if boss_type == "vhorethzir":
		_smart_ai_vhorethzir(b, enemies, target_dist)
		return
	if boss_type == "vaerith":
		_smart_ai_vaerith(b, enemies, target_dist)
		return
	if boss_type == "xirthalis":
		_smart_ai_xirthalis(b, enemies, target_dist)
		return
	if boss_type == "vhyssarion":
		_smart_ai_vhyssarion(b, enemies, target_dist)
		return
	if boss_type == "kenshiro":
		_smart_ai_kenshiro(b, enemies, target_dist)
		return
	if boss_type == "khazan":
		_smart_ai_khazan(b, enemies, target_dist)
		return
	if boss_type == "wiro":
		_smart_ai_wiro(b, enemies, target_dist)
		return
	if boss_type == "naraka":
		_smart_ai_naraka(b, enemies, target_dist)
		return
	if boss_type == "krognarr":
		_smart_ai_krognarr(b, enemies, target_dist)
		return
	if boss_type == "raz":
		_smart_ai_raz(b, enemies, target_dist)
		return
	if boss_type == "vraskhan":
		_smart_ai_vraskhan(b, enemies, target_dist)
		return
	if boss_type == "aurethzar":
		_smart_ai_aurethzar(b, enemies, target_dist)
		return
	if boss_type == "aeralith":
		_smart_ai_aeralith(b, enemies, target_dist)
		return
	if boss_type == "aurex":
		_smart_ai_aurex(b, enemies, target_dist)
		return
	if boss_type == "nyxareva":
		_smart_ai_nyxareva(b, enemies, target_dist)
		return
	if boss_type == "thalakryon":
		_smart_ai_thalakryon(b, enemies, target_dist)
		return
	if boss_type == "aurelix":
		_smart_ai_aurelix(b, enemies, target_dist)
		return
	if boss_type == "aurelyssa":
		_smart_ai_aurelyssa(b, enemies, target_dist)
		return
	if boss_type == "vargrath":
		_smart_ai_vargrath(b, enemies, target_dist)
		return
	if boss_type == "nazulmor":
		_smart_ai_nazulmor(b, enemies, target_dist)
		return
	if boss_type == "kaeldris":
		_smart_ai_kaeldris(b, enemies, target_dist)
		return
	if boss_type == "pyraklos":
		_smart_ai_pyraklos(b, enemies, target_dist)
		return
	if boss_type == "velmyrth":
		_smart_ai_velmyrth(b, enemies, target_dist)
		return
	if boss_type == "solvarin":
		_smart_ai_solvarin(b, enemies, target_dist)
		return
	if boss_type == "malzareth":
		_smart_ai_malzareth(b, enemies, target_dist)
		return
	if boss_type == "akashari":
		_smart_ai_akashari(b, enemies, target_dist)
		return
	if boss_type == "vorenmarr":
		_smart_ai_vorenmarr(b, enemies, target_dist)
		return
	if boss_type == "azureth":
		_smart_ai_azureth(b, enemies, target_dist)
		return
	if boss_type == "luminar":
		_smart_ai_luminar(b, enemies, target_dist)
		return
	if boss_type == "solara":
		_smart_ai_solara(b, enemies, target_dist)
		return
	if boss_type == "pyraethis":
		_smart_ai_pyraethis(b, enemies, target_dist)
		return
	if boss_type == "auroth":
		_smart_ai_auroth(b, enemies, target_dist)
		return
	if boss_type == "morvein":
		_smart_ai_morvein(b, enemies, target_dist)
		return
	if boss_type == "thorvak":
		_smart_ai_thorvak(b, enemies, target_dist)
		return
	if boss_type == "yamako":
		_smart_ai_yamako(b, enemies, target_dist)
		return
	if boss_type == "ignirus":
		_smart_ai_ignirus(b, enemies, target_dist)
		return
	if boss_type == "leoric":
		_smart_ai_leoric(b, enemies, target_dist)
		return
	if boss_type == "shirotaka":
		_smart_ai_shirotaka(b, enemies, target_dist)
		return
	if boss_type == "seiryukong":
		_smart_ai_seiryukong(b, enemies, target_dist)
		return
	if boss_type == "kaelthorn":
		_smart_ai_kaelthorn(b, enemies, target_dist)
		return
	if boss_type == "solvanth":
		_smart_ai_solvanth(b, enemies, target_dist)
		return
	if boss_type == "xyrael":
		_smart_ai_xyrael(b, enemies, target_dist)
		return
	if boss_type == "nyxareth":
		_smart_ai_nyxareth(b, enemies, target_dist)
		return
	if boss_type == "cryssalia":
		_smart_ai_cryssalia(b, enemies, target_dist)
		return
	if boss_type == "kaelthar":
		_smart_ai_kaelthar(b, enemies, target_dist)
		return
	if boss_type == "morkhaera":
		_smart_ai_morkhaera(b, enemies, target_dist)
		return
	if boss_type == "aurelion":
		_smart_ai_aurelion(b, enemies, target_dist)
		return
	if boss_type == "akahime":
		_smart_ai_akahime(b, enemies, target_dist)
		return
	if boss_type == "nyxthrael":
		_smart_ai_nyxthrael(b, enemies, target_dist)
		return
	if boss_type == "sylvantheros":
		_smart_ai_sylvantheros(b, enemies, target_dist)
		return
	if boss_type == "vaelindra":
		_smart_ai_vaelindra(b, enemies, target_dist)
		return
	if boss_type == "astraelion":
		_smart_ai_astraelion(b, enemies, target_dist)
		return
	if boss_type == "morvaenthir":
		_smart_ai_morvaenthir(b, enemies, target_dist)
		return
	if boss_type == "thornvaegrim":
		_smart_ai_thornvaegrim(b, enemies, target_dist)
		return
	if boss_type == "morthraxis":
		_smart_ai_morthraxis(b, enemies, target_dist)
		return
	# boss tanpa smart-AI: ability generik ditangani Boss.gd
	return


# ══════════════════════════════════════════════════════════
#  SMART AI PER BOSS — transpile 1:1 dari bosses/base_boss.py
# ══════════════════════════════════════════════════════════
## bosses/base_boss.py:6450-6455 — stat mentah boss_data TANPA
## pengali enrage/skill_down (beda dengan kit_get_stats).
static func _l9_stats(b):
	return b.kit_stats_full()
## bosses/base_boss.py:1107-1156
static func _smart_ai_abaddon(b, enemies, target_dist):
	var hp_ratio = null
	var nearby_count = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
			__g0 += 1
	nearby_count = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.3)) and ((b.kit["w_timer"]) == (0)):
		_cast_w_aphotic_shield(b, enemies)
		return
	if ((nearby_count) >= (3)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_death_sever(b, enemies)
		return
	if ((target_dist) < (130)) and ((b.kit["q_timer"]) == (0)):
		_cast_q_mist_coil(b)
		return
	if ((target_dist) > (100)) and ((b.kit["e_timer"]) == (0)):
		_cast_e_darkness_gale(b)
		return


## bosses/base_boss.py:1229-1286
static func _smart_ai_alchemist(b, enemies, target_dist):
	var hp_ratio = null
	var nearby_count = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["rage_active"] = false
		b.kit["rage_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["rage_active"]:
		b.kit["rage_timer"] -= 1
		if (b.kit["rage_timer"]) <= (0):
			b.kit["rage_active"] = false
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby_count = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby_count) >= (3)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_greevils_greed(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and (not (b.kit["rage_active"])) and ((b.kit["e_timer"]) == (0)):
		_cast_e_chemical_rage(b)
		return
	if ((nearby_count) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_cast_w_unstable_concoction(b, enemies)
		return
	if ((target_dist) < (200)) and ((b.kit["q_timer"]) == (0)):
		_cast_q_acid_spray(b)
		return


## bosses/base_boss.py:1384-1454
static func _smart_ai_ancient_apparition(b, enemies, target_dist):
	var damage = null
	var dist = null
	var hp_ratio = null
	var med_range_count = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["vortex_x"] = 0
		b.kit["vortex_y"] = 0
		b.kit["vortex_active_timer"] = 0
		b.kit["cold_feet_target_x"] = 0
		b.kit["cold_feet_target_y"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if (b.kit["vortex_active_timer"]) > (0):
		b.kit["vortex_active_timer"] -= 1
		if (((b.kit["vortex_active_timer"]) % (20))) == (0):
			stats = b.kit_get_stats()
			damage = int((stats.get("skill_q_damage", 180)) / (3))
			for e in enemies:
				dist = Vector2((e.global_position.x) - (b.kit["vortex_x"]), (e.global_position.y) - (b.kit["vortex_y"])).length()
				if (dist) <= (80):
					b.kit_skill_hit(e, damage)
					if b.kit_has_slow(e):
						b.kit_apply_slow(e, 0.5, 60)
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (300):
			__g0 += 1
	med_range_count = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((med_range_count) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_cold_feet(b, enemies)
		return
	if ((med_range_count) >= (3)) and ((b.kit["q_timer"]) == (0)):
		_cast_q_ice_vortex(b, enemies)
		return
	if ((target_dist) > (250)) and ((b.kit["e_timer"]) == (0)):
		_cast_e_ice_blast(b)
		return
	if ((target_dist) < (320)) and ((b.kit["w_timer"]) == (0)):
		_cast_w_chilling_touch(b, enemies)
		return


## bosses/base_boss.py:1592-1662
static func _smart_ai_ignis_drachorn(b, enemies, target_dist):
	var hp_ratio = null
	var nearby_count = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["dragon_form_active"] = false
		b.kit["dragon_form_timer"] = 0
		b.kit["dragon_blood_active"] = false
		b.kit["dragon_blood_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["dragon_form_active"]:
		b.kit["dragon_form_timer"] -= 1
		if (b.kit["dragon_form_timer"]) <= (0):
			b.kit["dragon_form_active"] = false
			stats = b.kit_get_stats()
			b.damage = stats.get("damage", 120)
	if b.kit["dragon_blood_active"]:
		b.kit["dragon_blood_timer"] -= 1
		if (b.kit["dragon_blood_timer"]) <= (0):
			b.kit["dragon_blood_active"] = false
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby_count = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.5)) and ((nearby_count) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_elder_dragon_form(b, enemies)
		return
	if ((hp_ratio) < (0.65)) and (not (b.kit["dragon_blood_active"])) and ((b.kit["e_timer"]) == (0)):
		_cast_e_dragon_blood(b)
		return
	if ((nearby_count) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_cast_w_dragon_tail(b, enemies)
		return
	if ((target_dist) < (220)) and ((b.kit["q_timer"]) == (0)):
		_cast_q_dragon_breath(b, enemies)
		return


## bosses/base_boss.py:1827-1875
static func _smart_ai_vhorethzir(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["corrosive_active"] = false
		b.kit["corrosive_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["corrosive_active"]:
		b.kit["corrosive_timer"] -= 1
		if (b.kit["corrosive_timer"]) <= (0):
			b.kit["corrosive_active"] = false
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_vhorethzir_r(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and (not (b.kit["corrosive_active"])) and ((b.kit["e_timer"]) == (0)):
		_vhorethzir_e(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_vhorethzir_w(b, enemies)
		return
	if ((target_dist) < (280)) and ((b.kit["q_timer"]) == (0)):
		_vhorethzir_q(b, enemies)
		return


## bosses/base_boss.py:2018-2057
static func _smart_ai_vaerith(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.45)) and ((b.kit["r_timer"]) == (0)):
		_vaerith_r(b, enemies)
		return
	if ((hp_ratio) < (0.7)) and ((b.kit["e_timer"]) == (0)):
		_vaerith_e(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_vaerith_w(b, enemies)
		return
	if ((target_dist) < (260)) and ((b.kit["q_timer"]) == (0)):
		_vaerith_q(b, enemies)
		return


## bosses/base_boss.py:2187-2246
static func _smart_ai_xirthalis(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["shukuchi_active"] = false
		b.kit["shukuchi_timer"] = 0
		b.kit["timelapse_hp_mark"] = null
		b.kit["timelapse_mark_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["shukuchi_active"]:
		b.kit["shukuchi_timer"] -= 1
		if (b.kit["shukuchi_timer"]) <= (0):
			b.kit["shukuchi_active"] = false
			stats = b.kit_get_stats()
			b.move_speed = (stats.get("speed", 1.15)) * 60.0
	b.kit["timelapse_mark_timer"] = (b.kit["timelapse_mark_timer"]) + (1)
	if (b.kit["timelapse_mark_timer"]) >= (300):
		b.kit["timelapse_mark_timer"] = 0
		b.kit["timelapse_hp_mark"] = b.hp
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((b.kit["r_timer"]) == (0)):
		_xirthalis_r(b, enemies)
		return
	if ((hp_ratio) < (0.65)) and (not (b.kit["shukuchi_active"])) and ((b.kit["q_timer"]) == (0)):
		_xirthalis_q(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_xirthalis_w(b, enemies)
		return
	if ((target_dist) < (250)) and ((b.kit["e_timer"]) == (0)):
		_xirthalis_e(b, enemies)
		return


## bosses/base_boss.py:2365-2404
static func _smart_ai_vhyssarion(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.45)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_vhyssarion_r(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["q_timer"]) == (0)):
		_vhyssarion_q(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		_vhyssarion_e(b, enemies)
		return
	if ((target_dist) < (270)) and ((b.kit["w_timer"]) == (0)):
		_vhyssarion_w(b, enemies)
		return


## bosses/base_boss.py:2522-2578
static func _smart_ai_gornak(b, enemies, target_dist):
	var hp_ratio = null
	var nearby_count = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["blink_target_x"] = 0
		b.kit["blink_target_y"] = 0
		b.kit["mana_void_x"] = 0
		b.kit["mana_void_y"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
			__g0 += 1
	nearby_count = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_mana_void(b, enemies)
		return
	if ((target_dist) > (120)) and ((b.kit["w_timer"]) == (0)):
		_cast_w_blink(b)
		return
	if ((nearby_count) >= (3)) and ((b.kit["e_timer"]) == (0)):
		_cast_e_counterspell(b, enemies)
		return
	if ((target_dist) < (200)) and ((b.kit["q_timer"]) == (0)):
		_cast_q_mana_break(b)
		return


## bosses/base_boss.py:2663-2741
static func _smart_ai_morgath(b, enemies, target_dist):
	var clone_damage = null
	var close_count = null
	var dot_damage = null
	var hp_ratio = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["flux_target"] = null
		b.kit["flux_active_timer"] = 0
		b.kit["clones_active_timer"] = 0
		b.kit["clones_positions"] = []
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if (b.kit["flux_active_timer"]) > (0):
		b.kit["flux_active_timer"] -= 1
		if (((b.kit["flux_active_timer"]) % (30))) == (0):
			if (b.kit["flux_target"]) and (b.kit_unit_alive(b.kit["flux_target"])):
				stats = b.kit_get_stats()
				dot_damage = int((stats.get("skill_w_damage", 150)) / (4))
				b.kit_skill_hit(b.kit["flux_target"], dot_damage)
				if b.kit_has_slow(b.kit["flux_target"]):
					b.kit_apply_slow(b.kit["flux_target"], 0.4, 60)
	if (b.kit["clones_active_timer"]) > (0):
		b.kit["clones_active_timer"] -= 1
		if (((b.kit["clones_active_timer"]) % (40))) == (0):
			if (b.target) and (b.kit_unit_alive(b.target)):
				stats = b.kit_get_stats()
				clone_damage = int((b.damage) * (0.5))
				b.kit_skill_hit(b.target, clone_damage)
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	close_count = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.5)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_tempest_double(b)
		return
	if ((close_count) >= (2)) and ((b.kit["e_timer"]) == (0)):
		_cast_e_magnetic_field(b, enemies)
		return
	if ((target_dist) < (300)) and ((b.kit["w_timer"]) == (0)) and ((b.kit["flux_active_timer"]) <= (0)):
		_cast_w_flux(b)
		return
	if ((target_dist) < (350)) and ((b.kit["q_timer"]) == (0)):
		_cast_q_spark_wraith(b)
		return


## bosses/base_boss.py:2825-2903
static func _smart_ai_drakar(b, enemies, target_dist):
	var hp_ratio = null
	var low_hp_target = null
	var nearby_count = null
	var stats = null
	var target_hp_ratio = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["rage_active"] = false
		b.kit["rage_timer"] = 0
		b.defense_boost = false
		b.defense_timer = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["rage_active"]:
		b.kit["rage_timer"] -= 1
		if (b.kit["rage_timer"]) <= (0):
			b.kit["rage_active"] = false
			stats = b.kit_get_stats()
			b.damage = stats.get("damage", 80)
	if b.defense_boost:
		b.defense_timer -= 1
		if (b.defense_timer) <= (0):
			b.defense_boost = false
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (120):
			__g0 += 1
	nearby_count = __g0
	low_hp_target = null
	if (b.target) and (b.kit_unit_alive(b.target)):
		target_hp_ratio = float(b.target.hp) / float(b.target.max_hp)
		if (target_hp_ratio) < (0.3):
			low_hp_target = b.target
	hp_ratio = float(b.hp) / float(b.max_hp)
	if (low_hp_target) and ((target_dist) < (100)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_culling_blade(b)
		return
	if ((hp_ratio) < (0.4)) and (not (b.kit["rage_active"])) and ((b.kit["q_timer"]) == (0)):
		_cast_q_battle_hunger(b)
		return
	if ((nearby_count) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_cast_w_counter_helix(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and (not (b.defense_boost)) and ((b.kit["e_timer"]) == (0)):
		_cast_e_berserkers_call(b, enemies)
		return


## bosses/base_boss.py:2998-3029
static func _smart_ai_razak(b, enemies, target_dist):
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby = __g0
	if ((nearby) >= (3)) and ((b.kit["r_timer"]) == (0)):
		_razak_r(b, enemies)
		return
	if ((target_dist) > (120)) and ((target_dist) < (260)) and ((b.kit["e_timer"]) == (0)):
		_razak_e(b, enemies)
		return
	if ((target_dist) <= (220)) and ((b.kit["w_timer"]) == (0)):
		_razak_w(b, enemies)
		return
	if ((target_dist) <= (260)) and ((b.kit["q_timer"]) == (0)):
		_razak_q(b, enemies)
		return


## bosses/base_boss.py:3124-3156
static func _smart_ai_khalros(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (140):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((b.kit["r_timer"]) == (0)):
		_khalros_r(b, enemies)
		return
	if ((hp_ratio) < (0.7)) and ((b.kit["w_timer"]) == (0)):
		_khalros_w(b, enemies)
		return
	if ((target_dist) > (110)) and ((b.kit["e_timer"]) == (0)):
		_khalros_e(b, enemies)
		return
	if ((target_dist) <= (260)) and ((b.kit["q_timer"]) == (0)):
		_khalros_q(b, enemies)
		return


## bosses/base_boss.py:3227-3276
static func _smart_ai_gorath(b, enemies, target_dist):
	var hp_ratio = null
	var low_hp_target = null
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["rage_active"] = false
		b.kit["rage_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["rage_active"]:
		b.kit["rage_timer"] -= 1
		if (b.kit["rage_timer"]) <= (0):
			b.kit["rage_active"] = false
			stats = b.kit_get_stats()
			b.damage = stats.get("damage", 94)
			b.move_speed = (stats.get("speed", 1.18)) * 60.0
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	low_hp_target = (b.target) and (b.kit_unit_alive(b.target)) and ((float(b.target.hp) / float(maxf(1, b.target.max_hp))) < (0.35))
	if (low_hp_target) and ((b.kit["r_timer"]) == (0)):
		_gorath_r(b, enemies)
		return
	if (not (b.kit["rage_active"])) and ((hp_ratio) < (0.7)) and ((b.kit["q_timer"]) == (0)):
		_gorath_q(b)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_gorath_w(b, enemies)
		return
	if ((target_dist) > (90)) and ((b.kit["e_timer"]) == (0)):
		_gorath_e(b, enemies)
		return
	if ((hp_ratio) < (0.45)) and ((b.kit["r_timer"]) == (0)):
		_gorath_r(b, enemies)
		return


## bosses/base_boss.py:3373-3405
static func _smart_ai_varkul(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((b.kit["r_timer"]) == (0)):
		_varkul_r(b, enemies)
		return
	if ((hp_ratio) < (0.5)) and ((b.kit["e_timer"]) == (0)):
		_varkul_e(b)
		return
	if ((target_dist) <= (250)) and ((b.kit["w_timer"]) == (0)):
		_varkul_w(b, enemies)
		return
	if ((target_dist) <= (280)) and ((b.kit["q_timer"]) == (0)):
		_varkul_q(b)
		return


## bosses/base_boss.py:3491-3529
static func _smart_ai_xerathis(b, enemies, target_dist):
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["arcane_buff_active"] = false
		b.kit["arcane_buff_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["arcane_buff_active"]:
		b.kit["arcane_buff_timer"] -= 1
		if (b.kit["arcane_buff_timer"]) <= (0):
			b.kit["arcane_buff_active"] = false
			b.damage = b.base_damage
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			__g0 += 1
	nearby = __g0
	if ((nearby) >= (4)) and ((b.kit["r_timer"]) == (0)):
		_xerathis_r(b, enemies)
		return
	if (not (b.kit["arcane_buff_active"])) and ((b.kit["e_timer"]) == (0)):
		_xerathis_e(b)
		return
	if ((nearby) >= (2)) and ((b.kit["q_timer"]) == (0)):
		_xerathis_q(b, enemies)
		return
	if ((target_dist) <= (280)) and ((b.kit["w_timer"]) == (0)):
		_xerathis_w(b)
		return


## bosses/base_boss.py:3619-3657
static func _smart_ai_nyzrak(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["shield_active"] = false
		b.kit["shield_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["shield_active"]:
		b.kit["shield_timer"] -= 1
		if (b.kit["shield_timer"]) <= (0):
			b.kit["shield_active"] = false
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.45)) and (not (b.kit["shield_active"])) and ((b.kit["r_timer"]) == (0)):
		_nyzrak_r(b, enemies)
		return
	if ((target_dist) <= (220)) and ((b.kit["e_timer"]) == (0)):
		_nyzrak_e(b)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_nyzrak_w(b, enemies)
		return
	if ((target_dist) <= (260)) and ((b.kit["q_timer"]) == (0)):
		_nyzrak_q(b)
		return


## bosses/base_boss.py:3756-3787
static func _smart_ai_zharok(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	hp_ratio = float(b.hp) / float(b.max_hp)
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	if ((hp_ratio) < (0.4)) and ((b.kit["r_timer"]) == (0)):
		_cast_zharok_r(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		_cast_zharok_e(b, enemies)
		return
	if ((target_dist) < (200)) and ((b.kit["w_timer"]) == (0)):
		_cast_zharok_w(b)
		return
	if ((target_dist) < (250)) and ((b.kit["q_timer"]) == (0)):
		_cast_zharok_q(b)
		return


## bosses/base_boss.py:3866-3897
static func _smart_ai_pyrenth(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	hp_ratio = float(b.hp) / float(b.max_hp)
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby = __g0
	if ((hp_ratio) < (0.4)) and ((b.kit["r_timer"]) == (0)):
		_cast_pyrenth_r(b, enemies)
		return
	if ((nearby) >= (3)) and ((b.kit["e_timer"]) == (0)):
		_cast_pyrenth_e(b, enemies)
		return
	if ((b.kit["w_timer"]) == (0)) and ((hp_ratio) < (0.6)):
		_cast_pyrenth_w(b)
		return
	if ((target_dist) < (200)) and ((b.kit["q_timer"]) == (0)):
		_cast_pyrenth_q(b)
		return


## bosses/base_boss.py:3966-3997
static func _smart_ai_vokrahn(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	hp_ratio = float(b.hp) / float(b.max_hp)
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	if ((hp_ratio) < (0.5)) and ((b.kit["r_timer"]) == (0)):
		_cast_vokrahn_r(b, enemies)
		return
	if ((nearby) >= (3)) and ((b.kit["w_timer"]) == (0)):
		_cast_vokrahn_w(b, enemies)
		return
	if ((target_dist) < (200)) and ((b.kit["e_timer"]) == (0)):
		_cast_vokrahn_e(b)
		return
	if (b.kit["q_timer"]) == (0):
		_cast_vokrahn_q(b)
		return


## bosses/base_boss.py:4081-4251
static func _smart_ai_nyxara(b, enemies, target_dist):
	var damage = null
	var distance = null
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	for attr in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if (b.kit[attr]) > (0):
			b.kit[attr] = (b.kit[attr]) - (1)
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	stats = b.kit_get_stats()
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			__g0 += 1
	nearby = __g0
	if (b.target) and ((float(b.hp) / float(b.max_hp)) < (0.55)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 560)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		b.kit_fx_cast("r")
		damage = stats.get("skill_r_damage", 320)
		b.kit_skill_hit(b.target, damage)
		b.hp = minf(b.max_hp, (b.hp) + (int((b.max_hp) * (0.135))))
		return
	if ((nearby) >= (3)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 80
		b.kit_fx_cast("e")
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 100, "e")
		for enemy in enemies:
			distance = Vector2((enemy.global_position.x) - (b.global_position.x), (enemy.global_position.y) - (b.global_position.y)).length()
			if (distance) <= (100):
				b.kit_skill_hit(enemy, stats.get("skill_e_damage", 160))
		return
	if (b.target) and ((target_dist) <= (280)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 70
		b.kit_fx_cast("w")
		b.kit_skill_hit(b.target, stats.get("skill_w_damage", 140))
		if "attack_timer" in b.target:
			b.kit_lock_attack(b.target, maxf(b.kit_atk_timer(b.target), 75))
		return
	if (b.target) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 60
		b.kit_fx_cast("q")
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 130, "q")
		b.kit_skill_hit(b.target, stats.get("skill_q_damage", 220))


## bosses/base_boss.py:4253-4340
static func _smart_ai_gravefang(b, enemies, target_dist):
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	for attr in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if (b.kit[attr]) > (0):
			b.kit[attr] = (b.kit[attr]) - (1)
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	stats = b.kit_get_stats()
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby = __g0
	if (((nearby) >= (3)) or ((float(b.hp) / float(b.max_hp)) < (0.35))) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 620)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 100
		b.kit_fx_cast("r")
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 180, "r")
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
				b.kit_skill_hit(e, stats.get("skill_r_damage", 380))
		return
	if (b.target) and ((target_dist) > (90)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 70
		b.kit_fx_cast("w")
		b.kit_skill_hit(b.target, stats.get("skill_w_damage", 240))
		return
	if (b.target) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 70
		b.kit_fx_cast("e")
		b.kit_skill_hit(b.target, stats.get("skill_e_damage", 190))
		if "attack_timer" in b.target:
			b.kit_lock_attack(b.target, maxf(b.kit_atk_timer(b.target), 60))
		return
	if ((nearby) >= (2)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 60
		b.kit_fx_cast("q")
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 120, "q")
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (120):
				b.kit_skill_hit(e, stats.get("skill_q_damage", 260))


## bosses/base_boss.py:4342-4437
static func _smart_ai_vhalzun(b, enemies, target_dist):
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	for attr in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if (b.kit[attr]) > (0):
			b.kit[attr] = (b.kit[attr]) - (1)
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["active_skill"]:
		return
	stats = b.kit_get_stats()
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			__g0 += 1
	nearby = __g0
	if ((float(b.hp) / float(b.max_hp)) < (0.4)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 620)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 100
		b.hp = minf(b.max_hp, (b.hp) + (int((b.max_hp) * (0.18))))
		b.kit_fx_cast("r")
		return
	if ((nearby) >= (3)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 80
		b.kit_fx_cast("w")
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 150, "w")
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
				b.kit_skill_hit(e, stats.get("skill_w_damage", 170))
		return
	if (b.target) and ((target_dist) > (96)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 320)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		b.kit_fx_cast("e")
		b.kit_skill_hit(b.target, stats.get("skill_e_damage", 280))
		return
	if (b.target) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 60
		b.kit_fx_cast("q")
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 130, "q")
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (130):
				b.kit_skill_hit(e, stats.get("skill_q_damage", 230))


## bosses/base_boss.py:4442-4468
static func _smart_ai_malzareth(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	for attr in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if (b.kit[attr]) > (0):
			b.kit[attr] = (b.kit[attr]) - (1)
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_malzareth_r(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_malzareth_w(b, enemies)
		return
	if ((target_dist) < (260)) and ((b.kit["e_timer"]) == (0)):
		_malzareth_e(b, enemies)
		return
	if ((target_dist) < (280)) and ((b.kit["q_timer"]) == (0)):
		_malzareth_q(b, enemies)
		return


## bosses/base_boss.py:4530-4556
static func _smart_ai_akashari(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	for attr in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if (b.kit[attr]) > (0):
			b.kit[attr] = (b.kit[attr]) - (1)
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_akashari_r(b, enemies)
		return
	if ((nearby) >= (3)) and ((b.kit["e_timer"]) == (0)):
		_akashari_e(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and ((b.kit["w_timer"]) == (0)):
		_akashari_w(b, enemies)
		return
	if ((target_dist) < (280)) and ((b.kit["q_timer"]) == (0)):
		_akashari_q(b, enemies)
		return


## bosses/base_boss.py:4622-4648
static func _smart_ai_vorenmarr(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true
	for attr in ["q_timer", "w_timer", "e_timer", "r_timer"]:
		if (b.kit[attr]) > (0):
			b.kit[attr] = (b.kit[attr]) - (1)
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_vorenmarr_r(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and ((b.kit["w_timer"]) == (0)):
		_vorenmarr_w(b)
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		_vorenmarr_e(b, enemies)
		return
	if ((target_dist) < (280)) and ((b.kit["q_timer"]) == (0)):
		_vorenmarr_q(b, enemies)
		return


## bosses/base_boss.py:4718-4776
static func _smart_ai_nyxarath(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["necro_buff_active"] = false
		b.kit["necro_buff_timer"] = 0
		b.kit["presence_active"] = false
		b.kit["presence_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["necro_buff_active"]:
		b.kit["necro_buff_timer"] -= 1
		if (b.kit["necro_buff_timer"]) <= (0):
			b.kit["necro_buff_active"] = false
			stats = b.kit_get_stats()
			b.damage = stats.get("damage", 130)
	if b.kit["presence_active"]:
		b.kit["presence_timer"] -= 1
		if (b.kit["presence_timer"]) <= (0):
			b.kit["presence_active"] = false
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_nyxarath_r(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and (not (b.kit["presence_active"])) and ((b.kit["e_timer"]) == (0)):
		_nyxarath_e(b, enemies)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_nyxarath_w(b, enemies)
		return
	if ((target_dist) < (280)) and ((b.kit["q_timer"]) == (0)):
		_nyxarath_q(b, enemies)
		return


## bosses/base_boss.py:4951-5001
static func _smart_ai_thalgryn(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["morph_buff_active"] = false
		b.kit["morph_buff_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["morph_buff_active"]:
		b.kit["morph_buff_timer"] -= 1
		if (b.kit["morph_buff_timer"]) <= (0):
			b.kit["morph_buff_active"] = false
			stats = b.kit_get_stats()
			b.damage = stats.get("damage", 92)
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_thalgryn_r(b, enemies)
		return
	if ((hp_ratio) < (0.55)) and (not (b.kit["morph_buff_active"])) and ((b.kit["e_timer"]) == (0)):
		_thalgryn_e(b)
		return
	if ((target_dist) > (150)) and ((b.kit["q_timer"]) == (0)):
		_thalgryn_q(b, enemies)
		return
	if ((target_dist) < (280)) and ((b.kit["w_timer"]) == (0)):
		_thalgryn_w(b, enemies)
		return


## bosses/base_boss.py:5175-5225
static func _smart_ai_syrentha(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["mirror_buff_active"] = false
		b.kit["mirror_buff_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["mirror_buff_active"]:
		b.kit["mirror_buff_timer"] -= 1
		if (b.kit["mirror_buff_timer"]) <= (0):
			b.kit["mirror_buff_active"] = false
			stats = b.kit_get_stats()
			b.damage = stats.get("damage", 98)
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.45)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_syrentha_r(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and (not (b.kit["mirror_buff_active"])) and ((b.kit["e_timer"]) == (0)):
		_syrentha_e(b)
		return
	if ((nearby) >= (3)) and ((b.kit["w_timer"]) == (0)):
		_syrentha_w(b, enemies)
		return
	if ((target_dist) < (260)) and ((b.kit["q_timer"]) == (0)):
		_syrentha_q(b, enemies)
		return


## bosses/base_boss.py:5401-5448
static func _smart_ai_gravewake(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["shell_active"] = false
		b.kit["shell_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["shell_active"]:
		b.kit["shell_timer"] -= 1
		if (b.kit["shell_timer"]) <= (0):
			b.kit["shell_active"] = false
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_gravewake_r(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and (not (b.kit["shell_active"])) and ((b.kit["e_timer"]) == (0)):
		_gravewake_e(b)
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_gravewake_w(b, enemies)
		return
	if ((target_dist) < (220)) and ((b.kit["q_timer"]) == (0)):
		_gravewake_q(b, enemies)
		return


## bosses/base_boss.py:5630-5712
static func _smart_ai_kunkka(b, enemies, target_dist):
	var damage = null
	var hp_ratio = null
	var nearby_count = null
	var stats = null

	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["rum_buff_active"] = false
		b.kit["rum_buff_timer"] = 0
		b.kit["x_mark_target"] = null
		b.kit["x_mark_timer"] = 0
		b.kit["kit_ready"] = true
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null
	if b.kit["rum_buff_active"]:
		b.kit["rum_buff_timer"] -= 1
		if (b.kit["rum_buff_timer"]) <= (0):
			b.kit["rum_buff_active"] = false
			stats = b.kit_get_stats()
			b.damage = stats.get("damage", 125)
	if (b.kit["x_mark_timer"]) > (0):
		b.kit["x_mark_timer"] -= 1
		if ((b.kit["x_mark_timer"]) <= (0)) and (b.kit["x_mark_target"]):
			if b.kit_unit_alive(b.kit["x_mark_target"]):
				stats = b.kit_get_stats()
				damage = stats.get("skill_w_damage", 300)
				for e in enemies:
					if (Vector2((e.global_position.x) - (b.kit["x_mark_target"].global_position.x), (e.global_position.y) - (b.kit["x_mark_target"].global_position.y)).length()) <= (120):
						b.kit_skill_hit(e, damage)
						if "attack_timer" in e:
							b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 60))
			b.kit["x_mark_target"] = null
	var __g0 := 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			__g0 += 1
	nearby_count = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((hp_ratio) < (0.4)) and ((nearby_count) >= (2)) and ((b.kit["r_timer"]) == (0)):
		_cast_r_torrent(b, enemies)
		return
	if ((hp_ratio) < (0.6)) and (not (b.kit["rum_buff_active"])) and ((b.kit["e_timer"]) == (0)):
		_cast_e_ghost_ship(b, enemies)
		return
	if ((nearby_count) >= (2)) and ((b.kit["w_timer"]) == (0)):
		_cast_w_x_marks(b, enemies)
		return
	if ((target_dist) < (220)) and ((b.kit["q_timer"]) == (0)):
		_cast_q_tide_bringer(b, enemies)
		return


## bosses/base_boss.py:6481-6526
static func _smart_ai_kenshiro(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((hp_ratio) < (0.5)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 70
		_l9_aoe(b, enemies, 190, stats.get("skill_r_damage", 520))
		return
	if ((hp_ratio) < (0.55)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 90)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 340))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 150, stats.get("skill_e_damage", 320))
		return
	if ((target_dist) < (140)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 300))
		return


## bosses/base_boss.py:6529-6574
static func _smart_ai_khazan(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (210)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (2)) and ((hp_ratio) < (0.45)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 660)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 75
		_l9_aoe(b, enemies, 210, stats.get("skill_r_damage", 560))
		return
	if ((nearby) >= (3)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 160, stats.get("skill_e_damage", 340))
		return
	if ((target_dist) > (120)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 50
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 110)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			_l9_aoe(b, enemies, 90, stats.get("skill_w_damage", 360))
		return
	if ((target_dist) < (150)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 320))
		return


## bosses/base_boss.py:6577-6622
static func _smart_ai_wiro(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 620)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 80
		_l9_aoe(b, enemies, 200, stats.get("skill_r_damage", 540))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		_l9_aoe(b, enemies, 140, stats.get("skill_w_damage", 340))
		return
	if ((hp_ratio) < (0.5)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 240)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 100)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_e_damage", 330))
		return
	if ((target_dist) < (140)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 190)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 30
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 300))
		return


## bosses/base_boss.py:6625-6671
static func _smart_ai_naraka(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (240)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 230, stats.get("skill_r_damage", 700))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 180, stats.get("skill_e_damage", 420))
		return
	if ((hp_ratio) < (0.6)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 50
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 120)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 400))
		return
	if ((target_dist) < (170)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 380))
		return


## bosses/base_boss.py:6678-6713
static func _smart_ai_krognarr(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((hp_ratio) < (0.5)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 660)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 85
		_l9_aoe(b, enemies, 210, stats.get("skill_r_damage", 600))
		return
	if ((hp_ratio) < (0.55)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 320)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 120, stats.get("skill_e_damage", 300))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_w_damage", 380))
		return
	if ((target_dist) < (200)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 210)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 340))
		return


## bosses/base_boss.py:6716-6761
static func _smart_ai_raz(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (210)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 80
		_l9_aoe(b, enemies, 200, stats.get("skill_r_damage", 580))
		return
	if ((hp_ratio) < (0.55)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 100)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 360))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 160, stats.get("skill_e_damage", 340))
		return
	if ((target_dist) < (170)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 190)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 330))
		return


## bosses/base_boss.py:6764-6812
static func _smart_ai_vraskhan(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 650)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 85
		_l9_aoe(b, enemies, 220, stats.get("skill_r_damage", 590))
		return
	if ((target_dist) > (150)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.global_position = Vector2(float(tgt.global_position.x), b.global_position.y)
			b.global_position = Vector2(b.global_position.x, float((tgt.global_position.y) - (20)))
			b.facing = 1 if (tgt.global_position.x) > (b.global_position.x) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 360))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_e_damage", 350))
		return
	if ((target_dist) < (160)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 190)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 90)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 340))
		return


## bosses/base_boss.py:6815-6855
static func _smart_ai_aurethzar(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (260)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 740))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 200, stats.get("skill_w_damage", 440))
		return
	if ((target_dist) < (160)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_e_damage", 380))
			if b.kit_has_slow(tgt):
				b.kit_apply_slow(tgt, 0.5, 90)
		return
	if ((target_dist) < (320)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 210)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 400))
		return


## bosses/base_boss.py:6862-6897
static func _smart_ai_aeralith(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (240)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 630)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 80
		_l9_aoe(b, enemies, 240, stats.get("skill_r_damage", 570))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_e_damage", 340))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 350))
		return
	if ((target_dist) < (320)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 190)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 330))
		return


## bosses/base_boss.py:6900-6938
static func _smart_ai_aurex(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 650)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 75
		_l9_aoe(b, enemies, 210, stats.get("skill_r_damage", 580))
		return
	if ((hp_ratio) < (0.55)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 130, stats.get("skill_e_damage", 320))
		return
	if ((target_dist) < (280)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 270)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 370))
		return
	if ((target_dist) < (160)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 340))
		return


## bosses/base_boss.py:6941-6978
static func _smart_ai_nyxareva(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.45))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 85
		_l9_aoe(b, enemies, 220, stats.get("skill_r_damage", 590))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_e_damage", 350))
		return
	if ((hp_ratio) < (0.55)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 360))
		return
	if ((target_dist) < (170)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 190)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 340))
		return


## bosses/base_boss.py:6981-7019
static func _smart_ai_thalakryon(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (260)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 260, stats.get("skill_r_damage", 760))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 190, stats.get("skill_e_damage", 440))
		return
	if ((hp_ratio) < (0.6)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 260))
		return
	if ((target_dist) < (340)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 210)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 420))
		return


## bosses/base_boss.py:7026-7060
static func _smart_ai_aurelix(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (240)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 650)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 85
		_l9_aoe(b, enemies, 240, stats.get("skill_r_damage", 600))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_e_damage", 360))
		return
	if ((hp_ratio) < (0.55)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 60
		return
	if ((target_dist) < (320)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 350))
		return


## bosses/base_boss.py:7063-7100
static func _smart_ai_aurelyssa(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.45))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 80
		_l9_aoe(b, enemies, 220, stats.get("skill_r_damage", 590))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 160, stats.get("skill_e_damage", 350))
		return
	if ((hp_ratio) < (0.55)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 360))
		return
	if ((target_dist) < (160)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 190)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 340))
		return


## bosses/base_boss.py:7103-7148
static func _smart_ai_vargrath(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 660)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 85
		_l9_aoe(b, enemies, 230, stats.get("skill_r_damage", 620))
		return
	if ((target_dist) > (140)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 270)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 110)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			_l9_aoe(b, enemies, 100, stats.get("skill_w_damage", 380))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 290)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_e_damage", 370))
		return
	if ((target_dist) < (160)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 360))
		return


## bosses/base_boss.py:7151-7188
static func _smart_ai_nazulmor(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (270)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 270, stats.get("skill_r_damage", 800))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 200, stats.get("skill_e_damage", 460))
		return
	if ((hp_ratio) < (0.6)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 280))
		return
	if ((target_dist) < (350)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 210)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 440))
		return


## bosses/base_boss.py:7195-7240
static func _smart_ai_kaeldris(b, enemies, target_dist):
	var d = null
	var dx = null
	var dy = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var step = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.45))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 650)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 80
		_l9_aoe(b, enemies, 220, stats.get("skill_r_damage", 620))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 290)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_e_damage", 370))
		return
	if ((target_dist) > (140)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 270)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dx = (tgt.global_position.x) - (b.global_position.x)
			dy = (tgt.global_position.y) - (b.global_position.y)
			d = Vector2(dx, dy).length()
			if (d) > (1):
				step = minf(d, 110)
				b.global_position += Vector2((float(dx) / float(d)) * (step), 0.0)
				b.global_position += Vector2(0.0, (float(dy) / float(d)) * (step))
				b.facing = 1 if (dx) > (0) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 380))
		return
	if ((target_dist) < (160)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 360))
		return


## bosses/base_boss.py:7243-7278
static func _smart_ai_pyraklos(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((nearby) >= (3)) and ((b.kit["r_timer"]) == (0)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 660)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 85
		_l9_aoe(b, enemies, 230, stats.get("skill_r_damage", 640))
		return
	if ((hp_ratio) < (0.5)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 130, stats.get("skill_e_damage", 240))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_w_damage", 390))
		return
	if ((target_dist) < (180)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 370))
		return


## bosses/base_boss.py:7281-7326
static func _smart_ai_velmyrth(b, enemies, target_dist):
	var hp_ratio = null
	var low_target = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	var __g1 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((float(e.hp) / float(maxf(1, e.max_hp))) < (0.3)): __g1 = 1
	low_target = __g1
	if ((b.kit["r_timer"]) == (0)) and ((low_target) or ((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 80
		_l9_aoe(b, enemies, 220, stats.get("skill_r_damage", 630))
		return
	if ((target_dist) > (150)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.global_position = Vector2(float(tgt.global_position.x), b.global_position.y)
			b.global_position = Vector2(b.global_position.x, float((tgt.global_position.y) - (20)))
			b.facing = 1 if (tgt.global_position.x) > (b.global_position.x) else -(1)
			b.kit_skill_hit(tgt, stats.get("skill_w_damage", 380))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 170, stats.get("skill_e_damage", 370))
		return
	if ((target_dist) < (160)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 190)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 35
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 360))
		return


## bosses/base_boss.py:7329-7364
static func _smart_ai_solvarin(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (280)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 280, stats.get("skill_r_damage", 840))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 200, stats.get("skill_e_damage", 380))
		return
	if ((hp_ratio) < (0.6)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 270)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 180, stats.get("skill_w_damage", 480))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 210)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 460))
		return


## bosses/base_boss.py:7368-7404
static func _smart_ai_azureth(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (270)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 650)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 85
		_l9_aoe(b, enemies, 270, stats.get("skill_r_damage", 680))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 290)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 200, stats.get("skill_e_damage", 370))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 270)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 400))
		return
	if ((target_dist) < (400)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 380))
		return


## bosses/base_boss.py:7407-7442
static func _smart_ai_luminar(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (280)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 660)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 280, stats.get("skill_r_damage", 700))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 295)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 205, stats.get("skill_e_damage", 380))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 275)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 195, stats.get("skill_w_damage", 410))
		return
	if ((target_dist) < (410)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 205)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 390))
		return


## bosses/base_boss.py:7445-7482
static func _smart_ai_solara(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (240)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 680)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 240, stats.get("skill_r_damage", 720))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 270)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 185, stats.get("skill_w_damage", 420))
		return
	if ((hp_ratio) < (0.65)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 195, stats.get("skill_e_damage", 390))
		b.hp = minf(b.max_hp, (b.hp) + (int((b.max_hp) * (0.1))))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 210)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 400))
		return


## bosses/base_boss.py:7485-7524
static func _smart_ai_pyraethis(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (300)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 660)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 300, stats.get("skill_r_damage", 900))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 310)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 220, stats.get("skill_e_damage", 460))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 200, stats.get("skill_w_damage", 500))
		return
	if ((target_dist) < (430)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 480))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.5))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:7528-7564
static func _smart_ai_auroth(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (240)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 700)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 240, stats.get("skill_r_damage", 740))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 310)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 195, stats.get("skill_e_damage", 400))
		return
	if ((hp_ratio) < (0.6)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 185, stats.get("skill_w_damage", 420))
		b.hp = minf(b.max_hp, (b.hp) + (int((b.max_hp) * (0.1))))
		return
	if ((target_dist) < (350)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 215)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 410))
		return


## bosses/base_boss.py:7567-7606
static func _smart_ai_morvein(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (250)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 690)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 760))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 205, stats.get("skill_e_damage", 410))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 275)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 440))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 215)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 420))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.5))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:7609-7644
static func _smart_ai_thorvak(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (250)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 680)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 760))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 195, stats.get("skill_w_damage", 440))
		return
	if ((hp_ratio) < (0.65)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 310)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 200, stats.get("skill_e_damage", 410))
		return
	if ((target_dist) < (350)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 420))
		return


## bosses/base_boss.py:7647-7685
static func _smart_ai_yamako(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (300)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 670)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 300, stats.get("skill_r_damage", 950))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 315)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 220, stats.get("skill_e_damage", 480))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 285)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 205, stats.get("skill_w_damage", 520))
		return
	if ((target_dist) < (400)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 225)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 500))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.4))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:7689-7724
static func _smart_ai_ignirus(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (280)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 690)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 280, stats.get("skill_r_damage", 800))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 315)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 210, stats.get("skill_e_damage", 430))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 285)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 195, stats.get("skill_w_damage", 460))
		return
	if ((target_dist) < (410)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 225)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 440))
		return


## bosses/base_boss.py:7727-7763
static func _smart_ai_leoric(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (250)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and ((hp_ratio) < (0.45)):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 700)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 800))
		b.hp = minf(b.max_hp, (b.hp) + (int((b.max_hp) * (0.2))))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 310)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 200, stats.get("skill_e_damage", 440))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 460))
		return
	if ((target_dist) < (350)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 225)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 450))
		return


## bosses/base_boss.py:7766-7805
static func _smart_ai_shirotaka(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (250)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 680)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 820))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 310)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 205, stats.get("skill_e_damage", 450))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 470))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 460))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.5))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:7808-7847
static func _smart_ai_seiryukong(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (300)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 680)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 300, stats.get("skill_r_damage", 1000))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 320)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 220, stats.get("skill_e_damage", 500))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 290)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 205, stats.get("skill_w_damage", 540))
		return
	if ((target_dist) < (400)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 230)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 520))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.4))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:7851-7887
static func _smart_ai_kaelthorn(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (250)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 690)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 840))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 320)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 205, stats.get("skill_e_damage", 460))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 290)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 480))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 230)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 470))
		return


## bosses/base_boss.py:7890-7926
static func _smart_ai_solvanth(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (260)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 700)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 260, stats.get("skill_r_damage", 860))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 320)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 210, stats.get("skill_e_damage", 470))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 290)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 195, stats.get("skill_w_damage", 490))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 235)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 480))
		return


## bosses/base_boss.py:7929-7967
static func _smart_ai_xyrael(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (250)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 680)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 880))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 315)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 205, stats.get("skill_e_damage", 480))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 285)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 500))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 225)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 490))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.5))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:7973-8008
static func _smart_ai_nyxareth(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (300)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 690)
		b.kit["active_skill"] = "4"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 300, stats.get("skill_r_damage", 1050))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 325)
		b.kit["active_skill"] = "3"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 220, stats.get("skill_e_damage", 520))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 295)
		b.kit["active_skill"] = "2"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 205, stats.get("skill_w_damage", 560))
		return
	if ((target_dist) < (420)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 235)
		b.kit["active_skill"] = "1"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 540))
		return


## bosses/base_boss.py:8012-8047
static func _smart_ai_cryssalia(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (280)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 700)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 280, stats.get("skill_r_damage", 900))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 325)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 215, stats.get("skill_e_damage", 490))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 295)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 200, stats.get("skill_w_damage", 510))
		return
	if ((target_dist) < (420)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 235)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 500))
		return


## bosses/base_boss.py:8050-8085
static func _smart_ai_kaelthar(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (250)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 690)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 250, stats.get("skill_r_damage", 920))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 320)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 200, stats.get("skill_e_damage", 500))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 290)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 190, stats.get("skill_w_damage", 520))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 230)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 510))
		return


## bosses/base_boss.py:8088-8124
static func _smart_ai_morkhaera(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (280)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 700)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 280, stats.get("skill_r_damage", 920))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 325)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 215, stats.get("skill_e_damage", 500))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 295)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 200, stats.get("skill_w_damage", 520))
		return
	if ((target_dist) < (420)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 235)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 510))
		return


## bosses/base_boss.py:8127-8166
static func _smart_ai_aurelion(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (300)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 700)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 300, stats.get("skill_r_damage", 1100))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 330)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 225, stats.get("skill_e_damage", 540))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 210, stats.get("skill_w_damage", 580))
		return
	if ((target_dist) < (400)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 560))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.4))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:8170-8205
static func _smart_ai_akahime(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (270)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 710)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 270, stats.get("skill_r_damage", 950))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 330)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 210, stats.get("skill_e_damage", 510))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 195, stats.get("skill_w_damage", 530))
		return
	if ((target_dist) < (410)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 520))
		return


## bosses/base_boss.py:8208-8246
static func _smart_ai_nyxthrael(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (260)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 700)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 260, stats.get("skill_r_damage", 960))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 325)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 210, stats.get("skill_e_damage", 520))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 295)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 195, stats.get("skill_w_damage", 540))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 235)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 530))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.5))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:8249-8284
static func _smart_ai_sylvantheros(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (280)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 710)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 280, stats.get("skill_r_damage", 960))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 330)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 215, stats.get("skill_e_damage", 520))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 200, stats.get("skill_w_damage", 540))
		return
	if ((target_dist) < (420)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 530))
		return


## bosses/base_boss.py:8287-8326
static func _smart_ai_vaelindra(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (310)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 710)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 310, stats.get("skill_r_damage", 1150))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 335)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 230, stats.get("skill_e_damage", 560))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 305)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 215, stats.get("skill_w_damage", 600))
		return
	if ((target_dist) < (430)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 245)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 580))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.4))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:8330-8369
static func _smart_ai_astraelion(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (260)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 710)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 260, stats.get("skill_r_damage", 1000))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 330)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 205, stats.get("skill_e_damage", 540))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 195, stats.get("skill_w_damage", 560))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 550))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.5))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:8372-8408
static func _smart_ai_morvaenthir(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (290)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 720)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 290, stats.get("skill_r_damage", 1010))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 335)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 220, stats.get("skill_e_damage", 550))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 305)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 205, stats.get("skill_w_damage", 570))
		return
	if ((target_dist) < (420)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 245)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 560))
		return


## bosses/base_boss.py:8411-8446
static func _smart_ai_thornvaegrim(b, enemies, target_dist):
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (270)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 710)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 90
		_l9_aoe(b, enemies, 270, stats.get("skill_r_damage", 1010))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 330)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 60
		_l9_aoe(b, enemies, 215, stats.get("skill_e_damage", 550))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 200, stats.get("skill_w_damage", 570))
		return
	if ((target_dist) < (360)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 245)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 40
		tgt = _l9_target(b, enemies)
		if tgt:
			b.kit_skill_hit(tgt, stats.get("skill_q_damage", 560))
		return


## bosses/base_boss.py:8449-8488
static func _smart_ai_morthraxis(b, enemies, target_dist):
	var dmg = null
	var hp_ratio = null
	var nearby = null
	var stats = null
	var tgt = null

	_init_l9_timers(b)
	_tick_l9_timers(b)
	stats = _l9_stats(b)
	var __g0 := 0
	for e in enemies:
		if (b.kit_unit_alive(e)) and ((Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (310)):
			__g0 += 1
	nearby = __g0
	hp_ratio = float(b.hp) / float(b.max_hp)
	if ((b.kit["r_timer"]) == (0)) and (((nearby) >= (3)) or ((hp_ratio) < (0.4))):
		b.kit["r_timer"] = stats.get("skill_r_cooldown", 720)
		b.kit["active_skill"] = "r"
		b.kit["active_skill_timer"] = 95
		_l9_aoe(b, enemies, 310, stats.get("skill_r_damage", 1200))
		return
	if ((nearby) >= (2)) and ((b.kit["e_timer"]) == (0)):
		b.kit["e_timer"] = stats.get("skill_e_cooldown", 340)
		b.kit["active_skill"] = "e"
		b.kit["active_skill_timer"] = 65
		_l9_aoe(b, enemies, 225, stats.get("skill_e_damage", 580))
		return
	if ((nearby) >= (2)) and ((b.kit["w_timer"]) == (0)):
		b.kit["w_timer"] = stats.get("skill_w_cooldown", 310)
		b.kit["active_skill"] = "w"
		b.kit["active_skill_timer"] = 55
		_l9_aoe(b, enemies, 210, stats.get("skill_w_damage", 620))
		return
	if ((target_dist) < (430)) and ((b.kit["q_timer"]) == (0)):
		b.kit["q_timer"] = stats.get("skill_q_cooldown", 250)
		b.kit["active_skill"] = "q"
		b.kit["active_skill_timer"] = 45
		tgt = _l9_target(b, enemies)
		if tgt:
			dmg = int(stats.get("skill_q_damage", 600))
			if (float(tgt.hp) / float(maxf(1, tgt.max_hp))) < (0.3):
				dmg = int((dmg) * (1.4))
			b.kit_skill_hit(tgt, dmg)
		return


## bosses/base_boss.py:1158-1170
static func _cast_q_mist_coil(b):
	var damage = null
	var stats = null

	b.kit["q_timer"] = 240
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 30
	stats = b.kit_get_stats()
	damage = stats.get("skill_q_damage", 250)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
	b._shake(10.0)


## bosses/base_boss.py:1172-1190
static func _cast_w_aphotic_shield(b, enemies):
	var damage = null
	var shield_hp = null
	var stats = null

	b.kit["w_timer"] = 360
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 90
	stats = b.kit_get_stats()
	damage = stats.get("skill_w_damage", 300)
	shield_hp = stats.get("skill_w_shield", 500)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (100):
			b.kit_skill_hit(e, damage)
	b.hp = minf(b.max_hp, (b.hp) + (shield_hp))
	b._shake(12.0)


## bosses/base_boss.py:1192-1211
static func _cast_e_darkness_gale(b):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var stats = null

	b.kit["e_timer"] = 300
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 40
	stats = b.kit_get_stats()
	damage = stats.get("skill_e_damage", 200)
	if (b.target) and (b.kit_unit_alive(b.target)):
		dx = (b.target.global_position.x) - (b.global_position.x)
		dy = (b.target.global_position.y) - (b.global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			b.global_position += Vector2((float(dx) / float(dist)) * (80), 0.0)
			b.global_position += Vector2(0.0, (float(dy) / float(dist)) * (80))
		b.kit_skill_hit(b.target, damage)
	b._shake(8.0)


## bosses/base_boss.py:1213-1227
static func _cast_r_death_sever(b, enemies):
	var damage = null
	var stats = null

	b.kit["r_timer"] = 600
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 60
	stats = b.kit_get_stats()
	damage = stats.get("skill_r_damage", 500)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			b.kit_skill_hit(e, damage)
	b._shake(20.0)


## bosses/base_boss.py:1288-1300
static func _cast_q_acid_spray(b):
	var damage = null
	var stats = null

	b.kit["q_timer"] = 210
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 40
	stats = b.kit_get_stats()
	damage = stats.get("skill_q_damage", 220)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
	b._shake(8.0)


## bosses/base_boss.py:1302-1330
static func _cast_w_unstable_concoction(b, enemies):
	var damage = null
	var stats = null
	var target_x = null
	var target_y = null

	b.kit["w_timer"] = 300
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 60
	stats = b.kit_get_stats()
	damage = stats.get("skill_w_damage", 320)
	if (b.target) and (b.kit_unit_alive(b.target)):
		target_x = b.target.global_position.x
		target_y = b.target.global_position.y
	else:
		target_x = b.global_position.x
		target_y = b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (target_x), (e.global_position.y) - (target_y)).length()) <= (100):
			b.kit_skill_hit(e, damage)
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 180)
	b.kit["w_target_x"] = target_x
	b.kit["w_target_y"] = target_y
	b._shake(15.0)


## bosses/base_boss.py:1332-1358
static func _cast_e_chemical_rage(b):
	var game = null
	var heal = null

	b.kit["e_timer"] = 480
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	b.kit["rage_active"] = true
	b.kit["rage_timer"] = 360
	b.damage = int((b.damage) * (1.5))
	heal = int((b.max_hp) * (0.15))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(12.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:1360-1382
static func _cast_r_greevils_greed(b, enemies):
	var damage = null
	var heal = null
	var kills_count = null
	var stats = null

	b.kit["r_timer"] = 720
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	stats = b.kit_get_stats()
	damage = stats.get("skill_r_damage", 550)
	kills_count = 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if not (b.kit_unit_alive(e)):
				kills_count += 1
	if (kills_count) > (0):
		heal = (kills_count) * (100)
		b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(25.0)


## bosses/base_boss.py:1456-1482
static func _cast_q_ice_vortex(b, enemies):
	var dist = null
	var initial_damage = null
	var stats = null

	b.kit["q_timer"] = 300
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 60
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit["vortex_x"] = b.target.global_position.x
		b.kit["vortex_y"] = b.target.global_position.y
	else:
		b.kit["vortex_x"] = (b.global_position.x) + (100)
		b.kit["vortex_y"] = b.global_position.y
	b.kit["vortex_active_timer"] = 180
	stats = b.kit_get_stats()
	initial_damage = int((stats.get("skill_q_damage", 180)) / (2))
	for e in enemies:
		dist = Vector2((e.global_position.x) - (b.kit["vortex_x"]), (e.global_position.y) - (b.kit["vortex_y"])).length()
		if (dist) <= (80):
			b.kit_skill_hit(e, initial_damage)
	b._shake(10.0)


## bosses/base_boss.py:1484-1528
static func _cast_w_chilling_touch(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null

	b.kit["w_timer"] = 240
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 45
	stats = b.kit_get_stats()
	damage = stats.get("skill_w_damage", 250)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 400
	line_width = 30
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				b.kit_skill_hit(e, damage)
				if b.kit_has_slow(e):
					b.kit_apply_slow(e, 0.6, 180)
	b.kit["w_dir_x"] = dx
	b.kit["w_dir_y"] = dy
	b._shake(8.0)


## bosses/base_boss.py:1530-1546
static func _cast_e_ice_blast(b):
	var damage = null
	var stats = null

	b.kit["e_timer"] = 360
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 50
	stats = b.kit_get_stats()
	damage = stats.get("skill_e_damage", 450)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if "attack_timer" in b.target:
			b.kit_lock_attack(b.target, maxf(b.kit_atk_timer(b.target), 90))
	b._shake(15.0)


## bosses/base_boss.py:1548-1590
static func _cast_r_cold_feet(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null

	b.kit["r_timer"] = 720
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	stats = b.kit_get_stats()
	damage = stats.get("skill_r_damage", 600)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 500
	line_width = 60
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				b.kit_skill_hit(e, damage)
				if b.kit_has_slow(e):
					b.kit_apply_slow(e, 0.7, 240)
	b.kit["r_dir_x"] = dx
	b.kit["r_dir_y"] = dy
	b._shake(25.0)


## bosses/base_boss.py:1664-1712
static func _cast_q_dragon_breath(b, enemies):
	var allowed_width = null
	var cone_width = null
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null

	b.kit["q_timer"] = 240
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 45
	stats = b.kit_get_stats()
	damage = stats.get("skill_q_damage", 320)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 250
	cone_width = 60
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			allowed_width = (cone_width) * ((0.3) + ((float(proj) / float(max_range)) * (0.7)))
			if (perp) < (allowed_width):
				b.kit_skill_hit(e, damage)
				if "attack_timer" in e:
					b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 45))
	b.kit_fx_cast("q")
	b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, (max_range) * (0.55), "q")
	b._shake(12.0)


## bosses/base_boss.py:1714-1750
static func _cast_w_dragon_tail(b, enemies):
	var damage = null
	var dist = null
	var push_x = null
	var push_y = null
	var stats = null

	b.kit["w_timer"] = 300
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 40
	stats = b.kit_get_stats()
	damage = stats.get("skill_w_damage", 380)
	for e in enemies:
		dist = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (dist) <= (130):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 60))
			dist = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
			if ((dist) > (0)) and (b.kit_can_move(e)):
				push_x = (float((e.global_position.x) - (b.global_position.x)) / float(dist)) * (15)
				push_y = (float((e.global_position.y) - (b.global_position.y)) / float(dist)) * (15)
				e.global_position += Vector2(push_x, 0.0)
				e.global_position += Vector2(0.0, push_y)
	b.kit_fx_cast("w")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 130, "w")
	b._shake(15.0)


## bosses/base_boss.py:1752-1788
static func _cast_e_dragon_blood(b):
	var base_damage = null
	var game = null
	var heal = null
	var stats = null

	b.kit["e_timer"] = 420
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	b.kit["dragon_blood_active"] = true
	b.kit["dragon_blood_timer"] = 480
	stats = b.kit_get_stats()
	base_damage = stats.get("damage", 120)
	b.damage = int((base_damage) * (1.3))
	heal = int((b.max_hp) * (0.2))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 110, "e")
	b._shake(10.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:1790-1825
static func _cast_r_elder_dragon_form(b, enemies):
	var base_damage = null
	var damage = null
	var heal = null
	var stats = null

	b.kit["r_timer"] = 780
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	b.kit["dragon_form_active"] = true
	b.kit["dragon_form_timer"] = 600
	stats = b.kit_get_stats()
	base_damage = stats.get("damage", 120)
	b.damage = int((base_damage) * (1.8))
	damage = stats.get("skill_r_damage", 600)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
	heal = int((b.max_hp) * (0.25))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 220, "r")
	b._shake(28.0)


## bosses/base_boss.py:1877-1910
static func _vhorethzir_q(b, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var damage = null
	var falloff = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 45
	damage = stats.get("skill_q_damage", 400)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if (not (closest)) or ((closest_dist) > (300)):
		b._shake(10.0)
		return
	for e in enemies:
		d = Vector2((e.global_position.x) - (closest.global_position.x), (e.global_position.y) - (closest.global_position.y)).length()
		if (d) <= (70):
			falloff = 1.0 if (e) == (closest) else 0.6
			b.kit_skill_hit(e, int((damage) * (falloff)))
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 45))
	b._shake(14.0)


## bosses/base_boss.py:1912-1943
static func _vhorethzir_w(b, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_w_damage", 360)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if (not (closest)) or ((closest_dist) > (320)):
		b._shake(12.0)
		return
	for e in enemies:
		if (Vector2((e.global_position.x) - (closest.global_position.x), (e.global_position.y) - (closest.global_position.y)).length()) <= (110):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 60))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.6, 180)
	b._shake(16.0)


## bosses/base_boss.py:1945-1979
static func _vhorethzir_e(b, enemies):
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 420)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 80
	b.kit["corrosive_active"] = true
	b.kit["corrosive_timer"] = 360
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 240)
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(14.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:1981-2015
static func _vhorethzir_r(b, enemies):
	var closest = null
	var closest_dist = null
	var cx = null
	var cy = null
	var d = null
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 780)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 100
	damage = stats.get("skill_r_damage", 720)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	cx = closest.global_position.x if closest else b.global_position.x
	cy = closest.global_position.y if closest else b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (cx), (e.global_position.y) - (cy)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 120))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.65, 300)
	b._shake(30.0)
	heal = int((b.max_hp) * (0.12))
	b.hp = minf(b.max_hp, (b.hp) + (heal))


## bosses/base_boss.py:2059-2085
static func _vaerith_q(b, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_q_damage", 300)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if (not (closest)) or ((closest_dist) > (280)):
		b._shake(8.0)
		return
	b.kit_skill_hit(closest, damage)
	if "attack_timer" in closest:
		b.kit_lock_attack(closest, maxf(b.kit_atk_timer(closest), 40))
	b._shake(10.0)


## bosses/base_boss.py:2087-2117
static func _vaerith_w(b, enemies):
	var closest = null
	var closest_dist = null
	var cx = null
	var cy = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 70
	damage = stats.get("skill_w_damage", 240)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	cx = closest.global_position.x if closest else b.global_position.x
	cy = closest.global_position.y if closest else b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (cx), (e.global_position.y) - (cy)).length()) <= (90):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 75))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.7, 240)
	b._shake(12.0)


## bosses/base_boss.py:2119-2160
static func _vaerith_e(b, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var damage = null
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 260)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 55
	damage = stats.get("skill_e_damage", 330)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if (not (closest)) or ((closest_dist) > (220)):
		b._shake(10.0)
		return
	b.kit_skill_hit(closest, damage)
	if "attack_timer" in closest:
		b.kit_lock_attack(closest, maxf(b.kit_atk_timer(closest), 60))
	heal = int((damage) * (0.6))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(14.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:2162-2185
static func _vaerith_r(b, enemies):
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 620)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 470)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 100))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.6, 240)
	heal = int((b.max_hp) * (0.15))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(24.0)


## bosses/base_boss.py:2248-2262
static func _xirthalis_q(b, enemies):
	var base_speed = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 180)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 60
	b.kit["shukuchi_active"] = true
	b.kit["shukuchi_timer"] = 180
	base_speed = stats.get("speed", 1.15)
	b.move_speed = ((base_speed) * (1.8)) * 60.0
	b._shake(6.0)


## bosses/base_boss.py:2264-2293
static func _xirthalis_w(b, enemies):
	var closest = null
	var closest_dist = null
	var cx = null
	var cy = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 70
	damage = stats.get("skill_w_damage", 260)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	cx = closest.global_position.x if closest else b.global_position.x
	cy = closest.global_position.y if closest else b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (cx), (e.global_position.y) - (cy)).length()) <= (100):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 60))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.6, 200)
	b._shake(12.0)


## bosses/base_boss.py:2295-2324
static func _xirthalis_e(b, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 220)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 45
	damage = stats.get("skill_e_damage", 340)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if (not (closest)) or ((closest_dist) > (270)):
		b._shake(8.0)
		return
	b.kit_skill_hit(closest, damage)
	if b.kit_unit_alive(closest):
		b.kit_skill_hit(closest, int((damage) * (0.6)))
	if "attack_timer" in closest:
		b.kit_lock_attack(closest, maxf(b.kit_atk_timer(closest), 50))
	b._shake(14.0)


## bosses/base_boss.py:2326-2362
static func _xirthalis_r(b, enemies):
	var game = null
	var healed = null
	var mark = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 60
	mark = b.kit["timelapse_hp_mark"]
	if (mark) == (null):
		mark = int((b.max_hp) * (0.5))
	healed = maxf(0, (minf(b.max_hp, mark)) - (b.hp))
	b.hp = minf(b.max_hp, maxf(b.hp, mark))
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (160):
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 180)
	b._shake(20.0)
	if (healed) > (0):
		b._callout("+" + str(healed), true)


## bosses/base_boss.py:2406-2436
static func _vhyssarion_q(b, enemies):
	var closest = null
	var closest_dist = null
	var cx = null
	var cy = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_q_damage", 280)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	cx = closest.global_position.x if closest else b.global_position.x
	cy = closest.global_position.y if closest else b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (cx), (e.global_position.y) - (cy)).length()) <= (100):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 70))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.65, 240)
	b._shake(14.0)


## bosses/base_boss.py:2438-2466
static func _vhyssarion_w(b, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 200)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 40
	damage = stats.get("skill_w_damage", 350)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if (not (closest)) or ((closest_dist) > (300)):
		b._shake(8.0)
		return
	b.kit_skill_hit(closest, damage)
	if "attack_timer" in closest:
		b.kit_lock_attack(closest, maxf(b.kit_atk_timer(closest), 55))
	if b.kit_has_slow(closest):
		b.kit_apply_slow(closest, 0.5, 180)
	b._shake(12.0)


## bosses/base_boss.py:2468-2498
static func _vhyssarion_e(b, enemies):
	var closest = null
	var closest_dist = null
	var cx = null
	var cy = null
	var d = null
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 70
	damage = stats.get("skill_e_damage", 300)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	cx = closest.global_position.x if closest else b.global_position.x
	cy = closest.global_position.y if closest else b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (cx), (e.global_position.y) - (cy)).length()) <= (85):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 80))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.75, 200)
	b._shake(16.0)


## bosses/base_boss.py:2500-2519
static func _vhyssarion_r(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 640)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 430)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (190):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 110))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.6, 260)
	b._shake(26.0)


## bosses/base_boss.py:2580-2592
static func _cast_q_mana_break(b):
	var damage = null
	var stats = null

	b.kit["q_timer"] = 180
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 40
	stats = b.kit_get_stats()
	damage = stats.get("skill_q_damage", 180)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
	b._shake(10.0)


## bosses/base_boss.py:2594-2620
static func _cast_w_blink(b):
	var dist = null
	var dx = null
	var dy = null
	var offset = null

	b.kit["w_timer"] = 240
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 25
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit["blink_from_x"] = b.global_position.x
		b.kit["blink_from_y"] = b.global_position.y
		dx = (b.target.global_position.x) - (b.global_position.x)
		dy = (b.target.global_position.y) - (b.global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			offset = maxf(0, (dist) - (60))
			b.global_position = Vector2((b.global_position.x) + ((float(dx) / float(dist)) * (offset)), b.global_position.y)
			b.global_position = Vector2(b.global_position.x, (b.global_position.y) + ((float(dy) / float(dist)) * (offset)))
		b.kit["blink_to_x"] = b.global_position.x
		b.kit["blink_to_y"] = b.global_position.y
	b._shake(8.0)


## bosses/base_boss.py:2622-2640
static func _cast_e_counterspell(b, enemies):
	var damage = null
	var dist = null
	var stats = null

	b.kit["e_timer"] = 300
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	stats = b.kit_get_stats()
	damage = stats.get("skill_e_damage", 150)
	for e in enemies:
		dist = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (dist) <= (100):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 60))
	b._shake(12.0)


## bosses/base_boss.py:2642-2661
static func _cast_r_mana_void(b, enemies):
	var damage = null
	var stats = null

	b.kit["r_timer"] = 540
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	stats = b.kit_get_stats()
	damage = stats.get("skill_r_damage", 380)
	b.kit["mana_void_x"] = b.global_position.x
	b.kit["mana_void_y"] = b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.kit["mana_void_x"]), (e.global_position.y) - (b.kit["mana_void_y"])).length()) <= (180):
			b.kit_skill_hit(e, damage)
	b._shake(20.0)


## bosses/base_boss.py:2743-2755
static func _cast_q_spark_wraith(b):
	var damage = null
	var stats = null

	b.kit["q_timer"] = 200
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	stats = b.kit_get_stats()
	damage = stats.get("skill_q_damage", 200)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
	b._shake(10.0)


## bosses/base_boss.py:2757-2778
static func _cast_w_flux(b):
	var damage = null
	var stats = null

	b.kit["w_timer"] = 300
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 40
	stats = b.kit_get_stats()
	damage = stats.get("skill_w_damage", 150)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit["flux_target"] = b.target
		b.kit["flux_active_timer"] = 240
		b.kit_skill_hit(b.target, int((damage) / (2)))
		if b.kit_has_slow(b.target):
			b.kit_apply_slow(b.target, 0.5, 240)
	b._shake(8.0)


## bosses/base_boss.py:2780-2802
static func _cast_e_magnetic_field(b, enemies):
	var damage = null
	var dist = null
	var heal = null
	var stats = null

	b.kit["e_timer"] = 360
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 90
	stats = b.kit_get_stats()
	damage = stats.get("skill_e_damage", 100)
	for e in enemies:
		dist = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (dist) <= (90):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 45))
	heal = int((b.max_hp) * (0.08))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(10.0)


## bosses/base_boss.py:2804-2823
static func _cast_r_tempest_double(b):
	var heal = null

	b.kit["r_timer"] = 720
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 60
	b.kit["clones_active_timer"] = 480
	b.kit["clones_positions"] = [[-(60), 0], [60, 0]]
	heal = int((b.max_hp) * (0.15))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(15.0)


## bosses/base_boss.py:2905-2932
static func _cast_q_battle_hunger(b):
	var base_damage = null
	var game = null
	var heal = null
	var stats = null

	b.kit["q_timer"] = 420
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 90
	b.kit["rage_active"] = true
	b.kit["rage_timer"] = 300
	stats = b.kit_get_stats()
	base_damage = stats.get("damage", 80)
	b.damage = int((base_damage) * (1.5))
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(12.0)
	b._callout("RAGE! +" + str(heal), true)


## bosses/base_boss.py:2934-2948
static func _cast_w_counter_helix(b, enemies):
	var damage = null
	var stats = null

	b.kit["w_timer"] = 240
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 45
	stats = b.kit_get_stats()
	damage = stats.get("skill_w_damage", 220)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (100):
			b.kit_skill_hit(e, damage)
	b._shake(15.0)


## bosses/base_boss.py:2950-2970
static func _cast_e_berserkers_call(b, enemies):
	var damage = null
	var dist = null
	var stats = null

	b.kit["e_timer"] = 360
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	b.defense_boost = true
	b.defense_timer = 180
	stats = b.kit_get_stats()
	damage = stats.get("skill_e_damage", 150)
	for e in enemies:
		dist = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (dist) <= (120):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 30))
	b._shake(18.0)


## bosses/base_boss.py:2972-2992
static func _cast_r_culling_blade(b):
	var damage = null
	var stats = null
	var target_hp_ratio = null

	b.kit["r_timer"] = 480
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 60
	stats = b.kit_get_stats()
	damage = stats.get("skill_r_damage", 450)
	if (b.target) and (b.kit_unit_alive(b.target)):
		target_hp_ratio = float(b.target.hp) / float(b.target.max_hp)
		if (target_hp_ratio) < (0.3):
			damage = int((damage) * (2))
			b.kit["r_timer"] = 120
		b.kit_skill_hit(b.target, damage)
	b._shake(25.0)


## bosses/base_boss.py:3031-3044
static func _razak_q(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 40
	if (b.target) and (b.kit_unit_alive(b.target)):
		damage = stats.get("skill_q_damage", 160)
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.target.global_position.x), (e.global_position.y) - (b.target.global_position.y)).length()) <= (75):
				b.kit_skill_hit(e, damage)
				if b.kit_has_slow(e):
					b.kit_apply_slow(e, 0.35, 120)
	b._shake(10.0)


## bosses/base_boss.py:3049-3072
static func _razak_w(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 50
	if (b.target) and (b.kit_unit_alive(b.target)):
		damage = stats.get("skill_w_damage", 220)
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.target.global_position.x), (e.global_position.y) - (b.target.global_position.y)).length()) <= (95):
				b.kit_skill_hit(e, damage)
				if "attack_timer" in e:
					b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 45))
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 95, "w")
	b._shake(14.0)


## bosses/base_boss.py:3074-3099
static func _razak_e(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var jump = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 35
	if (b.target) and (b.kit_unit_alive(b.target)):
		dx = (b.target.global_position.x) - (b.global_position.x)
		dy = (b.target.global_position.y) - (b.global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			jump = minf(110, maxf(40, (dist) - (50)))
			b.global_position += Vector2((float(dx) / float(dist)) * (jump), 0.0)
			b.global_position += Vector2(0.0, (float(dy) / float(dist)) * (jump))
			b.facing = 1 if (dx) > (0) else -(1)
		damage = stats.get("skill_e_damage", 180)
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (80):
				b.kit_skill_hit(e, damage)
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 80, "e")
	b._shake(12.0)


## bosses/base_boss.py:3101-3118
static func _razak_r(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 520)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 340)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			b.kit_skill_hit(e, damage)
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 180, "r")
	b._shake(20.0)


## bosses/base_boss.py:3158-3169
static func _khalros_q(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	if (b.target) and (b.kit_unit_alive(b.target)):
		damage = stats.get("skill_q_damage", 210)
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.target.global_position.x), (e.global_position.y) - (b.target.global_position.y)).length()) <= (70):
				b.kit_skill_hit(e, damage)
	b._shake(10.0)


## bosses/base_boss.py:3171-3184
static func _khalros_w(b, enemies):
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 60
	damage = stats.get("skill_w_damage", 160)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (120):
			b.kit_skill_hit(e, damage)
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 90)
	heal = int((b.max_hp) * (0.08))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(12.0)


## bosses/base_boss.py:3186-3207
static func _khalros_e(b, enemies):
	var charge = null
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 45
	if (b.target) and (b.kit_unit_alive(b.target)):
		dx = (b.target.global_position.x) - (b.global_position.x)
		dy = (b.target.global_position.y) - (b.global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			charge = minf(90, maxf(35, (dist) - (45)))
			b.global_position += Vector2((float(dx) / float(dist)) * (charge), 0.0)
			b.global_position += Vector2(0.0, (float(dy) / float(dist)) * (charge))
			b.facing = 1 if (dx) > (0) else -(1)
		damage = stats.get("skill_e_damage", 220)
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (85):
				b.kit_skill_hit(e, damage)
				if "attack_timer" in e:
					b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 40))
	b._shake(14.0)


## bosses/base_boss.py:3209-3221
static func _khalros_r(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 560)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 70
	damage = stats.get("skill_r_damage", 380)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 30))
	b._shake(20.0)


## bosses/base_boss.py:3278-3295
static func _gorath_q(b):
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 420)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 90
	b.kit["rage_active"] = true
	b.kit["rage_timer"] = 300
	b.damage = int((stats.get("damage", 94)) * (1.4))
	b.move_speed = ((stats.get("speed", 1.18)) * (1.2)) * 60.0
	heal = int((b.max_hp) * (0.08))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(12.0)
	b.kit_fx_cast("q")


## bosses/base_boss.py:3297-3320
static func _gorath_w(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 240)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 60
	damage = stats.get("skill_w_damage", 210)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 50))
			b.kit_fx_impact(e.global_position.x, e.global_position.y, 150, "w")
	b._shake(15.0)
	b.kit_fx_cast("w")


## bosses/base_boss.py:3322-3347
static func _gorath_e(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var leap = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 260)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 35
	if (b.target) and (b.kit_unit_alive(b.target)):
		dx = (b.target.global_position.x) - (b.global_position.x)
		dy = (b.target.global_position.y) - (b.global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			leap = minf(120, maxf(45, (dist) - (35)))
			b.global_position += Vector2((float(dx) / float(dist)) * (leap), 0.0)
			b.global_position += Vector2(0.0, (float(dy) / float(dist)) * (leap))
			b.facing = 1 if (dx) > (0) else -(1)
		damage = stats.get("skill_e_damage", 190)
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (85):
				b.kit_skill_hit(e, damage)
	b._shake(12.0)
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 85, "e")


## bosses/base_boss.py:3349-3367
static func _gorath_r(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 560)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 420)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (190):
			b.kit_skill_hit(e, damage)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, int((damage) / (2)))
	b._shake(22.0)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 190, "r")


## bosses/base_boss.py:3407-3425
static func _varkul_q(b):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_q_damage", 220)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if b.kit_has_slow(b.target):
			b.kit_apply_slow(b.target, 0.4, 120)
		b.kit_fx_cast("q")
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 54, "q")
	b._shake(10.0)


## bosses/base_boss.py:3427-3446
static func _varkul_w(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 60
	damage = stats.get("skill_w_damage", 280)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if "attack_timer" in b.target:
			b.kit_lock_attack(b.target, maxf(b.kit_atk_timer(b.target), 60))
		b.kit_fx_cast("w")
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 34, "w")
	b._shake(14.0)


## bosses/base_boss.py:3448-3465
static func _varkul_e(b):
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 360)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_e_damage", 160)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
	heal = int((b.max_hp) * (0.12))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 95, "e")
	b._shake(10.0)


## bosses/base_boss.py:3467-3485
static func _varkul_r(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 540)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 80
	damage = stats.get("skill_r_damage", 380)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, damage)
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 180)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 120, "r")
	b._shake(20.0)


## bosses/base_boss.py:3531-3551
static func _xerathis_q(b, enemies):
	var damage = null
	var stats = null
	var tx = null
	var ty = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 260)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 60
	damage = stats.get("skill_q_damage", 200)
	if (b.target) and (b.kit_unit_alive(b.target)):
		tx = b.target.global_position.x
		ty = b.target.global_position.y
		for e in enemies:
			if (Vector2((e.global_position.x) - (tx), (e.global_position.y) - (ty)).length()) <= (90):
				b.kit_skill_hit(e, damage)
				if b.kit_has_slow(e):
					b.kit_apply_slow(e, 0.4, 120)
		b.kit_fx_cast("q")
		b.kit_fx_impact(tx, ty, 48, "q")
	b._shake(12.0)


## bosses/base_boss.py:3553-3574
static func _xerathis_w(b):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 240)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_w_damage", 280)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if "attack_timer" in b.target:
			b.kit_lock_attack(b.target, maxf(b.kit_atk_timer(b.target), 75))
		if b.kit_has_slow(b.target):
			b.kit_apply_slow(b.target, 0.6, 180)
		b.kit_fx_cast("w")
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 30, "w")
	b._shake(14.0)


## bosses/base_boss.py:3576-3593
static func _xerathis_e(b):
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 420)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 90
	b.kit["arcane_buff_active"] = true
	b.kit["arcane_buff_timer"] = 360
	b.damage = int((b.base_damage) * (1.3))
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 90, "e")
	b._shake(10.0)


## bosses/base_boss.py:3595-3613
static func _xerathis_r(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 580)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 100
	damage = stats.get("skill_r_damage", 360)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (240):
			b.kit_skill_hit(e, damage)
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.55, 240)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 110, "r")
	b._shake(24.0)


## bosses/base_boss.py:3659-3680
static func _nyzrak_q(b):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_q_damage", 240)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if b.kit_has_slow(b.target):
			b.kit_apply_slow(b.target, 0.4, 120)
	b._shake(12.0)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 60, "q")


## bosses/base_boss.py:3682-3703
static func _nyzrak_w(b, enemies):
	var damage = null
	var stats = null
	var tx = null
	var ty = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_w_damage", 200)
	if (b.target) and (b.kit_unit_alive(b.target)):
		tx = b.target.global_position.x
		ty = b.target.global_position.y
		for e in enemies:
			if (Vector2((e.global_position.x) - (tx), (e.global_position.y) - (ty)).length()) <= (80):
				b.kit_skill_hit(e, damage)
	b._shake(14.0)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 80, "w")


## bosses/base_boss.py:3705-3728
static func _nyzrak_e(b):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 340)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 70
	damage = stats.get("skill_e_damage", 220)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if "attack_timer" in b.target:
			b.kit_lock_attack(b.target, maxf(b.kit_atk_timer(b.target), 90))
		if b.kit_has_slow(b.target):
			b.kit_apply_slow(b.target, 0.7, 180)
	b._shake(16.0)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 44, "e")


## bosses/base_boss.py:3730-3753
static func _nyzrak_r(b, enemies):
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 560)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	b.kit["shield_active"] = true
	b.kit["shield_timer"] = 240
	damage = stats.get("skill_r_damage", 400)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 180)
	heal = int((b.max_hp) * (0.15))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(22.0)
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 200, "r")


## bosses/base_boss.py:3789-3809
static func _cast_zharok_q(b):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 200)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, stats.get("skill_q_damage", 220))
	b._shake(10.0)
	b.kit_fx_cast("q")
	if (b.target) != (null):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 60, "q")


## bosses/base_boss.py:3811-3824
static func _cast_zharok_w(b):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 40
	b._shake(5.0)
	b.kit_fx_cast("w")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 200, "w")


## bosses/base_boss.py:3826-3843
static func _cast_zharok_e(b, enemies):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
			b.kit_skill_hit(e, stats.get("skill_e_damage", 280))
	b._shake(15.0)
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 150, "e")


## bosses/base_boss.py:3845-3863
static func _cast_zharok_r(b, enemies):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 80
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, stats.get("skill_r_damage", 400))
	b._shake(20.0)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 220, "r")


## bosses/base_boss.py:3899-3912
static func _cast_pyrenth_q(b):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, stats.get("skill_q_damage", 320))
	b._shake(12.0)
	b.kit_fx_cast("q")


## bosses/base_boss.py:3914-3927
static func _cast_pyrenth_w(b):
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 360)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 40
	heal = int((b.max_hp) * (0.08))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(10.0)
	b.kit_fx_cast("w")


## bosses/base_boss.py:3929-3945
static func _cast_pyrenth_e(b, enemies):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 300)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			b.kit_skill_hit(e, stats.get("skill_e_damage", 380))
	b._shake(18.0)
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 180, "e")


## bosses/base_boss.py:3947-3963
static func _cast_pyrenth_r(b, enemies):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 70
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, stats.get("skill_r_damage", 550))
	b._shake(25.0)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 220, "r")


## bosses/base_boss.py:3999-4019
static func _cast_vokrahn_q(b):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, stats.get("skill_q_damage", 350))
	b._shake(12.0)
	b.kit_fx_cast("q")
	if (b.target) != (null):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 70, "q")


## bosses/base_boss.py:4021-4039
static func _cast_vokrahn_w(b, enemies):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 60
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, stats.get("skill_w_damage", 250))
	b._shake(18.0)
	b.kit_fx_cast("w")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 220, "w")


## bosses/base_boss.py:4041-4059
static func _cast_vokrahn_e(b):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 50
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, stats.get("skill_e_damage", 400))
	b._shake(15.0)
	b.kit_fx_cast("e")
	if (b.target) != (null):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 60, "e")


## bosses/base_boss.py:4061-4079
static func _cast_vokrahn_r(b, enemies):
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 80
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, 150)
	b._shake(20.0)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 220, "r")


## bosses/base_boss.py:4470-4480
static func _malzareth_q(b, enemies):
	var damage = null
	var stats = null
	var tx = null
	var ty = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 60
	damage = stats.get("skill_q_damage", 300)
	if (b.target) and (b.kit_unit_alive(b.target)):
		tx = b.target.global_position.x
		ty = b.target.global_position.y
		for e in enemies:
			if (Vector2((e.global_position.x) - (tx), (e.global_position.y) - (ty)).length()) <= (100):
				b.kit_skill_hit(e, damage)
	b._shake(14.0)


## bosses/base_boss.py:4482-4493
static func _malzareth_w(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 280)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_w_damage", 280)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		for e in enemies:
			if ((e) != (b.target)) and ((Vector2((e.global_position.x) - (b.target.global_position.x), (e.global_position.y) - (b.target.global_position.y)).length()) <= (60)):
				b.kit_skill_hit(e, int((damage) / (2)))
	b._shake(12.0)


## bosses/base_boss.py:4495-4504
static func _malzareth_e(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 260)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 45
	damage = stats.get("skill_e_damage", 220)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if b.kit_has_slow(b.target):
			b.kit_apply_slow(b.target, 0.5, 180)
	b._shake(10.0)


## bosses/base_boss.py:4506-4525
static func _malzareth_r(b, enemies):
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 400)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
	heal = int((b.max_hp) * (0.12))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(22.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:4558-4567
static func _akashari_q(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 220)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_q_damage", 320)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if b.kit_has_slow(b.target):
			b.kit_apply_slow(b.target, 0.4, 120)
	b._shake(14.0)


## bosses/base_boss.py:4569-4586
static func _akashari_w(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 55
	damage = stats.get("skill_w_damage", 250)
	if (b.target) and (b.kit_unit_alive(b.target)):
		dx = (b.target.global_position.x) - (b.global_position.x)
		dy = (b.target.global_position.y) - (b.global_position.y)
		dist = Vector2(dx, dy).length()
		if (dist) > (0):
			b.global_position += Vector2((float(dx) / float(dist)) * (minf(dist, 150)), 0.0)
			b.global_position += Vector2(0.0, (float(dy) / float(dist)) * (minf(dist, 150)))
		for e in enemies:
			if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (80):
				b.kit_skill_hit(e, damage)
	heal = int((b.max_hp) * (0.08))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(12.0)


## bosses/base_boss.py:4588-4596
static func _akashari_e(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 260)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	damage = stats.get("skill_e_damage", 300)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
			b.kit_skill_hit(e, damage)
	b._shake(16.0)


## bosses/base_boss.py:4598-4617
static func _akashari_r(b, enemies):
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 450)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, damage)
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 240)
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(25.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:4650-4661
static func _vorenmarr_q(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 70
	damage = stats.get("skill_q_damage", 260)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		for e in enemies:
			if ((e) != (b.target)) and ((Vector2((e.global_position.x) - (b.target.global_position.x), (e.global_position.y) - (b.target.global_position.y)).length()) <= (80)):
				b.kit_skill_hit(e, int((damage) / (2)))
	b._shake(12.0)


## bosses/base_boss.py:4663-4677
static func _vorenmarr_w(b):
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 70
	heal = int((b.max_hp) * (0.14))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(8.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:4679-4691
static func _vorenmarr_e(b, enemies):
	var damage = null
	var stats = null
	var tx = null
	var ty = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 280)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 80
	damage = stats.get("skill_e_damage", 350)
	if (b.target) and (b.kit_unit_alive(b.target)):
		tx = b.target.global_position.x
		ty = b.target.global_position.y
		for e in enemies:
			if (Vector2((e.global_position.x) - (tx), (e.global_position.y) - (ty)).length()) <= (120):
				b.kit_skill_hit(e, damage)
				if "attack_timer" in e:
					b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 60))
	b._shake(18.0)


## bosses/base_boss.py:4693-4712
static func _vorenmarr_r(b, enemies):
	var damage = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 100
	damage = stats.get("skill_r_damage", 420)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
	heal = int((b.max_hp) * (0.12))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(25.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:4778-4825
static func _nyxarath_q(b, enemies):
	var closest = null
	var closest_dist = null
	var d = null
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 40
	damage = stats.get("skill_q_damage", 380)
	closest = null
	closest_dist = 9999
	for e in enemies:
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (closest_dist):
			closest_dist = d
			closest = e
	if (not (closest)) or ((closest_dist) > (300)):
		b._shake(12.0)
		return
	dx = (closest.global_position.x) - (b.global_position.x)
	dy = (closest.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		b._shake(12.0)
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 280
	line_width = 50
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				b.kit_skill_hit(e, damage)
				if "attack_timer" in e:
					b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 45))
	b._shake(18.0)


## bosses/base_boss.py:4827-4864
static func _nyxarath_w(b, enemies):
	var base_damage = null
	var damage = null
	var game = null
	var heal = null
	var kills_count = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 70
	damage = stats.get("skill_w_damage", 350)
	kills_count = 0
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (180):
			b.kit_skill_hit(e, damage)
			if not (b.kit_unit_alive(e)):
				kills_count += 1
	b.kit["necro_buff_active"] = true
	b.kit["necro_buff_timer"] = 480
	base_damage = stats.get("damage", 130)
	b.damage = int((base_damage) * (1.4))
	heal = (int((b.max_hp) * (0.06))) + ((kills_count) * (30))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(16.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:4866-4900
static func _nyxarath_e(b, enemies):
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 420)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 80
	b.kit["presence_active"] = true
	b.kit["presence_timer"] = 360
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 240)
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._shake(14.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:4902-4945
static func _nyxarath_r(b, enemies):
	var damage = null
	var dist = null
	var game = null
	var heal = null
	var push_x = null
	var push_y = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 780)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 110
	damage = stats.get("skill_r_damage", 700)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 120))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.6, 240)
			dist = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
			if ((dist) > (0)) and (b.kit_can_move(e)):
				push_x = (float((e.global_position.x) - (b.global_position.x)) / float(dist)) * (20)
				push_y = (float((e.global_position.y) - (b.global_position.y)) / float(dist)) * (20)
				e.global_position += Vector2(push_x, 0.0)
				e.global_position += Vector2(0.0, push_y)
	b._shake(30.0)
	heal = int((b.max_hp) * (0.13))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5003-5051
static func _thalgryn_q(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null
	var surge_dist = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 300)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 60
	damage = stats.get("skill_q_damage", 320)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		b._shake(12.0)
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		b._shake(12.0)
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 250
	line_width = 50
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				b.kit_skill_hit(e, damage)
	surge_dist = minf(dist, 200)
	b.global_position += Vector2((dx) * (surge_dist), 0.0)
	b.global_position += Vector2(0.0, (dy) * (surge_dist))
	b.kit_fx_cast("q")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 130, "q")
	b._shake(18.0)


## bosses/base_boss.py:5053-5087
static func _thalgryn_w(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 260)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 50
	damage = stats.get("skill_w_damage", 400)
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_skill_hit(b.target, damage)
		if "attack_timer" in b.target:
			b.kit_lock_attack(b.target, maxf(b.kit_atk_timer(b.target), 60))
		for e in enemies:
			if ((e) != (b.target)) and ((Vector2((e.global_position.x) - (b.target.global_position.x), (e.global_position.y) - (b.target.global_position.y)).length()) <= (60)):
				b.kit_skill_hit(e, int((damage) / (3)))
	b.kit_fx_cast("w")
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 60, "w")
	else:
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 60, "w")
	b._shake(15.0)


## bosses/base_boss.py:5089-5127
static func _thalgryn_e(b):
	var base_damage = null
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 360)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 60
	b.kit["morph_buff_active"] = true
	b.kit["morph_buff_timer"] = 300
	base_damage = stats.get("damage", 92)
	b.damage = int((base_damage) * (1.35))
	heal = int((b.max_hp) * (0.14))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 115, "e")
	b._shake(10.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5129-5169
static func _thalgryn_r(b, enemies):
	var damage = null
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 80
	damage = stats.get("skill_r_damage", 380)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.4, 180)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 200, "r")
	b._shake(22.0)
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5227-5278
static func _syrentha_q(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 45
	damage = stats.get("skill_q_damage", 250)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		b._shake(10.0)
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		b._shake(10.0)
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 250
	line_width = 70
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				b.kit_skill_hit(e, damage)
				if b.kit_has_slow(e):
					b.kit_apply_slow(e, 0.5, 180)
	b.kit_fx_cast("q")
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 250, "q")
	else:
		b.kit_fx_impact((b.global_position.x) + ((dx) * (220)), (b.global_position.y) + ((dy) * (220)), 250, "q")
	b._shake(12.0)


## bosses/base_boss.py:5280-5309
static func _syrentha_w(b, enemies):
	var damage = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 80
	damage = stats.get("skill_w_damage", 180)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (150):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 120))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.7, 240)
	b.kit_fx_cast("w")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 150, "w")
	b._shake(14.0)


## bosses/base_boss.py:5311-5349
static func _syrentha_e(b):
	var base_damage = null
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 420)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 70
	b.kit["mirror_buff_active"] = true
	b.kit["mirror_buff_timer"] = 360
	base_damage = stats.get("damage", 98)
	b.damage = int((base_damage) * (1.4))
	heal = int((b.max_hp) * (0.12))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 150, "e")
	b._shake(10.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5351-5395
static func _syrentha_r(b, enemies):
	var damage = null
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 420)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (220):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 150))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.8, 300)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 220, "r")
	b._shake(22.0)
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5450-5501
static func _gravewake_q(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["q_timer"] = stats.get("skill_q_cooldown", 240)
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 45
	damage = stats.get("skill_q_damage", 280)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		b._shake(12.0)
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		b._shake(12.0)
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 200
	line_width = 60
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				b.kit_skill_hit(e, damage)
				if b.kit_has_slow(e):
					b.kit_apply_slow(e, 0.5, 180)
	b.kit_fx_cast("q")
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 200, "q")
	else:
		b.kit_fx_impact((b.global_position.x) + ((dx) * (220)), (b.global_position.y) + ((dy) * (220)), 200, "q")
	b._shake(15.0)


## bosses/base_boss.py:5503-5533
static func _gravewake_w(b, enemies):
	var damage = null
	var stats = null
	var tx = null
	var ty = null

	stats = b.kit_get_stats()
	b.kit["w_timer"] = stats.get("skill_w_cooldown", 300)
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 80
	damage = stats.get("skill_w_damage", 250)
	if (b.target) and (b.kit_unit_alive(b.target)):
		tx = b.target.global_position.x
		ty = b.target.global_position.y
	else:
		tx = b.global_position.x
		ty = b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (tx), (e.global_position.y) - (ty)).length()) <= (120):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 60))
	b.kit_fx_cast("w")
	b.kit_fx_impact(tx, ty, 120, "w")
	b._shake(14.0)


## bosses/base_boss.py:5535-5569
static func _gravewake_e(b):
	var game = null
	var heal = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["e_timer"] = stats.get("skill_e_cooldown", 360)
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 70
	b.kit["shell_active"] = true
	b.kit["shell_timer"] = 300
	heal = int((b.max_hp) * (0.12))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("e")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 90, "e")
	b._shake(10.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5571-5624
static func _gravewake_r(b, enemies):
	var damage = null
	var dist = null
	var game = null
	var heal = null
	var push_x = null
	var push_y = null
	var stats = null

	stats = b.kit_get_stats()
	b.kit["r_timer"] = stats.get("skill_r_cooldown", 600)
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 90
	damage = stats.get("skill_r_damage", 400)
	for e in enemies:
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
			if b.kit_has_slow(e):
				b.kit_apply_slow(e, 0.5, 180)
			dist = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
			if ((dist) > (0)) and (b.kit_can_move(e)):
				push_x = (float((e.global_position.x) - (b.global_position.x)) / float(dist)) * (18)
				push_y = (float((e.global_position.y) - (b.global_position.y)) / float(dist)) * (18)
				e.global_position += Vector2(push_x, 0.0)
				e.global_position += Vector2(0.0, push_y)
	b.kit_fx_cast("r")
	b.kit_fx_impact(b.global_position.x, b.global_position.y, 200, "r")
	b._shake(25.0)
	heal = int((b.max_hp) * (0.1))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5714-5762
static func _cast_q_tide_bringer(b, enemies):
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var line_width = null
	var max_range = null
	var perp = null
	var proj = null
	var stats = null

	b.kit["q_timer"] = 240
	b.kit["active_skill"] = "q"
	b.kit["active_skill_timer"] = 45
	stats = b.kit_get_stats()
	damage = stats.get("skill_q_damage", 380)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 250
	line_width = 70
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (line_width):
				b.kit_skill_hit(e, damage)
	b.kit_fx_cast("q")
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 250, "q")
	else:
		b.kit_fx_impact((b.global_position.x) + ((dx) * (220)), (b.global_position.y) + ((dy) * (220)), 250, "q")
	b._shake(15.0)


## bosses/base_boss.py:5764-5788
static func _cast_w_x_marks(b, enemies):
	b.kit["w_timer"] = 300
	b.kit["active_skill"] = "w"
	b.kit["active_skill_timer"] = 80
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit["x_mark_target"] = b.target
		b.kit["x_mark_timer"] = 120
	b.kit_fx_cast("w")
	if (b.kit["x_mark_target"]) and (b.kit_unit_alive(b.kit["x_mark_target"])):
		b.kit_fx_impact(b.kit["x_mark_target"].global_position.x, b.kit["x_mark_target"].global_position.y, 120, "w")
	else:
		b.kit_fx_impact(b.global_position.x, b.global_position.y, 120, "w")
	b._shake(8.0)


## bosses/base_boss.py:5790-5861
static func _cast_e_ghost_ship(b, enemies):
	var base_damage = null
	var damage = null
	var dist = null
	var dx = null
	var dy = null
	var ex = null
	var ey = null
	var game = null
	var heal = null
	var max_range = null
	var perp = null
	var proj = null
	var ship_width = null
	var stats = null

	b.kit["e_timer"] = 480
	b.kit["active_skill"] = "e"
	b.kit["active_skill_timer"] = 90
	stats = b.kit_get_stats()
	damage = stats.get("skill_e_damage", 450)
	if (not (b.target)) or (not (b.kit_unit_alive(b.target))):
		return
	dx = (b.target.global_position.x) - (b.global_position.x)
	dy = (b.target.global_position.y) - (b.global_position.y)
	dist = Vector2(dx, dy).length()
	if (dist) == (0):
		return
	dx = float(dx) / float(dist)
	dy = float(dy) / float(dist)
	max_range = 300
	ship_width = 80
	for e in enemies:
		ex = (e.global_position.x) - (b.global_position.x)
		ey = (e.global_position.y) - (b.global_position.y)
		proj = ((ex) * (dx)) + ((ey) * (dy))
		if (0) < (proj) and (proj) < (max_range):
			perp = absf(((ex) * (-(dy))) + ((ey) * (dx)))
			if (perp) < (ship_width):
				b.kit_skill_hit(e, damage)
				if "attack_timer" in e:
					b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 90))
	b.kit["rum_buff_active"] = true
	b.kit["rum_buff_timer"] = 480
	base_damage = stats.get("damage", 125)
	b.damage = int((base_damage) * (1.3))
	heal = int((b.max_hp) * (0.15))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b.kit_fx_cast("e")
	if (b.target) and (b.kit_unit_alive(b.target)):
		b.kit_fx_impact(b.target.global_position.x, b.target.global_position.y, 300, "e")
	else:
		b.kit_fx_impact((b.global_position.x) + ((dx) * (240)), (b.global_position.y) + ((dy) * (240)), 300, "e")
	b._shake(18.0)
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:5863-5919
static func _cast_r_torrent(b, enemies):
	var damage = null
	var dist = null
	var game = null
	var heal = null
	var push_x = null
	var push_y = null
	var stats = null
	var tx = null
	var ty = null

	b.kit["r_timer"] = 720
	b.kit["active_skill"] = "r"
	b.kit["active_skill_timer"] = 100
	stats = b.kit_get_stats()
	damage = stats.get("skill_r_damage", 650)
	if (b.target) and (b.kit_unit_alive(b.target)):
		tx = b.target.global_position.x
		ty = b.target.global_position.y
	else:
		tx = b.global_position.x
		ty = b.global_position.y
	for e in enemies:
		if (Vector2((e.global_position.x) - (tx), (e.global_position.y) - (ty)).length()) <= (200):
			b.kit_skill_hit(e, damage)
			if "attack_timer" in e:
				b.kit_lock_attack(e, maxf(b.kit_atk_timer(e), 120))
			dist = Vector2((e.global_position.x) - (tx), (e.global_position.y) - (ty)).length()
			if ((dist) > (0)) and (b.kit_can_move(e)):
				push_x = (float((e.global_position.x) - (tx)) / float(dist)) * (20)
				push_y = (float((e.global_position.y) - (ty)) / float(dist)) * (20)
				e.global_position += Vector2(push_x, 0.0)
				e.global_position += Vector2(0.0, push_y)
	b.kit_fx_cast("r")
	b.kit_fx_impact(tx, ty, 200, "r")
	b._shake(28.0)
	heal = int((b.max_hp) * (0.2))
	b.hp = minf(b.max_hp, (b.hp) + (heal))
	b._callout("+" + str(heal), true)


## bosses/base_boss.py:6431-6438
static func _init_l9_timers(b):
	if not b.kit["kit_ready"]:
		b.kit["q_timer"] = 0
		b.kit["w_timer"] = 0
		b.kit["e_timer"] = 0
		b.kit["r_timer"] = 0
		b.kit["active_skill"] = null
		b.kit["active_skill_timer"] = 0
		b.kit["kit_ready"] = true


## bosses/base_boss.py:6440-6448
static func _tick_l9_timers(b):
	if (b.kit["q_timer"]) > (0):
		b.kit["q_timer"] -= 1
	if (b.kit["w_timer"]) > (0):
		b.kit["w_timer"] -= 1
	if (b.kit["e_timer"]) > (0):
		b.kit["e_timer"] -= 1
	if (b.kit["r_timer"]) > (0):
		b.kit["r_timer"] -= 1
	if (b.kit["active_skill_timer"]) > (0):
		b.kit["active_skill_timer"] -= 1
		if (b.kit["active_skill_timer"]) <= (0):
			b.kit["active_skill"] = null


## bosses/base_boss.py:6457-6468
static func _l9_target(b, enemies):
	var best = null
	var best_d = null
	var d = null

	best = null
	best_d = 999999
	for e in enemies:
		if not (b.kit_unit_alive(e)):
			continue
		d = Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()
		if (d) < (best_d):
			best_d = d
			best = e
	return best


## bosses/base_boss.py:6470-6478
static func _l9_aoe(b, enemies, radius, damage):
	var hit = null

	hit = 0
	for e in enemies:
		if not (b.kit_unit_alive(e)):
			continue
		if (Vector2((e.global_position.x) - (b.global_position.x), (e.global_position.y) - (b.global_position.y)).length()) <= (radius):
			b.kit_skill_hit(e, damage)
			hit += 1
	return hit
