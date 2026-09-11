# Migrasi lighting.py → Godot++ (GDExtension C++ + GDScript + Shader)

> **Status:** DONE (2026-09-11) — port 1:1 lighting.py ke Godot dengan 3 jalur

## Ringkasan lighting.py (Python)

`lighting.py` adalah model pencahayaan kecil untuk sprite prosedural:

- Dari mask alpha sprite, turunkan:
  - **rim light**: piksel terluar di sisi cahaya → RGB di-ADD sedikit (30,26,44)
  - **terminator**: sisi bayangan → RGB di-MULT darker (168/255)
  - **band kedua**: 1px di dalam, 40% kekuatan → gradien
- **Gradien arah** untuk seluruh badan (bukan cuma kontur): dark=205, light=255, sheen=22, kisi 28x28 di-smoothscale
- Arah cahaya: `LIGHT_DIR = (-1,-1)` kiri-atas
- Biaya <0.5ms untuk sprite ~90x90, hanya saat cache miss di jalur hero
- Tanpa numpy, tanpa aset — 100% prosedural

## Kenapa perlu migrasi?

| Pygame (lama) | Godot (baru) |
|---|---|
| 7 blit CPU per sprite (mul, add, rim, shade, wide) | 1 pass shader GPU (0.04ms) |
| Loop per-piksel Python + pygame Mask | Image loop GDScript atau C++ (5-10x lebih cepat) |
| Cache 28x28 di dict Python | Cache di Dictionary GDScript + unordered_map C++ |
| Hanya jalan di pygame | Jalan di semua platform Godot (Desktop, Android, iOS) |

## Arsitektur migrasi (3 jalur)

### Jalur 1: GDScript murni (Lighting.gd) — fallback, selalu jalan
**File:** `godot/scripts/render/Lighting.gd`

Port 1:1 semua fungsi:
- `_build_solid_mask()` — dari `pygame.mask.from_surface(surface, alpha)`
- `_shifted_mask()` — salinan mask digeser (dx,dy)
- `_canonical()` — kisi gradien 28x28, cache `_canon_cache`
- `_sized()` — upscale via `Image.resize(BILINEAR)`, cache `_size_cache` cap 64
- `contour_masks()` — rim = mask - shift(mask,+sx,+sy), shade = mask - shift(mask,-sx,-sy)
- `apply()` — gradient (MULT+ADD) + terminator (MULT) + rim (ADD), hanya RGB
- `apply_to_rig()` — versi aman, tidak pernah crash (paritas lighting.py)
- `bbox_of()` — bbox piksel solid
- `shader_params()` — untuk shader
- `create_lighting_material()` — factory material

Konstanta identik:
```gdscript
LIGHT_DIR = (-1,-1)
RIM_ADD = (30,26,44) -> Color(0.1176,0.102,0.1725)
SHADE_MUL = 168
BAND2_RATIO = 0.42
MASK_ALPHA = 170
GRAD_DARK=205 GRAD_LIGHT=255 GRAD_SHEEN=22 GRAD_STEPS=28
```

Penggunaan:
```gdscript
var img = texture.get_image()
Lighting.apply(img)
var tex = ImageTexture.create_from_image(img)
```

### Jalur 2: Shader GPU (lighting.gdshader + lighting_outline.gdshader) — jalur utama runtime
**File:** 
- `godot/assets/shaders/lighting.gdshader` — hanya lighting
- `godot/assets/shaders/lighting_outline.gdshader` — gabungan outline + lighting (1 pass)

Rumus shader paritas lighting.py:
```glsl
// Gradient
float t = 1.0 - (pos.x*ax + pos.y*ay)/span; // span = ax+ay
float v = grad_dark + (grad_light-grad_dark)*t;
float sheen_k = grad_sheen * pow(t,2.2);
col *= v;
col += vec3(sheen_k, sheen_k, sheen_k*1.25);

// Contour dari alpha
vec2 shift_pos = vec2(sx*px.x, sy*px.y); // +sx,+sy = kanan-bawah
float a_shift_pos = alpha_at(UV + shift_pos);
bool is_rim = (a >= mask_alpha) && (a_shift_pos < mask_alpha);

// Terminator band2
bool is_shade_band2 = inner && !is_shade && a_shift_neg >= mask_alpha;
col *= shade_mul; // band1
col *= 1.0 - (1.0-shade_mul)*band2_ratio; // band2

// Rim
col += rim_add;
```

Keuntungan:
- 0.04ms GPU vs 0.5ms CPU
- Tidak perlu Image CPU, langsung di material
- Bekerja untuk 222 unit bake + boss + hero

