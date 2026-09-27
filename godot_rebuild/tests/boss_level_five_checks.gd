extends RefCounted
## Vhalzun and Krobellus real recipes, gates, timers, attacks and respawn,
## replayed against native combat from the captured source fixture.
const LevelChecks = preload("res://tests/boss_tier_checks.gd")
const BOSS_FIXTURE := "res://tests/fixtures/boss_level_five_source.json"
const BOSSES := {
	"vhalzun": preload("res://data/heroes/vhalzun.tres"),
	"krobellus": preload("res://data/heroes/krobellus.tres")
}


func run(check: Callable) -> void:
	LevelChecks.new().run_level(check, BOSS_FIXTURE, BOSSES, 601)
