"""F8 데모용 샘플 이미지를 코드로 그린다 (사진이 아니라 저작권 걱정 없음).

    python examples/assets/make_sample_cat.py   → cat.png (투명 배경), cat_on_paper.jpg (밝은 종이 배경)
"""
# ===== 설정 =====
WIDTH, HEIGHT  = 800, 900              # 이미지 크기 px
SS             = 2                     # 테두리를 부드럽게 하려고 몇 배로 그린 뒤 줄일지
FUR_RGB        = (232, 142, 58)        # 털 색 (주황)
STRIPE_RGB     = (168, 86, 34)         # 줄무늬 색
BELLY_RGB      = (248, 218, 178)       # 배·입가 밝은 털
EYE_RGB        = (176, 214, 62)        # 눈 색
PUPIL_RGB      = (20, 20, 16)          # 눈동자
NOSE_RGB       = (220, 120, 130)       # 코
PAPER_RGB      = (242, 239, 230)       # JPG 배경 (종이)
STRIPE_FREQ    = 0.055                 # 줄무늬 촘촘함
LIGHT_FALLOFF  = 0.45                  # 왼쪽 위에서 오른쪽 아래로 어두워지는 정도
# ===== 코드 =====
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def ellipse(X, Y, cx, cy, rx, ry):
    return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 <= 1


def triangle(X, Y, a, b, c):
    def side(p, q):
        return (X - q[0]) * (p[1] - q[1]) - (p[0] - q[0]) * (Y - q[1])
    d1, d2, d3 = side(a, b), side(b, c), side(c, a)
    neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
    pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
    return ~(neg & pos)


def tail(X, Y, s):
    mask = np.zeros(X.shape, bool)
    for t in np.linspace(0, 1, 60):
        cx = (600 + 130 * np.sin(t * 2.2)) * s
        cy = (790 - 330 * t) * s
        mask |= ellipse(X, Y, cx, cy, (40 - 12 * t) * s, (40 - 12 * t) * s)
    return mask


def draw():
    s = SS
    H, W = HEIGHT * s, WIDTH * s
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    body = ellipse(X, Y, 420 * s, 610 * s, 215 * s, 235 * s)
    head = ellipse(X, Y, 400 * s, 300 * s, 155 * s, 140 * s)
    ears = triangle(X, Y, (280 * s, 220 * s), (245 * s, 85 * s), (370 * s, 170 * s)) | \
        triangle(X, Y, (520 * s, 220 * s), (565 * s, 90 * s), (440 * s, 170 * s))
    paws = ellipse(X, Y, 340 * s, 835 * s, 62 * s, 38 * s) | ellipse(X, Y, 480 * s, 835 * s, 62 * s, 38 * s)
    cat = body | head | ears | paws | tail(X, Y, s)

    rgb = np.zeros((H, W, 3), np.float32)
    rgb[...] = FUR_RGB
    stripes = (np.sin((X * 0.35 + Y) * STRIPE_FREQ / s) > 0.55) & ~paws
    rgb[stripes] = STRIPE_RGB
    belly = ellipse(X, Y, 410 * s, 680 * s, 110 * s, 170 * s) | ellipse(X, Y, 400 * s, 360 * s, 70 * s, 45 * s)
    rgb[belly | paws] = BELLY_RGB
    eyes = ellipse(X, Y, 345 * s, 290 * s, 26 * s, 30 * s) | ellipse(X, Y, 455 * s, 290 * s, 26 * s, 30 * s)
    rgb[eyes] = EYE_RGB
    pupils = ellipse(X, Y, 345 * s, 290 * s, 7 * s, 24 * s) | ellipse(X, Y, 455 * s, 290 * s, 7 * s, 24 * s)
    rgb[pupils] = PUPIL_RGB
    nose = triangle(X, Y, (385 * s, 340 * s), (415 * s, 340 * s), (400 * s, 358 * s))
    rgb[nose] = NOSE_RGB
    light = 1 - LIGHT_FALLOFF * np.clip((X / W + Y / H) / 2, 0, 1)
    rgb = rgb * light[..., None]

    rgba = np.zeros((H, W, 4), np.float32)
    rgba[..., :3] = rgb * cat[..., None]
    rgba[..., 3] = cat * 255
    img = Image.fromarray(rgba.clip(0, 255).astype(np.uint8), "RGBA").resize((WIDTH, HEIGHT), Image.LANCZOS)
    return img


if __name__ == "__main__":
    img = draw()
    img.save(os.path.join(HERE, "cat.png"))
    paper = Image.new("RGBA", img.size, PAPER_RGB + (255,))
    paper.alpha_composite(img)
    paper.convert("RGB").save(os.path.join(HERE, "cat_on_paper.jpg"), quality=92)
    print("saved", os.path.join(HERE, "cat.png"), "and cat_on_paper.jpg", img.size)
