extends RefCounted
## Match-local integer ledger. Not permanent currency, cloud state, or a save format.

const Rounding = preload("res://scripts/combat/damage_rules.gd")
const BUILD_COST := 100
const SELL_REFUND := 50

var gold: Array[int] = [1000, 350]
var opening: Array[int] = [1000, 350]
var passive: Array[int] = [0, 0]
var earned: Array[int] = [0, 0]
var refunded: Array[int] = [0, 0]
var spent: Array[int] = [0, 0]
var income_per_second := 3.0
var income_milli := 0
var income_ticks := 0


static func starting_gold(base: int, level: int, difficulty: String) -> int:
	return int((base + (maxi(1, level) - 1) * 100) * multiplier(difficulty))


static func passive_rate(level: int, difficulty: String) -> float:
	return (3.0 + (maxi(1, level) - 1) * 0.3) * multiplier(difficulty)


static func multiplier(difficulty: String) -> float:
	return float({"easy": 1.25, "normal": 1.0, "hard": 0.75}.get(difficulty, 1.0))


func step_tick(wave: int) -> void:
	income_ticks += 1
	if income_ticks < 60:
		return
	income_ticks = 0
	income_milli += Rounding.rounded_like_python(income_per_second * 1000.0)
	var gain := int(income_milli / 1000.0)
	income_milli %= 1000
	gold[0] += gain
	passive[0] += gain
	var red_gain := 3 + maxi(0, wave)
	gold[1] += red_gain
	passive[1] += red_gain


func spend(team: int, amount: int) -> bool:
	if team not in [0, 1] or amount <= 0 or gold[team] < amount:
		return false
	gold[team] -= amount
	spent[team] += amount
	return true


func credit_kill(team: int, amount: int) -> void:
	if team in [0, 1] and amount > 0:
		gold[team] += amount
		earned[team] += amount


func credit_sale(team: int) -> void:
	gold[team] += SELL_REFUND
	refunded[team] += SELL_REFUND


func is_balanced() -> bool:
	for team in range(2):
		if (
			gold[team]
			!= opening[team] + passive[team] + earned[team] + refunded[team] - spent[team]
		):
			return false
	return true
