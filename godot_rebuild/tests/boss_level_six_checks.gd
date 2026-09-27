extends RefCounted
## Kunkka, Gravewake, Syrentha and Thalgryn real recipes, gates, timers,
## attacks and respawn, replayed against native combat.
const LevelChecks = preload("res://tests/boss_tier_checks.gd")
const BOSS_FIXTURE := "res://tests/fixtures/boss_level_six_source.json"
const BOSSES := {
	"kunkka": preload("res://data/heroes/kunkka.tres"),
	"gravewake": preload("res://data/heroes/gravewake.tres"),
	"syrentha": preload("res://data/heroes/syrentha.tres"),
	"thalgryn": preload("res://data/heroes/thalgryn.tres")
}


func run(check: Callable) -> void:
	LevelChecks.new().run_level(check, BOSS_FIXTURE, BOSSES, 601)
