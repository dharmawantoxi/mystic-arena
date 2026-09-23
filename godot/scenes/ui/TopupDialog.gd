# TopupDialog.gd — dialog TOP UP HERO GOLD (port Menu._draw_topup_* 1:1).
#
# Modal 920x580 di tengah layar: pilih paket + metode bayar (select),
# animasi proses 1.6 detik (processing), sukses (success), dan redeem
# kode voucher dengan keypad on-screen (redeem). Pembayaran disimulasikan
# seperti pygame (tanpa gateway); gold masuk ke SaveManager.meta_gold.
#
# TATA LETAK = PUSAT FRAME ARENA, BUKAN PUSAT VIEWPORT (perbaikan 2026-09-14,
# laporan user "pop up top up berada di luar frame"). Pygame menggambar dialog
# ke surface 1280x720 (`cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2`), jadi di
# Godot titik acuannya pusat frame arena — bukan pusat viewport, yang di
# jendela desktop lebih tinggi/lebar dari 16:9 jatuh DI LUAR peta karena
# kamera arena terkunci limit 0..1280 x 0..720 (lihat MobileLayout). Skala fit
# juga dihitung dari bagian frame yang terlihat supaya isi dialog tidak pernah
# terpotong.
#
# Perbaikan KEDUA hari yang sama (PR lanjutan #240): root, lapisan gelap, dan
# _body dulu memakai set_anchors_preset(PRESET_FULL_RECT) yang TIDAK
# mengosongkan offset — Control hasil kode tetap 0x0, jadi panel ber-anchor
# 0.5 terpusat di (0,0) (dialog seperti keluar lewat pojok kiri-atas layar)
# dan dim tidak terlihat. Semua lapisan full-rect kini memakai
# MobileLayout.fill_parent (anchor 0..1 + offset nol eksplisit).
#
# FASE 33 - HARGA MULTI-MATA-UIANG (gap #2 audit). Sebelumnya dialog ini hanya
# punya satu angka IDR dan memformatnya sendiri ("Rp10.000" - tanpa spasi,
# beda dari pygame "Rp 10.000"). Kini harga lewat TopupCurrency (port 1:1
# topup_currency.py di root) dengan nama mata uang per pengguna, meniru alur
# pygame:
#   * `Game.topup_currency` (_core.py:3190, None) -> `currency` di sini;
#     deteksi malas (_core.py:5583-5589) sekali di _ready - dialog Godot
#     ditata ulang saat dibuka, tidak digambar tiap frame - dan kegagalan
#     sama-sama jatuh ke "USD";
#   * `Game._topup_price_str` (_core.py:5344-5347, `or "IDR"`) -> _price_str;
#   * riwayat pembelian (_core.py:6107-6109, 6119) -> `cur` + `price_cur`
#     ikut tersimpan; redeem tetap "IDR"/0 seperti _core.py:6065-6073.
# Nilai mata uang, simbol, dan pembulatannya TIDAK ada di berkas ini — semuanya
# hidup di TopupCurrency.gd (port 1:1) supaya tes parity bisa memutar ulang
# tabelnya tanpa menyalin angka ke dua tempat.
extends Control
class_name TopupDialog

signal closed

const PACKAGES: Array = [
	{"label": "PAKET 50K", "gold": 50000, "bonus": 0, "price": 10000},
]
const METHODS: Array = ["GOPAY", "OVO", "DANA", "SHOPEEPAY",
	"BANK TRANSFER"]
const PROCESSING_SECONDS := 1.6
const CODE_PREFIX := "MA-"
const MAX_DIGITS := 6

const DW := 920.0
const DH := 580.0
## Margin minimum panel terhadap tepi viewport saat di-fit (px).
const FIT_MARGIN := 24.0
## Skala minimum panel — di bawah ini dialog tidak lagi terbaca.
const MIN_SCALE := 0.4

var phase: String = "select"
## Nama mata uang tampilan harga (paritas `Game.topup_currency`,
## _core.py:3190). "" = belum terdeteksi -> harga tampil sebagai IDR, persis
## `self.topup_currency or "IDR"` di pygame.
var currency: String = ""
var pkg_idx: int = 0
var method_idx: int = 0
var progress: float = 0.0
var tx_id: String = ""
var last_total: int = 0
var last_method: String = ""
var redeem_code: String = ""
var redeem_input: String = ""
var redeem_msg: String = ""
var redeem_msg_color: Color = Color("#ff7878")

