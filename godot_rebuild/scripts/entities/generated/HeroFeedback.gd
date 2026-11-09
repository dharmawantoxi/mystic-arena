class_name HeroFeedback
extends RefCounted

## Generated game-feel slice only. Do not edit; no particle/rig parity claimed.


static func cast(bus: HeroCombatFeel, hero: String, skill: String) -> void:
	match hero:
		"grimjaw":
			if skill == "q":
				bus.shake(3.0, 0.26)
				bus.hit_stop(0.027)
			else:
				if skill == "w":
					bus.shake(1.0, 0.14)
				else:
					if skill == "e":
						bus.shake(2.0, 0.18)
						bus.hit_stop(0.024)
					else:
						if skill == "r":
							bus.shake(4.0, 0.42)
							bus.hit_stop(0.04)
		"kaizen":
			if skill == "q":
				bus.shake(2.2, 0.2)
				bus.hit_stop(0.021)
			else:
				if skill == "w":
					bus.shake(1.1, 0.14)
				else:
					if skill == "e":
						bus.shake(2.5, 0.22)
						bus.hit_stop(0.024)
					else:
						if skill == "r":
							bus.shake(4.5, 0.4)
							bus.hit_stop(0.04)
		"sylara":
			if skill == "q":
				bus.shake(2.0, 0.18)
				bus.hit_stop(0.02)
			else:
				if skill == "w":
					bus.shake(2.5, 0.22)
				else:
					if skill == "e":
						bus.shake(1.7, 0.18)
					else:
						if skill == "r":
							bus.shake(1.5, 0.2)
		"vex":
			if skill == "q":
				bus.shake(2.1, 0.2)
				bus.hit_stop(0.021)
			else:
				if skill == "w":
					bus.shake(2.8, 0.24)
					bus.hit_stop(0.025)
				else:
					if skill == "e":
						bus.shake(1.7, 0.18)
					else:
						if skill == "r":
							bus.shake(5.5, 0.42)
							bus.hit_stop(0.04)
		"zephyr":
			bus.shake((3.0 if skill != "r" else 7.0), (0.18 if skill != "r" else 0.42))
		_:
			pass


static func impact(bus: HeroCombatFeel, hero: String, power: float, crit: bool) -> void:
	match hero:
		"grimjaw":
			bus.shake(((4.0 + (3.5 * minf(2.0, power))) + (3.0 if crit else 0.0)), (0.18 + (0.08 * minf(2.0, power))))
			bus.hit_stop(((0.038 + (0.02 * minf(1.5, power))) + (0.015 if crit else 0.0)))
		"kaizen":
			bus.shake(((3.6 + (3.2 * minf(2.0, power))) + (2.6 if crit else 0.0)), (0.16 + (0.08 * minf(2.0, power))))
			bus.hit_stop(((0.036 + (0.02 * minf(1.5, power))) + (0.014 if crit else 0.0)))
		"sylara":
			bus.shake(((3.2 + (3.0 * minf(2.0, power))) + (2.6 if crit else 0.0)), (0.16 + (0.08 * minf(2.0, power))))
			bus.hit_stop(((0.034 + (0.02 * minf(1.5, power))) + (0.014 if crit else 0.0)))
		"vex":
			bus.shake(((3.4 + (3.2 * minf(2.0, power))) + (2.6 if crit else 0.0)), (0.16 + (0.08 * minf(2.0, power))))
			bus.hit_stop(((0.036 + (0.02 * minf(1.5, power))) + (0.014 if crit else 0.0)))
		"zephyr":
			bus.shake(((4.0 + (3.5 * minf(2.0, power))) + (3.0 if crit else 0.0)), (0.18 + (0.08 * minf(2.0, power))))
			bus.hit_stop(((0.038 + (0.02 * minf(1.5, power))) + (0.015 if crit else 0.0)))
		_:
			pass


static func projectile_hit(bus: HeroCombatFeel, hero: String, damage: float, crit: bool) -> void:
	match hero:
		"sylara":
			var power := (0.75 + minf(1.7, (float(damage) / 45.0)))
			impact(bus, hero, power, crit)
		"vex":
			var power := (0.75 + minf(1.7, (float(damage) / 42.0)))
			impact(bus, hero, power, crit)
		"zephyr":
			var power := (0.7 + minf(1.6, (float(damage) / 45.0)))
			impact(bus, hero, power, crit)
		_:
			pass
