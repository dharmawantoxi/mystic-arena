extends RefCounted
## Layer 9ar: replays the `mobile/combat_audio.py` source oracle fixture
## through the native gate. `combat_audio_source_oracle.py` runs the REAL
## module under a scriptable pygame shim (clock, free channels, SoundManager
## volume) and records every decision of a scripted request stream, so the
## spacing / budget / channel / volume rules are not hand-written here.

const CombatAudio = preload("res://scripts/audio/combat_audio.gd")
const FIXTURE := "res://tests/fixtures/combat_audio_source.json"
const AUDIO_ROOT := "res://assets/audio/"


func run(check: Callable) -> void:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	check.call(data is Dictionary, "Combat audio fixture parses")
	if not (data is Dictionary):
		return
	_constant_checks(data, check)
	_classifier_checks(data, check)
	_stream_checks(data, check)
	_isolation_checks(check)


func _constant_checks(data: Dictionary, check: Callable) -> void:
	var kinds: Array = data["kinds"]
	check.call(kinds.size() == CombatAudio.CONFIG.size(), "gate knows the seven source kinds")
	var config: Dictionary = data["config"]
	for kind in kinds:
		var expected: Array = config[kind]
		var actual: Array = CombatAudio.CONFIG.get(kind, [])
		check.call(
			(
				actual.size() == 3
				and is_equal_approx(float(actual[0]), float(expected[0]))
				and int(actual[1]) == int(expected[1])
				and bool(actual[2]) == bool(expected[2])
			),
			"config for %s matches the source _KONFIG" % kind
		)
		var bank: Array = data["bank"][kind]
		var files: Array = CombatAudio.BANK.get(kind, [])
		check.call(files.size() == bank.size(), "bank for %s has the source variant count" % kind)
		for index in range(mini(files.size(), bank.size())):
			var source_base := String(bank[index]).get_basename()
			check.call(
				String(files[index]).get_basename() == source_base,
				"bank file %s mirrors the source discovery for %s" % [files[index], kind]
			)
			check.call(
				ResourceLoader.exists(AUDIO_ROOT + String(files[index])),
				"combat sound %s ships with the rebuild" % files[index]
			)
	check.call(
		is_equal_approx(CombatAudio.RANGED_THRESHOLD, float(data["ranged_threshold"])),
		"ranged threshold matches AMBANG_RANGED"
	)
	check.call(CombatAudio.FRAME_BUDGET == int(data["frame_budget"]), "frame budget is 4")
	check.call(CombatAudio.MIXER_CHANNELS == int(data["mixer_channels"]), "24 mixer channels")
	check.call(
		is_equal_approx(CombatAudio.FALLBACK_VOLUME, float(data["fallback_volume"])),
		"fallback volume matches the source"
	)


func _classifier_checks(data: Dictionary, check: Callable) -> void:
	var attack: Dictionary = data["attack_kind"]
	for key in attack:
		check.call(
			CombatAudio.attack_kind(float(String(key).to_int())) == String(attack[key]),
			"attack kind for range %s matches jenis_serangan" % key
		)
	check.call(
		CombatAudio.attack_kind(0.0) == String(data["attack_kind_none"]),
		"missing range falls back to melee like jenis_serangan(None)"
	)
	var tower: Dictionary = data["tower_kind"]
	for key in tower:
		check.call(
			CombatAudio.tower_kind(String(key)) == String(tower[key]),
			"tower kind for '%s' matches jenis_tower" % key
		)
	for case in data["hero_kinds"]:
		var hero := _FakeHero.new()
		match String(case["case"]):
			"flag_melee":
				hero.is_melee = true
				hero.attack_range = 500.0
			"flag_ranged":
				hero.is_melee = false
				hero.attack_range = 40.0
			_:
				# No flag in the source: the native HeroState always carries
				# `is_melee`, so the range path is exercised directly.
				hero = null
		var expected := String(case["kind"])
		if hero != null:
			check.call(
				CombatAudio.hero_kind(hero) == expected,
				"play_hero_basic honours the melee flag (%s)" % case["case"]
			)
		else:
			var range_value := 99.0 if String(case["case"]) == "range_99" else 100.0
			if String(case["case"]) == "range_none":
				range_value = 0.0
			check.call(
				CombatAudio.attack_kind(range_value) == expected,
				"play_hero_basic range fallback (%s)" % case["case"]
			)
	check.call(
		CombatAudio.hero_kind(null) == CombatAudio.HERO_MELEE,
		"null hero classifies as melee (source getattr default range 40)"
	)


func _stream_checks(data: Dictionary, check: Callable) -> void:
	var gate := CombatAudio.new()
	var index := 0
	for event in data["events"]:
		if bool(event["new_frame"]):
			gate.new_frame()
		var global_volume := 0.0
		if bool(event["enabled"]):
			global_volume = float(event["master"]) * float(event["sfx"])
		var before := gate.stats.duplicate()
		var decision := gate.request(
			String(event["kind"]),
			int(event["ms"]),
			float(event["volume_mult"]),
			int(event["free_channels"]),
			global_volume
		)
		var label := "event %d (%s @ %d ms)" % [index, event["kind"], int(event["ms"])]
		check.call(bool(decision["ok"]) == bool(event["ok"]), label + " decision matches")
		if bool(event["ok"]):
			check.call(
				is_equal_approx(float(decision["volume"]), float(event["volume"])),
				label + " volume matches the source Sound.set_volume"
			)
		var delta: Dictionary = event["stats_delta"]
		for key in delta:
			check.call(
				int(gate.stats[key]) - int(before[key]) == int(delta[key]),
				label + " stats[%s] delta matches" % key
			)
		check.call(
			gate.budget_left == int(event["budget_left"]), label + " remaining frame budget matches"
		)
		index += 1


func _isolation_checks(check: Callable) -> void:
	# Headless runs have no AudioManager: the production wrapper must behave
	# like the source `_mati` branch (nothing plays, nothing counted).
	var gate: RefCounted = CombatAudio.shared()
	var before: Dictionary = gate.stats.duplicate()
	check.call(
		CombatAudio.play(CombatAudio.MINION_HIT) == false,
		"play() without an AudioManager returns false"
	)
	check.call(gate.stats == before, "play() without an AudioManager counts nothing")
	check.call(
		CombatAudio.new().pick_file(CombatAudio.TOWER_ICE) == "tower_ice.wav",
		"single-variant bank picks its only file"
	)
	check.call(CombatAudio.new().pick_file("nope") == "", "unknown kind picks no file")


class _FakeHero:
	extends RefCounted
	var is_melee := true
	var attack_range := 40.0
