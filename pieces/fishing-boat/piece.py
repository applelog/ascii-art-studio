"""달빛 아래 낚시배 — 밤바다 한가운데 등불을 단 작은 조각배.

요청: "밤하늘에 달빛을 받아서 바다 한 가운데 떠있는 낚시배 만들어줘"
설명: brief.md   용어: GLOSSARY.md
진행: ① 정지 그림 (scene) 만 있음. ② 등장, ③ 모션은 ① 승인 후 추가.
"""
# ===== ① 장면 설정: 여기 값만 바꾸면 아래 코드 전체가 따라 바뀝니다 =====
# --- 화면 (세로 9:16) ---
COLS, ROWS   = 90, 100                 # 글자 칸 수. 90×100 칸 = 900×1600 px
FONT         = "Menlo"                 # 글꼴 이름 또는 .ttf/.ttc 경로
FONT_PX      = 14                      # 글자 크기 px (셀 = 10×16 px)
CELL_ASPECT  = 0.62                    # 셀 너비/높이 (0.35~1.2)
BACKGROUND   = (6, 10, 26)             # 바탕 남색
# --- 색 (어두움 → 밝음) ---
PALETTE      = [(30, 46, 92), (66, 96, 160), (140, 168, 222), (226, 236, 255)]
LANTERN_RGB  = (255, 168, 72)          # 등불 주황
RIM_RGB      = (176, 196, 236)         # 달빛 받은 배 윤곽선
# --- 글자 ---
SKY_RAMP     = " .:-=+*#%@"            # 하늘·달 밝기 순 글자
WATER_RAMP   = " .-~=*#"               # 바다 밝기 순 글자 (가로로 긴 글자 위주)
STAR_CHARS   = ".+*"                   # 별 (작은 별 → 큰 별)
GAMMA        = 0.8                     # 밝기 감마 (<1 이면 어두운 쪽 글자가 늘어남)
DITHER       = 0.9                     # 셀마다 고정 디더 폭 (램프 단계, 띠 무늬 제거)
DARK_CUT     = 0.07                    # 이보다 어두운 곳은 비운다 (밤의 빈 어둠)
MIN_COLOR    = 0.35                    # 글자 색 밝기 하한 (어두운 글자가 안 보이는 것 방지)
# --- 하늘 ---
HORIZON      = 0.58                    # 수평선 높이 (화면 위=0, 아래=1)
SKY_GLOW     = 0.13                    # 수평선 근처 하늘 밝기
STAR_COUNT   = 150                     # 별 개수
STAR_MAX     = 0.9                     # 가장 밝은 별 밝기 0~1
STAR_MIN     = 0.15                    # 가장 어두운 별 밝기 0~1
STAR_MARGIN  = 0.03                    # 수평선 바로 위에 별을 두지 않는 여백 (하늘 높이 비율)
STAR_SKY_MAX = 0.12                    # 이보다 밝은 하늘(달무리 등)에는 별을 두지 않음
SKY_GLOW_POW = 3                       # 하늘이 수평선 쪽으로 밝아지는 곡선 (클수록 수평선 가까이만)
# --- 달 ---
MOON_X       = 0.64                    # 달 가로 위치 (0=왼쪽, 1=오른쪽)
MOON_Y       = 0.18                    # 달 세로 위치 (0=위)
MOON_R       = 0.05                    # 달 반지름 (화면 높이 비율)
CRATER       = 0.12                    # 달 표면 얼룩 세기 0~1
CRATER_SCALE = 0.9                     # 달 얼룩 크기 (작을수록 큰 얼룩)
CRATER_GAIN  = 1.6                     # 달 얼룩 대비 (노이즈 × GAIN − BIAS)
CRATER_BIAS  = 0.5                     # 달 얼룩 기준값
MOON_LIMB    = 0.18                    # 달 가장자리가 어두워지는 정도 0~1
MOON_EDGE    = 1.0                     # 달 테두리 부드러움 (칸)
HALO         = 0.32                    # 달무리 밝기
HALO_SIZE    = 0.03                    # 달무리 퍼짐 (화면 높이 비율)
# --- 바다 ---
WATER_BASE   = 0.12                    # 달빛 밖 물결 기본 밝기
FAR_WATER    = 0.45                    # 먼 바다(수평선 쪽) 물결 밝기 비율 0~1
WAVE_X       = 7.0                     # 물결 가로 길이 (클수록 잘게)
WAVE_ROWS    = 9.0                     # 물결 세로 촘촘함 (원근으로 수평선 쪽이 촘촘)
PATH_W0      = 0.035                   # 달빛 길 폭 (수평선에서, 화면 너비 비율)
PATH_W1      = 0.20                    # 달빛 길 폭 증가 (화면 아래로 갈수록)
PATH_BRIGHT  = 1.15                    # 달빛 길 밝기
PATH_FLOOR   = 0.12                    # 반짝임이 없는 곳의 달빛 길 밝기
PATH_FADE    = 0.35                    # 화면 아래로 갈수록 달빛 길이 약해지는 정도 0~1
GLITTER_GAIN = 2.2                     # 달빛 반짝임 대비 (물결 × GAIN − BIAS)
GLITTER_BIAS = 0.85                    # 달빛 반짝임 기준값
PERSPECTIVE  = 0.04                    # 원근 세기 (작을수록 수평선 쪽 물결이 더 촘촘)
WAVE_NEAR    = 0.12                    # 수평선 근처 물결이 가로로 늘어나는 한계
WAVE_FLOOR   = 0.5                     # 물결 밝기 바닥값
RIPPLE2_MIX  = 0.35                    # 잔물결(두 번째 물결 층) 섞는 비율 0~1
RIPPLE2_SCALE = (2.3, 2.1)             # 잔물결 크기 (가로, 세로 배수)
# --- 배 ---
BOAT_X       = 0.50                    # 배 가운데 가로 위치
BOAT_Y       = 0.71                    # 배 흘수선(물에 닿는 선) 세로 위치
BOAT_W       = 0.44                    # 배 길이 (화면 너비 비율)
HULL_ROWS    = 4                       # 선체 높이 (칸)
HULL_TAPER   = 0.14                    # 선체 아래가 좁아지는 정도 (한쪽, 배 길이 비율)
CABIN_W      = 0.22                    # 조타실 너비 (배 길이 비율)
CABIN_ROWS   = 5                       # 조타실 높이 (칸)
CABIN_X      = -0.20                   # 조타실 위치 (배 가운데 기준, 배 길이 비율, -는 뒤쪽)
MAST_ROWS    = 13                      # 돛대 높이 (갑판 위 칸)
MAST_X       = 0.12                    # 돛대 위치 (배 가운데 기준, 배 길이 비율)
ROD_ROWS     = 9                       # 낚싯대 높이 (칸)
ROD_COLS     = 12                      # 낚싯대가 뒤로 뻗는 길이 (칸)
LANTERN_GLOW = 4.0                     # 등불 빛 퍼짐 (칸)
LANTERN_TINT = 0.8                     # 등불 근처 글자에 주황을 섞는 최대 비율 0~1
LANTERN_DX, LANTERN_DY = 1, 2          # 등불 위치 (돛대 꼭대기 기준 오른쪽·아래로 칸)
LANTERN_CHAR = "@"                     # 등불 글자
WINDOW_CHAR  = "o"                     # 조타실 불 켜진 창 글자
MAST_TOP_CHAR = "^"                    # 돛대 꼭대기 글자
ROD_INSET    = 2                       # 낚싯대 뿌리가 배 뒤 끝에서 안쪽으로 들어온 칸
LINE_RGB     = (120, 136, 170)         # 낚싯줄 색
LINE_CHAR    = ":"                     # 낚싯줄 글자
LINE_GAP     = 2                       # 낚싯줄 점 간격 (칸)
LINE_DEPTH   = 1                       # 낚싯줄이 물속으로 들어가는 칸
# --- 등불 물 반사 ---
REFLECT_ROWS = 12                      # 물에 비친 등불 길이 (칸)
REFLECT_GAP  = 2                       # 반사 줄 간격 (칸)
REFLECT_CHARS = "=-"                   # 반사 글자 (가까운 쪽, 먼 쪽)
REFLECT_SPLIT = 0.6                    # 이 밝기 아래부터 두 번째 반사 글자
REFLECT_MIN  = 0.35                    # 반사 끝 밝기 비율 0~1
# --- 난수 ---
SEED         = 7                       # 별 위치·물결·디더 seed
NOISE_SIZE   = 128                     # 노이즈 난수표 크기
MOON_SPOT_SHIFT = 40                   # 달 얼룩 무늬 위치 (바꾸면 얼룩 배치만 달라짐)
RIPPLE2_SHIFT = (17, 31)               # 잔물결 무늬 위치 (바꾸면 물결 배치만 달라짐)
# ===== 코드 =====
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(_d, "asciiart")) and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np  # noqa: E402

