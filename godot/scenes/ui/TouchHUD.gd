# TouchHUD.gd — HUD sentuh (port mobile/hud.py TouchHUD 1:1).
#
# Tombol layar pengganti keyboard: PAUSE (II) + FPS di kiri atas bawah
# panel gold, REPLAY / NEXT LEVEL / MENU setelah match usai, BACK di menu.
# Tombol SKIP sengaja DIMATIKAN di gerbang visibilitas (_sync_visibility)
# — cinematic tetap bisa dilewati lewat tap di mana saja / SPACE/ENTER.
# Geometri & visibilitas = kanon HudLayout (TOUCH_BUTTONS /
# TOUCH_VISIBILITY) yang dikunci UiHudParityTest.
#
# Aksi diteruskan sebagai signal `hud_action(action)`; Main.gd
# menerjemahkannya lewat _apply_touch_action (paritas apply_hud_action):
# pause, debug, skip, replay, next_level, menu, back.
#
# INPUT — hanya InputEventMouseButton. Di perangkat, sentuhan tiba sebagai
# mouse lewat emulate_mouse_from_touch (project.godot, eksplisit true);
# menangani InputEventScreenTouch juga = aksi GANDA (toggle debug 2x =
# no-op, back = 2x ESC). Di desktop, mouse fisik memakai jalur yang sama —
# paritas hit_test pygame yang juga dipakai klik mouse.
#
# SYNC — pygame memanggil hud.sync tiap frame dari main.py; di sini
# sync_from_match() dipanggil tiap _process (ditulis ulang hanya kalau
# kunci state / panel / menu berubah, supaya tidak redraw sia-sia).
extends Control
class_name TouchHUD

signal hud_action(action: String)

const BG := Color(16.0 / 255.0, 14.0 / 255.0, 22.0 / 255.0, 205.0 / 255.0)
const BG_ACTIVE := Color(60.0 / 255.0, 48.0 / 255.0, 20.0 / 255.0,
	235.0 / 255.0)
const BTN_WHITE := Color("#ebebf5")
const BTN_GREY := Color("#787887")
const BTN_GOLD := Color("#ffc846")
const BTN_GOLD_DIM := Color("#967628")
## Bentuk & ukuran font per tombol (mobile/hud.py _build_layout).
## Geometri + label = kanon HudLayout.TOUCH_BUTTONS (sumber tunggal,
## anti-drift dari data yang dikunci UiHudParityTest).
const BTN_SHAPE := {
	"pause": "round", "debug": "round", "skip": "capsule",
	"replay": "capsule", "next_level": "capsule", "menu": "capsule",
	"back": "capsule",
}
const BTN_FONT_SIZE := {
	"pause": 22, "debug": 16, "skip": 20, "replay": 20,
	"next_level": 18, "menu": 22, "back": 20,
}

var _buttons: Dictionary = {}
var _state_key: String = "menu"
## Paritas main.py:180 — tombol FPS mati default, nyala hanya dengan
## MYSTIC_DEBUG=1 (di kedua engine tombolnya tak ada di rilis).
var show_debug_button: bool = false
## Stempel sync terakhir (kunci|panel|debug) — cegah tulis ulang tiap frame.
var _last_sync: String = ""
## WATCHDOG cinematic: PAUSE hanya boleh sembunyi selama cinematic sungguhan
## aktif — intro level (pause tree), banner boss ±1,7 dtk, perayaan kematian
## ±2 dtk. Kalau sesuatu mengklaim "cinematic aktif" lebih lama dari ini
## TANPA memegang pause, klaimnya basi (node nyangkut / flag tak pernah
## dilepas) dan HUD terkunci di matriks game_playing_cine: PAUSE tak pernah
## kembali. Di situ klaimnya diputus supaya tombol normal lagi —
## self-healing, bukan menebak node mana yang nyangkut. (Tombol SKIP sudah
## dimatikan permanen di _sync_visibility, jadi watchdog ini khusus PAUSE.)
##
## LATCH + COOLDOWN (keluhan "SKIP menempel selama wave"): memutus sekali
## saja tidak cukup kalau node yang sama terus mengklaim tiap frame — watchdog
## lama menghitung ulang dari nol, membiarkan PAUSE hilang selama 10 detik,
## lalu memutus lagi, dan seterusnya. Sekarang klaim basi di-LATCH (tetap
## diputus) sampai klaim itu benar-benar hilang selama CINE_COOLDOWN_SEC, dan
## sehabis memutus watchdog tidak mempersenjatai diri lagi selama
## CINE_COOLDOWN_SEC (anti-chatter). Latch 6 detik: lebih panjang dari
## cinematic sungguhan mana pun yang tidak memegang pause (banner boss 1,7
## dtk, perayaan 2 dtk), tapi cukup pendek supaya gelombang pertama yang
## terkena tidak menunggu lama.
const CINE_WATCHDOG_SEC := 6.0
const CINE_COOLDOWN_SEC := 2.0
var _cine_watch := 0.0
var _cine_stuck := false
## Sisa waktu sebelum watchdog boleh mempersenjatai diri lagi.
var _cine_cool := 0.0
## Sudah berapa lama TIDAK ada klaim cinematic (pelepas latch).
var _cine_absent := 0.0


