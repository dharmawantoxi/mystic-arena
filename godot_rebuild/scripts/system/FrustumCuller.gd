class_name FrustumCuller
extends RefCounted

## Native _system.FrustumCuller: skip draw outside screen + margin.
const MARGIN := 80
const SCREEN_WIDTH := 1280
const SCREEN_HEIGHT := 720


static func is_visible(pos: Vector2, radius := 30.0) -> bool:
	var m := MARGIN + radius
	return pos.x >= -m and pos.x <= SCREEN_WIDTH + m and pos.y >= -m and pos.y <= SCREEN_HEIGHT + m


static func is_visible_xy(x: float, y: float, radius := 30.0) -> bool:
	return is_visible(Vector2(x, y), radius)