var _t: float = 0.0
var _panel: PygamePanel = null
var _body: Control = null


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	# Deteksi malas seperti pygame (_core.py:5583-5589): hanya bila belum
	# pernah diresolve; kegagalan deteksi -> fallback "USD".
	# MYSTIC_FORCE_LOCALE (env) memaksa locale - dipakai tes headless dan
	# tes screenshot supaya cabang deteksi bisa dibandingkan deterministik.
	if currency == "":
		currency = TopupCurrency.detect_currency()
	MobileLayout.fill_parent(self)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	# Nama eksplisit: test tata letak (ArenaFrameLayoutTest) mencari lapisan
	# ini lewat find_child("Dim") untuk memastikan ia benar-benar menutupi
	# jendela (bukan 0x0 — kegagalan senyap sebelum fill_parent).
	dim.name = "Dim"
	dim.color = Color(0, 0, 0, 205.0 / 255.0)
	MobileLayout.fill_parent(dim)
	add_child(dim)
	_panel = PygamePanel.new(Color("#ffc850"), 3.0, 16.0)
	_panel.name = "TopupPanel"
	_panel.configure(Color("#202642"), Color("#101426"), Color("#ffc850"),
		3.0, 16.0, true, true)
	# Margin konten NOL: seluruh isi dialog diposisikan absolut persis di
	# ruang 920x580 (paritas koordinat pygame). Margin bawaan PygamePanel
	# (14/10/14/10) menggeser _body sehingga sisi kanan jadi mepet.
	_panel.set_margins(0, 0, 0, 0)
	_panel.ticks_color = UiTheme.GOLD_BRIGHT
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_panel)
	_place_panel()
	_rebuild()
	# Ukuran jendela berubah selagi dialog terbuka (resize/maximize/rotasi):
	# MobileLayout.layout_changed selalu membawa ukuran viewport yang segar,
	# jadi tata letak tidak bergantung urutan dengan NOTIFICATION_RESIZED.
	MobileLayout.layout_changed.connect(_place_panel)


func _notification(what: int) -> void:
	# Root full-rect ikut berubah saat viewport di-resize selagi dialog
	# terbuka (resize jendela / rotasi) — panel diletakkan ulang seketika.
	# Ukuran viewport-nya SENDIRI datang lewat MobileLayout.layout_changed
	# (dari root.size_changed), jadi tidak perlu membaca ulang di sini:
	# satu sumber angka, dan urutan notifikasi tidak jadi soal.
	if what == NOTIFICATION_RESIZED:
		_place_panel()


## Panel 920x580 dipusatkan pada FRAME ARENA 1280x720 (pusat peta, paritas
## `cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2` pygame) dan diskalakan seragam
## supaya SELALU muat di bagian frame yang terlihat (margin FIT_MARGIN).
## Di 1280x720 skala = 1 (persis desain pygame); di jendela lebih kecil /
## portrait / tanpa stretch dialog mengecil proporsional alih-alih terpotong
## keluar frame. Input mouse tetap akurat (engine memetakan klik ke kontrol
## yang diskalakan).
func _place_panel() -> void:
	if _panel == null:
		return
	if MobileLayout.viewport_size.x <= 0.0 or MobileLayout.viewport_size.y <= 0.0:
		return
	MobileLayout.place_in_arena(_panel, Vector2.ZERO, Vector2(DW, DH))
	var s := clampf(MobileLayout.arena_fit_scale(Vector2(DW, DH), FIT_MARGIN),
		MIN_SCALE, 1.0)
	_panel.pivot_offset = Vector2(DW * 0.5, DH * 0.5)
	_panel.scale = Vector2(s, s)


func _process(delta: float) -> void:
	_t += delta * 60.0
	if phase == "processing":
		progress += delta / PROCESSING_SECONDS
		if progress >= 1.0:
			_topup_complete()
		else:
			_rebuild() # progress bar bergerak (murah: dialog kecil)


func _unhandled_key_input(event: InputEvent) -> void:
	if phase != "redeem":
		return
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	if k.keycode >= KEY_0 and k.keycode <= KEY_9:
		_redeem_append(str(k.keycode - KEY_0))
	elif k.keycode >= KEY_KP_0 and k.keycode <= KEY_KP_9:
		_redeem_append(str(k.keycode - KEY_KP_0))
	elif k.keycode == KEY_BACKSPACE or k.keycode == KEY_DELETE:
		_redeem_backspace()
	elif k.keycode == KEY_ENTER or k.keycode == KEY_KP_ENTER:
		_redeem_submit()
	elif k.keycode == KEY_ESCAPE:
		phase = "select"
		redeem_input = ""
		redeem_msg = ""
		AudioManager.play_sfx("ui_click", 0.5)
		_rebuild()
		get_viewport().set_input_as_handled()
		return
	else:
		return
	get_viewport().set_input_as_handled()


