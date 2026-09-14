# KaizenPose.gd — data pose tunggal rig Kaizen (v4 rebuild).
#
# Satu pose = semua sudut/offset yang dibutuhkan KaizenRenderer untuk
# menggambar karakter. Animator memproduksi pose target tiap frame; root
# (KaizenSkeleton.gd) me-lerp pose sekarang menuju target supaya transisi
# antar-state halus (tidak robotic).
#
# Konvensi sudut:
#   * torso/kepala/lengan/kaki: 0 = lurus ke bawah / tegak, positif = ke
#     depan (+x lokal). Semua radian.
#   * weapon_angle: arah bilah ABSOLUT, 0 = +x (depan), positif = naik
#     (CCW di layar, karena y-down).
#   * scarf/pony/band: arah absolut segmen, 0 = +x, PI = belakang,
#     positif turun (y-down standar).
class_name KaizenPose
extends RefCounted

# ── Root / tubuh ──
var root_x := 0.0          # pergeseran pinggul (lunge serangan, dsb.)
var root_y := 0.0          # naik/turun pinggul (bob napas, crouch)
var torso_lean := 0.0      # kemiringan tulang punggung dari vertikal
var chest_flex := 0.0      # tambahan flex dada (membungkuk/menengadah)
var head_lean := 0.0       # relatif dada; positif = menunduk ke depan

# ── Lengan (depan = sisi pedang) ──
var arm_f_sh := 0.12       # bahu: 0 = lurus bawah, + = ke depan
var arm_f_el := 0.55       # siku: tekuk relatif lengan atas
var arm_b_sh := -0.10
var arm_b_el := 0.40

# ── Kaki ──
var leg_f_hip := 0.05
var leg_f_knee := -0.06
var leg_f_foot := 0.12     # sudut telapak (0 = datar ke depan)
var leg_b_hip := -0.06
var leg_b_knee := -0.05
var leg_b_foot := 0.10

# ── Senjata ──
var weapon_angle := -0.55  # santai: bilah menunjuk depan-bawah
var weapon_off := Vector2.ZERO  # offset grip tambahan (dipakai skill)

# ── Secondary motion: arah absolut tiap segmen (rad, y-down) ──
var scarf: Array = [2.98, 3.10, 2.86]
var pony: Array = [3.05, 3.18, 2.95]
var band: Array = [2.85, 3.10]

# ── Ekspresi / flare ──
var skirt_flare := 0.5     # lebar bukaan hakama (px ekstra di hem)
var eye_blink := 0.0       # 0 = terbuka, 1 = tertutup
var wind_glow := 0.0       # intensitas aksen sihir angin (0..1)
var hurt_tint := 0.0       # kilatan merah saat kena pukul (0..1)
var alpha := 1.0           # seluruh rig (death fade)
var trail := false         # aktifkan jejak bilah (swing)
