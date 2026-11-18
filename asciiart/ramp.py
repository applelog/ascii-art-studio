"""밝기 → 글자.

    ramp_chars   밝기를 램프 글자로 (감마 · 어두운 곳 비우기 · 디더 · 반짝임)
    pool_chars   글자 풀: 밝기 단계마다 글자 묶음, 칸마다 그 안에서 고름
    edge_chars   밝기 경계 방향 → 윤곽 글자 | / - \\
    edges        밝기 필드에서 경계 세기와 방향 계산 (Sobel)

모두 numpy 배열을 한 번에 처리한다. 결과는 grid.fill() 에 바로 넣을 수 있는 글자 코드 배열이다
(빈칸 = 0).

루프 작품에서 반짝임(step)을 쓸 때는 step = int(phase * STEPS) % STEPS 처럼 넘긴다.
phase 0 과 1 에서 같은 step 이 나와야 끝과 처음이 이어진다.
"""
import numpy as np

# ---------- 램프 모음 (어두움 → 밝음, 첫 글자는 빈칸) ----------
RAMPS = {
    "short": " .:-=+*#%@",
    # Paul Bourke 의 70단계 표준 램프를 어두움→밝음 순으로 뒤집은 것
    "long": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "blocks": " ░▒▓█",
    "dots": " .·:•●",
    "digits": " .:17402369",
    "water": " .-~=*#",
}

# 4단계 글자 풀 (어두움 → 밝음). 이 프로젝트에서 직접 고른 것으로, 단계마다 글자 잉크 양이 늘어난다
# (Menlo 14px 평균 잉크 비율 약 0.04 → 0.07 → 0.11 → 0.22, tests/test_f4_ramp.py 가 확인).
GLYPH_POOLS = [".,'`-", ":;~^\"", "=+<>ivc*", "#%@MWN"]

# 4×4 Bayer 행렬 (규칙적인 바둑판 디더)
BAYER4 = np.array([[0, 8, 2, 10],
                   [12, 4, 14, 6],
                   [3, 11, 1, 9],
                   [15, 7, 13, 5]], np.float64)

# 윤곽 글자: 경계 방향(0°, 45°, 90°, 135°)마다 하나
EDGE_GLYPHS = "|/-\\"


def codes_of(chars):
    """문자열 → 글자 코드 배열. 빈칸은 0."""
    return np.array([0 if c == " " else ord(c) for c in chars], np.uint32)


def cell_hash(xx, yy, seed=0):
    """칸 좌표(정수 배열) → 0..1 고정 값. 같은 칸·같은 seed 면 언제나 같다."""
    m = np.uint64(0xFFFFFFFF)
    h = (np.asarray(xx).astype(np.uint64) * np.uint64(374761393)
         + np.asarray(yy).astype(np.uint64) * np.uint64(668265263)
         + np.uint64(seed) * np.uint64(2147483647)) & m
    h = (h ^ (h >> np.uint64(13))) * np.uint64(1274126177) & m
    h ^= h >> np.uint64(16)
    return (h & m).astype(np.float64) / 4294967296.0


def _grid_coords(shape, xx, yy):
    if xx is None or yy is None:
        yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return xx, yy


def dither_offset(shape, mode, xx=None, yy=None, seed=0):
    """칸마다 −0.5..0.5 의 고정 값.

    mode "hash"  : 칸마다 무작위 (eyeTutorial 의 HSC 방식, 자연스러운 질감)
         "bayer" : 4×4 바둑판 (규칙적인 망점 느낌)
    """
    xx, yy = _grid_coords(shape, xx, yy)
    if mode == "hash":
        return cell_hash(xx, yy, seed) - 0.5
    if mode == "bayer":
        return (BAYER4[yy % 4, xx % 4] + 0.5) / 16.0 - 0.5
    raise ValueError("디더 방식은 'hash' 또는 'bayer': %r" % (mode,))


def levels(lum, n, gamma=1.0, cut=0.0, dither=0.0, mode="hash", shimmer=0.0, step=0,
           xx=None, yy=None, seed=0):
    """밝기 0..1 → 0..n-1 단계 (정수 배열). cut 보다 어두운 칸은 0 (빈칸).

    gamma   1 보다 작으면 어두운 쪽 단계가 늘어난다 (eyeTutorial 은 0.72)
    dither  칸마다 고정 흔들림 폭 (단계 기준). 1 이면 띠가 거의 사라진다
    shimmer step 이 바뀔 때마다 칸마다 다른 흔들림 (단계 기준). 반짝임
    """
    lum = np.asarray(lum, np.float64)
    xx, yy = _grid_coords(lum.shape, xx, yy)
    t = np.clip((lum - cut) / (1.0 - cut), 0, 1) if cut > 0 else np.clip(lum, 0, 1)
    if gamma != 1.0:
        t = t ** gamma
    x = t * (n - 1)
    if dither:
        x = x + dither_offset(lum.shape, mode, xx, yy, seed) * dither
    if shimmer:
        x = x + (cell_hash(xx, yy, seed + 7919 * (int(step) + 1)) - 0.5) * shimmer
    idx = np.clip(np.round(x), 0, n - 1).astype(np.int64)
    if cut > 0:
        idx[lum < cut] = 0
    return idx


