#ifndef MYSTIC_LIGHTING_PROCESSOR_H
#define MYSTIC_LIGHTING_PROCESSOR_H

// lighting_processor.h — port C++ (godot++) dari lighting.py
// Paritas 1:1 dengan lighting.py + Lighting.gd
//
// Fitur:
// - Rim light: piksel terluar sisi cahaya -> RGB ADD
// - Terminator: sisi bayangan -> RGB MULT darker + band kedua 40%
// - Gradient arah: dark->light + sheen specular, di-cache 28x28 lalu upscale
// - Semua dari mask alpha saja, bebas bentuk karakter
// - Biaya <0.5ms untuk sprite 90x90 (paritas lighting.py)
//
// Penggunaan dari GDScript:
//   var img = texture.get_image()
//   MysticLighting.apply(img)
//   var tex = ImageTexture.create_from_image(img)
//
// Atau sebagai Node:
//   var processor = MysticLightingProcessor.new()
//   processor.apply_to_image(img, box)

#include <godot_cpp/classes/image.hpp>
#include <godot_cpp/classes/image_texture.hpp>
#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/variant/vector2i.hpp>
#include <godot_cpp/variant/color.hpp>
#include <godot_cpp/variant/rect2i.hpp>
#include <unordered_map>
#include <vector>
#include <string>
#include <cmath>

namespace godot {

class MysticLighting : public RefCounted {
    GDCLASS(MysticLighting, RefCounted);

public:
    // --- Konstanta paritas lighting.py ---
    static constexpr int LIGHT_DIR_X = -1;
    static constexpr int LIGHT_DIR_Y = -1;
    static constexpr int RIM_ADD_R = 30;
    static constexpr int RIM_ADD_G = 26;
    static constexpr int RIM_ADD_B = 44;
    static constexpr int SHADE_MUL = 168;
    static constexpr double BAND2_RATIO = 0.42;
    static constexpr int MASK_ALPHA = 170;
    static constexpr bool GRADIENT_ENABLED = true;
    static constexpr int GRAD_DARK = 205;
    static constexpr int GRAD_LIGHT = 255;
    static constexpr int GRAD_SHEEN = 22;
    static constexpr int GRAD_STEPS = 28;

private:
    // Cache gradient kanonik 28x28
    struct GradPair {
        Ref<Image> mul;
        Ref<Image> add;
    };
    static std::unordered_map<std::string, GradPair> _canon_cache;
    static std::unordered_map<std::string, GradPair> _size_cache;

    static std::string _canon_key(int dark, int light, int sheen);
    static std::string _size_key(int w, int h, int dark, int light, int sheen);

    // Mask helpers
    using Mask = std::vector<std::vector<uint8_t>>; // [y][x] 0/1
    static Mask _build_solid_mask(const Ref<Image>& img, int alpha_threshold);
    static int _count_mask(const Mask& mask);
    static Mask _shifted_mask(const Mask& mask, int dx, int dy, int w, int h);
    static Mask _copy_mask(const Mask& mask);
    static void _erase_mask(Mask& a, const Mask& b);

public:
    MysticLighting() {}
    ~MysticLighting() {}

    // --- API utama (paritas lighting.py) ---
    static void reset_gradient_cache();

    // contour_masks: return Dictionary {rim, shade, solid, valid, w, h} — tapi di C++ kita pakai internal struct
    // Untuk GDScript binding, kita expose versi yang return Dictionary
    static Dictionary contour_masks_gd(const Ref<Image>& image, int alpha = MASK_ALPHA, int width = 1);
    static Rect2i bbox_of_gd(const Ref<Image>& image, int alpha = MASK_ALPHA);

    // apply: beri cahaya IN-PLACE pada Image (RGB saja, alpha tetap)
    static Ref<Image> apply(const Ref<Image>& image,
                            Color rim_add = Color(30.0f/255.0f, 26.0f/255.0f, 44.0f/255.0f, 1.0f),
                            int shade_mul = SHADE_MUL,
                            bool two_band = true,
                            int alpha = MASK_ALPHA,
                            bool gradient = GRADIENT_ENABLED,
                            Rect2i box = Rect2i(-1, -1, -1, -1));

    static Ref<Image> apply_to_rig(const Ref<Image>& image,
                                   bool enabled = true,
                                   Color rim_add = Color(30.0f/255.0f, 26.0f/255.0f, 44.0f/255.0f, 1.0f),
                                   int shade_mul = SHADE_MUL,
                                   bool two_band = true,
                                   int alpha = MASK_ALPHA,
                                   bool gradient = GRADIENT_ENABLED,
                                   Rect2i box = Rect2i(-1, -1, -1, -1));

    // Helper Texture2D -> ImageTexture
    static Ref<ImageTexture> apply_to_texture(const Ref<Texture2D>& tex, bool enabled = true, Rect2i box = Rect2i(-1,-1,-1,-1));

    // Gradient internal
    static GradPair _canonical(int dark = GRAD_DARK, int light = GRAD_LIGHT, int sheen = GRAD_SHEEN);
    static GradPair _sized(int w, int h, int dark = GRAD_DARK, int light = GRAD_LIGHT, int sheen = GRAD_SHEEN);

    // Shader params untuk GDScript
    static Dictionary shader_params();

    // Factory material
    static Ref<ShaderMaterial> create_lighting_material();

protected:
    static void _bind_methods();
};

} // namespace godot

#endif // MYSTIC_LIGHTING_PROCESSOR_H