# ── pembangunan tampilan ──

func _clear_body() -> void:
	if _body != null and is_instance_valid(_body):
		_body.queue_free()
	_body = Control.new()
	_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	MobileLayout.fill_parent(_body)
	_panel.add_child(_body)


func _rebuild() -> void:
	_clear_body()
	var cx := DW * 0.5
	# Judul Cinzel 34 + subtitle + garis.
	var title := Label.new()
	UiTheme.style_label(title, "TOP UP HERO GOLD", UiTheme.title_font(),
		34, UiTheme.GOLD_BRIGHT, HORIZONTAL_ALIGNMENT_CENTER)
	title.add_theme_color_override("font_outline_color",
		Color("#080912"))
	title.add_theme_constant_override("outline_size", 4)
	title.position = Vector2(0, 10)
	title.size = Vector2(DW, 48)
	_body.add_child(title)
	var sub_text := MysticLocalization.tr_text("topup_subtitle")
	if phase == "redeem":
		sub_text = "REDEEM CODE - enter the code you received from admin after paying"
	elif phase == "processing":
		sub_text = "Please wait - do not close the dialog"
	elif phase == "success":
		sub_text = "Transaction complete"
	var sub := Label.new()
	UiTheme.style_label(sub, sub_text, UiTheme.body_regular(), 20,
		Color("#a0aabe"), HORIZONTAL_ALIGNMENT_CENTER)
	sub.position = Vector2(0, 56)
	sub.size = Vector2(DW, 26)
	_body.add_child(sub)
	var div := ColorRect.new()
	div.color = Color("#3c465a")
	div.position = Vector2(18, 80)
	div.size = Vector2(DW - 36, 1)
	_body.add_child(div)
	match phase:
		"select":
			_build_select(cx)
		"processing":
			_build_processing(cx)
		"success":
			_build_success(cx)
		"redeem":
			_build_redeem(cx)


func _lbl(text: String, font: Font, size: int, color: Color, pos: Vector2,
		align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT,
		w: float = 0.0) -> Label:
	var l := Label.new()
	UiTheme.style_label(l, text, font, size, color, align)
	l.position = pos
	if w > 0.0:
		l.size = Vector2(w, size + 12)
	_body.add_child(l)
	return l


# ── fase SELECT ──

func _build_select(_cx: float) -> void:
	var col_x := 24.0
	_lbl("1. CHOOSE PACKAGE", UiTheme.body_regular(), 20,
		Color("#8cbe96"), Vector2(col_x, 92))
	# Kartu paket tunggal (504x92, dipusatkan di area kiri 112..430).
	var card_w := 504.0
	var card_h := 92.0
	var y0 := 112.0 + (430.0 - 112.0 - card_h) * 0.5
	var pkg: Dictionary = PACKAGES[pkg_idx]
	var card := _SelectCard.new(0, pkg, pkg_idx == 0, _price_str(int(pkg.get("price", 0))))
	card.position = Vector2(col_x, y0)
	card.size = Vector2(card_w, card_h)
	card.chosen.connect(_on_pkg_chosen)
	_body.add_child(card)
	# Metode pembayaran (kanan).
	var meth_x := 556.0
	var meth_w := DW - (meth_x - 0.0) - 24.0
	_lbl("2. PAYMENT METHOD", UiTheme.body_regular(), 20,
		Color("#8cbe96"), Vector2(meth_x, 88))
	for i in range(METHODS.size()):
		var row := _MethodRow.new(i, str(METHODS[i]), method_idx == i)
		row.position = Vector2(meth_x, 116 + i * 46)
		row.size = Vector2(meth_w, 38)
		row.chosen.connect(_on_method_chosen)
		_body.add_child(row)
	# Baris REDEEM CODE.
	var rd := _RedeemRow.new()
	rd.position = Vector2(meth_x, 346)
	rd.size = Vector2(meth_w, 38)
	rd.chosen.connect(_on_redeem_open)
	_body.add_child(rd)
	# Ringkasan.
	var div2 := ColorRect.new()
	div2.color = Color("#3c465a")
	div2.position = Vector2(18, 430)
	div2.size = Vector2(DW - 36, 1)
	_body.add_child(div2)
	var total := int(pkg["gold"]) + int(pkg.get("bonus", 0))
	_lbl("TOTAL GOLD: ", UiTheme.body_medium(), 24, Color("#aab4c8"),
		Vector2(24, 448))
	_lbl("+%s" % _grouped(total), UiTheme.body_medium(), 24,
		UiTheme.GOLD, Vector2(170, 446))
	var price := _lbl(_price_str(int(pkg.get("price", 0))), UiTheme.body_medium(), 24,
		Color.WHITE, Vector2(DW - 24 - 200, 446),
		HORIZONTAL_ALIGNMENT_RIGHT, 200)
	price.position = Vector2(DW - 24 - 200, 446)
	_lbl("Simulated payment - no real charge.", UiTheme.body_regular(),
		20, Color("#788296"), Vector2(24, 474))
	# Tombol bawah.
	var cancel := PygameButton.pill_button("CANCEL", "neutral", "", 170,
		52, 24)
	cancel.position = Vector2(24, 496)
	cancel.size = Vector2(170, 52)
	cancel.pressed.connect(_on_cancel)
	_body.add_child(cancel)
	var pay := PygameButton.pill_button(
		"PAY NOW  •  %s" % _price_str(int(pkg.get("price", 0))), "success", "coin", 340, 52,
		24)
	pay.position = Vector2(DW - 24 - 340, 496)
	pay.size = Vector2(340, 52)
	pay.pressed.connect(_on_pay)
	_body.add_child(pay)


