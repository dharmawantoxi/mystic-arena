# Migrasi `tactical_commands.py` ke Godot

Dokumen ini menjelaskan port native sistem perintah taktis dari
`tactical_commands.py` (pygame) ke proyek aktif `godot_rebuild/`. Python tetap
menjadi sumber kebenaran dan oracle; Godot tidak memanggil Python saat runtime.
Hasil gate dan batas verifikasi dirangkum di
[`GODOT_TACTICAL_VERIFICATION.md`](GODOT_TACTICAL_VERIFICATION.md).

## Berkas utama

- `tools/prepare_godot_tactical.py` — exporter fail-closed. State oracle memakai
  ulang harness closed-world pygame di `tools/test_godot_match_parity.py`
  (`make_tactical_commands_fixture`): `TacticalCommandManager` asli + unit
  pygame asli, tanpa `Game.update` penuh. Geometri `draw_world`/`draw_ui`
  direkam dari metode asli dengan spy pygame.
- `godot_rebuild/data/tactical.json` — kontrak runtime: konstanta frame,
  warna, formula formasi/target/auto-protect, anchor sumber, dan hash sumber.
- `godot_rebuild/tests/fixtures/tactical_parity.json` — oracle 37 skenario
  closed-world, 3 kasus `draw_world`, 5 kasus `draw_ui`.
- `godot_rebuild/scripts/core/TacticalCommands.gd` — manager hold/tap,
  cooldown, timer, feedback, auto-protect, dan issuer perintah.
- `godot_rebuild/scripts/core/TacticalTargeting.gd` — helper target:
  hero hidup, threatened tower, nearest enemy, damage dealer, count musuh.
- `godot_rebuild/scripts/core/TacticalDraw.gd` — geometri world overlay,
  parameter UI feedback, warna perintah, dan status text.
- `godot_rebuild/tests/TacticalParityTest.gd` — replay fixture pada
  `BattleUnit` dan perbandingan snapshot manager/hero/unit.
- `tools/test_godot_tactical_prepare.py` dan
  `tools/test_godot_tactical_parity.py` — gate Python exporter/oracle.

## Semantik yang dipertahankan

- Perintah: `gather`, `protect_tower`, `protect_castle`, `attack_boss`,
  `attack_damage_dealer`.
- Frame-based 60 fps: cooldown 30 frame, durasi perintah 600 frame,
  visual gather point 150 frame, feedback 180 frame, auto-check 90 frame.
- HOLD: `hold_start` menerbitkan perintah dengan feedback penuh, lalu
  `update()` menerbitkan ulang senyap tiap cooldown selesai. Penekanan
  berulang untuk hold yang sama tidak mereset waktu. Hold yang syaratnya
  belum terpenuhi tetap “dipersenjatai”; keberhasilan pertama diumumkan loud.
- TAP cepat (<20 frame) membiarkan durasi normal 600 frame. HOLD yang dilepas
  setelah >=20 frame memotong timer ke ekor 30 frame. `hold_end(name)` tidak
  membatalkan hold lain yang lebih baru.
- GATHER: titik default selected hero > rata-rata + mid-mix 0.35 ke red base
  (clamp 200..1080 / 100..620) > single (640,360). Spread 35 + (i%3)*15.
  Push follow-up hanya hidup pada mode HOLD setelah `hold_elapsed >= 240`
  dan >=60% hero tiba dalam radius 100; one-shot jalur `command_timer == 300`
  tetap dipertahankan meskipun secara praktik tertutup oleh visual 150 frame.
- PROTECT TOWER: pilih tower paling terancam (musuh radius 220, bobot 10,
  HP rendah bobot 15, bonus outer x<400 +2), fallback HP terendah/depan.
  Hero <=3 semua berangkat; >3 kirim 2 terdekat, atau 3 bila threat >=3.
- PROTECT CASTLE: formasi radius 80 + (i%2)*30, clamp 50..1230 / 50..670.
- ATTACK BOSS / DAMAGE DEALER: semua hero follow target, spread
  `range*0.5 + i*8`; damage dealer dievaluasi ulang tiap penerbitan.
- Auto-protect: castle HP<40% + >=2 musuh radius 300; tower HP<60% + >=2
  musuh radius 250, atau >=4 musuh; boss HP<80% + wave>=11 dengan peluang
  20% per evaluasi. RNG parity disuntikkan lewat `random_script`; produksi
  memakai RNG Godot, bukan klaim stream Mersenne Twister Python.
- `move_to` native memetakan semantik pygame: destination, destination_auto,
  follow_target clear, retreat clear. Urutan stabil Python pada tie dijaga
  dengan index tie-breaker.
- Feedback, suara, dan efek dipancarkan sebagai signal ke `MatchModel`, lalu
  ke notification/popup/audio CoreGame. `HudView` menggambar overlay world
  (cincin, titik pusat, garis hero) dan UI feedback (fade in/out, shadow,
  border) dari data yang sama dengan oracle.

## Integrasi input

- Keyboard G/T/C/B/D menahan perintah; GATHER keyboard memakai
  `follow_mouse=True` dan posisi mouse diperbarui ke `MatchModel`.
- Tombol panel tactical menahan perintah lewat jalur touch yang sudah ada.
- Controller/keyboard/touch release memanggil `hold_end` dengan nama perintah;
  `release_all_holds()` sekarang memanggil `hold_end()` (ekor source), bukan
  mereset seluruh manager.

## Perintah

```bash
python3 -m pip install pygame==2.6.1 gdtoolkit==4.5.0
python3 tools/prepare_godot_tactical.py
python3 tools/prepare_godot_tactical.py --check
python3 tools/test_godot_tactical_prepare.py
python3 tools/test_godot_tactical_parity.py
python3 godot_rebuild/tests/validate_project.py
```

`--check` membandingkan byte JSON secara eksak dan tidak menulis apa pun.
CI menjalankan gate ini di `godot-check.yml` dan `godot-rebuild.yml`.

## Batas yang jujur

- Overlay native menggambar primitif Godot dari geometri/alpha oracle; bukan
  replika piksel pygame (anti-alias circle/line, border radius, dan raster font
  dapat berbeda). Metrik font UI feedback memakai font Godot asli.
- Audio output, GPU visual, dan perangkat Android tidak diverifikasi.
- Oracle menutup dunia taktis saja: tidak ada combat/reward/wave penuh di
  dalam fixture. Integrasi simulasi penuh tetap diuji oleh suite native lain.
- `command_origin` source selalu `None`; port mempertahankannya sebagai
  `null` dan tidak mengarang asal perintah.
- Peluang auto-boss 20% memakai RNG Godot di produksi; parity numerik
  menyuntikkan roll yang sama dengan oracle.
