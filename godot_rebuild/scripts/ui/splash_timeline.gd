extends RefCounted
## Port of `splash_screen.py` (layer 9at): the boot splash timeline, baked
## background, particle motion and layout - every number the source uses.
##
## Fade in 0.4 s, title fade from 0.5 s over 0.6 s, fade out over the last
## 0.45 s of SPLASH_DURATION (3 s); a tap sets `skipped` and the splash is
## done once ELAPSED (since boot, not since the tap) reaches 0.25 s, with the
## fade `1 - elapsed / 0.25` (so a late tap is an immediate cut - source
## behaviour kept). The logo fits a 340x320 box and grows from 85 % to 100 %
## over 0.9 s in 5 % steps. Pure and clock-free: the Control feeds `dt`.

const GAME_NAME := "MYSTIC ARENA"
const SUBTITLE := "A MOBA TOWER DEFENSE ADVENTURE"
const HINT := "Tap anywhere to skip"
const DURATION := 3.0
const SKIP_FADE := 0.25
const FADE_IN := 0.4
const FADE_OUT := 0.45
const TITLE_DELAY := 0.5
const TITLE_FADE := 0.6
const MAX_DT := 0.05
const PARTICLE_COUNT := 46
const LOGO_BOX := Vector2(340.0, 320.0)
const LOGO_GROW_TIME := 0.9
const LOGO_LIFT := 26
const GLOW_PAD := 30
const TITLE_SIZE := 92
const TITLE_BELOW_SIZE := 66
const SUB_SIZE := 22
const HINT_SIZE := 16
const HINT_ALPHA := 140
const VIGNETTE_MAX := 140
const GRADIENT_STEPS := 48

const ACCENT := Color8(255, 190, 60)
const ACCENT_2 := Color8(200, 140, 255)
const TEXT_MAIN := Color8(245, 240, 230)
const TEXT_DIM := Color8(160, 155, 170)
const BG_TOP := Vector3i(8, 8, 18)
const BG_MID := Vector3i(22, 16, 38)
const BG_BOTTOM := Vector3i(6, 6, 14)
const PARTICLE_PALETTE := [
	Color8(255, 210, 120), Color8(230, 160, 255), Color8(255, 245, 230), Color8(180, 200, 255)
]


static func overall_alpha(elapsed: float, skipped: bool) -> float:
	var fade_in := minf(1.0, elapsed / FADE_IN)
	var fade_out := 0.0
	if skipped:
		fade_out = maxf(0.0, 1.0 - elapsed / SKIP_FADE)
	else:
		fade_out = minf(1.0, maxf(0.0, (DURATION - elapsed) / FADE_OUT))
	return clampf(fade_in * fade_out, 0.0, 1.0)


static func title_alpha(elapsed: float) -> int:
	if elapsed < TITLE_DELAY:
		return 0
	return int(255.0 * minf(1.0, (elapsed - TITLE_DELAY) / TITLE_FADE))


static func is_done(elapsed: float, skipped: bool) -> bool:
	return elapsed >= (SKIP_FADE if skipped else DURATION)


## `_make_particles`: 46 drifting dots; `rng` must be seeded by the caller.
static func make_particles(width: float, height: float, rng: RandomNumberGenerator) -> Array:
	var particles: Array = []
	for _index in range(PARTICLE_COUNT):
		(
			particles
			. append(
				{
					"x": rng.randf_range(0.0, width),
					"y": rng.randf_range(0.0, height),
					"r": rng.randf_range(0.6, 2.4),
					"speed": rng.randf_range(0.08, 0.35),
					"drift": rng.randf_range(-0.12, 0.12),
					"phase": rng.randf_range(0.0, TAU),
					"color": PARTICLE_PALETTE[rng.randi_range(0, PARTICLE_PALETTE.size() - 1)],
				}
			)
		)
	return particles


