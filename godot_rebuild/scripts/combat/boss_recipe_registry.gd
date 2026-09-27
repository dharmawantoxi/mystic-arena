extends RefCounted
## Level 10+ special boss recipe handlers. Each handler owns an explicit IDS
## allowlist; unknown/pending IDs resolve to null (no generic substitution).
## Keeps minion_battle.gd under the gdlint max-file-lines budget.
const HANDLERS := [
	preload("res://scripts/combat/boss_level_ten_skills.gd"),
	preload("res://scripts/combat/boss_level_eleven_skills.gd"),
]


static func handler(id: String, native: Dictionary):
	if native.has(id):
		return native[id]
	for candidate in HANDLERS:
		if id in candidate.IDS:
			return candidate
	return null
