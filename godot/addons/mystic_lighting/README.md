# Mystic Lighting GDExtension (godot++)

Port C++ dari `lighting.py` ke Godot 4 GDExtension.

## Struktur
- `bin/` — hasil build library (.so/.dll/.dylib)
- `mystic_lighting.gdextension` — manifest GDExtension (auto-load Godot)
- `../gdext/mystic_lighting/` — source C++

## Build
Butuh `godot-cpp` dan SCons.

```bash
cd godot/gdext/mystic_lighting

# 1. Clone godot-cpp (sekali)
git clone --depth 1 -b godot-4.3-stable https://github.com/godotengine/godot-cpp.git
# atau untuk 4.4:
# git clone --depth 1 -b 4.3 https://github.com/godotengine/godot-cpp.git

# 2. Build godot-cpp
cd godot-cpp
scons target=template_release -j4
cd ..

# 3. Build extension
scons target=template_release -j4
# atau debug:
scons target=template_debug -j4

# Output ke godot/addons/mystic_lighting/bin/
```

Di Windows:
```powershell
scons target=template_release vsproj=yes
```

## Penggunaan dari GDScript

Tanpa GDExtension (fallback murni GDScript) sudah jalan:
```gdscript
var lighting = preload("res://scripts/render/Lighting.gd")
var img = texture.get_image()
lighting.apply(img)
```

Dengan GDExtension (lebih cepat 5-10x, <0.5ms per sprite 90x90):
```gdscript
var img = texture.get_image()
MysticLighting.apply(img) # C++ version
var tex = ImageTexture.create_from_image(img)
sprite.texture = tex
```

Atau material shader (jalur utama runtime, 0.04ms GPU):
```gdscript
sprite.material = MysticLighting.create_lighting_material()
# atau
sprite.material = preload("res://scripts/render/Lighting.gd").create_lighting_material()
```

## Paritas dengan lighting.py

| Python | C++ / GDScript |
|---|---|
| `LIGHT_DIR = (-1,-1)` | `LIGHT_DIR_X/Y = -1` |
| `RIM_ADD = (30,26,44)` | `Color(30/255,26/255,44/255)` |
| `SHADE_MUL = 168` | `168` |
| `BAND2_RATIO = 0.42` | `0.42` |
| `MASK_ALPHA = 170` | `170` |
| `GRAD_DARK=205 LIGHT=255 SHEEN=22 STEPS=28` | sama |
| `_canonical()` | `_canonical()` |
| `_sized()` | `_sized()` |
| `contour_masks()` | `contour_masks_gd()` |
| `apply()` | `apply()` |
| `apply_to_rig()` | `apply_to_rig()` |
| `reset_gradient_cache()` | `reset_gradient_cache()` |

## Integrasi otomatis

`BakedSprite.gd` sudah dimodifikasi untuk pakai shader `lighting_outline.gdshader` bila `mystic/rendering/use_lighting_shader = true` di ProjectSettings.

Aktifkan di `project.godot`:
```ini
[mystic]
rendering/use_lighting_shader=true
rendering/use_gdext_lighting=false # true kalau GDExtension sudah dibuild
```

## Catatan Android

GDExtension di Android butuh build terpisah:
```bash
scons platform=android target=template_release android_arch=arm64v8 -j4
scons platform=android target=template_release android_arch=armeabi-v7a -j4
```

Tapi untuk Android, jalur shader lebih direkomendasikan (tidak perlu native lib).