func _on_pkg_chosen(idx: int) -> void:
	pkg_idx = idx
	_rebuild()


func _on_method_chosen(idx: int) -> void:
	method_idx = idx
	_rebuild()


func _on_redeem_open() -> void:
	phase = "redeem"
	redeem_input = ""
	redeem_msg = ""
	_rebuild()


func _on_cancel() -> void:
	closed.emit()
	queue_free()


func _on_pay() -> void:
	# Pembayaran server tidak tersedia di port Godot — selalu simulasi
	# 1.6 detik seperti pygame tanpa topup_server_url.
	phase = "processing"
	progress = 0.0
	_rebuild()


# ── fase PROCESSING ──

func _build_processing(cx: float) -> void:
	var cy := DH * 0.5
	var pkg: Dictionary = PACKAGES[pkg_idx]
	var spin := _Spinner.new(_t)
	spin.position = Vector2(cx - 48, cy - 70 - 48)
	spin.size = Vector2(96, 96)
	_body.add_child(spin)
	_lbl("PROCESSING PAYMENT...", UiTheme.body_semibold(), 30,
		Color("#f0f5fa"), Vector2(0, cy + 10),
		HORIZONTAL_ALIGNMENT_CENTER, DW)
	_lbl("via %s  •  %s" % [str(METHODS[method_idx]),
		_price_str(int(pkg.get("price", 0)))], UiTheme.body_medium(), 24, Color("#aab4c8"),
		Vector2(0, cy + 42), HORIZONTAL_ALIGNMENT_CENTER, DW)
	var bar := _ProgressView.new(progress)
	bar.position = Vector2(cx - 180, cy + 72)
	bar.size = Vector2(360, 10)
	_body.add_child(bar)


# ── fase SUCCESS ──

func _build_success(cx: float) -> void:
	var cy := DH * 0.5
	var pkg: Dictionary = PACKAGES[pkg_idx]
	var check := _CheckView.new()
	check.position = Vector2(cx - 46, cy - 90 - 46)
	check.size = Vector2(92, 92)
	_body.add_child(check)
	var is_redeem := last_method == "redeem"
	_lbl("CODE REDEEMED!" if is_redeem else "TOP UP SUCCESSFUL!",
		UiTheme.body_semibold(), 30, Color("#ffdc64"),
		Vector2(0, cy), HORIZONTAL_ALIGNMENT_CENTER, DW)
	_lbl("+%s HERO GOLD ADDED" % _grouped(last_total),
		UiTheme.body_semibold(), 30, UiTheme.GOLD, Vector2(0, cy + 36),
		HORIZONTAL_ALIGNMENT_CENTER, DW)
	var tx_line := ""
	if is_redeem:
		tx_line = "TX ID: %s   •   CODE %s" % [tx_id, redeem_code]
	else:
		tx_line = "TX ID: %s   •   %s   •   %s" % [tx_id,
			str(METHODS[method_idx]), _price_str(int(pkg.get("price", 0)))]
	_lbl(tx_line, UiTheme.body_regular(), 20, Color("#96a0b4"),
		Vector2(0, cy + 68), HORIZONTAL_ALIGNMENT_CENTER, DW)
	var back := PygameButton.pill_button("BACK", "cyan", "", 220, 48, 24)
	back.position = Vector2(cx - 110, cy + 96)
	back.size = Vector2(220, 48)
	back.pressed.connect(_on_success_back)
	_body.add_child(back)


