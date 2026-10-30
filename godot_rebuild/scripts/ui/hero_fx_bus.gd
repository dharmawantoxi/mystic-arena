extends RefCounted
## Live hero-FX bus: the native port of the FX half of `heroes/__init__.py`.
##
## Pygame splits hero work in two. The hero *body* goes through
## `HERO_RENDERERS` + the measured-scale pipeline, which Godot carries as
## pre-baked atlases (`data/art/heroes.json`, `scripts/ui/hero_art.gd`,
## `scripts/ui/hero_anim.gd`). The *live* layer — particles, trails, ground
## decals, skill projectiles — is 27 separate `heroes/*_fx.py` directors that
## the source bus drives twice per hero per frame:
##
##     _live_fx_pre()   ground FX below the sprite, budget limited
##     _live_fx_post()  skill visuals above the sprite, never budget limited
##
## This module is that bus. It owns the registry, the per-frame frame counter
## and busy count, the ground-layer budget, and the guards that make a hero
## opt out (`_portrait_hd` for the shop/portrait renderer).
##
## Two source rules matter enough to restate, because getting them wrong is
## what made the Pygame skills flicker:
##
## 1. A frame is NEVER skipped. Load is reduced through intensity
##    (`FxGovernor.particle_ratio()`), never by drawing on 2 of 3 frames.
## 2. When the ground budget is exhausted only `draw_ground_layer` is skipped.
##    `attach()` and `tick()` still run, because the ground call is where every
##    director advances its simulation; skipping it froze the whole hero's FX
##    (measured: the top layer fell from 3,99 to 0,03 ms/frame, i.e. the skill
##    visually vanished instead of just losing its floor decoration).
##
## Director contract (same twelve entry points as the source modules):
##
##     attach(unit) -> bool      owns(unit) -> bool
##     tick()                    reset_all()
##     draw_ground_layer(unit)   draw_live_layer(unit)
##     stats() -> Dictionary     total_particles() -> int
##     plus `MAX_PARTICLES`, `Particle`, `ParticleSystem`, `ProjectileSystem`
##
## The drawing calls drop the source `(surface, hero, x, y)` arguments: a native
## director owns its own canvas item and reads `unit.position` itself, so the
## surface/offset pair is injected at construction and the unit is passed whole.

const FxGovernor = preload("res://scripts/settings/fx_governor.gd")

## Source `HERO_SKILL_QUANT` (the coarse first step of the pose ladder).
const HERO_SKILL_QUANT := 6
## Source `_FX_GROUND_LEFT = [99]`: the "never limits" default.
const GROUND_BUDGET_UNLIMITED := 99
## Source `MYSTIC_FX_GROUND=0` benchmarking switch.
const GROUND_ENV_KEY := "MYSTIC_FX_GROUND"

## The 27 live-FX heroes, in the order the source registry lists them.
const LIVE_FX_HEROES := [
	"zephyr",
	"gornak",
	"grimjaw",
	"kaizen",
	"vex",
	"sylara",
	"abaddon",
	"gorath",
	"razak",
	"khalros",
	"alchemist",
	"ancient_apparition",
	"nyzrak",
	"xerathis",
	"varkul",
	"ignis_drachorn",
	"zharok",
	"vokrahn",
	"pyrenth",
	"krobellus",
	"vhalzun",
	"nyxara",
	"gravefang",
	"thalgryn",
	"kunkka",
	"syrentha",
	"gravewake",
]

## The twelve shared entry points every director exposes, in fixture order.
const FX_CONTRACT := [
	"attach",
	"owns",
	"tick",
	"draw_ground_layer",
	"draw_live_layer",
	"reset_all",
	"stats",
	"total_particles",
	"MAX_PARTICLES",
	"Particle",
	"ParticleSystem",
	"ProjectileSystem",
]

static var _frame := 0
static var _busy := 0
static var _ground_left := GROUND_BUDGET_UNLIMITED
static var _ground_on := true
static var _env_read := false
static var _directors := {}
static var _property_cache := {}


