class_name KaizenBodyBuilder
extends Node
## Builds the Kaizen rig programmatically.
##
## Why code instead of .tscn? Pixel-art rigs need ~40 Polygon2D nodes with
## hand-tuned vertex lists. Writing these in the .tscn editor is fine for
## the artist, but a clean, version-controlled source of truth is the GDScript
## here. The output is the same Node2D tree you would build in the editor.
##
## Result tree under [code]target[/code]:
##   Body (Node2D)
##   ├── Torso, Chest, Sash, Pelvis (Polygon2D)
##   ├── LeftThigh, RightThigh, LeftBoot, RightBoot (Polygon2D)
##   ├── Head (Node2D)
##   │   ├── Neck, Skull, HairBack, HairFront, TopKnot, Band
##   │   ├── Eye (left, mirrored for right)
##   │   └── Iris
##   ├── SwordArm (Node2D, pivot at shoulder)
##   │   ├── UpperArm, Forearm, Glove
##   │   └── Sword (Node2D, pivot at hilt)
##   │       ├── SwordHandle, SwordGuard
##   │       └── SwordBlade, SwordEdge
##   └── Scabbard (Node2D, pivot at hip)
##       ├── ScabbardBody, ScabbardTip
##

const P := {
	"ink":          Color(0.094, 0.102, 0.157),
	"skin_dark":    Color(0.471, 0.329, 0.259),
	"skin_mid":     Color(0.769, 0.588, 0.439),
	"skin_light":   Color(0.886, 0.729, 0.573),
	"hair_dark":    Color(0.114, 0.094, 0.086),
	"hair_mid":     Color(0.337, 0.267, 0.196),
	"cloth_dark":   Color(0.149, 0.196, 0.337),
	"cloth_mid":    Color(0.243, 0.329, 0.525),
	"cloth_light":  Color(0.4, 0.541, 0.761),
	"sash":         Color(0.337, 0.510, 0.808),
	"pants_mid":    Color(0.180, 0.235, 0.431),
	"pants_dark":   Color(0.102, 0.141, 0.259),
	"boot":         Color(0.082, 0.063, 0.043),
	"steel_dark":   Color(0.298, 0.322, 0.369),
	"steel_mid":    Color(0.494, 0.525, 0.580),
	"steel_light":  Color(0.722, 0.745, 0.792),
	"steel_shine":  Color(0.902, 0.925, 0.961),
	"gold_mid":     Color(0.662, 0.494, 0.169),
	"saya_dark":    Color(0.451, 0.118, 0.173),
	"saya_mid":     Color(0.631, 0.176, 0.247),
	"wrap_mid":     Color(0.463, 0.165, 0.204),
	"eye_white":    Color(0.969, 0.992, 1.0),
	"eye_iris":     Color(0.808, 0.596, 0.212),
	"wind":         Color(0.439, 0.698, 0.902),
	"wind_bright":  Color(0.847, 0.949, 1.0),
}


