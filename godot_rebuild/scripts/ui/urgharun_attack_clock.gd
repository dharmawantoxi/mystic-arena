extends RefCounted
## Layer 9bq8: the urgharun swing clock, ported from
## `bosses/level40.py::_NS_urgharun._update_urg_attack_anim`.
##
## The source keeps this clock on the boss (`_urg_attack_active`, `_urg_attack_frame`,
## `_urg_previous_timer`, `_urg_attack_progress`) and advances it once per painted frame at the
## top of `draw_urgharun`. It is purely presentational: the swing reads `boss.timer` and the RAW
## `boss.attack_cooldown`, never the slowed effective cooldown.
##
##   cooldown = max(2, int(attack_cooldown))
##   just_reset = previous > cooldown - 5 and timer < 3
##   near_max   = timer >= cooldown - 1
##   if (just_reset or near_max) and not active:  arm (frame = 0)
##   if active: frame += 1; at ATTACK_DURATION frames: disarm, frame = 0
##   previous_timer = timer
##   progress = min(1.0, frame / ATTACK_DURATION) if active else 0.0
##
## Because `cooldown` is the raw value while `timer` was armed from the (possibly slowed)
## effective cooldown, a slowed boss arms its swing early on the way down. That is a source
## quirk and is pinned by the oracle.

## `attack_duration = 28` in the source.
const ATTACK_DURATION := 28
## `cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))`.
const MIN_COOLDOWN := 2

var active := false
var frame := 0
## `_urg_previous_timer`, or -1 while the clock has not seen a timer yet (the source falls back
## to the current timer in that case).
var previous_timer := -1
var progress := 0.0


## One painted frame. Return `progress` so callers can feed the FX builder directly.
func advance(timer: int, attack_cooldown: int) -> float:
	var cooldown := maxi(MIN_COOLDOWN, attack_cooldown)
	var previous := timer if previous_timer < 0 else previous_timer
	var just_reset := previous > cooldown - 5 and timer < 3
	var near_max := timer >= cooldown - 1
	if (just_reset or near_max) and not active:
		active = true
		frame = 0
	if active:
		frame += 1
		if frame >= ATTACK_DURATION:
			active = false
			frame = 0
	previous_timer = timer
	progress = minf(1.0, float(frame) / float(ATTACK_DURATION)) if active else 0.0
	return progress
