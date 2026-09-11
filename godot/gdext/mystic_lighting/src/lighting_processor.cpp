#include "lighting_processor.h"

#include <godot_cpp/classes/texture2d.hpp>
#include <godot_cpp/classes/shader.hpp>
#include <godot_cpp/classes/shader_material.hpp>
#include <godot_cpp/variant/utility_functions.hpp>
#include <godot_cpp/core/math.hpp>

using namespace godot;

std::unordered_map<std::string, MysticLighting::GradPair> MysticLighting::_canon_cache;
std::unordered_map<std::string, MysticLighting::GradPair> MysticLighting::_size_cache;

std::string MysticLighting::_canon_key(int dark, int light, int sheen) {
    return std::to_string(dark) + "_" + std::to_string(light) + "_" + std::to_string(sheen) + "_" +
           std::to_string(LIGHT_DIR_X) + "_" + std::to_string(LIGHT_DIR_Y);
}
std::string MysticLighting::_size_key(int w, int h, int dark, int light, int sheen) {
    return std::to_string(w) + "_" + std::to_string(h) + "_" + std::to_string(dark) + "_" +
           std::to_string(light) + "_" + std::to_string(sheen);
}

MysticLighting::Mask MysticLighting::_build_solid_mask(const Ref<Image>& img, int alpha_threshold) {
    int w = img->get_width();
    int h = img->get_height();
    Mask mask(h, std::vector<uint8_t>(w, 0));
    float thresh = (float)alpha_threshold / 255.0f;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            Color c = img->get_pixel(x, y);
            if (c.a * 255.0f >= (float)alpha_threshold || c.a >= thresh) {
                mask[y][x] = 1;
            }
        }
    }
    return mask;
}

int MysticLighting::_count_mask(const Mask& mask) {
    int cnt = 0;
    for (auto& row : mask) for (auto v : row) if (v) ++cnt;
    return cnt;
}

MysticLighting::Mask MysticLighting::_shifted_mask(const Mask& mask, int dx, int dy, int w, int h) {
    Mask out(h, std::vector<uint8_t>(w, 0));
    for (int y = 0; y < h; ++y) {
        int sy = y - dy;
        if (sy < 0 || sy >= h) continue;
        for (int x = 0; x < w; ++x) {
            int sx = x - dx;
            if (sx < 0 || sx >= w) continue;
            if (mask[sy][sx]) out[y][x] = 1;
        }
    }
    return out;
}

MysticLighting::Mask MysticLighting::_copy_mask(const Mask& mask) {
    return mask;
}

void MysticLighting::_erase_mask(Mask& a, const Mask& b) {
    int h = (int)a.size();
    if (h == 0) return;
    int w = (int)a[0].size();
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            if (b[y][x] && a[y][x]) a[y][x] = 0;
        }
    }
}

MysticLighting::GradPair MysticLighting::_canonical(int dark, int light, int sheen) {
    std::string key = _canon_key(dark, light, sheen);
    auto it = _canon_cache.find(key);
    if (it != _canon_cache.end()) return it->second;

    int n = GRAD_STEPS;
    Ref<Image> mul_img = Image::create(n, n, false, Image::FORMAT_RGBA8);
    Ref<Image> add_img = Image::create(n, n, false, Image::FORMAT_RGBA8);

    int ax = std::abs(LIGHT_DIR_X);
    int ay = std::abs(LIGHT_DIR_Y);
    double span = double((n - 1) * (ax + ay));
    if (span < 1.0) span = 1.0;

    for (int gy = 0; gy < n; ++gy) {
        for (int gx = 0; gx < n; ++gx) {
            double t = 1.0 - (double(gx * ax + gy * ay) / span);
            t = Math::clamp(t, 0.0, 1.0);
            int v = int(std::round(double(dark) + double(light - dark) * t));
            v = Math::clamp(v, 0, 255);
            float vf = float(v) / 255.0f;
            mul_img->set_pixel(gx, gy, Color(vf, vf, vf, 1.0f));

            int k = int(std::round(double(sheen) * std::pow(t, 2.2)));
            k = Math::clamp(k, 0, 255);
            int kb = int(std::round(double(k) * 1.25));
            kb = Math::clamp(kb, 0, 255);
            add_img->set_pixel(gx, gy, Color(float(k)/255.0f, float(k)/255.0f, float(kb)/255.0f, 1.0f));
        }
    }

    GradPair gp{mul_img, add_img};
    _canon_cache[key] = gp;
    return gp;
}

