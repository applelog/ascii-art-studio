"""필드 렌더 (eyeTutorial 방식): 화면의 모든 점에서 색을 numpy 로 한 번에 계산한 뒤 글자로 바꾼다.

    X, Y = coords(...)                 화면 좌표 (슈퍼샘플링된 점들)
    rgb  = shade(fn, ...)              fn(X, Y) → 색 (0..1, 1 보다 커도 됨) → 칸마다 평균
    field_to_grid(rgb, grid, ramp)     칸 밝기 → 램프 글자, 칸 색 → 글자 색

좌표: 화면 높이가 위 +1 … 아래 −1, 가로는 화면 비율만큼 (−half_w … +half_w).
칸이 세로로 긴 것(cell_aspect)을 반영하므로 원은 화면에서도 둥글다.
"""
import numpy as np

from .color import quantize
from .ramp import RAMPS, ramp_chars

_COORD_CACHE = {}


def half_width(cols, rows, cell_aspect):
    """화면 가로 절반 길이 (세로 절반 = 1 기준)."""
    return cols * cell_aspect / float(rows)


def coords(cols, rows, cell_aspect, ss=1):
    """슈퍼샘플링된 점들의 화면 좌표 X, Y — 모양 (rows*ss, cols*ss). 같은 인자면 캐시를 쓴다."""
    key = (cols, rows, cell_aspect, ss)
    if key not in _COORD_CACHE:
        hw = half_width(cols, rows, cell_aspect)
        u = (np.arange(cols * ss) + 0.5) / (cols * ss)          # 0..1 왼→오
        v = (np.arange(rows * ss) + 0.5) / (rows * ss)          # 0..1 위→아래
        X, Y = np.meshgrid((u * 2 - 1) * hw, 1 - v * 2)
        X.setflags(write=False)
        Y.setflags(write=False)
        _COORD_CACHE[key] = (X, Y)
    return _COORD_CACHE[key]


def downsample(img, ss):
    """(rows*ss, cols*ss[, 3]) → (rows, cols[, 3]) 칸마다 평균 (슈퍼샘플링)."""
    if ss == 1:
        return np.asarray(img, np.float64)
    h, w = img.shape[0] // ss, img.shape[1] // ss
    if img.ndim == 2:
        return img.reshape(h, ss, w, ss).mean(axis=(1, 3))
    return img.reshape(h, ss, w, ss, img.shape[2]).mean(axis=(1, 3))


def shade(fn, cols, rows, cell_aspect, ss=1):
    """fn(X, Y) 로 화면 전체 색을 계산하고 칸마다 평균 낸다.

    fn 은 (H, W, 3) 색 또는 (H, W) 밝기를 돌려준다. 결과는 (rows, cols, 3) 또는 (rows, cols).
    ss: 칸 하나를 ss×ss 점으로 계산 (1~3). 테두리가 부드러워진다.
    """
    X, Y = coords(cols, rows, cell_aspect, ss)
    return downsample(np.asarray(fn(X, Y), np.float64), ss)


def luminance(rgb):
    """eyeTutorial 의 밝기 공식 0.30R + 0.60G + 0.10B (색 0..1)."""
    rgb = np.asarray(rgb, np.float64)
    return 0.30 * rgb[..., 0] + 0.60 * rgb[..., 1] + 0.10 * rgb[..., 2]


def field_to_grid(rgb, grid, ramp=RAMPS["short"], cut=0.0, gamma=1.0, dither=0.0, mode="hash",
                  shimmer=0.0, step=0, seed=0, color_levels=0, min_color=0.0, mask=None):
    """색 필드 (rows, cols, 3) 0..1 → grid 글자와 색.

    min_color   어두운 칸의 글자 색을 이 밝기까지 끌어올린다 (글자 자체가 밝기를 표현하므로)
    color_levels 색을 채널마다 이 단계로 줄인다 (eyeTutorial QL=24). 0 이면 그대로
    mask        True 인 칸에만 쓴다 (다른 그림 위에 겹칠 때)
    """
    rgb = np.clip(np.asarray(rgb, np.float64), 0, 1)
    lum = luminance(rgb)
    yy, xx = np.mgrid[0:grid.rows, 0:grid.cols]
    codes = ramp_chars(lum, ramp, cut=cut, gamma=gamma, dither=dither, mode=mode,
                       shimmer=shimmer, step=step, xx=xx, yy=yy, seed=seed)
    color = rgb
    if min_color > 0:
        peak = rgb.max(axis=-1, keepdims=True)
        lift = np.where(peak > 0, np.maximum(peak, min_color) / np.maximum(peak, 1e-9), 1.0)
        color = np.clip(rgb * lift, 0, 1)
    color = quantize(color * 255.0, color_levels)
    sel = codes != 0
    if mask is not None:
        sel &= np.asarray(mask, bool)
    grid.fill(sel, codes, color)
    return codes
