// lighting_outline.gdshader — gabungan outline.gdshader + lighting.gdshader
// 1 pass saja untuk outline + hit flash + rim + terminator + gradient
// Port dari lighting.py + outline.gdshader (yang sebelumnya 5 blit CPU)
shader_type canvas_item;

uniform vec4 outline_color : source_color = vec4(1.0, 0.85, 0.3, 1.0);
uniform float outline_width : hint_range(0.0, 4.0) = 1.5;
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);

// lighting uniforms (paritas lighting.py)
uniform vec2 light_dir = vec2(-1.0, -1.0);
uniform vec3 rim_add : source_color = vec3(0.1176, 0.102, 0.1725);
uniform float shade_mul : hint_range(0.0, 1.0) = 0.6588;
uniform float band2_ratio : hint_range(0.0, 1.0) = 0.42;
uniform float grad_dark : hint_range(0.0, 1.0) = 0.8039;
uniform float grad_light : hint_range(0.0, 1.0) = 1.0;
uniform float grad_sheen : hint_range(0.0, 1.0) = 0.08627;
uniform float mask_alpha : hint_range(0.0, 1.0) = 0.6667;
uniform float rim_width_l : hint_range(0.0, 4.0) = 1.0;
uniform bool gradient_enabled = true;
uniform bool two_band = true;
uniform vec4 bbox : hint_default = vec4(0.0, 0.0, 1.0, 1.0);

float alpha_at(vec2 uv) {
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return 0.0;
    return texture(TEXTURE, uv).a;
}

void fragment() {
    vec4 c = texture(TEXTURE, UV);
    float a = c.a;

    // Outline detection (dari outline.gdshader asli)
    float o = 0.0;
    o += texture(TEXTURE, UV + vec2(outline_width * TEXTURE_PIXEL_SIZE.x, 0.0)).a;
    o += texture(TEXTURE, UV + vec2(-outline_width * TEXTURE_PIXEL_SIZE.x, 0.0)).a;
    o += texture(TEXTURE, UV + vec2(0.0, outline_width * TEXTURE_PIXEL_SIZE.y)).a;
    o += texture(TEXTURE, UV + vec2(0.0, -outline_width * TEXTURE_PIXEL_SIZE.y)).a;
    o = clamp(o - a, 0.0, 1.0);

    vec4 col = c;
    // Jika ini outline (a==0 tapi tetangga solid), pakai outline_color
    if (a < 0.01 && o > 0.01) {
        col = outline_color;
        col.a = o;
        COLOR = col;
        return;
    }

    // Jika transparan total, early out
    if (a < mask_alpha * 0.5) {
        // tapi masih ada outline?
        vec4 outline_mix = mix(c, outline_color, o * (1.0 - a));
        COLOR = outline_mix;
        return;
    }

    // --- Gradient (paritas lighting.py) ---
    vec3 rgb = c.rgb;
    if (gradient_enabled) {
        vec2 pos_in_box = (UV - bbox.xy) / bbox.zw;
        pos_in_box = clamp(pos_in_box, vec2(0.0), vec2(1.0));
        float ax = abs(light_dir.x);
        float ay = abs(light_dir.y);
        float span = ax + ay;
        if (span < 0.001) span = 1.0;
        float t = 1.0 - (pos_in_box.x * ax + pos_in_box.y * ay) / span;
        t = clamp(t, 0.0, 1.0);
        float v = grad_dark + (grad_light - grad_dark) * t;
        float sheen_k = grad_sheen * pow(t, 2.2);
        rgb *= v;
        rgb += vec3(sheen_k, sheen_k, sheen_k * 1.25);
    }

    // --- Contour rim/shade ---
    vec2 px = TEXTURE_PIXEL_SIZE;
    vec2 shift_pos = vec2(abs(light_dir.x) * rim_width_l * px.x, abs(light_dir.y) * rim_width_l * px.y);
    vec2 shift_neg = -shift_pos;
    float a_shift_pos = alpha_at(UV + shift_pos);
    float a_shift_neg = alpha_at(UV + shift_neg);

    bool is_rim = (a >= mask_alpha) && (a_shift_pos < mask_alpha);
    bool is_shade = (a >= mask_alpha) && (a_shift_neg < mask_alpha);
    bool is_shade_band2 = false;
    if (two_band) {
        float a_shift2_neg = alpha_at(UV + shift_neg * 2.0);
        bool inner = (a >= mask_alpha) && (a_shift2_neg < mask_alpha);
        if (inner && !is_shade && a_shift_neg >= mask_alpha) {
            is_shade_band2 = true;
        }
    }

    if (is_shade) {
        rgb *= shade_mul;
    } else if (is_shade_band2) {
        float k2 = 1.0 - (1.0 - shade_mul) * band2_ratio;
        rgb *= k2;
    }
    if (is_rim) {
        rgb += rim_add;
    }

    // --- Flash (hit) ---
    rgb = mix(rgb, flash_color.rgb, flash_amount * a);
    rgb = clamp(rgb, vec3(0.0), vec3(1.0));

    // Outline mix untuk tepi semi-transparan
    col.rgb = rgb;
    // Kalau ada outline di sekitar, blend seperti shader outline asli untuk AA
    // Tapi karena kita sudah di dalam solid, outline tidak overlap
    // Untuk AA tepi: mix dengan outline jika a<1
    if (o > 0.01) {
        // tepi luar sudah di-handle di atas, ini untuk transisi AA di dalam
        col.rgb = mix(col.rgb, outline_color.rgb, o * 0.15);
    }

    COLOR = vec4(col.rgb, a);
}
