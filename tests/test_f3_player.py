"""F3: 시간 → 프레임, 설정 검사, 재생 상태, 창 재생(가짜 창·가짜 시계)."""
import importlib.util
import os

import numpy as np
import pytest
from PIL import Image

from asciiart.config import apply_set, check, setting_names
from asciiart.player import KEYMAP, PieceRenderer, Playback, play
from asciiart.timeline import frame_at, frame_count, frame_phase, frame_time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "examples", "f3_demo.py")
BOAT = os.path.join(ROOT, "pieces", "fishing-boat", "piece.py")


def load(path):
    spec = importlib.util.spec_from_file_location("m_" + os.path.basename(path).replace(".", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return vars(mod)


class FakeClock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


# ---------- timeline ----------
def test_frame_count_and_no_duplicate_end():
    assert frame_count(4, 30) == 120
    assert frame_count(0.01, 30) == 1
    assert frame_phase(0, 120) == 0
    assert frame_phase(119, 120) < 1
    assert frame_time(90, 30) == 3


def test_frame_at_loop_and_end():
    assert frame_at(1.0, 30, 120) == (30, False)
    assert frame_at(4.0, 30, 120) == (0, False)        # 루프: 처음으로
    assert frame_at(5.0, 30, 120, loop=False) == (119, True)


# ---------- config ----------
def test_setting_names_from_file():
    names = setting_names(DEMO)
    assert names[:2] == ["COLS", "ROWS"]
    assert "WAVES" in names and "RANGES" not in names
    boat = setting_names(BOAT)
    assert "MOON_X" in boat and "LANTERN_DX" in boat and "LANTERN_DY" in boat


def test_check_clamps_and_warns():
    ns = load(DEMO)
    ns.update(COLS=9999, FPS=29, WAVES=20, BACKGROUND=(300, -5, 10.4))
    warnings = check(ns, setting_names(DEMO))
    assert ns["COLS"] == 400 and ns["FPS"] == 30 and ns["WAVES"] == 8
    assert ns["BACKGROUND"] == (255, 0, 10)
    assert len(warnings) == 4


def test_check_rejects_bad_types():
    ns = load(DEMO)
    ns["RAMP"] = "x"
    with pytest.raises(SystemExit):
        check(ns, setting_names(DEMO))


def test_apply_set():
    ns = load(DEMO)
    names = setting_names(DEMO)
    assert apply_set(ns, ["WAVES=3", "RAMP= .oO@", "PALETTE=[(1,2,3)]"], names) == ["WAVES", "RAMP", "PALETTE"]
    assert ns["WAVES"] == 3 and ns["RAMP"] == ".oO@"
    for bad in (["NOPE=1"], ["WAVES=abc"], ["BACKGROUND=(1,2)"], ["LOOP=3"], ["WAVES"]):
        with pytest.raises(SystemExit):
            apply_set(load(DEMO), bad, names)


def test_unknown_setting_suggests_close_name():
    with pytest.raises(SystemExit) as e:
        apply_set(load(DEMO), ["WAVE=3"], setting_names(DEMO))
    assert "WAVES" in str(e.value)


# ---------- 재생 상태 ----------
def test_playback_real_time_pause_resume():
    c = FakeClock()
    pb = Playback(120, 30, True, c)
    c.t += 1.0
    assert pb.update() == 30
    pb.toggle()                         # 정지
    c.t += 5.0
    assert pb.update() == 30            # 정지 중에는 그대로
    pb.toggle()                         # 재생: 멈춘 곳부터 이어서
    c.t += 0.5
    assert pb.update() == 45


def test_playback_restart_step_and_wrap():
    c = FakeClock()
    pb = Playback(120, 30, True, c)
    c.t += 2.0
    pb.step(+1)
    assert (pb.frame, pb.playing) == (61, False)
    pb.restart()
    assert (pb.update(), pb.playing) == (0, True)
    pb.step(-1)
    assert pb.frame == 119              # 루프면 앞뒤가 이어진다


def test_playback_non_loop_stops_at_end():
    c = FakeClock()
    pb = Playback(60, 30, False, c)
    c.t += 10
    assert pb.update() == 59 and not pb.playing
    pb.toggle()                         # 끝에서 다시 누르면 처음부터
    assert pb.frame == 0 and pb.playing


def test_still_piece_has_one_frame():
    r = PieceRenderer(load(BOAT))
    assert r.kind == "still" and r.n == 1
    assert not Playback(r.n, r.fps).playing


# ---------- 렌더 ----------
def test_same_frame_same_image_and_frames_differ():
    r = PieceRenderer(load(DEMO))
    a = r.image_at(17).copy()
    r.image_at(80)
    assert (r.image_at(17) == a).all()
    assert not (r.image_at(0) == a).all()


def test_wave_loops_seamlessly():
    ns = load(DEMO)
    ns["TEXT_ROW"] = -100                # 글씨(시간 표시)는 빼고 물결만 비교
    r = PieceRenderer(ns)
    assert r.grid_at_phase(0).digest() == r.grid_at_phase(1).digest()


def test_settings_change_picture():
    a = PieceRenderer(load(DEMO)).grid_at(10).digest()
    ns = load(DEMO)
    apply_set(ns, ["WAVES=3"], setting_names(DEMO))
    assert PieceRenderer(ns).grid_at(10).digest() != a


# ---------- 창 재생 (가짜 창) ----------
class FakeDisplay:
    """키를 순서대로 누르고, 기다린 만큼 가짜 시계를 진행한다."""

    def __init__(self, clock, keys):
        self.clock, self.keys, self.shown, self.titles = clock, list(keys), [], []

    def show(self, img):
        self.shown.append(img.copy())

    def wait_action(self, ms):
        self.clock.t += ms / 1000.0
        return KEYMAP.get(self.keys.pop(0) if self.keys else -1)

    def title(self, text):
        self.titles.append(text)

    def closed(self):
        return False

    def close(self):
        pass


def test_play_keys_and_save(tmp_path):
    c = FakeClock()
    r = PieceRenderer(load(DEMO))
    keys = [-1] * 5 + [32, ord("."), ord("."), ord("s"), ord(","), ord("r"), -1, -1, 27]
    d = FakeDisplay(c, keys)
    stats = play(r, "demo", str(tmp_path), display=d, clock=c, log=lambda *_: None)
    assert len(stats["saved"]) == 1
    saved = np.asarray(Image.open(stats["saved"][0]).convert("RGB"))
    frame_no = int(os.path.basename(stats["saved"][0])[6:10])
    assert (saved == PieceRenderer(load(DEMO)).image_at(frame_no)).all()   # 저장 = 같은 번호의 렌더
    assert stats["shown"] >= 5 and d.titles


def test_play_stops_after_max_seconds(tmp_path):
    c = FakeClock()
    d = FakeDisplay(c, [])
    stats = play(PieceRenderer(load(DEMO)), "demo", str(tmp_path), display=d, clock=c, max_seconds=2, log=lambda *_: None)
    assert 50 <= stats["shown"] <= 62          # 2초 × 30fps 근처


def test_arrow_keys_mapped_for_all_platforms():
    assert {KEYMAP[k] for k in (63234, 2424832, 65361)} == {"prev"}
    assert {KEYMAP[k] for k in (63235, 2555904, 65363)} == {"next"}


def test_ctrl_c_closes_window_cleanly(tmp_path):
    """터미널에서 Ctrl+C 를 눌러도 오류 없이 창을 닫고 통계를 돌려준다."""
    c = FakeClock()

    class InterruptDisplay(FakeDisplay):
        closed_called = False

        def wait_action(self, ms):
            if len(self.shown) >= 3:
                raise KeyboardInterrupt
            return super().wait_action(ms)

        def close(self):
            InterruptDisplay.closed_called = True

    d = InterruptDisplay(c, [])
    stats = play(PieceRenderer(load(DEMO)), "demo", str(tmp_path), display=d, clock=c, log=lambda *_: None)
    assert InterruptDisplay.closed_called and stats["shown"] >= 3


# ---------- pygame 창 (실제 화면 없이: SDL dummy) ----------
@pytest.fixture
def dummy_pygame(monkeypatch):
    pygame = pytest.importorskip("pygame")
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    yield pygame
    pygame.display.quit()


def test_pygame_display_shows_and_maps_keys(dummy_pygame):
    from asciiart.player import PygameDisplay
    pg = dummy_pygame
    img = PieceRenderer(load(DEMO)).image_at(5)
    d = PygameDisplay("t", img.shape[1], img.shape[0])
    d.show(img)
    shown = pg.surfarray.array3d(pg.display.get_surface()).transpose(1, 0, 2)
    if d.view == d.size:
        assert (shown == img).all()                       # 원본 크기면 화면 = 렌더 그대로
    for key, action in [(pg.K_SPACE, "toggle"), (pg.K_r, "restart"), (pg.K_s, "save"),
                        (pg.K_LEFT, "prev"), (pg.K_PERIOD, "next"), (pg.K_ESCAPE, "quit")]:
        pg.event.post(pg.event.Event(pg.KEYDOWN, key=key, scancode=0, mod=0, unicode=""))
        assert d.wait_action(50) == action
    # 한글 입력 상태처럼 key 가 다르게 와도 물리 키 위치(scancode)로 찾는다
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=0, scancode=pg.KSCAN_R, mod=0, unicode="ㄱ"))
    assert d.wait_action(50) == "restart"
    assert d.wait_action(5) is None                       # 아무것도 안 누르면 None
    pg.event.post(pg.event.Event(pg.QUIT))
    assert d.wait_action(50) == "quit" and d.closed()
    d.close()


