# Regression test tata letak panel kanan ala pygame:
#   * layar LEBIH LEBAR dari 16:9 (1624x720 = HP 2436x1080): rail dinding
#     batu 344 px menempel di tepi arena (x=1280) berisi pause/STATUS/
#     HEROES/SHOP + TACTICAL COMMANDS di dasarnya, tidak keluar frame,
#   * z-order: rail < tactical < shop (popup toko paling atas),
#   * TOWER/CASTLE shop = popup panel kanan; HERO/ITEM = modal tengah,
#   * 16:9 PERSIS (1280x720): TANPA rail (paritas "di layar 16:9 panelnya
#     tidak ada") — arena penuh, tactical jatuh ke sudut kanan-bawah arena,
#     SEMUA tab toko memakai modal tengah,
#   * tombol tactical tak pernah hilang: yang syaratnya tak terpenuhi tampil
#     ABU tak-bisa-ditekan (paritas kotak abu _gambar_tactical pygame),
#   * layar kecil/potret kembali ke tata letak tengah (rail disembunyikan).
extends Node

const MainScene = preload("res://scenes/main.tscn")

var _failures: int = 0


func _ready() -> void:
	_run.call_deferred()


func _expect(cond: bool, message: String) -> void:
	if not cond:
		_failures += 1
		push_error("[MobileSidePanelParityTest] FAIL: %s" % message)
		print("[MobileSidePanelParityTest] FAIL: %s" % message)


## Penanda langkah: kalau harness mati di tengah (crash/timeout), ekor log
## menunjukkan langkah terakhir yang tercapai.
func _step(label: String) -> void:
	print("[MobileSidePanelParityTest] step: %s" % label)


