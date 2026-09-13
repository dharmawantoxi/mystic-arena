# Regression test 2026-09-14 — "victory/defeat & pop up top up di luar frame".
#
# Kasusnya: kamera arena dikunci limit 0..1280 x 0..720 (Main._frame_camera),
# jadi di jendela desktop yang lebih tinggi/lebar dari 16:9 sudut kiri-atas
# viewport = world (0,0) dan pusat VIEWPORT ada DI LUAR peta. Elemen ber-anchor
# 0.5 (overlay VICTORY/DEFEAT + dialog TOP UP) karena itu tampak melayang di
# area panel kanan / tepi kosong, padahal pygame menggambar semuanya ke surface
# 1280x720 sehingga selalu di tengah arena.
#
# Yang dikunci di sini:
#   1. aritmetika frame arena MobileLayout (frame_rect/center/center_offset/
#      visible_rect/fit_scale) untuk 16:9, jendela lebih lebar (HP 1624x720),
#      jendela lebih tinggi (16:10 1866x1050), dan jendela LEBIH KECIL
#      (1000x600 -> arena terpotong rata tengah, pusat frame = pusat viewport),
#   2. GameOverOverlay: SEMUA elemen (panel stat, popup unlock, baris keycap,
#      achievement, baris tombol aksi) terpusat di frame arena dan tidak
#      keluar frame — bukan pusat viewport,
#   3. lapisan gelap menutup frame ARENA saja (paritas pygame: panel kanan
#      tidak pernah digelapkan),
#   4. tata ulang saat ukuran jendela berubah SELAGI layar hasil tampil,
#   5. TopupDialog: panel 920x580 terpusat di frame arena + diskalakan supaya
#      selalu muat di bagian frame yang terlihat.
#
# Cara mensimulasikan ukuran jendela di headless: satu Control pembungkus
# berukuran tetap (parent anchor-0.5 memakai ukuran PARENT) + MobileLayout.
# viewport_size disamakan. Jadi angka yang diuji benar-benar angka yang dipakai
# produksi (MobileLayout), bukan salinan rumus.
extends Node

const GameOverOverlayScript = preload("res://scenes/ui/GameOverOverlay.gd")
const TopupDialogScript = preload("res://scenes/ui/TopupDialog.gd")

## Toleransi 1 px: offset Control dibulatkan engine ke bilangan bulat.
const EPS := 1.0

var _failures: int = 0


func _ready() -> void:
	_run.call_deferred()


func _expect(cond: bool, message: String) -> void:
	if not cond:
		_failures += 1
		push_error("[ArenaFrameLayoutTest] FAIL: %s" % message)
		print("[ArenaFrameLayoutTest] FAIL: %s" % message)


func _step(label: String) -> void:
	print("[ArenaFrameLayoutTest] step: %s" % label)


## Dua frame: perubahan ukuran Control diproses di akhir frame (layout
## di-defer), jadi satu frame belum cukup untuk mengukur rect final.
func _settle() -> void:
	await get_tree().process_frame
	await get_tree().process_frame


func _approx(a: float, b: float) -> bool:
	return absf(a - b) <= EPS


func _finish() -> void:
	# Kembalikan ukuran viewport simulasi supaya scene uji lain (bila
	# dijalankan di proses yang sama) tidak mewarisi angka palsu.
	MobileLayout.viewport_size = MobileLayout.DESIGN_SIZE
	MobileLayout.layout_changed.emit()
	if _failures == 0:
		print("[ArenaFrameLayoutTest] PASS")
		get_tree().quit(0)
	else:
		push_error("ArenaFrameLayoutTest failures: %d" % _failures)
		print("[ArenaFrameLayoutTest] SELESAI dengan %d kegagalan" % _failures)
		get_tree().quit(1)


## Ganti ukuran jendela yang disimulasikan: MobileLayout + rect pembungkus +
## rect widget.
##
## Rect widget DIPATOK eksplisit (anchor tetap + offset), TIDAK bergantung
## pada ukuran pembungkus: di production overlay/dialog ini full-rect di dalam
## HUD/MainMenu yang berukuran jendela, jadi rect-nya = ukuran jendela. Kalau
## mengandalkan container/pembungkus saja, Control bisa tetap 0x0 di headless
## (terbukti di CI: seluruh elemen lalu menempel di offset mentah) sehingga
## yang diukur bukan rumus produksi. Ukurannya diperiksa di test masing-masing.
func _simulate(sim: Vector2, holder: Control, widget: Control) -> void:
	MobileLayout.viewport_size = sim
	_pin_rect(holder, sim)
	_pin_rect(widget, sim)
	MobileLayout.layout_changed.emit()