from asciiart.run import run  # noqa: E402

# ---------- 임시 도구 (F4·F5 에서 엔진 ramp.py / noise.py 로 옮김) ----------


def cell_hash(x, y, seed):
    """정수 칸 좌표 → 0..1 고정 값 (디더·반짝임용)."""
    h = (x.astype(np.uint64) * np.uint64(374761393) + y.astype(np.uint64) * np.uint64(668265263)
         + np.uint64(seed) * np.uint64(2147483647)) & np.uint64(0xFFFFFFFF)
    h = (h ^ (h >> np.uint64(13))) * np.uint64(1274126177) & np.uint64(0xFFFFFFFF)
    h ^= h >> np.uint64(16)
    return (h & np.uint64(0xFFFFFFFF)).astype(np.float64) / 4294967296.0


def value_noise(table, x, y):
    """격자 값 노이즈 (부드러운 bilinear). table 은 seed 로 만든 정사각 난수표."""
    n = table.shape[0]
    xi, yi = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - xi, y - yi
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    x0, y0 = xi % n, yi % n
    x1, y1 = (x0 + 1) % n, (y0 + 1) % n
    a = table[y0, x0] * (1 - fx) + table[y0, x1] * fx
    b = table[y1, x0] * (1 - fx) + table[y1, x1] * fx
    return a * (1 - fy) + b * fy


