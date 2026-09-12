# HeroSkillKitLoader.gd — pilih implementasi skill kit: GDExt (MysticHeroSkills)
# atau GDScript (HeroSkillKit.gd, hasil transpile tools/gen_hero_skill_kit.py).
#
# Bagian dari migrasi hero_skills/_bundle.py -> godot++ (C++ GDExtension):
#   python side   hero_skills/_bundle.py            (sumber kebenaran)
#   GDScript side godot/scenes/hero/HeroSkillKit.gd (tools/gen_hero_skill_kit.py)
#   C++ side      godot/gdext/mystic_skills/src/*   (tools/gen_hero_skills_cpp.py)
# Keduanya dibangkitkan dari AST Python yang sama, jadi API-nya identik dan
# loader ini murni saklar: Hero.gd tidak tahu backend mana yang jalan.
#
# Kapan pakai C++: mystic/skills/use_gdext_skills=true DI project.godot DAN
# lib hasil scons ada di addons/mystic_skills/bin/ (lihat
# godot/gdext/mystic_skills/README.md + .github/workflows/godot-gdext.yml).
# Kalau lib belum dibuild, fallback ke GDScript — tidak ada error, tidak ada
# perubahan perilaku.
#
# PENTING: tidak boleh menyebut `MysticHeroSkills` sebagai IDENTIFIER di sini.
# Di CI headless lib .so tidak ikut repo, jadi referensi langsung ke class
# GDExt akan Parse Error dan mematikan seluruh project. Semua akses lewat
# ClassDB.class_exists/instantiate dengan string — pola sama dengan
# LightingCompat.gd untuk MysticLighting.

extends RefCounted

const HeroSkillKitGD = preload("res://scenes/hero/HeroSkillKit.gd")

## Nama class yang didaftarkan register_types.cpp (GDCLASS MysticHeroSkills).
const GDEXT_CLASS := "MysticHeroSkills"
## Setting project yang menyalakan jalur C++.
const SETTING := "mystic/skills/use_gdext_skills"
## Hero starter = satu-satunya hero_type yang punya kelas handler sendiri;
## sisanya lewat BossHeroSkills (kind "boss"). Sama dengan hero_kind().
const STARTER_KINDS := ["grimjaw", "kaizen", "sylara", "thorne", "vex", "zephyr"]

static var _use_gdext: bool = false
static var _checked: bool = false
## "" = ikut ProjectSettings; "gdext"/"gdscript" = paksa (harness paritas
## HeroSkillGdextParityTest butuh ini karena project.godot default-nya false).
static var _forced: String = ""
## Instance GDExt di-cache: semua method MysticHeroSkills static, tapi Godot
## butuh sebuah Object untuk callv(). Tanpa cache, tiap panggilan skill (dan
## tiap pembanding sort_custom __by_pair0!) mengalokasikan instance baru.
static var _inst: Object = null
## Backend terakhir yang DIUMUMKAN ke log — harness A/B memanggil
## force_backend() ribuan kali, dan satu baris log per panggilan menenggelamkan
## error sungguhan (plus CI me-require baris ini, jadi harus tetap tercetak).
static var _announced: String = "__belum__"


## True kalau lib C++ termuat engine (terlepas dari setting/force).
static func gdext_available() -> bool:
	return ClassDB.class_exists(GDEXT_CLASS)


static func _resolve() -> void:
	_checked = true
	_use_gdext = false
	_inst = null
	var want := _forced
	if want == "":
		var flag := false
		if ProjectSettings.has_setting(SETTING):
			flag = bool(ProjectSettings.get_setting(SETTING))
		want = "gdext" if flag else "gdscript"
	if want == "gdext":
		if not ClassDB.class_exists(GDEXT_CLASS):
			if _forced == "":
				_announce("gdext-hilang", "[HeroSkillKitLoader] flag "
					+ "use_gdext_skills=true tapi GDExt tidak ditemukan, "
					+ "fallback GDScript")
		else:
			var inst = ClassDB.instantiate(GDEXT_CLASS)
			if inst == null:
				_announce("gdext-gagal", "[HeroSkillKitLoader] GAGAL instantiate "
					+ "%s, fallback GDScript" % GDEXT_CLASS)
			else:
				_inst = inst
				_use_gdext = true
				# Baris ini di-require CI (godot-gdext.yml): bukti jalur C++
				# benar-benar dipakai, bukan fallback diam-diam.
				_announce("gdext", "[HeroSkillKitLoader] GDExtension "
					+ "MysticHeroSkills aktif (godot++ C++)")
	if not _use_gdext:
		_announce("gdscript", "[HeroSkillKitLoader] backend GDScript "
			+ "(HeroSkillKit.gd transpile)")


