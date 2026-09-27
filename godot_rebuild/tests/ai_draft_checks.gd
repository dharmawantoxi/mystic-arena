extends RefCounted
## Source differential draft tests. Recruitment receipts are NOT spawned Hero kits.

const Draft = preload("res://scripts/match/ai_draft.gd")
const Economy = preload("res://scripts/match/match_economy.gd")
const FIXTURE := "res://tests/fixtures/ai_draft_source.json"

var _draw_value := 0.0
var _calls: Array = []
var _owned: Array = []
var _receipts: Array = []
var _wallet: Economy
var _reject_purchase := false


func run(check: Callable) -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	_test_pools_and_choices(fixture, check)
	for row in fixture.purchases:
		_test_purchase(row, {}, check)
	for row in fixture.synthetic.purchases:
		_test_purchase(row, fixture.synthetic.metadata, check)
	for row in fixture.reserves:
		var draft := Draft.new()
		draft.purchase_target = row.target
		draft.purchase_target_cost = int(row.cost)
		check.call(draft.reserve() == int(row.reserve), "AI source reserve clamp/empty target")
		var threshold := 100 + int(row.reserve)
		check.call(
			not draft.can_spend_nonhero(threshold - 1, 100), "AI reserve blocks nonhero spend"
		)
		check.call(
			draft.can_spend_nonhero(threshold, 100), "AI exact reserve permits nonhero spend"
		)
	for row in fixture.sampling:
		check.call(
			Draft.weighted_at(row.options, row.weights, row.draw) == row.chosen,
			"AI weighted sampler source boundary"
		)
	_test_adapter_failure(check)
	_test_native_rng(check)


func _test_pools_and_choices(fixture: Dictionary, check: Callable) -> void:
	for row in fixture.pools:
		var draft := Draft.new()
		draft.level_number = int(row.level)
		check.call(_same(draft.hero_pool(), row.pool), "AI ordered pool source parity")
		check.call(_same(draft.source_levels, row.sources), "AI first source level parity")
	var synthetic := Draft.new(fixture.synthetic.metadata)
	synthetic.level_number = 4
	check.call(
		_same(synthetic.hero_pool(), fixture.synthetic.pool), "AI filters invalid/duplicate bosses"
	)
	check.call(
		_same(synthetic.source_levels, fixture.synthetic.sources), "AI retains first source level"
	)
	synthetic.level_number = 1
	check.call(
		(
			_same(synthetic.hero_pool(), fixture.synthetic.metadata.starters)
			and synthetic.source_levels.is_empty()
		),
		"AI rebuilds source levels after level change"
	)
	for row in fixture.choices:
		var draft := Draft.new()
		draft.level_number = int(row.level)
		_bind_choices(draft, row.draw)
		var available: Array = []
		for hero_type in draft.hero_pool():
			if hero_type not in row.owned:
				available.append(hero_type)
		check.call(
			draft.choose_target(available, row.owned) == row.chosen, "AI draft selection parity"
		)
		check.call(_same(_calls, row.calls), "AI exact candidates/weights/RNG calls")


func _test_purchase(row: Dictionary, metadata: Dictionary, check: Callable) -> void:
	var draft := Draft.new(metadata)
	draft.level_number = int(row.level)
	_bind_choices(draft, row.draw)
	_owned = row.owned.duplicate()
	_wallet = Economy.new()
	_wallet.gold[1] = int(row.initial_gold)
	_wallet.opening[1] = int(row.initial_gold)
	for step in row.steps:
		var input: Dictionary = step.input
		if input.has("level"):
			draft.level_number = int(input.level)
		if input.has("own"):
			_owned.append_array(input.own)
		if input.get("own_target", false):
			_owned.append(draft.purchase_target)
		if input.get("own_pool", false):
			_owned = draft.hero_pool()
		_wallet.credit_kill(1, int(input.get("credit", 0)))
		_calls.clear()
		_receipts.clear()
		var success := draft.try_buy(_owned, _wallet.gold[1], _purchase)
		check.call(success == step.success, "AI purchase result parity")
		check.call(_wallet.gold[1] == int(step.gold), "AI purchase gold parity")
		check.call(_same(_owned, step.owned), "AI owned types include dead heroes")
		check.call(draft.purchase_target == step.target, "AI saved/stale/cleared draft parity")
		check.call(draft.purchase_target_cost == int(step.cost), "AI summon cost not unlock cost")
		check.call(draft.reserve() == int(step.reserve), "AI purchase reserve parity")
		check.call(draft.total_heroes_bought == int(step.total), "AI purchase counter parity")
		check.call(_same(_calls, step.calls), "AI no reroll of unaffordable saved draft")
		check.call(_same(_receipts, step.receipts), "AI spawn offset source parity")
		check.call(_wallet.is_balanced(), "AI recruitment receipt ledger invariant")


