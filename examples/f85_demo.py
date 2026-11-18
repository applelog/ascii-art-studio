"""F8.5 데모: 3D — 바닥 위에 떠 있는 매끈한 물체(구 + 기울어진 고리), 그림자, 둘레를 도는 점 고리. 단계 구조.

    ① 완성 화면: 레이마칭 + 빛(난반사·하이라이트·테두리 빛·그림자) + 거리 안개, 점 고리는 물체에 가려짐
    ② 등장: 카메라 쪽에서 안쪽으로 깊이 순서대로 나타남 (앞면에 밝은 띠)
    ③ 모션: 물체가 SPIN 바퀴 돌고 점 고리가 RING_SPIN 바퀴 돎

    python examples/f85_demo.py                창: 등장 → 모션 반복
    python examples/f85_demo.py --stage 1      ① 완성 화면 PNG
"""
# ===== ① 장면 설정 =====
COLS, ROWS      = 110, 55               # 글자 칸 수
FONT            = "Menlo"               # 글꼴
FONT_PX         = 14                    # 글자 크기 px
CELL_ASPECT     = 0.6                   # 칸 너비/높이
BACKGROUND      = (6, 7, 12)            # 바탕색
SUPERSAMPLE     = 1                     # 칸 하나를 몇×몇 점으로 계산 (1~2, 2 면 4배 느림)
CAMERA_POS      = (0.0, 1.5, -4.6)      # 카메라 위치 (x 오른쪽, y 위, z 안쪽)
CAMERA_TARGET   = (0.0, 0.25, 0.0)      # 카메라가 보는 곳
FOV             = 40                    # 세로 화각 (도)
LIGHT_DIR       = (-0.5, 0.6, -0.65)    # 빛이 오는 쪽 (왼쪽 위 앞)
FLOAT_Y         = 0.45                  # 물체 높이
BALL_R          = 0.35                  # 가운데 구 반지름
RING_R, RING_W  = 0.85, 0.22            # 고리 큰 반지름, 굵기
RING_TILT       = 1.1                   # 고리 기울기 (라디안, 클수록 카메라를 향해 섬)
BLEND           = 0.18                  # 구와 고리를 부드럽게 잇는 정도
OBJECT_RGB      = (240, 196, 120)       # 물체 색
FLOOR_Y         = -0.75                 # 바닥 높이
FLOOR_A_RGB     = (70, 76, 96)          # 바닥 체크 색 1
FLOOR_B_RGB     = (40, 44, 58)          # 바닥 체크 색 2
CHECK           = 0.8                   # 바닥 체크 한 칸 크기
AMBIENT         = 0.14                  # 그늘 밝기
SPECULAR        = 0.5                   # 하이라이트 세기
SHININESS       = 30                    # 하이라이트 날카로움
RIM             = 0.35                  # 테두리 빛 세기
FOG             = 0.35                  # 거리 안개 세기 (FOG_START 보다 먼 곳이 어두워짐)
FOG_START       = 4.8                   # 안개가 시작되는 거리 (물체 바로 뒤)
SHADOWS         = True                  # 부드러운 그림자
MAX_STEPS       = 56                    # 레이마칭 최대 걸음
POINTS          = 90                    # 둘레를 도는 점 개수
ORBIT_R         = 1.65                  # 점 고리 반지름
ORBIT_TILT      = -0.25                 # 점 고리 기울기 (라디안)
POINT_CHARS     = ".+*"                 # 점 글자 (먼 것 → 가까운 것)
POINT_RGB       = (150, 220, 255)       # 점 색
RAMP            = " .:-=+*#%@"          # 밝기 순 글자
GAMMA           = 0.8                   # 밝기 감마
CUT             = 0.03                  # 이보다 어두우면 빈칸
MIN_COLOR       = 0.3                   # 글자 색 밝기 하한
# ===== ② 등장 설정 =====
INTRO_SECONDS   = 2.5                   # 등장 길이 (초)
INTRO_HOLD      = 1.0                   # 등장 검토 영상 끝에 완성 화면을 보여 주는 시간 (초)
SWEEP_BAND      = 0.6                   # 깊이 띠 두께 (거리)
SWEEP_RGB       = (120, 255, 200)       # 깊이 띠 색
SWEEP_CHAR      = "#"                   # 깊이 띠 글자
# ===== ③ 모션 설정 =====
LOOP_SECONDS    = 6                     # 한 루프 길이 (초)
FPS             = 30                    # 12 | 24 | 30 | 60
LOOP            = True                  # 모션 반복
SPIN            = 1                     # 한 루프 동안 물체가 도는 바퀴 수 (정수)
RING_SPIN       = 2                     # 한 루프 동안 점 고리가 도는 바퀴 수 (정수)
# ===== 최종 출력 =====
FINAL_LOOPS     = 2                     # 최종 영상에서 모션 반복 횟수
# ===== 효과 =====
GLOW            = 0.35                  # 글로우 0~1
GLOW_RADIUS     = 0.8                   # 글로우 번짐 (칸 높이 배수)
SEED            = 8                     # 디더 seed
RANGES          = {"SUPERSAMPLE": (1, 2), "SPIN": (0, 4), "RING_SPIN": (0, 6), "POINTS": (0, 400), "FOV": (10, 120)}
# ===== 코드 =====
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from asciiart import three as T  # noqa: E402
from asciiart.grid import Grid  # noqa: E402
from asciiart.ramp import codes_of  # noqa: E402
from asciiart.run import run  # noqa: E402


