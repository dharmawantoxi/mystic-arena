class_name LightingResampler
extends RefCounted

## Integer RGB resampling matching pygame.transform.smoothscale's GENERIC path.
## Separable X then Y, with byte truncation after each axis. Expansion uses
## 16.16 bilinear weights; shrinking uses pygame's area accumulator. This is
## deliberately not Godot's Image.resize filter, which rounds differently.
const FIXED := 65536
const CHANNELS := 3


static func resize(
	source: PackedByteArray, width: int, height: int, size: Vector2i
) -> PackedByteArray:
	if width <= 0 or height <= 0 or size.x <= 0 or size.y <= 0:
		return PackedByteArray()
	if source.size() != width * height * CHANNELS:
		return PackedByteArray()
	var result := source
	if size.x != width:
		result = _resize_x(result, width, height, size.x)
	if size.y != height:
		result = _resize_y(result, size.x, height, size.y)
	return result


static func _resize_x(
	source: PackedByteArray, width: int, height: int, target: int
) -> PackedByteArray:
	return (
		_expand_x(source, width, height, target)
		if target > width
		else _shrink_x(source, width, height, target)
	)


static func _resize_y(
	source: PackedByteArray, width: int, height: int, target: int
) -> PackedByteArray:
	return (
		_expand_y(source, width, height, target)
		if target > height
		else _shrink_y(source, width, height, target)
	)


static func _expand_x(
	source: PackedByteArray, width: int, height: int, target: int
) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(target * height * CHANNELS)
	for y in range(height):
		for x in range(target):
			var product := x * (width - 1)
			var index := floori(float(product) / target)
			var weight1 := floori(float(FIXED * (product % target)) / target)
			var weight0 := FIXED - weight1
			var src := (y * width + index) * CHANNELS
			var dst := (y * target + x) * CHANNELS
			for channel in range(CHANNELS):
				out[dst + channel] = (
					(source[src + channel] * weight0 + source[src + CHANNELS + channel] * weight1)
					>> 16
				)
	return out


static func _expand_y(
	source: PackedByteArray, width: int, height: int, target: int
) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(width * target * CHANNELS)
	for y in range(target):
		var product := y * (height - 1)
		var index := floori(float(product) / target)
		var weight1 := floori(float(FIXED * (product % target)) / target)
		var weight0 := FIXED - weight1
		for x in range(width):
			var src := (index * width + x) * CHANNELS
			var dst := (y * width + x) * CHANNELS
			for channel in range(CHANNELS):
				out[dst + channel] = (
					(
						source[src + channel] * weight0
						+ source[src + width * CHANNELS + channel] * weight1
					)
					>> 16
				)
	return out


static func _shrink_x(
	source: PackedByteArray, width: int, height: int, target: int
) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(target * height * CHANNELS)
	var space := floori(float(FIXED * width) / target)
	var reciprocal := floori(4294967296.0 / space)
	for y in range(height):
		var accumulate := [0, 0, 0]
		var counter := space
		var dst := y * target * CHANNELS
		for x in range(width):
			var src := (y * width + x) * CHANNELS
			if counter > FIXED:
				for channel in range(CHANNELS):
					accumulate[channel] += source[src + channel]
				counter -= FIXED
			else:
				var fraction := FIXED - counter
				for channel in range(CHANNELS):
					var value: int = accumulate[channel] + ((source[src + channel] * counter) >> 16)
					out[dst] = (value * reciprocal) >> 16
					dst += 1
					accumulate[channel] = (source[src + channel] * fraction) >> 16
				counter = space - fraction
	return out


static func _shrink_y(
	source: PackedByteArray, width: int, height: int, target: int
) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(width * target * CHANNELS)
	var space := floori(float(FIXED * height) / target)
	var reciprocal := floori(4294967296.0 / space)
	var stride := width * CHANNELS
	var accumulate := PackedInt32Array()
	accumulate.resize(stride)
	var counter := space
	var dst_row := 0
	for y in range(height):
		var src_row := y * stride
		if counter > FIXED:
			for index in range(stride):
				accumulate[index] += source[src_row + index]
			counter -= FIXED
		else:
			var fraction := FIXED - counter
			var dst := dst_row * stride
			for index in range(stride):
				var value: int = accumulate[index] + ((source[src_row + index] * counter) >> 16)
				out[dst + index] = (value * reciprocal) >> 16
				accumulate[index] = (source[src_row + index] * fraction) >> 16
			dst_row += 1
			counter = space - fraction
	return out
