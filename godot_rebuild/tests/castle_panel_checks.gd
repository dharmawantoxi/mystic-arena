extends RefCounted
## Geometry and affordability for the Android castle popup in the right dock.

const Layout = preload("res://scripts/ui/castle_panel_layout.gd")


func run(check: Callable) -> void:
	var panel := Rect2i(1280, 0, 344, 720)
	var geometry := Layout.mobile_geometry(panel)
	check.call(
		geometry == {"panel_pos": [1288, 140], "popup_w": 328},
		"castle popup fits and centers in the source 344 px mobile dock"
	)
	var state := {
		"panel_pos": geometry["panel_pos"],
		"popup_w": geometry["popup_w"],
		"upgrade_cost": 500,
		"gold": 1000,
		"shield_can_activate": false,
		"shield_active": true,
		"shield_free": true,
		"shield_cost": 1200,
	}
	var card := Layout.panel_rect(state)
	check.call(
		card.position == Vector2i(1288, 140) and card.size == Vector2i(328, 440),
		"castle card stays inside dock"
	)
	check.call(
		(
			card.encloses(Layout.close_rect(state))
			and card.encloses(Layout.shield_rect(state))
			and card.encloses(Layout.upgrade_rect(state))
		),
		"close, shield and upgrade targets fit within castle card"
	)
	check.call(
		(
			Layout.shield_rect(state).position == Vector2i(1303, 331)
			and Layout.upgrade_rect(state).position == Vector2i(1303, 401)
		),
		"free-shield castle controls follow the Pygame popup's source vertical flow"
	)
	var depleted := state.duplicate()
	depleted["shield_active"] = false
	depleted["shield_free"] = false
	depleted["shield_can_activate"] = true
	check.call(
		(
			Layout.shield_rect(depleted).position == Vector2i(1303, 309)
			and Layout.upgrade_rect(depleted).position == Vector2i(1303, 379)
		),
		"depleted-shield castle controls follow the Pygame popup's compact flow"
	)
	check.call(
		Layout.button_enabled(state, "castle_upgrade"), "affordable castle upgrade is enabled"
	)
	var purchasable := state.duplicate()
	purchasable["shield_active"] = false
	purchasable["shield_free"] = false
	purchasable["shield_can_activate"] = true
	check.call(
		not Layout.button_enabled(purchasable, "castle_shield"),
		"unaffordable castle shield is disabled"
	)
	purchasable["gold"] = 1300
	check.call(
		Layout.button_enabled(purchasable, "castle_shield"), "affordable castle shield is enabled"
	)
	state["gold"] = 0
	check.call(
		not Layout.button_enabled(state, "castle_upgrade"), "poor castle upgrade is disabled"
	)
	state["upgrade_cost"] = 0
	state["gold"] = 5000
	check.call(
		not Layout.button_enabled(state, "castle_upgrade"), "max-level castle upgrade is disabled"
	)
	check.call(
		Layout.mobile_geometry(Rect2i(1280, 0, 120, 720)).is_empty(),
		"narrow dock cannot host castle popup"
	)
