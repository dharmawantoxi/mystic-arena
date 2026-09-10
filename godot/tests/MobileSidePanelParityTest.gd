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
	# Tanpa rail, pygame tidak menggambar tombol command sama sekali (pemain
	# memakai hotkey). Godot menyediakan chip TACTICAL kecil supaya HP tanpa
	# keyboard tetap bisa memerintah — TAPI kotak 220x210-nya TERLIPAT default,
	# kalau tidak map kanan-bawah tertutup dan ketukan ke unit ikut tertelan.
	tactical._refresh()
	var tac_box := tactical.find_child("TacticalBox", true, false) as Control
	var tac_toggle := tactical.find_child("TacticalToggle", true, false) as Control
	_expect(tac_toggle != null and tac_toggle.visible,
		"chip TACTICAL tampil saat tak ada rail")
	if tac_toggle != null:
		var cg: Rect2 = tac_toggle.get_global_rect()
		_expect(cg.position.x >= 0.0 and cg.position.y >= 0.0
			and cg.position.x + cg.size.x <= 1280.5
			and cg.position.y + cg.size.y <= 720.5,
			"chip TACTICAL masuk frame (got %s)" % cg)
		_expect(cg.size.x <= 200.0 and cg.size.y <= 60.0,
			"chip TACTICAL kecil, map tak tertutup (got %s)" % cg.size)
	_expect(tac_box != null and not tac_box.visible,
		"TacticalBox terlipat default di 16:9 (map bersih)")
	# Dibuka lewat chip -> kotak command muncul di kanan-bawah, di dalam frame.
	tactical.set_expanded(true)
	_expect(tac_box != null and tac_box.visible, "TacticalBox terbuka via chip")
	if tac_box != null:
		var tr: Rect2 = tac_box.get_global_rect()
		_expect(tr.position.x >= 0.0 and tr.position.y >= 0.0
			and tr.position.x + tr.size.x <= 1280.5
			and tr.position.y + tr.size.y <= 720.5,
			"tactical terbuka masuk frame (got %s)" % tr)
		_expect(tr.position.x >= 900.0 and tr.position.y >= 300.0,
			"tactical terbuka di kanan-bawah arena (got %s)" % tr.position)
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

	_step("panel hero (popup upgrade)")
	# Paritas HeroPanel pygame: panel 280x276 HANYA ada saat ada hero terpilih
	# & hidup — dulu di Godot panelnya duduk permanen di kiri-bawah arena
	# (teks "tidak ada hero dipilih") sehingga map/base Radiant tertutup dan
	# hero di sana tak bisa diketuk -> popup upgrade tak pernah muncul.
	var skill := hud.find_child("SkillBar", true, false)
	_expect(skill != null, "SkillBar ada")
	if skill == null:
		_finish()
		return
	var bar := skill.find_child("BarRoot", true, false) as Control
	_expect(bar != null, "panel hero (BarRoot) ada")
	GameManager.clear_selection()
	_expect(bar != null and not bar.visible,
		"panel hero tersembunyi tanpa hero terpilih (map bersih)")
	GameManager.gold = 1000000
	_expect(GameManager.try_buy_hero("kaizen"), "beli kaizen untuk panel hero")
	var hero = GameManager.owned_heroes()[0]
	GameManager.select_hero(hero)
	await get_tree().process_frame
	_expect(bar != null and bar.visible, "panel hero tampil setelah hero dipilih")
	if bar != null:
		var br: Rect2 = bar.get_global_rect()
		# 16:9 (tanpa rail) = fallback pygame (20, H - h - 20), tetap di frame
		# dan tombol UPGRADE (anak terakhir kolom) ikut terlihat.
		_expect(absf(br.position.x - 20.0) < 2.0
			and br.position.y + br.size.y <= 720.5
			and br.size.y >= 276.0,
			"panel hero kiri-bawah arena di 16:9 (got %s)" % br)
		# Tombol UPGRADE HERO = anak TERAKHIR kolom panel: kalau tingginya
		# kurang, tombol inilah yang dulu terdorong keluar layar.
		var upg = skill.get("_upgrade_btn")
		if upg is Control:
			var ur: Rect2 = (upg as Control).get_global_rect()
			_expect(ur.size.y > 0.0 and ur.position.y + ur.size.y <= 720.5
				and ur.position.y >= 0.0,
				"tombol UPGRADE HERO di dalam layar (got %s)" % ur)
		# Layar lebar: panel pindah KE DALAM rail (paritas panel_pos_bawah)
		# sehingga tidak menutupi arena sama sekali.
		MobileLayout.viewport_size = Vector2(1624.0, 720.0)
		MobileLayout.layout_changed.emit()
		await get_tree().process_frame
		var br_rail: Rect2 = bar.get_global_rect()
		_expect(br_rail.position.x >= 1280.0
			and br_rail.position.x + br_rail.size.x <= 1624.5
			and br_rail.position.y + br_rail.size.y <= 720.5,
			"panel hero di dalam rail saat layar lebar (got %s)" % br_rail)
		var want := MobileLayout.hero_panel_rect(280.0, br_rail.size.y)
		_expect(absf(br_rail.position.x - want.position.x) < 1.0
			and absf(br_rail.position.y - want.position.y) < 1.0,
			"panel hero == MobileLayout.hero_panel_rect (got %s want %s)"
			% [br_rail.position, want.position])
		GameManager.clear_selection()
		_expect(not bar.visible, "panel hero hilang lagi setelah deselect")
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
