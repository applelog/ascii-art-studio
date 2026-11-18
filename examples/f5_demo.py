"""F5 데모: 필드 렌더로 그린 빛나는 원 (태양 같은 구).

화면의 모든 점에서 색을 계산(슈퍼샘플링) → 블룸 · 톤매핑 · 비네트 → 밝기로 글자, 색으로 글자 색.
4초마다 코로나(바깥 빛)가 한 번 숨 쉬듯 커졌다 작아진다.

    python examples/f5_demo.py                           창에서 재생
    python examples/f5_demo.py --stage 1                 out/stage1.png
    python examples/f5_demo.py --stage 1 --set BLOOM=0 --set EXPOSURE=0 --set VIGNETTE=0   후처리 끄고 비교
"""
# ===== 설정: 여기 값만 바꾸면 아래 코드 전체가 따라 바뀝니다 =====
# --- 화면 ---
COLS, ROWS     = 120, 60                # 글자 칸 수
FONT           = "Menlo"                # 글꼴
FONT_PX        = 14                     # 글자 크기 px
CELL_ASPECT    = 0.6                    # 칸 너비/높이
BACKGROUND     = (4, 4, 10)             # 바탕색
SUPERSAMPLE    = 2                      # 칸 하나를 몇×몇 점으로 계산할지 (1~3)
# --- 구 ---
ORB_X, ORB_Y   = 0.0, 0.0               # 구 중심 (화면 좌표, 세로 −1..1)
ORB_R          = 0.42                   # 구 반지름 (화면 높이 절반 = 1)
ORB_RGB        = (255, 196, 120)        # 구 표면 색
INTENSITY      = 1.8                    # 구 밝기 (1 넘으면 톤매핑이 눌러 줌)
LIMB           = 0.55                   # 가장자리가 어두워지는 정도 0~1
# --- 코로나 (바깥 빛) ---
CORONA_RGB     = (255, 110, 50)         # 코로나 색
CORONA         = 0.6                    # 코로나 밝기
CORONA_SIZE    = 0.07                   # 코로나 퍼짐 (화면 높이 절반 기준)
PULSE          = 0.25                   # 코로나 숨쉬기 세기 0~1
PULSES         = 1                      # 한 루프 동안 숨쉬기 횟수 (정수)
# --- 배경 ---
SKY_TOP_RGB    = (20, 24, 60)           # 위쪽 하늘 색
SKY_BOTTOM_RGB = (60, 30, 40)           # 아래쪽 하늘 색
SKY            = 0.07                   # 배경 밝기
# --- 후처리 ---
BLOOM          = 1.0                    # 블룸 세기 (0 이면 끔)
BLOOM_RADIUS   = 7.0                    # 블룸 번짐 (세로 칸)
BLOOM_THRESHOLD = 0.5                   # 이보다 밝은 부분만 번짐
EXPOSURE       = 1.6                    # 톤매핑 노출 (0 이면 끔)
WHITE          = 1.3                    # 이 밝기 이상이 가장 진한 글자가 됨 (톤매핑 흰색 기준)
VIGNETTE       = 0.5                    # 가장자리 어둡게 0~1
# --- 글자 ---
RAMP           = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"  # 70단계 (RAMPS long)
GAMMA          = 0.72                   # 밝기 감마
DITHER         = 1.0                    # 디더 폭
CUT            = 0.07                   # 이보다 어두우면 빈칸
COLOR_LEVELS   = 24                     # 글자 색 단계 (eyeTutorial QL)
MIN_COLOR      = 0.35                   # 글자 색 밝기 하한
# --- 시간 ---
LOOP_SECONDS   = 4                      # 한 루프 길이 (초)
FPS            = 30                     # 12 | 24 | 30 | 60
LOOP           = True                   # 끝과 처음이 이어짐
SEED           = 5                      # 디더 seed
RANGES         = {"SUPERSAMPLE": (1, 3), "LIMB": (0, 1), "PULSE": (0, 1), "PULSES": (1, 8),
                  "VIGNETTE": (0, 1), "BLOOM": (0, 3)}
# ===== 코드 =====
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from asciiart.post import bloom, tonemap, vignette  # noqa: E402
from asciiart.run import run  # noqa: E402
from asciiart.shade import field_to_grid, shade  # noqa: E402


def rgb01(c):
    return np.array(c, np.float64) / 255.0


def setup():
    return {}


def scene_light(phase):
    """phase → 화면 색을 계산하는 함수 fn(X, Y)."""
    breath = 1 + PULSE * np.sin(2 * np.pi * round(PULSES) * phase)

    def fn(X, Y):
        r = np.hypot(X - ORB_X, Y - ORB_Y) / ORB_R                    # 구 중심에서 거리 (반지름 = 1)
        inside = r < 1
        mu = np.sqrt(np.clip(1 - r ** 2, 0, 1))                        # 표면이 정면을 보는 정도
        surface = INTENSITY * (1 - LIMB * (1 - mu)) * inside
        outside = np.maximum(r - 1, 0) * ORB_R                         # 표면 밖 거리 (화면 단위)
        corona = CORONA * np.exp(-outside / (CORONA_SIZE * breath)) * ~inside
        t = (1 - Y) / 2                                                # 위 0 → 아래 1
        sky = SKY * ((1 - t)[..., None] * rgb01(SKY_TOP_RGB) + t[..., None] * rgb01(SKY_BOTTOM_RGB))
        return (surface[..., None] * rgb01(ORB_RGB) + corona[..., None] * rgb01(CORONA_RGB) + sky)

    return fn


def frame(state, t, phase, grid):
    rgb = shade(scene_light(phase), COLS, ROWS, CELL_ASPECT, SUPERSAMPLE)
    rgb = bloom(rgb, BLOOM, BLOOM_RADIUS, BLOOM_THRESHOLD, CELL_ASPECT)
    rgb = tonemap(rgb, EXPOSURE, white=WHITE)
    rgb = vignette(rgb, VIGNETTE, CELL_ASPECT)
    field_to_grid(rgb, grid, RAMP, cut=CUT, gamma=GAMMA, dither=DITHER, seed=SEED,
                  color_levels=COLOR_LEVELS, min_color=MIN_COLOR)


if __name__ == "__main__":
    run(globals())