def rgb01(c):
    return np.array(c, np.float64) / 255.0


def setup():
    cam = T.Camera(CAMERA_POS, CAMERA_TARGET, fov=FOV)
    k = np.arange(POINTS)
    return {"cam": cam, "angles": 2 * math.pi * k / max(1, POINTS), "point_codes": codes_of(POINT_CHARS)}


def scene_sdf(phase):
    spin = T.rot_y(2 * math.pi * round(SPIN) * phase)
    ring_rot = spin @ T.rot_x(RING_TILT)
    center = np.array([0, FLOAT_Y, 0])

    def object_sdf(p):
        ball = T.sphere(p - center, BALL_R)
        ring = T.torus(T.local(p, ring_rot, center), RING_R, RING_W)
        return T.smooth_union(ball, ring, BLEND)

    def sdf(p):
        return T.union(object_sdf(p), T.plane(p, (0, 1, 0), -FLOOR_Y))

    def color(p, n):
        floor = p[:, 1] < FLOOR_Y + 1e-2
        check = (np.floor(p[:, 0] / CHECK) + np.floor(p[:, 2] / CHECK)) % 2
        floor_rgb = np.where(check[:, None] > 0, rgb01(FLOOR_A_RGB), rgb01(FLOOR_B_RGB))
        return np.where(floor[:, None], floor_rgb, rgb01(OBJECT_RGB))

    return sdf, color


def draw(s, phase, grid):
    sdf, color = scene_sdf(phase)
    r = T.render_sdf(sdf, s["cam"], COLS, ROWS, CELL_ASPECT, SUPERSAMPLE, color=color, light_dir=LIGHT_DIR,
                     ambient=AMBIENT, specular=SPECULAR, shininess=SHININESS, rim=RIM, shadows=SHADOWS,
                     fog=FOG, fog_start=FOG_START, max_steps=MAX_STEPS)
    T.to_grid(grid, r, RAMP, gamma=GAMMA, cut=CUT, dither=1.0, seed=SEED, min_color=MIN_COLOR)
    # 점 고리: 물체 뒤로 가면 가려진다 (to_grid 가 남긴 깊이와 비교)
    a = s["angles"] + 2 * math.pi * round(RING_SPIN) * phase
    ring = np.stack([np.cos(a) * ORBIT_R, np.zeros_like(a), np.sin(a) * ORBIT_R], -1) @ T.rot_x(ORBIT_TILT).T
    pts = ring + [0, FLOAT_Y, 0]
    _, _, z, _ = s["cam"].project(pts, COLS, ROWS, CELL_ASPECT)
    near = (z - z.min()) / max(1e-9, z.max() - z.min())
    k = np.clip(((1 - near) * len(s["point_codes"])).astype(int), 0, len(s["point_codes"]) - 1)
    T.draw_points(grid, pts, s["cam"], CELL_ASPECT, s["point_codes"][k], POINT_RGB)
    return r


def scene(s, grid):
    """① 완성 화면 = 모션의 처음."""
    draw(s, 0.0, grid)


def intro(s, p, grid):
    """② 카메라 쪽에서 안쪽으로 깊이 순서대로 나타난다 (앞면에 밝은 띠). p=1 이면 scene 그대로."""
    final = Grid(COLS, ROWS)
    scene(s, final)
    if p >= 1:
        grid.ch[...], grid.rgb[...] = final.ch, final.rgb
        return
    depth = final.z
    finite = np.isfinite(depth)
    near, far = depth[finite].min(), depth[finite].max()
    front = near + (far - near + SWEEP_BAND) * p
    shown = finite & (depth < front - SWEEP_BAND) & (final.ch != 0)
    band = finite & (depth >= front - SWEEP_BAND) & (depth < front) & (final.ch != 0)
    grid.ch[shown], grid.rgb[shown] = final.ch[shown], final.rgb[shown]
    grid.fill(band, SWEEP_CHAR, SWEEP_RGB)


def motion(s, t, phase, grid):
    """③ 물체가 돌고 점 고리가 돈다."""
    draw(s, phase, grid)


if __name__ == "__main__":
    run(globals())
