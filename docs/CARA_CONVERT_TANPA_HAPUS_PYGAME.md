# Cara Convert Pygame → Godot **Tanpa Menghapus Pygame**

> Pygame tetap jalan 100%. Godot hidup di folder terpisah `godot/`. Data cuma di-**copy**, bukan di-**pindah**.

```
mystic-arena/               ← ROOT (satu repo, dua engine)
├── main.py                 ← Pygame tetap (jalan seperti biasa)
├── _core.py                ← sumber data hero
├── heroes/                 ← 222 hero pygame (JANGAN dihapus)
├── bosses/                 ← 216 boss
├── levels/                 ← 54 level
├── buildozer.spec          ← Android Pygame (tetap)
│
├── godot/                  ← Godot hidup di sini SAJA (terisolasi)
│   ├── project.godot       ← project Godot 4.3 Forward+
│   ├── data/*.json         ← hasil COPY dari pygame (bukan pindahan)
│   ├── scenes/hero/kaizen/ ← contoh flagship Skeleton2D
│   ├── shaders/hamon.gdshader
│   └── export_presets.cfg  ← Android Godot (AAB) — package SAMA
│
└── tools/convert_to_godot.py ← jembatan read-only pygame → json
```

**Prinsip:** `tools/convert_to_godot.py` cuma **MEMBACA** `import _core, bosses.boss_data, levels.level_data`, lalu **MENULIS** `godot/data/*.json`. Tidak ada `os.remove`, tidak ada `shutil.move`. Pygame tidak pernah disentuh.

---

## Step-by-step (3 menit, aman)

### Langkah 0 — Cek posisi (kamu di branch aman)
```bash
pwd                    # harus /home/user/mystic-arena
git branch --show-current
# arena/01a075b1-mystic-arena  ← branch Godot, pygame di main tetap utuh
git status --short     # yang muncul cuma ?? godot/ ?? tools/convert_to_godot.py — tidak ada D (delete) di heroes/ atau _core.py
```

Kenapa aman? Semua file Godot itu **untracked** (`??`). File pygame tidak ada yang `D` atau `M`. Artinya Godot cuma **tambahan**, bukan pengganti.

### Langkah 1 — Install dependensi converter (sekali saja)
Converter butuh `pygame-ce` cuma untuk import data (tidak buka window). Tidak mengganggu `main.py`.

```bash
pip install pygame-ce --break-system-packages -q
python -c "import pygame; print(pygame.__version__)"
# 2.5.8 ok
```

> Di laptop/CI yang sudah punya `pygame` tidak perlu lagi. Flag `--break-system-packages` cuma karena PEP 668 di Debian.

### Langkah 2 — Jalankan converter (read-only)

```bash
python tools/convert_to_godot.py
```

Output yang benar:
```
[convert] heroes.json: 222 entries -> /home/user/mystic-arena/godot/data/heroes.json
[convert] bosses.json: 216 entries -> /home/user/mystic-arena/godot/data/bosses.json
[convert] levels.json: 54 entries -> /home/user/mystic-arena/godot/data/levels.json
[convert] hero_archetypes.json: 222 entries -> ...
[convert] items.json: 33 entries -> ...
[convert] Done.
```

Apa yang terjadi di dalam (`tools/convert_to_godot.py` baris 14-18):
```python
ROOT = os.path.dirname(os.path.dirname(__file__))  # mystic-arena/
GODOT_DATA = os.path.join(ROOT, "godot", "data")
os.makedirs(GODOT_DATA, exist_ok=True)           # bikin folder godot/data kalau belum ada
sys.path.insert(0, ROOT)                         # supaya bisa `from _core import ...` tanpa pindah file
```
Lalu tiap fungsi `export_*` cuma:
```python
from _core import get_all_hero_types   # baca dict HERO_TYPES
simple[k] = {"hp": v["hp"], "damage": v["damage"], ...}
json.dump(simple, open("godot/data/heroes.json","w"))
```
**Tidak ada** kode yang menghapus `heroes/_bundle.py` atau mengubah `_core.py`.

Verifikasi tidak ada yang hilang:
```bash
ls heroes | wc -l          # tetap 222 file hero pygame
ls bosses/level*.py | wc -l # tetap 54 level
wc -l godot/data/*.json    # 10045 baris (222+216+54+222+33 sudah ter-copy)
# bandingkan:
wc -l _core.py hero_archetypes.json  # file asli tetap ada
```

### Langkah 3 — Buktikan pygame tetap jalan

```bash
# Pygame (cara lama, harus tetap bisa)
python main.py
# atau
python -c "from _core import get_all_hero_types; print(len(get_all_hero_types()))"
# 222

# Godot (cara baru, terpisah)
godot godot/project.godot
# atau headless cek:
godot --headless --path godot --quit  # kalau Godot terinstall, exit 0 = project valid
```

Keduanya baca **sumber yang sama** tapi jalur beda:
- Pygame baca langsung `HERO_TYPES` dict di RAM
- Godot baca `godot/data/heroes.json` (snapshot copy)

### Langkah 4 — Buka & tes Kaizen di Godot (tanpa dot mengganggu pygame)

```bash
godot godot/project.godot &
# Di Godot Editor:
# 1. FileSystem dock → klik godot/scenes/demo/KaizenDemo.tscn
# 2. Tekan F6 (Run Current Scene) — bukan F5
#    Akan muncul siklus idle 3s → walk 3s → attack loop dengan hamon berkilau
# 3. Tekan SPACE = force attack, F = flip, R = reset
```

Kalau mau tes di arena utama (tetap tidak hapus pygame):
- Godot `scenes/main.tscn` → F5 → hero Kaizen sudah pakai Skeleton2D 25 tulang (fallback hero lain masih kotak warna + shader)

