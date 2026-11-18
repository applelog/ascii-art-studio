"""F3 데모: 재생 창 확인용. 글자 물결이 4초마다 한 바퀴 돈다.

    python examples/f3_demo.py               창에서 재생
    python examples/f3_demo.py --set WAVES=3 물결 수를 바꿔서 재생
"""
# ===== 설정: 여기 값만 바꾸면 아래 코드 전체가 따라 바뀝니다 =====
COLS, ROWS   = 96, 40                  # 글자 칸 수
FONT         = "Menlo"                 # 글꼴
FONT_PX      = 16                      # 글자 크기 px
CELL_ASPECT  = 0.6                     # 칸 너비/높이
BACKGROUND   = (10, 10, 14)            # 바탕색
PALETTE      = [(60, 90, 170), (120, 190, 255), (240, 250, 255)]  # 어두움 → 밝음
TEXT_RGB     = (150, 150, 160)         # 글씨 색
RAMP         = " .:-=+*#%@"            # 밝기 순 글자
LOOP_SECONDS = 4                       # 한 루프 길이 (초)
FPS          = 30                      # 12 | 24 | 30 | 60
LOOP         = True                    # 끝과 처음이 이어짐
WAVES        = 2                       # 한 루프 동안 물결이 지나가는 횟수 (정수)
WAVELENGTH   = 32                      # 물결 한 개의 가로 길이 (칸)
AMPLITUDE    = 9                       # 물결 높이 (칸)
THICKNESS    = 3.5                     # 물결 두께 (칸)
TEXT_ROW     = 2                       # 안내 글씨 줄
RANGES       = {"WAVES": (1, 8), "AMPLITUDE": (0, 18), "THICKNESS": (0.5, 10), "WAVELENGTH": (4, 200)}
# ===== 코드 =====
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from asciiart.run import run  # noqa: E402


def setup():
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    codes = np.array([0 if c == " " else ord(c) for c in RAMP], np.uint32)
    return {"xx": xx, "yy": yy, "codes": codes, "pal": np.array(PALETTE, float)}


def frame(s, t, phase, grid):
    """phase 0→1 동안 물결이 WAVES 번 지나간다 (정수라서 끝과 처음이 이어짐)."""
    xx, yy = s["xx"], s["yy"]
    center = ROWS / 2 + AMPLITUDE * np.sin(2 * np.pi * (xx / WAVELENGTH - round(WAVES) * phase))
    lum = np.exp(-((yy - center) / THICKNESS) ** 2)
    idx = np.clip(np.round(lum * (len(RAMP) - 1)), 0, len(RAMP) - 1).astype(int)
    pal = s["pal"]
    k = lum * (len(pal) - 1)
    i = np.clip(np.floor(k).astype(int), 0, len(pal) - 2)
    f = (k - i)[..., None]
    rgb = (pal[i] * (1 - f) + pal[i + 1] * f).round().astype(np.uint8)
    codes = s["codes"][idx]
    grid.fill(codes != 0, codes, rgb)
    grid.text(TEXT_ROW, TEXT_ROW, "F3 PLAYER  t=%.2fs  phase=%.3f" % (t, phase), TEXT_RGB)


if __name__ == "__main__":
    run(globals())
