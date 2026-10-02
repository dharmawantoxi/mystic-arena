# gdlint:disable=max-file-lines,max-line-length
extends RefCounted
## Layer 8d native suite: source ability casts and smart-AI dispatch.
## The fixture is produced by executing the original Boss methods; these checks
## replay the same first-slice cases through BossAI and the live combat hit path.

const BossAI = preload("res://scripts/match/boss_ai.gd")
const HeroState = preload("res://scripts/combat/hero_state.gd")
const UnitState = preload("res://scripts/combat/unit_state.gd")
const Prototype = preload("res://scripts/match/prototype_battle.gd")
const THORNE = preload("res://data/heroes/thorne.tres")
const FIXTURE := "res://tests/fixtures/boss_ability_source.json"


func run(check: Callable) -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(fixture is Dictionary and fixture.has("cases"), "boss ability fixture parses")
	if not fixture is Dictionary or not fixture.has("cases"):
		return
	var cases: Array = fixture["cases"]
	check.call(cases.size() == 319, "boss ability fixture has all first-slice cases")
	_case(check, cases, "gornak_q", "gornak", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(check, cases, "gornak_blink", "gornak", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"gornak_counterspell",
		"gornak",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "gornak_mana_void", "gornak", 0.3, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "morgath_spark", "morgath", 1.0, [[330, 0, 10000, "target"]], 330.0)
	_case(check, cases, "morgath_flux", "morgath", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"morgath_field",
		"morgath",
		1.0,
		[[20, 0, 10000, "a"], [30, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "morgath_clones", "morgath", 0.4, [[20, 0, 10000, "target"]], 20.0)
	_persistent_flux(check, cases)
	_case(check, cases, "drakar_rage", "drakar", 0.3, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"drakar_counter_helix",
		"drakar",
		1.0,
		[[20, 0, 10000, "a"], [30, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "drakar_call", "drakar", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "drakar_culling", "drakar", 1.0, [[50, 0, 1000, "target", 10000]], 50.0)
	_case(check, cases, "abaddon_coil", "abaddon", 1.0, [[100, 0, 10000, "target"]], 100.0)
	# The source fixture isolates _smart_ai_abaddon. The live Boss.update heal
	# runs before that method, so hold its cooldown here to replay the cast.
	_case(check, cases, "abaddon_shield", "abaddon", 0.2, [[20, 0, 10000, "target"]], 20.0, true)
	_case(check, cases, "abaddon_gale", "abaddon", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"abaddon_death_sever",
		"abaddon",
		1.0,
		[[20, 0, 10000, "a"], [30, 0, 10000, "b"], [40, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"alchemist_greevils_greed",
		"alchemist",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"alchemist_chemical_rage",
		"alchemist",
		0.5,
		[[300, 0, 10000, "target"]],
		300.0
	)
	_case(
		check,
		cases,
		"alchemist_unstable_concoction",
		"alchemist",
		1.0,
		[[100, 0, 10000, "a"], [150, 0, 10000, "b"]],
		100.0
	)
	_case(
		check, cases, "alchemist_acid_spray", "alchemist", 1.0, [[100, 0, 10000, "target"]], 100.0
	)
	_case(
		check,
		cases,
		"malzareth_death_pulse",
		"malzareth",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"malzareth_shadow_word",
		"malzareth",
		1.0,
		[[100, 0, 10000, "target"], [140, 0, 10000, "splash"]],
		100.0
	)
	_case(
		check, cases, "malzareth_nether_blast", "malzareth", 1.0, [[100, 0, 10000, "target"]], 100.0
	)
	_case(check, cases, "malzareth_void", "malzareth", 1.0, [[270, 0, 10000, "target"]], 270.0)
	_case(
		check,
		cases,
		"akashari_sonic_scream",
		"akashari",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"akashari_scream_of_pain",
		"akashari",
		1.0,
		[[100, 0, 10000, "a"], [120, 0, 10000, "b"], [140, 0, 10000, "c"]],
		100.0
	)
	_case(
		check,
		cases,
		"akashari_shadow_strike",
		"akashari",
		0.5,
		[[200, 0, 10000, "target"], [220, 0, 10000, "near"]],
		200.0
	)
	_case(check, cases, "akashari_scream", "akashari", 1.0, [[270, 0, 10000, "target"]], 270.0)
	_case(
		check,
		cases,
		"vorenmarr_chaos_storm",
		"vorenmarr",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check, cases, "vorenmarr_shadow_word", "vorenmarr", 0.5, [[300, 0, 10000, "target"]], 300.0
	)
	_case(
		check,
		cases,
		"vorenmarr_rain_of_fire",
		"vorenmarr",
		1.0,
		[[100, 0, 10000, "target"], [150, 0, 10000, "near"]],
		100.0
	)
	_case(
		check, cases, "vorenmarr_chaos_bolt", "vorenmarr", 1.0, [[270, 0, 10000, "target"]], 270.0
	)
	_case(
		check,
		cases,
		"nyxarath_requiem",
		"nyxarath",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "nyxarath_presence", "nyxarath", 0.5, [[300, 0, 10000, "target"]], 300.0)
	_case(
		check,
		cases,
		"nyxarath_necromastery",
		"nyxarath",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "nyxarath_shadowraze", "nyxarath", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"thalgryn_replicate",
		"thalgryn",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "thalgryn_morph", "thalgryn", 0.5, [[300, 0, 10000, "target"]], 300.0)
	_case(
		check,
		cases,
		"thalgryn_waveform",
		"thalgryn",
		1.0,
		[[300, 0, 10000, "target"], [100, 0, 10000, "path"]],
		300.0
	)
	_case(
		check,
		cases,
		"thalgryn_adaptive_strike",
		"thalgryn",
		1.0,
		[[100, 0, 10000, "target"], [150, 0, 10000, "splash"]],
		100.0
	)
	_case(
		check,
		cases,
		"syrentha_song_of_siren",
		"syrentha",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check, cases, "syrentha_mirror_image", "syrentha", 0.5, [[300, 0, 10000, "target"]], 300.0
	)
	_case(
		check,
		cases,
		"syrentha_enchanting_song",
		"syrentha",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"syrentha_riptide",
		"syrentha",
		1.0,
		[[100, 0, 10000, "target"], [150, 50, 10000, "splash"]],
		100.0
	)
	_case(
		check,
		cases,
		"gravewake_ravage",
		"gravewake",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check, cases, "gravewake_kraken_shell", "gravewake", 0.5, [[300, 0, 10000, "target"]], 300.0
	)
	_case(
		check,
		cases,
		"gravewake_tidebringer",
		"gravewake",
		1.0,
		[[100, 0, 10000, "target"], [150, 60, 10000, "near"], [300, 0, 10000, "far"]],
		100.0
	)
	_case(
		check,
		cases,
		"gravewake_anchor_smash",
		"gravewake",
		1.0,
		[[100, 0, 10000, "target"], [190, 0, 10000, "wave"]],
		100.0
	)
	_case(
		check,
		cases,
		"kunkka_torrent",
		"kunkka",
		0.35,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"kunkka_ghost_ship",
		"kunkka",
		0.5,
		[[250, 0, 10000, "target"], [200, 100, 10000, "off_path"]],
		250.0
	)
	_case(
		check,
		cases,
		"kunkka_x_marks",
		"kunkka",
		1.0,
		[[100, 0, 10000, "target"], [150, 60, 10000, "near"]],
		100.0
	)
	_case(
		check,
		cases,
		"kunkka_tide_bringer",
		"kunkka",
		1.0,
		[[100, 0, 10000, "target"], [240, 0, 10000, "wave"]],
		100.0
	)
	# The X Marks the Spot burst lands on a later tick, so hold every cooldown
	# and expire the mark, mirroring the Morgath flux tick case.
	_case(
		check,
		cases,
		"kunkka_x_mark_burst",
		"kunkka",
		1.0,
		[[60, 0, 10000, "marked"], [150, 0, 10000, "near"], [400, 0, 10000, "far"]],
		60.0
	)
	_case(
		check,
		cases,
		"razak_firestorm",
		"razak",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"razak_firefly",
		"razak",
		1.0,
		[[200, 0, 10000, "target"], [60, 0, 10000, "near"]],
		200.0
	)
	_case(
		check,
		cases,
		"razak_flame_cone",
		"razak",
		1.0,
		[[100, 0, 10000, "target"], [150, 40, 10000, "near"]],
		100.0
	)
	_case(
		check,
		cases,
		"razak_molotov",
		"razak",
		1.0,
		[[260, 0, 10000, "target"], [100, 0, 10000, "near"], [300, 40, 10000, "splash"]],
		260.0
	)
	_case(
		check,
		cases,
		"kenshiro_supremacy",
		"kenshiro",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "kenshiro_assault", "kenshiro", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"kenshiro_gale",
		"kenshiro",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "kenshiro_swiftslash", "kenshiro", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"khazan_vanishing_execution",
		"khazan",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"khazan_spin_carnage",
		"khazan",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "khazan_leap_smash", "khazan", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "khazan_chained_blade", "khazan", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"wiro_typhoon",
		"wiro",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "wiro_whirl", "wiro", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "wiro_dash", "wiro", 0.4, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "wiro_wind_cut", "wiro", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"naraka_execute",
		"naraka",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"naraka_chain_hammer",
		"naraka",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "naraka_shadowstep", "naraka", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "naraka_chaos", "naraka", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"krognarr_eruption",
		"krognarr",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "krognarr_rampart", "krognarr", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"krognarr_seismic",
		"krognarr",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "krognarr_stone_strike", "krognarr", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"raz_gloom_leap",
		"raz",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "raz_searing_dash", "raz", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "raz_surge", "raz", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "raz_overdrive", "raz", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"vraskhan_omni_arms",
		"vraskhan",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "vraskhan_shadow_leap", "vraskhan", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"vraskhan_death_slash",
		"vraskhan",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "vraskhan_thorned", "vraskhan", 1.0, [[80, 0, 10000, "target"]], 80.0)
	_case(
		check,
		cases,
		"aurethzar_r",
		"aurethzar",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"aurethzar_w",
		"aurethzar",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "aurethzar_e", "aurethzar", 1.0, [[140, 0, 10000, "target"]], 140.0)
	_case(check, cases, "aurethzar_q", "aurethzar", 1.0, [[300, 0, 10000, "target"]], 300.0)
	_case(
		check,
		cases,
		"aeralith_r",
		"aeralith",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"aeralith_e",
		"aeralith",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"aeralith_w",
		"aeralith",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "aeralith_q", "aeralith", 1.0, [[300, 0, 10000, "target"]], 300.0)
	_case(
		check,
		cases,
		"aurex_r",
		"aurex",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "aurex_e", "aurex", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "aurex_w", "aurex", 1.0, [[260, 0, 10000, "target"]], 260.0)
	_case(check, cases, "aurex_q", "aurex", 1.0, [[140, 0, 10000, "target"]], 140.0)
	_case(
		check,
		cases,
		"nyxareva_r",
		"nyxareva",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"nyxareva_e",
		"nyxareva",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "nyxareva_w", "nyxareva", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "nyxareva_q", "nyxareva", 1.0, [[150, 0, 10000, "target"]], 150.0)
	_case(
		check,
		cases,
		"thalakryon_r",
		"thalakryon",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"thalakryon_e",
		"thalakryon",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"thalakryon_w",
		"thalakryon",
		0.5499999999999999,
		[[200, 0, 10000, "target"]],
		200.0
	)
	_case(check, cases, "thalakryon_q", "thalakryon", 1.0, [[320, 0, 10000, "target"]], 320.0)
	_case(
		check,
		cases,
		"aurelix_r",
		"aurelix",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check, cases, "aurelix_e", "aurelix", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "aurelix_w", "aurelix", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "aurelix_q", "aurelix", 1.0, [[300, 0, 10000, "target"]], 300.0)
	_case(
		check,
		cases,
		"aurelyssa_r",
		"aurelyssa",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"aurelyssa_e",
		"aurelyssa",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "aurelyssa_w", "aurelyssa", 0.5, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "aurelyssa_q", "aurelyssa", 1.0, [[140, 0, 10000, "target"]], 140.0)
	_case(
		check,
		cases,
		"vargrath_r",
		"vargrath",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "vargrath_w", "vargrath", 1.0, [[220, 0, 10000, "target"]], 220.0)
	_case(
		check,
		cases,
		"vargrath_e",
		"vargrath",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "vargrath_q", "vargrath", 1.0, [[140, 0, 10000, "target"]], 140.0)
	_case(
		check,
		cases,
		"nazulmor_r",
		"nazulmor",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"nazulmor_e",
		"nazulmor",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"nazulmor_w",
		"nazulmor",
		0.5499999999999999,
		[[200, 0, 10000, "target"]],
		200.0
	)
	_case(check, cases, "nazulmor_q", "nazulmor", 1.0, [[330, 0, 10000, "target"]], 330.0)
	_case(
		check,
		cases,
		"kaeldris_r",
		"kaeldris",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"kaeldris_e",
		"kaeldris",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "kaeldris_w", "kaeldris", 1.0, [[220, 0, 10000, "target"]], 220.0)
	_case(check, cases, "kaeldris_q", "kaeldris", 1.0, [[140, 0, 10000, "target"]], 140.0)
	_case(
		check,
		cases,
		"pyraklos_r",
		"pyraklos",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "pyraklos_e", "pyraklos", 0.45, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"pyraklos_w",
		"pyraklos",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "pyraklos_q", "pyraklos", 1.0, [[160, 0, 10000, "target"]], 160.0)
	_case(
		check,
		cases,
		"velmyrth_r",
		"velmyrth",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "velmyrth_w", "velmyrth", 1.0, [[230, 0, 10000, "target"]], 230.0)
	_case(
		check,
		cases,
		"velmyrth_e",
		"velmyrth",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "velmyrth_q", "velmyrth", 1.0, [[140, 0, 10000, "target"]], 140.0)
	_case(
		check,
		cases,
		"solvarin_r",
		"solvarin",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"solvarin_e",
		"solvarin",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"solvarin_w",
		"solvarin",
		0.5499999999999999,
		[[200, 0, 10000, "target"]],
		200.0
	)
	_case(check, cases, "solvarin_q", "solvarin", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"azureth_r",
		"azureth",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check, cases, "azureth_e", "azureth", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(
		check, cases, "azureth_w", "azureth", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "azureth_q", "azureth", 1.0, [[380, 0, 10000, "target"]], 380.0)
	_case(
		check,
		cases,
		"luminar_r",
		"luminar",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check, cases, "luminar_e", "luminar", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(
		check, cases, "luminar_w", "luminar", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "luminar_q", "luminar", 1.0, [[390, 0, 10000, "target"]], 390.0)
	_case(
		check,
		cases,
		"solara_r",
		"solara",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "solara_w", "solara", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "solara_e", "solara", 0.6, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "solara_q", "solara", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"pyraethis_r",
		"pyraethis",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"pyraethis_e",
		"pyraethis",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"pyraethis_w",
		"pyraethis",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "pyraethis_q", "pyraethis", 1.0, [[410, 0, 10000, "target"]], 410.0)
	_case(
		check,
		cases,
		"auroth_r",
		"auroth",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "auroth_e", "auroth", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(
		check, cases, "auroth_w", "auroth", 0.5499999999999999, [[200, 0, 10000, "target"]], 200.0
	)
	_case(check, cases, "auroth_q", "auroth", 1.0, [[330, 0, 10000, "target"]], 330.0)
	_case(
		check,
		cases,
		"morvein_r",
		"morvein",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check, cases, "morvein_e", "morvein", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(
		check, cases, "morvein_w", "morvein", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "morvein_q", "morvein", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"thorvak_r",
		"thorvak",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check, cases, "thorvak_w", "thorvak", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "thorvak_e", "thorvak", 0.6, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "thorvak_q", "thorvak", 1.0, [[330, 0, 10000, "target"]], 330.0)
	_case(
		check,
		cases,
		"yamako_r",
		"yamako",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "yamako_e", "yamako", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "yamako_w", "yamako", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "yamako_q", "yamako", 1.0, [[380, 0, 10000, "target"]], 380.0)
	_case(
		check,
		cases,
		"ignirus_r",
		"ignirus",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check, cases, "ignirus_e", "ignirus", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(
		check, cases, "ignirus_w", "ignirus", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "ignirus_q", "ignirus", 1.0, [[390, 0, 10000, "target"]], 390.0)
	_case(check, cases, "leoric_r", "leoric", 0.4, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "leoric_e", "leoric", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "leoric_w", "leoric", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "leoric_q", "leoric", 1.0, [[330, 0, 10000, "target"]], 330.0)
	_case(
		check,
		cases,
		"shirotaka_r",
		"shirotaka",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"shirotaka_e",
		"shirotaka",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"shirotaka_w",
		"shirotaka",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "shirotaka_q", "shirotaka", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"seiryukong_r",
		"seiryukong",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"seiryukong_e",
		"seiryukong",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"seiryukong_w",
		"seiryukong",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "seiryukong_q", "seiryukong", 1.0, [[380, 0, 10000, "target"]], 380.0)
	_case(
		check,
		cases,
		"kaelthorn_r",
		"kaelthorn",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"kaelthorn_e",
		"kaelthorn",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"kaelthorn_w",
		"kaelthorn",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "kaelthorn_q", "kaelthorn", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"solvanth_r",
		"solvanth",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"solvanth_e",
		"solvanth",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"solvanth_w",
		"solvanth",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "solvanth_q", "solvanth", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"xyrael_r",
		"xyrael",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "xyrael_e", "xyrael", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "xyrael_w", "xyrael", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "xyrael_q", "xyrael", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"nyxareth_4",
		"nyxareth",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"nyxareth_3",
		"nyxareth",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"nyxareth_2",
		"nyxareth",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "nyxareth_1", "nyxareth", 1.0, [[400, 0, 10000, "target"]], 400.0)
	_case(
		check,
		cases,
		"cryssalia_r",
		"cryssalia",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"cryssalia_e",
		"cryssalia",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"cryssalia_w",
		"cryssalia",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "cryssalia_q", "cryssalia", 1.0, [[400, 0, 10000, "target"]], 400.0)
	_case(
		check,
		cases,
		"kaelthar_r",
		"kaelthar",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"kaelthar_e",
		"kaelthar",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"kaelthar_w",
		"kaelthar",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "kaelthar_q", "kaelthar", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"morkhaera_r",
		"morkhaera",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"morkhaera_e",
		"morkhaera",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"morkhaera_w",
		"morkhaera",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "morkhaera_q", "morkhaera", 1.0, [[400, 0, 10000, "target"]], 400.0)
	_case(
		check,
		cases,
		"aurelion_r",
		"aurelion",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"aurelion_e",
		"aurelion",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"aurelion_w",
		"aurelion",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "aurelion_q", "aurelion", 1.0, [[380, 0, 10000, "target"]], 380.0)
	_case(
		check,
		cases,
		"akahime_r",
		"akahime",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check, cases, "akahime_e", "akahime", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(
		check, cases, "akahime_w", "akahime", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "akahime_q", "akahime", 1.0, [[390, 0, 10000, "target"]], 390.0)
	_case(
		check,
		cases,
		"nyxthrael_r",
		"nyxthrael",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"nyxthrael_e",
		"nyxthrael",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"nyxthrael_w",
		"nyxthrael",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "nyxthrael_q", "nyxthrael", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"sylvantheros_r",
		"sylvantheros",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"sylvantheros_e",
		"sylvantheros",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"sylvantheros_w",
		"sylvantheros",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "sylvantheros_q", "sylvantheros", 1.0, [[400, 0, 10000, "target"]], 400.0)
	_case(
		check,
		cases,
		"vaelindra_r",
		"vaelindra",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"vaelindra_e",
		"vaelindra",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"vaelindra_w",
		"vaelindra",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "vaelindra_q", "vaelindra", 1.0, [[410, 0, 10000, "target"]], 410.0)
	_case(
		check,
		cases,
		"astraelion_r",
		"astraelion",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"astraelion_e",
		"astraelion",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"astraelion_w",
		"astraelion",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "astraelion_q", "astraelion", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"morvaenthir_r",
		"morvaenthir",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"morvaenthir_e",
		"morvaenthir",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"morvaenthir_w",
		"morvaenthir",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "morvaenthir_q", "morvaenthir", 1.0, [[400, 0, 10000, "target"]], 400.0)
	_case(
		check,
		cases,
		"thornvaegrim_r",
		"thornvaegrim",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"thornvaegrim_e",
		"thornvaegrim",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"thornvaegrim_w",
		"thornvaegrim",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "thornvaegrim_q", "thornvaegrim", 1.0, [[340, 0, 10000, "target"]], 340.0)
	_case(
		check,
		cases,
		"morthraxis_r",
		"morthraxis",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"morthraxis_e",
		"morthraxis",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"morthraxis_w",
		"morthraxis",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "morthraxis_q", "morthraxis", 1.0, [[410, 0, 10000, "target"]], 410.0)
	_case(
		check,
		cases,
		"ancient_apparition_r",
		"ancient_apparition",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"ancient_apparition_q",
		"ancient_apparition",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(
		check,
		cases,
		"ancient_apparition_e",
		"ancient_apparition",
		1.0,
		[[300, 0, 10000, "target"]],
		300.0
	)
	_case(
		check,
		cases,
		"ancient_apparition_w",
		"ancient_apparition",
		1.0,
		[[100, 0, 10000, "target"]],
		100.0
	)
	_case(
		check,
		cases,
		"ignis_drachorn_r",
		"ignis_drachorn",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "ignis_drachorn_e", "ignis_drachorn", 0.6, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"ignis_drachorn_w",
		"ignis_drachorn",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check, cases, "ignis_drachorn_q", "ignis_drachorn", 1.0, [[100, 0, 10000, "target"]], 100.0
	)
	_case(
		check,
		cases,
		"vhorethzir_r",
		"vhorethzir",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "vhorethzir_e", "vhorethzir", 0.5, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"vhorethzir_w",
		"vhorethzir",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "vhorethzir_q", "vhorethzir", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "vaerith_r", "vaerith", 0.4, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "vaerith_e", "vaerith", 0.6, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check, cases, "vaerith_w", "vaerith", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0
	)
	_case(check, cases, "vaerith_q", "vaerith", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "xirthalis_r", "xirthalis", 0.3, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "xirthalis_q", "xirthalis", 0.6, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"xirthalis_w",
		"xirthalis",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "xirthalis_e", "xirthalis", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"vhyssarion_r",
		"vhyssarion",
		0.4,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"vhyssarion_q",
		"vhyssarion",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(
		check,
		cases,
		"vhyssarion_e",
		"vhyssarion",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "vhyssarion_w", "vhyssarion", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"khalros_r",
		"khalros",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "khalros_w", "khalros", 0.6, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "khalros_e", "khalros", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "khalros_q", "khalros", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "gorath_r_low", "gorath", 1.0, [[20, 0, 1000, "target", 10000]], 20.0)
	_case(check, cases, "gorath_q", "gorath", 0.6, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "gorath_w", "gorath", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "gorath_e", "gorath", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(
		check,
		cases,
		"varkul_r",
		"varkul",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "varkul_e", "varkul", 0.4, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "varkul_w", "varkul", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "varkul_q", "varkul", 1.0, [[260, 0, 10000, "target"]], 260.0)
	_case(
		check,
		cases,
		"xerathis_r",
		"xerathis",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"], [80, 0, 10000, "d"]],
		20.0
	)
	_case(check, cases, "xerathis_e", "xerathis", 1.0, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"xerathis_q",
		"xerathis",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "xerathis_w", "xerathis", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "nyzrak_r", "nyzrak", 0.4, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "nyzrak_e", "nyzrak", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "nyzrak_w", "nyzrak", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "nyzrak_q", "nyzrak", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "zharok_r", "zharok", 0.3, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "zharok_e", "zharok", 1.0, [[20, 0, 10000, "a"], [40, 0, 10000, "b"]], 20.0)
	_case(check, cases, "zharok_w", "zharok", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "zharok_q", "zharok", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "pyrenth_r", "pyrenth", 0.3, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"pyrenth_e",
		"pyrenth",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "pyrenth_w", "pyrenth", 0.5, [[20, 0, 10000, "target"]], 20.0)
	_case(check, cases, "pyrenth_q", "pyrenth", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "vokrahn_r", "vokrahn", 0.4, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"vokrahn_w",
		"vokrahn",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "vokrahn_e", "vokrahn", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "vokrahn_q", "vokrahn", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "nyxara_r", "nyxara", 0.4, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"nyxara_e",
		"nyxara",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "nyxara_w", "nyxara", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(check, cases, "nyxara_q", "nyxara", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"gravefang_r",
		"gravefang",
		0.3,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "gravefang_w", "gravefang", 1.0, [[200, 0, 10000, "target"]], 200.0)
	_case(check, cases, "gravefang_e", "gravefang", 1.0, [[100, 0, 10000, "target"]], 100.0)
	_case(
		check,
		cases,
		"gravefang_q",
		"gravefang",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"]],
		20.0
	)
	_case(check, cases, "vhalzun_r", "vhalzun", 0.3, [[20, 0, 10000, "target"]], 20.0)
	_case(
		check,
		cases,
		"vhalzun_w",
		"vhalzun",
		1.0,
		[[20, 0, 10000, "a"], [40, 0, 10000, "b"], [60, 0, 10000, "c"]],
		20.0
	)
	_case(check, cases, "vhalzun_e", "vhalzun", 1.0, [[150, 0, 10000, "target"]], 150.0)
	_case(check, cases, "vhalzun_q", "vhalzun", 1.0, [[20, 0, 10000, "target"]], 20.0)
	_generic(check, cases)
	_true_boss_heal(check)


func _world(kind: String, hp_ratio: float) -> Array:
	var world := Prototype.new()
	world.setup_arena()
	var boss := world._spawn_boss(kind)
	boss.position = Vector2.ZERO
	boss.previous_position = boss.position
	boss.hp = float(int(float(boss.max_hp) * hp_ratio))
	return [world, boss]


func _target(world: Prototype, spec: Array) -> HeroState:
	var target := world.spawn_hero(THORNE, world.BLUE, Vector2(float(spec[0]), float(spec[1])))
	target.max_hp = float(int(spec[4]) if spec.size() > 4 else int(spec[2]))
	target.hp = float(int(spec[2]))
	target.alive = target.hp > 0.0
	target.attack_timer = 0
	return target


func _case(
	check: Callable,
	cases: Array,
	label: String,
	kind: String,
	hp_ratio: float,
	specs: Array,
	distance: float,
	hold_true_heal: bool = false
) -> void:
	var expected := _fixture_case(cases, label)
	check.call(not expected.is_empty(), "%s fixture row exists" % label)
	if expected.is_empty():
		return
	var pair := _world(kind, hp_ratio)
	var world: Prototype = pair[0]
	var boss = pair[1]
	var enemies: Array[UnitState] = []
	for spec in specs:
		var target := _target(world, spec)
		enemies.append(target)
	if hold_true_heal:
		boss.ability2_timer = 999
	if label == "morgath_flux_tick":
		boss.q_timer = 999
		boss.w_timer = 999
		boss.e_timer = 999
		boss.r_timer = 999
		boss.flux_target_id = enemies[0].id
		boss.flux_active_timer = 31
	if label == "kunkka_x_mark_burst":
		boss.q_timer = 999
		boss.w_timer = 999
		boss.e_timer = 999
		boss.r_timer = 999
		boss.x_mark_target_id = enemies[0].id
		boss.x_mark_timer = 1
	BossAI.tick(world, boss, enemies, enemies[0], distance)
	_compare(check, expected["result"], boss, enemies, label)


func _persistent_flux(check: Callable, cases: Array) -> void:
	_case(check, cases, "morgath_flux_tick", "morgath", 1.0, [[400, 0, 10000, "flux"]], 400.0)


func _generic(check: Callable, cases: Array) -> void:
	var expected := _fixture_case(cases, "generic_ability")
	var pair := _world("abaddon", 1.0)
	var world: Prototype = pair[0]
	var boss = pair[1]
	boss.ability_cooldown = 180
	boss.ability_damage_value = 270
	boss.ability_range = 50.0
	boss.ability_timer = 0
	var enemies: Array[UnitState] = []
	for spec in [[20, 0, 10000, "near"], [100, 0, 10000, "far"]]:
		enemies.append(_target(world, spec))
	BossAI._generic(world, boss, enemies)
	_compare(check, expected["result"], boss, enemies, "generic_ability")
	check.call(boss.ability_active_timer == 60, "generic ability active window is sixty ticks")


func _true_boss_heal(check: Callable) -> void:
	var pair := _world("abaddon", 0.2)
	var world: Prototype = pair[0]
	var boss = pair[1]
	var enemies: Array[UnitState] = [_target(world, [200, 0, 10000, "target"])]
	BossAI.tick(world, boss, enemies, enemies[0], 200.0)
	check.call(boss.hp == 18000.0, "true boss heal uses source percentage")
	check.call(boss.ability2_timer == boss.ability2_cooldown, "true boss heal starts cooldown")
	check.call(boss.active_skill == "e", "true boss heals before smart ability selection")


func _fixture_case(cases: Array, label: String) -> Dictionary:
	for entry in cases:
		if String(entry.get("label", "")) == label:
			return entry
	return {}


func _compare(
	check: Callable, expected: Dictionary, boss, enemies: Array[UnitState], label: String = ""
) -> void:
	var expected_skill: Variant = expected.get("skill", null)
	var actual_skill: Variant = boss.active_skill if not boss.active_skill.is_empty() else null
	check.call(actual_skill == expected_skill, "%s %s active skill" % [label, expected["type"]])
	check.call(
		boss.active_skill_timer == int(expected["active_skill_timer"]),
		"%s %s active skill timer" % [label, expected["type"]]
	)
	for field in [
		"q_timer",
		"w_timer",
		"e_timer",
		"r_timer",
		"ability_timer",
		"hp",
		"damage",
		"rage_timer",
		"necro_buff_timer",
		"presence_timer",
		"morph_buff_timer",
		"mirror_buff_timer",
		"shell_timer",
		"rum_buff_timer",
		"x_mark_timer",
		"defense_timer",
		"flux_active_timer",
		"clones_active_timer"
	]:
		var actual: Variant = boss.hp if field == "hp" else boss.get(field)
		check.call(
			int(actual) == int(expected[field]), "%s %s %s" % [label, expected["type"], field]
		)
	check.call(
		boss.ability_active == bool(expected["ability_active"]),
		"%s %s generic active flag" % [label, expected["type"]]
	)
	check.call(
		(
			is_equal_approx(boss.position.x, float(expected["x"]))
			and is_equal_approx(boss.position.y, float(expected["y"]))
		),
		"%s %s position" % [label, expected["type"]]
	)
	check.call(boss.rage_active == bool(expected["rage_active"]), "%s rage flag" % label)
	check.call(
		boss.necro_buff_active == bool(expected["necro_buff_active"]),
		"%s necromastery flag" % label
	)
	check.call(
		boss.presence_active == bool(expected["presence_active"]), "%s presence flag" % label
	)
	check.call(
		boss.morph_buff_active == bool(expected["morph_buff_active"]), "%s morph flag" % label
	)
	check.call(
		boss.mirror_buff_active == bool(expected["mirror_buff_active"]), "%s mirror flag" % label
	)
	check.call(boss.shell_active == bool(expected["shell_active"]), "%s kraken shell flag" % label)
	check.call(
		boss.rum_buff_active == bool(expected["rum_buff_active"]), "%s rum buff flag" % label
	)
	check.call(boss.defense_boost == bool(expected["defense_boost"]), "%s defense flag" % label)
	var expected_targets: Array = expected["targets"]
	check.call(enemies.size() == expected_targets.size(), "%s target count" % label)
	for index in range(mini(enemies.size(), expected_targets.size())):
		var target := enemies[index] as HeroState
		var row: Dictionary = expected_targets[index]
		var expected_hits: Array = row["hits"]
		var start_hp := 10000
		if row["name"] == "target" and expected["type"] == "drakar" and row["hp"] == 0:
			start_hp = 1000
		if label == "gorath_r_low" and row["name"] == "target":
			start_hp = 1000
		check.call(target.hp == float(row["hp"]), "%s %s target hp" % [label, row["name"]])
		check.call(target.alive == bool(row["alive"]), "%s %s target alive" % [label, row["name"]])
		var damage_taken := start_hp - int(target.hp)
		var expected_damage := 0
		for hit in expected_hits:
			expected_damage += int(hit)
		check.call(
			damage_taken == mini(start_hp, expected_damage),
			"%s %s target damage" % [label, row["name"]]
		)
		check.call(
			target.attack_timer == int(row["attack_timer"]),
			"%s %s attack lock" % [label, row["name"]]
		)
		var slows: Array = row["slows"]
		if slows.is_empty():
			check.call(target.slow_timer == 0, "%s %s has no slow" % [label, row["name"]])
		else:
			check.call(
				(
					is_equal_approx(target.slow_amount, float(slows[0][0]))
					and target.slow_timer == int(slows[0][1])
				),
				"%s %s slow" % [label, row["name"]]
			)
