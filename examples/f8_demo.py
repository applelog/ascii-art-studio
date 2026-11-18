"""F8 데모: 이미지 입력 — 그림(고양이)을 필드로 바꿔 글자로 그린다. 단계 구조.

    ① 실루엣: 털 밝기 → 글자, 원래 색 → 글자 색, 바깥선 → 방향 글자
    ② 등장: 윤곽선이 둘레를 따라 한 바퀴 그려진 뒤, 안쪽이 바깥에서 가운데로 채워짐
    ③ 모션: 앉은 자리를 기준으로 숨 쉬듯 커졌다 작아지고, 털 글자가 반짝임

필드 만들기 (원본 이미지는 작품 폴더에 넣지 않고, 줄인 필드만 씀):
    python tools/image_to_field.py examples/assets/cat.png --out examples/assets/cat_field.json \\
           --cols 120 --rows 60 --ss 2 --cell-aspect 0.6

    python examples/f8_demo.py                  창: 등장 → 모션 반복
    python examples/f8_demo.py --stage 1        ① 완성 화면 PNG
"""
# ===== ① 장면 설정 =====
COLS, ROWS     = 120, 60                # 글자 칸 수
FONT           = "Menlo"                # 글꼴
FONT_PX        = 14                     # 글자 크기 px
CELL_ASPECT    = 0.6                    # 칸 너비/높이
BACKGROUND     = (12, 10, 18)           # 바탕색
FIELD          = "assets/cat_field.json"  # 이미지 필드 (이 파일 기준 상대 경로)
FIT            = "contain"              # "contain" 다 보이게 | "cover" 꽉 차게
SCALE          = 0.95                   # 이미지 크기 배수
CENTER_X       = 0.5                    # 이미지 중심 가로 위치 (0..1)
CENTER_Y       = 0.5                    # 이미지 중심 세로 위치 (0..1)
RAMP           = " .:-=+*#%@"           # 밝기 순 글자
BRIGHTNESS     = "lum"                  # "lum" | "inverse" | "alpha"
COLOR          = "original"             # "original" | "palette" | (r, g, b)
GAMMA          = 0.8                    # 밝기 감마
CUT            = 0.04                   # 이보다 어두우면 빈칸
ALPHA_CUT      = 0.5                    # 피사체로 볼 투명도 기준
MIN_COLOR      = 0.4                    # 글자 색 밝기 하한
EDGE_CUT       = 0.45                   # 이보다 센 윤곽에 방향 글자
EDGE_RGB       = (255, 228, 190)        # 윤곽 글자 색
# ===== ② 등장 설정 =====
INTRO_SECONDS  = 3.0                    # 등장 길이 (초)
INTRO_HOLD     = 1.0                    # 등장 검토 영상 끝에 완성 화면을 보여 주는 시간 (초)
OUTLINE_PART   = 0.45                   # 등장 중 윤곽선을 그리는 비율 (나머지는 안쪽 채우기)
OUTLINE_START  = -0.25                  # 윤곽선이 시작하는 각도 (바퀴 단위, 0 = 오른쪽, −0.25 = 위)
FILL_SOFT      = 0.08                   # 채우기 경계의 흔들림 (칸마다 조금씩 앞뒤로)
# ===== ③ 모션 설정 =====
LOOP_SECONDS   = 4                      # 한 루프 길이 (초)
FPS            = 30                     # 12 | 24 | 30 | 60
LOOP           = True                   # 모션 반복
BREATHS        = 1                      # 한 루프 동안 숨 쉬는 횟수 (정수)
BREATH         = 0.025                  # 숨 쉴 때 커지는 정도 (크기 비율)
SHIMMER        = 0.6                    # 털 글자 반짝임 세기 (램프 단계)
SHIMMER_STEPS  = 8                      # 한 루프 동안 반짝임이 바뀌는 횟수 (정수)
# ===== 최종 출력 =====
FINAL_LOOPS    = 2                      # 최종 영상에서 모션 반복 횟수
# ===== 효과 =====
GLOW           = 0.35                   # 글로우 0~1
GLOW_RADIUS    = 0.8                    # 글로우 번짐 (칸 높이 배수)
SEED           = 4                      # 디더·반짝임 seed
RANGES         = {"SCALE": (0.2, 3), "BREATH": (0, 0.2), "BREATHS": (1, 8), "SHIMMER": (0, 3),
                  "SHIMMER_STEPS": (1, 60), "OUTLINE_PART": (0.05, 0.95), "EDGE_CUT": (0, 1)}
