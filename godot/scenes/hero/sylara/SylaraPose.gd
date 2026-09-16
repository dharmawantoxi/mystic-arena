# SylaraPose.gd — data pose tunggal rig Sylara.
#
# Satu pose = semua sudut/offset yang dibutuhkan SylaraRenderer untuk
# menggambar karakter. Animator MENULIS pose target ke instance yang
# dipakai ulang tiap frame (tanpa alokasi per frame — penting di
# Android), lalu SylaraSkeleton me-lerp pose saat-ini menuju target
# supaya transisi antar-state halus (tidak robotic).
#
# Konvensi sudut (radian, layar y-down Godot):
#   * torso/kepala/lengan/kaki: 0 = lurus ke bawah / tegak, positif =
#     ke depan (+x lokal).
#   * aim_angle: arah bidik ABSOLUT ruang lokal rig, 0 = +x (arah
#     hadap), positif = memutar ke bawah layar (searah jarum jam).
#     Diisi root dari posisi target (ruang dunia → lokal) sehingga busur
#     bisa membidik 360° bebas — bukan hanya kiri/kanan.
#   * bow_offset: offset pose busur relatif aim_angle (busur diturunkan
#     saat idle, sejajar saat bidik).
#   * bow_draw: 0.0 = santai, 1.0 = tali tertarik penuh.
#   * cape/hood/hair: arah absolut tiap segmen, PI = ke belakang.
class_name SylaraPose
extends RefCounted

# ── Root / tubuh ──
var root_x := 0.0          # pergeseran pinggul (lunge, recoil)
var root_y := 0.0          # naik/turun pinggul (bob napas, crouch)
var torso_lean := 0.0      # kemiringan tulang punggung dari vertikal
var chest_flex := 0.0      # tambahan flex dada (membungkuk/menengadah)
var head_lean := 0.0       # relatif dada; positif = menunduk ke depan

# ── Lengan (depan = sisi busur / grip hand) ──
var arm_f_sh := 0.12       # bahu: 0 = lurus bawah, + = ke depan
var arm_f_el := 0.55       # siku: tekuk relatif lengan atas
var arm_b_sh := -0.10      # bahu belakang (sisi tarik tali)
var arm_b_el := 0.40       # siku belakang

# ── Kaki ──
var leg_f_hip := 0.05
var leg_f_knee := -0.06
var leg_f_foot := 0.12     # sudut telapak (0 = datar ke depan)
var leg_b_hip := -0.06
var leg_b_knee := -0.05
var leg_b_foot := 0.10

# ── Busur (senjata utama) ──
var aim_angle := 0.0       # arah bidik absolut lokal (rad)
var bow_offset := 0.0      # offset pose busur dari arah bidik
var bow_draw := 0.0        # tarikan tali 0..1 (0 = rileks, 1 = full draw)
var bow_off := Vector2.ZERO  # offset grip tambahan (dipakai skill)

# ── Secondary motion: arah absolut tiap segmen (rad, y-down) ──
var cape: Array[float] = [2.98, 3.10, 2.86]     # 3 segmen cape
var hood: Array[float] = [2.85, 3.10]           # 2 segmen hood edges
var hair: Array[float] = [3.05, 3.18, 2.95]     # 3 segmen rambut

# ── Ekspresi / aura ──
var cape_flare := 0.5      # lebar bukaan cape (px ekstra di hem)
var eye_blink := 0.0       # 0 = terbuka, 1 = tertutup
var wind_glow := 0.0       # intensitas aksen sihir angin (0..1)
var focus_glow := 0.0      # aura Focus Fire di busur (0..1)
var windrun := 0.0         # aura Windrun + trail angin (0..1)
var channel := 0.0         # tegangan charge Powershot (0..1)
var hurt_tint := 0.0       # kilatan merah saat kena pukul (0..1)
var alpha := 1.0           # seluruh rig (death fade)

# ── Tether Shackle Shot (ruang lokal rig) ──
var tether_on := false         # apakah sulur aktif
var tether_alpha := 0.0        # fade masuk/keluar (di-blend root)
var tether_local := Vector2.ZERO  # posisi target di ruang lokal rig
var aim_point_local := Vector2.ZERO  # titik bidik channel (ruang lokal rig)


## Kembalikan ke nilai default sebelum dipakai ulang sebagai pose target.
## Dipanggil animator di awal compute() — tanpa alokasi baru.
func reset() -> void:
	root_x = 0.0
	root_y = 0.0
	torso_lean = 0.0
	chest_flex = 0.0
	head_lean = 0.0
	arm_f_sh = 0.12
	arm_f_el = 0.55
	arm_b_sh = -0.10
	arm_b_el = 0.40
	leg_f_hip = 0.05
	leg_f_knee = -0.06
	leg_f_foot = 0.12
	leg_b_hip = -0.06
	leg_b_knee = -0.05
	leg_b_foot = 0.10
	aim_angle = 0.0
	bow_offset = 0.0
	bow_draw = 0.0
	bow_off = Vector2.ZERO
	cape[0] = 2.98
	cape[1] = 3.10
	cape[2] = 2.86
	hood[0] = 2.85
	hood[1] = 3.10
	hair[0] = 3.05
	hair[1] = 3.18
	hair[2] = 2.95
	cape_flare = 0.5
	eye_blink = 0.0
	wind_glow = 0.0
	focus_glow = 0.0
	windrun = 0.0
	channel = 0.0
	hurt_tint = 0.0
	alpha = 1.0
	tether_on = false
	tether_alpha = 0.0
	tether_local = Vector2.ZERO
	aim_point_local = Vector2.ZERO
