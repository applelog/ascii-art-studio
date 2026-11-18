"""창 재생. pygame-ce 가 있으면 pygame 창 (빠름), 없으면 OpenCV 창.

macOS 에서 잰 화면 표시 시간 (1200×960 그림): OpenCV 약 20ms, pygame 약 4~6ms.

그림은 프레임 번호로만 정해지고(PieceRenderer), 실제 시간은 "지금 몇 번 프레임인지" 고를 때만 쓴다.
그래서 렌더가 느리면 프레임을 건너뛰어도 속도는 실제 시간에 맞고, 같은 번호의 그림은 늘 같다.

키
    Space   정지 / 재생
    R       처음부터
    S       지금 프레임을 PNG 로 저장 (원래 해상도)
    ← →     한 프레임 이동 (정지됨).  , . 도 같음
    Esc Q   끝내기
"""
import os
import threading
import time

import numpy as np

from .atlas import DEFAULT_FONT, GlyphAtlas, save_png
from .effects import TrailGlow, warmup_frames
from .grid import Grid
from .timeline import frame_at, frame_count, frame_phase, frame_time

# 키 코드 → 동작. 화살표 코드는 운영체제마다 다르다 (mac / windows / linux).
KEYMAP = {
    32: "toggle",
    ord("r"): "restart", ord("R"): "restart",
    ord("s"): "save", ord("S"): "save",
    27: "quit", ord("q"): "quit", ord("Q"): "quit",
    ord(","): "prev", ord("."): "next",
    63234: "prev", 63235: "next",        # macOS
    2424832: "prev", 2555904: "next",    # Windows
    65361: "prev", 65363: "next",        # Linux
}
MAX_VIEW = 900          # 창 기본 크기 상한 (px). 출력·저장 해상도와는 무관
CACHE_LIMIT_MB = 256    # 글자 버퍼(grid) 캐시 상한. 넘으면 더 저장하지 않고 그때그때 계산
PREFETCH_AHEAD = 45     # 재생 중 뒤에서 미리 계산해 둘 프레임 수 (30fps 기준 1.5초)
TITLE_EVERY = 0.25      # 창 제목(상태 표시) 갱신 간격 (초)
IDLE_WAIT_MS = 30       # 정지 중 키 입력 확인 간격 (ms)
POLL_SECONDS = 0.002    # pygame 창에서 키 입력을 확인하는 간격 (초)


def draw_stage(ns, state, g, stage, i, n, fps):
    """단계 하나를 grid 에 그린다 (렌더러와 미리 계산 프로세스가 같이 쓴다)."""
    g.clear()
    if stage == "frame":
        ns["frame"](state, frame_time(i, fps), frame_phase(i, n), g)
    elif stage == "scene":
        ns["scene"](state, g)
    elif stage == "intro":
        ns["intro"](state, i / float(n), g)
    else:
        ns["motion"](state, frame_time(i, fps), frame_phase(i, n), g)


