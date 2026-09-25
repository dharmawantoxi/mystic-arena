extends RefCounted

const Slot = preload("res://scripts/match/build_slot.gd")


static func create(paths: Array[PackedVector2Array]) -> Array[Slot]:
	var slots: Array[Slot] = []
	for team in range(2):
		for lane in range(3):
			var fractions: Array = [0.15, 0.30, 0.45] if lane != 1 else [0.10, 0.25, 0.40]
			if team == 1:
				fractions = [0.85, 0.70, 0.55] if lane != 1 else [0.90, 0.75, 0.60]
			for fraction in fractions:
				var slot := Slot.new()
				slot.id = slots.size()
				slot.team = team
				slot.lane = lane
				var index := mini(int(paths[lane].size() * float(fraction)), paths[lane].size() - 1)
				slot.position = paths[lane][index]
				slots.append(slot)
	return slots