## Cetak sekali per PERUBAHAN backend (bukan sekali per panggilan _resolve).
static func _announce(key: String, message: String) -> void:
	if _announced == key:
		return
	_announced = key
	print(message)


static func _ensure_checked() -> void:
	if not _checked:
		_resolve()


## Paksa backend — dipakai harness paritas supaya jalur C++ bisa diuji tanpa
## mengubah project.godot (yang default-nya false demi CI tanpa compiler).
## backend: "gdext" | "gdscript" | "" (kembali ikut ProjectSettings).
static func force_backend(backend: String) -> void:
	_forced = backend
	_checked = false
	_inst = null
	_resolve()


static func reset_backend() -> void:
	force_backend("")


## "gdext" kalau jalur C++ aktif, selain itu "gdscript".
static func backend_name() -> String:
	_ensure_checked()
	return "gdext" if _use_gdext else "gdscript"


static func is_using_gdext() -> bool:
	_ensure_checked()
	return _use_gdext


## Panggil method static MysticHeroSkills lewat instance cache.
## Return null kalau backend GDScript aktif / method tidak ada — pemanggil
## menerjemahkan null menjadi "pakai fallback GDScript".
static func _call_gdext(method: String, args: Array):
	_ensure_checked()
	if _inst == null:
		return null
	if not _inst.has_method(method):
		push_error("[HeroSkillKitLoader] %s tidak punya method %s — "
			% [GDEXT_CLASS, method]
			+ "regenerasi tools/gen_hero_skills_cpp.py")
		return null
	return _inst.callv(method, args)


static func hero_kind(h) -> String:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("hero_kind", [h])
		if r != null:
			return str(r)
	return HeroSkillKitGD.hero_kind(h)


static func init_state(h) -> void:
	_ensure_checked()
	if _use_gdext:
		# return void: JANGAN cek null di sini — null artinya "nilai balik nil",
		# bukan "gagal". Kalau jatuh ke GDScript juga, kit di-init dua kali.
		_call_gdext("init_state", [h])
		return
	HeroSkillKitGD.init_state(h)


static func update_timers(h, all_units, all_towers, all_bases) -> void:
	_ensure_checked()
	if _use_gdext:
		_call_gdext("update_timers", [h, all_units, all_towers, all_bases])
		return
	HeroSkillKitGD.update_timers(h, all_units, all_towers, all_bases)


static func cast_q(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_q", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_q(h, all_units, all_towers, all_bases)


static func cast_w(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_w", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_w(h, all_units, all_towers, all_bases)


static func cast_e(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_e", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_e(h, all_units, all_towers, all_bases)


static func cast_r(h, all_units, all_towers, all_bases) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("cast_r", [h, all_units, all_towers, all_bases])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.cast_r(h, all_units, all_towers, all_bases)


## Pembanding sort jarak (dist, lalu indeks = tie-break stabil Python) —
## dipakai Hero.gd: enemies.sort_custom(Callable(HeroSkillKit, "__by_pair0")).
static func __by_pair0(a, b) -> bool:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("__by_pair0", [a, b])
		if r != null:
			return bool(r)
	return HeroSkillKitGD.__by_pair0(a, b)


static func by_pair0(a, b) -> bool:
	return __by_pair0(a, b)


## Durasi visual skill (FRAME) untuk hero_type + tombol q/w/e/r.
## Backend C++: MysticHeroSkills.visual_duration. Fallback GDScript membaca
## tabel konstanta HeroSkillKit.gd yang sama (DEFAULT/VISUAL_DURATION/
## BOSS_HERO_VISUAL_DURATION) — BUKAN angka 40 hardcoded seperti dulu.
static func get_visual_duration(hero_type: String, key: String) -> int:
	_ensure_checked()
	if _use_gdext:
		var r = _call_gdext("visual_duration", [hero_type, key])
		if r != null:
			return int(r)
	return _gdscript_visual_duration(hero_type, key)


static func visual_duration(hero_type: String, key: String) -> int:
	return get_visual_duration(hero_type, key)


static func _gdscript_visual_duration(hero_type: String, key: String) -> int:
	var dflt: Dictionary = HeroSkillKitGD.DEFAULT_VISUAL_DURATION
	if STARTER_KINDS.has(hero_type):
		var per_kind: Dictionary = HeroSkillKitGD.VISUAL_DURATION
		if per_kind.has(hero_type) and (per_kind[hero_type] as Dictionary).has(key):
			return int((per_kind[hero_type] as Dictionary)[key])
		return int(dflt.get(key, 60))
	var boss: Dictionary = HeroSkillKitGD.BOSS_HERO_VISUAL_DURATION
	if boss.has(hero_type) and (boss[hero_type] as Dictionary).has(key):
		return int((boss[hero_type] as Dictionary)[key])
	return int(dflt.get(key, 60))