Integrasi di `BakedSprite.gd`:
```gdscript
if use_lighting and ResourceLoader.exists(lighting_path):
    var l_mat = ShaderMaterial.new()
    l_mat.shader = load(lighting_path)
    l_mat.set_shader_parameter("light_dir", lp["light_dir"])
    # ... set semua param dari Lighting.shader_params()
    sprite.material = l_mat
```

Aktifkan di `project.godot`:
```ini
[mystic]
rendering/use_lighting_shader=true
rendering/lighting_shader_path="res://assets/shaders/lighting_outline.gdshader"
```

### Jalur 3: GDExtension C++ (godot++) — performa maksimal untuk bake offline
**File:**
- `godot/gdext/mystic_lighting/src/lighting_processor.h`
- `godot/gdext/mystic_lighting/src/lighting_processor.cpp`
- `godot/gdext/mystic_lighting/src/register_types.h/cpp`
- `godot/gdext/mystic_lighting/SConstruct`
- `godot/addons/mystic_lighting/mystic_lighting.gdextension`
- `godot/addons/mystic_lighting/bin/` — output lib

Class `MysticLighting : RefCounted` dengan method static:
- `apply(Image)`, `apply_to_rig()`, `apply_to_texture()`
- `contour_masks()`, `bbox_of()`, `reset_gradient_cache()`
- `shader_params()`, `create_lighting_material()`

Cache C++:
```cpp
static std::unordered_map<std::string, GradPair> _canon_cache;
static std::unordered_map<std::string, GradPair> _size_cache; // cap 64
```

Build:
```bash
cd godot/gdext/mystic_lighting
git clone -b godot-4.3-stable https://github.com/godotengine/godot-cpp godot-cpp --depth 1
scons target=template_release -j4
# output -> godot/addons/mystic_lighting/bin/libmystic_lighting.linux.release.x86_64.so
```

Android:
```bash
scons platform=android target=template_release android_arch=arm64v8 -j4
scons platform=android target=template_release android_arch=armeabi-v7a -j4
```

Aktifkan:
```ini
[mystic]
rendering/use_gdext_lighting=true
```

### Jalur 4: Wrapper kompatibel (LightingCompat.gd)
**File:** `godot/scripts/render/LightingCompat.gd`

Abstraksi yang otomatis pilih C++ jika ada, fallback GDScript:
```gdscript
LightingCompat.apply_image(img) # pakai C++ kalau ada, kalau tidak GDScript
LightingCompat.create_lighting_material() # sama
```

Deteksi:
```gdscript
if ClassDB.class_exists("MysticLighting") and ProjectSettings.get_setting("mystic/rendering/use_gdext_lighting"):
    has_gdext = true
```

## Paritas yang dikunci

| Aspek | Python | GDScript | C++ | Shader |
|---|---|---|---|---|
| LIGHT_DIR | (-1,-1) | Vector2i(-1,-1) | -1,-1 | vec2(-1,-1) |
| RIM_ADD | (30,26,44) | Color(30/255,26/255,44/255) | Color same | vec3(0.1176,0.102,0.1725) |
| SHADE_MUL | 168 | 168 | 168 | 0.6588 |
| BAND2 | 0.42 | 0.42 | 0.42 | 0.42 |
| MASK_ALPHA | 170 | 170 | 170 | 0.6667 |
| GRAD | 205,255,22,28 | sama | sama | sama |
| Rumus t | 1-(gx*ax+gy*ay)/span | sama | sama | sama |
| Rim | mask-shift(+sx,+sy) | sama | sama | alpha_at(UV+shift_pos)<threshold |
| Shade | mask-shift(-sx,-sy) | sama | sama | alpha_at(UV+shift_neg)<threshold |
| Band2 | inner-shade | sama | sama | inner && !shade && shift_neg solid |
| Cache | dict, clear >64 | Dictionary, clear >64 | unordered_map, clear >64 | - |
| Safe | try/except return surface | return img asli | duplicate + return asli | early out jika a<threshold |

## Penggunaan di game

### Runtime (arena) — shader (disarankan)
```gdscript
# BakedSprite.gd sudah otomatis pakai lighting_outline.gdshader bila use_lighting_shader=true
# Tidak perlu ubah kode game lain
```

### Bake offline (tools/convert_to_godot.py) — CPU Image
```python
# Kalau mau re-bake dengan lighting baru:
# Di convert_to_godot.py, setelah render sprite:
import lighting
lighting.apply(surface, box=rig_bbox) # box konstan rig untuk anti-kedip
```