## Rect Control = (0,0,sim) lewat anchor tetap + offset eksplisit (bukan
## `size =`, yang bisa ditimpa parent/container).
func _pin_rect(c: Control, sim: Vector2) -> void:
	c.set_anchors_preset(Control.PRESET_TOP_LEFT)
	c.offset_left = 0.0
	c.offset_top = 0.0
	c.offset_right = sim.x
	c.offset_bottom = sim.y


func _run() -> void:
	_step("start")
	if MobileLayout == null:
		_expect(false, "autoload MobileLayout ada")
		_finish()
		return

	_step("aritmetika frame arena")
	_test_frame_math()

	_step("overlay VICTORY/DEFEAT")
	await _test_game_over_overlay()

	_step("dialog TOP UP")
	await _test_topup_dialog()

	_finish()


# ══════════════════════════════════════════════════════════
#  1. ARITMETIKA FRAME ARENA
# ══════════════════════════════════════════════════════════

func _test_frame_math() -> void:
	# 16:9 persis: frame = seluruh viewport, offset nol.
	MobileLayout.viewport_size = Vector2(1280.0, 720.0)
	_expect(MobileLayout.arena_frame_rect() == Rect2(0.0, 0.0, 1280.0, 720.0),
		"16:9: frame = (0,0,1280,720) (got %s)" % MobileLayout.arena_frame_rect())
	_expect(MobileLayout.arena_center() == Vector2(640.0, 360.0),
		"16:9: pusat frame (640,360)")
	_expect(MobileLayout.arena_center_offset() == Vector2.ZERO,
		"16:9: offset pusat = nol (jendela & frame sama)")

	# HP landscape 2436x1080 -> viewport 1624x720 (rail 344 px): arena menempel
	# di kiri, pusat frame TETAP 640 walau pusat viewport 812.
	MobileLayout.viewport_size = Vector2(1624.0, 720.0)
	_expect(MobileLayout.arena_center() == Vector2(640.0, 360.0),
		"1624x720: pusat frame tetap (640,360) (got %s)"
			% MobileLayout.arena_center())
	_expect(MobileLayout.arena_center_offset() == Vector2(-172.0, 0.0),
		"1624x720: offset pusat frame - pusat viewport = -172 px")
	_expect(MobileLayout.arena_visible_rect() == Rect2(0.0, 0.0, 1280.0, 720.0),
		"1624x720: frame terlihat penuh 1280x720")

	# Desktop 16:10: viewport 1866x1050 -> sisa 586 px di kanan dan 330 px di
	# bawah, SEMUANYA di luar peta.
	MobileLayout.viewport_size = Vector2(1866.0, 1050.0)
	_expect(MobileLayout.arena_center() == Vector2(640.0, 360.0),
		"1866x1050: pusat frame (640,360), bukan pusat viewport (933,525)")
	_expect(MobileLayout.arena_center_offset() == Vector2(-293.0, -165.0),
		"1866x1050: offset pusat = (-293,-165) (got %s)"
			% MobileLayout.arena_center_offset())
	_expect(MobileLayout.arena_visible_rect() == Rect2(0.0, 0.0, 1280.0, 720.0),
		"1866x1050: frame terlihat penuh")

	# Jendela LEBIH KECIL dari frame: kamera terpotong rata tengah, jadi pusat
	# frame = pusat viewport (arena melewati tepi layar di kedua sisi).
	MobileLayout.viewport_size = Vector2(1000.0, 600.0)
	_expect(MobileLayout.arena_center() == Vector2(500.0, 300.0),
		"1000x600: pusat frame = pusat viewport (got %s)"
			% MobileLayout.arena_center())
	_expect(MobileLayout.arena_frame_rect() == Rect2(-140.0, -60.0, 1280.0, 720.0),
		"1000x600: frame melewati tepi layar (got %s)"
			% MobileLayout.arena_frame_rect())
	_expect(MobileLayout.arena_visible_rect() == Rect2(0.0, 0.0, 1000.0, 600.0),
		"1000x600: frame terlihat = seluruh viewport")
	var s_small := MobileLayout.arena_fit_scale(Vector2(920.0, 580.0), 24.0)
	_expect(s_small < 1.0 and s_small > 0.5,
		"1000x600: dialog 920x580 mengecil (skala %.3f)" % s_small)
	_expect(920.0 * s_small <= 1000.0 - 24.0 + EPS
		and 580.0 * s_small <= 600.0 - 24.0 + EPS,
		"1000x600: dialog muat setelah diskalakan")

	# Di 1280x720 skala = 1 (persis desain pygame).
	MobileLayout.viewport_size = Vector2(1280.0, 720.0)
	_expect(MobileLayout.arena_fit_scale(Vector2(920.0, 580.0), 24.0) == 1.0,
		"1280x720: skala fit = 1 (tanpa distorsi)")


