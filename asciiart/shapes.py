"""2D 도형: 화면 좌표(세로 −1..1, 가로 ±half_width)에서 부호 거리(안쪽 음수)를 계산하고 글자로 그린다.

썰매·동물·간판처럼 3D 까지는 필요 없는 형태를 부위별 도형으로 조립할 때 쓴다.

    d = union2(ellipse2(X, Y, 0, 0, 0.2, 0.1), capsule2(X, Y, (0, 0), (0.3, 0.2), 0.03))
    cov = coverage(d, ss)                 # 칸마다 덮인 비율 0..1
    draw_line2(grid, (x0, y0), (x1, y1), CELL_ASPECT, "/", (255, 255, 255))
"""
import math

import numpy as np

from .shade import downsample, half_width


# ---------- 좌표 ----------
def to_cell(x, y, cols, rows, cell_aspect):
    """화면 좌표 → 칸 좌표 (실수, floor 하면 칸 번호)."""
    hw = half_width(cols, rows, cell_aspect)
    return (np.asarray(x) / hw + 1) / 2 * cols, (1 - np.asarray(y)) / 2 * rows


def to_screen(col, row, cols, rows, cell_aspect):
    """칸 좌표 (칸 가운데는 +0.5) → 화면 좌표."""
    hw = half_width(cols, rows, cell_aspect)
    return (np.asarray(col) / cols * 2 - 1) * hw, 1 - np.asarray(row) / rows * 2


# ---------- 부호 거리 (안쪽 음수) ----------
def circle2(X, Y, cx, cy, r):
    return np.hypot(X - cx, Y - cy) - r


def ellipse2(X, Y, cx, cy, rx, ry, angle=0.0):
    """타원 (근사 거리: 짧은 반지름 기준으로 맞춤). angle 은 라디안, 반시계."""
    c, s = math.cos(angle), math.sin(angle)
    dx, dy = X - cx, Y - cy
    u, v = dx * c + dy * s, -dx * s + dy * c
    k = np.hypot(u / rx, v / ry)
    return (k - 1) * min(rx, ry)


def seg_dist(X, Y, a, b):
    """선분 a–b 까지 거리와 선분 위 위치 h (0..1)."""
    ax, ay = a
    bx, by = b
    px, py, ex, ey = X - ax, Y - ay, bx - ax, by - ay
    h = np.clip((px * ex + py * ey) / max(ex * ex + ey * ey, 1e-12), 0, 1)
    return np.hypot(px - ex * h, py - ey * h), h


def capsule2(X, Y, a, b, r, r_end=None):
    """두께 r 인 막대 a–b. r_end 를 주면 a 쪽 r 에서 b 쪽 r_end 로 가늘어진다."""
    d, h = seg_dist(X, Y, a, b)
    return d - (r if r_end is None else r + (r_end - r) * h)


def polygon2(X, Y, pts):
    """다각형 (꼭짓점 목록, 순서 무관한 방향). iq sdPolygon."""
    pts = np.asarray(pts, np.float64)
    d = np.full(np.shape(X), np.inf)
    s = np.ones(np.shape(X))
    n = len(pts)
    for i in range(n):
        a, b = pts[i - 1], pts[i]
        dd, _ = seg_dist(X, Y, a, b)
        d = np.minimum(d, dd)
        c1 = Y >= a[1]
        c2 = Y < b[1]
        c3 = (b[0] - a[0]) * (Y - a[1]) > (b[1] - a[1]) * (X - a[0])
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * d


def star2(X, Y, cx, cy, r, inner=0.45, points=5, angle=0.0):
    """별 (바깥 반지름 r, 안쪽 반지름 r·inner). angle 0 이면 꼭짓점 하나가 위를 향한다."""
    k = np.arange(points * 2)
    a = math.pi / 2 + angle + k * math.pi / points
    rr = np.where(k % 2 == 0, r, r * inner)
    return polygon2(X, Y, np.stack([cx + rr * np.cos(a), cy + rr * np.sin(a)], -1))


def union2(*ds):
    return np.minimum.reduce(ds)


# ---------- 칸으로 ----------
def coverage(d, ss):
    """슈퍼샘플 부호 거리 (rows*ss, cols*ss) → 칸마다 안쪽 비율 0..1."""
    return downsample((np.asarray(d) < 0).astype(np.float64), ss)


def line_glyph(dx, dy):
    """화면 위 방향 (오른쪽 +x, 위 +y, 같은 단위) → - / | \\ 글자."""
    ang = math.degrees(math.atan2(dy, dx)) % 180.0
    return "-/|\\"[int(round(ang / 45.0)) % 4]


def draw_line2(grid, a, b, cell_aspect, char, color, density=2.0, mask=None):
    """화면 좌표 선분 a–b 를 칸에 찍는다. char=None 이면 방향 글자. 찍은 칸 mask(bool) 를 돌려준다.

    mask 를 주면 그 배열에 찍은 칸을 표시해 같이 돌려준다 (여러 선을 모을 때).
    """
    cols, rows = grid.cols, grid.rows
    ca, ra = to_cell(a[0], a[1], cols, rows, cell_aspect)
    cb, rb = to_cell(b[0], b[1], cols, rows, cell_aspect)
    n = int(max(2, math.ceil(max(abs(cb - ca), abs(rb - ra)) * density)))
    s = np.linspace(0, 1, n)
    x = np.floor(ca + (cb - ca) * s).astype(np.int64)
    y = np.floor(ra + (rb - ra) * s).astype(np.int64)
    ok = (x >= 0) & (y >= 0) & (x < cols) & (y < rows)
    ch = char if char is not None else line_glyph(b[0] - a[0], b[1] - a[1])
    out = np.zeros((rows, cols), bool) if mask is None else mask
    out[y[ok], x[ok]] = True
    sel = np.zeros((rows, cols), bool)
    sel[y[ok], x[ok]] = True
    grid.fill(sel, ch, color)
    return out


def draw_polyline2(grid, pts, cell_aspect, char, color, density=2.0):
    """꺾은선 (점 목록). 마디마다 방향 글자."""
    mask = np.zeros((grid.rows, grid.cols), bool)
    for a, b in zip(pts[:-1], pts[1:]):
        draw_line2(grid, a, b, cell_aspect, char, color, density, mask)
    return mask
