extends RefCounted
class_name MapTheme
## Langkah 13: palet map persis themes.py pygame (Color8 = RGB 0-255).

static func get_theme(theme_name: String) -> Dictionary:
	match theme_name:
		"desert":
			return {
				"name": "Desert",
				"r1": Color8(155, 115, 60), "r2": Color8(180, 135, 75),
				"r3": Color8(210, 165, 95), "r4": Color8(230, 190, 120),
				"r_high": Color8(245, 215, 150), "r_moss": Color8(140, 110, 55),
				"d1": Color8(95, 55, 30), "d2": Color8(125, 75, 40),
				"d3": Color8(150, 95, 55), "d4": Color8(175, 120, 75),
				"d_ash": Color8(100, 75, 50), "d_burnt": Color8(60, 35, 20),
				"t1": Color8(135, 100, 60), "t2": Color8(165, 125, 80),
				"p1": Color8(110, 85, 55), "p2": Color8(145, 115, 75),
				"p3": Color8(180, 145, 100), "p4": Color8(215, 180, 130),
				"p_moss": Color8(100, 85, 45), "p_crack": Color8(60, 40, 20),
				"rv_deep": Color8(8, 29, 18), "rv_mid": Color8(25, 79, 34),
				"rv_glow": Color8(150, 220, 68), "rv_foam": Color8(220, 255, 160),
			}
		"volcanic":
			return {
				"name": "Volcanic",
				"r1": Color8(75, 35, 20), "r2": Color8(100, 50, 28),
				"r3": Color8(130, 65, 35), "r4": Color8(160, 85, 45),
				"r_high": Color8(190, 110, 55), "r_moss": Color8(95, 45, 22),
				"d1": Color8(45, 18, 12), "d2": Color8(65, 28, 18),
				"d3": Color8(90, 40, 25), "d4": Color8(115, 55, 32),
				"d_ash": Color8(70, 45, 35), "d_burnt": Color8(30, 12, 8),
				"t1": Color8(85, 42, 25), "t2": Color8(110, 58, 35),
				"p1": Color8(55, 32, 22), "p2": Color8(85, 55, 40),
				"p3": Color8(115, 78, 55), "p4": Color8(145, 100, 70),
				"p_moss": Color8(95, 45, 22), "p_crack": Color8(255, 100, 20),
				"rv_deep": Color8(80, 15, 8), "rv_mid": Color8(180, 55, 12),
				"rv_glow": Color8(255, 180, 60), "rv_foam": Color8(255, 230, 130),
			}
		_:
			return {
				"name": "Forest",
				"r1": Color8(28, 55, 32), "r2": Color8(38, 72, 42),
				"r3": Color8(52, 92, 55), "r4": Color8(68, 115, 70),
				"r_high": Color8(90, 145, 85), "r_moss": Color8(55, 90, 40),
				"d1": Color8(45, 32, 28), "d2": Color8(65, 45, 38),
				"d3": Color8(85, 60, 48), "d4": Color8(105, 78, 62),
				"d_ash": Color8(60, 55, 50), "d_burnt": Color8(30, 20, 18),
				"t1": Color8(55, 55, 42), "t2": Color8(75, 68, 50),
				"p1": Color8(58, 52, 45), "p2": Color8(85, 76, 65),
				"p3": Color8(115, 105, 90), "p4": Color8(145, 130, 108),
				"p_moss": Color8(65, 90, 45), "p_crack": Color8(170, 36, 61),
				"rv_deep": Color8(8, 8, 18), "rv_mid": Color8(35, 12, 34),
				"rv_glow": Color8(177, 46, 75), "rv_foam": Color8(255, 130, 140),
			}