def lum_to_chars(lum, ramp, xx, yy, seed):
    """밝기 0..1 → 램프 글자 코드 (감마 + 셀 고정 디더)."""
    n = len(ramp) - 1
    t = np.clip((lum - DARK_CUT) / (1 - DARK_CUT), 0, 1)
    level = t ** GAMMA * n + (cell_hash(xx, yy, seed) - 0.5) * DITHER
    idx = np.clip(np.round(level), 0, n).astype(int)
    idx[lum < DARK_CUT] = 0
    codes = np.array([0 if c == " " else ord(c) for c in ramp], np.uint32)
    return codes[idx]


def palette_color(lum):
    """밝기 → PALETTE 보간 색 (rows, cols, 3)."""
    pal = np.array(PALETTE, np.float64)
    t = np.clip(MIN_COLOR + (1 - MIN_COLOR) * np.clip(lum, 0, 1), 0, 1) * (len(pal) - 1)
    i = np.clip(np.floor(t).astype(int), 0, len(pal) - 2)
    f = (t - i)[..., None]
    return (pal[i] * (1 - f) + pal[i + 1] * f).round().astype(np.uint8)


# ---------- 장면 ----------


def setup():
    """한 번만 계산: 좌표, 노이즈 표, 별 위치."""
    rng = np.random.RandomState(SEED)
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    width = COLS * CELL_ASPECT                     # 화면 너비 (칸 높이 단위)
    px, py = (xx + 0.5) * CELL_ASPECT, yy + 0.5    # 칸 중심 (칸 높이 단위, 정사각 좌표)
    stars = []
    for _ in range(STAR_COUNT):
        sx, sy = rng.uniform(0, COLS), rng.uniform(0, ROWS * HORIZON * (1 - STAR_MARGIN))
        stars.append((int(sx), int(sy), rng.uniform(STAR_MIN, 1)))
    return {
        "xx": xx, "yy": yy, "px": px, "py": py, "width": width,
        "u": px / width, "v": py / ROWS,
        "noise": rng.uniform(0, 1, (NOISE_SIZE, NOISE_SIZE)),
        "stars": stars,
    }


