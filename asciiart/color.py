"""밝기 → 색."""
import numpy as np


def palette_color(lum, palette, min_color=0.0):
    """밝기 0..1 → 팔레트(어두움→밝음) 사이를 보간한 색 (…, 3) uint8.

    min_color: 어두운 칸의 글자도 보이도록 색 밝기 하한을 준다 (0..1).
    """
    pal = np.asarray(palette, np.float64)
    if len(pal) == 1:
        return np.broadcast_to(pal[0], np.shape(lum) + (3,)).round().astype(np.uint8)
    t = np.clip(min_color + (1 - min_color) * np.clip(lum, 0, 1), 0, 1) * (len(pal) - 1)
    i = np.clip(np.floor(t).astype(np.int64), 0, len(pal) - 2)
    f = (t - i)[..., None]
    return (pal[i] * (1 - f) + pal[i + 1] * f).round().astype(np.uint8)


def quantize(rgb, levels):
    """색을 채널마다 levels 단계로 줄인다 (eyeTutorial 의 QL). 0 이면 그대로."""
    if not levels:
        return np.asarray(rgb, np.uint8)
    q = np.round(np.asarray(rgb, np.float64) / 255.0 * (levels - 1)) / (levels - 1) * 255.0
    return q.round().astype(np.uint8)


def rgb01(c):
    """(r, g, b) 0..255 → numpy 0..1 (필드 렌더에서 색을 곱할 때)."""
    return np.asarray(c, np.float64) / 255.0
