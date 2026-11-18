"""F6 데모: 시간 도구 — 흐르는 성운(루프 노이즈), 반짝이는 별, 별똥별(seed 일정표 + 잔상), 제목(막·오버슈트).

6초마다 정확히 같은 장면으로 돌아온다 (끝 프레임 다음이 처음 프레임과 이어짐).

    python examples/f6_demo.py                 창에서 재생
    python examples/f6_demo.py --stage 1       out/stage1.png
    python examples/f6_demo.py --set TRAIL=0   잔상 끄고 비교
"""
# ===== 설정: 여기 값만 바꾸면 아래 코드 전체가 따라 바뀝니다 =====
# --- 화면 ---
COLS, ROWS      = 120, 60               # 글자 칸 수
FONT            = "Menlo"               # 글꼴
FONT_PX         = 14                    # 글자 크기 px
CELL_ASPECT     = 0.6                   # 칸 너비/높이
BACKGROUND      = (3, 4, 12)            # 바탕색
# --- 시간 ---
LOOP_SECONDS    = 6                     # 한 루프 길이 (초)
FPS             = 30                    # 12 | 24 | 30 | 60
LOOP            = True                  # 끝과 처음이 이어짐
# --- 성운 (루프 노이즈) ---
NEBULA_SCALE    = 1.4                   # 성운 무늬 크기 (클수록 잘게)
NEBULA_FLOW     = 0.9                   # 한 루프 동안 성운이 변하는 정도
NEBULA_OCTAVES  = 4                     # 성운 노이즈 겹 수
NEBULA_BRIGHT   = 0.9                   # 성운 밝기
NEBULA_FLOOR    = 0.5                   # 노이즈가 이 값보다 낮은 곳은 성운 없음 (클수록 구름이 작음)
NEBULA_CONTRAST = 1.4                   # 성운 대비 (클수록 가운데만 진함)
NEBULA_A_RGB    = (150, 70, 220)        # 성운 색 1 (보라)
NEBULA_B_RGB    = (40, 170, 200)        # 성운 색 2 (청록)
NEBULA_MIX      = 0.8                   # 두 색이 섞이는 무늬 크기
NEBULA_RAMP     = " .:;+*%"             # 성운 글자 (어두움 → 밝음)
NEBULA_CUT      = 0.08                  # 이보다 어두운 성운은 비움
# --- 별 ---
STAR_COUNT      = 140                   # 별 개수
STAR_CHARS      = ".+*"                 # 별 글자 (어두움 → 밝음)
STAR_RGB        = (230, 235, 255)       # 별 색
TWINKLES        = 3                     # 한 루프 동안 반짝이는 횟수 (정수)
TWINKLE         = 0.7                   # 반짝임 세기 0~1
# --- 별똥별 (seed 일정표) ---
METEORS         = 5                     # 한 루프 동안 별똥별 수
METEOR_DUR      = (0.45, 0.8)           # 별똥별 하나가 지나가는 시간 (초, 최소~최대)
METEOR_GAP      = 0.7                   # 별똥별끼리 최소 간격 (초)
METEOR_LENGTH   = 0.55                  # 날아가는 거리 (화면 너비 비율)
METEOR_ANGLE    = (20, 40)              # 내려가는 각도 (도, 최소~최대)
METEOR_HEAD     = "*"                   # 별똥별 머리 글자
METEOR_RGB      = (255, 240, 200)       # 별똥별 색
METEOR_FADE     = 0.3                   # 마지막 이 비율 동안 사라짐 (0~1)
# --- 제목 (막: 등장 → 머무름 → 퇴장) ---
TITLE           = "F6  TIME TOOLS"      # 제목 글자
TITLE_RGB       = (255, 220, 150)       # 제목 색
TITLE_ROW       = 4                     # 제목이 머무는 줄
T_IN, T_IN_D    = 0.3, 0.9              # 등장 시작·길이 (초)
T_OUT, T_OUT_D  = 4.8, 0.8              # 퇴장 시작·길이 (초)
BOUNCE          = 2.2                   # 등장할 때 넘쳤다 돌아오는 정도 (오버슈트)
# --- 효과 ---
TRAIL           = 0.82                  # 잔상 0~0.97 (별똥별 꼬리)
GLOW            = 0.55                  # 글로우 0~1
GLOW_RADIUS     = 0.8                   # 글로우 번짐 (칸 높이 배수)
SEED            = 11                    # 난수 seed
RANGES          = {"NEBULA_OCTAVES": (1, 6), "TWINKLES": (1, 12), "METEORS": (0, 30), "TWINKLE": (0, 1)}
# ===== 코드 =====
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from asciiart.ease import ease_in, loop_sin, overshoot, segment  # noqa: E402
from asciiart.noise import loop_noise, noise2  # noqa: E402
from asciiart.ramp import codes_of, edge_chars, ramp_chars  # noqa: E402
from asciiart.run import run  # noqa: E402
from asciiart.schedule import active, make_schedule  # noqa: E402


