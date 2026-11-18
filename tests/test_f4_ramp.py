"""F4: 밝기 → 글자 (램프·감마·디더·반짝임·글자 풀·윤곽 방향)."""
import numpy as np
import pytest

from asciiart.color import palette_color, quantize
from asciiart.ramp import (BAYER4, GLYPH_POOLS, RAMPS, cell_hash, codes_of, dither_offset, edge_chars, edges,
                           levels, pool_chars, ramp_chars, thin_edges)

H, W = 60, 200
GRAD = np.tile(np.linspace(0, 1, W), (H, 1))      # 왼→오 0..1


SMOOTH = 4   # 눈이 보는 것처럼 가로 4칸씩 묶어 평균 (Bayer 는 4×4 칸 단위로 밝기를 만든다)


def banding_error(lv, n):
    """세로 전체·가로 4칸으로 평균 낸 단계가 이상적인 값(밝기×(n-1))에서 얼마나 벗어나는지 (최대, 단계 단위)."""
    k = np.ones(SMOOTH) / SMOOTH
    col = np.convolve(lv.mean(0), k, mode="same")
    ideal = np.convolve(np.linspace(0, 1, W) * (n - 1), k, mode="same")
    err = np.abs(col - ideal)[8:-8]          # 양 끝은 잘림·평균 경계 때문에 제외
    return err.max(), err.mean()


def test_ramp_ends():
    c = ramp_chars(np.array([[0.0, 1.0]]), RAMPS["short"])
    assert c[0, 0] == 0 and chr(c[0, 1]) == "@"


def test_no_dither_has_bands_dither_removes_them():
    n = len(RAMPS["short"])
    plain = banding_error(levels(GRAD, n), n)
    hashd = banding_error(levels(GRAD, n, dither=1.0), n)
    bayer = banding_error(levels(GRAD, n, dither=1.0, mode="bayer"), n)
    # 디더가 없으면 계단 (최대 0.4 단계 이상 어긋남), 있으면 평균이 밝기를 따라간다
    assert plain[0] > 0.35 and hashd[0] < 0.15 and bayer[0] < 0.15
    assert plain[1] > 4 * max(hashd[1], bayer[1])
    print("banding max/mean: none %.2f/%.2f  hash %.2f/%.2f  bayer %.2f/%.2f" % (plain + hashd + bayer))


def test_dither_is_fixed_per_cell():
    a = dither_offset((10, 10), "hash", seed=4)
    assert (a == dither_offset((10, 10), "hash", seed=4)).all()
    assert not (a == dither_offset((10, 10), "hash", seed=5)).all()
    assert a.min() >= -0.5 and a.max() < 0.5
    b = dither_offset((8, 8), "bayer")
    assert (b[:4, :4] == b[4:, 4:]).all() and len(np.unique(b)) == 16
    with pytest.raises(ValueError):
        dither_offset((2, 2), "nope")


def test_gamma_below_one_uses_more_dark_steps():
    n = len(RAMPS["long"])
    assert levels(GRAD, n, gamma=0.72).mean() > levels(GRAD, n).mean()


def test_cut_blanks_dark_cells():
    lv = levels(GRAD, 10, cut=0.3, dither=1.0)
    assert (lv[:, GRAD[0] < 0.3] == 0).all()
    assert (lv[:, GRAD[0] > 0.45] > 0).all()


def test_shimmer_changes_with_step_and_repeats():
    n = 10
    a = levels(GRAD, n, shimmer=1.0, step=0)
    assert not (a == levels(GRAD, n, shimmer=1.0, step=1)).all()
    assert (a == levels(GRAD, n, shimmer=1.0, step=0)).all()     # 같은 step → 같은 글자 (루프 이음)


def test_pool_chars_follow_brightness_and_shimmer():
    c = pool_chars(GRAD, GLYPH_POOLS, step=0)
    pools = [set(codes_of(p).tolist()) for p in GLYPH_POOLS]
    lo, hi = c[:, 10:30], c[:, -30:-10]
    assert set(np.unique(lo)) <= pools[0] and set(np.unique(hi)) <= pools[3]
    assert not (c == pool_chars(GRAD, GLYPH_POOLS, step=1)).all()
    assert (c[:, 0] == 0).all()                                 # 밝기 0 은 빈칸


def test_glyph_pools_get_darker_ink_per_level():
    """글자 풀은 단계마다 실제 글자 잉크 양(평균)이 늘어나야 밝기 순서가 맞는다."""
    from asciiart.atlas import GlyphAtlas
    atlas = GlyphAtlas("Menlo", 14, 0.6)
    ink = [np.mean([atlas.mask(ord(ch)).mean() for ch in p]) for p in GLYPH_POOLS]
    assert all(a < b for a, b in zip(ink, ink[1:])), ink


def _disc(r=10, aspect=0.6):
    yy, xx = np.mgrid[0:31, 0:61]
    d = np.hypot((xx - 30) * aspect, yy - 15)
    return np.clip(r - d + 0.5, 0, 1)


def test_edge_glyph_directions_on_a_disc():
    cover = _disc()
    mag, gx, gy = edges(cover, 0.6)
    ch = edge_chars(gx, gy)
    keep = thin_edges(mag, gx, gy, 0.2 * mag.max())
    def at(y, x):
        ys, xs = np.nonzero(keep)
        k = np.argmin((ys - y) ** 2 + (xs - x) ** 2)       # 그 근처 윤곽 칸
        return chr(ch[ys[k], xs[k]])
    assert at(15, 0) == "|" and at(15, 60) == "|"            # 왼쪽·오른쪽
    assert at(5, 30) == "-" and at(25, 30) == "-"            # 위·아래
    assert at(8, 18) == "/" and at(22, 42) == "/"            # 왼쪽 위·오른쪽 아래
    assert at(8, 42) == "\\" and at(22, 18) == "\\"          # 오른쪽 위·왼쪽 아래


def test_thin_edges_are_one_cell_thick():
    cover = _disc()
    mag, gx, gy = edges(cover, 0.6)
    keep = thin_edges(mag, gx, gy, 0.2 * mag.max())
    thick = (mag > 0.2 * mag.max())
    assert keep.sum() < thick.sum() * 0.6
    assert keep[15].sum() <= 4                                # 가운데 가로줄에서 왼쪽·오른쪽 몇 칸뿐


def test_palette_color_and_quantize():
    pal = [(0, 0, 0), (255, 255, 255)]
    c = palette_color(np.array([0.0, 0.5, 1.0]), pal)
    assert c.tolist() == [[0, 0, 0], [128, 128, 128], [255, 255, 255]]
    assert palette_color(np.array([0.0]), pal, min_color=0.4)[0, 0] == 102
    assert palette_color(np.zeros((2, 2)), [(9, 8, 7)]).shape == (2, 2, 3)
    q = quantize(np.array([[10, 128, 250]]), 3)
    assert set(q.ravel().tolist()) <= {0, 128, 255}


def test_cell_hash_range_and_spread():
    yy, xx = np.mgrid[0:50, 0:50]
    h = cell_hash(xx, yy, 1)
    assert h.min() >= 0 and h.max() < 1 and 0.4 < h.mean() < 0.6
    assert BAYER4.shape == (4, 4)
