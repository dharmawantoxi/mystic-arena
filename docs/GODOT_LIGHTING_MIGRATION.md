# Migrasi `lighting.py` → Godot (`godot_rebuild/`)

Status: **native GDScript/Image API, tanpa Python saat runtime**. Melanjutkan
migrasi `main.py` (#377), `_core.py` (#378), `_entity.py` (#379), `_render.py`
(#380), `_system.py` (#381), `hero_archetypes.py` (#382), `hero_balance.py`
(#383), dan `hero_items.py` (#384). Python tetap menjadi sumber kebenaran dan
oracle pixel; port ini **tidak** mengubah angka lighting, arah cahaya, atau
urutan blend.

## Cakupan

| Sumber Python | Native Godot | Catatan |
|---|---|---|
| `LIGHT_DIR`, `RIM_ADD`, `SHADE_MUL`, `BAND2_RATIO`, `MASK_ALPHA`, `GRAD_*`, `_GRAD_STEPS` | `scripts/render/Lighting.gd` + `data/lighting.json` | Kontrak fail-closed dengan SHA-256 `lighting.py`. |
| `_canonical()` grid mul/add 28×28 | `Lighting.canonical(config)` | Array RGB diekspor dari pygame, bukan dihitung ulang dengan float GPU. |
| `_sized()` + `pygame.transform.smoothscale` | `Lighting.gradient(size, config)` + `LightingResampler.gd` | Clone integer separable X→Y backend GENERIC pygame 2.6.1, termasuk truncation antar sumbu. |
| `_SIZE_CACHE` >64.clear, `reset_gradient_cache()` | cache ukuran native, batas 65, `reset_gradient_cache()/clear_cache()` | Cache dibersihkan saat quality berubah / match selesai. |
| `contour_masks(surface, alpha, width)` | `Lighting.contour_masks(image, alpha, width)` | Mask rim/shade berbasis alpha **strictly > threshold**, guard ukuran ≤2 dan solid <24. |
| `_bbox_of()` | `Lighting.bbox_of(image, alpha)` | Rect2i piksel solid, kosong bila tidak ada. |
| `apply(...)` gradient MULT+ADD, terminator, rim ADD | `Lighting.apply(image, options)` | In-place RGB-only; alpha tidak disentuh. |
| `apply_to_rig(enabled=...)` | `Lighting.apply_to_rig(image, enabled, options)` | Kill-switch dan perilaku partial-error pygame direplikasi. |
| Kualitas `hero_lighting` | `RenderQuality.preset()` + `EntityVisuals.configure()` | Low mematikan lighting runtime; medium/high menyala. |

## Arsitektur runtime

```text
data/lighting.json
  └── Lighting.gd (kontrak, cache canonical/ukuran, mask, blend)
        └── LightingResampler.gd (smoothscale integer GENERIC)

EntityVisuals.gd
  ├── strip baked default: lighting_baked=true -> TIDAK diproses ulang
  └── raw import opt-in: lighting_baked=false + RenderQuality.hero_lighting
        └── lit_frame_texture() cache maks 128 frame, invalidasi saat quality berubah

CoreGame.gd
  └── configure()/apply_render_quality() -> EntityVisuals.configure(preset)
```

- Sprite strip yang sudah dibake oleh renderer Python **sudah mengandung
  lighting**. Default native tidak menerapkan pass kedua, sehingga tidak ada
  double rim/shade pada pahlawan/boss yang sudah ada.
- Jalur runtime hanya untuk tekstur mentah yang secara eksplisit declaring
  `lighting_baked=false` di manifest. Opsi per-unit dapat memakai kunci
  `lighting` (`rim_add`, `shade_mul`, `gradient`, `two_band`, `box`, `alpha`).
- `box` adalah bidang acuan gradien. Default mengikuti sumber: seluruh surface,
  bukan bbox per frame, agar arah cahaya tidak berkedip saat pose berubah.
- Ini pass CPU `Image`, bukan shader GPU. Tidak ada klaim paritas visual GPU
  atau performa perangkat mobile sampai diukur di perangkat nyata.

## Semantik pixel yang dikunci

1. `BLEND_RGB_MULT` pygame 2.6.1 memakai `(dst * src + 255) >> 8`
   (ceil terhadap 256), bukan pembulatan `/255` biasa.
2. `BLEND_RGB_ADD` menjenuhkan di 255; alpha tujuan dipertahankan. Piksel
   transparan di dalam box gradient tetap menerima perubahan RGB, persis
   seperti sumber.
3. Mask alpha memakai threshold **strictly greater**: alpha 170 tidak masuk,
   171 masuk.
4. Terminator dua band meniru quirk sumber: mask band-2 diblit dengan
   `unsetcolor` putih opaque, sehingga saat `two_band` aktif ia menimpa
   multiplier deep-shade di luar ring band-2.
5. Warna rim di luar 0..255 membuat pygame melempar `ValueError` setelah
   gradient/terminator mengubah surface. `apply_to_rig` menelan error itu;
   native menghasilkan hasil partial yang sama: gradient/terminator terjadi,
   rim ADD dilewati.
6. Box negatif/invalid menjadi no-op untuk keselamatan GDScript, sesuai kasus
   oracle yang mengunci perilaku fail-closed.

## Kontrak data & tooling

```bash
# Setelah mengubah lighting.py:
python3 tools/prepare_godot_lighting.py
python3 tools/prepare_godot_lighting.py --check
python3 tools/test_godot_lighting_prepare.py
python3 tools/test_lighting_parity.py
python3 tools/test_hero_lighting.py
```

Exporter mengimpor `lighting.py` asli dengan `pygame==2.6.1`, mem-pin backend
smoothscale `GENERIC`, lalu memulihkan backend/cache. Ia menulis:

- `godot_rebuild/data/lighting.json`: konstanta, grid canonical 28×28, batas
  cache, identitas resampler, SHA-256 sumber.
- `godot_rebuild/tests/fixtures/lighting_parity.json`: 8 kasus contour/bbox,
  40 kasus gradient (SHA-256 RGB + sampel), 19 kasus apply pixel RGBA.

`--check` tidak menulis ulang file; ia gagal bila kontrak/fixture hilang atau
tidak byte-identik dengan hasil ekspor deterministik.

## Batas jujur

- Tidak ada rebake sprite.Cacat bake yang sudah diketahui tetap tercatat di
  migrasi entity; lighting tidak memperbaikinya secara diam-diam.
- Belum ada benchmark FPS/perangkat nyata untuk jalur raw CPU lighting.
- Tidak ada shader/GDExtension lighting baru; klaim hanya pada port GDScript
  dan fixture oracle yang diuji.
- Jalur hero/boss existing tetap memakai strip baked; integrasi runtime adalah
  opt-in untuk aset mentah, bukan penggantian renderer baked.
