"""lighting.py - model pencahayaan kecil untuk sprite prosedural.

Kenapa modul ini ada
-------------------
Renderer prosedural di proyek ini membangun volume dengan BLOK NILAI yang
di-author manual (skin_dark -> skin_mid -> skin_light). Itu bertahan di
ukuran besar, tapi di 720p hasilnya masih terbaca sebagai "tumpukan pita
datar" - bukan badan yang kena cahaya - karena tidak ada apa pun yang
menghubungkan nilai-nilai itu dengan SATU arah cahaya yang konsisten, dan
tidak ada terminator (garis gelap-terang) di sepanjang siluet.

Modul ini menambahkan tahap yang murah dan universal: dari mask alpha
sprite, turunkan

  * rim light   : piksel terluar di sisi cahaya  -> RGB di-ADD sedikit
  * terminator  : piksel terluar di sisi bayangan -> RGB di-MULT darker
  * band kedua  : 1 px di dalamnya, 40% kekuatan  -> terasa seperti gradien

Semua dihitung dari mask saja, jadi BEBAS dari bentuk karakter: berlaku
untuk boss yang digambar langsung (Gornak, dst.) maupun untuk keenam hero
masterwork lewat `_finish_hd_sprite`. Tidak ada numpy, tidak ada
image.load, tidak ada aset - aturan "100% prosedural" tetap utuh, dan
karena operasinya byte-per-piksel pada sprite ~90x90, biayanya di bawah
setengah milidetik (jalur hero hanya dibayar saat cache miss).

Arah cahaya
-----------
Cahaya datang dari kiri-atas (LIGHT_DIR = (-1, -1)) - cocok dengan highlight
yang sudah di-author di semua renderer (kulit terang di kiri-atas,
`*_shine` di tepi atas pelat & bahu). Mengubahnya = mengubah SISI rim dan
terminator, tidak perlu menyentuh renderer mana pun.
"""

import pygame

# Arah datang cahaya (x, y) dalam piksel; (-1,-1) = kiri-atas.
LIGHT_DIR = (-1, -1)

# Kekuatan default. Sengaja konservatif: rim/terminator 1 px yang terlalu
# terang membuat semua karakter terlihat "berbingkai plastik" setelah
# smoothscale jalur hero.
RIM_ADD = (30, 26, 44)
SHADE_MUL = 168          # 0..255, pengali RGB di band terminator
BAND2_RATIO = 0.42       # kekuatan band kedua relatif band pertama
MASK_ALPHA = 170         # ambang mask: AA tepi tidak ikut jadi rim

# Gradien arah untuk SELURUH badan (bukan cuma kontur). Tanpa ini, rim 1 px
# hanya "menggambar ulang tepi" dan blok nilai yang di-author manual tetap
# terlihat datar di tengah badan. Gradien dibuat sekali per ukuran sprite
# pada kisi kecil lalu di-smoothscale (lihat _gradient()) - jadi biayanya
# satu blit per frame, bukan loop per-piksel.
GRADIENT_ENABLED = True
GRAD_DARK = 205          # pengali RGB di sudut terjauh dari cahaya
GRAD_LIGHT = 255         # pengali di sudut yang menghadap cahaya
GRAD_SHEEN = 22          # ADD maksimum di sudut cahaya (band specular)
_GRAD_STEPS = 28         # resolusi kisi gradien sebelum di-upscale


def _shifted_mask(mask, dx, dy):
    """Salinan mask digeser (dx, dy); area kosong dianggap luar."""
    w, h = mask.get_size()
    out = pygame.Mask((w, h))
    out.draw(mask, (dx, dy))
    return out


_CANON_CACHE = {}      # gradien kanonik 28x28 (tidak tergantung ukuran)
_SIZE_CACHE = {}       # hasil upscale-nya, key (w, h)


def _canonical(dark, light, sheen):
    """Kisi gradien kecil pada sumbu cahaya - dibuat SEKALI per konfigurasi.

    Sengaja dipisah dari ukuran sprite: yang berubah tiap frame biasanya
    hanya bbox hasil crop, jadi kisi kanoniknya bisa dipakai terus dan
    per-frame tinggal satu smoothscale murah.
    """
    key = (dark, light, sheen, LIGHT_DIR)
    hit = _CANON_CACHE.get(key)
    if hit is not None:
        return hit
    n = _GRAD_STEPS
    mul = pygame.Surface((n, n), pygame.SRCALPHA)
    add = pygame.Surface((n, n), pygame.SRCALPHA)
    ax, ay = abs(LIGHT_DIR[0]), abs(LIGHT_DIR[1])
    span = (n - 1) * (ax + ay)
    for gy in range(n):
        for gx in range(n):
            # t = 1 di sudut cahaya (kiri-atas), 0 di sudut bayangan
            t = 1.0 - (gx * ax + gy * ay) / max(1.0, span)
            t = max(0.0, min(1.0, t))
            v = int(round(dark + (light - dark) * t))
            mul.set_at((gx, gy), (v, v, v, 255))
            k = int(round(sheen * (t ** 2.2)))
            add.set_at((gx, gy), (k, k, int(k * 1.25), 255))
    _CANON_CACHE[key] = (mul, add)
    return mul, add


def _sized(w, h, dark=GRAD_DARK, light=GRAD_LIGHT, sheen=GRAD_SHEEN):
    key = (w, h, dark, light, sheen)
    hit = _SIZE_CACHE.get(key)
    if hit is not None:
        return hit
    if len(_SIZE_CACHE) > 64:
        _SIZE_CACHE.clear()
    mul, add = _canonical(dark, light, sheen)
    mul = pygame.transform.smoothscale(mul, (w, h))
    add = pygame.transform.smoothscale(add, (w, h))
    _SIZE_CACHE[key] = (mul, add)
    return mul, add