def rgb(c):
    return np.array(c, np.float64)


def setup():
    rng = np.random.RandomState(SEED)
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    aspect_w = COLS * CELL_ASPECT / ROWS                      # 화면 가로/세로
    stars = [(rng.randint(0, COLS), rng.randint(0, ROWS), rng.uniform(0, 1), rng.uniform(0, 1))
             for _ in range(STAR_COUNT)]
    meteors = make_schedule(SEED + 1, METEORS, LOOP_SECONDS, METEOR_DUR, METEOR_GAP)
    mix = noise2(xx / COLS * aspect_w / NEBULA_MIX * 3, yy / ROWS / NEBULA_MIX * 3, SEED + 2)
    color = (1 - mix)[..., None] * rgb(NEBULA_A_RGB) + mix[..., None] * rgb(NEBULA_B_RGB)
    return {"xx": xx, "yy": yy, "u": xx / COLS * aspect_w, "v": yy / ROWS,
            "stars": stars, "meteors": meteors, "color": color}


def nebula(s, phase, grid):
    n = loop_noise(s["u"] * NEBULA_SCALE * 3, s["v"] * NEBULA_SCALE * 3, phase, NEBULA_FLOW,
                   octaves=NEBULA_OCTAVES, seed=SEED)
    lum = NEBULA_BRIGHT * np.clip((n - NEBULA_FLOOR) / (1 - NEBULA_FLOOR), 0, 1) ** NEBULA_CONTRAST
    codes = ramp_chars(lum, NEBULA_RAMP, cut=NEBULA_CUT, dither=1.0, xx=s["xx"], yy=s["yy"], seed=SEED)
    col = np.clip(s["color"] * (0.35 + 0.65 * np.clip(lum, 0, 1))[..., None], 0, 255).astype(np.uint8)
    grid.fill(codes != 0, codes, col)


def stars(s, phase, grid):
    for x, y, b, off in s["stars"]:
        tw = 1 - TWINKLE * (0.5 + 0.5 * loop_sin(phase, TWINKLES, off))
        k = min(len(STAR_CHARS) - 1, int(b * tw * len(STAR_CHARS)))
        grid.put(x, y, STAR_CHARS[k], tuple(int(c * (0.4 + 0.6 * tw)) for c in STAR_RGB))


def meteor_head(ev, p):
    """사건 진행도 p → 별똥별 머리 위치 (칸 높이 단위 x, y)."""
    r = ev["rand"]
    width = COLS * CELL_ASPECT                                           # 화면 너비 (칸 높이 단위)
    ang = math.radians(METEOR_ANGLE[0] + (METEOR_ANGLE[1] - METEOR_ANGLE[0]) * r[0])
    sx, sy = width * (0.25 + 0.7 * r[1]), ROWS * 0.6 * r[2]             # 시작점
    dist = METEOR_LENGTH * width * p
    return sx - dist * math.cos(ang), sy + dist * math.sin(ang), ang     # 왼쪽 아래로


def meteors(s, t, grid):
    """직전 프레임 위치부터 지금 위치까지 선을 그어, 빠르게 움직여도 꼬리가 끊기지 않게 한다."""
    dt = 1.0 / FPS
    for ev, p in active(s["meteors"], t, LOOP_SECONDS):
        p0 = max(0.0, p - dt / ev["dur"])
        x0, y0, ang = meteor_head(ev, p0)
        x1, y1, _ = meteor_head(ev, p)
        fade = 1 - segment(p, 1 - METEOR_FADE, 1)
        col = tuple(int(c * fade) for c in METEOR_RGB)
        line = int(edge_chars(np.array([[-math.sin(ang)]]), np.array([[-math.cos(ang) / CELL_ASPECT]]))[0, 0])
        steps = int(max(abs(x1 - x0) / CELL_ASPECT, abs(y1 - y0))) + 1   # 지나간 칸 수
        for k in range(steps):
            q = k / float(steps)
            grid.put(int((x0 + (x1 - x0) * q) / CELL_ASPECT), int(y0 + (y1 - y0) * q), line, col)
        grid.put(int(x1 / CELL_ASPECT), int(y1), METEOR_HEAD, col)


def title(t, grid):
    p_in = overshoot(segment(t, T_IN, T_IN + T_IN_D), BOUNCE)
    p_out = ease_in(segment(t, T_OUT, T_OUT + T_OUT_D))
    top = -2                                                 # 화면 위 바깥 줄
    row = top + (TITLE_ROW - top) * p_in - (TITLE_ROW - top) * p_out
    grid.text((COLS - len(TITLE)) // 2, int(round(row)), TITLE, TITLE_RGB)


def frame(s, t, phase, grid):
    nebula(s, phase, grid)
    stars(s, phase, grid)
    meteors(s, t, grid)
    title(t, grid)


if __name__ == "__main__":
    run(globals())
