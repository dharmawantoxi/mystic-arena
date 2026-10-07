extends SceneTree
## Temporary native shutdown probe for the permanent Hero Shop ownership graph.

const APP = preload("res://app/App.tscn")
const Store = preload("res://scripts/match/hero_unlock_store.gd")


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var state := Store.bootstrap_state({})
	var item := Store.entry("thorne")
	var app := APP.instantiate()
	root.add_child(app)
	await _settle()
	var menu = app.current_screen
	menu.hero_shop_panel.open_with_state(state)
	await _settle()
	menu.hero_shop_panel.set_open(false)
	app.queue_free()
	await _settle()
	menu = null
	app = null
	state.clear()
	item.clear()
	await _settle()
	quit(0)


func _settle() -> void:
	await process_frame
	await process_frame
	await process_frame