func _ready() -> void:
	name = "TouchHUD"
	add_to_group("touch_hud")
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	MobileLayout.fill_parent(self)
	show_debug_button = OS.has_environment("MYSTIC_DEBUG") \
		and OS.get_environment("MYSTIC_DEBUG") == "1"
	_build_layout()
	# TouchHUD digambar manual (satu _draw) — bukan kumpulan Button,
	# supaya glow + cincin ganda + capsule highlight identik pygame.
	var view := _TouchView.new(self)
	MobileLayout.fill_parent(view)
	view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(view)
	sync_from_match()


func _build_layout() -> void:
	# Geometri + label persis HudLayout.TOUCH_BUTTONS (kanon fixture
	# touchhud — urutan iterasi = urutan pygame: pause s/d back, sehingga
	# prioritas hit_test terbalik juga sama).
	_buttons.clear()
	var colors := {
		"pause": BTN_GOLD, "debug": Color("#78c8ff"), "skip": BTN_GOLD,
		"replay": BTN_GOLD, "next_level": Color("#78e68c"),
		"menu": BTN_GOLD, "back": BTN_GOLD,
	}
	for action in HudLayout.TOUCH_BUTTONS:
		var spec: Dictionary = HudLayout.TOUCH_BUTTONS[action]
		var r: Array = spec.get("rect", [0, 0, 0, 0])
		var col: Color = colors.get(str(action), BTN_GOLD)
		_add_button(str(action),
			Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])),
			str(spec.get("label", "?")),
			str(BTN_SHAPE.get(str(action), "capsule")), col,
			int(BTN_FONT_SIZE.get(str(action), 20)))


func _add_button(action: String, rect: Rect2, label: String, shape: String,
		color: Color, font_size: int) -> void:
	# Area sentuh diperlonggar (paritas inflate 24 + MIN_TAP 80).
	var hit := rect.grow(12.0)
	if hit.size.x < 80.0 or hit.size.y < 80.0:
		hit = rect.grow_individual(
			maxf(0.0, (80.0 - rect.size.x) * 0.5), maxf(0.0,
				(80.0 - rect.size.y) * 0.5),
			maxf(0.0, (80.0 - rect.size.x) * 0.5),
			maxf(0.0, (80.0 - rect.size.y) * 0.5))
	_buttons[action] = {"rect": rect, "hit": hit, "label": label,
		"shape": shape, "color": color, "font_size": font_size,
		"visible": false, "enabled": true, "press_anim": 0.0}


## Kunci visibilitas dari state (paritas TouchHUD.sync + matriks fixture).
func set_state_key(state_key: String) -> void:
	_state_key = state_key
	_sync_visibility()
	queue_redraw()


