# SkillBook.gd — FACADE TIPIS untuk HUD (tombol Q/W/E/R + tooltip).
#
# Semua logika skill kini hidup di HeroSkillKit.gd (di-generate 1:1 dari
# hero_skills/_bundle.py oleh tools/gen_hero_skill_kit.py) dan Hero.gd
# (timer frame, auto-cast, CDR + spell vamp — mirror Hero.cast_skill/
# _try_auto_cast _entity.py). Kelas ini TIDAK lagi mengeksekusi cast, tidak
# menyimpan cooldown sendiri, dan tidak punya ticker/durasi: setiap getter
# membacanya LANGSUNG dari state Hero supaya HUD selalu menampilkan angka
# yang sama dengan yang dipakai simulator (satu sumber kebenaran, tanpa
# drift antar-dua-jam-cooldown seperti mesin lama).
#
# Satuan: Hero menyimpan SEMUA timer dalam FRAME (paritas _entity.py);
# facade ini mengonversi ke DETIK hanya untuk tampilan UI.
extends RefCounted

const FPS := 60.0

## Nama skill untuk UI (skill bar / tooltip toko). Nama kelas starter diambil
## dari docstring hero_skills/_bundle.py — sama dengan yang muncul di pygame.
const SKILL_NAMES := {
	"grimjaw": {"q": "Blade Fury", "w": "Healing Ward", "e": "Critical Strike", "r": "Omnislash"},
	"kaizen": {"q": "Steel Wind", "w": "Wind Wall", "e": "Sweep", "r": "Tornado"},
	"sylara": {"q": "Focus Fire", "w": "Windrun", "e": "Shackle Shot", "r": "Powershot"},
	"thorne": {"q": "Viscous Nose", "w": "Bristleback", "e": "Quill Spray", "r": "Warpath"},
	"vex": {"q": "Arcane Orb", "w": "Sanity's Eclipse", "e": "Astral Imprisonment", "r": "Essence Flux"},
	"zephyr": {"q": "Bramble Maze", "w": "Shadow Realm", "e": "Casket Curse", "r": "Bedlam"},
}
const GENERIC_SKILL_NAMES := {"q": "Strike", "w": "Surge", "e": "Blink", "r": "Cataclysm"}

var hero = null


func _init(p_hero = null) -> void:
	hero = p_hero


## Dipanggil dari Hero._ready/apply_hero_data. Tidak ada state yang harus
## disiapkan — facade hanya mengikat referensi hero (kontrak lama dijaga).
func setup(p_hero) -> void:
	hero = p_hero


# ══════════════════════════════════════════════════════════
#  COOLDOWN — dibaca langsung dari field frame Hero
# ══════════════════════════════════════════════════════════

func _cd_frames(key: String) -> int:
	if hero == null or not is_instance_valid(hero):
		return 0
	match key:
		"q":
			return int(hero.skill_timer)
		"w":
			return int(hero.w_cooldown)
		"e":
			return int(hero.e_cooldown)
		"r":
			return int(hero.r_cooldown)
	return 0


func _cd_max_frames(key: String) -> int:
	if hero == null or not is_instance_valid(hero):
		return 300
	match key:
		"q":
			return int(hero.skill_cooldown_max)
		"w":
			return int(hero.w_cooldown_max)
		"e":
			return int(hero.e_cooldown_max)
		"r":
			return int(hero.r_cooldown_max)
	return 300


## Paritas Hero.is_skill_ready (_entity.py) — siap = timer 0.
func is_ready(key: String) -> bool:
	if hero == null or not is_instance_valid(hero):
		return false
	return bool(hero.is_skill_ready(key))


func cooldown_remaining(key: String) -> float:
	return float(maxi(0, _cd_frames(key))) / FPS


## 0 = siap, 1 = baru mulai cooldown (untuk gambar busur di SkillButton).
func cooldown_ratio(key: String) -> float:
	var mx := maxi(1, _cd_max_frames(key))
	return clampf(float(maxi(0, _cd_frames(key))) / float(mx), 0.0, 1.0)


## Indikator charge: satu-satunya state "menunggu" yang punya pygame adalah
## Sylara powershot (h._powershot_charging, hero_skills/_bundle.py:4403),
## jadi tombol "..." hanya menyala di R selama charge berjalan.
func is_charging(key: String) -> bool:
	if hero == null or not is_instance_valid(hero) or key != "r":
		return false
	return bool(hero.kit.get("_powershot_charging", false))


## Nama skill untuk UI. Kaizen Q bergantian Steel Wind / Dash Strike
## (paritas h._q_stack di _bundle.py:4036-4043); hero tanpa tabel
## memakai nama generik.
func skill_label(key: String) -> String:
	if hero == null or not is_instance_valid(hero):
		return str(GENERIC_SKILL_NAMES.get(key, key.to_upper()))
	var htype := str(hero.hero_type)
	if key == "q" and htype == "kaizen" \
			and int(hero.kit.get("_q_stack", 0)) % 2 == 1:
		return "Dash Strike"
	var table: Dictionary = SKILL_NAMES.get(htype, {})
	if table.has(key):
		return str(table[key])
	return str(GENERIC_SKILL_NAMES.get(key, key.to_upper()))
