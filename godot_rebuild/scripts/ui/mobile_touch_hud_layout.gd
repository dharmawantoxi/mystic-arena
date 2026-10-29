extends RefCounted
## Source geometry for `mobile.hud.TouchHUD._build_layout()` on 16:9 touch screens.

const SAFE_MARGIN := 28
const PAUSE_Y := 158
const BUTTON_SIZE := 52
const DEBUG_GAP := 84
const MIN_TAP := 80


static func pause_rect(safe_left: int = SAFE_MARGIN) -> Rect2i:
	return Rect2i(maxi(22, safe_left + 6), PAUSE_Y, BUTTON_SIZE, BUTTON_SIZE)


static func debug_rect(safe_left: int = SAFE_MARGIN) -> Rect2i:
	var pause := pause_rect(safe_left)
	return Rect2i(pause.position.x + DEBUG_GAP, pause.position.y, BUTTON_SIZE, BUTTON_SIZE)


static func hit_rect(button_rect: Rect2i) -> Rect2i:
	# TouchButton first inflates by 24, then guarantees an 80 px target.
	var hit := button_rect.grow(12)
	if hit.size.x < MIN_TAP or hit.size.y < MIN_TAP:
		var width_delta := maxi(0, MIN_TAP - button_rect.size.x)
		var height_delta := maxi(0, MIN_TAP - button_rect.size.y)
		var left := int(width_delta / 2)
		var top := int(height_delta / 2)
		hit = Rect2i(
			button_rect.position.x - left,
			button_rect.position.y - top,
			button_rect.size.x + width_delta,
			button_rect.size.y + height_delta
		)
	return hit
