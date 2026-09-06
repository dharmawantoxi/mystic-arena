shader_type canvas_item;
uniform vec4 outline_color : source_color = vec4(1.0, 0.85, 0.3, 1.0);
uniform float outline_width : hint_range(0.0, 4.0) = 1.5;
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);

void fragment() {
    vec4 c = texture(TEXTURE, UV);
    float a = c.a;
    float o = 0.0;
    o += texture(TEXTURE, UV + vec2(outline_width * TEXTURE_PIXEL_SIZE.x, 0.0)).a;
    o += texture(TEXTURE, UV + vec2(-outline_width * TEXTURE_PIXEL_SIZE.x, 0.0)).a;
    o += texture(TEXTURE, UV + vec2(0.0, outline_width * TEXTURE_PIXEL_SIZE.y)).a;
    o += texture(TEXTURE, UV + vec2(0.0, -outline_width * TEXTURE_PIXEL_SIZE.y)).a;
    o = clamp(o - a, 0.0, 1.0);
    vec4 col = mix(c, outline_color, o * (1.0 - a));
    col.rgb = mix(col.rgb, flash_color.rgb, flash_amount * a);
    // rim light kiri atas (menggantikan mobile/perf Quality.cheap_alpha)
    vec2 light_dir = normalize(vec2(-0.6, -0.8));
    float rim = max(0.0, dot(normalize(UV - 0.5), -light_dir)) * 0.18 * a;
    col.rgb += rim;
    COLOR = col;
}
