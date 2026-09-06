shader_type canvas_item;
// Bloom + glow untuk skill hero (menggantikan 14 Surface SRCALPHA per frame di pygame)
uniform float bloom_strength : hint_range(0.0, 2.0) = 0.8;
uniform vec4 glow_color : source_color = vec4(1.0, 0.85, 0.3, 1.0);
uniform float time : hint_range(0.0, 10.0) = 0.0;

void fragment() {
    vec4 c = texture(TEXTURE, UV);
    float dist = distance(UV, vec2(0.5));
    float pulse = 0.7 + 0.3 * sin(time * 3.0);
    float glow = exp(-dist * 4.0) * bloom_strength * pulse;
    c.rgb += glow_color.rgb * glow * c.a;
    COLOR = c;
}