class PieceRenderer:
    """작품 → 프레임별 grid·이미지. 미리보기·창·저장이 모두 이것을 쓴다.

    작품 종류 (kind)
        "staged" : scene(①) + intro(②, 선택) + motion(③, 선택)   ← /ascii 작품의 기본 형식
        "frame"  : frame(state, t, phase, grid) 하나               ← 예제·예전 형식
        "still"  : scene 하나 (정지 그림)

    part (staged 작품에서 무엇을 볼지)
        "all"    : 등장 한 번 → 모션 반복 (창 재생, 최종 영상)
        "scene"  : ① 완성 화면 한 장
        "intro"  : ② 등장 + 끝에 완성 화면 INTRO_HOLD 초 (등장 검토용)
        "motion" : ③ 모션만 반복 (모션 검토용)

    시간축
        cyclic=True  : 위치 k 를 n 으로 나눈 나머지로 본다. 끝 다음이 처음 (잔상도 끝에서 처음으로 이어짐)
        cyclic=False : 0 부터 곧게 가는 시간. 0 번 앞은 빈 화면. loop 이면 loop_start 부터 반복
    """

    def __init__(self, ns, part="all"):
        self.ns = ns
        self.fps = ns.get("FPS", 30)
        has = {k: callable(ns.get(k)) for k in ("frame", "scene", "intro", "motion")}
        if has["intro"] or has["motion"]:
            if not has["scene"]:
                raise SystemExit("intro/motion 이 있는 작품에는 scene(state, grid) 도 있어야 합니다")
            self.kind = "staged"
        elif has["frame"]:
            self.kind = "frame"
        elif has["scene"]:
            self.kind = "still"
        else:
            raise SystemExit("작품에 scene() 이나 frame() 이 없습니다")
        self.part = part if self.kind == "staged" else "all"
        self.n_intro = frame_count(ns.get("INTRO_SECONDS", 1), self.fps) if has["intro"] else 0
        self.n_motion = frame_count(ns.get("LOOP_SECONDS", 1), self.fps) if has["motion"] else 0
        self.n_hold = int(round(ns.get("INTRO_HOLD", 1.0) * self.fps)) if has["intro"] else 0
        self.loop_start = 0
        if self.kind == "frame":
            self.n = frame_count(ns.get("LOOP_SECONDS", 1), self.fps)
            self.loop = bool(ns.get("LOOP", True))
            self.cyclic = self.loop
        elif self.kind == "still" or self.part == "scene":
            self.n, self.loop, self.cyclic = 1, True, True
        elif self.part == "intro":
            if not has["intro"]:
                raise SystemExit("이 작품에는 intro() 가 없습니다")
            self.n, self.loop, self.cyclic = self.n_intro + self.n_hold, False, False
        elif self.part == "motion":
            if not has["motion"]:
                raise SystemExit("이 작품에는 motion() 이 없습니다")
            self.n, self.loop, self.cyclic = self.n_motion, True, True
        else:  # all
            if not has["motion"]:                       # 등장만 있음: 등장 후 완성 화면에 머묾
                self.n, self.loop, self.cyclic = self.n_intro + 1, False, False
            elif not has["intro"]:                      # 모션만 있음
                self.n, self.loop, self.cyclic = self.n_motion, True, True
            else:
                self.n, self.loop, self.cyclic = self.n_intro + self.n_motion, True, False
                self.loop_start = self.n_intro
        self.grid = Grid(ns["COLS"], ns["ROWS"])
        self.atlas = GlyphAtlas(ns.get("FONT", DEFAULT_FONT), ns["FONT_PX"], ns["CELL_ASPECT"])
        self.state = ns["setup"]()
        self.last_ms = 0.0
        trail, glow = ns.get("TRAIL", 0) or 0, ns.get("GLOW", 0) or 0
        self.fx = None
        if trail > 0 or glow > 0:
            self.fx = TrailGlow(ns["BACKGROUND"], trail, glow, ns.get("GLOW_RADIUS", 0.8) * self.atlas.h)
        self.warmup = warmup_frames(trail)
        self._fx_last = None      # 잔상 상태가 몇 번 위치까지 반영됐는지
        self._fx_exact = False    # 그 상태가 "앞에서부터 빠짐없이" 계산된 것인지
        # 글자 버퍼 캐시: 같은 (단계, 번호) 면 언제나 같은 grid 이므로 저장해 두고 다시 쓴다
        self._cache = {}
        self._cache_bytes = 0
        self._cache_lock = threading.Lock()
        self.cache_hits = 0
        self.pool = None          # 무거운 작품이면 GridPool (여러 프로세스로 미리 계산)

    def start_pool(self, log=None):
        """첫 프레임 계산이 무거우면 프로세스 풀을 켠다. 켰으면 True."""
        from .pool import HEAVY_MS, GridPool

        t0 = time.perf_counter()
        self._draw_into(Grid(self.ns["COLS"], self.ns["ROWS"]), 0)
        ms = (time.perf_counter() - t0) * 1000
        if ms < HEAVY_MS or self.pool is not None:
            return False
        try:
            self.pool = GridPool(self)
        except Exception as e:  # noqa: BLE001
            if log:
                log("미리 계산 프로세스를 쓰지 못해 한 프로세스로 계산합니다: %s" % e)
            return False
        if log:
            log("무거운 작품 (프레임당 약 %.0fms): 프로세스 %d개로 미리 계산합니다" % (ms, self.pool.workers))
        return True

    def stop_pool(self):
        if self.pool is not None:
            self.pool.close()
            self.pool = None

    # ---------- 시간축 ----------
    def locate(self, k):
        """위치 k → (단계, 그 단계 안의 프레임 번호, 그 단계의 프레임 수)."""
        if self.cyclic:
            k = k % self.n
        elif self.loop and k >= self.n:
            k = self.loop_start + (k - self.loop_start) % (self.n - self.loop_start)
        else:
            k = min(max(0, k), self.n - 1)
        if self.kind == "frame":
            return "frame", k, self.n
        if self.kind == "still" or self.part == "scene":
            return "scene", 0, 1
        if self.part == "motion" or (self.part == "all" and self.n_intro == 0):
            return "motion", k, self.n_motion
        if k < self.n_intro:
            return "intro", k, self.n_intro
        if self.part == "intro" or self.n_motion == 0:
            return "scene", 0, 1
        return "motion", k - self.n_intro, self.n_motion

    def describe(self, k):
        stage, i, n = self.locate(k)
        name = {"intro": "② 등장", "motion": "③ 모션", "scene": "① 완성", "frame": ""}[stage]
        return ("%s %d/%d" % (name, i + 1, n)).strip()

    def video_frames(self, loops=1):
        """영상에 넣을 위치들. 원형이면 한 바퀴를 loops 번, 직선 반복이면 등장 + 모션 loops 번."""
        loops = max(1, int(loops))
        if self.cyclic:
            return list(range(self.n * loops))
        if self.loop:
            return list(range(self.loop_start + loops * (self.n - self.loop_start)))
        return list(range(self.n))

    # ---------- 그리기 ----------
    def _draw_into(self, g, k):
        stage, i, n = self.locate(k)
        draw_stage(self.ns, self.state, g, stage, i, n, self.fps)
        return (stage, i)

    def store_arrays(self, key, ch, rgb):
        size = ch.nbytes + rgb.nbytes
        with self._cache_lock:
            if key not in self._cache and self._cache_bytes + size <= CACHE_LIMIT_MB * 1024 * 1024:
                self._cache[key] = (ch, rgb)
                self._cache_bytes += size

    def _store(self, key, g):
        self.store_arrays(key, g.ch.copy(), g.rgb.copy())

    def cached(self, k):
        stage, i, _ = self.locate(k)
        return self.cached_key((stage, i))

    def cached_key(self, key):
        with self._cache_lock:
            return key in self._cache

    def grid_at(self, k):
        """위치 k 의 글자 버퍼. 캐시에 있으면 꺼내 쓰고, 없으면 계산해서 캐시에 넣는다."""
        g = self.grid
        stage, i, _ = self.locate(k)
        with self._cache_lock:
            hit = self._cache.get((stage, i))
        if hit is None and self.pool is not None and self.pool.wait_for((stage, i)):
            with self._cache_lock:
                hit = self._cache.get((stage, i))
        if hit is not None:
            g.ch[...], g.rgb[...] = hit
            g.z.fill(np.inf)
            self.cache_hits += 1
            return g
        self._store(self._draw_into(g, k), g)
        return g

    def prefetch(self, k, scratch):
        """위치 k 의 글자 버퍼를 미리 계산해 캐시에 넣는다 (다른 스레드에서 부름, scratch 는 그 스레드 전용 grid)."""
        if not self.cached(k):
            self._store(self._draw_into(scratch, k), scratch)

    def grid_at_phase(self, phase):
        """phase 를 직접 넣어 계산 (루프 끝 phase=1 확인용). frame 작품은 frame, staged 는 motion."""
        g = self.grid
        g.clear()
        fn = "frame" if self.kind == "frame" else "motion"
        n = self.n if self.kind == "frame" else self.n_motion
        self.ns[fn](self.state, phase * n / float(self.fps), phase, g)
        return g

    def base_image(self, k, bgr=False):
        """효과(잔상·글로우) 없이 글자만 그린 위치 k."""
        return self.atlas.render(self.grid_at(k), self.ns["BACKGROUND"], bgr=bgr)

    def image_at(self, k, bgr=False, exact=True):
        """위치 k 의 최종 이미지 (RGB). bgr=True 는 창 표시용 (색 순서만 다르고 그림은 같다).

        잔상이 있을 때:
          exact=True  (저장·정지 화면·내보내기) 바로 다음 위치면 이어서, 아니면 warmup 만큼 앞에서부터
                      다시 계산한다 → 같은 위치면 언제나 픽셀까지 같은 그림.
          exact=False (창에서 재생 중) 몇 프레임 건너뛰었으면 그 사이를 빈 화면으로 보고 잔상만 그만큼 흐리게 한
                      뒤 이어 그린다 → 빠름. 눈으로는 차이가 거의 없다.
        """
        t0 = time.perf_counter()
        if self.fx is None:
            img = self.base_image(k, bgr=bgr)
        else:
            if self.cyclic:
                k = k % self.n
                gap = None if self._fx_last is None else (k - self._fx_last) % self.n
            else:
                k = max(0, k) if self.loop else min(max(0, k), self.n - 1)
                gap = None if self._fx_last is None else k - self._fx_last
            if gap == 1 and (self._fx_exact or not exact):
                img = self.fx.apply(self.base_image(k))
            elif not exact and gap is not None and 1 < gap <= self.warmup and self.fx.state is not None:
                self.fx.state *= np.float32(self.fx.trail ** (gap - 1))   # 건너뛴 프레임만큼 흐리게
                img = self.fx.apply(self.base_image(k))
                self._fx_exact = False
            else:
                self.fx.reset()
                start = k - self.warmup if self.cyclic else max(0, k - self.warmup)
                for j in range(start, k + 1):
                    img = self.fx.apply(self.base_image(j))
                self._fx_exact = True
            self._fx_last = k
            if bgr:
                img = np.ascontiguousarray(img[..., ::-1])
        self.last_ms = (time.perf_counter() - t0) * 1000
        return img


