extends RefCounted
## Combat-load FX governor: the native port of the FX half of `mobile/perf.py`.
##
## Pygame measured that hero live-FX cost scales linearly with the number of
## heroes fighting at once (ground decals alone were 2,57 ms/frame for ten
## heroes on a PC, 8-13 ms on a phone). The fix was a governor that never skips
## a frame, only lowers INTENSITY: `fx_load()` scales every particle system, and
## a hard per-frame spawn-token budget sits on top of that for modules that
## ignore the ratio.
##
##   `set_fx_load(n_active)` runs once per frame from the hero FX bus:
##
##       target = 1.0                                  when n <= 1 hero
##       target = max(0.10, (1 / n) ** 1.5)            otherwise
##       load  += (target - load) * 0.40               smoothing, never a jump
##
##   Tokens are refilled from the smoothed load with hard floors:
##
##       particles           max(56, int(140 * load))
##       FX projectiles      max(10, int( 18 * load))
##       skill projectiles   max( 5, int( 10 * load))
##
## The quality presets those knobs read from are here too, because the atlas
## bake and the hero FX bus both need the same numbers:
##
##       particle ratio      0.20 / 0.40 / 0.70      low / medium / high
##       skill pose floor    12   /  8   /  4
##       attack pose floor    6   /  4   /  3
##       ground FX budget     2   /  3   /  6
##       full hero render     3   /  4   /  8
##
## `heroes/__init__.py` reads `Quality.particle_ratio`, `skill_quant_floor`,
## `atk_quant_floor`, `fx_ground_budget` and `max_hero_render`; `heroes/*_fx.py`
## read `particle_ratio` only, which is why the ratio is the loaded one.

const LEVEL_LOW := "low"
const LEVEL_MEDIUM := "medium"
const LEVEL_HIGH := "high"

## How fast the load follows the number of fighting heroes (source 0.40).
const LOAD_SMOOTH := 0.40
## One hero gets full intensity; everything above it scales down.
const BASE_HEROES := 1.0
## Never drop below this intensity, or FX disappears instead of thinning out.
const LOAD_MIN := 0.10
## Higher = more aggressive falloff once three or more heroes fight.
const LOAD_EXP := 1.5

const PARTICLE_CAP := 140
const PROJECTILE_CAP := 18
const SKILL_PROJECTILE_CAP := 10
const PARTICLE_FLOOR := 56
const PROJECTILE_FLOOR := 10
const SKILL_PROJECTILE_FLOOR := 5

const PARTICLE_RATIO := {
	"low": 0.20,
	"medium": 0.40,
	"high": 0.70,
}
const SKILL_QUANT_FLOOR := {
	"low": 12,
	"medium": 8,
	"high": 4,
}
const ATK_QUANT_FLOOR := {
	"low": 6,
	"medium": 4,
	"high": 3,
}
const GROUND_BUDGET := {
	"low": 2,
	"medium": 3,
	"high": 6,
}
const MAX_HERO_RENDER := {
	"low": 3,
	"medium": 4,
	"high": 8,
}

static var _level := LEVEL_HIGH
static var _load := 1.0
static var _particle_left := PARTICLE_CAP
static var _projectile_left := PROJECTILE_CAP
static var _skill_projectile_left := SKILL_PROJECTILE_CAP
static var _tokens_active := false


## Active preset. Starts on HIGH, exactly like `_Quality()` calling `apply(HIGH)`.
static func level() -> String:
	return _level


## Apply a preset. Mirrors `Quality.apply(level)` for the FX knobs only.
static func set_quality(value: String) -> void:
	if not PARTICLE_RATIO.has(value):
		return
	_level = value


## Preset particle ratio, before the combat load is folded in (0.20/0.40/0.70).
static func base_particle_ratio() -> float:
	return float(PARTICLE_RATIO.get(_level, 0.70))


## Effective particle ratio = preset ratio x combat load. This is the number
## every FX module multiplies its spawn counts with.
static func particle_ratio() -> float:
	return base_particle_ratio() * _load


