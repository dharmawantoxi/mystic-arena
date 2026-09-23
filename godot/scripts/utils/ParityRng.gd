# ParityRng.gd — kanal RNG terkontrol untuk harness paritas damage.
#
# Mengapa ada: oracle pygame (tools/test_godot_match_parity.py, seksi
# `hero_rng_guards` dan `item_procs`) menjalankan take_damage/_do_attack/
# inv.update pygame ASLI dengan `random.random` DI-MONKEYPATCH per situs
# roll (basename file + nama fungsi: _entity.py::take_damage,
# hero_items.py::roll_crit/_on_hit_common/notify_damage_taken, dan
# base_boss.py::take_damage). GDScript tidak punya monkeypatch, jadi roll
# combat yang mau di-parity-kan lewat pintu ini:
#
#   CombatSystem.apply_damage : windrun 75%, evasion/blind hero, block item,
#                               blind BOSS (base_boss.take_damage)
#   ItemInventory.roll_crit   : crit Dead Edge
#   ItemInventory proc        : bash Abyss Breaker, pierce bash Sundering
#                               Cudgel, chain Fenrir/Thunder, multishot
#                               Polycephaly, static charge Thunder Coil
#                               (on-damage)
#
# Perilaku produksi TIDAK berubah: tanpa begin() -> next() = randf()
# global persis seperti sebelumnya (hanya lewat pintu yang sama). Harness
# (HeroRngGuardParityTest / ItemProcParityTest) memasang script lewat
# begin() dengan urutan nilai roll dari fixture — termasuk script KOSONG
# (nol roll diharapkan: roll apa pun di luar itu dicatat sebagai roll
# liar). end() mengembalikan nilai yang BENAR-BENAR dikonsumsi; jumlah,
# nilai, dan urutan dibandingkan dengan oracle, jadi roll yang hilang /
# bertambah / tertukar urutan di salah satu engine gagal tes.
#
# Roll yang SENGAJA tidak lewat pintu ini (masih randf() langsung, belum
# di-parity-kan — lihat docs/AUDIT_ULANG_DARI_AWAL.md): sebaran posisi damage
# number (visual).
extends RefCounted
class_name ParityRng

static var _active := false
static var _script: Array = []
static var _pos := 0
static var _consumed: Array = []


## Pasang script roll (dipakai harness parity). Nilai diambil berurutan
## oleh next() sampai end() melepasnya. Script kosong = nol roll yang
## diharapkan (bukan mode produksi).
static func begin(values: Array) -> void:
	_active = true
	_script = values.duplicate()
	_pos = 0
	_consumed = []


## Lepas script; kembalikan daftar nilai yang terkonsumsi sejak begin().
static func end() -> Array:
	var out := _consumed.duplicate()
	_active = false
	_script = []
	_pos = 0
	_consumed = []
	return out


## Satu-satunya pintu roll combat parity: tanpa begin() = randf() global.
## Script habis saat aktif = roll combat tak terduga (urutan roll Godot
## != oracle) — nilai liar tetap dicatat supaya selisih jumlah terdeteksi.
static func next() -> float:
	if not _active:
		return randf()
	if _pos >= _script.size():
		push_error("[ParityRng] script habis: roll combat tak terduga "
			+ "(urutan/jumlah roll Godot != oracle pygame)")
		var stray := randf()
		_consumed.append(stray)
		return stray
	var v := float(_script[_pos])
	_pos += 1
	_consumed.append(v)
	return v