func _on_success_back() -> void:
	# Kembali ke Hero Shop (dialog ditutup; chip gold disegarkan pemanggil).
	closed.emit()
	queue_free()


# ── fase REDEEM ──

func _build_redeem(cx: float) -> void:
	var vback := PygameButton.pill_button("BACK", "neutral", "", 68, 30,
		16)
	vback.position = Vector2(DW - 92, 22)
	vback.size = Vector2(68, 30)
	vback.pressed.connect(_on_redeem_back)
	_body.add_child(vback)
	# Kotak input.
	var box := _InputBox.new(redeem_input, _t)
	box.position = Vector2(cx - 180, 104)
	box.size = Vector2(360, 58)
	_body.add_child(box)
	_lbl("Format: MA-123456  (4-6 digits)", UiTheme.body_regular(), 20,
		Color("#788296"), Vector2(0, 180), HORIZONTAL_ALIGNMENT_CENTER,
		DW)
	if not redeem_msg.is_empty():
		_lbl(redeem_msg, UiTheme.body_medium(), 24, redeem_msg_color,
			Vector2(0, 206), HORIZONTAL_ALIGNMENT_CENTER, DW)
	# Keypad 3x4.
	var key_w := 130.0
	var key_h := 58.0
	var gap := 18.0
	var keys := [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"],
		["del", "0", "redeem"]]
	var x0 := cx - (3 * key_w + 2 * gap) * 0.5
	var y0 := 232.0
	for r in range(4):
		for c in range(3):
			var k := str(keys[r][c])
			var key := _KeyButton.new(k)
			key.position = Vector2(x0 + c * (key_w + gap),
				y0 + r * (key_h + gap))
			key.size = Vector2(key_w, key_h)
			key.key_pressed.connect(_on_keypad)
			_body.add_child(key)


func _on_redeem_back() -> void:
	phase = "select"
	redeem_input = ""
	redeem_msg = ""
	_rebuild()


func _on_keypad(k: String) -> void:
	if k == "del":
		_redeem_backspace()
	elif k == "redeem":
		_redeem_submit()
	else:
		_redeem_append(k)


func _redeem_append(ch: String) -> void:
	var digits := redeem_input.replace(CODE_PREFIX, "")
	if digits.length() >= MAX_DIGITS:
		return
	if not redeem_input.begins_with(CODE_PREFIX):
		redeem_input = CODE_PREFIX
	redeem_input += ch
	redeem_msg = ""
	AudioManager.play_sfx("ui_click", 0.25)
	_rebuild()


func _redeem_backspace() -> void:
	if redeem_input.is_empty():
		return
	if redeem_input.begins_with(CODE_PREFIX) \
			and redeem_input.length() == CODE_PREFIX.length():
		redeem_input = ""
	else:
		redeem_input = redeem_input.substr(0, redeem_input.length() - 1)
	redeem_msg = ""
	AudioManager.play_sfx("ui_click", 0.25)
	_rebuild()


func _redeem_submit() -> void:
	var code := redeem_input.strip_edges().to_upper()
	if not _valid_format(code):
		redeem_msg = "Invalid code. Format: MA-123456"
		redeem_msg_color = Color("#ff7878")
		AudioManager.play_sfx("ui_error", 0.5)
		_rebuild()
		return
	var used: Array = SaveManager.data.get("redeemed_codes", [])
	if code in used:
		redeem_msg = "Code already redeemed."
		redeem_msg_color = Color("#ff7878")
		AudioManager.play_sfx("ui_error", 0.5)
		_rebuild()
		return
	# Mode demo: tanpa allowlist, semua kode berformat valid diterima
	# (paritas load_vouchers() == None).
	var pkg: Dictionary = PACKAGES[0]
	var amount := int(pkg["gold"]) + int(pkg.get("bonus", 0))
	_redeem_grant(code, amount)


func _valid_format(code: String) -> bool:
	if not code.begins_with(CODE_PREFIX):
		return false
	var digits := code.substr(CODE_PREFIX.length())
	if digits.length() < 4 or digits.length() > 8:
		return false
	for i in range(digits.length()):
		if not digits[i].is_valid_int():
			return false
	return true