# ===== 코드 =====
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from asciiart.field import ImageField, Placement, draw_field  # noqa: E402
from asciiart.grid import Grid  # noqa: E402
from asciiart.ramp import cell_hash  # noqa: E402
from asciiart.run import run  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def placement(field, breath):
    """앉은 자리(이미지 아래쪽)는 그대로 두고 크기만 breath 배로."""
    base = Placement(field, COLS, ROWS, CELL_ASPECT, FIT, SCALE, CENTER_X, CENTER_Y)
    bottom = base.top + base.h
    p = Placement(field, COLS, ROWS, CELL_ASPECT, FIT, SCALE * breath, CENTER_X, CENTER_Y)
    p.top = bottom - p.h
    return p


def draw(s, phase, grid):
    breath = 1 + BREATH * math.sin(2 * math.pi * round(BREATHS) * phase)
    u, v = placement(s["field"], breath).cells()
    step = int(phase * SHIMMER_STEPS) % SHIMMER_STEPS
    return draw_field(grid, s["field"], u, v, RAMP, BRIGHTNESS, ALPHA_CUT, CUT, GAMMA, 1.0, SEED, COLOR, MIN_COLOR,
                      EDGE_CUT, EDGE_RGB, CELL_ASPECT, SHIMMER, step)


def setup():
    field = ImageField.load(os.path.join(HERE, FIELD))
    s = {"field": field}
    # ② 등장 순서: 윤곽선은 둘레 각도 순, 안쪽은 바깥선에서의 거리 순 (가까운 곳부터)
    g = Grid(COLS, ROWS)
    inside, edge = draw(s, 0.0, g)
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    ys, xs = np.nonzero(inside | edge)
    cy, cx = ys.mean(), xs.mean()
    ang = (np.arctan2((yy - cy), (xx - cx) * CELL_ASPECT) / (2 * math.pi) - OUTLINE_START) % 1.0
    dist = cv2.distanceTransform((inside & ~edge).astype(np.uint8), cv2.DIST_L2, 3)
    dist = dist / max(dist.max(), 1e-6)
    fill = np.clip(dist + (cell_hash(xx, yy, SEED) - 0.5) * FILL_SOFT, 0, 1) * (1 - FILL_SOFT)
    s.update(edge_cells=edge, edge_order=ang, fill_order=fill)
    return s


def scene(s, grid):
    """① 완성 화면 = 모션의 처음."""
    draw(s, 0.0, grid)


def intro(s, p, grid):
    """② 윤곽선이 둘레를 따라 그려진 뒤 안쪽이 바깥에서 가운데로 채워진다. p=1 이면 scene 그대로."""
    final = Grid(COLS, ROWS)
    scene(s, final)
    if p >= 1:
        grid.ch[...], grid.rgb[...] = final.ch, final.rgb
        return
    edge = s["edge_cells"]
    show_edge = edge & (s["edge_order"] <= p / OUTLINE_PART)
    fill_p = (p - OUTLINE_PART) / (1 - OUTLINE_PART)
    show_fill = ~edge & (s["fill_order"] < fill_p)
    show = (show_edge | show_fill) & (final.ch != 0)
    grid.ch[show], grid.rgb[show] = final.ch[show], final.rgb[show]


def motion(s, t, phase, grid):
    """③ 숨쉬기 + 털 반짝임."""
    draw(s, phase, grid)


if __name__ == "__main__":
    run(globals())
