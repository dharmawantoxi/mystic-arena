extends RefCounted
## Mobile dock popup for the selected blue castle, including the source upgrade
## and castle-shield controls. Geometry is screen-space like the Pygame dock.

const POPUP_W := 380
const MIN_POPUP_W := 240
const POPUP_H := 440
const CLOSE_SIZE := 22
const SHIELD_H := 36
const UPGRADE_H := 42
const BUTTON_X := 15
const SHIELD_SECTION_Y := 169
const SHIELD_ACTIVE_EXTRA_Y := 22
const SHIELD_SECTION_EXTRA_Y := 46
const NEXT_NAME_GAP := 24


static func mobile_geometry(panel: Rect2i) -> Dictionary:
	if panel.size.x < MIN_POPUP_W + 16 or panel.size.y <= 0:
		return {}
	var popup_width := mini(POPUP_W, panel.size.x - 16)
	if popup_width > panel.size.x - 8:
		return {}
	var centered_y := floori(float(panel.size.y - POPUP_H) / 2.0)
	var py := maxi(12, mini(panel.size.y - POPUP_H - 12, centered_y))
	var px := panel.position.x + int((panel.size.x - popup_width) / 2)
	return {"panel_pos": [px, py], "popup_w": popup_width}


static func state_width(state: Dictionary) -> int:
	return clampi(int(state.get("popup_w", POPUP_W)), 1, POPUP_W)


static func origin(state: Dictionary) -> Vector2i:
	var supplied: Variant = state.get("panel_pos", null)
	if supplied is Array and supplied.size() >= 2:
		return Vector2i(int(supplied[0]), int(supplied[1]))
	if supplied is Vector2i:
		return supplied
	return Vector2i.ZERO


static func panel_rect(state: Dictionary) -> Rect2i:
	return Rect2i(origin(state), Vector2i(state_width(state), POPUP_H))


static func close_rect(state: Dictionary) -> Rect2i:
	var at := origin(state)
	return Rect2i(
		at + Vector2i(state_width(state) - CLOSE_SIZE - 4, 6), Vector2i(CLOSE_SIZE, CLOSE_SIZE)
	)


static func shield_section_y(state: Dictionary) -> int:
	return (
		SHIELD_SECTION_Y + (SHIELD_ACTIVE_EXTRA_Y if bool(state.get("shield_active", false)) else 0)
	)


static func shield_rect(state: Dictionary) -> Rect2i:
	var at := origin(state)
	var width := state_width(state) - BUTTON_X * 2
	return Rect2i(at + Vector2i(BUTTON_X, shield_section_y(state)), Vector2i(width, SHIELD_H))


static func upgrade_rect(state: Dictionary) -> Rect2i:
	var at := origin(state)
	var width := state_width(state) - BUTTON_X * 2
	var shield_row := (
		bool(state.get("shield_free", false))
		or bool(state.get("shield_purchased", false))
		or bool(state.get("shield_can_activate", false))
	)
	var y := shield_section_y(state)
	if shield_row:
		y += SHIELD_SECTION_EXTRA_Y
	y += NEXT_NAME_GAP
	return Rect2i(at + Vector2i(BUTTON_X, y), Vector2i(width, UPGRADE_H))


static func button_enabled(state: Dictionary, action: String) -> bool:
	match action:
		"castle_upgrade":
			var cost := int(state.get("upgrade_cost", 0))
			return cost > 0 and int(state.get("gold", 0)) >= cost
		"castle_shield":
			return (
				bool(state.get("shield_can_activate", false))
				and int(state.get("gold", 0)) >= int(state.get("shield_cost", 0))
			)
	return false