class Playback:
    """재생 상태. clock 을 바꿔 끼울 수 있어서 창 없이 테스트할 수 있다.

    cyclic   : 위치가 0..n-1 을 돈다
    직선 반복 : 위치가 계속 늘어난다 (렌더러가 등장 뒤 모션 반복으로 바꿔 읽음)
    한 번     : 끝에서 멈춘다
    """

    def __init__(self, n, fps, loop=True, clock=time.perf_counter, cyclic=None):
        self.n, self.fps, self.loop, self.clock = n, fps, loop, clock
        self.cyclic = loop if cyclic is None else cyclic
        self.frame = 0
        self.playing = n > 1
        self.anchor = clock()      # 0 번 위치가 보였어야 할 시각

    def update(self):
        if self.playing:
            elapsed = self.clock() - self.anchor
            if self.loop and not self.cyclic:
                self.frame = int(elapsed * self.fps + 1e-9)
            else:
                self.frame, ended = frame_at(elapsed, self.fps, self.n, self.loop)
                if ended:
                    self.playing = False
        return self.frame

    def toggle(self):
        if self.playing:
            self.update()
            self.playing = False
        else:
            if not self.loop and self.frame >= self.n - 1:
                self.frame = 0
            self.anchor = self.clock() - self.frame / float(self.fps)
            self.playing = self.n > 1

    def restart(self):
        self.frame = 0
        self.anchor = self.clock()
        self.playing = self.n > 1

    def step(self, d):
        self.update()
        self.playing = False
        f = self.frame + d
        if self.cyclic:
            self.frame = f % self.n
        elif self.loop:
            self.frame = max(0, f)
        else:
            self.frame = min(self.n - 1, max(0, f))

    def seconds_to_next(self):
        """다음 프레임이 나올 때까지 남은 시간 (재생 중일 때)."""
        elapsed = self.clock() - self.anchor
        return max(0.0, (int(elapsed * self.fps) + 1) / float(self.fps) - elapsed)


