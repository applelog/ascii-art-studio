"""F7.5 데모: 단계 구조 — ① 고리 행성 → ② 위에서부터 '해독'되며 나타남 → ③ 폭풍이 돌고 고리·별이 반짝임.

작성 요령 (연결 검사가 저절로 맞는 형태):
    draw(state, phase, grid)  그림 하나를 phase 로 그린다
    scene  = draw(phase=0)
    motion = draw(phase)                         phase 0 과 1 이 같도록 모든 변화는 정수 주기
    intro  = scene 을 가렸다 드러내기             p=1 이면 scene 그대로

    python examples/f75_demo.py                  창: 등장 한 번 → 모션 반복 (R: 등장부터 다시)
    python examples/f75_demo.py --check          단계 연결 검사
    python examples/f75_demo.py --stage 2        ② 등장 MP4 + 프레임 띠
    python examples/f75_demo.py --final          최종 MP4 + 대표 그림
"""
# ===== ① 장면 설정 =====
COLS, ROWS      = 120, 60               # 글자 칸 수
FONT            = "Menlo"               # 글꼴
FONT_PX         = 14                    # 글자 크기 px
CELL_ASPECT     = 0.6                   # 칸 너비/높이
BACKGROUND      = (5, 6, 14)            # 바탕색
SUPERSAMPLE     = 2                     # 칸 하나를 몇×몇 점으로 계산 (1~3)
PLANET_X, PLANET_Y = -0.15, 0.05        # 행성 중심 (화면 좌표, 세로 −1..1)
PLANET_R        = 0.45                  # 행성 반지름 (화면 높이 절반 = 1)
BAND_COUNT      = 9                     # 줄무늬 수
BAND_A_RGB      = (230, 190, 130)       # 줄무늬 색 1
BAND_B_RGB      = (170, 110, 80)        # 줄무늬 색 2
STORM           = 0.35                  # 폭풍 무늬 세기 0~1
STORM_SCALE     = 1.6                   # 폭풍 무늬 크기 (클수록 잘게)
LIGHT_X, LIGHT_Y = -0.55, 0.45          # 빛 방향 (화면 기준, 왼쪽 위에서)
AMBIENT         = 0.06                  # 그늘진 쪽 최소 밝기
RING_TILT       = 0.28                  # 고리 기울기 (세로/가로 비율)
RING_INNER      = 1.35                  # 고리 안쪽 반지름 (행성 반지름 배수)
RING_OUTER      = 2.15                  # 고리 바깥 반지름
RING_GAPS       = 26                    # 고리 줄 수
RING_RGB        = (200, 205, 225)       # 고리 색
RING_BRIGHT     = 0.75                  # 고리 밝기
STAR_COUNT      = 110                   # 별 개수
STAR_CHARS      = ".+*"                 # 별 글자 (어두움 → 밝음)
STAR_RGB        = (220, 228, 255)       # 별 색
RAMP            = " .:-=+*#%@"          # 밝기 순 글자
GAMMA           = 0.8                   # 밝기 감마
CUT             = 0.05                  # 이보다 어두우면 빈칸
MIN_COLOR       = 0.35                  # 글자 색 밝기 하한
# ===== ② 등장 설정 =====
INTRO_SECONDS   = 3.0                   # 등장 길이 (초)
INTRO_HOLD      = 1.0                   # 등장 검토 영상 끝에 완성 화면을 보여 주는 시간 (초)
REVEAL_SCAN     = 0.65                  # 위→아래로 쓸어내리는 정도 (0 이면 무작위 순서만)
REVEAL_JITTER   = 0.35                  # 칸마다 드러나는 순서의 흔들림
DECODE_SPAN     = 0.18                  # 칸 하나가 무작위 글자로 섞이는 시간 (등장 길이 비율)
DECODE_HZ       = 20                    # 섞이는 글자가 바뀌는 속도 (초당)
DECODE_CHARS    = "01<>[]{}#%&$?/\\|+="  # 섞일 때 쓰는 글자
DECODE_RGB      = (120, 255, 170)       # 섞일 때 글자 색
# ===== ③ 모션 설정 =====
LOOP_SECONDS    = 6                     # 모션 한 루프 길이 (초)
FPS             = 30                    # 12 | 24 | 30 | 60
LOOP            = True                  # 모션 반복
SPIN            = 1                     # 한 루프 동안 행성이 도는 바퀴 수 (정수)
RING_SPIN       = 2                     # 한 루프 동안 고리 반짝임이 도는 바퀴 수 (정수)
RING_SPARKLE    = 0.45                  # 고리 반짝임 세기 0~1
TWINKLES        = 3                     # 한 루프 동안 별이 반짝이는 횟수 (정수)
TWINKLE         = 0.6                   # 별 반짝임 세기 0~1
# ===== 최종 출력 =====
FINAL_LOOPS     = 2                     # 최종 영상에서 모션 반복 횟수
# ===== 효과 =====
TRAIL           = 0.45                  # 잔상 0~0.97
GLOW            = 0.45                  # 글로우 0~1
GLOW_RADIUS     = 0.9                   # 글로우 번짐 (칸 높이 배수)
SEED            = 21                    # 난수 seed
RANGES          = {"SUPERSAMPLE": (1, 3), "SPIN": (0, 6), "RING_SPIN": (0, 8), "TWINKLES": (1, 12),
                   "STORM": (0, 1), "RING_SPARKLE": (0, 1), "TWINKLE": (0, 1), "DECODE_SPAN": (0.02, 0.5)}