def ramp_chars(lum, ramp=RAMPS["short"], **kw):
    """밝기 → 램프 글자 코드. 키워드는 levels() 와 같다."""
    codes = codes_of(ramp)
    return codes[levels(lum, len(codes), **kw)]


def pool_chars(lum, pools=GLYPH_POOLS, gamma=1.0, cut=0.0, dither=0.0, mode="hash", step=0,
               xx=None, yy=None, seed=0):
    """글자 풀: 밝기 단계마다 글자 묶음(pool)을 두고, 칸마다 그 묶음 안에서 하나를 고른다.

    step 이 바뀌면 같은 밝기 안에서 글자가 바뀐다 (반짝임). cut 보다 어두우면 빈칸.
    """
    lum = np.asarray(lum, np.float64)
    xx, yy = _grid_coords(lum.shape, xx, yy)
    k = len(pools)
    t = np.clip((lum - cut) / (1.0 - cut), 0, 1) if cut > 0 else np.clip(lum, 0, 1)
    if gamma != 1.0:
        t = t ** gamma
    x = t * k
    if dither:
        x = x + dither_offset(lum.shape, mode, xx, yy, seed) * dither
    level = np.clip(np.floor(x), 0, k - 1).astype(np.int64)
    width = max(len(p) for p in pools)
    table = np.zeros((k, width), np.uint32)
    sizes = np.array([len(p) for p in pools], np.int64)
    for i, p in enumerate(pools):
        table[i, :len(p)] = codes_of(p)
    pick = (np.floor(cell_hash(xx, yy, seed + 1) * width).astype(np.int64) + int(step)) % sizes[level]
    out = table[level, pick]
    out[(lum <= cut) | (t <= 0)] = 0
    return out


def edges(lum, cell_aspect=1.0):
    """밝기 필드 → (경계 세기, gx, gy). 칸이 세로로 긴 것(cell_aspect)을 보정한 실제 방향.

    gx 는 오른쪽 +, gy 는 아래쪽 + (화면 좌표).
    """
    p = np.pad(np.asarray(lum, np.float64), 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])
    gx = gx / cell_aspect          # 칸 너비가 높이보다 좁으면 가로 변화가 실제로는 더 가파르다
    return np.hypot(gx, gy), gx, gy


def edge_chars(gx, gy):
    """경계 방향 → 윤곽 글자 코드. 선은 밝기 기울기에 수직이다.

    밝은 원의 둘레라면  왼쪽·오른쪽 |, 위·아래 -, 왼쪽 위·오른쪽 아래 /, 오른쪽 위·왼쪽 아래 \\
    """
    ang = np.degrees(np.arctan2(gy, gx)) % 180.0          # 기울기 방향 0..180
    sector = np.round(ang / 45.0).astype(np.int64) % 4     # 0:가로 기울기 1:45° 2:세로 3:135°
    return codes_of(EDGE_GLYPHS)[sector]


def thin_edges(mag, gx, gy, threshold=0.0):
    """경계를 한 칸 두께로 줄인다 (기울기 방향 양옆보다 센 칸만 남김, non-maximum suppression).

    threshold: 경계 세기 하한 (mag 와 같은 단위). 돌려주는 것은 bool 마스크.
    """
    mag = np.asarray(mag, np.float64)
    p = np.pad(mag, 1, mode="constant")
    c = p[1:-1, 1:-1]
    sector = np.round((np.degrees(np.arctan2(gy, gx)) % 180.0) / 45.0).astype(np.int64) % 4
    # 기울기 방향의 앞뒤 이웃 (화면 좌표: 오른쪽 +x, 아래 +y)
    left, right = p[1:-1, :-2], p[1:-1, 2:]
    up, down = p[:-2, 1:-1], p[2:, 1:-1]
    ul, dr = p[:-2, :-2], p[2:, 2:]
    ur, dl = p[:-2, 2:], p[2:, :-2]
    a = np.select([sector == 0, sector == 1, sector == 2, sector == 3], [left, ul, up, ur])
    b = np.select([sector == 0, sector == 1, sector == 2, sector == 3], [right, dr, down, dl])
    return (c >= a) & (c >= b) & (c > threshold)
