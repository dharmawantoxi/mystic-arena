class_name Economy
extends RefCounted

## Integer-safe port of _core.py starting gold and passive income helpers.
const GOLD_PER_LEVEL_BONUS := 100
const GOLD_PER_SECOND_LEVEL_BONUS := 0.3
const BASE_GOLD_PER_SECOND := 3.0
const DIFFICULTY_MULT := {"easy": 1.25, "normal": 1.0, "hard": 0.75}


static func starting_gold(
	level_config: Dictionary, level_number: int, difficulty := "normal"
) -> int:
	var base := int(level_config.get("starting_gold", 1000))
	var level := maxi(1, level_number)
	var mult := float(DIFFICULTY_MULT.get(difficulty, 1.0))
	return int((base + (level - 1) * GOLD_PER_LEVEL_BONUS) * mult)


static func gold_per_second(level_number: int, difficulty := "normal") -> float:
	var level := maxi(1, level_number)
	var mult := float(DIFFICULTY_MULT.get(difficulty, 1.0))
	return (BASE_GOLD_PER_SECOND + (level - 1) * GOLD_PER_SECOND_LEVEL_BONUS) * mult


static func format_rate(rate: float) -> String:
	var text := "%.1f" % rate
	return text.trim_suffix("0").trim_suffix(".")


static func add_income(balance: int, milli: int, rate: float) -> Dictionary:
	milli += int(round(rate * 1000.0))
	var gain := int(milli / 1000.0)
	return {"gold": balance + gain, "milli": milli % 1000}
