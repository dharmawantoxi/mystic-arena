# SylaraPose.gd — data pose tunggal rig Sylara (v2 rebuild).
#
# Satu pose = semua sudut/offset yang dibutuhkan SylaraRenderer untuk
# menggambar karakter. Animator memproduksi pose target tiap frame; root
# (SylaraSkeleton.gd) me-lerp pose sekarang menuju target supaya transisi
# antar-state halus (tidak robotic).
#
# Konvensi sudut (radian, y-down standar Godot):
#   * torso/kepala/lengan/kaki: 0 = lurus ke bawah, positif = ke depan (+x).
#   * bow_angle: arah busur ABSOLUT, 0 = +x (depan), positif = naik (CCW layar).
#   * bow_draw: 0.0 = santai, 1.0 = tali tertarik penuh.
#   * cape/hood/hair: arah absolut segmen, 0 = +x, PI = belakang.
class_name SylaraPose
extends RefCounted

# ── Root / tubuh ──
var root_x := 0.0          # pergeseran pinggul (lunge, recoil)
var root_y := 0.0          # naik/turun pinggul (bob napas, crouch)
var torso_lean := 0.0      # kemiringan tulang punggung dari vertikal
var chest_flex := 0.0      # tambahan flex dada (membungkuk/menengadah)
var head_lean := 0.0       # relatif dada; positif = menunduk ke depan
var look := 0.0            # drift pandangan idle (-1..1)

# ── Lengan (depan = sisi busur / grip hand) ──
var arm_f_sh := 0.12       # bahu: 0 = lurus bawah, + = ke depan
var arm_f_el := 0.55       # siku: tekuk relatif lengan atas
var arm_b_sh := -0.10      # bahu belakang (sisi tarik tali)
var arm_b_el := 0.40       # siku belakang

# ── Kaki (di-lerp oleh root; sumber = solver kaki Animator) ──
var leg_f_hip := 0.05
var leg_f_knee := -0.06
var leg_f_foot := 0.12     # sudut telapak (0 = datar ke depan)
var leg_b_hip := -0.06
var leg_b_knee := -0.05
var leg_b_foot := 0.10
## Intensitas debu kontak kaki (0..1) — renderer menggambar puff kecil
## di telapak yang baru menapak.
var dust := 0.0

# ── Busur (senjata utama) ──
var bow_angle := -0.35     # arah busur (0 = +x, positif = CCW layar)
var bow_draw := 0.0        # tarikan tali 0..1 (0 = rileks, 1 = full draw)
var bow_off := Vector2.ZERO  # offset grip tambahan (dipakai skill)
var shiver := 0.0          # getar tali pasca-release (0..1, meluruh)
var charge := 0.0          # intensitas charge skill R (getar busur 0..1)

# ── Secondary motion: arah absolut tiap segmen (rad, y-down) ──
var cape: Array[float] = [2.98, 3.10, 2.86]     # 3 segmen cape
var hood: Array[float] = [2.85, 3.10]           # 2 segmen hood edges
var hair: Array[float] = [3.05, 3.18, 2.95]     # 3 segmen rambut

# ── Ekspresi / flare ──
var cape_flare := 0.5      # lebar bukaan cape (px ekstra di hem)
var eye_blink := 0.0       # 0 = terbuka, 1 = tertutup
var wind_glow := 0.0       # intensitas aksen sihir angin (0..1)
var hurt_tint := 0.0       # kilatan merah saat kena pukul (0..1)
var alpha := 1.0           # seluruh rig (death fade)
var trail := false         # aktifkan jejak busur (swing/melee riposte)
