# L36-hero-shrine.gd — Paritas Visual & Logika Hero Shrine 1:1 Pygame (_core.py & HeroShop)
# 6 Hero Starter: Kaizen, Grimjaw, Sylara, Vex, Thorne, Zephyr
# Format Kartu Compact Horizontal (480x145 px): Portrait, Title, Role Chip, Stats (HP/DMG/RNG/SPD), Skill Preview, Action Button (ACTIVE / REKRUT / GOLD -).
# Logika Ganti Hero: transfer inventori item + pasang base stat + reset stat lama + re-apply item stat bonuses + heal penuh + ganti skill kit QWER.

const HERO_CATALOG := {
	"kaizen": {
		"name": "Kaizen",
		"title": "The Wind Blade",
		"role": "ASSASSIN",
		"cost": 100,
		"hp": 550,
		"dmg": 35,
		"range": 90,
		"speed": 120.0,
		"color": Color8(100, 200, 255),
		"glow": Color8(140, 220, 255),
		"skills": ["Wind Slash", "Swift Dash", "Blade Ward", "Storm Gale"],
		"short": ["Slash", "Dash", "Ward", "Gale"],
		"cds": [4.0, 8.0, 7.0, 15.0],
		"desc": "Assassin lincah dengan tebasan beruntun mematikan."
	},
	"grimjaw": {
		"name": "Grimjaw",
		"title": "The Berserker",
		"role": "FIGHTER",
		"cost": 120,
		"hp": 800,
		"dmg": 33,
		"range": 85,
		"speed": 115.0,
		"color": Color8(200, 80, 40),
		"glow": Color8(255, 120, 80),
		"skills": ["Blade Fury", "Blood Rage", "Earth Smash", "Berserk"],
		"short": ["Fury", "Rage", "Smash", "Berserk"],
		"cds": [5.0, 9.0, 8.0, 18.0],
		"desc": "Petarung buas dengan putaran pedang area dan amukan darah."
	},
	"sylara": {
		"name": "Sylara",
		"title": "The Wind Ranger",
		"role": "MARKSMAN",
		"cost": 110,
		"hp": 470,
		"dmg": 45,
		"range": 130,
		"speed": 120.0,
		"color": Color8(100, 220, 120),
		"glow": Color8(150, 255, 170),
		"skills": ["Focus Fire", "Wind Run", "Powershot", "Gale Arrow"],
		"short": ["Focus", "Run", "Shot", "Arrow"],
		"cds": [4.0, 7.0, 6.0, 14.0],
		"desc": "Pemanah jarak jauh dengan tembakan menembus dan kelincahan angin."
	},
	"vex": {
		"name": "Vex",
		"title": "The Void Harbinger",
		"role": "MAGE",
		"cost": 130,
		"hp": 520,
		"dmg": 34,
		"range": 115,
		"speed": 110.0,
		"color": Color8(160, 120, 255),
		"glow": Color8(200, 160, 255),
		"skills": ["Arcane Orb", "Void Rift", "Null Field", "Supernova"],
		"short": ["Orb", "Rift", "Field", "Nova"],
		"cds": [3.5, 8.0, 10.0, 16.0],
		"desc": "Penyihir kehampaan dengan daya ledak magis burst dahsyat."
	},
	"thorne": {
		"name": "Thorne",
		"title": "The Quill Sprayer",
		"role": "TANK",
		"cost": 140,
		"hp": 1400,
		"dmg": 32,
		"range": 75,
		"speed": 105.0,
		"color": Color8(215, 155, 30),
		"glow": Color8(255, 200, 80),
		"skills": ["Viscous Nose", "Quill Spray", "Bristleback", "Warpath"],
		"short": ["Goo", "Spray", "Spikes", "Warpath"],
		"cds": [4.5, 6.0, 8.0, 20.0],
		"desc": "Tank berduri tebal yang membalas serangan dan memperlambat musuh."
	},
	"zephyr": {
		"name": "Zephyr",
		"title": "Meander of Mischief",
		"role": "TRICKSTER",
		"cost": 120,
		"hp": 520,
		"dmg": 27,
		"range": 120,
		"speed": 130.0,
		"color": Color8(215, 60, 90),
		"glow": Color8(255, 100, 130),
		"skills": ["Bramble Maze", "Shadow Realm", "Cursed Crown", "Bedlam"],
		"short": ["Maze", "Shadow", "Crown", "Bedlam"],
		"cds": [5.0, 8.0, 9.0, 15.0],
		"desc": "Peri pengacau cepat dengan jebakan duri rantai dan ilusi bayangan."
	}
}