## One `update` step of the particle field (after `elapsed` was advanced).
## A particle leaving the top re-enters at the bottom with a fresh x from
## `rng` (null keeps x, for deterministic replays).
static func step_particles(
	particles: Array, elapsed: float, width: float, height: float, rng: RandomNumberGenerator
) -> void:
	for particle_value in particles:
		var p: Dictionary = particle_value
		p["y"] = float(p["y"]) - float(p["speed"])
		p["x"] = (float(p["x"]) + float(p["drift"]) + sin(elapsed * 0.8 + float(p["phase"])) * 0.05)
		if float(p["y"]) < -6.0:
			p["y"] = height + 6.0
			if rng != null:
				p["x"] = rng.randf_range(0.0, width)


## Draw colour of a particle at `elapsed` (twinkle 35 %..100 %).
static func particle_color(particle: Dictionary, elapsed: float) -> Color:
	var tw := 0.5 + 0.5 * sin(elapsed * 2.5 + float(particle["phase"]))
	var base: Color = particle["color"]
	var k := 0.35 + 0.65 * tw
	return Color8(int(base.r8 * k), int(base.g8 * k), int(base.b8 * k))


static func particle_radius(particle: Dictionary) -> int:
	return maxi(1, int(float(particle["r"])))


## Baked gradient rows: 48 bands top -> mid (55 %) -> bottom.
static func gradient_rows(width: int, height: int) -> Array:
	var rows: Array = []
	var step := maxi(1, height / GRADIENT_STEPS)
	var y := 0
	while y < height:
		var f := float(y) / float(height)
		var color := Vector3i()
		if f < 0.55:
			var f2 := f / 0.55
			color = Vector3i(
				int(BG_TOP.x + (BG_MID.x - BG_TOP.x) * f2),
				int(BG_TOP.y + (BG_MID.y - BG_TOP.y) * f2),
				int(BG_TOP.z + (BG_MID.z - BG_TOP.z) * f2)
			)
		else:
			var f2 := (f - 0.55) / 0.45
			color = Vector3i(
				int(BG_MID.x + (BG_BOTTOM.x - BG_MID.x) * f2),
				int(BG_MID.y + (BG_BOTTOM.y - BG_MID.y) * f2),
				int(BG_MID.z + (BG_BOTTOM.z - BG_MID.z) * f2)
			)
		rows.append({"rect": Rect2i(0, y, width, step), "color": Color8(color.x, color.y, color.z)})
		y += step
	return rows


## Vignette rings, outermost first: inset i (140 -> 2 step 2) with alpha
## min(255, int(2.2 * (140 - i))) black overlays.
static func vignette_rings() -> Array:
	var rings: Array = []
	var inset := VIGNETTE_MAX
	while inset > 0:
		rings.append({"inset": inset, "alpha": mini(255, int(2.2 * float(VIGNETTE_MAX - inset)))})
		inset -= 2
	return rings


## Alpha of the vignette at a pixel whose distance to the nearest edge is
## `d`. `pygame.draw.rect` does NOT blend on the SRCALPHA surface: every ring
## overwrites the pixels it covers, so the last ring drawn over a pixel (the
## smallest inset <= d, i.e. inset 2 with alpha 255 for any d >= 2) wins.
## Net effect in the source: the baked backdrop is black except a 2 px
## gradient border - kept as-is for parity.
static func vignette_alpha(d: int) -> int:
	var alpha := 0
	for ring_value in vignette_rings():
		var ring: Dictionary = ring_value
		if int(ring["inset"]) <= d:
			alpha = int(ring["alpha"])
	return alpha


static func vignette_factor(d: int) -> float:
	return 1.0 - float(vignette_alpha(d)) / 255.0


static func logo_scaled_size(image_size: Vector2i) -> Vector2i:
	var scale := minf(minf(LOGO_BOX.x / float(image_size.x), LOGO_BOX.y / float(image_size.y)), 1.0)
	return Vector2i(
		maxi(1, int(float(image_size.x) * scale)), maxi(1, int(float(image_size.y) * scale))
	)


## 0.85 -> 1.0 over 0.9 s, quantised to 1/20 with Python's half-even round.
static func logo_grow(elapsed: float) -> float:
	var grow := minf(1.0, elapsed / LOGO_GROW_TIME)
	return _round_half_even((0.85 + 0.15 * grow) * 20.0) / 20.0


