"""글자 아틀라스와 grid → 이미지 렌더.

Pillow 로 글자 모양(알파 마스크)을 한 번만 그려 두고(글자 아틀라스),
grid 의 모든 칸을 numpy 로 한 번에 합성한다. 칸마다 파이썬 루프를 돌지 않는다.

셀 크기는 글꼴 측정이 아니라 FONT_PX 와 CELL_ASPECT 로 정한다.
그래서 같은 설정이면 어느 기기에서나 출력 해상도가 같다.
"""
import os
import warnings

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 셀 높이 = FONT_PX × LINE_HEIGHT. 1.0 이면 '_' 'g' 같은 아래로 내려가는 글자가 잘린다.
LINE_HEIGHT = 1.15
# 세로 위치를 맞출 때 기준이 되는 글자들 (위·아래 끝이 가장 먼 글자)
FIT_CHARS = "Mgjpqy_|()[]{}"

# 이름 → (파일, ttc 인덱스). 경로를 직접 넣어도 된다.
FONTS = {
    "Menlo": ("/System/Library/Fonts/Menlo.ttc", 0),
    "Menlo Bold": ("/System/Library/Fonts/Menlo.ttc", 1),
    "SF Mono": ("/System/Library/Fonts/SFNSMono.ttf", 0),
    "Courier": ("/System/Library/Fonts/Courier.ttc", 0),
}
DEFAULT_FONT = "Menlo"


def cell_size(font_px, cell_aspect):
    """셀 픽셀 크기 (너비, 높이)."""
    h = max(4, int(round(font_px * LINE_HEIGHT)))
    w = max(2, int(round(h * cell_aspect)))
    return w, h


def load_font(font, font_px):
    """글꼴 이름(FONTS 의 키) 또는 파일 경로 → Pillow 글꼴. 못 찾으면 경고 후 기본 글꼴."""
    path, index = FONTS.get(font, (font, 0))
    if os.path.isfile(path):
        return ImageFont.truetype(path, size=font_px, index=index)
    warnings.warn("글꼴을 찾지 못해 Pillow 기본 글꼴을 씁니다: %r" % (font,))
    return ImageFont.load_default(size=font_px)


class GlyphAtlas:
    """글자 코드 → (h, w) 알파 마스크 0..1. 필요한 글자만 그때 만들어 캐시한다."""

    def __init__(self, font=DEFAULT_FONT, font_px=12, cell_aspect=0.6):
        self.font_name = font
        self.font_px = int(font_px)
        self.w, self.h = cell_size(font_px, cell_aspect)
        self.font = load_font(font, self.font_px)
        self._index = {0: 0}  # 코드 → 스택 위치. 0 번은 빈칸
        self._masks = [np.zeros((self.h, self.w), np.float32)]
        self._stack = None

    def _baseline(self):
        """기준 글자들의 위·아래 끝이 셀 가운데 오도록 하는 기준선 y."""
        top, bottom = None, None
        for c in FIT_CHARS:
            box = self.font.getbbox(c, anchor="ls")  # 기준선 기준 (위는 음수)
            top = box[1] if top is None else min(top, box[1])
            bottom = box[3] if bottom is None else max(bottom, box[3])
        return (self.h - (bottom - top)) / 2.0 - top

    def _draw(self, code):
        if not hasattr(self, "_base_y"):
            self._base_y = self._baseline()
        img = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(img).text((self.w / 2.0, self._base_y), chr(code), fill=255, font=self.font, anchor="ms")
        return np.asarray(img, np.float32) / 255.0

    def ensure(self, codes):
        """codes 에 있는 글자를 아틀라스에 추가한다."""
        added = False
        for c in np.unique(codes):
            c = int(c)
            if c not in self._index:
                self._index[c] = len(self._masks)
                self._masks.append(self._draw(c))
                added = True
        if added or self._stack is None:
            self._stack = np.stack(self._masks)

    def mask(self, ch):
        """글자 하나의 마스크 (테스트·확인용)."""
        code = ord(ch) if isinstance(ch, str) else int(ch)
        self.ensure(np.array([code]))
        return self._stack[self._index[code]]

    def lookup(self, codes):
        """(rows, cols) 코드 배열 → 스택 인덱스 배열."""
        self.ensure(codes)
        keys = np.fromiter(self._index.keys(), np.int64)
        vals = np.fromiter(self._index.values(), np.int64)
        order = np.argsort(keys)
        pos = np.searchsorted(keys[order], codes.astype(np.int64))
        return vals[order][pos]

    def render(self, grid, background, bgr=False):
        """grid → (rows*h, cols*w, 3) uint8 이미지. bgr=True 면 OpenCV 창용 색 순서(파랑·초록·빨강).

        채널마다 셀 블록 단위로 모든 칸을 한꺼번에 계산한다 (rows, cols, h, w). 120×60 칸 기준 약 10ms.
        (글자 칸만 골라 계산하는 방식도 재 봤지만 흩어 쓰기가 느려 모든 경우에 3~15배 느렸다.)
        알파가 0..1 이고 배경·글자색이 0..255 라 결과도 0..255 안에 있어 clip 이 필요 없다.
        """
        rows, cols, h, w = grid.rows, grid.cols, self.h, self.w
        idx = self.lookup(grid.ch)  # 아틀라스를 먼저 준비해야 _stack 이 채워진다
        alpha = self._stack[idx]  # (rows, cols, h, w)
        bg = np.asarray(background, np.float32)
        delta = grid.rgb.astype(np.float32) - bg  # (rows, cols, 3)
        out = np.empty((rows, h, cols, w, 3), np.uint8)
        tmp = np.empty_like(alpha)
        for c in range(3):
            np.multiply(alpha, delta[:, :, c, None, None], out=tmp)
            tmp += bg[c] + 0.5
            out[..., 2 - c if bgr else c] = tmp.transpose(0, 2, 1, 3)
        return out.reshape(rows * h, cols * w, 3)


def save_png(image, path):
    """numpy RGB 이미지를 PNG 로 저장한다. 폴더가 없으면 만든다."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    Image.fromarray(np.asarray(image, np.uint8), "RGB").save(path)
    return path