func _redeem_grant(code: String, amount: int) -> void:
	var used: Array = SaveManager.data.get("redeemed_codes", [])
	if code in used:
		return
	SaveManager.add_meta_gold(amount)
	tx_id = "MA-%010d" % (int(Time.get_ticks_msec()) % 10000000000)
	used.append(code)
	while used.size() > 50:
		used.pop_front()
	SaveManager.data["redeemed_codes"] = used
	var history: Array = SaveManager.data.get("topup_history", [])
	history.append({"tx": tx_id, "pkg": "REDEEM", "gold": amount,
		"bonus": 0, "price": 0, "cur": "IDR", "price_cur": 0,
		"method": "redeem", "code": code,
		"ts": int(Time.get_unix_time_from_system())})
	while history.size() > 50:
		history.pop_front()
	SaveManager.data["topup_history"] = history
	SaveManager.save()
	phase = "success"
	last_total = amount
	last_method = "redeem"
	redeem_code = code
	AudioManager.play_sfx("ui_buy", 0.9)
	_rebuild()


func _topup_complete() -> void:
	var pkg: Dictionary = PACKAGES[pkg_idx]
	var total := int(pkg["gold"]) + int(pkg.get("bonus", 0))
	SaveManager.add_meta_gold(total)
	tx_id = "MA-%010d" % (int(Time.get_ticks_msec()) % 10000000000)
	var history: Array = SaveManager.data.get("topup_history", [])
	# Paritas _core.py:6107-6109 + 6119: `cur` = mata uang pengguna ("IDR"
	# kalau belum terdeteksi) dan `price_cur` = harga dalam mata uang itu,
	# sudah dibulatkan 2 desimal ties-even. Pembulatannya lewat
	# HudLayout.round_half_even_scaled: `round()` engine membulatkan .5
	# menjauhi nol, jadi selisih satu sen di data tersimpan itu bug, bukan
	# gaya pembulatan.
	var price_idr := int(pkg["price"])
	var cur := currency if currency != "" else "IDR"
	# convert_idr mengembalikan [nilai, mata_uang_final] dan pygame menyimpan
	# `cur` ASLINYA (bukan yang final) + nilai yang dibulatkan 2 desimal
	# ties-even (_core.py:6108, 6119) — jadi riwayat lama tetap terbaca.
	var converted: Array = TopupCurrency.convert_idr(price_idr, cur)
	var price_cur := float(HudLayout.round_half_even_scaled(
			float(converted[0]), 2)) / 100.0
	history.append({"tx": tx_id, "pkg": str(pkg["label"]),
		"gold": int(pkg["gold"]), "bonus": int(pkg.get("bonus", 0)),
		"price": price_idr, "cur": cur,
		"price_cur": price_cur,
		"method": str(METHODS[method_idx]).to_lower(),
		"ts": int(Time.get_unix_time_from_system())})
	while history.size() > 50:
		history.pop_front()
	SaveManager.data["topup_history"] = history
	SaveManager.save()
	phase = "success"
	last_total = total
	last_method = str(METHODS[method_idx]).to_lower()
	AudioManager.play_sfx("ui_buy", 0.9)
	_rebuild()


# ── helper format ──

static func _grouped(n: int) -> String:
	return HudLayout.format_thousands(n)


func _price_str(amount_idr: float) -> String:
	# Paritas `Game._topup_price_str` (_core.py:5344-5347): mata uang kosong
	# berarti "tampilkan IDR apa adanya", jadi pemanggil tidak perlu tahu
	# apakah deteksi sudah terjadi atau belum.
	return TopupCurrency.format_price(amount_idr,
			currency if currency != "" else "IDR")


# ── sub-view kustom (gambar eksak pygame) ──

