extends RefCounted
## Layer 9bq9: `_core.py::TowerDebuffMixin._draw_tower_debuff_fx`, the debuff indicator that
## `Boss.draw` paints after its cached auras and the ground shadow, before the per-type renderer.
##
##   not alive                                   -> nothing
##   include_rings and slow_timer > 0            -> ellipse `(150, 220, 255)` width 1 at the feet:
##                                                  `(x - r - 2, y + r - 7, (r + 2) * 2, 10)`
##   burn_timer > 0                              -> three flame tongues, `flick = int(1.5 + 1.5 *
##                                                  sin(anim * 0.6))`, each an outer
##                                                  `(255, 140, 40)` circle and an inner
##                                                  `(255, 220, 90)` circle at `max(1, r - 1)`
##   pips                                        -> one 5x5 `(10, 10, 14)` block plus a 4x4
##                                                  colour block per active debuff, 5 px apart
##                                                  from `x - (count * 5 - 1) // 2` at
##                                                  `y + r + 12`, in this order: slow
##                                                  `(150, 220, 255)`, attack slow `(90, 160,
##                                                  255)`, skill down `(200, 120, 255)`, anti heal
##                                                  `(255, 90, 140)`, burn `(255, 130, 40)`
##
## `anim` is the source's `getattr(self, "anim_time", getattr(self, "pulse", 0))`; the view passes
## `anim_time`, which `BossState` always has. Every colour here is a raw source tuple, so alpha
## stays 255.

const SLOW := [150, 220, 255]
const ATK_SLOW := [90, 160, 255]
const SKILL_DOWN := [200, 120, 255]
const ANTI_HEAL := [255, 90, 140]
const BURN_PIP := [255, 130, 40]
const PIP_BACK := [10, 10, 14]
const FLAME_OUTER := [255, 140, 40]
const FLAME_INNER := [255, 220, 90]
## `pip_y = y + radius + 12`, each pip 5 px apart.
const PIP_STEP := 5
const PIP_RADIUS_OFFSET := 12


## One frame of the indicator. `slow`, `atk_slow`, `skill_down`, `anti_heal` and `burn` are the
## remaining timer ticks of each debuff (the source only tests them for `> 0`).
static func ops(
	x: int,
	y: int,
	radius: int,
	slow: int,
	atk_slow: int,
	skill_down: int,
	anti_heal: int,
	burn: int,
	anim_time: float,
	include_rings: bool = true
) -> Array:
	var out: Array = []
	if include_rings and slow > 0:
		(
			out
			. append(
				{
					"kind": "ellipse",
					"rect": [x - radius - 2, y + radius - 7, (radius + 2) * 2, 10],
					"width": 1,
					"mult": 255,
					"color": [SLOW[0], SLOW[1], SLOW[2], 255],
				}
			)
		)
	if burn > 0:
		var flick := int(1.5 + 1.5 * sin(anim_time * 0.6))
		var flames := [
			[-radius + 2, -radius - 2, 2 + flick],
			[radius - 2, -radius - 3, 2],
			[0, -radius - 6, 3 + flick],
		]
		for flame in flames:
			var cx := x + int(flame[0])
			var cy := y + int(flame[1])
			var size := int(flame[2])
			out.append(_circle([cx, cy], size, FLAME_OUTER))
			out.append(_circle([cx, cy], maxi(1, size - 1), FLAME_INNER))
	var pips: Array = []
	if slow > 0:
		pips.append(SLOW)
	if atk_slow > 0:
		pips.append(ATK_SLOW)
	if skill_down > 0:
		pips.append(SKILL_DOWN)
	if anti_heal > 0:
		pips.append(ANTI_HEAL)
	if burn > 0:
		pips.append(BURN_PIP)
	if not pips.is_empty():
		var pip_y := y + radius + PIP_RADIUS_OFFSET
		var total_w := pips.size() * PIP_STEP - 1
		var px := x - floori(float(total_w) / 2.0)
		for pip in pips:
			(
				out
				. append(
					{
						"kind": "rect",
						"rect": [px - 1, pip_y - 1, 5, 5],
						"width": 0,
						"radius": 0,
						"mult": 255,
						"color": [PIP_BACK[0], PIP_BACK[1], PIP_BACK[2], 255],
					}
				)
			)
			(
				out
				. append(
					{
						"kind": "rect",
						"rect": [px, pip_y, 4, 4],
						"width": 0,
						"radius": 0,
						"mult": 255,
						"color": [pip[0], pip[1], pip[2], 255],
					}
				)
			)
			px += PIP_STEP
	return out


static func _circle(center: Array, radius: int, rgb: Array) -> Dictionary:
	return {
		"kind": "circle",
		"center": center,
		"radius": radius,
		"width": 0,
		"mult": 255,
		"color": [rgb[0], rgb[1], rgb[2], 255],
	}