def reset_gradient_cache():
    """Dipakai test / saat skala atau arah cahaya diubah runtime."""
    _SIZE_CACHE.clear()


def contour_masks(surface, alpha=MASK_ALPHA, width=1):
    """(rim_mask, shade_mask) dari alpha surface.

    rim   = mask - shift(mask, +sx, +sy)   -> sisi yang MENGHADAP cahaya
    shade = mask - shift(mask, -sx, -sy)   -> sisi yang Membelakangi cahaya
    dengan shift mengikuti LIGHT_DIR, sehingga geserannya selalu "masuk" ke
    sisi cahaya.
    """
    if surface.get_width() <= 2 or surface.get_height() <= 2:
        return None, None
    try:
        solid = pygame.mask.from_surface(surface, alpha)
    except (pygame.error, ValueError):
        return None, None
    if solid.count() < 24:                   # sprite terlalu kecil/terpuruk
        return None, None
    sx, sy = abs(LIGHT_DIR[0]) * width, abs(LIGHT_DIR[1]) * width
    # tanda geseran: cahaya kiri-atas -> sisi terang adalah piksel yang
    # TIDAK ada di salinan yang digeser ke kanan-bawah.
    rim = solid.copy()
    rim.erase(_shifted_mask(solid, sx, sy), (0, 0))
    shade = solid.copy()
    shade.erase(_shifted_mask(solid, -sx, -sy), (0, 0))
    return rim, shade


def apply(surface, rim_add=RIM_ADD, shade_mul=SHADE_MUL, two_band=True,
          alpha=MASK_ALPHA, gradient=GRADIENT_ENABLED, box=None):
    """Beri cahaya IN-PLACE pada sprite: gradien arah + rim + terminator.

    Hanya RGB yang disentuh (BLEND_RGB_*), alpha sprite tidak berubah -
    penting karena jalur hero mengandalkan alpha untuk outline & colorkey.
    """
    if surface.get_width() <= 2 or surface.get_height() <= 2:
        return surface
    rim, shade = contour_masks(surface, alpha=alpha)
    if rim is None:
        return surface

    if gradient:
        # `box` = bidang acuan cahaya. Kalau dibiarkan None, dipakai seluruh
        # surface - itu TEPAT untuk jalur hero (sprite yang masuk ke sini
        # sudah hasil crop rapat, lihat _finish_hd_sprite) dan murah.
        # Untuk renderer yang menggambar ke buffer tetap (boss), pengirim
        # sebaiknya mengoper box KONSTANTA milik rig: menormalkan ke bbox
        # hasil render per frame membuat arah cahaya IKUT BERGESER saat
        # pose berubah, dan itu terbaca sebagai lampu yang berkedip - selain
        # itu membuat cache ukuran miss tiap frame (~1,5 ms, terukur).
        w, h = surface.get_size()
        bx, by, bw, bh = box if box else (0, 0, w, h)
        bw = max(2, min(bw, w - bx))
        bh = max(2, min(bh, h - by))
        if bw > 2 and bh > 2:
            mul, add = _sized(bw, bh)
            sub = surface.subsurface(pygame.Rect(bx, by, bw, bh))
            sub.blit(mul, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            sub.blit(add, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    w, h = surface.get_size()
    neutral = max(0, min(255, int(shade_mul)))

    # ---- terminator (sisi bayangan): band1 gelap, band2 lebih lemah ----
    if two_band:
        outer, inner = contour_masks(surface, alpha=alpha, width=2)
        deep = shade.copy() if shade is not None else None
        wide = inner
        if wide is not None and deep is not None:
            wide.erase(deep, (0, 0))
    else:
        wide = None

    mul = pygame.Surface((w, h), pygame.SRCALPHA)
    mul.fill((255, 255, 255, 255))
    if shade is not None:
        mul.blit(shade.to_surface(setcolor=(neutral, neutral, neutral, 255),
                                 unsetcolor=(255, 255, 255, 255)), (0, 0))
    if wide is not None:
        k = max(0, min(255, int(255 - (255 - neutral) * BAND2_RATIO)))
        mul.blit(wide.to_surface(setcolor=(k, k, k, 255),
                                 unsetcolor=(255, 255, 255, 255)), (0, 0))
    surface.blit(mul, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    # ---- rim light (sisi cahaya) ----
    add = pygame.Surface((w, h), pygame.SRCALPHA)
    add.fill((0, 0, 0, 255))
    if rim is not None:
        add.blit(rim.to_surface(
            setcolor=(int(rim_add[0]), int(rim_add[1]), int(rim_add[2]), 255),
            unsetcolor=(0, 0, 0, 255)), (0, 0))
    surface.blit(add, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    return surface


def _bbox_of(surface, alpha=MASK_ALPHA):
    """Bbox piksel SOLID sprite (x, y, w, h), atau None."""
    try:
        m = pygame.mask.from_surface(surface, alpha)
        r = m.get_bounding_rects()
    except (pygame.error, ValueError):
        return None
    if not r:
        return None
    x0 = min(q.left for q in r)
    y0 = min(q.top for q in r)
    x1 = max(q.right for q in r)
    y1 = max(q.bottom for q in r)
    return (x0, y0, max(1, x1 - x0), max(1, y1 - y0))


def apply_to_rig(surface, enabled=True, **kw):
    """Versi aman untuk renderer: tidak pernah membuat gambar gagal.

    Renderer hero/boss tidak boleh crash hanya karena backend SDL tertentu
    tidak mendukung operasi mask - jadi semua kesalahan ditelan dan sprite
    kembali apa adanya (persis kebijakan _finish_hd_sprite).
    """
    if not enabled:
        return surface
    try:
        return apply(surface, **kw)
    except (pygame.error, ValueError):
        return surface
