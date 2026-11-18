"""<제목> — <한 줄 설명>

요청: "<사용자 원문>"
설명: brief.md   용어: GLOSSARY.md
단계: ① scene (완성 화면) → ② intro (등장) → ③ motion (모션)

    python piece.py                     창: 등장 한 번 → 모션 반복 (R: 등장부터 다시)
    python piece.py --stage 1           ① 완성 화면 PNG
    python piece.py --stage 2           ② 등장 MP4 + 프레임 띠
    python piece.py --stage 3           ③ 모션 MP4 + 프레임 띠
    python piece.py --final             최종 MP4 + 대표 그림
    python piece.py --check             단계 연결 검사 (① = ② 끝 = ③ 처음 = ③ 끝)
"""
# ===== ① 장면 설정: 여기 값만 바꾸면 아래 코드 전체가 따라 바뀝니다 =====
COLS           = 120                    # 가로 글자 칸 수 (16~400)
ROWS           = 60                     # 세로 글자 칸 수 (8~240)
FONT           = "Menlo"                # 글꼴 이름 또는 .ttf/.ttc 경로 — Menlo 에는 한글이 없음
FONT_PX        = 14                     # 글자 크기 px (6~48)
CELL_ASPECT    = 0.6                    # 칸 너비/높이 (0.35~1.2)
BACKGROUND     = (8, 8, 14)             # 바탕색 (RGB 0~255)
SUPERSAMPLE    = 2                      # 칸 하나를 몇×몇 점으로 계산 (1~3)
SUBJECT_X      = 0.0                    # 주제 가로 위치, 가운데 0 (화면 좌표)
SUBJECT_Y      = 0.0                    # 주제 세로 위치 (−1 아래 … 1 위)
SUBJECT_R      = 0.55                   # 주제 크기, 화면 높이 절반 = 1 (0.05~3)
SUBJECT_RGB    = (240, 200, 140)        # 주제 색 (RGB 0~255)
LIGHT_X        = -0.5                   # 빛 방향 가로 (−1 왼쪽 … 1 오른쪽)
LIGHT_Y        = 0.5                    # 빛 방향 세로 (−1 아래 … 1 위)
AMBIENT        = 0.06                   # 그늘진 쪽 최소 밝기 (0~1)
RAMP           = " .:-=+*#%@"           # 밝기 순 글자 (첫 글자는 빈칸)
GAMMA          = 0.8                    # 밝기 감마 — 1 보다 작으면 어두운 글자가 늘어남 (0.3~2)
CUT            = 0.04                   # 이보다 어두우면 빈칸 (0~1)
DITHER         = 1.0                    # 칸마다 고정 디더 폭 — 띠 무늬 제거 (0~2)
MIN_COLOR      = 0.3                    # 글자 색 밝기 하한 (0~1)
# ===== ② 등장 설정 =====
INTRO_SECONDS  = 2.0                    # 등장 길이 (초)
INTRO_HOLD     = 1.0                    # 등장 검토 영상 끝에 완성 화면을 보여 주는 시간 (초)
REVEAL_SOFT    = 0.15                   # 등장 경계의 흔들림 (0~0.5)
# ===== ③ 모션 설정 =====
LOOP_SECONDS   = 4                      # 한 루프 길이 (초)
FPS            = 30                     # 초당 프레임 (12 | 24 | 30 | 60)
LOOP           = True                   # 모션 반복
PULSES         = 1                      # 한 루프 동안 맥박 횟수 (정수, 1~12)
PULSE          = 0.05                   # 맥박 크기 (크기 비율, 0~0.5)
# ===== 최종 출력 =====
FINAL_LOOPS    = 2                      # 최종 영상에서 모션 반복 횟수 (1~20)
# ===== 효과 =====
TRAIL          = 0.0                    # 잔상 (0~0.97)
GLOW           = 0.3                    # 글로우 (0~1)
GLOW_RADIUS    = 0.8                    # 글로우 번짐 (칸 높이 배수)
SEED           = 1                      # 디더·무작위 seed
RANGES         = {"SUPERSAMPLE": (1, 3), "PULSES": (1, 12), "PULSE": (0, 0.5), "REVEAL_SOFT": (0, 0.5)}
# ===== 코드 =====
import math
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(_d, "asciiart")) and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np  # noqa: E402

from asciiart.color import rgb01  # noqa: E402
from asciiart.grid import Grid  # noqa: E402
from asciiart.ramp import cell_hash  # noqa: E402
from asciiart.run import run  # noqa: E402
from asciiart.shade import field_to_grid, shade  # noqa: E402


def setup():
    """한 번만 계산: 등장 순서 같은 고정 값. 난수는 SEED 로만."""
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    dist = np.hypot((xx - COLS / 2) * CELL_ASPECT, yy - ROWS / 2)
    dist = dist / dist.max()
    order = np.clip(dist * (1 - REVEAL_SOFT) + cell_hash(xx, yy, SEED) * REVEAL_SOFT, 0, 1)
    return {"order": order}


def draw(s, phase, grid):
    """그림 하나를 phase(0..1) 로 그린다. 모든 시간 변화는 phase 의 정수 주기 → phase 0 과 1 이 같다."""
    size = SUBJECT_R * (1 + PULSE * math.sin(2 * math.pi * round(PULSES) * phase))
    lz = math.sqrt(max(0.0, 1 - LIGHT_X ** 2 - LIGHT_Y ** 2))

    def light(X, Y):
        nx, ny = (X - SUBJECT_X) / size, (Y - SUBJECT_Y) / size
        d2 = nx ** 2 + ny ** 2
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        lum = np.clip(nx * LIGHT_X + ny * LIGHT_Y + nz * lz, 0, 1) * (1 - AMBIENT) + AMBIENT
        return (lum * (d2 < 1))[..., None] * rgb01(SUBJECT_RGB)

    rgb = shade(light, COLS, ROWS, CELL_ASPECT, SUPERSAMPLE)
    field_to_grid(rgb, grid, RAMP, cut=CUT, gamma=GAMMA, dither=DITHER, seed=SEED, min_color=MIN_COLOR)


def scene(s, grid):
    """① 완성 화면 = 모션의 처음."""
    draw(s, 0.0, grid)


def intro(s, p, grid):
    """② 가운데에서 바깥으로 퍼지며 나타난다. p=1 이면 scene 그대로."""
    final = Grid(COLS, ROWS)
    scene(s, final)
    show = (s["order"] < p) | (p >= 1)
    grid.ch[show], grid.rgb[show] = final.ch[show], final.rgb[show]


def motion(s, t, phase, grid):
    """③ PULSES 번 맥박치듯 커졌다 작아진다."""
    draw(s, phase, grid)


if __name__ == "__main__":
    run(globals())
