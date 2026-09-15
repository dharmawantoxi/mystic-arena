# SylaraSpriteSetup.gd - Configures SpriteFrames for Sylara's sprite-based animations
#
# Loads sprite strips and creates animations for AnimatedSprite2D.
# Each strip is a horizontal spritesheet with multiple frames.
extends Resource

class_name SylaraSpriteSetup

# Animation definitions: [strip_path, frame_count, fps, loop]
const ANIMATIONS := {
	"idle": {
		"strip": "res://assets/units/sylara_idle_strip.png",
		"frames": 8,
		"fps": 8.0,
		"loop": true
	},
	"walk": {
		"strip": "res://assets/units/sylara_walk_strip.png",
		"frames": 8,
		"fps": 10.0,
		"loop": true
	},
	"run": {
		"strip": "res://assets/units/sylara_run_strip.png",
		"frames": 8,
		"fps": 12.0,
		"loop": true
	},
	"attack": {
		"strip": "res://assets/units/sylara_attack_strip.png",
		"frames": 8,
		"fps": 15.0,
		"loop": false
	},
	"swing": {
		"strip": "res://assets/units/sylara_swing_strip.png",
		"frames": 6,
		"fps": 12.0,
		"loop": false
	},
	"skill_q": {
		"strip": "res://assets/units/sylara_skill_q_strip.png",
		"frames": 10,
		"fps": 15.0,
		"loop": false
	},
	"skill_w": {
		"strip": "res://assets/units/sylara_skill_w_strip.png",
		"frames": 8,
		"fps": 10.0,
		"loop": false
	},
	"skill_e": {
		"strip": "res://assets/units/sylara_skill_e_strip.png",
		"frames": 8,
		"fps": 12.0,
		"loop": false
	},
	"skill_r": {
		"strip": "res://assets/units/sylara_skill_r_strip.png",
		"frames": 12,
		"fps": 12.0,
		"loop": false
	},
	"hurt": {
		"strip": "res://assets/units/sylara_hurt_strip.png",
		"frames": 4,
		"fps": 10.0,
		"loop": false
	}
}


static func create_sprite_frames() -> SpriteFrames:
	var sprite_frames := SpriteFrames.new()
	
	# Remove default "default" animation
	if sprite_frames.has_animation("default"):
		sprite_frames.remove_animation("default")
	
	# Create animations from strips
	for anim_name in ANIMATIONS:
		var config := ANIMATIONS[anim_name]
		var strip_path := config["strip"] as String
		var frame_count := config["frames"] as int
		var fps := config["fps"] as float
		var loop := config["loop"] as bool
		
		# Load the strip texture
		var texture := load(strip_path) as Texture2D
		if texture == null:
			push_warning("SylaraSpriteSetup: Failed to load strip: " + strip_path)
			continue
		
		# Calculate frame dimensions
		var strip_width := texture.get_width()
		var strip_height := texture.get_height()
		var frame_width := strip_width / frame_count
		var frame_height := strip_height
		
		# Create animation
		sprite_frames.add_animation(anim_name)
		sprite_frames.set_animation_speed(anim_name, fps)
		sprite_frames.set_animation_loop(anim_name, loop)
		
		# Extract frames from strip
		for i in frame_count:
			var atlas_texture := AtlasTexture.new()
			atlas_texture.atlas = texture
			atlas_texture.region = Rect2(
				i * frame_width, 0,
				frame_width, frame_height
			)
			sprite_frames.add_frame(anim_name, atlas_texture)
	
	return sprite_frames


static func setup_animated_sprite(animated_sprite: AnimatedSprite2D) -> void:
	if animated_sprite == null:
		push_warning("SylaraSpriteSetup: AnimatedSprite2D is null")
		return
	
	animated_sprite.sprite_frames = create_sprite_frames()
	animated_sprite.play("idle")
