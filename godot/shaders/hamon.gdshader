// hamon.gdshader — garis temper katana Kaizen (hamon)
// Efek: ripple metalik diagonal + pulse saat attack, mengkilap wind-metal
shader_type canvas_item;

uniform float time : hint_range(0.0, 100.0) = 0.0;
uniform float attack_t : hint_range(0.0, 1.0) = 0.0;
uniform vec4 steel_light : source_color = vec4(0.72, 0.74, 0.79, 1.0);
uniform vec4 steel_mid : source_color = vec4(0.49, 0.52, 0.58, 1.0);
uniform vec4 hamon_color : source_color = vec4(0.82, 0.93, 1.0, 1.0);

void fragment() {
    vec2 uv = UV;
    // uv.y = sepanjang bilah (0 pangkal, 1 ujung)
    float y = uv.y;
    float x = uv.x;
    // hamon wave: garis bergelombang sepanjang bilah
    float wave = sin(y * 22.0 - time * 6.0 + x * 8.0) * 0.5 + 0.5;
    wave = pow(wave, 18.0); // garis sangat tipis
    // temper cloud: area hamon dekat pusat bilah
    float temper = smoothstep(0.35, 0.65, x) * smoothstep(0.65, 0.35, x);
    temper *= smoothstep(0.08, 0.18, y) * smoothstep(0.92, 0.82, y);
    // attack pulse: kilatan putih saat swing
    float pulse = sin(attack_t * 18.0 - y * 12.0) * 0.5 + 0.5;
    pulse = pow(pulse, 6.0) * step(0.22, attack_t) * step(attack_t, 0.90) * 1.2;
    // base metal gradient (pangkal gelap → ujung terang)
    vec3 base = mix(steel_mid.rgb, steel_light.rgb, smoothstep(0.0, 1.0, y));
    // kilau diagnal
    float glint = sin((y - x*0.4 + time*0.9) * 30.0) * 0.5 + 0.5;
    glint = pow(glint, 34.0) * 0.55 * smoothstep(0.3, 0.7, y);
    vec3 col = base + glint * vec3(1.0);
    // hamon line
    col = mix(col, hamon_color.rgb, wave * 0.85);
    // temper haze biru
    col = mix(col, hamon_color.rgb * 0.55, temper * 0.35);
    // pulse flash
    col += pulse * vec3(1.0, 0.97, 0.88) * 0.85;
    float alpha = 1.0;
    // tepi bilah: alpha falloff
    float edge = smoothstep(0.0, 0.08, x) * smoothstep(1.0, 0.92, x);
    alpha *= mix(0.75, 1.0, edge);
    COLOR = vec4(col, alpha);
}
