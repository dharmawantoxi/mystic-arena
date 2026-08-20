# ================================
# mobile/touch.py
# Penerjemah sentuhan -> aksi game
#
# Filosofi: kode game lama SUDAH punya jalur masuk yang bagus
#   game.handle_click(pos, button)   button 1=kiri 3=kanan 4/5=scroll
#   game.handle_key(key)
# Jadi kita TIDAK membongkar 60k baris. Kita cuma menerjemahkan:
#
#   TAP singkat          -> handle_click(pos, 1)     (klik kiri)
#   TAHAN 450 ms         -> handle_click(pos, 3)     (klik kanan)
#   GESER vertikal       -> handle_click(pos, 4/5)   (scroll list)
#   GESER + lepas cepat  -> fling (scroll inersia)
#   DOUBLE TAP           -> aksi khusus (mis. pusatkan kamera)
#
# Multi-touch: jari kedua dipakai untuk tombol skill HUD, jadi
# pemain bisa menahan/menggeser sambil menekan skill.
# ================================

import time

import pygame

from mobile import platform_utils as plat

# ═══ Ambang batas (dalam koordinat logis 1280x720) ═══
TAP_SLOP = 14           # geser < 14 px masih dianggap tap
LONG_PRESS_MS = 450     # tahan selama ini -> klik kanan
DOUBLE_TAP_MS = 280
SCROLL_STEP = 42        # tiap 42 px geser = 1 notch scroll
FLING_FRICTION = 0.90
FLING_MIN_SPEED = 0.6


class TouchPoint:
    __slots__ = ("id", "start_pos", "pos", "prev_pos", "start_time",
                 "moved", "long_fired", "scroll_accum", "velocity",
                 "claimed_by")

    def __init__(self, tid, pos):
        self.id = tid
        self.start_pos = pos
        self.pos = pos
        self.prev_pos = pos
        self.start_time = time.perf_counter()
        self.moved = False
        self.long_fired = False
        self.scroll_accum = 0.0
        self.velocity = 0.0
        self.claimed_by = None   # 'hud' kalau ditangkap tombol HUD


class TouchAction:
    """Aksi hasil terjemahan gesture."""
    __slots__ = ("kind", "pos", "delta", "value", "touch_id")

    def __init__(self, kind, pos=(0, 0), delta=(0, 0), value=0, touch_id=0):
        self.kind = kind          # tap|long_press|double_tap|drag|
                                  # scroll|release|fling
        self.pos = pos
        self.delta = delta
        self.value = value
        self.touch_id = touch_id

    def __repr__(self):
        return "<TouchAction %s %s>" % (self.kind, self.pos)


