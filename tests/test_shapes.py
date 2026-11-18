"""2D 도형 (asciiart/shapes.py) 과 3D 잘린 원뿔 (three.capped_cone)."""
import numpy as np

from asciiart import shapes as S
from asciiart import three as T
from asciiart.grid import Grid
from asciiart.shade import coords


def test_cell_screen_roundtrip():
    c, r = S.to_cell(0.1, -0.3, 90, 100, 0.6)
    x, y = S.to_screen(c, r, 90, 100, 0.6)
    assert abs(x - 0.1) < 1e-12 and abs(y + 0.3) < 1e-12


def test_signs():
    X, Y = np.array([0.0, 2.0]), np.array([0.0, 0.0])
    assert (S.circle2(X, Y, 0, 0, 1) < 0).tolist() == [True, False]
    assert (S.ellipse2(X, Y, 0, 0, 1, 0.5) < 0).tolist() == [True, False]
    assert (S.capsule2(X, Y, (-1, 0), (1, 0), 0.1) < 0).tolist() == [True, False]
    sq = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    d = S.polygon2(X, Y, sq)
    assert d[0] < 0 and abs(d[0] + 1) < 1e-9 and abs(d[1] - 1) < 1e-9
    assert (S.polygon2(X, Y, sq[::-1]) < 0).tolist() == [True, False]
    assert S.star2(np.array([0.0]), np.array([0.0]), 0, 0, 1)[0] < 0
    # 별의 위 꼭짓점 바로 아래는 안쪽, 꼭짓점 사이 바깥 반지름 근처는 바깥
    assert S.star2(np.array([0.0]), np.array([0.9]), 0, 0, 1)[0] < 0
    assert S.star2(np.array([0.0]), np.array([-0.9]), 0, 0, 1)[0] > 0


def test_tapered_capsule():
    X, Y = np.array([-1.0, 1.0]), np.array([0.15, 0.15])
    d = S.capsule2(X, Y, (-1, 0), (1, 0), 0.2, 0.1)
    assert d[0] < 0 < d[1]


def test_coverage_area():
    X, Y = coords(60, 60, 1.0, 3)
    cov = S.coverage(S.circle2(X, Y, 0, 0, 0.5), 3)
    assert cov.shape == (60, 60)
    area = cov.sum() / (60 * 60) * 4                 # 화면 넓이 2×2
    assert abs(area - np.pi * 0.25) < 0.03


def test_draw_line_glyphs():
    g = Grid(40, 40)
    S.draw_line2(g, (-0.8, 0.0), (0.8, 0.0), 1.0, None, (255, 255, 255))
    assert set(g.to_text().replace(" ", "").replace("\n", "")) == {"-"}
    g = Grid(40, 40)
    m = S.draw_line2(g, (-0.5, -0.5), (0.5, 0.5), 1.0, None, (255, 0, 0))
    assert set(g.to_text().replace(" ", "").replace("\n", "")) == {"/"} and m.sum() >= 15
    assert S.line_glyph(0, 1) == "|" and S.line_glyph(1, -1) == "\\"
    g = Grid(40, 40)
    S.draw_polyline2(g, [(-0.5, 0), (0, 0.5), (0.5, 0)], 1.0, None, (0, 255, 0))
    t = g.to_text()
    assert "/" in t and "\\" in t


def test_capped_cone():
    p = np.array([[0, 0, 0], [0, 2, 0], [0.9, -0.95, 0], [3, 0, 0]], np.float64)
    d = T.capped_cone(p, 1.0, 1.0, 0.0)
    assert d[0] < 0 and d[2] < 0 and d[1] > 0.9 and d[3] > 2
    # 바닥 아래 정확한 거리
    assert abs(T.capped_cone(np.array([[0, -1.5, 0]]), 1.0, 1.0, 0.0)[0] - 0.5) < 1e-9
