shader_type canvas_item;

// Gradasi vertikal per-glyph untuk teks judul — port ui_theme.gradient_text.
// UV.y pada quad glyph Label bersifat lokal per-glyph, jadi mix() ini
// meniru gradasi masking per-baris pygame (atas terang -> bawah gelap).
// WAJIB sample TEXTURE: coverage glyph ada di alpha font-atlas; tanpa ini
// Label me-render kotak solid, bukan teks. Jangan pakai font_shadow atau
// font_outline pada Label ber-material ini (outline digambar sebagai Label
// susun terpisah — lihat MysticTitle — persis outline_text pygame yang
// mem-blit teks gelap di belakang badan gradasi).
uniform vec4 top_color : source_color = vec4(1.0, 0.91, 0.61, 1.0);
uniform vec4 bottom_color : source_color = vec4(0.77, 0.54, 0.16, 1.0);

void fragment() {
	float coverage = texture(TEXTURE, UV).a;
	COLOR.rgb = mix(top_color.rgb, bottom_color.rgb, UV.y);
	COLOR.a *= coverage;
}