MysticLighting::GradPair MysticLighting::_sized(int w, int h, int dark, int light, int sheen) {
    std::string key = _size_key(w, h, dark, light, sheen);
    auto it = _size_cache.find(key);
    if (it != _size_cache.end()) return it->second;

    if (_size_cache.size() > 64) _size_cache.clear();

    GradPair canon = _canonical(dark, light, sheen);
    Ref<Image> mul = canon.mul->duplicate();
    Ref<Image> add = canon.add->duplicate();
    mul->resize(w, h, Image::INTERPOLATE_BILINEAR);
    add->resize(w, h, Image::INTERPOLATE_BILINEAR);

    GradPair out{mul, add};
    _size_cache[key] = out;
    return out;
}

void MysticLighting::reset_gradient_cache() {
    _size_cache.clear();
    _canon_cache.clear();
}

Dictionary MysticLighting::contour_masks_gd(const Ref<Image>& image, int alpha, int width) {
    Dictionary ret;
    if (image.is_null()) {
        ret["valid"] = false;
        return ret;
    }
    int w = image->get_width();
    int h = image->get_height();
    if (w <= 2 || h <= 2) {
        ret["valid"] = false;
        return ret;
    }
    Mask solid = _build_solid_mask(image, alpha);
    if (_count_mask(solid) < 24) {
        ret["valid"] = false;
        return ret;
    }
    int sx = std::abs(LIGHT_DIR_X) * width;
    int sy = std::abs(LIGHT_DIR_Y) * width;

    Mask shifted_pos = _shifted_mask(solid, sx, sy, w, h);
    Mask rim = _copy_mask(solid);
    _erase_mask(rim, shifted_pos);

    Mask shifted_neg = _shifted_mask(solid, -sx, -sy, w, h);
    Mask shade = _copy_mask(solid);
    _erase_mask(shade, shifted_neg);

    // Untuk GDScript kita tidak bisa return Mask langsung, jadi return valid + bbox count
    // Tapi kita simpan count untuk debug
    ret["valid"] = true;
    ret["w"] = w;
    ret["h"] = h;
    ret["solid_count"] = _count_mask(solid);
    // rim/shade sebagai Image debug (opsional)
    Ref<Image> rim_img = Image::create(w, h, false, Image::FORMAT_RGBA8);
    Ref<Image> shade_img = Image::create(w, h, false, Image::FORMAT_RGBA8);
    for (int y=0;y<h;++y) for (int x=0;x<w;++x) {
        if (rim[y][x]) rim_img->set_pixel(x,y, Color(1,1,1,1));
        if (shade[y][x]) shade_img->set_pixel(x,y, Color(1,1,1,1));
    }
    ret["rim_image"] = rim_img;
    ret["shade_image"] = shade_img;
    return ret;
}

Rect2i MysticLighting::bbox_of_gd(const Ref<Image>& image, int alpha) {
    if (image.is_null()) return Rect2i(0,0,0,0);
    int w = image->get_width();
    int h = image->get_height();
    Mask solid = _build_solid_mask(image, alpha);
    int x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (int y=0;y<h;++y) for (int x=0;x<w;++x) if (solid[y][x]) {
        if (x < x0) x0 = x;
        if (y < y0) y0 = y;
        if (x > x1) x1 = x;
        if (y > y1) y1 = y;
    }
    if (x1 < 0) return Rect2i(0,0,0,0);
    return Rect2i(x0, y0, std::max(1, x1 - x0 + 1), std::max(1, y1 - y0 + 1));
}

