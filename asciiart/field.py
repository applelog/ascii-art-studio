"""이미지 → 필드 (작품에서 사진·그림을 쓸 때).

    make_field(이미지, cols, ...)       이미지를 칸 단위 필드로 줄인다 (밝기·투명도·윤곽·원래 색·팔레트)
    save_field / ImageField.load      field.json 저장·읽기
    Placement(field, COLS, ROWS, …)   이미지 비율을 지켜 화면에 놓기 (contain: 다 보이게, cover: 꽉 차게)
    draw_field(grid, field, u, v, …)  밝기 글자 · 윤곽 방향 글자 · 원래 색/팔레트 색으로 그리기

원본 이미지는 작품 폴더에 복사하지 않는다. 줄인 필드 값만 field.json 에 남는다.
필드 해상도는 칸 수 × ss (ss=2 면 칸보다 2배 촘촘) — 이미지를 흔들거나 키울 때 부드럽다.
"""
import json
import os

import numpy as np
from PIL import Image, ImageOps

from .color import palette_color
from .ramp import RAMPS, edge_chars, edges, ramp_chars

MAX_PIXELS = 40_000_000      # 너무 큰 이미지는 거부
MAX_CELLS = 400_000          # 필드 점 수 상한 (cols × rows × ss²)
FIELD_VERSION = 2


class FieldError(ValueError):
    pass


# ---------- 이미지 → 필드 ----------
def _open(image):
    if isinstance(image, Image.Image):
        img = image
    else:
        if not os.path.isfile(image):
            raise FieldError("파일이 없습니다: %s" % image)
        try:
            img = Image.open(image)
        except Exception as e:  # noqa: BLE001
            raise FieldError("이미지를 열 수 없습니다: %s" % e)
    if img.width * img.height > MAX_PIXELS:
        raise FieldError("이미지가 너무 큽니다 (%dx%d)" % (img.width, img.height))
    return ImageOps.exif_transpose(img).convert("RGBA")


