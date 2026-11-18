"""F4 데모: 밝기 → 글자 방식 비교. 위에서부터
   1) 디더 없음 (띠가 생김)  2) 칸마다 디더 (hash)  3) 바둑판 디더 (bayer)
   4) 긴 램프 + 감마  5) 글자 풀 + 반짝임  6) 밝기 채움 + 윤곽 방향 글자

    python examples/f4_demo.py              창에서 재생 (5번 띠가 반짝임)
    python examples/f4_demo.py --stage 1    out/stage1.png 로 저장
"""
# ===== 설정: 여기 값만 바꾸면 아래 코드 전체가 따라 바뀝니다 =====
COLS, ROWS    = 120, 61                 # 글자 칸 수
FONT          = "Menlo"                 # 글꼴
FONT_PX       = 14                      # 글자 크기 px
CELL_ASPECT   = 0.6                     # 칸 너비/높이
BACKGROUND    = (10, 10, 14)            # 바탕색
PALETTE       = [(70, 80, 110), (150, 175, 230), (245, 248, 255)]  # 어두움 → 밝음
LABEL_RGB     = (140, 140, 150)         # 설명 글씨 색
EDGE_RGB      = (255, 200, 120)         # 윤곽 글자 색
MIN_COLOR     = 0.3                     # 글자 색 밝기 하한
LOOP_SECONDS  = 4                       # 한 루프 길이 (초)
FPS           = 30                      # 12 | 24 | 30 | 60
LOOP          = True                    # 끝과 처음이 이어짐
TOP           = 1                       # 첫 띠가 시작하는 줄
BAND_ROWS     = 5                       # 띠 하나의 높이 (줄)
BAND_GAP      = 2                       # 띠 사이 간격 (줄)
LABEL_COLS    = 26                      # 왼쪽 설명 칸 너비
DITHER        = 1.0                     # 디더 폭 (램프 단계)
GAMMA         = 0.72                    # 4번 띠 감마 (eyeTutorial 값)
SHIMMER_STEPS = 12                      # 한 루프 동안 반짝임이 바뀌는 횟수 (정수)
DISC_R        = 10                      # 6번 원 반지름 (줄)
DISC_SOFT     = 1                       # 6번 원 테두리 부드러움 (줄)
DISC_LIGHT    = (-0.45, -0.55)          # 6번 원에 빛이 오는 방향 (가로, 세로, 화면 기준)
EDGE_MIN      = 0.2                     # 이보다 센 경계에 윤곽 글자 (가장 센 경계 대비)
SEED          = 3                       # 디더·반짝임 seed
RANGES        = {"SHIMMER_STEPS": (1, 60), "DITHER": (0, 2), "GAMMA": (0.2, 3)}
# ===== 코드 =====
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from asciiart.color import palette_color  # noqa: E402
from asciiart.ramp import GLYPH_POOLS, RAMPS, edge_chars, edges, pool_chars, ramp_chars, thin_edges  # noqa: E402
from asciiart.run import run  # noqa: E402


def setup():
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    grad = np.clip((xx - LABEL_COLS) / float(COLS - LABEL_COLS - 1), 0, 1)   # 왼→오 0..1
    return {"xx": xx, "yy": yy, "grad": grad}


def band_rows(k):
    top = TOP + k * (BAND_ROWS + BAND_GAP)
    return top, top + BAND_ROWS


def frame(s, t, phase, grid):
    xx, yy, grad = s["xx"], s["yy"], s["grad"]
    step = int(phase * SHIMMER_STEPS) % SHIMMER_STEPS
    common = {"xx": xx, "yy": yy, "seed": SEED}
    bands = [
        ("1 no dither", ramp_chars(grad, RAMPS["short"], **common)),
        ("2 dither: hash", ramp_chars(grad, RAMPS["short"], dither=DITHER, **common)),
        ("3 dither: bayer", ramp_chars(grad, RAMPS["short"], dither=DITHER, mode="bayer", **common)),
        ("4 long ramp + gamma", ramp_chars(grad, RAMPS["long"], gamma=GAMMA, dither=DITHER, **common)),
        ("5 glyph pools + shimmer", pool_chars(grad, GLYPH_POOLS, dither=DITHER, step=step, **common)),
    ]
    color = palette_color(grad, PALETTE, MIN_COLOR)
    for k, (label, codes) in enumerate(bands):
        r0, r1 = band_rows(k)
        mask = (yy >= r0) & (yy < r1) & (xx >= LABEL_COLS) & (codes != 0)
        grid.fill(mask, codes, color)
        grid.text(1, r0 + BAND_ROWS // 2, label, LABEL_RGB)

    # 6) 밝은 원: 안쪽은 밝기 글자, 경계는 방향 글자
    r0, _ = band_rows(len(bands))
    cy, cx = r0 + DISC_R + 1, LABEL_COLS + (COLS - LABEL_COLS) // 2
    dx, dy = (xx - cx) * CELL_ASPECT / DISC_R, (yy - cy) / DISC_R      # 원 안 좌표 −1..1
    cover = np.clip((DISC_R - np.hypot(dx, dy) * DISC_R) / DISC_SOFT + 0.5, 0, 1)
    nz = np.sqrt(np.clip(1 - dx ** 2 - dy ** 2, 0, 1))                 # 공 표면의 앞쪽 성분
    lx, ly = DISC_LIGHT
    lz = np.sqrt(max(0, 1 - lx ** 2 - ly ** 2))                     # 빛의 화면 앞쪽 성분
    shade = np.clip(dx * lx + dy * ly + nz * lz, 0, 1)               # 램버트 음영 (법선 · 빛)
    lum = shade * cover
    fill = ramp_chars(lum, RAMPS["short"], dither=DITHER, **common)
    grid.fill(fill != 0, fill, palette_color(lum, PALETTE, MIN_COLOR))
    mag, gx, gy = edges(cover, CELL_ASPECT)
    edge = thin_edges(mag, gx, gy, EDGE_MIN * mag.max())
    grid.fill(edge, edge_chars(gx, gy), EDGE_RGB)
    grid.text(1, cy, "6 fill + edge glyphs", LABEL_RGB)


if __name__ == "__main__":
    run(globals())