Ref<Image> MysticLighting::apply(const Ref<Image>& image, Color rim_add, int shade_mul, bool two_band, int alpha, bool gradient, Rect2i box) {
    if (image.is_null()) return image;
    int w = image->get_width();
    int h = image->get_height();
    if (w <= 2 || h <= 2) return image;

    // Pastikan RGBA8
    if (image->get_format() != Image::FORMAT_RGBA8) {
        image->convert(Image::FORMAT_RGBA8);
    }

    Mask solid = _build_solid_mask(image, alpha);
    if (_count_mask(solid) < 24) return image;

    int sx = std::abs(LIGHT_DIR_X);
    int sy = std::abs(LIGHT_DIR_Y);

    // rim & shade width=1
    Mask shifted_pos = _shifted_mask(solid, sx, sy, w, h);
    Mask rim = _copy_mask(solid);
    _erase_mask(rim, shifted_pos);

    Mask shifted_neg = _shifted_mask(solid, -sx, -sy, w, h);
    Mask shade = _copy_mask(solid);
    _erase_mask(shade, shifted_neg);

    // gradient
    if (gradient) {
        int bx, by, bw, bh;
        if (box.size.x < 0) {
            bx = 0; by = 0; bw = w; bh = h;
        } else {
            bx = box.position.x; by = box.position.y;
            bw = box.size.x; bh = box.size.y;
            bw = std::max(2, std::min(bw, w - bx));
            bh = std::max(2, std::min(bh, h - by));
        }
        if (bw > 2 && bh > 2) {
            GradPair grad = _sized(bw, bh);
            for (int yy=0; yy<bh; ++yy) for (int xx=0; xx<bw; ++xx) {
                int gx = bx + xx;
                int gy = by + yy;
                if (gx <0 || gx>=w || gy<0 || gy>=h) continue;
                Color src = image->get_pixel(gx, gy);
                if (src.a <= 0.001f) continue;
                Color m = grad.mul->get_pixel(xx, yy);
                Color a = grad.add->get_pixel(xx, yy);
                src.r *= m.r;
                src.g *= m.g;
                src.b *= m.b;
                src.r = std::min(1.0f, src.r + a.r);
                src.g = std::min(1.0f, src.g + a.g);
                src.b = std::min(1.0f, src.b + a.b);
                image->set_pixel(gx, gy, src);
            }
        }
    }

    // terminator band2
    Mask wide;
    bool has_wide = false;
    if (two_band) {
        // width=2 shade = outer band
        Mask shifted2_pos = _shifted_mask(solid, sx*2, sy*2, w, h);
        Mask shifted2_neg = _shifted_mask(solid, -sx*2, -sy*2, w, h);
        Mask inner = _copy_mask(solid);
        _erase_mask(inner, shifted2_neg);
        // wide = inner - shade
        wide = _copy_mask(inner);
        _erase_mask(wide, shade);
        has_wide = true;
    }

    int neutral = Math::clamp(shade_mul, 0, 255);
    float neutral_f = float(neutral) / 255.0f;
    int k2 = Math::clamp(int(255.0 - (255.0 - float(neutral)) * BAND2_RATIO), 0, 255);
    float k2_f = float(k2) / 255.0f;

    for (int y=0;y<h;++y) for (int x=0;x<w;++x) {
        bool is_shade = shade[y][x];
        bool is_wide = has_wide && wide[y][x];
        if (!is_shade && !is_wide) continue;
        Color src = image->get_pixel(x, y);
        if (src.a <= 0.001f) continue;
        if (is_shade) {
            src.r *= neutral_f;
            src.g *= neutral_f;
            src.b *= neutral_f;
        } else if (is_wide) {
            src.r *= k2_f;
            src.g *= k2_f;
            src.b *= k2_f;
        }
        image->set_pixel(x, y, src);
    }

    // rim light
    for (int y=0;y<h;++y) for (int x=0;x<w;++x) {
        if (!rim[y][x]) continue;
        Color src = image->get_pixel(x, y);
        if (src.a <= 0.001f) continue;
        src.r = std::min(1.0f, src.r + rim_add.r);
        src.g = std::min(1.0f, src.g + rim_add.g);
        src.b = std::min(1.0f, src.b + rim_add.b);
        image->set_pixel(x, y, src);
    }

    return image;
}

Ref<Image> MysticLighting::apply_to_rig(const Ref<Image>& image, bool enabled, Color rim_add, int shade_mul, bool two_band, int alpha, bool gradient, Rect2i box) {
    if (!enabled) return image;
    if (image.is_null()) return image;
    // Jangan crash renderer — copy dulu, kalau gagal return asli
    Ref<Image> copy = image->duplicate();
    if (copy.is_null()) return image;
    return apply(copy, rim_add, shade_mul, two_band, alpha, gradient, box);
}

Ref<ImageTexture> MysticLighting::apply_to_texture(const Ref<Texture2D>& tex, bool enabled, Rect2i box) {
    if (tex.is_null()) return Ref<ImageTexture>();
    Ref<Image> img = tex->get_image();
    if (img.is_null()) return Ref<ImageTexture>();
    if (img->get_format() != Image::FORMAT_RGBA8) img->convert(Image::FORMAT_RGBA8);
    Ref<Image> out = apply_to_rig(img, enabled, Color(30.0f/255.0f,26.0f/255.0f,44.0f/255.0f,1.0f), SHADE_MUL, true, MASK_ALPHA, GRADIENT_ENABLED, box);
    Ref<ImageTexture> itex = ImageTexture::create_from_image(out);
    return itex;
}