def test_pygame_display_scales_big_images(dummy_pygame, monkeypatch):
    from asciiart.player import PygameDisplay
    monkeypatch.setattr(PygameDisplay, "SCREEN_FILL", 0.0001)   # 화면이 아주 작다고 가정 → 축소
    d = PygameDisplay("t", 1200, 960)
    if d.view != d.size:                                         # dummy 는 화면 크기를 모를 수 있음
        assert max(d.view) == PygameDisplay.MIN_VIEW              # 아무리 작아도 최소 크기는 지킨다
        assert abs(d.view[0] / d.view[1] - 1200 / 960) < 0.02    # 비율 유지
    d.show(np.zeros((960, 1200, 3), np.uint8))
    d.close()


def test_make_display_picks_pygame_when_available(dummy_pygame):
    from asciiart.player import make_display
    d = make_display("t", 200, 100)
    assert d.backend == "pygame" and d.bgr is False
    d.close()


def test_play_with_pygame_display(dummy_pygame, tmp_path):
    from asciiart.player import PygameDisplay
    pg = dummy_pygame
    r = PieceRenderer(load(DEMO))
    img = r.image_at(0)
    d = PygameDisplay("t", img.shape[1], img.shape[0])
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_s, scancode=0, mod=0, unicode="s"))
    stats = play(r, "demo", str(tmp_path), display=d, max_seconds=0.5, log=lambda *_: None)
    assert stats["shown"] >= 3 and len(stats["saved"]) == 1
