extends RefCounted
class_name CombatCalc
## L37 — Formula armor 1:1 dengan pygame (_entity.py:4653/5814/1067).
##
##   armor > 0  →  red  = armor*0.06 / (1 + armor*0.06)
##                 damage = max(1, int(round(damage * (1 - red))))
##   armor < 0  →  bonus = min(1.0, -armor*0.06)   (korosi/aura, maks +100%)
##                 damage = int(round(damage * (1 + bonus)))
##   armor = 0  →  damage utuh.
##
## Dipanggil dari take_damage() Hero/Minion/Tower/Nexus. Yang memutuskan KAPAN
## armor berlaku adalah PEMANGGIL (gate `school`), meniru aturan pygame:
##   - target HERO    : semua damage non-'fire' kena armor (gate damage_type)
##   - target MINION  : hanya school "physical" (auto-attack hero)
##   - target TOWER   : hanya school "physical" (auto-attack hero)
##   - tembakan menara / pukulan minion (tanpa school) TIDAK pernah kena
##     armor target — paritas resolve_damage_school() yang mengembalikan None.
##   - skill hero pakai school "magic" → tembus armor (magic_resist semua
##     target port ini = 0, jadi angka skill tetap penuh seperti sekarang).

const LOG_HITS := false # set true untuk melihat angka armor di panel Output


static func mitigate(damage: float, armor: float) -> float:
	if damage <= 0.0 or armor == 0.0:
		return damage
	var out: float
	if armor > 0.0:
		var red := armor * 0.06 / (1.0 + armor * 0.06)
		out = float(maxi(1, int(round(damage * (1.0 - red)))))
	else:
		var bonus: float = minf(1.0, -armor * 0.06)
		out = float(int(round(damage * (1.0 + bonus))))
	if LOG_HITS and out != damage:
		print("[Armor] " + str(damage) + " -> " + str(int(out)) + " (armor " + str(armor) + ")")
	return out