## Current smoothed combat load (0.10 .. 1.0). 1.0 = normal.
static func fx_load() -> float:
	return _load


## Feed one frame's worth of "how many live-FX units are fighting". Runs once
## per frame from `HeroFxBus.begin_fx_frame()`; enables the token gate, because
## unit tests that spawn particles outside the game loop must not be starved.
static func set_fx_load(active_count: int) -> void:
	_tokens_active = true
	var count := maxi(0, active_count)
	var target := 1.0
	if float(count) > BASE_HEROES:
		target = maxf(LOAD_MIN, pow(BASE_HEROES / float(count), LOAD_EXP))
	_load += (target - _load) * LOAD_SMOOTH
	_reset_tokens()


## Back to normal intensity (leaving a match, switching preset).
static func reset_fx_load() -> void:
	_load = 1.0
	_tokens_active = false
	_reset_tokens()


static func tokens_active() -> bool:
	return _tokens_active


## Claim one particle spawn token. `true` while the frame still has budget, and
## always `true` outside the frame loop (source `_FX_TOKENS_ACTIVE` gate).
static func claim_particle() -> bool:
	if not _tokens_active:
		return true
	if _particle_left <= 0:
		return false
	_particle_left -= 1
	return true


## Give the token back when the spawn was refused (director cap / full pool).
static func refund_particle() -> void:
	if not _tokens_active:
		return
	_particle_left += 1


static func claim_projectile() -> bool:
	if not _tokens_active:
		return true
	if _projectile_left <= 0:
		return false
	_projectile_left -= 1
	return true


static func refund_projectile() -> void:
	if not _tokens_active:
		return
	_projectile_left += 1


## Skill projectiles are a one-way gate in the source (`allow_skill_projectile`):
## there is no refund hook, because the spawn either happens or never does.
static func allow_skill_projectile() -> bool:
	if not _tokens_active:
		return true
	if _skill_projectile_left <= 0:
		return false
	_skill_projectile_left -= 1
	return true


## Remaining tokens this frame: particles / FX projectiles / skill projectiles.
static func tokens() -> Dictionary:
	return {
		"particle": _particle_left,
		"projectile": _projectile_left,
		"skill_projectile": _skill_projectile_left,
	}


## Pose quantum for skill animations. More heroes fighting -> coarser poses,
## never finer than the preset floor. The ladder is the source's own, including
## its non-monotonic first step (`HERO_SKILL_QUANT` = 6 is coarser than the 4 it
## falls back to for three or four heroes).
static func skill_quant(busy_count: int, hero_skill_quant: int) -> int:
	var count := maxi(0, busy_count)
	var quantum: int
	if count <= 2:
		quantum = hero_skill_quant
	elif count <= 4:
		quantum = 4
	elif count <= 6:
		quantum = 8
	else:
		quantum = 12
	return maxi(quantum, int(SKILL_QUANT_FLOOR.get(_level, 4)))


## Pose quantum for attack animations: pure preset floor, no load ladder.
static func atk_quant() -> int:
	return int(ATK_QUANT_FLOOR.get(_level, 3))


## How many heroes may paint the decoration layer under their feet this frame.
static func ground_budget() -> int:
	return int(GROUND_BUDGET.get(_level, 6))


## How many heroes may be fully re-rendered this frame before the rest reuse
## their cached sprite.
static func max_hero_render() -> int:
	return int(MAX_HERO_RENDER.get(_level, 8))


static func _reset_tokens() -> void:
	var load := maxf(LOAD_MIN, _load)
	_particle_left = maxi(PARTICLE_FLOOR, int(PARTICLE_CAP * load))
	_projectile_left = maxi(PROJECTILE_FLOOR, int(PROJECTILE_CAP * load))
	_skill_projectile_left = maxi(SKILL_PROJECTILE_FLOOR, int(SKILL_PROJECTILE_CAP * load))
