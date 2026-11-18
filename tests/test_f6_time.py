"""F6: 시간 도구 (이징·노이즈·사건 일정표) + 잔상·글로우 + 루프 이음."""
import importlib.util
import math
import os
import time

import numpy as np
import pytest

from asciiart.ease import (ease_in, ease_in_out, ease_out, exp_lerp, keyframes, loop_cycles, loop_sin, overshoot,
                           segment, smoothstep)
from asciiart.effects import TrailGlow, warmup_frames
from asciiart.noise import fbm, loop_noise, noise1, noise2, noise3
from asciiart.player import PieceRenderer
from asciiart.schedule import active, make_schedule

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "examples", "f6_demo.py")


def load(**over):
    spec = importlib.util.spec_from_file_location("f6demo", DEMO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ns = vars(m)
    ns.update(over)
    return ns


SMALL = dict(COLS=60, ROWS=30, FONT_PX=8, LOOP_SECONDS=2, STAR_COUNT=40, METEORS=3, METEOR_GAP=0.2,
             T_IN=0.1, T_IN_D=0.4, T_OUT=1.3, T_OUT_D=0.4)


# ---------- 이징 ----------
def test_segment_and_curves_endpoints():
    assert segment(5, 0, 10) == 0.5 and segment(-1, 0, 10) == 0 and segment(11, 0, 10) == 1
    for f in (ease_in, ease_out, ease_in_out):
        assert np.isclose(f(0), 0) and np.isclose(f(1), 1)
    assert np.isclose(smoothstep(0, 2, 1), 0.5)
    assert ease_in(0.5) < 0.5 < ease_out(0.5)


def test_overshoot_goes_past_then_settles():
    ps = np.linspace(0, 1, 201)
    v = overshoot(ps)
    assert np.isclose(v[0], 0) and np.isclose(v[-1], 1) and 1.05 < v.max() < 1.15
    assert overshoot(ps, 3.0).max() > v.max()


def test_keyframes_and_exp_lerp():
    keys = [(0, 0.0), (1, 10.0), (2, 4.0)]
    assert keyframes(-5, keys) == 0 and keyframes(9, keys) == 4
    assert keyframes(1, keys) == 10 and np.isclose(keyframes(0.5, keys), 5)
    assert np.isclose(exp_lerp(1, 100, 0.5), 10)              # 줌: 중간 배율은 기하평균


def test_loop_sin_repeats():
    assert np.isclose(loop_sin(0.0, 3, 0.2), loop_sin(1.0, 3, 0.2))
    assert np.isclose(loop_sin(0.0, 2.6, 0), loop_sin(1.0, 2.6, 0))   # 소수 주기도 정수로 반올림
    assert loop_cycles(0.2) == 1 and loop_cycles(2.6) == 3


# ---------- 노이즈 ----------
def test_noise_range_determinism_and_seed():
    X, Y = np.meshgrid(np.linspace(-5, 5, 80), np.linspace(-3, 3, 40))
    a = noise2(X, Y, 1)
    assert a.min() >= 0 and a.max() <= 1
    assert (a == noise2(X, Y, 1)).all() and not (a == noise2(X, Y, 2)).all()
    assert noise3(X, Y, 0.3, 1).shape == X.shape and np.ndim(noise1(0.5)) == 0


def test_noise_is_smooth():
    x = np.linspace(0, 10, 2001)
    v = noise1(x, 3)
    assert np.abs(np.diff(v)).max() < 0.02                     # 촘촘히 보면 끊김 없음


def test_fbm_normalized_and_loop_noise_seamless():
    X, Y = np.meshgrid(np.linspace(0, 4, 60), np.linspace(0, 2, 30))
    f = fbm(X, Y, octaves=5)
    assert 0 <= f.min() and f.max() <= 1
    a, b = loop_noise(X, Y, 0.0, 1.3, seed=4), loop_noise(X, Y, 1.0, 1.3, seed=4)
    assert np.abs(a - b).max() < 1e-12
    assert np.abs(a - loop_noise(X, Y, 0.5, 1.3, seed=4)).max() > 0.1


# ---------- 사건 일정표 ----------
def test_schedule_deterministic_with_gaps():
    a = make_schedule(7, 6, 6.0, (0.5, 0.9), min_gap=0.6)
    b = make_schedule(7, 6, 6.0, (0.5, 0.9), min_gap=0.6)
    assert [e["start"] for e in a] == [e["start"] for e in b] and len(a) == 6
    starts = [e["start"] for e in a]
    for i, s in enumerate(starts):
        for o in starts[i + 1:]:
            assert min(abs(s - o), 6 - abs(s - o)) >= 0.6 - 1e-9
    assert all(0.5 <= e["dur"] <= 0.9 for e in a) and len(a[0]["rand"]) >= 4


def test_active_wraps_around_loop_end():
    ev = [{"start": 5.8, "dur": 0.5, "rand": np.zeros(8)}]
    assert active(ev, 5.9, 6.0) and active(ev, 0.2, 6.0)          # 끝에서 시작해 처음으로 이어짐
    assert np.isclose(active(ev, 0.2, 6.0)[0][1], 0.8)
    assert not active(ev, 0.4, 6.0)
    assert not active(ev, 0.2, 6.0, loop=False)


# ---------- 잔상·글로우 ----------
def test_warmup_frames():
    from asciiart.effects import trail_release
    assert warmup_frames(0) == 0
    k = warmup_frames(0.82)
    r = trail_release(0.82)
    assert 255 - k * r <= 0 < 255 - (k - 1) * r                  # 선형 감쇠: k 프레임 뒤 정확히 사라짐
    assert warmup_frames(0.9) > warmup_frames(0.5)                 # TRAIL 이 클수록 꼬리가 길다


def _dot(bg, color, shape=(40, 60, 3)):
    img = np.empty(shape, np.uint8)
    img[...] = bg
    img[18:22, 28:32] = color
    return img


def test_trail_fades_to_background():
    bg = (10, 10, 20)
    fx = TrailGlow(bg, trail=0.8)
    fx.apply(_dot(bg, (250, 250, 250)))
    blank = _dot(bg, bg)
    out = fx.apply(blank)
    assert out[20, 30, 0] > 150                                    # 다음 프레임에 잔상
    for _ in range(warmup_frames(0.8)):
        out = fx.apply(blank)
    assert (out == blank).all()                                    # 충분히 지나면 완전히 사라짐


def test_trail_on_light_background_darkens():
    bg = (240, 236, 225)
    fx = TrailGlow(bg, trail=0.8)
    fx.apply(_dot(bg, (20, 20, 20)))
    out = fx.apply(_dot(bg, bg))
    assert out[20, 30, 0] < 120                                    # 밝은 종이에는 어두운 잔상


def test_glow_spreads_light_near_glyphs_only():
    bg = (0, 0, 0)
    fx = TrailGlow(bg, glow=1.0, glow_radius_px=6)
    out = fx.apply(_dot(bg, (255, 255, 255), (80, 120, 3)))
    assert out[20, 30].sum() > 0 and out[20, 26].sum() > 0          # 글자 옆이 밝아짐
    assert (out[75, 5] == 0).all()                                  # 먼 곳은 그대로


# ---------- 데모 작품: 루프 이음과 탐색 재현 ----------
def test_demo_grid_loops():
    r = PieceRenderer(load(**SMALL))
    assert r.grid_at_phase(0).digest() == r.grid_at_phase(1).digest()
    assert r.grid_at(0).digest() != r.grid_at(r.n // 3).digest()


def test_demo_trail_loop_is_seamless():
    """한 바퀴 연속 재생한 다음의 0번 프레임 = 처음 본 0번 프레임 (잔상까지 이어짐)."""
    r = PieceRenderer(load(**SMALL))
    first = [r.image_at(i).copy() for i in range(r.n)]
    again = r.image_at(r.n)                                         # 연속으로 이어서 0번
    assert (again == first[0]).all()
    assert (r.image_at(r.n + 5) == first[5]).all()


@pytest.mark.parametrize("frame", [0, 7, 31, 59])
def test_demo_seek_equals_sequential(frame):
    """아무 프레임으로 건너뛰어도 (앞에서부터 다시 계산) 연속 재생과 같은 그림."""
    seq = PieceRenderer(load(**SMALL))
    for i in range(frame + 1):
        img = seq.image_at(i)
    jump = PieceRenderer(load(**SMALL)).image_at(frame)
    assert (jump == img).all()


def test_demo_trail_off_changes_picture():
    a = PieceRenderer(load(**SMALL)).image_at(10)
    b = PieceRenderer(load(TRAIL=0, GLOW=0, **SMALL)).image_at(10)
    assert not (a == b).all()


def test_demo_sequential_frame_budget():
    r = PieceRenderer(load())
    r.image_at(0)
    t0 = time.perf_counter()
    for i in range(1, 16):
        r.image_at(i)
    ms = (time.perf_counter() - t0) / 15 * 1000
    print("f6 demo sequential frame %.1f ms" % ms)
    assert ms < 33


def test_playback_fast_path_does_not_rebuild_on_small_skips():
    """창 재생 중(exact=False) 몇 프레임 건너뛰어도 다시 계산하지 않는다 (재생이 밀리는 악순환 방지)."""
    r = PieceRenderer(load(**SMALL))
    r.image_at(0)
    calls = []
    orig = r.base_image
    r.base_image = lambda k, bgr=False: (calls.append(k), orig(k, bgr))[1]
    r.image_at(3, exact=False)                       # 2칸 건너뜀
    assert calls == [3]
    calls.clear()
    exact = r.image_at(10)                           # 정확한 그림 요청 → 앞에서부터 다시 계산
    assert len(calls) == r.warmup + 1
    assert (exact == PieceRenderer(load(**SMALL)).image_at(10)).all()
