extends RefCounted
## Port of `mobile/combat_audio.py` (layer 9ar): the combat-sound GATE.
##
## Seven sound kinds (hero melee/ranged shared by heroes AND bosses, four
## tower shots, minion hit), each with a base volume and a minimum spacing in
## ms; a budget of four new sounds per frame; a channel lookup that never
## steals; and the live master*sfx volume of the sound manager (0 when sound
## is disabled, the 0.6 fallback when no manager exists). Towers, heroes,
## minions and bosses call `play()` from their attack code exactly where the
## source does (`_entity.py:881/4420/5588`, `base_boss.py:750`).
##
## The gate itself is pure and clock-injected (`request()`), so the suite
## replays the oracle's scripted stream decision-for-decision; `play()` is
## the production wrapper that reads the clock and the AudioManager pool.

const AudioRuntime = preload("res://scripts/audio/audio_runtime.gd")

const HERO_MELEE := "hero_melee"
const HERO_RANGED := "hero_ranged"
const TOWER_ARCHER := "tower_archer"
const TOWER_CANNON := "tower_cannon"
const TOWER_ICE := "tower_ice"
const TOWER_MAGE := "tower_mage"
const MINION_HIT := "minion_hit"

## kind -> [base volume, minimum spacing ms, may steal a busy channel]
const CONFIG := {
	HERO_MELEE: [0.78, 90, false],
	HERO_RANGED: [0.72, 90, false],
	TOWER_ARCHER: [0.62, 110, false],
	TOWER_CANNON: [0.62, 110, false],
	TOWER_ICE: [0.62, 110, false],
	TOWER_MAGE: [0.62, 110, false],
	MINION_HIT: [0.50, 140, false],
}
## `jenis_serangan`: range >= 100 -> ranged (heroes and bosses alike).
const RANGED_THRESHOLD := 100.0
const FRAME_BUDGET := 4
const MIXER_CHANNELS := 24
const FALLBACK_VOLUME := 0.6
## Source `init()` discovery over assets/sounds (base name + `_N` variants);
## the rebuild ships the same base files under assets/audio.
const BANK := {
	HERO_MELEE: ["hero_melee.wav"],
	HERO_RANGED: ["hero_ranged.wav"],
	TOWER_ARCHER: ["tower_archer.wav"],
	TOWER_CANNON: ["tower_cannon.wav"],
	TOWER_ICE: ["tower_ice.wav"],
	TOWER_MAGE: ["tower_mage.wav"],
	MINION_HIT: ["minion_hit.ogg"],
}

static var _shared: RefCounted

var last_ms := {}
var budget_left := FRAME_BUDGET
var stats := {"main": 0, "tolak_jeda": 0, "tolak_anggaran": 0, "tolak_channel": 0}
var variant_rng := RandomNumberGenerator.new()


static func shared() -> RefCounted:
	if _shared == null:
		_shared = new()
	return _shared


## Source `new_frame()`: called once per simulation tick (60 Hz = the
## source main-loop frame).
func new_frame() -> void:
	budget_left = FRAME_BUDGET


## Pure decision of source `play()`. `global_volume` is master*sfx (0 when
## sound is disabled); `free_channels` is the number of idle mixer channels.
func request(
	kind: String,
	now_ms: int,
	volume_mult: float = 1.0,
	free_channels: int = MIXER_CHANNELS,
	global_volume: float = FALLBACK_VOLUME
) -> Dictionary:
	if not BANK.has(kind) or not CONFIG.has(kind):
		return {"ok": false, "reason": "bank", "volume": 0.0}
	var config: Array = CONFIG[kind]
	var base := float(config[0])
	var spacing := int(config[1])
	var may_steal := bool(config[2])
	if now_ms - int(last_ms.get(kind, -99999)) < spacing:
		stats["tolak_jeda"] += 1
		return {"ok": false, "reason": "jeda", "volume": 0.0}
	if not may_steal and budget_left <= 0:
		stats["tolak_anggaran"] += 1
		return {"ok": false, "reason": "anggaran", "volume": 0.0}
	if free_channels <= 0 and not may_steal:
		stats["tolak_channel"] += 1
		return {"ok": false, "reason": "channel", "volume": 0.0}
	var volume := clampf(base * volume_mult * global_volume, 0.0, 1.0)
	last_ms[kind] = now_ms
	if not may_steal:
		budget_left -= 1
	stats["main"] += 1
	return {"ok": true, "reason": "", "volume": volume}


## Random variant like the source `random.choice`; the gate owns its RNG so
## match determinism never depends on audio.
func pick_file(kind: String) -> String:
	var files: Array = BANK.get(kind, [])
	if files.is_empty():
		return ""
	if files.size() == 1:
		return String(files[0])
	return String(files[variant_rng.randi_range(0, files.size() - 1)])


static func attack_kind(attack_range: float) -> String:
	return HERO_RANGED if attack_range >= RANGED_THRESHOLD else HERO_MELEE


static func tower_kind(tower_type: String) -> String:
	match tower_type:
		"archer":
			return TOWER_ARCHER
		"cannon":
			return TOWER_CANNON
		"ice":
			return TOWER_ICE
		"mage":
			return TOWER_MAGE
		_:
			return TOWER_ARCHER


## `play_hero_basic`: the balance-pass `is_melee_hero` flag wins over range.
static func hero_kind(hero: Object) -> String:
	if hero == null:
		return HERO_MELEE
	var flag = hero.get("is_melee")
	if typeof(flag) == TYPE_BOOL:
		return HERO_MELEE if bool(flag) else HERO_RANGED
	return attack_kind(float(hero.get("attack_range")))


## Production wrapper: without an AudioManager (headless suites, the lab
## runner) the source `_mati` branch applies - nothing plays, nothing counts.
static func play(kind: String, volume_mult: float = 1.0) -> bool:
	var manager := AudioRuntime.manager()
	if manager == null or not manager.has_method("play_combat"):
		return false
	var gate: RefCounted = shared()
	var decision: Dictionary = gate.request(
		kind,
		Time.get_ticks_msec(),
		volume_mult,
		int(manager.call("combat_free_channels")),
		float(manager.call("combat_global_volume"))
	)
	if not bool(decision["ok"]):
		return false
	manager.call("play_combat", gate.pick_file(kind), float(decision["volume"]))
	return true


static func play_hero_basic(hero: Object) -> bool:
	return play(hero_kind(hero))