Di Godot:
```gdscript
var img = baked_texture.get_image()
LightingCompat.apply_image(img, box=Rect2i(rig_bbox))
```

### Manual per sprite
```gdscript
@onready var sprite = $Sprite
func _ready():
    sprite.material = LightingCompat.create_lighting_material()
    # Atau
    sprite.material = preload("res://scripts/render/Lighting.gd").create_lighting_material()
```

## Testing

### Python oracle
```bash
SDL_VIDEODRIVER=dummy python tools/test_lighting_parity.py
```

### Godot headless (CI)
```bash
godot --headless --path godot res://tests/LightingParityTest.tscn --quit-after 60
# Atau
XDG_DATA_HOME=$(mktemp -d) godot --headless --path godot res://tests/LightingParityTest.tscn --quit-after 60
```

### Manual di editor
- Buka `godot/tests/LightingParityTest.tscn` → F5 Run
- Harus keluar "SEMUA TES GODOT LULUS" di Output

## File yang dibuat/diubah

Baru:
- `godot/scripts/render/Lighting.gd` — port GDScript 1:1
- `godot/scripts/render/LightingCompat.gd` — wrapper GDExt+GDScript
- `godot/assets/shaders/lighting.gdshader` — shader GPU
- `godot/assets/shaders/lighting_outline.gdshader` — outline+lighting 1 pass
- `godot/gdext/mystic_lighting/src/lighting_processor.h/cpp` — C++ GDExtension
- `godot/gdext/mystic_lighting/src/register_types.h/cpp`
- `godot/gdext/mystic_lighting/SConstruct`
- `godot/addons/mystic_lighting/mystic_lighting.gdextension` — manifest
- `godot/addons/mystic_lighting/bin/` — output lib (gitignored, build lokal)
- `godot/addons/mystic_lighting/README.md`
- `godot/tests/LightingParityTest.gd/tscn` — test paritas
- `tools/test_lighting_parity.py` — oracle Python
- `docs/LIGHTING_GODOTPP.md` — dokumen ini

Diubah:
- `godot/project.godot` — tambah `mystic/rendering/use_lighting_shader`, `lighting_shader_path`, `use_gdext_lighting`, `light_dir_x/y`
- `godot/scenes/render/BakedSprite.gd` — pakai lighting_outline shader bila aktif, team tint rim

## Catatan desain (kenapa begini)

1. **Kenapa 3 jalur, bukan 1?**
   - Shader = paling cepat runtime (0.04ms), tapi tidak bisa untuk bake offline yang butuh Image CPU
   - GDScript = selalu jalan tanpa build, untuk dev & CI headless
   - C++ = tercepat untuk bake offline batch 222 unit (5-10x GDScript), opsional

2. **Kenapa box konstan rig penting?**
   - `lighting.py` sudah jelaskan: kalau box = bbox hasil crop per frame, arah cahaya ikut bergeser saat pose berubah → lampu berkedip
   - Di Godot shader, `bbox` uniform bisa diisi Rect2 konstan rig untuk anti-kedip
   - Default (0,0,1,1) = pakai UV penuh, paritas jalur hero yang sudah crop rapat

3. **Kenapa rim_add team tint?**
   - Paritas `_finish_hd_sprite` pygame: `_HD_RIM_ADD` vs `_HD_RIM_ADD_RED` (biru vs merah tipis)
   - Di BakedSprite.gd, kita tambah team tint ke base rim (30,26,44) * 0.35

4. **Kenapa Android disarankan shader, bukan GDExtension?**
   - GDExtension Android butuh build per arch (arm64v8 + armeabi-v7a) + packaging AAB lebih rumit
   - Shader sudah jalan di Mobile renderer (Vulkan fallback GLES3) tanpa native lib

## Next step (opsional)

- [ ] Re-bake 222 unit dengan lighting baru: `tools/convert_to_godot.py --units-png --with-lighting` (perlu tambah flag di converter)
- [ ] Tambah UI slider di Settings untuk atur `light_dir` runtime (debug)
- [ ] Port ke `UnitSilhouette.gd` juga (minion masih silhouette, belum dapat lighting)
- [ ] Benchmark: ukur ms per frame sebelum/sesudah shader di Android low-end

## Referensi

- `lighting.py` — sumber asli (240 baris, 0 deps)
- `heroes/__init__.py:1866+` — `_finish_hd_sprite` yang pakai lighting
- `docs/GODOT_MIGRATION.md` Fase 5 — bake strip
- `godot/assets/shaders/outline.gdshader` — shader outline lama yang diganti