## True when `hero_id` is allowed a live FX layer at all.
static func has_live_fx(hero_id: String) -> bool:
	return LIVE_FX_HEROES.has(hero_id)


## Register the director instance for one hero. A hero without a director keeps
## its baked sprite art and simply has no live layer, exactly like a Pygame hero
## whose `*_fx.py` module is missing.
static func register(hero_id: String, director: Variant) -> bool:
	if not has_live_fx(hero_id) or director == null:
		return false
	_directors[hero_id] = director
	return true


static func director_for(hero_id: String) -> Variant:
	return _directors.get(hero_id)


static func registered_count() -> int:
	return _directors.size()


## Heroes that still have no native director. The migration report must list
## every one of them until its `*_fx.py` is ported.
static func pending_heroes() -> Array:
	var out: Array = []
	for hero_id in LIVE_FX_HEROES:
		if not _directors.has(hero_id):
			out.append(hero_id)
	return out


## Ground-layer decoration can be switched off for benchmarking, matching the
## source `MYSTIC_FX_GROUND=0` switch.
static func set_ground_effects_enabled(enabled: bool) -> void:
	_ground_on = enabled
	if not enabled:
		_ground_left = GROUND_BUDGET_UNLIMITED


static func ground_effects_enabled() -> bool:
	read_env_once()
	return _ground_on


## Read the environment switch once, like the source reads it at import time.
static func read_env_once() -> void:
	if _env_read:
		return
	_env_read = true
	_ground_on = OS.get_environment(GROUND_ENV_KEY) != "0"


## Once per frame, from the match update: advances the frame counter, tells the
## governor how loaded the combat is, and refills the ground budget. Returns the
## busy count it recorded.
static func begin_fx_frame(active_count: int = 0) -> int:
	read_env_once()
	_frame += 1
	_busy = maxi(0, active_count)
	FxGovernor.set_fx_load(_busy)
	if _ground_on:
		_ground_left = FxGovernor.ground_budget()
	else:
		_ground_left = GROUND_BUDGET_UNLIMITED
	return _busy


## Frame number of the governor (debug overlay / HUD).
static func fx_frame() -> int:
	return _frame


static func busy_count() -> int:
	return _busy


static func ground_budget_left() -> int:
	return _ground_left


## True while the unit is producing FX: casting, mid attack swing, mid boss
## attack, or carrying a live projectile. Sources: `_fx_busy`.
static func is_busy(unit: Variant) -> bool:
	var skill: Variant = _attr(unit, "active_skill", null)
	if skill is String:
		if not skill.is_empty():
			return true
	elif skill != null:
		return true
	if int(_attr(unit, "attack_timer", 0)) > 0:
		return true
	if int(_attr(unit, "timer", 0)) > 0:
		return true
	var projectiles: Variant = _attr(unit, "projectiles", null)
	if projectiles is Array:
		for projectile in projectiles:
			if projectile is Dictionary and bool(projectile.get("alive", false)):
				return true
	return false


## How many units are producing live FX right now. Bosses count too: the source
## deliberately reads `boss_type` when `hero_type` is missing, because bosses use
## the same live layer through `render_boss`.
static func count_busy_fx_heroes(units: Array) -> int:
	var count := 0
	for unit in units:
		var kind: Variant = _attr(unit, "hero_type", null)
		if kind == null or (kind is String and String(kind).is_empty()):
			kind = _attr(unit, "boss_type", null)
		if not (kind is String) or not has_live_fx(String(kind)):
			continue
		if not bool(_attr(unit, "alive", true)):
			continue
		if is_busy(unit):
			count += 1
	return count


## Ground layer of one hero: attach + tick + draw, subject to the budget.
## Returns `true` only when the decoration layer was actually drawn.
static func draw_ground(hero_id: String, unit: Variant) -> bool:
	if not has_live_fx(hero_id):
		return false
	if bool(_attr(unit, "_portrait_hd", false)):
		return false
	var director: Variant = director_for(hero_id)
	if director == null:
		return false
	read_env_once()
	if _ground_left <= 0:
		# Budget gone: keep the simulation alive, skip only the drawing.
		if not _attach(director, unit):
			return false
		_tick(director)
		return false
	_ground_left -= 1
	if not _attach(director, unit):
		return false
	_tick(director)
	return _call_draw(director, "draw_ground_layer", [unit])