## Port TouchHUD.sync per frame (main.py:399): node hanya tampil DI DALAM
## match — pygame menggambar hud HANYA di STATE_GAME (cabang menu/pause/
## splash main.py tidak memanggil hud.draw sama sekali). Tombol mengikuti
## matriks TOUCH_VISIBILITY berdasar state + cinematic + level.
func sync_from_match(delta: float = 0.0) -> void:
	var menu_open := false
	var menu = get_tree().get_first_node_in_group("main_menu")
	if menu != null and menu.has_method("is_open"):
		menu_open = bool(menu.call("is_open"))
	var in_game := not GameManager.in_menu and not menu_open
	if visible != in_game:
		visible = in_game
	if not in_game:
		_last_sync = "hidden"
		_cine_watch = 0.0
		_cine_stuck = false
		_cine_cool = 0.0
		_cine_absent = 0.0
		return
	var key := "menu"
	var cine := _cinematic_active()
	# Watchdog: cinematic sungguhan yang TIDAK membekukan tree cuma banner
	# boss (±1,7 dtk) dan perayaan kematian (±2 dtk). Klaim aktif berdetak
	# tanpa pause = flag nyangkut -> putuskan + latch supaya PAUSE kembali
	# (lihat CINE_WATCHDOG_SEC / CINE_COOLDOWN_SEC).
	if not cine:
		# Klaim hilang. Latch baru benar-benar lepas setelah tidak ada klaim
		# selama cooldown — klaim yang berkedip tiap frame tidak boleh
		# menghidupkan mode cine lagi (PAUSE tersembunyi) di sela kedipannya.
		_cine_absent += delta
		_cine_watch = 0.0
		if _cine_absent >= CINE_COOLDOWN_SEC:
			_cine_stuck = false
			_cine_cool = 0.0
	elif _cine_stuck:
		# LATCH: klaim basi tetap diputus walau node-nya masih mengaku aktif.
		cine = false
		_cine_cool = maxf(0.0, _cine_cool - delta)
	elif GameManager.state == "playing" and not get_tree().paused:
		_cine_absent = 0.0
		_cine_cool = maxf(0.0, _cine_cool - delta)
		if _cine_cool <= 0.0:
			_cine_watch += delta
			if _cine_watch > CINE_WATCHDOG_SEC:
				_cine_stuck = true
				_cine_cool = CINE_COOLDOWN_SEC
				cine = false
				push_warning(("[TouchHUD] cinematic mengklaim aktif > %.0f dtk "
					+ "tanpa pause — klaim diputus + dilatch %.0f dtk supaya "
					+ "PAUSE normal") % [CINE_WATCHDOG_SEC,
						CINE_COOLDOWN_SEC])
	else:
		_cine_watch = 0.0
		_cine_absent = 0.0
	match GameManager.state:
		"playing":
			key = "game_playing_cine" if cine else "game_playing"
		"victory":
			# next_level tampil hanya kalau ada level berikut (paritas
			# cabang get_next_level hud.py sync).
			key = "game_victory_L1" if GameManager.next_level_number() > 0 \
				else "game_victory_L54"
		"defeat":
			key = "game_defeat"
	var panel := MobileLayout.has_side_panel()
	var stamp := "%s|%d|%d" % [key, int(panel), int(show_debug_button)]
	if stamp == _last_sync:
		return
	_last_sync = stamp
	_state_key = key
	_sync_visibility()
	if panel:
		# Paritas _panel_ada (hud.py sync): pause pindah ke rail, tombol
		# FPS DIHAPUS dari rail pygame (sidepanel.py:125-128) = sembunyi.
		# Rail Godot (SidePanel RailPause) sudah menampung pause.
		var pause_btn: Dictionary = _buttons["pause"]
		pause_btn["visible"] = false
		var debug_btn: Dictionary = _buttons["debug"]
		debug_btn["visible"] = false
	queue_redraw()


## Cine aktif = intro level / banner boss / perayaan kematian (paritas
## _cinematic_active main.py — fase kematian boss BUKAN cine, jadi pause
## tetap tampil di sana seperti pygame).
func _cinematic_active() -> bool:
	var main = get_tree().get_first_node_in_group("main")
	if main == null or not main.has_method("_cinematic_active"):
		return false
	return bool(main.call("_cinematic_active"))


func _sync_visibility() -> void:
	var vis: Dictionary = HudLayout.touch_visibility(_state_key)
	for action in _buttons:
		var d: Dictionary = _buttons[action]
		d["visible"] = bool(vis.get(action, false))
	# Tombol debug bisa disembunyikan permanen (paritas show_debug_button).
	if not show_debug_button and _buttons.has("debug"):
		(_buttons["debug"] as Dictionary)["visible"] = false
	# ── SKIP DIHAPUS DARI RENDER (keluhan pemain berulang 3x) ──
	# Satu-satunya gerbang visibilitas ada di sini: matriks
	# `game_playing_cine`, `set_state_key` manual, override panel rail,
	# maupun watchdog semuanya berakhir lewat fungsi ini. Mematikan skip di
	# sini berarti tombolnya TIDAK PERNAH tergambar lewat jalur apa pun.
	# DEVIASI SADAR dari oracle: HudLayout.TOUCH_BUTTONS / TOUCH_VISIBILITY
	# sengaja DIBIARKAN utuh (fixture touchhud + UiHudParityTest tetap
	# hijau); yang dipotong hanya jalur render. Cinematic tetap bisa
	# dilewati: tap di mana saja (Main._cinematic_click) atau SPACE/ENTER.
	(_buttons["skip"] as Dictionary)["visible"] = false


func _process(delta: float) -> void:
	sync_from_match(delta)
	var dirty := false
	for action in _buttons:
		var d: Dictionary = _buttons[action]
		if float(d["press_anim"]) > 0.0:
			d["press_anim"] = maxf(0.0,
				float(d["press_anim"]) - delta * 7.2)
			dirty = true
	if dirty:
		queue_redraw()


func _gui_input(event: InputEvent) -> void:
	# Root IGNORE — input ditangani di _input global (di bawah).
	pass


func _input(event: InputEvent) -> void:
	if not visible:
		return
	# Mouse SAJA (lihat catatan INPUT di header): sentuhan perangkat
	# sudah tiba sebagai mouse via emulate_mouse_from_touch.
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			_tap_at(get_global_mouse_position())