func _test_adapter_failure(check: Callable) -> void:
	var draft := Draft.new()
	_bind_choices(draft, 0.0)
	_owned = []
	_receipts.clear()
	_wallet = Economy.new()
	_wallet.credit_kill(1, 50)
	_reject_purchase = true
	check.call(
		not draft.try_buy(_owned, 400, _purchase), "AI failed native adapter refuses purchase"
	)
	check.call(
		draft.reserve() == 400 and draft.total_heroes_bought == 0, "AI failed spawn retains draft"
	)
	check.call(_owned.is_empty() and _receipts.is_empty(), "AI failed spawn has no roster mutation")
	check.call(_wallet.gold[1] == 400 and _wallet.is_balanced(), "AI failed spawn never debits")
	_calls.clear()
	_reject_purchase = false
	check.call(draft.try_buy(_owned, 400, _purchase), "AI saved draft retries successful adapter")
	check.call(_calls.is_empty(), "AI retry does not reroll")
	check.call(
		draft.reserve() == 0 and draft.total_heroes_bought == 1, "AI success clears draft once"
	)
	check.call(_wallet.gold[1] == 0 and _wallet.is_balanced(), "AI successful retry debits once")
	var fresh := Draft.new()
	check.call(
		(
			fresh.purchase_target.is_empty()
			and fresh.reserve() == 0
			and fresh.total_heroes_bought == 0
		),
		"AI new match has no carried draft/reserve/counter"
	)


func _test_native_rng(check: Callable) -> void:
	var first := Draft.new()
	var second := Draft.new()
	first.rng.seed = 281
	second.rng.seed = 281
	first.level_number = 7
	second.level_number = 7
	var pool := first.hero_pool()
	second.hero_pool()
	for index in range(30):
		for owned in [[], ["kaizen"], ["kaizen", "gornak"]]:
			var available: Array = []
			for hero_type in pool:
				if hero_type not in owned:
					available.append(hero_type)
			var chosen := first.choose_target(available, owned)
			check.call(chosen in available, "AI native RNG chooses an eligible entry")
			check.call(
				chosen == second.choose_target(available, owned),
				"AI same native seed replays choices"
			)
	check.call(
		Draft.weighted_at(["a", "b"], [1, 1], 1.0) == "b", "AI Godot RNG inclusive endpoint is safe"
	)


func _bind_choices(draft: Draft, draw: float) -> void:
	_draw_value = draw
	_calls.clear()
	draft.uniform_picker = _uniform
	draft.weighted_picker = _weighted


func _uniform(options: Array) -> String:
	_calls.append({"kind": "uniform", "options": options.duplicate(), "weights": []})
	return options[mini(options.size() - 1, int(_draw_value * options.size()))]


func _weighted(options: Array, weights: Array) -> String:
	_calls.append(
		{"kind": "weighted", "options": options.duplicate(), "weights": weights.duplicate()}
	)
	return Draft.weighted_at(options, weights, _draw_value)


func _purchase(hero_type: String, cost: int, point: Vector2) -> bool:
	# A test adapter only, using the actual match ledger. No combat hero is spawned.
	if _reject_purchase or not _wallet.spend(1, cost):
		return false
	_owned.append(hero_type)
	_receipts.append({"hero_type": hero_type, "team": "red", "position": [point.x, point.y]})
	return true


func _same(actual: Variant, expected: Variant) -> bool:
	# JSON numbers are float; compare scalar numbers, never nested Array identity.
	if expected is Array:
		if not actual is Array or actual.size() != expected.size():
			return false
		for index in range(expected.size()):
			if not _same(actual[index], expected[index]):
				return false
	elif expected is Dictionary:
		if not actual is Dictionary or actual.size() != expected.size():
			return false
		for key in expected:
			if not actual.has(key) or not _same(actual[key], expected[key]):
				return false
	else:
		return actual == expected
	return true
