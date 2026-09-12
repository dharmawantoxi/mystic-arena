# HurtFlash.gd — flash putih saat HP turun, port `hurt_flash_timer` pygame.
#
# SUMBER PARITAS
#   Minion : _entity.py:5484 (init), :5545-5551 (set 8 frame saat hp < prev_hp,
#            lalu hitung mundur tiap frame di update())
#   Boss   : bosses/base_boss.py:483 / :6039 / :609-610 (mekanisme identik) —
#            dan renderer boss BENAR-BENAR membacanya, mis. `_draw_generic_body`
#            (:6307) mengganti warna badan jadi putih selama timer > 0.
#   Hero   : pygame TIDAK punya hurt flash untuk hero; di Godot hero memakainya
#            juga supaya semua unit bereaksi seragam (deviasi visual yang
#            disengaja, dicatat di godot/README.md).
#
# KENAPA DETEKSI `hp < prev_hp` DAN BUKAN HOOK DI take_damage()
# Sama persis dengan alasan pygame menaruhnya di update(): damage datang dari
# BANYAK pintu. Di port Godot pun `Hero.take_damage()` / `Minion.take_damage()`
# hampir tidak pernah dipanggil — serangan dasar hero (`Hero._attack`), peluru
# menara (`TowerBullet`), skill (`SkillBook._damage`), item, dan reflect semua
# memanggil `CombatSystem.apply_damage()` LANGSUNG (yang mengubah `target.hp`).
# Menonton `hp` menangkap semuanya tanpa harus menambal tiap call site.
#
# CATATAN: ini flash unit-nya sendiri, BUKAN "impact FX" (flash + shockwave +
# serpihan + shake + hit-stop) yang oleh pemilik game dilarang untuk serangan
# dasar — lihat tools/test_basic_attack_no_impact_fx.py dan Hero.play_hit_fx().
extends RefCounted

## 8 frame @60fps pygame -> detik.
const DURATION := 8.0 / 60.0
## Kuat tint saat memakai `modulate` (silhouette punya flash_amount sendiri).
const MODULATE_GAIN := 0.8

var _t: float = 0.0
var _prev_hp: float = 0.0
var _dirty: bool = false # ada tint yang masih perlu dibersihkan
var _extra = null        # fallback: Node2D/CanvasItem atau ShaderMaterial
## Minion & boss: pygame menyalakan flash untuk damage APA PUN, jadi tick()
## memantau hp. HERO tidak: pygame tidak punya hurt flash hero sama sekali,
## dan menyalakannya tiap pukulan berarti serangan dasar punya flash — persis
## yang dilarang kontrak tools/test_basic_attack_no_impact_fx.py. Hero memakai
## watch_hp = false, jadi flash hanya muncul lewat trigger() (skill/take_damage).
var watch_hp: bool = true


## `extra` = target cadangan kalau unit tidak punya silhouette/custom_visual
## (Hero: hit_flash_mat ShaderMaterial, Minion: Polygon2D badan, Boss: sprite).
func _init(unit = null, extra = null, p_watch_hp: bool = true) -> void:
	_extra = extra
	watch_hp = p_watch_hp
	if unit != null:
		_prev_hp = float(unit.get("hp"))


## Nyalakan flash manual (dipakai take_damage / play_hit_fx yang sudah tahu
## unit-nya kena) — sama dengan `hurt_flash_timer = 8` di pygame.
func trigger() -> void:
	_t = DURATION


## `hurt_flash_timer > 0` pygame. Dibaca renderer yang menggambar ulang tiap
## frame (BossOverlay: badan generik jadi putih, base_boss.py:6307) — tint
## modulate di bawah ini hanya untuk sprite/silhouette.
func is_active() -> bool:
	return _t > 0.0


## Dipanggil tiap frame dari _physics_process unit.
func tick(unit, delta: float) -> void:
	if unit == null or not is_instance_valid(unit):
		return
	if watch_hp:
		var hp := float(unit.get("hp"))
		if hp < _prev_hp:
			_t = DURATION # damage baru: mulai ulang, persis pygame
		_prev_hp = hp
	if _t <= 0.0:
		if _dirty:
			_apply(unit, 0.0)
			_dirty = false
		return
	_t = maxf(0.0, _t - delta)
	# Turun linear = hitung mundur 8 frame pygame (bukan tween ease).
	_apply(unit, _t / DURATION)
	_dirty = true


func _apply(unit, amount: float) -> void:
	var sil = unit.get("silhouette")
	if sil != null and is_instance_valid(sil) and "flash_amount" in sil:
		sil.flash_amount = amount
		return
	var cv = unit.get("custom_visual")
	if cv != null and is_instance_valid(cv) and cv is CanvasItem:
		_tint(cv, amount)
		return
	if _extra == null:
		return
	if _extra is ShaderMaterial:
		(_extra as ShaderMaterial).set_shader_parameter("flash_amount", amount)
	elif is_instance_valid(_extra) and _extra is CanvasItem:
		_tint(_extra, amount)


## modulate > 1 = lebih terang (HDR 2D aktif di project.godot, jadi kena bloom)
func _tint(ci: CanvasItem, amount: float) -> void:
	var g := 1.0 + MODULATE_GAIN * amount
	var a := ci.modulate.a
	ci.modulate = Color(g, g, g, a)
