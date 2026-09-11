// lighting.gdshader — port GPU dari lighting.py
// Paritas penuh: gradien arah + rim light + terminator (2 band) dari mask alpha saja.
// Dibuat untuk menggantikan 7 blit CPU di pygame dengan 1 pass shader.
// Cocok untuk 222 unit bake (BakedSprite) maupun rig prosedural.
//
// Arah cahaya: LIGHT_DIR = (-1,-1) kiri-atas, sama dengan lighting.py
// Rumus gradien: t = 1 - (gx*ax + gy*ay)/span, v = dark + (light-dark)*t, sheen = sheen * t^2.2
// Rim: mask - shift(mask, +sx,+sy) -> sisi menghadap cahaya
// Shade: mask - shift(mask, -sx,-sy) -> sisi membelakangi cahaya
//
// Penggunaan:
//   material = MysticLighting.create_lighting_material()
//   sprite.material = material
// Atau manual di .tscn: ShaderMaterial dengan shader ini.
//
// Untuk BakedSprite, shader membaca TEXTURE alpha sebagai mask (threshold MASK_ALPHA).

shader_type canvas_item;

uniform vec2 light_dir = vec2(-1.0, -1.0); // paritas LIGHT_DIR
uniform vec4 rim_add : source_color = vec4(0.1176, 0.102, 0.1725, 1.0); // (30,26,44)/255
uniform float shade_mul : hint_range(0.0, 1.0) = 0.6588; // 168/255
uniform float band2_ratio : hint_range(0.0, 1.0) = 0.42;
uniform float grad_dark : hint_range(0.0, 1.0) = 0.8039; // 205/255
uniform float grad_light : hint_range(0.0, 1.0) = 1.0; // 255/255
uniform float grad_sheen : hint_range(0.0, 1.0) = 0.08627; // 22/255
uniform float mask_alpha : hint_range(0.0, 1.0) = 0.6667; // 170/255
uniform float rim_width : hint_range(0.0, 4.0) = 1.0;
uniform float shade_width : hint_range(0.0, 4.0) = 1.0;
uniform bool gradient_enabled = true;
uniform bool two_band = true;
uniform vec4 bbox = vec4(0.0, 0.0, 1.0, 1.0); // x,y,w,h normalized untuk gradient box, default full
// bbox: jika ingin cahaya konstan per rig (anti-kedip saat pose berubah), isi dengan
// Rect2 konstan rig dalam UV space. Jika (0,0,1,1) = pakai UV penuh (paritas box=None jalur hero).

// Helper: apakah piksel di (uv + offset) solid?
float alpha_at(vec2 uv) {
    // clamp biar tidak sampling di luar
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return 0.0;
    return texture(TEXTURE, uv).a;
}

void fragment() {
    vec4 c = texture(TEXTURE, UV);
    float a = c.a;

    // Jika transparan di bawah threshold, jangan apa-apakan (biarkan transparan)
    if (a < mask_alpha * 0.5) {
        COLOR = c;
        return;
    }

    // --- Gradient arah (paritas lighting.py GRAD_BOX) ---
    vec3 col = c.rgb;
    if (gradient_enabled) {
        // Normalisasi posisi terhadap bbox (untuk anti-kedip, bbox = konstan rig)
        // Jika bbox = (0,0,1,1), maka t langsung dari UV.
        vec2 pos_in_box = (UV - bbox.xy) / bbox.zw;
        // clamp 0..1
        pos_in_box = clamp(pos_in_box, vec2(0.0), vec2(1.0));
        // t = 1 di sudut cahaya (kiri-atas), 0 di sudut bayangan (kanan-bawah)
        // lighting.py: t = 1 - (gx*ax + gy*ay)/span, span = (n-1)*(ax+ay)
        // Di UV space: ax=|light_dir.x|, ay=|light_dir.y|
        float ax = abs(light_dir.x);
        float ay = abs(light_dir.y);
        float span = ax + ay;
        if (span < 0.001) span = 1.0;
        // pos_in_box 0..1, cahaya di (0,0) jika light_dir (-1,-1)
        // Jadi t = 1 - (u*ax + v*ay)/span
        float t = 1.0 - (pos_in_box.x * ax + pos_in_box.y * ay) / span;
        t = clamp(t, 0.0, 1.0);
        float v = grad_dark + (grad_light - grad_dark) * t;
        // sheen specular di sudut cahaya
        float sheen_k = grad_sheen * pow(t, 2.2);
        // MULT
        col *= v;
        // ADD sheen (biru sedikit lebih terang: k*1.25 di B, paritas lighting.py)
        col += vec3(sheen_k, sheen_k, sheen_k * 1.25);
    }

    // --- Contour detection dari alpha (rim & terminator) ---
    // Kita pakai offset 1px dalam UV space
    vec2 px = TEXTURE_PIXEL_SIZE;
    float sx = abs(light_dir.x) * rim_width;
    float sy = abs(light_dir.y) * rim_width;

    // Rim: sisi menghadap cahaya = mask sekarang solid tapi shifted(+sx,+sy) kosong
    // Shade: sisi membelakangi = mask solid tapi shifted(-sx,-sy) kosong
    // Implementasi: sample tetangga sesuai light_dir

    // Arah geser: cahaya kiri-atas (-1,-1) => rim adalah piksel yang TIDAK ada di salinan yang digeser ke kanan-bawah
    vec2 shift_pos = vec2(sx * px.x, sy * px.y); // +sx,+sy = kanan-bawah
    vec2 shift_neg = -shift_pos;

    float a_shift_pos = alpha_at(UV + shift_pos);
    float a_shift_neg = alpha_at(UV + shift_neg);

    bool is_rim = (a >= mask_alpha) && (a_shift_pos < mask_alpha);
    bool is_shade = (a >= mask_alpha) && (a_shift_neg < mask_alpha);

    // Band kedua (width=2): 1px di dalam dari terminator
    bool is_shade_band2 = false;
    if (two_band) {
        vec2 shift2_neg = shift_neg * 2.0;
        float a_shift2_neg = alpha_at(UV + shift2_neg);
        // inner = mask - shift(mask, -2), deep = shade (mask - shift -1)
        // wide = inner - deep => solid, shift1 solid, shift2 kosong
        bool inner = (a >= mask_alpha) && (a_shift2_neg < mask_alpha);
        // wide = inner && !is_shade (sudah ada shift1 kosong? cek)
        // Sederhananya: jika tidak termasuk shade band1 tapi termasuk inner 2px
        if (inner && !is_shade) {
            // Pastikan 1px ke arah bayangan masih solid (jadi ini band ke-2)
            // yaitu a_shift_neg >= threshold
            if (a_shift_neg >= mask_alpha) {
                is_shade_band2 = true;
            }
        }
    }

    // --- Terminator (MULT darker) ---
    if (is_shade) {
        col *= shade_mul;
    } else if (is_shade_band2) {
        float k2 = 1.0 - (1.0 - shade_mul) * band2_ratio;
        col *= k2;
    }

    // --- Rim light (ADD) ---
    if (is_rim) {
        col += rim_add.rgb;
    }

    // Clamp
    col = clamp(col, vec3(0.0), vec3(1.0));

    COLOR = vec4(col, a);
}
