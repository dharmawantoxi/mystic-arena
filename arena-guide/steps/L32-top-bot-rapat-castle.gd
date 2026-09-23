# L32 — fix patah TOP/BOT + rapatkan Dire Castle (paritas + visual) — SNIPPET
# Masalah dari screenshot user 2026-09-23:
#   - TOP lane patah di 2 tikungan (120,220→39° dan 240,100→38°) — bata 16px axis-aligned retak
#   - BOT lane patah di 2 tikungan (1070,620→39° dan 1170,500→32°)
#   - MID lane zigzag pygame 65°×4 di tengah juga patah (panah biru tengah)
#   - Dire castle spase 35px dari ujung lane (BASE_RED 1145,175 vs ujung 1180,180)
#
# Solusi L32 (4 suntingan, semua di Main.gd — copy-paste aman):
#   A) Rapatkan BASE_RED ke ujung lane → 1180,180 (gap 35→0)
#   B) Haluskan TOP: tambah 1 waypoint (235,125) pecah sudut 39° jadi <19°
#   C) Haluskan BOT: geser 2 titik (1070→1020,605 dan 1170→1090,535+1150,420) → <23°
#   D) Haluskan MID: kembalikan ke halus L30 (280,450...) → sudut <16° (jika mau 100% pygame, skip MID)
#   E) Padatkan kurva top/bot 10→14 + trunc int(x),int(y) biar bata tidak bolong 0.5px
#
# CATATAN: Jika kamu NGOTOT 100% pygame, cukup lakukan A+E saja (B/C/D skip).
# Tapi screenshot kamu sudah tandai patahnya — A+B+C+D+E adalah yang bikin lane mulus di 1.png.
# MID halus memang deviasi dari pygame, tapi mengorbankan 65° zigzag demi bata rapi.

# ═══════════════════════════════════════════
# A — rapatkan Dire castle (baris ~12)
# ═══════════════════════════════════════════
const BASE_RED = Vector2(1180, 180) # dulu Vector2(1145, 175) → jarak ke ujung lane 35.4px, sekarang 0px nempel

# ═══════════════════════════════════════════
# B+C+D — ganti 3 lane waypoint + smooth (baris ~19)
# ═══════════════════════════════════════════
const LANE_TOP_WP = [Vector2(90, 590), Vector2(85, 460), Vector2(95, 340), Vector2(130, 260), Vector2(175, 185), Vector2(235, 125), Vector2(285, 95), Vector2(380, 75), Vector2(550, 70), Vector2(720, 75), Vector2(880, 85), Vector2(1030, 110), Vector2(1180, 180)]
const LANE_MID_WP = [Vector2(170, 550), Vector2(280, 450), Vector2(400, 380), Vector2(520, 350), Vector2(640, 340), Vector2(760, 330), Vector2(880, 300), Vector2(1000, 240), Vector2(1110, 170)]
const LANE_BOT_WP = [Vector2(130, 630), Vector2(260, 650), Vector2(420, 660), Vector2(600, 660), Vector2(780, 655), Vector2(940, 645), Vector2(1020, 605), Vector2(1090, 535), Vector2(1150, 420), Vector2(1185, 330), Vector2(1190, 250), Vector2(1180, 180)]
const LANE_SMOOTH = [14, 8, 14]
# TOP: 12wp 10→14 (111→155 titik) + 1 wp baru (235,125) → sudut 39°→19°
# MID: 9wp halus L30 (skip jika mau pygame final [300,420,440,320,580,400...])
# BOT: 11→12wp + geser 2 titik → sudut 39°→23°
# Penjelasan MID alternatif pygame final (jangan pakai kalau mau mulus):
# const LANE_MID_WP = [Vector2(170, 550), Vector2(300, 420), Vector2(440, 320), Vector2(580, 400), Vector2(640, 360), Vector2(700, 320), Vector2(840, 400), Vector2(980, 300), Vector2(1110, 170)]

# ═══════════════════════════════════════════
# E — fix trunc di _curved_path (baris ~55, di dalam loop)
# ═══════════════════════════════════════════
# GANTI:
#   out.append(Vector2(x, y))
# MENJADI:
#   out.append(Vector2(int(x), int(y)))
# Alasan: pygame pakai int(x),int(y) truncate, Godot float bikin bata geser 0.5px → terlihat patah

# ═══════════════════════════════════════════
# CARA PASANG STEP-BY-STEP (di D:\mystic-godot-471)
# ═══════════════════════════════════════════
# 1. Buka scripts/Main.gd → Ctrl+F "BASE_RED" → ganti 1145,175 → 1180,180 → Ctrl+S
# 2. Ctrl+F "LANE_TOP_WP" → blok 1 baris penuh → paste 3 baris LANE_*_WP + LANE_SMOOTH di atas → Ctrl+S
# 3. Ctrl+F "out.append(Vector2(x" → ganti jadi Vector2(int(x), int(y)) → Ctrl+S
# 4. F5 → cek Output: "top 155 / mid 65 / bot 155 titik" (dulu 111/65/101) → lane harus mulus
# 5. Cek Dire castle: sekarang menempel lane, tidak ada spase seperti di 1.png tulisan SPASE
# Jika setelah F5 masih ada patah di titik lain, screenshot lagi lingkari → aku halus di titik itu saja
