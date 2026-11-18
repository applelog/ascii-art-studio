"""F5: 필드 렌더 (슈퍼샘플링) + 후처리 (블룸·톤매핑·비네트) + 색 필드 → 글자."""
import importlib.util
import os
import time

import numpy as np
import pytest

from asciiart.grid import Grid
from asciiart.player import PieceRenderer
from asciiart.post import blur, bloom, tonemap, vignette
from asciiart.ramp import RAMPS
from asciiart.shade import coords, downsample, field_to_grid, half_width, luminance, shade

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "examples", "f5_demo.py")


def load(path):
    spec = importlib.util.spec_from_file_location("f5demo", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return vars(m)


def disc(X, Y, r=0.5):
    return (np.hypot(X, Y) < r).astype(float)


# ---------- 좌표 · 슈퍼샘플링 ----------
def test_coords_shape_range_and_cache():
    X, Y = coords(40, 20, 0.6, 2)
    assert X.shape == (40, 80)
    hw = half_width(40, 20, 0.6)
    assert X.min() > -hw and X.max() < hw and np.isclose(X.mean(), 0)
    assert Y.max() < 1 and Y.min() > -1 and Y[0, 0] > Y[-1, 0]          # 위가 +
    assert coords(40, 20, 0.6, 2)[0] is X
    with pytest.raises(ValueError):
        X[0, 0] = 5                                                        # 캐시는 읽기 전용


def test_supersampling_softens_edges():
    hard = shade(disc, 60, 30, 0.6, 1)
    soft = shade(disc, 60, 30, 0.6, 3)
    partial = lambda f: int(((f > 0.01) & (f < 0.99)).sum())
    assert partial(hard) == 0 and partial(soft) > 20


def test_disc_is_round_on_screen():
    f = shade(disc, 120, 60, 0.6, 2) > 0.5
    ys, xs = np.nonzero(f)
    w_rows = (xs.ptp() + 1) * 0.6               # 가로 칸 수 × 칸 너비 비율 = 세로 칸 단위 너비
    h_rows = ys.ptp() + 1
    assert abs(w_rows / h_rows - 1) < 0.06


def test_downsample_keeps_mean():
    a = np.random.RandomState(1).rand(30, 60, 3)
    assert np.isclose(downsample(a, 3).mean(), a.mean())
    assert downsample(a, 3).shape == (10, 20, 3)


# ---------- 색 필드 → 글자 ----------
def test_field_to_grid_brightness_cut_color():
    rgb = np.zeros((2, 3, 3))
    rgb[0, 0] = (1, 1, 1)          # 가장 밝음 → 마지막 램프 글자
    rgb[0, 1] = (0.02, 0.02, 0.02) # cut 아래 → 빈칸
    rgb[0, 2] = (0.3, 0.1, 0.0)    # 어두운 주황 → 글자 색은 min_color 까지 끌어올림, 색조 유지
    g = Grid(3, 2)
    field_to_grid(rgb, g, RAMPS["short"], cut=0.05, min_color=0.6)
    assert chr(g.ch[0, 0]) == "@" and g.ch[0, 1] == 0
    r, gg, b = g.rgb[0, 2].astype(int)
    assert r >= 150 and r > gg > b                                          # 밝아졌지만 주황 그대로


def test_field_to_grid_mask_and_quantize():
    rgb = np.full((4, 4, 3), 0.8)
    rgb[..., 1] = 0.41
    g = Grid(4, 4)
    mask = np.zeros((4, 4), bool)
    mask[:2] = True
    field_to_grid(rgb, g, RAMPS["short"], color_levels=3, mask=mask)
    assert (g.ch[2:] == 0).all() and (g.ch[:2] != 0).all()
    assert set(np.unique(g.rgb[:2])) <= {0, 128, 255}


def test_luminance_weights():
    assert np.isclose(luminance(np.array([1.0, 1.0, 1.0])), 1.0)
    assert luminance(np.array([0.0, 1.0, 0.0])) > luminance(np.array([1.0, 0.0, 0.0]))


# ---------- 후처리 ----------
def test_blur_is_round_and_keeps_energy():
    a = np.zeros((41, 81))
    a[20, 40] = 1
    b = blur(a, 4, cell_aspect=0.5)
    assert np.isclose(b.sum(), 1, atol=1e-6)
    ys, xs = np.nonzero(b > b.max() * 0.1)
    assert (xs.ptp() + 1) > 1.6 * (ys.ptp() + 1)       # 칸이 좁으니 가로로 더 많은 칸에 번짐


def test_bloom_spreads_only_bright_light():
    rgb = np.zeros((30, 30, 3))
    rgb[13:17, 13:17] = 1.5
    out = bloom(rgb, 1.0, 3, threshold=0.5)
    assert out[10, 15].sum() > 0 and rgb[10, 15].sum() == 0               # 주변이 밝아짐
    dim = np.full((10, 10, 3), 0.3)
    assert np.allclose(bloom(dim, 1.0, 3, threshold=0.5), dim)            # 기준보다 어두우면 그대로
    assert np.allclose(bloom(rgb, 0, 3), rgb)


def test_tonemap_curve_white_point_and_color():
    x = np.linspace(0, 5, 50)[:, None] * np.array([1.0, 0.6, 0.2])
    t = tonemap(x, 2.0)
    lum = luminance(t)
    assert (np.diff(lum) >= -1e-12).all() and lum.max() < 1                # 단조 증가, 1 에 닿지 않음
    assert np.allclose(t[10] / t[10, 0], x[10] / x[10, 0])                 # keep_color: 색 비율 유지
    w = tonemap(np.array([[1.0, 1.0, 1.0]]) * 1.3, 1.6, white=1.3)
    assert np.allclose(luminance(w), 1.0)                                  # 흰색 기준 → 정확히 1
    per = tonemap(np.array([[3.0, 1.0, 0.2]]), 2.0, keep_color=False)
    assert per[0, 0] < 1 and per[0, 2] / per[0, 0] > 0.2 / 3.0             # 채널별: 흰색 쪽으로 바램
    assert np.allclose(tonemap(x, 0), x)


def test_vignette_darkens_corners_only():
    rgb = np.ones((40, 80, 3))
    v = vignette(rgb, 0.6, cell_aspect=0.6)
    assert v[20, 40].min() > 0.99 and v[0, 0].max() < 0.5
    assert np.allclose(vignette(rgb, 0), rgb)


# ---------- 데모 작품 ----------
def test_demo_loops_and_is_deterministic():
    r = PieceRenderer(load(DEMO))
    assert r.grid_at_phase(0).digest() == r.grid_at_phase(1).digest()
    a = r.grid_at(20).digest()
    r.grid_at(50)
    assert r.grid_at(20).digest() == a
    assert r.grid_at(0).digest() != r.grid_at(r.n // 4).digest()          # 코로나가 숨 쉰다


def test_demo_post_processing_changes_picture():
    on = PieceRenderer(load(DEMO)).grid_at(0).digest()
    ns = load(DEMO)
    ns.update(BLOOM=0, EXPOSURE=0, VIGNETTE=0)
    assert PieceRenderer(ns).grid_at(0).digest() != on


def test_demo_frame_budget():
    r = PieceRenderer(load(DEMO))
    r.image_at(0)
    t0 = time.perf_counter()
    for i in range(10):
        r.image_at(i * 7)
    ms = (time.perf_counter() - t0) / 10 * 1000
    print("f5 demo frame %.1f ms" % ms)
    assert ms < 40