func _tap_at(logical_pos: Vector2) -> void:
	# Urutan terbalik (tombol terakhir = paling atas) — paritas hit_test.
	var keys := _buttons.keys()
	keys.reverse()
	for action in keys:
		var d: Dictionary = _buttons[action]
		if not bool(d["visible"]):
			continue
		if (d["hit"] as Rect2).has_point(logical_pos):
			d["press_anim"] = 1.0
			queue_redraw()
			hud_action.emit(str(action))
			get_viewport().set_input_as_handled()
			return


## Paritas `TouchButton.contains` (hud.py:73-74): `visible and
## hit_rect.collidepoint(pos)` — sisi kanan/bawah TIDAK termasuk (semantik
## Rect pygame; `Rect2.has_point` Godot sudah setengah-terbuka). Dipakai
## Main untuk cabang "TAHAN tombol jeda = overlay debug" (main.py:407-413).
func contains_button(action: String, pos: Vector2) -> bool:
	if not _buttons.has(action):
		return false
	var d: Dictionary = _buttons[action]
	return bool(d["visible"]) and (d["hit"] as Rect2).has_point(pos)


func is_visible_button(action: String) -> bool:
	if not _buttons.has(action):
		return false
	return bool((_buttons[action] as Dictionary)["visible"])


# ── View (gambar manual 1:1 pygame) ──

class _TouchView extends Control:
	var hud: TouchHUD

	func _init(h: TouchHUD) -> void:
		hud = h
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		if hud == null or size.x <= 0.0:
			return
		# Gambar 1:1 koordinat logis — stretch canvas_items engine yang
		# memetakan ke piksel fisik. JANGAN diskala manual size/1280:
		# dengan aspect expand, size adalah ukuran logis yang MELAR
		# (1624x720 di HP 18:9) sehingga skala manual menggelembungkan
		# + menggeser tombol keluar geometri kanon (dan hit-test).
		for action in hud._buttons:
			var d: Dictionary = hud._buttons[action]
			if not bool(d["visible"]):
				continue
			if str(d["shape"]) == "round":
				_draw_round(d)
			else:
				_draw_capsule(d)

	func _draw_round(d: Dictionary) -> void:
		var rect: Rect2 = d["rect"]
		var c := rect.get_center()
		var r := rect.size.x * 0.5
		var col: Color = d["color"]
		var ring := col if bool(d["enabled"]) else TouchHUD.BTN_GREY
		var press := int(float(d["press_anim"]) * 3.0)
		# Glow lembut di belakang tombol.
		UiTheme.draw_glow(self, Rect2(c.x - r - 22, c.y - r - 22,
			r * 2 + 44, r * 2 + 44), col, 46.0 / 255.0, 8)
		var base := TouchHUD.BG_ACTIVE if float(d["press_anim"]) > 0.0 \
			else TouchHUD.BG
		draw_circle(c, r, base)
		draw_arc(c, r, 0, TAU, 40, ring, 3.0)
		# Cincin dalam halus (identitas premium).
		draw_arc(c, r - 6.0, 0, TAU, 36, Color.WHITE, 1.0)
		var font := UiTheme.body_bold()
		var txt_col := TouchHUD.BTN_WHITE if bool(d["enabled"]) \
			else Color("#aaaab4")
		UiTheme.draw_text_centered(self, font, str(d["label"]),
			int(d["font_size"]) + press, txt_col, c + Vector2(0, -2),
			false)

	func _draw_capsule(d: Dictionary) -> void:
		var rect: Rect2 = d["rect"]
		var radius := rect.size.y * 0.5
		var col: Color = d["color"]
		var ring := col if bool(d["enabled"]) else TouchHUD.BTN_GREY
		UiTheme.draw_glow(self, rect.grow_individual(18, 14, 18, 14), col,
			40.0 / 255.0, 8)
		var base := TouchHUD.BG_ACTIVE if float(d["press_anim"]) > 0.0 \
			else TouchHUD.BG
		UiTheme.draw_rr(self, rect, base, radius)
		UiTheme.draw_rr_outline(self, rect, ring, radius, 2.0)
		# Sorot tepi atas (kedalaman).
		draw_line(Vector2(rect.position.x + rect.size.x * 0.25,
			rect.position.y + 2),
			Vector2(rect.position.x + rect.size.x * 0.75,
			rect.position.y + 2), Color.WHITE, 1.0)
		var font := UiTheme.body_bold()
		var txt_col := TouchHUD.BTN_WHITE if bool(d["enabled"]) \
			else Color("#aaaab4")
		UiTheme.draw_text_centered(self, font, str(d["label"]),
			int(d["font_size"]), txt_col, rect.get_center(), false)