class _SelectCard extends BaseButton:
	signal chosen(idx: int)
	var idx: int = 0
	var pkg: Dictionary = {}
	var selected: bool = false
	var price_str: String = ""
	var _hover: bool = false

	func _init(p_idx: int, p_pkg: Dictionary, p_sel: bool,
			p_price: String) -> void:
		idx = p_idx
		pkg = p_pkg
		selected = p_sel
		price_str = p_price
		focus_mode = Control.FOCUS_NONE
		mouse_entered.connect(_set_hover.bind(true))
		mouse_exited.connect(_set_hover.bind(false))
		pressed.connect(func(): chosen.emit(idx))

	func _set_hover(v: bool) -> void:
		_hover = v
		queue_redraw()

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		var hover := _hover
		var bg := Color("#16422c") if selected \
			else (Color("#222c44") if hover else Color("#1c2236"))
		var edge := Color("#78ffa0") if selected \
			else (Color("#78e696") if hover else Color("#4b556e"))
		UiTheme.draw_rr(self, rect, bg, 10.0)
		UiTheme.draw_rr_outline(self, rect, edge, 10.0,
			3.0 if selected else 1.0)
		var lb_col := Color("#ffdc82") if selected \
			else Color("#aab4c8")
		UiTheme.draw_text(self, UiTheme.body_regular(), str(pkg["label"]),
			20, lb_col, rect.position + Vector2(12, 9), false)
		var pr_col := Color.WHITE if selected else Color("#c8cddc")
		var font := UiTheme.body_medium()
		var pw := font.get_string_size(price_str,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 24).x
		UiTheme.draw_text(self, font, price_str, 24, pr_col,
			Vector2(rect.end.x - 12 - pw, rect.position.y + 9), false)
		var total := int(pkg["gold"]) + int(pkg.get("bonus", 0))
		UiTheme.draw_text(self, UiTheme.body_medium(),
			"+%s" % HudLayout.format_thousands(total), 24,
			Color("#ffc832"), rect.position + Vector2(12, 40), false)
		var gw := font.get_string_size(
			"+%s" % HudLayout.format_thousands(total),
			HORIZONTAL_ALIGNMENT_LEFT, -1, 24).x
		UiTheme.draw_text(self, UiTheme.body_regular(), "GOLD", 20,
			Color("#c8a03c"),
			rect.position + Vector2(12 + gw + 6, 44), false)
		if int(pkg.get("bonus", 0)) > 0:
			UiTheme.draw_text(self, UiTheme.body_regular(),
				"incl. +%s BONUS" % HudLayout.format_thousands(
					int(pkg["bonus"])),
				20, Color("#78eb96"),
				Vector2(rect.position.x + 12, rect.end.y - 22), false)


class _MethodRow extends BaseButton:
	signal chosen(idx: int)
	var idx: int = 0
	var label_text: String = ""
	var _hover: bool = false
	var selected: bool = false

	func _init(p_idx: int, p_label: String, p_sel: bool) -> void:
		idx = p_idx
		label_text = p_label
		selected = p_sel
		focus_mode = Control.FOCUS_NONE
		mouse_entered.connect(_set_hover.bind(true))
		mouse_exited.connect(_set_hover.bind(false))
		pressed.connect(func(): chosen.emit(idx))

	func _set_hover(v: bool) -> void:
		_hover = v
		queue_redraw()

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		var hover := _hover
		var bg := Color("#16422c") if selected \
			else (Color("#222c44") if hover else Color("#1c2236"))
		var edge := Color("#78ffa0") if selected \
			else (Color("#78e696") if hover else Color("#4b556e"))
		UiTheme.draw_rr(self, rect, bg, 8.0)
		UiTheme.draw_rr_outline(self, rect, edge, 8.0,
			2.0 if selected else 1.0)
		var cc := Vector2(rect.position.x + 21, rect.get_center().y)
		draw_circle(cc, 8.0,
			Color("#78ffa0") if selected else Color("#5a647d"))
		if selected:
			draw_circle(cc, 4.0, Color("#0a2818"))
		var lab_col := Color("#ebfff0") if selected \
			else Color("#bec8d7")
		UiTheme.draw_text(self, UiTheme.body_medium(), label_text, 24,
			lab_col, Vector2(rect.position.x + 40,
				rect.get_center().y - 9), false)


class _RedeemRow extends BaseButton:
	signal chosen

	var _hover: bool = false

	func _init() -> void:
		focus_mode = Control.FOCUS_NONE
		mouse_entered.connect(_set_hover.bind(true))
		mouse_exited.connect(_set_hover.bind(false))
		pressed.connect(func(): chosen.emit())

	func _set_hover(v: bool) -> void:
		_hover = v
		queue_redraw()

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		var hover := _hover
		UiTheme.draw_rr(self, rect,
			Color("#383016") if hover else Color("#282414"), 8.0)
		UiTheme.draw_rr_outline(self, rect,
			Color("#ffdc82") if hover else Color("#bea050"), 8.0, 2.0)
		var tx := rect.position.x + 14
		var ty := rect.get_center().y
		UiTheme.draw_rr(self, Rect2(tx, ty - 6, 16, 12),
			Color("#ffd26e"), 3.0)
		draw_circle(Vector2(tx, ty), 3.0, Color("#282414"))
		draw_circle(Vector2(tx + 16, ty), 3.0, Color("#282414"))
		UiTheme.draw_text(self, UiTheme.body_medium(), "REDEEM CODE",
			24, Color("#ffe196"),
			Vector2(rect.position.x + 40, ty - 9), false)


