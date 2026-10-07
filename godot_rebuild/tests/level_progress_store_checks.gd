extends RefCounted
## Isolated test file, never the development/default progress file.

const Store = preload("res://scripts/match/level_progress_store.gd")
const Progress = preload("res://scripts/match/level_progress.gd")
const TEST_PATH := "user://level_progress_test_only.json"
const CLAIM_PATH := "user://level_claim_test_only.json"
const World = preload("res://scripts/match/prototype_battle.gd")


func _cleanup() -> void:
	for path in [TEST_PATH, TEST_PATH + ".tmp", TEST_PATH + ".bak"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)


func run(check: Callable) -> void:
	_cleanup()
	for path in [CLAIM_PATH, CLAIM_PATH + ".tmp", CLAIM_PATH + ".bak"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)
	check.call(Store.load_state(TEST_PATH).is_empty(), "Missing progress is empty")
	var first: Dictionary = Progress.apply_result({}, 1, true, false, "normal")
	check.call(Store.save_state(first.state, TEST_PATH), "Write first clear")
	check.call(Store.load_state(TEST_PATH) == first.state, "Load first clear")
	var replay: Dictionary = Progress.apply_result(first.state, 1, true, false, "normal")
	check.call(Store.save_state(replay.state, TEST_PATH), "Replace with replay")
	check.call(Store.load_state(TEST_PATH) == replay.state, "Replay survives replacement")
	var invalid := {"meta_gold": -1, "completed_levels": [1]}
	check.call(not Store.save_state(invalid, TEST_PATH), "Negative currency rejected")
	check.call(
		not Store.save_state({"meta_gold": 0, "completed_levels": [1, 1]}, TEST_PATH),
		"Duplicate completion rejected"
	)
	check.call(Store.load_state(TEST_PATH) == replay.state, "Rejected write preserves save")
	var with_roster := replay.state.duplicate(true)
	with_roster["purchased_heroes"] = ["kaizen", "gornak"]
	with_roster["unlocked_bosses"] = ["gornak"]
	check.call(Store.save_state(with_roster, TEST_PATH), "Write persistent player hero roster")
	check.call(Store.load_state(TEST_PATH) == with_roster, "Player hero roster survives reload")
	var invalid_roster := with_roster.duplicate(true)
	invalid_roster["purchased_heroes"] = ["kaizen", "kaizen"]
	check.call(not Store.save_state(invalid_roster, TEST_PATH), "Duplicate purchased hero rejected")
	invalid_roster = with_roster.duplicate(true)
	invalid_roster["unlocked_bosses"] = ["kaizen"]
	check.call(
		not Store.save_state(invalid_roster, TEST_PATH), "Starter cannot occupy boss unlock list"
	)
	# Restore the replay state used by the interrupted-write checks below.
	check.call(
		Store.save_state(replay.state, TEST_PATH), "Roster save can return to progression state"
	)
	# Simulate an interrupted replacement: primary missing, backup intact.
	check.call(
		DirAccess.rename_absolute(TEST_PATH, TEST_PATH + ".bak") == OK,
		"Move progress to recovery copy"
	)
	check.call(Store.load_state(TEST_PATH) == replay.state, "Backup can recover progress")
	check.call(not Store.save_state(first.state, TEST_PATH), "Pending recovery blocks overwrite")
	check.call(Store.load_state(TEST_PATH) == replay.state, "Pending recovery remains intact")
	check.call(Store.recover_backup(TEST_PATH), "Restore interrupted write")
	check.call(not Store.recover_backup(TEST_PATH), "Cannot overwrite recovered primary")
	check.call(Store.save_state(first.state, TEST_PATH), "Recovered progress can be updated")
	# A malformed file is never interpreted as a new/empty valid save.
	var corrupt := FileAccess.open(TEST_PATH, FileAccess.WRITE)
	check.call(corrupt != null, "Open isolated file for corruption probe")
	if corrupt != null:
		corrupt.store_string("{truncated")
		corrupt.close()
	check.call(Store.load_state(TEST_PATH).is_empty(), "Reject truncated JSON")
	var fractional := FileAccess.open(TEST_PATH, FileAccess.WRITE)
	if fractional != null:
		fractional.store_string('{"version":1,"state":{"meta_gold":3.5,"completed_levels":[1]}}')
		fractional.close()
	check.call(
		Store.load_state(TEST_PATH).is_empty(), "Reject fractional currency without truncating"
	)
	check.call(not Store.recover_backup(TEST_PATH), "Never overwrite corrupt primary silently")
	var world := World.new()
	check.call(world.commit_level_result(CLAIM_PATH).is_empty(), "No result cannot commit")
	world.winner = 0
	var paid: Dictionary = world.commit_level_result(CLAIM_PATH)
	check.call(paid.get("reward", -1) == 3000, "Winning match commits first clear")
	check.call(
		Store.load_state(CLAIM_PATH) == paid.get("state", {}), "Committed state survives reload"
	)
	check.call(world.commit_level_result(CLAIM_PATH).is_empty(), "Same match cannot double-pay")
	var replay_world := World.new()
	replay_world.winner = 0
	var replay_paid: Dictionary = replay_world.commit_level_result(CLAIM_PATH)
	check.call(replay_paid.get("reward", -1) == 1500, "Next match pays replay once")
	check.call(
		Store.load_state(CLAIM_PATH) == replay_paid.get("state", {}), "Replay committed once"
	)
	var corrupt_claim := FileAccess.open(CLAIM_PATH, FileAccess.WRITE)
	if corrupt_claim != null:
		corrupt_claim.store_string("invalid save")
		corrupt_claim.close()
	var blocked := World.new()
	blocked.winner = 0
	check.call(blocked.commit_level_result(CLAIM_PATH).is_empty(), "Corrupt save blocks reward")
	check.call(not Store.save_state(first.state, CLAIM_PATH), "Corrupt save cannot be overwritten")
	_cleanup()
	for path in [CLAIM_PATH, CLAIM_PATH + ".tmp", CLAIM_PATH + ".bak"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)
