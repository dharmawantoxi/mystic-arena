class_name RenderEasing
extends RefCounted

## Easing curves ported 1:1 from _render.py (_ease_* helpers).


static func out_back(t: float) -> float:
	var c1 := 1.70158
	var c3 := c1 + 1.0
	var t1 := t - 1.0
	return 1.0 + c3 * (t1 * t1 * t1) + c1 * (t1 * t1)


static func in_back(t: float) -> float:
	var c1 := 1.70158
	var c3 := c1 + 1.0
	return c3 * t * t * t - c1 * t * t


static func out_cubic(t: float) -> float:
	return 1.0 - pow(1.0 - t, 3.0)


static func out_elastic(t: float) -> float:
	var c4 := (2.0 * PI) / 3.0
	if t == 0.0:
		return 0.0
	if t == 1.0:
		return 1.0
	return pow(2.0, -10.0 * t) * sin((t * 10.0 - 0.75) * c4) + 1.0