Dictionary MysticLighting::shader_params() {
    Dictionary d;
    d["light_dir"] = Vector2((float)LIGHT_DIR_X, (float)LIGHT_DIR_Y);
    d["rim_add"] = Color(30.0f/255.0f, 26.0f/255.0f, 44.0f/255.0f, 1.0f);
    d["shade_mul"] = float(SHADE_MUL) / 255.0f;
    d["band2_ratio"] = BAND2_RATIO;
    d["grad_dark"] = float(GRAD_DARK) / 255.0f;
    d["grad_light"] = float(GRAD_LIGHT) / 255.0f;
    d["grad_sheen"] = float(GRAD_SHEEN) / 255.0f;
    d["mask_alpha"] = float(MASK_ALPHA) / 255.0f;
    return d;
}

Ref<ShaderMaterial> MysticLighting::create_lighting_material() {
    Ref<Shader> shader = ResourceLoader::get_singleton()->load("res://assets/shaders/lighting.gdshader");
    if (shader.is_null()) {
        shader = ResourceLoader::get_singleton()->load("res://assets/shaders/outline.gdshader");
    }
    Ref<ShaderMaterial> mat;
    mat.instantiate();
    mat->set_shader(shader);
    Dictionary p = shader_params();
    Vector2 ld = p["light_dir"];
    Color rim = p["rim_add"];
    mat->set_shader_parameter("light_dir", ld);
    mat->set_shader_parameter("rim_add", rim); // shader sekarang vec4 : source_color
    mat->set_shader_parameter("shade_mul", p["shade_mul"]);
    mat->set_shader_parameter("band2_ratio", p["band2_ratio"]);
    mat->set_shader_parameter("grad_dark", p["grad_dark"]);
    mat->set_shader_parameter("grad_light", p["grad_light"]);
    mat->set_shader_parameter("grad_sheen", p["grad_sheen"]);
    mat->set_shader_parameter("mask_alpha", p["mask_alpha"]);
    return mat;
}

void MysticLighting::_bind_methods() {
    ClassDB::bind_method(D_METHOD("reset_gradient_cache"), &MysticLighting::reset_gradient_cache);
    ClassDB::bind_method(D_METHOD("contour_masks", "image", "alpha", "width"), &MysticLighting::contour_masks_gd, DEFVAL(MASK_ALPHA), DEFVAL(1));
    ClassDB::bind_method(D_METHOD("bbox_of", "image", "alpha"), &MysticLighting::bbox_of_gd, DEFVAL(MASK_ALPHA));
    ClassDB::bind_method(D_METHOD("apply", "image", "rim_add", "shade_mul", "two_band", "alpha", "gradient", "box"),
        &MysticLighting::apply, DEFVAL(Color(30.0f/255.0f,26.0f/255.0f,44.0f/255.0f,1.0f)), DEFVAL(SHADE_MUL), DEFVAL(true), DEFVAL(MASK_ALPHA), DEFVAL(GRADIENT_ENABLED), DEFVAL(Rect2i(-1,-1,-1,-1)));
    ClassDB::bind_method(D_METHOD("apply_to_rig", "image", "enabled", "rim_add", "shade_mul", "two_band", "alpha", "gradient", "box"),
        &MysticLighting::apply_to_rig, DEFVAL(true), DEFVAL(Color(30.0f/255.0f,26.0f/255.0f,44.0f/255.0f,1.0f)), DEFVAL(SHADE_MUL), DEFVAL(true), DEFVAL(MASK_ALPHA), DEFVAL(GRADIENT_ENABLED), DEFVAL(Rect2i(-1,-1,-1,-1)));
    ClassDB::bind_method(D_METHOD("apply_to_texture", "texture", "enabled", "box"), &MysticLighting::apply_to_texture, DEFVAL(true), DEFVAL(Rect2i(-1,-1,-1,-1)));
    ClassDB::bind_method(D_METHOD("shader_params"), &MysticLighting::shader_params);
    ClassDB::bind_method(D_METHOD("create_lighting_material"), &MysticLighting::create_lighting_material);

    // Konstanta
    ClassDB::bind_integer_constant("MysticLighting", "LIGHT_DIR_X", LIGHT_DIR_X);
    ClassDB::bind_integer_constant("MysticLighting", "LIGHT_DIR_Y", LIGHT_DIR_Y);
    ClassDB::bind_integer_constant("MysticLighting", "SHADE_MUL", SHADE_MUL);
    ClassDB::bind_integer_constant("MysticLighting", "MASK_ALPHA", MASK_ALPHA);
    ClassDB::bind_integer_constant("MysticLighting", "GRAD_DARK", GRAD_DARK);
    ClassDB::bind_integer_constant("MysticLighting", "GRAD_LIGHT", GRAD_LIGHT);
    ClassDB::bind_integer_constant("MysticLighting", "GRAD_SHEEN", GRAD_SHEEN);
    ClassDB::bind_integer_constant("MysticLighting", "GRAD_STEPS", GRAD_STEPS);
}