class TouchManager:
    """
    Kumpulkan event pygame -> daftar TouchAction per frame.

    Pakai di main loop:
        actions = touch.begin_frame()
        for event in pygame.event.get():
            touch.process_event(event)
        for action in touch.collect():
            ...
    """

    def __init__(self, use_finger_events=None):
        # Di Android SDL mengirim FINGER *dan* MOUSE (sintesis).
        # Kita pilih satu supaya tidak dobel.
        if use_finger_events is None:
            use_finger_events = plat.IS_ANDROID
        self.use_finger = use_finger_events
        self.points = {}
        self._actions = []
        self._last_tap_time = 0.0
        self._last_tap_pos = (0, 0)
        self.fling_velocity = 0.0
        self.fling_pos = (0, 0)
        self.active_pos = None        # untuk highlight/hover
        self.enabled = True

    # ── siklus per frame ──────────────────────────────
    def collect(self):
        out = self._actions
        self._actions = []
        return out

    def _emit(self, kind, pos, delta=(0, 0), value=0, tid=0):
        self._actions.append(TouchAction(kind, pos, delta, value, tid))

    # ── event masuk ───────────────────────────────────
    def process_event(self, event):
        if not self.enabled:
            return False

        t = event.type
        if self.use_finger:
            if t == pygame.FINGERDOWN:
                pos = plat.finger_to_logical(event.x, event.y)
                self._down(self._fid(event), pos)
                return True
            if t == pygame.FINGERMOTION:
                pos = plat.finger_to_logical(event.x, event.y)
                self._motion(self._fid(event), pos)
                return True
            if t == pygame.FINGERUP:
                pos = plat.finger_to_logical(event.x, event.y)
                self._up(self._fid(event), pos)
                return True
            # Buang mouse sintesis supaya tidak dobel
            if t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                     pygame.MOUSEMOTION):
                return True
            return False

        # ── mode desktop / uji coba di PC ──
        if t == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._down(0, event.pos)
            return True
        if t == pygame.MOUSEMOTION and event.buttons and event.buttons[0]:
            self._motion(0, event.pos)
            return True
        if t == pygame.MOUSEBUTTONUP and event.button == 1:
            self._up(0, event.pos)
            return True
        if t == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            self._emit("scroll", event.pos, value=-1 if event.button == 4
                       else 1)
            return True
        if t == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self._emit("long_press", event.pos)
            return True
        return False

    @staticmethod
    def _fid(event):
        return getattr(event, "finger_id", getattr(event, "fingerId", 0))

    # ── mesin gesture ─────────────────────────────────
    def _down(self, tid, pos):
        self.points[tid] = TouchPoint(tid, pos)
        self.active_pos = pos
        self.fling_velocity = 0.0
        self._emit("down", pos, tid=tid)

    def _motion(self, tid, pos):
        tp = self.points.get(tid)
        if tp is None:
            return
        dx = pos[0] - tp.pos[0]
        dy = pos[1] - tp.pos[1]
        tp.prev_pos = tp.pos
        tp.pos = pos
        self.active_pos = pos

        total = ((pos[0] - tp.start_pos[0]) ** 2 +
                 (pos[1] - tp.start_pos[1]) ** 2) ** 0.5
        if total > TAP_SLOP:
            tp.moved = True

        if tp.moved:
            tp.velocity = tp.velocity * 0.6 + dy * 0.4
            self._emit("drag", pos, delta=(dx, dy), tid=tid)

            # geser vertikal -> notch scroll untuk list panjang
            tp.scroll_accum += dy
            while abs(tp.scroll_accum) >= SCROLL_STEP:
                direction = -1 if tp.scroll_accum > 0 else 1
                tp.scroll_accum -= SCROLL_STEP * (1 if tp.scroll_accum > 0
                                                  else -1)
                self._emit("scroll", pos, value=direction, tid=tid)

    def _up(self, tid, pos):
        tp = self.points.pop(tid, None)
        if tp is None:
            return
        held_ms = (time.perf_counter() - tp.start_time) * 1000.0

        if not tp.moved and not tp.long_fired:
            now = time.perf_counter()
            is_double = ((now - self._last_tap_time) * 1000.0 < DOUBLE_TAP_MS
                         and abs(pos[0] - self._last_tap_pos[0]) < 40
                         and abs(pos[1] - self._last_tap_pos[1]) < 40)
            if is_double:
                self._emit("double_tap", pos, tid=tid)
                self._last_tap_time = 0.0
            else:
                self._emit("tap", pos, value=held_ms, tid=tid)
                self._last_tap_time = now
                self._last_tap_pos = pos
        elif tp.moved and abs(tp.velocity) > 4:
            self.fling_velocity = tp.velocity
            self.fling_pos = pos
            self._emit("fling", pos, value=tp.velocity, tid=tid)

        self._emit("release", pos, tid=tid)
        if not self.points:
            self.active_pos = None

    # ── dipanggil tiap frame (long-press & inersia) ───
    def update(self):
        now = time.perf_counter()
        for tp in self.points.values():
            if tp.long_fired or tp.moved:
                continue
            if (now - tp.start_time) * 1000.0 >= LONG_PRESS_MS:
                tp.long_fired = True
                self._emit("long_press", tp.pos, tid=tp.id)

        # inersia scroll setelah jari diangkat
        if abs(self.fling_velocity) > FLING_MIN_SPEED:
            self.fling_velocity *= FLING_FRICTION
            steps = int(abs(self.fling_velocity) / (SCROLL_STEP * 0.35))
            for _ in range(min(steps, 3)):
                self._emit("scroll", self.fling_pos,
                           value=-1 if self.fling_velocity > 0 else 1)
        else:
            self.fling_velocity = 0.0

    def cancel(self):
        self.points.clear()
        self.fling_velocity = 0.0
        self._actions.clear()


# ═══════════════════════════════════════════════════════
# JEMBATAN KE API LAMA
# ═══════════════════════════════════════════════════════
def dispatch_to_game(action, game):
    """
    Terjemahkan TouchAction menjadi panggilan API lama milik game.
    Kembalikan True kalau aksi sudah dikonsumsi.
    """
    if game is None:
        return False
    k = action.kind
    if k == "tap":
        game.handle_click(action.pos, 1)
        return True
    if k == "long_press":
        game.handle_click(action.pos, 3)
        return True
    if k == "scroll":
        game.handle_click(action.pos, 4 if action.value < 0 else 5)
        return True
    return False


def dispatch_to_menu(action, menu):
    """Sama seperti di atas tapi untuk layar menu/pause."""
    if menu is None:
        return False
    k = action.kind
    if k == "tap":
        menu.handle_click(action.pos, 1)
        return True
    if k == "scroll":
        menu.handle_click(action.pos, 4 if action.value < 0 else 5)
        return True
    if k == "long_press":
        menu.handle_click(action.pos, 3)
        return True
    return False
