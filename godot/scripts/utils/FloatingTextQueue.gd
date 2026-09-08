# FloatingTextQueue — data/antrean EffectManager + FloatingText pygame.
# FASE 14: popup gold boss dan teks SLAYER di map memakai antrean yang sama.
# Data frame (60 Hz) terpisah dari draw; WorldPopups hanya membacanya.
# Font/shadow/rasterisasi tidak diklaim pixel-identik oleh tes headless.
extends RefCounted
class_name FloatingTextQueue

const MAX_FLOATING := 300

var floating_texts: Array = []
# DamageNumber lama masih menggambar dirinya sendiri. WeakRef memasukkannya
# ke FIFO/budget YANG SAMA, supaya +G tidak memperoleh 300 slot tambahan
# di arena ramai. Data/gerak popup reward tetap hanya di floating_texts.
var _order: Array = []
var damage_numbers_enabled := true
var max_damage_numbers := 16
# RNG lokal yang bisa direkam harness. Produksi tetap RNG Godot biasa;
# oracle mengunci HANYA uniform FloatingText + randint add_damage_number,
# bukan RNG combat atau cinematic. Jumlah/urutan/range ikut direplay.
var uniform_rng: Callable = randf_range
var integer_rng: Callable = randi_range
var _accum := 0.0


func reset() -> void:
	for entry in _order:
		if entry is WeakRef:
			var node = entry.get_ref()
			if is_instance_valid(node):
				node.queue_free()
	_order.clear()
	floating_texts.clear()
	_accum = 0.0


## _render.EffectManager.add_gold_popup: TIDAK membaca flag damage number
## atau anggaran kualitas. Batas keras 300, buang satu yang tertua.
func add_gold_popup(x: float, y: float, amount: int) -> void:
	_append(x, y - 10.0, "+%dG" % amount, false, -1.5, 50, 18)


## Cabang critical EffectManager.add_damage_number yang dipanggil
## Game._unlock_achievement(map_x, map_y). Judul sudah berakhiran !,
## pygame menambah ! lagi — sengaja TIDAK 'dibetulkan' jadi satu.
func add_slayer_text(x: float, y: float, title: String) -> void:
	if not damage_numbers_enabled:
		return
	_prepare_damage_slot()
	var offset_x := int(integer_rng.call(-8, 8))
	var offset_y := int(integer_rng.call(-3, 3))
	_append(x + offset_x, y + offset_y, title + "!", true, -2.0, 45, 24)


func _append(x: float, y: float, text: String, critical: bool,
		velocity_y: float, lifetime: int, font_size: int) -> void:
	var data := {
		"x": x, "y": y, "text": text, "color": [255, 220, 50],
		"velocity_x": 0.0, "velocity_y": velocity_y,
		"lifetime": lifetime, "max_lifetime": lifetime, "alive": true,
		"critical": critical, "font_size": font_size,
		"x_drift": float(uniform_rng.call(-0.3, 0.3)),
		"scale": 0.3, "target_scale": 1.2 if critical else 1.0,
	}
	_prune()
	floating_texts.append(data)
	_order.append(data)
	if _order.size() > MAX_FLOATING:
		_drop_oldest()


func advance(delta: float) -> void:
	_accum += delta
	while _accum >= 1.0 / 60.0:
		_accum -= 1.0 / 60.0
		tick()


## FloatingText.update diikuti filter alive EffectManager.update.
func tick() -> void:
	for t in floating_texts:
		if not bool(t["alive"]):
			continue
		t["x"] += float(t["velocity_x"]) + float(t["x_drift"])
		t["y"] += float(t["velocity_y"])
		t["velocity_y"] *= 0.95
		if float(t["scale"]) < float(t["target_scale"]):
			t["scale"] += (float(t["target_scale"]) - float(t["scale"])) * 0.3
		else:
			t["scale"] *= 0.99
		t["lifetime"] -= 1
		if int(t["lifetime"]) <= 0:
			t["alive"] = false
	floating_texts = floating_texts.filter(func(t): return bool(t["alive"]))
	_prune()


## Adapter FIFO bagi renderer DamageNumber lama. Tidak memindahkan pixel
## draw/geraknya ke view baru, hanya menyatukan budget EffectManager.
func register_damage_number(node: Node) -> void:
	if not damage_numbers_enabled:
		node.queue_free()
		return
	_prepare_damage_slot()
	_order.append(weakref(node))
	if _order.size() > MAX_FLOATING:
		_drop_oldest()


func _prepare_damage_slot() -> void:
	_prune()
	# Pygame menghapus SATU yang tertua, bukan menguras sampai cap kualitas.
	if _order.size() >= max_damage_numbers or _order.size() >= MAX_FLOATING:
		if not _order.is_empty():
			_drop_oldest()


func _drop_oldest() -> void:
	var entry = _order.pop_front()
	if entry is Dictionary:
		# Array.erase memakai equality nilai; gunakan identity supaya
		# dua popup identik tetap memiliki urutan FIFO yang benar.
		for i in range(floating_texts.size()):
			if is_same(floating_texts[i], entry):
				floating_texts.remove_at(i)
				break
	else:
		var node = entry.get_ref()
		if is_instance_valid(node):
			node.queue_free()


func _prune() -> void:
	_order = _order.filter(func(entry):
		if entry is Dictionary:
			return bool(entry["alive"])
		var node = entry.get_ref()
		return is_instance_valid(node) and not node.is_queued_for_deletion())


## Urutan seluruh FIFO (termasuk adapter legacy), dipakai replay budget
## headless tanpa harus membandingkan rasterisasi renderer lama.
func queued_texts() -> Array:
	_prune()
	var texts: Array = []
	for entry in _order:
		texts.append(entry["text"] if entry is Dictionary else entry.get_ref().text)
	return texts
