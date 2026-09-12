# HeroSkillGdextParityTest — hero_skills/_bundle.py -> godot++ (C++).
#
# Scene ini memutar ULANG HeroSkillParityTest (oracle Pygame: 222 hero × 4
# skenario, jejak event per frame + state final) dengan backend skill kit
# DIPAKSA ke GDExtension C++ (`MysticHeroSkills`, lib hasil build
# godot/gdext/mystic_skills). Jadi yang diuji bukan "C++ sama dengan C++",
# melainkan "C++ sama dengan Python", lewat rantai:
#
#   hero_skills/_bundle.py --(tools/test_godot_match_parity.py)--> fixture
#   fixture <--dibandingkan--> Hero.gd + HeroSkillKitLoader -> MysticHeroSkills (C++)
#
# Hero.gd memanggil skill lewat HeroSkillKitLoader, jadi memaksa backend di
# loader sudah cukup untuk mengalihkan init_state/update_timers/cast_q..r
# (dan pembanding sort __by_pair0) ke C++ tanpa menyentuh Hero.gd.
#
# Ditambah baterai A/B backend untuk API yang TIDAK pasti tersentuh replay:
# hero_kind() + visual_duration() untuk SEMUA hero_type katalog HeroDB
# (closed-world: hero baru yang lupa dimasukkan generator C++ ketahuan di
# sini), dan urutan sort_custom __by_pair0 dengan jarak SERI (tie-break indeks
# = stabilitas sort Python).
#
# Scene ini HANYA berarti kalau lib GDExt sudah dibuild:
#   cd godot/gdext/mystic_skills
#   git clone -b godot-4.3-stable --depth 1 \
#     https://github.com/godotengine/godot-cpp godot-cpp
#   scons platform=linux target=template_debug -j4
# Tanpa lib, scene GAGAL (bukan skip) — CI .github/workflows/godot-gdext.yml
# yang membuild lib lalu menjalankannya. Jalur GDScript murni tetap dijaga
# HeroSkillParityTest di godot-check.yml (tanpa compiler).
#
# godot --headless --path godot res://tests/HeroSkillGdextParityTest.tscn --quit-after 900
# Require "[HeroSkillGdextParityTest] PASS" tanpa SCRIPT ERROR / Parse Error.
extends "res://tests/HeroSkillParityTest.gd"

const Loader = preload("res://scenes/hero/HeroSkillKitLoader.gd")

## Kunci q/w/e/r pada tabel durasi visual.
const KEYS: Array = ["q", "w", "e", "r"]


## Hero tiruan untuk hero_kind()/visual_duration(): cuma butuh `hero_type`.
## Node2D polos TIDAK cukup — `set("hero_type", ...)` pada node tanpa properti
## itu mencetak "Invalid set index" yang dibaca fatal oleh godot_log_gate.
class KindProbe extends Node2D:
	var hero_type := ""
	var team := "blue"


func _boot() -> void:
	if not Loader.gdext_available():
		_fail_gdext("class MysticHeroSkills tidak terdaftar engine",
			"build lib GDExt dulu (godot/gdext/mystic_skills/README.md) lalu "
			+ "jalankan scene ini — tanpa lib, jalur C++ tidak teruji")
		_abort()
		return
	Loader.force_backend("gdext")
	if not Loader.is_using_gdext():
		_fail_gdext("force_backend('gdext') tidak mengaktifkan jalur C++",
			"HeroSkillKitLoader gagal instantiate MysticHeroSkills")
		_abort()
		return
	print("[HeroSkillGdextParityTest] backend=%s (class MysticHeroSkills termuat)"
		% Loader.backend_name())

	_ab_battery()

	# Sisa replay = persis HeroSkillParityTest (fixture oracle Pygame), tapi
	# tiap init_state/update_timers/cast_* kini masuk ke C++.
	super._boot()