## Build the rig under [param target]. [param target] is typically a
## Node2D called "Body" inside the Kaizen scene.
static func build(target: Node2D) -> void:
	# Clear any pre-existing children (idempotent).
	for c in target.get_children():
		c.queue_free()

	# Body anchor is at the character's feet. Y is up.
	# Body parts are positioned with y=0 at the hip line.
	_make_poly(target, "Torso", P["cloth_mid"],
		[-12, -8, 12, -8, 14, 14, 10, 22, -10, 22, -14, 14])
	_make_poly(target, "Chest", P["cloth_dark"],
		[-10, -4, 10, -4, 8, 4, -8, 4])
	_make_poly(target, "Sash", P["sash"],
		[-13, 8, 13, 8, 11, 16, -11, 16])
	_make_poly(target, "Pelvis", P["cloth_dark"],
		[-10, 18, 10, 18, 8, 28, -8, 28])

	# Legs (thighs + boots). The exact silhouette: thick upper, taper to boot.
	_make_poly(target, "LeftThigh", P["pants_mid"],
		[-8, 26, -2, 26, -3, 42, -7, 42])
	_make_poly(target, "RightThigh", P["pants_mid"],
		[2, 26, 8, 26, 7, 42, 3, 42])
	_make_poly(target, "LeftBoot", P["boot"],
		[-8, 40, -2, 40, -1, 48, -9, 48])
	_make_poly(target, "RightBoot", P["boot"],
		[2, 40, 8, 40, 9, 48, 1, 48])

	# Head.
	var head := Node2D.new()
	head.name = "Head"
	head.position = Vector2(0, -22)
	target.add_child(head)
	_make_poly(head, "Neck", P["skin_mid"],
		[-4, 8, 4, 8, 3, 14, -3, 14])
	_make_poly(head, "Skull", P["skin_mid"],
		[-9, -10, 9, -10, 10, 0, 8, 6, -8, 6, -10, 0])
	_make_poly(head, "HairBack", P["hair_dark"],
		[-11, -12, 11, -12, 10, -4, 6, -2, -6, -2, -10, -4])
	_make_poly(head, "HairFront", P["hair_dark"],
		[-10, -10, 10, -10, 8, -4, -8, -4])
	_make_poly(head, "TopKnot", P["hair_dark"],
		[-4, -16, 4, -16, 3, -10, -3, -10])
	_make_poly(head, "Band", P["wrap_mid"],
		[-10, -6, 10, -6, 9, -4, -9, -4])
	_make_poly(head, "Eye", P["eye_white"],
		[-6, -2, -2, -2, -2, 1, -6, 1])
	_make_poly(head, "Iris", P["eye_iris"],
		[-5, -1, -3, -1, -3, 0, -5, 0])

	# Sword arm — pivot at the right shoulder, y -2 (where the arm meets torso).
	var sword_arm := Node2D.new()
	sword_arm.name = "SwordArm"
	sword_arm.position = Vector2(10, -2)
	target.add_child(sword_arm)
	_make_poly(sword_arm, "UpperArm", P["cloth_dark"],
		[-4, 0, 4, 0, 5, 14, -5, 14])
	_make_poly(sword_arm, "Forearm", P["skin_mid"],
		[-3, 0, 3, 0, 4, 12, -4, 12], Vector2(0, 12))
	_make_poly(sword_arm, "Glove", P["boot"],
		[-4, 0, 4, 0, 5, 4, -5, 4], Vector2(0, 22))

	# Sword — pivot at the hilt. Rotated slightly so it points up-and-back.
	var sword := Node2D.new()
	sword.name = "Sword"
	sword.position = Vector2(0, 24)
	sword.rotation = -0.6
	sword_arm.add_child(sword)
	_make_poly(sword, "SwordHandle", P["wrap_mid"],
		[-2, 0, 2, 0, 2, 8, -2, 8])
	_make_poly(sword, "SwordGuard", P["gold_mid"],
		[-5, -1, 5, -1, 5, 2, -5, 2], Vector2(0, 8))
	_make_poly(sword, "SwordBlade", P["steel_light"],
		[-2, 0, 2, 0, 1, 38, -1, 38], Vector2(0, 10))
	_make_poly(sword, "SwordEdge", P["steel_shine"],
		[0, 0, 2, 0, 1, 36, 0, 36], Vector2(0, 11))

	# Scabbard (off the left hip).
	var scabbard := Node2D.new()
	scabbard.name = "Scabbard"
	scabbard.position = Vector2(-8, 14)
	scabbard.rotation = -0.3
	target.add_child(scabbard)
	_make_poly(scabbard, "ScabbardBody", P["saya_mid"],
		[-3, 0, 3, 0, 2, 30, -2, 30])
	_make_poly(scabbard, "ScabbardTip", P["saya_dark"],
		[-3, 0, 3, 0, 0, 4], Vector2(0, 30))


## Create a Polygon2D as a child of [param parent]. [param pts] is a flat
## array of floats [x0, y0, x1, y1, ...] in local space. Optional [param pos]
## is the local offset for this polygon within [param parent].
static func _make_poly(parent: Node, name: String, color: Color,
		pts, pos: Vector2 = Vector2.ZERO) -> Polygon2D:
	var poly := Polygon2D.new()
	poly.name = name
	poly.color = color
	poly.position = pos
	poly.polygon = _to_packed(pts)
	parent.add_child(poly)
	return poly


static func _to_packed(arr) -> PackedVector2Array:
	var out := PackedVector2Array()
	if arr == null:
		return out
	if arr is PackedFloat32Array:
		for i in range(0, arr.size(), 2):
			out.append(Vector2(arr[i], arr[i + 1]))
	elif arr is Array:
		for i in range(0, arr.size(), 2):
			out.append(Vector2(arr[i], arr[i + 1]))
	return out
