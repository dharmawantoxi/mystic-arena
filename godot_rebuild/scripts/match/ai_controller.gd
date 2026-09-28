extends RefCounted
## Port of the AIPlayer.update scheduling wrapper (layer 6b): the AI controls
## its heroes on EVERY tick, then only thinks when `think_timer` runs out,
## performing `1 + round(2*elite)` actions and stopping at the first priority
## step that does nothing.
##
## The clock itself is `ai_policy.advance` (already a port of the same block);
## this module adds the bits the battle loop needs: per-tick bookkeeping, the
## draft reserve passthrough (`_ai_reserve`) and a single entry point whose
## callbacks are injected, so no economy transaction happens here. Adapters
## (build / buy hero / upgrade hero / item / upgrade tower / shields / nexus)
## stay in their own modules and are scanned by `ai_policy.choose_step`.

const AiPolicy = preload("res://scripts/match/ai_policy.gd")

var policy: AiPolicy
# Diagnostics: ticks observed, thinking ticks, and actions attempted/completed.
var ticks := 0
var think_ticks := 0
var steps_attempted := 0
var steps_completed := 0


func _init() -> void:
	policy = AiPolicy.new()


func tick(control_heroes: Callable, perform_step: Callable) -> int:
	# Source AIPlayer.update: control first, then the think timer, then the
	# action loop that stops at the first failing priority. The policy counts
	# the thinking tick, so the bookkeeping below mirrors its timer transition.
	ticks += 1
	var before := policy.think_timer
	var completed: int = policy.advance(control_heroes, perform_step)
	if before <= 1:
		think_ticks += 1
	steps_attempted += policy.last_attempts
	steps_completed += completed
	return completed


func reserve(draft: Object) -> int:
	# Source _ai_reserve: the price of the persistent hero draft, when any.
	if draft == null or String(draft.purchase_target) == "":
		return 0
	return maxi(0, int(draft.purchase_target_cost))