## Live layer of one hero: never budget limited. Returns `true` when the layer
## was drawn.
static func draw_live(hero_id: String, unit: Variant) -> bool:
	if not has_live_fx(hero_id):
		return false
	if bool(_attr(unit, "_portrait_hd", false)):
		return false
	var director: Variant = director_for(hero_id)
	if director == null:
		return false
	if not _attach(director, unit):
		return false
	_tick(director)
	return _call_draw(director, "draw_live_layer", [unit])


## Skill-pose quantum for this frame: busy-count ladder, floored by the preset.
static func skill_quant() -> int:
	return FxGovernor.skill_quant(_busy, HERO_SKILL_QUANT)


## Attack-pose quantum: preset floor only.
static func atk_quant() -> int:
	return FxGovernor.atk_quant()


## Clear every director and reset the frame state (leaving a match).
static func reset_all() -> void:
	for hero_id in _directors:
		_invoke(_directors[hero_id], "reset_all", [])
	_frame = 0
	_busy = 0
	_ground_left = GROUND_BUDGET_UNLIMITED
	_property_cache.clear()
	FxGovernor.reset_fx_load()


## Source `_wrap_fx_spawn` rule, expressed for native directors: a claimed
## token is refunded when the spawn did not actually grow the live count
## (director cap reached / pool full). Returns `true` when the spawn landed.
static func guard_spawn(kind: String, before: int, after: int) -> bool:
	if before >= 0 and after <= before:
		if kind == "particle":
			FxGovernor.refund_particle()
		else:
			FxGovernor.refund_projectile()
		return false
	return true


static func _attach(director: Variant, unit: Variant) -> bool:
	var result: Variant = _invoke(director, "attach", [unit])
	if result == null:
		return true
	return bool(result)


static func _tick(director: Variant) -> void:
	_invoke(director, "tick", [])


## Draw calls return nothing, so "did it draw" is "was there a callable".
static func _call_draw(director: Variant, method: String, args: Array) -> bool:
	if director is Dictionary:
		return director.get(method) is Callable
	if director is Object and director.has_method(method):
		director.callv(method, args)
		return true
	return false


## Directors are either objects with the contract methods or plain dictionaries
## of callables (used by the checks suite and by lightweight inline FX).
static func _invoke(director: Variant, method: String, args: Array) -> Variant:
	if director == null:
		return null
	if director is Dictionary:
		var handler: Variant = director.get(method)
		if handler is Callable:
			return handler.callv(args)
		return null
	if director is Object and director.has_method(method):
		return director.callv(method, args)
	return null


## Read `key` from a unit that is either a Dictionary (match snapshots) or an
## Object (`HeroState` / boss state). Optional attributes (`_portrait_hd`,
## `active_skill`, ...) are probed through a per-script property-name cache
## instead of `unit.key`, so a state class that does not declare them is not an
## error.
static func _attr(unit: Variant, key: String, fallback: Variant = null) -> Variant:
	if unit is Dictionary:
		return unit.get(key, fallback)
	if unit is Object:
		if _object_properties(unit).has(key):
			return unit.get(key)
	return fallback


static func _object_properties(unit: Object) -> Dictionary:
	# Keyed by instance, not by script: inner classes of one script share a
	# script id but declare different properties, and a real match only ever
	# creates a few dozen units.
	var cache_key := unit.get_instance_id()
	var cached: Variant = _property_cache.get(cache_key)
	if cached is Dictionary:
		return cached
	var names := {}
	for entry in unit.get_property_list():
		names[String(entry.get("name", ""))] = true
	if _property_cache.size() > 512:
		_property_cache.clear()
	_property_cache[cache_key] = names
	return names
