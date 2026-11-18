"""F2 데모: grid 에 글자와 색을 채워 PNG 한 장으로 저장한다.

    python examples/f2_demo.py            → out/f2_demo.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== 설정 =====
COLS, ROWS  = 96, 40
FONT        = "Menlo"
FONT_PX     = 16
CELL_ASPECT = 0.6
BACKGROUND  = (12, 12, 14)
RAMP        = " .:-=+*#%@"
POOLS       = [".,'`-", ":;~^\"", "=+<>ivc*", "#%@MWN"]  # 글자 풀 (어두움→밝음, asciiart.ramp.GLYPH_POOLS 와 같음)
OUT         = "out/f2_demo.png"
# ===== 코드 =====
import numpy as np  # noqa: E402

from asciiart.atlas import GlyphAtlas, save_png  # noqa: E402
from asciiart.grid import Grid  # noqa: E402

g = Grid(COLS, ROWS)
white, dim = (235, 235, 235), (120, 120, 125)

g.text(2, 1, "F2  GRID -> IMAGE -> PNG", white)
g.text(2, 2, "%dx%d cells, %s %dpx" % (COLS, ROWS, FONT, FONT_PX), dim)

# 1) 밝기 램프 (아직 디더·감마 없음 — F4 에서 추가)
g.text(2, 4, "ramp:", dim)
for i, c in enumerate(RAMP):
    v = int(60 + 195 * i / (len(RAMP) - 1))
    g.put(10 + i * 2, 4, c, (v, v, v))

# 2) 셀마다 다른 색 (가로 색상 그라데이션)
g.text(2, 6, "color:", dim)
for x in range(COLS - 12):
    t = x / (COLS - 13)
    r = int(255 * max(0, 1 - abs(t * 3 - 0.5)))
    gg = int(255 * max(0, 1 - abs(t * 3 - 1.5)))
    b = int(255 * max(0, 1 - abs(t * 3 - 2.5)))
    g.put(10 + x, 6, "#", (max(r, 40), max(gg, 40), max(b, 40)))

# 3) 글자 풀 4단계
g.text(2, 8, "pools:", dim)
x = 10
for k, pool in enumerate(POOLS):
    v = 90 + 55 * k
    g.text(x, 8, pool, (v, v, 255))
    x += len(pool) + 3

# 4) numpy 로 한 번에 채운 원 (거리 → 램프 단계)
cy, cx, R = 24, 30, 13
yy, xx = np.mgrid[0:ROWS, 0:COLS]
d = np.hypot((xx - cx) * CELL_ASPECT, yy - cy) / R  # 셀 비율을 보정해야 원이 둥글다
inside = d < 1
level = np.clip(((1 - d) * (len(RAMP) - 1)).round().astype(int), 0, len(RAMP) - 1)
codes = np.array([ord(c) for c in RAMP], np.uint32)[level]
color = np.zeros((ROWS, COLS, 3), np.uint8)
color[..., 0] = np.clip(255 * (1 - d * 0.5), 0, 255)
color[..., 1] = np.clip(80 * (1 - d), 0, 255)
color[..., 2] = 60
g.fill(inside & (codes != 32), codes, color)
g.text(cx - 6, cy + 14, "numpy fill", dim)

# 5) 깊이(put_z): 뒤에 놓인 글자가 앞 글자를 덮지 않는다
for i in range(30):
    g.put_z(60 + i, 20, 5.0, "-", (80, 80, 200))
for i in range(30):
    g.put_z(60 + i, 20, 2.0 if i % 3 == 0 else 9.0, "O", (255, 220, 120))
g.text(60, 22, "put_z: O near(z=2) / far(z=9)", dim)

atlas = GlyphAtlas(FONT, FONT_PX, CELL_ASPECT)
img = atlas.render(g, BACKGROUND)
save_png(img, OUT)
print("saved", OUT, img.shape[1], "x", img.shape[0], "px")