# ══════════════════════════════════════════════════════════
#  2. OVERLAY VICTORY / DEFEAT
# ══════════════════════════════════════════════════════════

func _test_game_over_overlay() -> void:
	for sim in [Vector2(1280.0, 720.0), Vector2(1624.0, 720.0),
			Vector2(1866.0, 1050.0), Vector2(1000.0, 600.0)]:
		var tag := "overlay @%dx%d" % [int(sim.x), int(sim.y)]
		var holder := Control.new()
		holder.name = "Holder"
		add_child(holder)
		MobileLayout.viewport_size = sim
		MobileLayout.layout_changed.emit()
		var overlay: GameOverOverlay = GameOverOverlayScript.new()
		overlay.name = "GameOverOverlay"
		holder.add_child(overlay)
		_simulate(sim, holder, overlay)
		await get_tree().process_frame
		_expect(_approx(overlay.size.x, sim.x) and _approx(overlay.size.y, sim.y),
			"%s: overlay berukuran jendela %s (got %s)"
				% [tag, sim, overlay.size])
		overlay.show_result(true)
		await _settle()
		_expect_overlay_inside_frame(overlay, sim)
		# Langkah 4: jendela diubah SELAGI layar hasil tampil.
		var resized := Vector2(maxf(1280.0, sim.x - 100.0),
			maxf(720.0, sim.y - 100.0))
		_simulate(resized, holder, overlay)
		await _settle()
		_expect_overlay_inside_frame(overlay, resized)
		holder.queue_free()
		await get_tree().process_frame


func _expect_overlay_inside_frame(overlay: GameOverOverlay, sim: Vector2) -> void:
	var frame := MobileLayout.arena_frame_rect()
	var center := MobileLayout.arena_center()
	var tag := "overlay @%dx%d" % [int(sim.x), int(sim.y)]

	# Panel statistik: terpusat horizontal di pusat frame, tepi atas = pusat
	# frame - 100 px (paritas pygame `cy - 100`). Ukurannya pasti (500 x h),
	# jadi posisinya bisa dikunci sampai 1 px.
	var panel := overlay.find_child("GameOverPanel", true, false) as Control
	_expect(panel != null, "%s: panel statistik ada" % tag)
	if panel != null:
		var r: Rect2 = panel.get_global_rect()
		_expect(_approx(r.get_center().x, center.x),
			"%s: panel statistik terpusat di frame (x=%.1f, seharusnya %.1f)"
				% [tag, r.get_center().x, center.x])
		# Toleransi 2 px: offset Control dibulatkan engine dan tinggi baris
		# ditentukan metrik font, bukan cuma angka desain.
		_expect(absf(r.position.y - (center.y - 100.0)) <= 2.0,
			"%s: tepi atas panel statistik = pusat frame - 100 (y=%.1f, panel %s)"
				% [tag, r.position.y, r.size])
		_expect(_contains(frame, r),
			"%s: panel statistik masuk frame (got %s)" % [tag, r])
		# Bukti bug lama: dulu panel ini terpusat di VIEWPORT. Di jendela
		# lebih lebar dari frame, dua titik itu berbeda — kalau sama, test
		# tidak membuktikan apa-apa.
		if sim.x > 1280.0:
			_expect(not _approx(r.get_center().x, sim.x * 0.5),
				"%s: panel TIDAK di pusat viewport (%.1f vs %.1f)"
					% [tag, r.get_center().x, sim.x * 0.5])

	# Semua blok overlay lain (judul, keycap, achievement, tombol aksi,
	# popup unlock): pusatnya = pusat frame + offset desainnya, dan seluruh
	# rect-nya di dalam frame. Toleransi vertikal lebih longgar karena tinggi
	# baris ditentukan minimum-size tombolnya (bisa tumbuh 1-2 px).
	var checked := 0
	for e in overlay._centered:
		var c := e[0] as Control
		if not is_instance_valid(c) or c.is_queued_for_deletion():
			continue
		checked += 1
		var r: Rect2 = c.get_global_rect()
		var want := center + (e[1] as Vector2)
		_expect(_contains(frame, r),
			"%s: %s masuk frame (got %s)" % [tag, c.name, r])
		_expect(absf(r.get_center().x - want.x) <= 2.0,
			"%s: %s terpusat di frame (x=%.1f, harap %.1f)"
				% [tag, c.name, r.get_center().x, want.x])
		_expect(absf(r.get_center().y - want.y) <= 12.0,
			"%s: %s di barisnya (y=%.1f, harap %.1f)"
				% [tag, c.name, r.get_center().y, want.y])
	_expect(checked >= 5, "%s: minimal 5 blok overlay diperiksa (got %d)"
		% [tag, checked])

	# Paritas pygame: yang digelapkan hanya surface arena 1280x720 — panel
	# kanan/tepi kosong di luar peta tidak ikut gelap.
	var dim := overlay.find_child("Dim", true, false) as Control
	_expect(dim != null, "%s: lapisan gelap ada" % tag)
	if dim != null:
		var dr: Rect2 = dim.get_global_rect()
		_expect(_contains(frame, dr) and _contains(dr, frame),
			"%s: lapisan gelap TEPAT frame arena (got %s)" % [tag, dr])
		_expect(_approx(dr.size.y, 720.0) and _approx(dr.size.x, 1280.0),
			"%s: lapisan gelap 1280x720 (got %s)" % [tag, dr.size])


