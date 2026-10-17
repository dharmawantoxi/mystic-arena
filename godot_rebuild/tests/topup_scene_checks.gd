extends RefCounted
## Layer 9au: the top-up dialog wired into the live menu. The hero shop's
## TOP UP button opens the dialog on the active profile, the simulation
## purchase runs through the panel's `_process` tick and the save callable,
## and BACK closes it. Nothing is persisted: the save callable is swapped for
## a recorder during the check.

const TopupFlow = preload("res://scripts/match/topup_flow.gd")


func run(tree: SceneTree, app: Node, check: Callable) -> void:
	var menu: Node = app.current_screen
	var panel: Variant = menu.get_node_or_null("TopupPanel")
	var client: Variant = menu.get_node_or_null("TopupClient")
	check.call(panel != null and client != null, "menu owns the top-up panel and client")
	if panel == null or client == null:
		return
	var flow: TopupFlow = menu.topup_flow
	check.call(
		flow != null and panel.flow == flow and client.flow == flow,
		"panel and client share the flow"
	)
	check.call(
		(
			flow.server_url == TopupFlow.default_server_url()
			and (flow.transport == null) == flow.server_url.is_empty()
		),
		"client follows MYSTIC_TOPUP_URL (simulation when unset)"
	)
	check.call(not panel.visible, "top-up dialog starts hidden")
	var original_save: Callable = flow.save_callable
	var saved: Array = []
	flow.save_callable = func(profile: Dictionary) -> bool:
		saved.append(profile.duplicate(true))
		return true
	flow.transport = null
	var original_url := flow.server_url
	flow.server_url = ""
	menu.hero_shop_panel.topup_requested.emit()
	await tree.process_frame
	check.call(
		panel.visible and flow.is_open and flow.phase == "select", "TOP UP button opens the dialog"
	)
	var gold_before := flow.meta_gold()
	check.call(
		panel.button("topup_pay") != null and panel.button("topup_pay").visible,
		"PAY NOW button is live"
	)
	check.call(
		panel.button("topup_pay").text.begins_with("PAY NOW"), "PAY NOW shows the local price"
	)
	panel.button("topup_pay").pressed.emit()
	check.call(flow.phase == "processing", "PAY NOW starts the simulated payment")
	for _frame in range(120):
		await tree.process_frame
		if flow.phase != "processing":
			break
	check.call(flow.phase == "success", "panel ticks the simulation to success")
	check.call(
		(
			saved.size() == 1
			and int(saved[0].get("meta_gold", -1)) == gold_before + int(TopupFlow.PACKAGES[0].gold)
		),
		"grant persists +%d Hero Gold through the save callable" % int(TopupFlow.PACKAGES[0].gold)
	)
	check.call(
		saved.size() == 1 and Array(saved[0].get("topup_history", [])).size() >= 1,
		"grant appends a topup_history entry"
	)
	panel.button("topup_back").pressed.emit()
	await tree.process_frame
	check.call(not panel.visible and not flow.is_open, "BACK closes the dialog")
	# voucher keypad through the panel buttons
	menu.hero_shop_panel.topup_requested.emit()
	panel.button("topup_redeem").pressed.emit()
	for key_name in ["vpk_1", "vpk_2", "vpk_3", "vpk_4", "vpk_5", "vpk_6"]:
		panel.button(key_name).pressed.emit()
	check.call(
		flow.phase == "redeem" and flow.redeem_input == "MA-123456", "keypad buttons type the code"
	)
	panel.button("vback").pressed.emit()
	panel.button("topup_cancel").pressed.emit()
	await tree.process_frame
	check.call(not panel.visible, "CANCEL closes the dialog")
	flow.save_callable = original_save
	flow.server_url = original_url
	client.configure(flow, original_url)
	if menu.hero_shop_panel.is_open:
		menu.hero_shop_panel.set_open(false)