### Langkah 5 — Sync kalau balance berubah (workflow harian)

Setiap kali kamu edit balance di pygame (misal `_core.py`, `hero_balance.py`, `bosses/boss_data.py`, `levels/level_data.py`):

```bash
# 1. Edit seperti biasa di pygame
nano _core.py
# atau
nano hero_archetypes.json

# 2. Test pygame dulu (wajib)
python main.py

# 3. Copy ulang ke Godot (1 perintah, tidak hapus apa pun)
python tools/convert_to_godot.py

# 4. Test Godot
godot godot/project.godot   # F5 / F6 KaizenDemo

# 5. Commit terpisah (opsional tapi rapi)
git add _core.py hero_archetypes.json          # perubahan pygame
git add godot/data/*.json                      # snapshot Godot
git commit -m "balance Kaizen hp 850→900 + sync godot data"
```

**Jangan edit `godot/data/*.json` manual** — nanti ketimpa pas convert. Sumber kebenaran tetap `*_core.py` + `heroes/` + `bosses/`.

### Langkah 6 — Android: dua jalur build, tidak tabrakan

| Engine | Config | Build | Output |
|---|---|---|---|
| **Pygame** | `buildozer.spec` (package `io.github.dharmawantoxi.mysticarena`) | `buildozer android debug` (8-12 menit) | `bin/*.apk` |
| **Godot** | `godot/export_presets.cfg` (package **sama** `io.github.dharmawantoxi.mysticarena`) | Godot Editor → Project → Export → Android → Export AAB (45 detik) | `godot/build/MysticArena.aab` |

Package SAMA sengaja — save `user://` / cloud tetap kebaca kalau migrasi full nanti. Selama fase dual-engine, build keduanya boleh hidup berdampingan. Mau publish Godot tidak perlu hapus `buildozer.spec`.

### Langkah 7 — Git: cara push tanpa nimpa main pygame

```bash
git status
# ?? godot/  ?? tools/convert_to_godot.py  ?? docs/AUDIT_ULANG_DARI_AWAL.md
# M hero_balance.py  (kalau kamu edit balance)

# Commit cuma file Godot + data json (pygame tetap)
git add tools/convert_to_godot.py godot/ docs/AUDIT_ULANG_DARI_AWAL.md
git commit -m "feat(godot): kaizen skeleton 25 bones + hamon + demo (pygame tetap)"

# Push ke branch ARENA saja (jangan ke main)
git push origin arena/01a075b1-mystic-arena

# main tetap murni pygame, bisa cek:
git checkout main -- _core.py main.py  # tidak akan ada file godot di main kalau belum merge
```

Kalau suatu saat mau full migrasi, tinggal `git merge arena/01a075b1-mystic-arena` ke `main` — `godot/` akan masuk sebagai folder baru, tidak menimpa `heroes/`. Rollback juga gampang: `git rm -r godot/`.

---

## FAQ yang sering ditanya

**Q: Apakah `godot/data/heroes.json` duplikat `hero_archetypes.json`? Kenapa tidak symlink?**
A: Duplikat sengaja (snapshot). Godot butuh JSON statis tanpa import Python. Symlink atau import langsung `hero_archetypes.json` bisa, tapi nanti Godot tidak bisa baca `HERO_TYPES` yang di-generate dari `_core.py` logic (hitung stat balance). Converter menggabungkan keduanya jadi satu.

**Q: Kaizen di Godot kok 25 tulang, di pygame tidak ada tulang?**
A: Pygame `heroes/_bundle.py` gambar pakai `pygame.draw.polygon` procedural 2906 baris, tidak ada konsep tulang. Godot mengubahnya jadi `Skeleton2D` — pose busur `ATTACK_ARC_START=-2.30 sweep -3.05` diambil 1:1 dari kode pygame, jadi animasi tetap identik tapi sekarang GPU-interpolasi 60fps.

**Q: Bagaimana kalau saya hapus `godot/` apakah pygame rusak?**
A: Tidak. `godot/` tidak pernah di-import oleh `main.py`, `_core.py`, atau `buildozer.spec`. Hapus folder `godot/` → `python main.py` tetap jalan.

**Q: Data 222 hero → 216 boss → 54 level, kok bisa beda?**
A: 222 hero = semua playable (termasuk boss-hero). 216 boss = mini+boss sejati (filter `boss_class`). 54 level = `levels.level_data.ALL_LEVELS` (bukan `LEVELS`). Converter sudah handle `getattr(ld,"ALL_LEVELS", ...)` + fallback 54 dummy kalau gagal.

**Q: Kenapa `export_presets.cfg` tidak bentrok dengan `buildozer.spec`?**
A: Beda folder & beda toolchain. `buildozer.spec` pakai `p4a` + `gradle` di `/.buildozer`. `export_presets.cfg` pakai Godot export template di `~/.local/share/godot/export_templates/`. Tidak saling tulis.

---

## Checklist 1 halaman (tempel di dinding)

- [ ] `python tools/convert_to_godot.py` → 222/216/54
- [ ] `python main.py` → pygame jalan
- [ ] `godot godot/project.godot` → F6 `KaizenDemo.tscn` → hamon kilat terlihat
- [ ] `git status` → hanya `?? godot/` dan `?? tools/`, tidak ada `D heroes/`
- [ ] Edit balance → re-run converter → test dua engine → commit

Selesai — kamu punya **dua engine hidup berdampingan**, migrasi bertahap hero-per-hero (contoh Kaizen sudah jadi template), tanpa kehilangan satu baris pun `pygame`.
