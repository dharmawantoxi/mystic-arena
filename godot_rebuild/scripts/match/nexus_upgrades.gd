extends RefCounted
## Native nexus catalog 1-5 plus minion scale/AI tables from NEXUS_LEVELS.
const LEVELS := [
	preload("res://data/structures/nexus_level_1.tres"),
	preload("res://data/structures/nexus_level_2.tres"),
	preload("res://data/structures/nexus_level_3.tres"),
	preload("res://data/structures/nexus_level_4.tres"),
	preload("res://data/structures/nexus_level_5.tres")
]
const MINION_SCALES := [1.0, 1.2, 1.4, 1.7, 2.0]
const MINION_AI := [1, 2, 3, 4, 5]