func _run() -> void:
	_step("start")
	if MobileLayout == null:
		_expect(false, "MobileLayout autoload")
		_finish()
		return
	var main := MainScene.instantiate()
	add_child(main)
	await get_tree().process_frame
	await get_tree().process_frame
	_step("main scene siap")
	var hud := main.find_child("HUD", true, false)
	_expect(hud != null, "HUD ada")
	if hud == null:
		_finish()
		return
	var rail := hud.find_child("SidePanel", true, false)
	var tactical := hud.find_child("TacticalBar", true, false)
	var shop := hud.find_child("ShopPanel", true, false)
	_expect(rail != null, "SidePanel ada")
	_expect(tactical != null, "TacticalBar ada")
	_expect(shop != null, "ShopPanel ada")
	if rail == null or tactical == null or shop == null:
		_finish()
		return

	# Headless tidak punya jendela nyata: ukuran viewport dipatok eksplisit
	# supaya asersi deterministik di CI maupun di desktop.
	print("[MobileSidePanelParityTest] viewport headless: %s"
		% MobileLayout.viewport_size)
	# ── viewport 1: LEBAR (1624x720 = HP uji pygame 2436x1080) ──
	MobileLayout.viewport_size = Vector2(1624.0, 720.0)
	MobileLayout.layout_changed.emit()

	await get_tree().process_frame

	_step("z-order")
	# ── z-order: urutan anak HUD = urutan gambar (belakang -> depan) ──
	_expect(rail.get_index() < tactical.get_index(),
		"rail di BAWAH tactical (%d < %d)" % [rail.get_index(), tactical.get_index()])
	_expect(tactical.get_index() < shop.get_index(),
		"tactical di BAWAH shop popup")

	_step("isi rail")
	# ── isi panel kanan ──
	for child_name in ["StoneRail", "StoneBG", "RailPause", "StatusBox",
			"HeroesBox", "ShopBox", "GoldValue", "WaveLabel", "ShieldLabel",
			"ModeLabel"]:
		_expect(rail.find_child(child_name, true, false) != null,
			"rail punya %s" % child_name)
	for tab_button in ["Rail_tower", "Rail_nexus", "Rail_hero", "Rail_item"]:
		var b := rail.find_child(tab_button, true, false) as Button
		_expect(b != null, "tombol rail %s" % tab_button)
		if b != null:
			_expect(b.mouse_filter == Control.MOUSE_FILTER_STOP,
				"%s bisa diklik" % tab_button)

	_step("geometri")
	# ── geometri: semua di dalam frame & di dalam rail ──
	var vp: Vector2 = MobileLayout.viewport_size
	_expect(MobileLayout.has_side_panel(), "layar lebar punya rail")
	var rail_rect: Rect2 = MobileLayout.side_panel_rect()
	# Paritas Rect(1280, 0, 344, 720) pygame pada HP 2436x1080: menempel di
	# tepi arena (x=1280), BUKAN menutupi arena.
	_expect(rail_rect == Rect2(1280.0, 0.0, 344.0, 720.0),
		"rail @(1280,0) 344x720 (got %s)" % rail_rect)
	var tac_rect: Rect2 = MobileLayout.tactical_rect()
	_expect(tac_rect.position.x >= rail_rect.position.x
		and tac_rect.position.x + tac_rect.size.x <= rail_rect.position.x + rail_rect.size.x + 0.5,
		"tactical di dalam rail secara horizontal")
	_expect(tac_rect.position.y + tac_rect.size.y <= vp.y + 0.5,
		"tactical tidak melewati bawah layar")
	_expect(tac_rect.position.y >= MobileLayout.SHOP_TOP + MobileLayout.SHOP_HEIGHT,
		"tactical di bawah kotak shop rail")

	# Popup panel kanan & modal tengah selalu di dalam viewport.
	var popup: Rect2 = MobileLayout.rail_popup_rect()
	_expect(popup.position.x >= rail_rect.position.x - 0.5
		and popup.position.x + popup.size.x <= vp.x + 0.5, "popup rail masuk frame")
	var modal: Rect2 = MobileLayout.modal_rect()
	_expect(modal.position.x >= 0.0 and modal.position.y >= 0.0
		and modal.position.x + modal.size.x <= vp.x + 0.5
		and modal.position.y + modal.size.y <= vp.y + 0.5, "modal masuk frame")

	_step("presentasi toko")
	# ── presentasi toko: rail popup vs modal ──
	GameManager.state = "playing"
	GameManager.in_menu = false
	shop.open_tab("tower")
	await get_tree().process_frame
	var panel := shop.find_child("Panel", true, false) as Control
	_expect(panel != null, "ShopPanel punya Panel")
	if panel != null:
		var r: Rect2 = panel.get_global_rect()
		_expect(r.position.x >= rail_rect.position.x - 1.0,
			"TOWER SHOP muncul di panel kanan (x=%s)" % r.position.x)
		_expect(r.position.x + r.size.x <= vp.x + 1.0, "popup tower tidak keluar frame")
		shop.open_tab("hero")
		await get_tree().process_frame
		var r2: Rect2 = panel.get_global_rect()
		_expect(r2.position.x < rail_rect.position.x,
			"HERO SHOP memakai modal tengah (x=%s)" % r2.position.x)
		_expect(r2.size.x > rail_rect.size.x, "modal hero lebih lebar dari rail")
		_expect(r2.position.x >= 0.0 and r2.position.x + r2.size.x <= vp.x + 1.0,
			"modal hero tidak keluar frame")
		var close_btn := shop.find_child("ShopClose", true, false) as Button
		_expect(close_btn != null and close_btn.mouse_filter == Control.MOUSE_FILTER_STOP,
			"tombol tutup bisa diklik")
		if close_btn != null:
			var cr: Rect2 = close_btn.get_global_rect()
			_expect(cr.position.x + cr.size.x <= r2.position.x + r2.size.x + 1.0,
				"tombol tutup di dalam panel")
	GameManager.close_shop()

	_step("16:9 tanpa rail")
	# ── 16:9 PERSIS: panel TIDAK ADA (paritas pygame), arena penuh ──
	MobileLayout.viewport_size = Vector2(1280.0, 720.0)
	MobileLayout.layout_changed.emit()
	await get_tree().process_frame
	_expect(not MobileLayout.has_side_panel(), "16:9 tanpa rail")
	_expect(MobileLayout.side_panel_width() == 0.0, "lebar rail 0 di 16:9")
	_expect(MobileLayout.content_width() == 1280.0, "arena 1280 penuh di 16:9")
	var stone := rail.find_child("StoneRail", true, false) as Control
	_expect(stone != null and not stone.visible, "StoneRail disembunyikan di 16:9")

	_step("tactical fallback 16:9")
	# Tactical jatuh ke sudut kanan-bawah ARENA (tetap terlihat + di frame).
	tactical._refresh()
	var tac_box := tactical.find_child("TacticalBox", true, false) as Control
	_expect(tac_box != null and tac_box.visible, "TacticalBox terlihat di 16:9")
	if tac_box != null:
		var tr: Rect2 = tac_box.get_global_rect()
		_expect(tr.position.x >= 0.0 and tr.position.y >= 0.0
			and tr.position.x + tr.size.x <= 1280.5
			and tr.position.y + tr.size.y <= 720.5,
			"tactical fallback masuk frame (got %s)" % tr)
		_expect(tr.position.x >= 900.0 and tr.position.y >= 300.0,
			"tactical fallback di kanan-bawah arena (got %s)" % tr.position)
	# Roster kosong (tanpa hero/boss): kelima tombol tampil ABU (tak hilang)
	# dan tak-bisa-ditekan — paritas kotak abu _gambar_tactical pygame.
	var avail: Dictionary = tactical.panel_available()
	for action in ["gather", "protect_tower", "protect_castle", "attack_boss",
			"attack_damage_dealer"]:
		var cb := tactical.find_child("Cmd_" + action, true, false) as Button
		_expect(cb != null, "tombol Cmd_%s ada" % action)
		if cb == null:
			continue
		_expect(cb.visible, "Cmd_%s tampil (abu, bukan hilang)" % action)
		_expect(cb.disabled, "Cmd_%s disabled tanpa syarat" % action)
		_expect(cb.mouse_filter == Control.MOUSE_FILTER_IGNORE,
			"Cmd_%s tak menelan klik saat abu" % action)
		_expect(not bool(avail.get(action, true)),
			"panel_available[%s] == false" % action)

	_step("toko modal 16:9")
	# Tanpa rail, SEMUA tab (termasuk tower) memakai modal tengah.
	shop.open_tab("tower")
	await get_tree().process_frame
	if panel != null:
		var rm: Rect2 = panel.get_global_rect()
		_expect(absf(rm.position.x - 190.0) < 2.0
			and absf(rm.size.x - 900.0) < 2.0
			and absf(rm.size.y - 560.0) < 2.0,
			"TOWER SHOP modal tengah 900x560 @(190,80) di 16:9 (got %s)" % rm)
	GameManager.close_shop()

	_step("fallback potret")
	# ── layar kecil / potret: rail hilang, tata letak tengah dipakai ──
	MobileLayout.viewport_size = Vector2(720.0, 1280.0)
	MobileLayout.layout_changed.emit()
	await get_tree().process_frame
	_expect(not MobileLayout.has_side_panel(), "potret tanpa rail")
	_expect(MobileLayout.side_panel_width() == 0.0, "lebar rail 0 di potret")
	_expect(MobileLayout.content_width() == 720.0, "arena memakai lebar penuh")
	var modal_p: Rect2 = MobileLayout.modal_rect()
	_expect(modal_p.position.x >= 0.0
		and modal_p.position.x + modal_p.size.x <= 720.5, "modal potret masuk frame")
	MobileLayout.viewport_size = Vector2(1280.0, 720.0)
	MobileLayout.layout_changed.emit()
	await get_tree().process_frame

	_finish()


func _finish() -> void:
	if _failures == 0:
		print("[MobileSidePanelParityTest] PASS")
		get_tree().quit(0)
	else:
		push_error("MobileSidePanelParityTest failures: %d" % _failures)
		get_tree().quit(1)