def sky_and_moon(s):
    """하늘·달·달무리 밝기와 '달 영역' 마스크."""
    v, px, py = s["v"], s["px"], s["py"]
    mx, my, mr = MOON_X * s["width"], MOON_Y * ROWS, MOON_R * ROWS
    d = np.hypot(px - mx, py - my)
    sky = SKY_GLOW * (v / HORIZON) ** SKY_GLOW_POW
    halo = HALO * np.exp(-np.maximum(d - mr, 0) / (HALO_SIZE * ROWS))
    cover = np.clip((mr - d) / MOON_EDGE + 0.5, 0, 1)   # 달 테두리 부드럽게
    limb = (1 - MOON_LIMB) + MOON_LIMB * np.sqrt(np.clip(1 - (d / mr) ** 2, 0, 1))
    spots = value_noise(s["noise"], px * CRATER_SCALE + MOON_SPOT_SHIFT, py * CRATER_SCALE + MOON_SPOT_SHIFT)
    moon = limb * (1 - CRATER * np.clip(spots * CRATER_GAIN - CRATER_BIAS, 0, 1))
    lum = np.maximum(sky + halo * (1 - cover), 0) * (1 - cover) + moon * cover
    return lum, cover > 0.5


def sea(s):
    """바다 밝기: 원근 물결 + 달빛 길."""
    u, v = s["u"], s["v"]
    t = np.clip((v - HORIZON) / (1 - HORIZON), 0, 1)        # 수평선 0 → 화면 아래 1
    depth = np.log(t + PERSPECTIVE)                                 # 원근: 수평선 쪽 촘촘
    ripple = value_noise(s["noise"], u * WAVE_X / (t + WAVE_NEAR), depth * WAVE_ROWS)
    ripple2 = value_noise(s["noise"], u * WAVE_X * RIPPLE2_SCALE[0] / (t + WAVE_NEAR) + RIPPLE2_SHIFT[0],
                          depth * WAVE_ROWS * RIPPLE2_SCALE[1] + RIPPLE2_SHIFT[1])
    wave = (1 - RIPPLE2_MIX) * ripple + RIPPLE2_MIX * ripple2
    base = WATER_BASE * (WAVE_FLOOR + wave) * (FAR_WATER + (1 - FAR_WATER) * t)
    width = PATH_W0 + PATH_W1 * t
    path = np.exp(-((u - MOON_X) / width) ** 2)
    glitter = np.clip(wave * GLITTER_GAIN - GLITTER_BIAS, 0, 1)
    lum = base + PATH_BRIGHT * path * (PATH_FLOOR + glitter) * (1 - PATH_FADE * t)
    return lum


