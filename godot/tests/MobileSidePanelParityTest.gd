# Regression smoke test for the responsive landscape rail and shop entry points.
extends Node

const MainScene = preload("res://scenes/main.tscn")

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	var failures := 0
	if MobileLayout == null:
		failures += 1
	var main := MainScene.instantiate()
	add_child(main)
	await get_tree().process_frame
	var hud := main.find_child("HUD", true, false)
	var rail := hud.find_child("SidePanel", true, false) if hud else null
	var shop := hud.find_child("ShopPanel", true, false) if hud else null
	if rail == null:
		failures += 1
	if shop == null:
		failures += 1
	if rail != null and rail.get_child_count() == 0:
		failures += 1
	if failures == 0:
		print("[MobileSidePanelParityTest] PASS")
		get_tree().quit(0)
	else:
		push_error("MobileSidePanelParityTest failures: %d" % failures)
		get_tree().quit(1)