# ══════════════════════════════════════════════════════════
#  3. DIALOG TOP UP
# ══════════════════════════════════════════════════════════

func _test_topup_dialog() -> void:
	for sim in [Vector2(1280.0, 720.0), Vector2(1624.0, 720.0),
			Vector2(1866.0, 1050.0), Vector2(1000.0, 600.0),
			Vector2(800.0, 500.0)]:
		var holder := Control.new()
		holder.name = "Holder"
		add_child(holder)
		MobileLayout.viewport_size = sim
		MobileLayout.layout_changed.emit()
		var dlg: TopupDialog = TopupDialogScript.new()
		dlg.name = "TopupDialog"
		holder.add_child(dlg)
		_simulate(sim, holder, dlg)
		await _settle()
		var tag := "topup @%dx%d" % [int(sim.x), int(sim.y)]
		_expect(_approx(dlg.size.x, sim.x) and _approx(dlg.size.y, sim.y),
			"%s: dialog berukuran jendela %s (got %s)" % [tag, sim, dlg.size])
		var panel := dlg.find_child("TopupPanel", false, false) as PygamePanel
		_expect(panel != null, "%s: panel dialog ada" % tag)
		if panel != null:
			var r: Rect2 = panel.get_global_rect()
			var center := MobileLayout.arena_center()
			var sc := panel.scale.x
			# get_global_rect() mengabaikan `scale` (dipusatkan di pivot =
			# tengah panel), jadi ukuran visual dihitung manual.
			var vis := Rect2(r.get_center() - r.size * sc * 0.5,
				r.size * sc)
			_expect(_approx(r.get_center().x, center.x)
				and _approx(r.get_center().y, center.y),
				"%s: panel terpusat di frame arena (pusat %.1f,%.1f vs %.1f,%.1f)"
					% [tag, r.get_center().x, r.get_center().y,
						center.x, center.y])
			var visible := Rect2(Vector2.ZERO, sim).intersection(
				MobileLayout.arena_frame_rect())
			_expect(_contains(visible, vis),
				"%s: isi dialog muat di frame yang terlihat (got %s)" % [tag, vis])
			_expect(sc > 0.0 and sc <= 1.0,
				"%s: skala 0..1 (got %.3f)" % [tag, sc])
			if sim.x >= 1280.0 and sim.y >= 720.0:
				_expect(sc == 1.0,
					"%s: jendela >= 1280x720 tidak mengecilkan dialog" % tag)
		holder.queue_free()
		await get_tree().process_frame


# ══════════════════════════════════════════════════════════
#  UTIL
# ══════════════════════════════════════════════════════════

## true kalau `inner` seluruhnya di dalam `outer` (toleransi 1 px, karena
## Control membulatkan offset ke bilangan bulat).
func _contains(outer: Rect2, inner: Rect2) -> bool:
	return inner.position.x >= outer.position.x - EPS \
		and inner.position.y >= outer.position.y - EPS \
		and inner.position.x + inner.size.x <= outer.position.x + outer.size.x + EPS \
		and inner.position.y + inner.size.y <= outer.position.y + outer.size.y + EPS