def boat_shape():
    """배 칸 좌표 계산 → (가려지는 칸 마스크, [(x, y, 글자, 색)])."""
    width_cols = BOAT_W * COLS
    cx, wl = BOAT_X * COLS, int(round(BOAT_Y * ROWS))      # 가운데 열, 흘수선 행
    deck = wl - HULL_ROWS                                  # 갑판 행
    mask = np.zeros((ROWS, COLS), bool)
    marks = []

    def put(x, y, ch, rgb=RIM_RGB):
        if 0 <= x < COLS and 0 <= y < ROWS:
            marks.append((int(x), int(y), ch, rgb))

    # 선체: 위가 넓고 아래가 좁은 사다리꼴
    for k, y in enumerate(range(deck, wl + 1)):
        f = k / max(1, HULL_ROWS)
        half = width_cols / 2 * (1 - 2 * HULL_TAPER * f)
        x0, x1 = int(round(cx - half)), int(round(cx + half))
        mask[y, x0:x1 + 1] = True
        if y == deck:
            for x in range(x0, x1 + 1):
                put(x, y - 1, "_")                          # 갑판선 ('_' 는 칸 아래쪽에 그려짐)
        if y == wl:
            put(x0, y, "\\")
            put(x1, y, "/")
            for x in range(x0 + 1, x1):
                put(x, y, "_")
        else:
            put(x0, y, "\\")
            put(x1, y, "/")
    # 조타실
    cw = int(round(CABIN_W * width_cols))
    c0 = int(round(cx + CABIN_X * width_cols - cw / 2))
    top = deck - CABIN_ROWS
    mask[top:deck, c0:c0 + cw + 1] = True
    for x in range(c0 + 1, c0 + cw):
        put(x, top - 1, "_")
    for y in range(top, deck):
        put(c0, y, "|")
        put(c0 + cw, y, "|")
    put(c0 + cw // 2, top + CABIN_ROWS // 2, WINDOW_CHAR, LANTERN_RGB)  # 불 켜진 창
    # 돛대와 등불
    mx = int(round(cx + MAST_X * width_cols))
    for y in range(deck - MAST_ROWS, deck):
        mask[y, mx] = True
        put(mx, y, "|")
    lantern = (mx + LANTERN_DX, deck - MAST_ROWS + LANTERN_DY)
    put(lantern[0], lantern[1], LANTERN_CHAR, LANTERN_RGB)
    put(mx, deck - MAST_ROWS - 1, MAST_TOP_CHAR)
    # 낚싯대: 배 뒤쪽 끝에서 뒤로 비스듬히 + 물로 내려가는 줄
    stern = int(round(cx - width_cols / 2)) + ROD_INSET
    for k in range(ROD_ROWS):
        x = stern - int(round(k * ROD_COLS / ROD_ROWS))
        put(x, deck - 1 - k, "|" if ROD_COLS == 0 else ("\\" if ROD_COLS > 0 else "/"))
    tip_x, tip_y = stern - ROD_COLS, deck - ROD_ROWS
    for y in range(tip_y + 1, wl + 1 + LINE_DEPTH):
        if (y - tip_y) % LINE_GAP == 0:
            put(tip_x - 1, y, LINE_CHAR, LINE_RGB)
    return mask, marks, lantern, wl


def scene(s, grid):
    """① 완성 화면을 grid 에 채운다."""
    xx, yy, v = s["xx"], s["yy"], s["v"]
    sky_lum, moon_mask = sky_and_moon(s)
    sea_lum = sea(s)
    is_sea = v >= HORIZON

    # 하늘·달 (밝기 글자)
    sky_codes = lum_to_chars(sky_lum, SKY_RAMP, xx, yy, SEED)
    grid.fill(~is_sea & (sky_codes != 0), sky_codes, palette_color(sky_lum))

    # 별 (달·달무리 위에는 두지 않음)
    for x, y, b in s["stars"]:
        if 0 <= y < ROWS and 0 <= x < COLS and sky_lum[y, x] < STAR_SKY_MAX and not moon_mask[y, x]:
            ch = STAR_CHARS[min(len(STAR_CHARS) - 1, int(b * len(STAR_CHARS)))]
            grid.put(x, y, ch, tuple(palette_color(np.array(b * STAR_MAX))))

    # 바다 (가로로 긴 글자)
    sea_codes = lum_to_chars(sea_lum, WATER_RAMP, xx, yy, SEED + 1)
    grid.fill(is_sea & (sea_codes != 0), sea_codes, palette_color(sea_lum))

    # 등불이 비치는 따뜻한 물 반사 (배 아래)
    mask, marks, (lx, ly), wl = boat_shape()
    for y in range(wl + 1, min(ROWS, wl + 1 + REFLECT_ROWS)):
        fade = 1 - (y - wl - 1) / REFLECT_ROWS
        if (y + lx) % REFLECT_GAP == 0:
            rgb = tuple(int(c * (REFLECT_MIN + (1 - REFLECT_MIN) * fade)) for c in LANTERN_RGB)
            grid.put(lx, y, REFLECT_CHARS[1] if fade < REFLECT_SPLIT else REFLECT_CHARS[0], rgb)

    # 배: 실루엣 자리를 비우고 윤곽선을 그린다
    grid.ch[mask] = 0
    for x, y, ch, rgb in marks:
        grid.put(x, y, ch, rgb)

    # 등불 주변 따뜻한 빛: 주변 글자 색을 주황 쪽으로 섞는다
    dist = np.hypot((xx - lx) * CELL_ASPECT, yy - ly)
    warm = np.clip(1 - dist / LANTERN_GLOW, 0, 1)[..., None] * LANTERN_TINT
    near = (warm[..., 0] > 0) & (grid.ch != 0) & ~mask
    mixed = grid.rgb * (1 - warm) + np.array(LANTERN_RGB) * warm
    grid.rgb[near] = mixed[near].round().astype(np.uint8)


if __name__ == "__main__":
    run(globals())
