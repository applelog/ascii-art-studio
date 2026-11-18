"""Grid — cols×rows 글자 버퍼.

화면(창·이미지)과 분리되어 있어서, 작품의 frame() 은 grid 만 채우고
테스트는 이미지 없이 grid 를 그대로 비교할 수 있다.

    ch   (rows, cols) uint32   글자 코드. 0 = 빈칸(배경)
    rgb  (rows, cols, 3) uint8 글자 색
    z    (rows, cols) float32  깊이. put_z 는 더 가까운(작은 z) 글자만 남긴다

좌표: x = 열(0..cols-1, 오른쪽 +), y = 행(0..rows-1, 아래 +).
"""
import hashlib

import numpy as np

BLANK = 0


def _code(ch):
    """글자 → 코드. 한 글자 문자열이나 정수를 받는다."""
    if isinstance(ch, str):
        if len(ch) != 1:
            raise ValueError("글자는 한 글자여야 합니다: %r" % (ch,))
        return 0 if ch == " " else ord(ch)
    return int(ch)


class Grid:
    def __init__(self, cols, rows):
        if cols < 1 or rows < 1:
            raise ValueError("cols, rows 는 1 이상이어야 합니다")
        self.cols = int(cols)
        self.rows = int(rows)
        self.ch = np.zeros((self.rows, self.cols), np.uint32)
        self.rgb = np.zeros((self.rows, self.cols, 3), np.uint8)
        self.z = np.full((self.rows, self.cols), np.inf, np.float32)

    # ---------- 지우기 ----------
    def clear(self):
        self.ch.fill(0)
        self.rgb.fill(0)
        self.z.fill(np.inf)

    # ---------- 한 칸씩 ----------
    def inside(self, x, y):
        return 0 <= x < self.cols and 0 <= y < self.rows

    def put(self, x, y, ch, color):
        """(x, y) 칸에 글자 하나. 화면 밖은 무시한다. color = (r, g, b)."""
        x, y = int(x), int(y)
        if not self.inside(x, y):
            return
        self.ch[y, x] = _code(ch)
        self.rgb[y, x] = color

    def put_z(self, x, y, z, ch, color):
        """깊이 z 가 지금 칸보다 가까울 때만 놓는다 (3D 점 투영용)."""
        x, y = int(x), int(y)
        if not self.inside(x, y) or z >= self.z[y, x]:
            return
        self.z[y, x] = z
        self.ch[y, x] = _code(ch)
        self.rgb[y, x] = color

    def text(self, x, y, s, color):
        """문자열을 가로로 쓴다. 공백은 건너뛴다 (아래 글자를 지우지 않음)."""
        for k, c in enumerate(s):
            if c != " ":
                self.put(x + k, y, c, color)

    # ---------- 한 번에 (numpy) ----------
    def fill(self, mask, ch, color):
        """mask(rows, cols bool) 가 참인 칸을 한 번에 채운다.

        ch    : 한 글자 / 코드 / (rows, cols) 코드 배열
        color : (r, g, b) / (rows, cols, 3) 배열
        """
        mask = np.asarray(mask, bool)
        if isinstance(ch, (str, int, np.integer)):
            self.ch[mask] = _code(ch)
        else:
            self.ch[mask] = np.asarray(ch, np.uint32)[mask]
        col = np.asarray(color, np.uint8)
        if col.ndim == 1:
            self.rgb[mask] = col
        else:
            self.rgb[mask] = col[mask]

    # ---------- 확인용 ----------
    def to_text(self):
        """글자만 줄 단위 문자열로 (디버그·테스트용)."""
        lines = []
        for row in self.ch:
            lines.append("".join(" " if c == 0 else chr(int(c)) for c in row))
        return "\n".join(lines)

    def digest(self):
        """글자와 색 전체의 해시. 같은 그림인지 비교할 때 쓴다."""
        h = hashlib.sha1()
        h.update(self.ch.tobytes())
        h.update(self.rgb.tobytes())
        return h.hexdigest()

    def filled_ratio(self):
        """글자가 있는 칸의 비율 0..1."""
        return float((self.ch != 0).mean())
