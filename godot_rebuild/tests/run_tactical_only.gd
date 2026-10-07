extends SceneTree
## Focused runner for the tactical command suites (domain + scene lifecycle).
## Same contract as run_all.gd: exit code 1 on any failure. Useful for bisecting
## a native-suite abort and for a fast Windows QA loop on this subsystem.

const TacticalChecks = preload("res://tests/tactical_checks.gd")
const TacticalSceneChecks = preload("res://tests/tactical_scene_checks.gd")
const APP = preload("res://app/App.tscn")

var failures: Array[String] = []
var checks := 0


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		printerr("FAIL: " + message)


func _settle() -> void:
	await process_frame
	await process_frame
	await process_frame


func _run() -> void:
	print("[stage] tactical domain")
	TacticalChecks.new().run(_check)
	print("[stage] tactical scene")
	var app = APP.instantiate()
	root.add_child(app)
	await _settle()
	await TacticalSceneChecks.new().run(self, app, _check)
	app.queue_free()
	await _settle()
	print("[stage] done")
	for message in failures:
		printerr("SUMMARY FAIL: " + message)
	if failures.is_empty():
		print("PASS: %d tactical checks" % checks)
		quit(0)
	else:
		printerr("FAIL: %d of %d tactical checks" % [failures.size(), checks])
		quit(1)
