# SylaraAudio.gd — audio dispatcher for Sylara (Godot 4.x).
#
# Membungkus AudioManager dengan volume yang diseimbangkan secara kontekstual
# untuk serangan panah, tebasan busur, skill windrun, shackle, dan powershot.
class_name SylaraAudio
extends Node

const AudioManagerScript = preload("res://scripts/autoload/AudioManager.gd")


func play_attack(is_melee: bool = false) -> void:
	if is_melee:
		AudioManager.play_combat("hero_melee", 0.78)
	else:
		AudioManager.play_combat("hero_ranged", 0.75)


func play_skill_cast(skill_key: String) -> void:
	match skill_key:
		"q":
			AudioManager.play_sfx("hero_skill", 0.8)
		"w":
			AudioManager.play_sfx("hero_skill", 0.85)
		"e":
			AudioManager.play_sfx("hero_skill", 0.85)
		"r":
			AudioManager.play_sfx("hero_skill", 1.0)
		_:
			AudioManager.play_sfx("hero_skill", 0.8)


func play_hit() -> void:
	AudioManager.play_combat("minion_hit", 0.6)


func play_death() -> void:
	AudioManager.play_sfx("minion_death", 0.8)


func play_victory() -> void:
	AudioManager.play_sfx("victory", 0.9)
