"""Uji mode HOLD tactical command (headless).

Skenario request user: "tactical command bisa di-hold; selama masih
dihold perintah itu terus aktif, sampai hold-nya dilepas".

Yang diuji:
  T1  TAP cepat (tekan-lepas < 0,33 detik) -> perilaku LAMA tidak
      berubah: perintah aktif dengan durasi penuh 10 detik.
  T2  HOLD lama -> command_timer terus terisi (durasi tidak pernah
      habis) dan perintah diterbitkan ulang berkala.
  T3  Lepas setelah HOLD lama -> penegakkan berhenti: timer dipangkas
      ke ekor 0,5 detik lalu perintah berakhir.
  T4  HOLD "dipersenjatai": tahan ATTACK BOSS saat belum ada boss ->
      tidak crash, tetap ter-hold; begitu boss muncul, aktivasi
      pertama berhasil dan semua hero mengunci boss.
  T5  hold_end dengan nama command LAIN tidak melepas hold yang
      sedang aktif (tuts lama tidak membatalkan hold tuts baru).
  T6  GATHER saat di-hold: setelah delay, push bersama terpicu
      (follow_target musuh terpasang) dan timer tetap hidup.
  T7  Jalur keyboard: InputHandler.handle_key mulai hold,
      handle_key_up melepasnya.
  T8  Jalur sentuh: hud.apply_hud_action mulai hold.
  T9  Penekanan berulang untuk hold yang sama TIDAK mereset
      hitungan waktu tahan (anti key-repeat / anti spam).
  T10 PROTECT TOWER dengan tower yang sudah hancur -> pilih ulang
      otomatis (fallback), bukan melindungi tower mati.

Jalankan:  python3 tools/test_tactical_hold.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()

import _core  # noqa: E402,F401 (alias legacy, pecah circular import)
from game import Game  # noqa: E402
from _entity import Hero  # noqa: E402
from bosses.base_boss import Boss  # noqa: E402
from tactical_commands import (  # noqa: E402
    TacticalCommand, HOLD_TAP_MAX_FRAMES, HOLD_RELEASE_TAIL,
)

screen = pygame.display.set_mode((1280, 720))
g = Game(screen, level_number=1)
g.level_intro = None
g.boss_intro = None

try:
    from heroes import combat_feel as _feel
except Exception:                              # pragma: no cover
    _feel = None


def step(n=1):
    """Jalankan ``n`` frame gameplay yang BENAR-BENAR maju.

    ``Game.update()`` sengaja langsung return selama hit-stop (blok
    HIT STOP di _core.py) supaya benturan terasa berbobot. Untuk test
    yang menghitung frame, itu berarti "620 kali update()" belum tentu
    "620 frame gameplay": pertempuran yang kebetulan terjadi bisa
    menelan sampai 20 frame, dan T1 cuma punya margin 20 frame (620
    vs durasi 600). Kosongkan bus tiap iterasi supaya jumlah frame
    yang dihitung test benar-benar deterministik.
    """
    for _ in range(n):
        if _feel is not None:
            _feel.reset()
        g.update()


# Pemanasan singkat supaya sistem siap.
step(30)

tac = g.tactical
assert tac is not None, "TacticalCommandManager tidak terpasang"

# Dua hero biru untuk semua perintah.
h1 = Hero("kaizen", "blue", 400, 360)
h2 = Hero("sylara", "blue", 420, 380)
g.heroes += [h1, h2]

# ── T1: TAP cepat = perilaku lama (durasi penuh) ──────────
tac.cooldown = 0
ok = tac.hold_start(TacticalCommand.PROTECT_CASTLE)
assert ok, "hold_start protect_castle gagal diterbitkan"
assert tac.held_command == TacticalCommand.PROTECT_CASTLE
assert tac.active_command == TacticalCommand.PROTECT_CASTLE
tac.hold_end(TacticalCommand.PROTECT_CASTLE)   # dilepas SEGERA (tap)
assert tac.held_command is None
assert tac.command_timer > 500, \
    f"tap cepat harus tetap durasi penuh, timer={tac.command_timer}"
# Perintah kedaluwarsa normal (bukan dipangkas ke ekor).
for _ in range(620):
    step()
assert tac.active_command is None, \
    f"perintah tap harus berakhir alami, masih {tac.active_command}"
print("T1 OK  - TAP cepat = tekanan biasa (durasi penuh 10 detik)")

# ── T2: HOLD lama: timer terus terisi, perintah tidak habis ─
tac.cooldown = 0
ok = tac.hold_start(TacticalCommand.PROTECT_CASTLE)
assert ok
min_timer = 9999
for i in range(300):           # 5 detik menahan
    step()
    assert tac.active_command == TacticalCommand.PROTECT_CASTLE, \
        f"frame {i}: perintah hilang padahal masih di-hold"
    assert tac.held_command == TacticalCommand.PROTECT_CASTLE
    if i > 60:                 # setelah fase awal, timer di-top-up
        min_timer = min(min_timer, tac.command_timer)
assert min_timer > 500, \
    f"timer tidak di-top-up selama hold: min={min_timer}"
assert tac._hold_has_fired, "hold yang sukses harus bertanda fired"
print(f"T2 OK  - selama 300 frame di-hold, timer tidak turun di "
      f"bawah {min_timer} (perintah terus aktif)")

# ── T3: lepas setelah HOLD lama -> penegakkan berhenti ────
tac.hold_end(TacticalCommand.PROTECT_CASTLE)
assert tac.held_command is None
assert tac.command_timer <= HOLD_RELEASE_TAIL, \
    f"timer harus dipangkas ke ekor, masih {tac.command_timer}"
for _ in range(HOLD_RELEASE_TAIL + 10):
    step()
assert tac.active_command is None, \
    f"perintah harus berakhir setelah hold dilepas, masih {tac.active_command}"
print("T3 OK  - perintah berhenti ditegakkan begitu hold dilepas")

# ── T4: HOLD dipersenjatai (belum ada boss) ───────────────
g.active_boss = None
tac.cooldown = 0
ok = tac.hold_start(TacticalCommand.ATTACK_BOSS)
assert not ok, "attack_boss tanpa boss harusnya gagal diterbitkan"
assert tac.held_command == TacticalCommand.ATTACK_BOSS, \
    "hold harus tetap dipersenjatai walau syarat belum terpenuhi"
# Beberapa frame tanpa boss: tidak ada yang crash/macet.
for _ in range(40):
    step()
assert tac.held_command == TacticalCommand.ATTACK_BOSS
assert not tac._hold_has_fired
# Boss MUNCUL saat tombol masih ditahan -> aktivasi otomatis.
lane = g.map_renderer.get_lane_path("mid")
boss = Boss("gornak", lane)
boss.entrance_timer = 0
g.active_boss = boss
fired = False
for _ in range(90):
    step()
    if tac.active_command == TacticalCommand.ATTACK_BOSS \
            and tac._hold_has_fired:
        fired = True
        break
assert fired, "hold attack_boss tidak aktif saat boss muncul"
hidup = [h for h in g.heroes if h.alive]
assert hidup, "tidak ada hero biru hidup"
assert all(h.follow_target is boss for h in hidup), \
    [getattr(h.follow_target, 'name', None) for h in hidup]
print(f"T4 OK  - hold dipersenjatai: {len(hidup)} hero langsung "
      f"mengunci {boss.name} saat boss muncul")
tac.hold_end()   # lepas apa pun yang di-hold
assert tac.held_command is None

# ── T5: hold_end nama lain tidak melepas ──────────────────
tac.cooldown = 0
assert tac.hold_start(TacticalCommand.PROTECT_CASTLE)
for _ in range(5):
    step()
tac.hold_end(TacticalCommand.ATTACK_BOSS)   # nama berbeda -> abaikan
assert tac.held_command == TacticalCommand.PROTECT_CASTLE, \
    "hold_end command lain tidak boleh melepas hold aktif"
tac.hold_end(TacticalCommand.PROTECT_CASTLE)
assert tac.held_command is None
print("T5 OK  - hold_end hanya melepas command yang sedang di-hold")

# ── T6: GATHER push selama hold ───────────────────────────
# Hero ditempatkan tepat di titik kumpul supaya cepat tiba.
h1.x, h1.y = 420, 360
h2.x, h2.y = 440, 360
h1.hp = h1.max_hp
h2.hp = h2.max_hp
musuh = Hero("thorne", "red", 700, 360)
g.ai.heroes.append(musuh)
tac.cooldown = 0
ok = tac.hold_start(TacticalCommand.GATHER, 430, 360)
assert ok, "gather gagal"
assert tac._gather_push_fired is False
push_frame = None
for i in range(420):           # maks 7 detik menahan
    step()
    if tac._gather_push_fired:
        push_frame = i
        break
assert push_frame is not None, "push GATHER tidak pernah terpicu saat hold"
assert tac.held_command == TacticalCommand.GATHER
assert tac.command_timer > 400, \
    f"timer harus tetap hidup selama hold, {tac.command_timer}"
hidup = [h for h in g.heroes if h.alive]
assert any(h.follow_target is not None for h in hidup), \
    "setelah push, hero harus mengunci musuh"
print(f"T6 OK  - push GATHER terpicu di frame ke-{push_frame} dan "
      f"perintah tetap hidup selama ditahan")
tac.hold_end(TacticalCommand.GATHER)

# ── T7: jalur keyboard (InputHandler) ─────────────────────
tac.cooldown = 0
g.input.handle_key(pygame.K_c)
assert tac.held_command == TacticalCommand.PROTECT_CASTLE, \
    f"KEYDOWN C harus mulai hold, yang tercatat {tac.held_command}"
g.input.handle_key_up(pygame.K_c)
assert tac.held_command is None, "KEYUP C harus melepas hold"
print("T7 OK  - keyboard: KEYDOWN mulai hold, KEYUP melepas")

# ── T8: jalur sentuh (apply_hud_action) ───────────────────
from mobile import hud as hud_mod  # noqa: E402
assert "gather" in hud_mod.TACTICAL_ACTIONS
tac.cooldown = 0
ctx = {"game": g, "menu": None, "debug": None, "request_pause": False}
assert hud_mod.apply_hud_action("gather", ctx) is True
assert tac.held_command == TacticalCommand.GATHER, \
    "tekan tombol panel harus mulai hold gather"
# Simulasi pelepasan jari seperti yang dilakukan main.py.
g.tactical.hold_end("gather")
assert tac.held_command is None
print("T8 OK  - sentuh panel: apply_hud_action mulai hold")

# ── T9: penekanan berulang tidak mereset waktu tahan ──────
tac.cooldown = 0
assert tac.hold_start(TacticalCommand.PROTECT_CASTLE)
for _ in range(12):
    step()
elapsed0 = tac.hold_elapsed
lagi = tac.hold_start(TacticalCommand.PROTECT_CASTLE)  # tekan ulang
assert lagi and tac.hold_elapsed == elapsed0, \
    f"repeat hold mereset elapsed: {elapsed0} -> {tac.hold_elapsed}"
tac.hold_end()
print("T9 OK  - penekanan berulang (key repeat) tidak mereset hold")

# ── T10: tower hancur -> fallback otomatis ────────────────
# Level mulai tanpa tower (pemain membangun sendiri), jadi pasang
# dua tower biru tiruan untuk menguji fallback-nya.
from _entity import Tower  # noqa: E402
ta = Tower(300, 400, "blue")
tb = Tower(320, 420, "blue")
tb.name = "Tower B"
g.towers += [ta, tb]
ta.alive = False                  # simulasikan tower target hancur
tac.cooldown = 0
ok = tac.command_protect_tower(ta)
assert ok, "protect_tower fallback gagal"
assert tac.command_target is not ta, \
    "masih melindungi tower yang sudah hancur"
assert tac.command_target.alive, "fallback memilih tower mati"
print("T10 OK - tower target hancur -> pilih ulang otomatis")

print("\nSEMUA TES MODE HOLD LULUS ✓")