## A/B backend: C++ vs GDScript untuk API yang tidak selalu tersentuh replay.
## Backend DIPAKAI per-batch (bukan per panggilan) — force_backend() me-resolve
## ulang loader, jadi memanggilnya 2×222×5 kali hanya memboroskan waktu + log.
func _ab_battery() -> void:
	var types: Array = HeroDB.get_all_types()
	if types.is_empty():
		_fail_gdext("HeroDB.get_all_types() kosong",
			"katalog heroes.json tidak termuat — A/B backend tidak bisa jalan")
		return
	var probe := KindProbe.new()
	add_child(probe)
	var got_c := _collect("gdext", probe, types)
	var got_g := _collect("gdscript", probe, types)
	Loader.force_backend("gdext")
	probe.free()

	var kind_mismatch := 0
	var vis_mismatch := 0
	var keys := got_c.keys()
	keys.sort()
	for k in keys:
		_checks += 1
		var a = got_c[k]
		var b = got_g.get(k)
		if str(a) == str(b):
			continue
		if str(k).begins_with("kind:"):
			kind_mismatch += 1
		else:
			vis_mismatch += 1
		_fail_gdext(str(k), "C++ %s vs GDScript %s" % [str(a), str(b)])
	_ab_sort_tiebreak()
	print("[HeroSkillGdextParityTest] A/B backend: %d hero_type × (hero_kind + "
		% types.size()
		+ "4 visual_duration) + tie-break sort = %d check, mismatch %d kind / %d vis"
		% [keys.size(), kind_mismatch, vis_mismatch])


## Kumpulkan hero_kind() + visual_duration(q/w/e/r) satu backend untuk semua
## hero_type katalog — kunci dict: "kind:<type>" / "vis:<type>/<key>".
func _collect(backend: String, probe, types: Array) -> Dictionary:
	Loader.force_backend(backend)
	var out := {}
	for ht in types:
		var name := str(ht)
		probe.hero_type = name
		out["kind:" + name] = str(Loader.hero_kind(probe))
		for key in KEYS:
			out["vis:" + name + "/" + str(key)] = int(
				Loader.get_visual_duration(name, str(key)))
	return out


## Urutan sort jarak dengan jarak SERI — `sort` Python stabil; GDScript meniru
## lewat elemen [dist, e, idx]; C++ harus menghasilkan urutan identik.
func _ab_sort_tiebreak() -> void:
	var pairs := [
		[10.0, "a", 0],
		[5.0, "b", 1],
		[10.0, "c", 2],
		[0.0, "d", 3],
		[5.0, "e", 4],
		[10.0, "f", 5],
		[5.0, "g", 6],
	]
	var got_c := _sort_with("gdext", pairs)
	var got_g := _sort_with("gdscript", pairs)
	Loader.force_backend("gdext")
	_checks += 1
	if str(got_c) != str(got_g):
		_fail_gdext("__by_pair0 tie-break", "C++ %s vs GDScript %s"
			% [str(got_c), str(got_g)])


func _sort_with(backend: String, pairs: Array) -> Array:
	var arr := pairs.duplicate(true)
	Loader.force_backend(backend)
	arr.sort_custom(Callable(Loader, "__by_pair0"))
	var labels: Array = []
	for row in arr:
		labels.append(str(row[1]))
	return labels


func _fail_gdext(tag: String, message: String) -> void:
	# Lewat _fail() base supaya ikut terhitung di _failures (exit code 1) dan
	# tercetak dengan pola "[...Test] ..." yang dibaca godot_log_gate.
	_fail("gdext/" + tag, message)


func _abort() -> void:
	_done = true
	for msg in _error_messages:
		print(msg)
	print("[HeroSkillGdextParityTest] FAIL: jalur C++ tidak bisa diuji")
	Loader.reset_backend()
	get_tree().quit(1)


func _finish() -> void:
	if _done:
		return
	var failed := int(_failures)
	var heroes := int(_hero_count)
	var events := int(_event_checks)
	var checks := int(_checks)
	super._finish()
	Loader.reset_backend()
	if failed == 0:
		print("[HeroSkillGdextParityTest] PASS: %d hero lewat MysticHeroSkills "
			% heroes + "(C++), %d event + %d check" % [events, checks])
		print("[HeroSkillGdextParityTest] PASS")
	else:
		print("[HeroSkillGdextParityTest] FAIL: %d kegagalan di backend gdext"
			% failed)
