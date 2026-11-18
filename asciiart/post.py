"""색 필드 후처리 (글자로 바꾸기 전에): 블룸 · 톤매핑 · 비네트.

색 필드는 (rows, cols, 3) 실수 배열, 0..1 기준이지만 1 을 넘어도 된다 (아주 밝은 빛).
톤매핑이 1 을 넘는 값을 자연스럽게 0..1 로 눌러 준다.
"""
import numpy as np


def _box_blur_axis(a, r, axis):
    """한 축 방향 상자 흐림 (누적합). r = 반지름 (칸)."""
    if r <= 0:
        return a
    r = int(round(r))
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=axis)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / float(2 * r + 1)


def blur(a, radius, cell_aspect=1.0, passes=3):
    """부드러운 흐림 (상자 흐림을 여러 번 = 가우시안에 가까움).

    radius 는 세로 칸 단위. 칸이 세로로 길어서 가로는 radius / cell_aspect 칸을 흐린다 → 둥근 번짐.
    """
    out = np.asarray(a, np.float64)
    ry = radius / np.sqrt(passes)
    rx = ry / cell_aspect
    for _ in range(passes):
        out = _box_blur_axis(out, ry, 0)
        out = _box_blur_axis(out, rx, 1)
    return out


def bloom(rgb, strength, radius=4.0, threshold=0.6, cell_aspect=1.0):
    """밝은 부분(threshold 초과)을 흐려서 더한다 → 빛이 번져 보임."""
    if strength <= 0:
        return np.asarray(rgb, np.float64)
    rgb = np.asarray(rgb, np.float64)
    bright = np.maximum(rgb - threshold, 0)
    return rgb + blur(bright, radius, cell_aspect) * strength


def tonemap(rgb, exposure=2.0, keep_color=True, white=None):
    """1 − exp(−exposure·x): 밝은 값을 부드럽게 0..1 로 누른다 (eyeTutorial). exposure 0 이면 그대로.

    keep_color=True  : 밝기만 누르고 색 비율은 유지한다 (주황은 주황으로 남음)
    keep_color=False : 채널마다 누른다 (아주 밝은 곳이 흰색 쪽으로 바램, eyeTutorial 원래 방식)
    white            : 이 밝기가 정확히 1(가장 진한 글자)이 되게 맞춘다. None 이면 1 에 닿지 않는다
    """
    norm = 1.0 / (1 - np.exp(-exposure * white)) if (white and exposure > 0) else 1.0
    rgb = np.maximum(np.asarray(rgb, np.float64), 0)
    if exposure <= 0:
        return rgb
    if not keep_color:
        return np.clip((1 - np.exp(-exposure * rgb)) * norm, 0, 1)
    lum = 0.30 * rgb[..., 0] + 0.60 * rgb[..., 1] + 0.10 * rgb[..., 2]
    scale = np.where(lum > 0, (1 - np.exp(-exposure * lum)) * norm / np.maximum(lum, 1e-12), exposure * norm)
    out = rgb * scale[..., None]
    # 한 채널이 1 을 넘으면 세 채널을 같이 줄인다 (잘라내면 색조가 바뀌므로)
    peak = out.max(axis=-1, keepdims=True)
    return np.where(peak > 1, out / np.maximum(peak, 1e-12), out)


def vignette(rgb, amount, cell_aspect=1.0, power=2.0):
    """가장자리를 어둡게. amount 0..1 (1 이면 모서리가 거의 검정). 화면 비율을 반영해 둥글게."""
    rgb = np.asarray(rgb, np.float64)
    if amount <= 0:
        return rgb
    rows, cols = rgb.shape[:2]
    y = (np.arange(rows) + 0.5) / rows * 2 - 1
    x = ((np.arange(cols) + 0.5) / cols * 2 - 1) * (cols * cell_aspect / rows)
    X, Y = np.meshgrid(x, y)
    r = np.hypot(X, Y) / np.hypot(cols * cell_aspect / rows, 1)   # 모서리 = 1
    k = 1 - amount * np.clip(r, 0, 1) ** power
    return rgb * (k[..., None] if rgb.ndim == 3 else k)