class CvDisplay:
    def __init__(self, name, width, height):
        import cv2

        self.cv2 = cv2
        self.name = name
        cv2.namedWindow(name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        scale = min(1.0, MAX_VIEW / float(max(width, height)))
        self.view = (int(width * scale), int(height * scale))
        cv2.resizeWindow(name, *self.view)
        self.front()

    def front(self):
        """창을 맨 앞으로 (터미널·다른 앱 뒤에 숨지 않게). 지원 안 되면 넘어간다."""
        try:
            self.cv2.setWindowProperty(self.name, self.cv2.WND_PROP_TOPMOST, 1)
        except Exception:  # noqa: BLE001
            pass

    def show(self, img_bgr):
        """창 크기보다 큰 그림은 먼저 줄여서 넘긴다 (맥에서 큰 그림 표시가 느림). 저장 해상도와는 무관."""
        h, w = img_bgr.shape[:2]
        if w > self.view[0] * 1.05:
            img_bgr = self.cv2.resize(img_bgr, self.view, interpolation=self.cv2.INTER_AREA)
        self.cv2.imshow(self.name, img_bgr)

    bgr = True          # OpenCV 는 파랑·초록·빨강 순서를 받는다
    backend = "opencv"

    def wait_action(self, ms):
        """ms 동안 키를 기다리고 동작 이름(없으면 None)을 돌려준다."""
        return KEYMAP.get(self.cv2.waitKeyEx(max(1, int(ms))))

    def title(self, text):
        self.cv2.setWindowTitle(self.name, text)

    def closed(self):
        return self.cv2.getWindowProperty(self.name, self.cv2.WND_PROP_VISIBLE) < 1

    def close(self):
        self.cv2.destroyWindow(self.name)
        self.cv2.waitKey(1)


class PygameDisplay:
    """pygame-ce 창. 그림을 그대로 화면에 붙이고(blit), 화면보다 크면 부드럽게 줄인다."""

    bgr = False
    backend = "pygame"
    SCREEN_FILL = 0.9   # 창이 화면에서 차지할 수 있는 최대 비율
    MIN_VIEW = 160      # 창 긴 변의 최소 크기 (px)

    def __init__(self, name, width, height):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame

        self.pg = pygame
        pygame.display.init()
        info = pygame.display.Info()
        max_w = info.current_w * self.SCREEN_FILL if info.current_w > 0 else width
        max_h = info.current_h * self.SCREEN_FILL if info.current_h > 0 else height
        scale = min(1.0, max_w / float(width), max_h / float(height))
        scale = max(scale, min(1.0, self.MIN_VIEW / float(max(width, height))))
        self.size = (width, height)
        self.view = (int(width * scale), int(height * scale))
        self.screen = pygame.display.set_mode(self.view)
        pygame.display.set_caption(name)
        self._closed = False
        self.actions = {
            pygame.K_SPACE: "toggle", pygame.K_r: "restart", pygame.K_s: "save",
            pygame.K_ESCAPE: "quit", pygame.K_q: "quit",
            pygame.K_LEFT: "prev", pygame.K_COMMA: "prev", pygame.K_RIGHT: "next", pygame.K_PERIOD: "next",
        }
        # 한글 입력 상태에서도 같은 자리의 키가 먹도록 물리 키 위치(scancode)로도 찾는다
        self.scan_actions = {
            pygame.KSCAN_SPACE: "toggle", pygame.KSCAN_R: "restart", pygame.KSCAN_S: "save",
            pygame.KSCAN_ESCAPE: "quit", pygame.KSCAN_Q: "quit",
            pygame.KSCAN_LEFT: "prev", pygame.KSCAN_COMMA: "prev",
            pygame.KSCAN_RIGHT: "next", pygame.KSCAN_PERIOD: "next",
        }

    def show(self, img_rgb):
        img = np.ascontiguousarray(img_rgb)
        surf = self.pg.image.frombuffer(img, self.size, "RGB")
        if self.view != self.size:
            self.pg.transform.smoothscale(surf, self.view, self.screen)
        else:
            self.screen.blit(surf, (0, 0))
        self.pg.display.flip()

    def action_of(self, event):
        if event.type == self.pg.QUIT:
            self._closed = True
            return "quit"
        if event.type == self.pg.KEYDOWN:
            return self.actions.get(event.key) or self.scan_actions.get(getattr(event, "scancode", -1))
        return None

    def wait_action(self, ms):
        """ms 동안 이벤트를 보며 기다리고, 키가 눌리면 바로 동작 이름을 돌려준다."""
        deadline = time.perf_counter() + max(1.0, ms) / 1000.0
        while True:
            for event in self.pg.event.get():
                action = self.action_of(event)
                if action:
                    return action
            left = deadline - time.perf_counter()
            if left <= 0:
                return None
            time.sleep(min(left, POLL_SECONDS))

    def title(self, text):
        self.pg.display.set_caption(text)

    def closed(self):
        return self._closed

    def close(self):
        self.pg.display.quit()


def make_display(name, width, height, backend="auto"):
    """backend: "auto"(pygame 있으면 pygame) | "pygame" | "opencv"."""
    if backend in ("auto", "pygame"):
        try:
            return PygameDisplay(name, width, height)
        except ImportError:
            if backend == "pygame":
                raise SystemExit("pygame-ce 가 없습니다: python -m pip install pygame-ce")
    return CvDisplay(name, width, height)


def play(renderer, title, out_dir, display=None, clock=time.perf_counter, max_seconds=None, log=print,
         backend="auto", use_processes=True):
    """창에서 재생한다. Esc·Q·창 닫기·Ctrl+C 로 끝나고, 끝나면 통계를 돌려준다."""
    pb = Playback(renderer.n, renderer.fps, renderer.loop, clock, cyclic=renderer.cyclic)
    # 무거운 작품이면 작업자를 창보다 먼저 띄우고 첫 프레임들을 바로 맡긴다 (시작할 때 멈춤 줄이기)
    use_pool = renderer.start_pool(log) if use_processes else False
    if use_pool:
        renderer.pool.request(range(1, PREFETCH_AHEAD + 1))
    first = renderer.image_at(0)
    h, w = first.shape[:2]
    display = display or make_display(title, w, h, backend)
    bgr = getattr(display, "bgr", False)
    if bgr:
        first = np.ascontiguousarray(first[..., ::-1])
    log("재생: %s  %dx%d px, %d 프레임 @ %d fps  (창: %s)"
        % (title, w, h, renderer.n, renderer.fps, getattr(display, "backend", "?")))
    log("키는 그림 창을 한 번 클릭한 뒤 누르세요 (터미널이 아니라 그림 창).  "
        "Space 정지 · R 처음 · S 저장 · ←→ 이동 · Esc 끝 · 터미널에서 Ctrl+C 도 끝")
    start = clock()
    st = {"shown": 0, "skipped": 0, "total_ms": 0.0, "last_frame": None, "last_title": -1e9, "saved": []}

    # 뒤에서 앞으로 나올 프레임의 글자 버퍼를 미리 계산 (numpy 계산은 GIL 을 놓아 화면 쪽과 겹쳐 돈다)
    stop = threading.Event()

    def prefetcher():
        scratch = Grid(renderer.ns["COLS"], renderer.ns["ROWS"])
        while not stop.is_set():
            base = pb.frame
            todo = [base + d for d in range(1, PREFETCH_AHEAD + 1)]
            if renderer.cyclic:
                todo = [k % renderer.n for k in todo]
            elif not renderer.loop:
                todo = [k for k in todo if k < renderer.n]
            if use_pool:
                renderer.pool.request(todo)              # 여러 프로세스가 계산해 캐시에 넣는다
                stop.wait(0.005)
                continue
            busy = False
            for k in todo:
                if stop.is_set() or abs(pb.frame - base) > PREFETCH_AHEAD // 2:
                    break
                if not renderer.cached(k):
                    renderer.prefetch(k, scratch)
                    busy = True
            if not busy:
                stop.wait(0.01)

    worker = threading.Thread(target=prefetcher, name="asciiart-prefetch", daemon=True)
    worker.start()

    def step():
        """한 번 돌기. 끝내야 하면 False."""
        f = pb.update()
        if f != st["last_frame"]:
            if st["last_frame"] is not None and pb.playing:
                jump = (f - st["last_frame"]) % renderer.n if renderer.cyclic else f - st["last_frame"]
                if 1 < jump < max(2, renderer.n // 2):   # 재생 중 앞으로 몇 칸 건너뛴 것만 센다
                    st["skipped"] += jump - 1
            # 재생 중에는 빠른 길(exact=False), 멈췄을 때는 정확한 그림
            img = first if (f == 0 and st["last_frame"] is None) else renderer.image_at(f, bgr=bgr, exact=not pb.playing)
            display.show(img)
            st["shown"] += 1
            st["total_ms"] += renderer.last_ms
            st["last_frame"] = f
        now = clock()
        if now - st["last_title"] >= TITLE_EVERY:
            display.title("%s   %s  %.2fs  %s  렌더 %.1fms"
                          % (title, renderer.describe(f), frame_time(f, renderer.fps),
                             "재생" if pb.playing else "정지", renderer.last_ms))
            st["last_title"] = now
        # 최소 1ms 는 기다린다 (프레임 경계에서 남은 시간이 소수점 오차로 0 이 되어 헛도는 것 방지)
        wait = max(1.0, pb.seconds_to_next() * 1000) if pb.playing else IDLE_WAIT_MS
        action = display.wait_action(wait)
        if action == "quit" or display.closed():
            return False
        if action == "toggle":
            pb.toggle()
        elif action == "restart":
            pb.restart()
        elif action in ("prev", "next"):
            pb.step(-1 if action == "prev" else 1)
        elif action == "save":
            path = os.path.join(out_dir, "frame_%04d.png" % pb.frame)
            save_png(renderer.image_at(pb.frame), path)
            st["saved"].append(path)
            log("저장: %s" % path)
        return not (max_seconds is not None and clock() - start >= max_seconds)

    try:
        while step():
            pass
    except KeyboardInterrupt:
        log("Ctrl+C: 재생을 끝냅니다")
    finally:
        stop.set()
        worker.join(timeout=2)
        renderer.stop_pool()
        display.close()
    stats = {"shown": st["shown"], "skipped": st["skipped"], "avg_ms": st["total_ms"] / max(1, st["shown"]),
             "saved": st["saved"], "frame": pb.frame}
    log("끝: 보여 준 프레임 %d, 건너뛴 프레임 %d, 평균 렌더 %.1fms" % (stats["shown"], stats["skipped"], stats["avg_ms"]))
    return stats