def _kmeans(colors, weights, k, seed=0, iters=12):
    rng = np.random.RandomState(seed)
    k = max(1, min(k, len(colors)))
    p = weights / weights.sum() if weights.sum() > 0 else None
    centers = colors[rng.choice(len(colors), k, replace=False, p=p)].copy()
    for _ in range(iters):
        lab = ((colors[:, None, :] - centers[None, :, :]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            m = lab == j
            if m.any():
                w = weights[m][:, None]
                centers[j] = (colors[m] * w).sum(0) / max(w.sum(), 1e-6)
    return centers


def make_field(image, cols, rows=0, cell_aspect=0.6, ss=1, palette=5, bg_threshold=0.12):
    """이미지 → 필드 dict.

    rows=0 이면 이미지 비율과 칸 비율로 자동. ss: 칸보다 몇 배 촘촘하게 (1~4).
    투명도가 있는 PNG 는 투명도를, 없으면 가장자리 배경색과의 차이를 피사체 마스크(alpha)로 쓴다.
    """
    img = _open(image)
    w, h = img.size
    ss = int(max(1, min(4, ss)))
    rows = rows or max(4, int(round(cols * (h / float(w)) * cell_aspect)))
    W, H = cols * ss, rows * ss
    if cols < 8 or rows < 4 or W * H > MAX_CELLS:
        raise FieldError("필드 크기가 범위를 벗어납니다 (%dx%d × ss %d)" % (cols, rows, ss))
    rgba = np.asarray(img).astype(np.float32) / 255.0
    has_alpha = (rgba[..., 3] < 250 / 255.0).mean() > 0.01

    # 투명도를 반영한 평균: 투명한 곳의 (보통 검은) 색이 가장자리에 섞이지 않게
    def box(arr):
        return np.asarray(Image.fromarray(arr.astype(np.float32), "F").resize((W, H), Image.BOX), np.float32)

    a_small = box(rgba[..., 3])
    rgb = np.stack([box(rgba[..., c] * rgba[..., 3]) for c in range(3)], -1)
    rgb = np.where(a_small[..., None] > 1e-4, rgb / np.maximum(a_small[..., None], 1e-4), 0)
    rgb = np.clip(rgb, 0, 1)

    if has_alpha:
        alpha = a_small
    else:
        border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
        bg = np.median(border, axis=0)
        diff = np.sqrt(((rgb - bg) ** 2).sum(-1))
        alpha = np.clip((diff - bg_threshold) / max(bg_threshold, 1e-3), 0, 1)

    lum = 0.30 * rgb[..., 0] + 0.60 * rgb[..., 1] + 0.10 * rgb[..., 2]
    # 윤곽: 밝기 경계와 피사체 바깥선 중 더 센 쪽.
    # 방향은 필드 한 점의 실제 가로/세로 비율(원본 픽셀 기준)로 보정한다 (rows 를 직접 정해도 맞게)
    point_aspect = (w / float(W)) / (h / float(H))
    m1, gx1, gy1 = edges(lum, point_aspect)
    m2, gx2, gy2 = edges(alpha, point_aspect)
    use2 = m2 > m1
    mag = np.where(use2, m2, m1)
    gx, gy = np.where(use2, gx2, gx1), np.where(use2, gy2, gy1)
    edge = np.clip(mag / (np.percentile(mag, 99) + 1e-6), 0, 1)
    angle = np.arctan2(gy, gx)

    flat = rgb.reshape(-1, 3)
    # 대표 색은 피사체에서만 뽑는다 (투명 배경·종이 배경이 팔레트에 섞이지 않게)
    subject = alpha.reshape(-1) > 0.5
    pick = subject if subject.sum() >= max(palette, 1) * 4 else np.ones_like(subject)
    centers = _kmeans(flat[pick].astype(np.float64), alpha.reshape(-1)[pick].astype(np.float64) + 1e-3, palette)
    centers = centers[np.argsort(0.30 * centers[:, 0] + 0.60 * centers[:, 1] + 0.10 * centers[:, 2])]
    idx = ((flat[:, None, :] - centers[None, :, :]) ** 2).sum(-1).argmin(1)

    def r3(x):
        return [round(float(v), 3) for v in np.asarray(x).reshape(-1)]

    return {
        "version": FIELD_VERSION, "cols": cols, "rows": rows, "ss": ss, "cell_aspect": cell_aspect,
        "src_size": [w, h], "alpha_from": "png" if has_alpha else "border-diff",
        "lum": r3(lum), "alpha": r3(alpha), "edge": r3(edge), "angle": r3(angle),
        "rgb": [int(round(v * 255)) for v in rgb.reshape(-1)],
        "palette": ["#%02X%02X%02X" % tuple(int(round(c * 255)) for c in col) for col in centers],
        "colorIndex": [int(i) for i in idx],
    }


def save_field(field, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(field, f, separators=(",", ":"))
    return path


# ---------- 필드 쓰기 ----------
def _hex(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


class ImageField:
    """field.json → numpy 배열들 (H = rows×ss, W = cols×ss)."""

    def __init__(self, d):
        ss = int(d.get("ss", 1))
        self.H, self.W = int(d["rows"]) * ss, int(d["cols"]) * ss
        shape = (self.H, self.W)
        self.lum = np.asarray(d["lum"], np.float32).reshape(shape)
        self.alpha = np.asarray(d["alpha"], np.float32).reshape(shape)
        self.edge = np.asarray(d["edge"], np.float32).reshape(shape)
        self.angle = np.asarray(d["angle"], np.float32).reshape(shape)
        self.palette = np.asarray([_hex(c) for c in d["palette"]], np.uint8)
        self.index = np.asarray(d["colorIndex"], np.int64).reshape(shape)
        if "rgb" in d:
            self.rgb = np.asarray(d["rgb"], np.uint8).reshape(shape + (3,))
        else:                                                # version 1: 팔레트 색으로 대신
            self.rgb = self.palette[self.index]
        w, h = d.get("src_size", [self.W, self.H / float(d.get("cell_aspect", 0.6))])
        self.aspect = float(w) / float(h)                    # 원본 이미지 가로/세로
        self.alpha_from = d.get("alpha_from", "?")

    @classmethod
    def load(cls, path):
        with open(path) as f:
            return cls(json.load(f))

    def sample(self, name, u, v):
        """u (0 왼→1 오른), v (0 위→1 아래) 에서 값을 부드럽게 읽는다. 이미지 밖은 0.

        name: "lum" | "alpha" | "edge" | "rgb" (bilinear),  "angle" | "index" (가장 가까운 점)
        """
        arr = getattr(self, name)
        u, v = np.asarray(u, np.float64), np.asarray(v, np.float64)
        x, y = u * self.W - 0.5, v * self.H - 0.5
        outside = (u < 0) | (u > 1) | (v < 0) | (v > 1)
        if name in ("angle", "index"):
            xi = np.clip(np.round(x).astype(np.int64), 0, self.W - 1)
            yi = np.clip(np.round(y).astype(np.int64), 0, self.H - 1)
            out = arr[yi, xi]
            return np.where(outside, 0, out)
        x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
        fx, fy = x - x0, y - y0
        def at(xx, yy):
            return arr[np.clip(yy, 0, self.H - 1), np.clip(xx, 0, self.W - 1)].astype(np.float64)
        if arr.ndim == 3:
            fx, fy = fx[..., None], fy[..., None]
        top = at(x0, y0) * (1 - fx) + at(x0 + 1, y0) * fx
        bot = at(x0, y0 + 1) * (1 - fx) + at(x0 + 1, y0 + 1) * fx
        out = top * (1 - fy) + bot * fy
        return np.where(outside[..., None] if arr.ndim == 3 else outside, 0, out)


class Placement:
    """이미지를 화면에 놓는 방법. 화면 좌표는 칸 높이 단위 (가로 = 칸 수 × CELL_ASPECT).

    fit "contain": 이미지가 다 보이게 / "cover": 화면을 꽉 채우게
    scale: 그 크기의 배수,  cx, cy: 이미지 중심의 화면 위치 (0..1)
    """

    def __init__(self, field, cols, rows, cell_aspect, fit="contain", scale=1.0, cx=0.5, cy=0.5):
        self.cols, self.rows, self.cell_aspect = cols, rows, cell_aspect
        gw, gh = cols * cell_aspect, float(rows)
        a = field.aspect
        h = min(gh, gw / a) if fit == "contain" else max(gh, gw / a)
        if fit not in ("contain", "cover"):
            raise FieldError("fit 은 'contain' 또는 'cover': %r" % (fit,))
        self.h = h * scale
        self.w = self.h * a
        self.left = cx * gw - self.w / 2
        self.top = cy * gh - self.h / 2

    def uv(self, xp, yp):
        """화면 좌표(칸 높이 단위) → 이미지 좌표 u, v."""
        return (np.asarray(xp) - self.left) / self.w, (np.asarray(yp) - self.top) / self.h

    def cells(self):
        """모든 칸 중심의 u, v."""
        yy, xx = np.mgrid[0:self.rows, 0:self.cols]
        return self.uv((xx + 0.5) * self.cell_aspect, yy + 0.5)


def draw_field(grid, field, u, v, ramp=RAMPS["short"], brightness="lum", alpha_cut=0.5, cut=0.04, gamma=1.0,
               dither=1.0, seed=0, color="original", min_color=0.3, edge_cut=None, edge_rgb=None, cell_aspect=0.6,
               shimmer=0.0, step=0):
    """필드를 grid 에 그린다 (피사체 마스크 안쪽만).

    brightness "lum"     밝은 곳일수록 진한 글자
               "inverse" 어두운 곳일수록 진한 글자 (밝은 바탕에 어두운 피사체를 그릴 때)
               "alpha"   피사체 전체를 같은 진하기로 (실루엣)
    color      "original" 원래 색 / "palette" 대표 색 / (r, g, b) 한 색
    edge_cut   주면 윤곽 세기가 이 값을 넘는 칸에 방향 글자 | / - \\ 를 덮어 그린다
    shimmer, step  같은 밝기 안에서 글자가 바뀌는 반짝임 (루프면 step 을 phase 의 정수 단계로)
    돌려주는 것: (피사체 안쪽 마스크, 윤곽 마스크)
    """
    alpha = field.sample("alpha", u, v)
    inside = alpha >= alpha_cut
    if brightness == "lum":
        lum = field.sample("lum", u, v)
    elif brightness == "inverse":
        lum = 1 - field.sample("lum", u, v)
    elif brightness == "alpha":
        lum = alpha
    else:
        raise FieldError("brightness 는 'lum' · 'inverse' · 'alpha': %r" % (brightness,))
    yy, xx = np.mgrid[0:grid.rows, 0:grid.cols]
    codes = ramp_chars(lum, ramp, cut=cut, gamma=gamma, dither=dither, xx=xx, yy=yy, seed=seed,
                       shimmer=shimmer, step=step)
    if isinstance(color, str) and color == "original":
        rgb = field.sample("rgb", u, v)
        peak = rgb.max(-1, keepdims=True)
        lift = np.where(peak > 0, np.maximum(peak, min_color * 255) / np.maximum(peak, 1e-9), 1)
        rgb = np.clip(rgb * lift, 0, 255).round().astype(np.uint8)
    elif isinstance(color, str) and color == "palette":
        rgb = field.palette[field.sample("index", u, v).astype(np.int64)]
    else:
        rgb = palette_color(lum, [color], 0)
    grid.fill(inside & (codes != 0), codes, rgb)
    on = np.zeros(inside.shape, bool)
    if edge_cut is not None:
        e = field.sample("edge", u, v)
        ang = field.sample("angle", u, v)
        on = (e >= edge_cut) & (alpha > 0.05)
        glyph = edge_chars(np.cos(ang), np.sin(ang))
        grid.fill(on, glyph, edge_rgb if edge_rgb is not None else rgb)
    return inside, on
