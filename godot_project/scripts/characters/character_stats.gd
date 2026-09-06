class_name CharacterStats
extends Resource
## Resource container for character stats.
##
## Subclass this for each hero (or just instance with custom values). Keeps
## balance data in one place, editable from the Inspector.
##

@export var character_id: StringName = &"kaizen"
@export var display_name: String = "Kaizen"
@export var max_hp: int = 1000
@export var speed: float = 180.0
@export var damage: int = 80
@export var attack_cooldown: float = 0.55
@export var attack_range: float = 70.0
@export var skill_damage: int = 120

@export var q_cooldown: float = 5.0
@export var w_cooldown: float = 12.0
@export var e_cooldown: float = 7.0
@export var r_cooldown: float = 30.0

@export var q_range: float = 90.0
@export var e_range: float = 100.0
@export var r_range: float = 150.0