class _Spinner extends Control:
	var t: float = 0.0

	func _init(p_t: float) -> void:
		t = p_t
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var c := size * 0.5
		var base := fmod(t, 60.0) / 60.0 * TAU
		for k in range(3):
			var start := base + TAU * float(k) / 3.0
			draw_arc(c, 48.0, start, start + TAU / 4.0, 24,
				Color("#78ffa0"), 5.0)


class _ProgressView extends Control:
	var frac: float = 0.0

	func _init(p: float) -> void:
		frac = p
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		UiTheme.draw_rr(self, rect, Color("#283044"), 5.0)
		var fill := size.x * clampf(frac, 0.0, 1.0)
		if fill > 4.0:
			UiTheme.draw_rr(self, Rect2(0, 0, fill, size.y),
				Color("#78ffa0"), 5.0)
		UiTheme.draw_rr_outline(self, rect, Color("#5a6482"), 5.0, 1.0)


class _CheckView extends Control:
	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var c := size * 0.5
		draw_arc(c, 46.0, 0, TAU, 48, Color("#103c24"), 6.0)
		draw_circle(c, 40.0, Color("#1e7842"))
		draw_line(c + Vector2(-18, -2), c + Vector2(-4, 14),
			Color("#8cffaF"), 6.0)
		draw_line(c + Vector2(-4, 14), c + Vector2(20, -16),
			Color("#8cffaF"), 6.0)


class _InputBox extends Control:
	var text: String = ""
	var t: float = 0.0

	func _init(p_text: String, p_t: float) -> void:
		text = p_text
		t = p_t
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		UiTheme.draw_rr(self, rect, Color("#0e1220"), 10.0)
		UiTheme.draw_rr_outline(self, rect, Color("#ffc850"), 10.0,
			2.0)
		var font := UiTheme.body_bold()
		if text.is_empty():
			var ph := "MA-_ _ _ _ _ "
			UiTheme.draw_text_centered(self, font, ph, 44,
				Color("#5a647d"), rect.get_center(), false)
		else:
			UiTheme.draw_text_centered(self, font, text, 44,
				Color.WHITE, rect.get_center(), false)
			if int(t / 30.0) % 2 == 0:
				var tw := font.get_string_size(text,
					HORIZONTAL_ALIGNMENT_LEFT, -1, 44).x
				var cur_x := rect.get_center().x + tw * 0.5 + 5.0
				draw_rect(Rect2(cur_x, rect.get_center().y - 14, 3,
					28), Color("#ffc850"))


class _KeyButton extends BaseButton:
	signal key_pressed(k: String)
	var key_id: String = ""
	var _hover: bool = false

	func _init(k: String) -> void:
		key_id = k
		focus_mode = Control.FOCUS_NONE
		mouse_entered.connect(_set_hover.bind(true))
		mouse_exited.connect(_set_hover.bind(false))
		pressed.connect(func(): key_pressed.emit(key_id))

	func _set_hover(v: bool) -> void:
		_hover = v
		queue_redraw()

	func _draw() -> void:
		var rect := Rect2(Vector2.ZERO, size)
		var hover := _hover
		var bg := Color("#212e4e")
		var bd := Color("#505f87")
		var fg := Color.WHITE
		var label := key_id.to_upper()
		if key_id == "redeem":
			bg = Color("#1e8248") if hover else Color("#126236")
			bd = Color("#8cffaf") if hover else Color("#55cd7d")
			fg = Color.WHITE
			label = "REDEEM"
		elif key_id == "del":
			bg = Color("#555a69") if hover else Color("#3a3e4e")
			bd = Color("#aab4c8") if hover else Color("#6e7891")
			fg = Color("#ebebf0")
			label = "DEL"
		else:
			bg = Color("#2c344e") if hover else Color("#21283e")
			bd = Color("#8296c8") if hover else Color("#505f87")
			label = key_id
		UiTheme.draw_rr(self, rect, bg, 8.0)
		UiTheme.draw_rr_outline(self, rect, bd, 8.0, 2.0)
		UiTheme.draw_text_centered(self, UiTheme.body_bold(), label,
			30 if key_id != "redeem" else 22, fg, rect.get_center(),
			false)