# ===== 코드 =====
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from asciiart.ease import loop_sin  # noqa: E402
from asciiart.grid import Grid  # noqa: E402
from asciiart.noise import noise3  # noqa: E402
from asciiart.ramp import cell_hash, codes_of  # noqa: E402
from asciiart.run import run  # noqa: E402
from asciiart.shade import field_to_grid, shade  # noqa: E402


def rgb01(c):
    return np.array(c, np.float64) / 255.0


def setup():
    rng = np.random.RandomState(SEED)
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    stars = [(rng.randint(0, COLS), rng.randint(0, ROWS), rng.uniform(0, 1), rng.uniform(0, 1))
             for _ in range(STAR_COUNT)]
    # ② 등장: 칸마다 드러나는 순서 0..(1−DECODE_SPAN)
    order = REVEAL_SCAN * (yy / float(ROWS)) + REVEAL_JITTER * cell_hash(xx, yy, SEED)
    order = order / max(1e-9, REVEAL_SCAN + REVEAL_JITTER) * (1 - DECODE_SPAN)
    return {"xx": xx, "yy": yy, "stars": stars, "order": order, "decode": codes_of(DECODE_CHARS)}


def planet_light(phase):
    """phase → 화면 색 함수 fn(X, Y). 행성(줄무늬·폭풍·빛) + 고리(앞·뒤) ."""
    lz = math.sqrt(max(0.0, 1 - LIGHT_X ** 2 - LIGHT_Y ** 2))
    spin = 2 * math.pi * round(SPIN) * phase
    ring_spin = 2 * math.pi * round(RING_SPIN) * phase

    def fn(X, Y):
        nx, ny = (X - PLANET_X) / PLANET_R, (Y - PLANET_Y) / PLANET_R
        d2 = nx ** 2 + ny ** 2
        inside = d2 < 1
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        lat = np.arcsin(np.clip(ny, -1, 1))
        lon = np.arctan2(nx, nz) + spin
        storm = noise3(np.cos(lon) * STORM_SCALE, np.sin(lon) * STORM_SCALE, lat * STORM_SCALE * 2, SEED)
        band = 0.5 + 0.5 * np.cos(lat * BAND_COUNT + (storm - 0.5) * STORM * math.pi * 2)
        surface = band[..., None] * rgb01(BAND_A_RGB) + (1 - band)[..., None] * rgb01(BAND_B_RGB)
        light = np.clip(nx * LIGHT_X + ny * LIGHT_Y + nz * lz, 0, 1) * (1 - AMBIENT) + AMBIENT
        planet = surface * (light * inside)[..., None]
        # 고리: 기울어진 원판. 아래쪽 반(ry<0)은 행성 앞, 위쪽 반은 행성 뒤
        rx, ry = nx, ny / RING_TILT
        rr = np.hypot(rx, ry)
        on_ring = (rr > RING_INNER) & (rr < RING_OUTER)
        theta = np.arctan2(ry, rx)
        lines = 0.6 + 0.4 * np.sin(rr * RING_GAPS)
        sparkle = 1 - RING_SPARKLE + RING_SPARKLE * noise3(np.cos(theta - ring_spin) * 3, np.sin(theta - ring_spin) * 3,
                                                          rr * 4, SEED + 1)
        ring = (RING_BRIGHT * lines * sparkle * on_ring)[..., None] * rgb01(RING_RGB)
        front = on_ring & (ry < 0)
        show_ring = front | ~inside
        return np.where(show_ring[..., None] & on_ring[..., None], ring, planet)

    return fn


def draw(s, phase, grid):
    rgb = shade(planet_light(phase), COLS, ROWS, CELL_ASPECT, SUPERSAMPLE)
    field_to_grid(rgb, grid, RAMP, cut=CUT, gamma=GAMMA, dither=1.0, seed=SEED, min_color=MIN_COLOR)
    for x, y, b, off in s["stars"]:
        if grid.ch[y, x] != 0:
            continue                                     # 행성·고리 위에는 별을 두지 않음
        tw = 1 - TWINKLE * (0.5 + 0.5 * loop_sin(phase, TWINKLES, off))
        k = min(len(STAR_CHARS) - 1, int(b * tw * len(STAR_CHARS)))
        grid.put(x, y, STAR_CHARS[k], tuple(int(c * (0.4 + 0.6 * tw)) for c in STAR_RGB))


def scene(s, grid):
    """① 완성 화면 = 모션의 처음."""
    draw(s, 0.0, grid)


def intro(s, p, grid):
    """② 해독 등장: 위에서부터 칸마다 무작위 글자로 섞이다가 제 글자로 맞춰진다. p=1 이면 scene 그대로."""
    final = Grid(COLS, ROWS)
    scene(s, final)
    if p >= 1:
        grid.ch[...], grid.rgb[...] = final.ch, final.rgb
        return
    order = s["order"]
    shown = p >= order + DECODE_SPAN
    decoding = (p >= order) & ~shown & (final.ch != 0)
    grid.ch[shown], grid.rgb[shown] = final.ch[shown], final.rgb[shown]
    step = int(p * INTRO_SECONDS * DECODE_HZ)
    pick = np.floor(cell_hash(s["xx"], s["yy"], SEED + 7 * (step + 1)) * len(s["decode"])).astype(int)
    grid.fill(decoding, s["decode"][pick], DECODE_RGB)


def motion(s, t, phase, grid):
    """③ 행성이 SPIN 바퀴 돌고, 고리 반짝임이 RING_SPIN 바퀴 돌고, 별이 TWINKLES 번 반짝인다."""
    draw(s, phase, grid)


if __name__ == "__main__":
    run(globals())