## Python `round()` (banker's rounding) for the grow quantisation.
static func _round_half_even(value: float) -> float:
	var base := floorf(value)
	var diff := value - base
	if diff > 0.5:
		return base + 1.0
	if diff < 0.5:
		return base
	return base if fmod(base, 2.0) == 0.0 else base + 1.0


static func logo_grown_size(base: Vector2i, gq: float) -> Vector2i:
	return Vector2i(maxi(1, int(float(base.x) * gq)), maxi(1, int(float(base.y) * gq)))


static func glow_radius(logo: Vector2i) -> int:
	return maxi(logo.x, logo.y) / 2 + GLOW_PAD


static func glow_rings(logo: Vector2i) -> Array:
	var radius := glow_radius(logo)
	var rings: Array = []
	var g := radius
	while g > 0:
		rings.append({"g": g, "alpha": int(12.0 * (1.0 - float(g) / float(radius)))})
		g -= 3
	return rings


static func _centered(center: Vector2i, size: Vector2i) -> Rect2i:
	return Rect2i(center.x - size.x / 2, center.y - size.y / 2, size.x, size.y)


## Layout of one frame. `measure(text, size) -> Vector2i` gives text boxes;
## `logo_base` is the fitted logo size or Vector2i.ZERO when no logo exists.
static func layout(
	elapsed: float, skipped: bool, width: int, height: int, logo_base: Vector2i, measure: Callable
) -> Dictionary:
	var a := overall_alpha(elapsed, skipped)
	var ta := int(float(title_alpha(elapsed)) * a)
	var cx := width / 2
	var base_y := height / 2
	var out := {
		"alpha": a, "title_alpha": ta, "drawn": a > 0.001, "has_logo": logo_base != Vector2i.ZERO
	}
	var title_center := Vector2i(cx, base_y)
	var sub_center := Vector2i(cx, base_y + 66)
	var title_size := TITLE_SIZE
	if logo_base != Vector2i.ZERO:
		var grown := logo_grown_size(logo_base, logo_grow(elapsed))
		var logo_rect := _centered(Vector2i(cx, base_y - LOGO_LIFT), grown)
		out["logo_rect"] = logo_rect
		out["logo_alpha"] = ta
		var radius := glow_radius(grown)
		out["glow_center"] = Vector2i(cx, logo_rect.position.y + logo_rect.size.y / 2)
		out["glow_radius"] = radius
		title_center = Vector2i(cx, logo_rect.end.y + 46)
		sub_center = Vector2i(cx, logo_rect.end.y + 88)
		title_size = TITLE_BELOW_SIZE
	var title_box: Vector2i = measure.call(GAME_NAME, title_size)
	var title_rect := _centered(title_center, title_box)
	out["title_rect"] = title_rect
	out["title_size"] = title_size
	out["sub_rect"] = _centered(sub_center, measure.call(SUBTITLE, SUB_SIZE))
	out["hint_rect"] = _centered(Vector2i(cx, height - 48), measure.call(HINT, HINT_SIZE))
	out["hint_alpha"] = int(float(HINT_ALPHA) * a)
	var lines: Array = []
	if ta > 0:
		var gap := title_rect.size.x / 2 + 18
		var y := title_rect.position.y + title_rect.size.y / 2
		var fac := (float(ta) / 255.0) * 0.85
		for pair in [[-6, ACCENT], [6, ACCENT_2]]:
			var off := int(pair[0])
			var col: Color = pair[1]
			var line_color := Color8(int(col.r8 * fac), int(col.g8 * fac), int(col.b8 * fac))
			(
				lines
				. append(
					{
						"color": line_color,
						"a": Vector2i(cx - gap, y + off),
						"b": Vector2i(cx - gap + 46, y + off),
					}
				)
			)
			(
				lines
				. append(
					{
						"color": line_color,
						"a": Vector2i(cx + gap, y + off),
						"b": Vector2i(cx + gap - 46, y + off),
					}
				)
			)
	out["lines"] = lines
	return out
