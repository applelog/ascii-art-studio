"""F2: 글자 버퍼(grid) → 이미지 → PNG."""
import time

import numpy as np
import pytest
from PIL import Image

from asciiart.atlas import GlyphAtlas, cell_size, save_png
from asciiart.grid import Grid

BG = (10, 10, 10)
RED = (230, 40, 40)


# ---------- grid ----------
def test_put_and_bounds():
    g = Grid(5, 3)
    g.put(1, 1, "A", RED)
    g.put(-1, 0, "B", RED)   # 화면 밖은 무시
    g.put(5, 0, "C", RED)
    assert g.to_text().splitlines()[1] == " A   "
    assert tuple(g.rgb[1, 1]) == RED
    assert g.filled_ratio() == pytest.approx(1 / 15)


def test_text_skips_spaces():
    g = Grid(6, 1)
    g.text(0, 0, "XXXXXX", RED)
    g.text(0, 0, "a b", (0, 255, 0))
    assert g.to_text() == "aXbXXX"


def test_put_z_keeps_nearest():
    g = Grid(1, 1)
    g.put_z(0, 0, 5.0, "F", RED)
    g.put_z(0, 0, 2.0, "N", RED)
    g.put_z(0, 0, 9.0, "X", RED)
    assert g.to_text() == "N"


def test_fill_with_mask_and_arrays():
    g = Grid(4, 2)
    mask = np.array([[1, 0, 1, 0], [0, 1, 0, 1]], bool)
    g.fill(mask, "#", RED)
    assert g.to_text() == "# # \n # #"
    codes = np.full((2, 4), ord("o"), np.uint32)
    colors = np.zeros((2, 4, 3), np.uint8)
    colors[..., 1] = 200
    g.fill(~mask, codes, colors)
    assert g.to_text() == "#o#o\no#o#"
    assert tuple(g.rgb[0, 1]) == (0, 200, 0)


def test_digest_and_clear():
    a, b = Grid(8, 4), Grid(8, 4)
    a.text(0, 0, "same", RED)
    b.text(0, 0, "same", RED)
    assert a.digest() == b.digest()
    b.put(0, 0, "s", (1, 2, 3))
    assert a.digest() != b.digest()
    a.clear()
    assert a.filled_ratio() == 0


def test_bad_char_rejected():
    with pytest.raises(ValueError):
        Grid(2, 2).put(0, 0, "ab", RED)


# ---------- atlas / render ----------
def test_cell_size_from_settings():
    assert cell_size(12, 0.6) == (8, 14)
    assert cell_size(20, 0.5) == (12, 23)


def _ink_uncropped(atlas, ch):
    """같은 글꼴로 넉넉한 캔버스에 그렸을 때의 잉크 총량 (잘림 없음 기준)."""
    from PIL import Image, ImageDraw
    big = Image.new("L", (atlas.w * 4, atlas.h * 4), 0)
    ImageDraw.Draw(big).text((atlas.w * 2, atlas.h * 2), ch, fill=255, font=atlas.font, anchor="ms")
    return np.asarray(big, np.float32).sum() / 255.0


@pytest.mark.parametrize("px", [10, 12, 16, 24])
def test_glyphs_not_clipped(px):
    """'_' 'g' '|' 처럼 위아래로 긴 글자가 셀 경계에서 잘리지 않는다 (잉크 97% 이상 남음)."""
    a = GlyphAtlas("Menlo", px, 0.6)
    for ch in "_gjy|()[]@M":
        kept = a.mask(ch).sum() / _ink_uncropped(a, ch)
        assert kept > 0.97, "%s %.2f" % (ch, kept)


def test_render_shape_background_and_color():
    a = GlyphAtlas("Menlo", 16, 0.6)
    g = Grid(10, 4)
    g.put(3, 2, "@", RED)
    img = a.render(g, BG)
    assert img.shape == (4 * a.h, 10 * a.w, 3)
    # 빈 칸은 정확히 배경색
    assert (img[: a.h, : a.w] == BG).all()
    # 글자 칸에는 글자 색에 가까운 픽셀이 있다
    cell = img[2 * a.h:3 * a.h, 3 * a.w:4 * a.w].reshape(-1, 3).astype(int)
    assert (np.abs(cell - RED).sum(1) < 40).any()


def test_different_glyphs_differ_and_space_is_blank():
    a = GlyphAtlas("Menlo", 16, 0.6)
    assert not np.allclose(a.mask("@"), a.mask("."))
    assert a.mask("@").sum() > a.mask(".").sum()
    assert a.mask(" ").sum() == 0


def test_render_is_deterministic():
    a = GlyphAtlas("Menlo", 12, 0.6)
    g = Grid(30, 10)
    g.text(2, 3, "deterministic", RED)
    assert a.render(g, BG).tobytes() == GlyphAtlas("Menlo", 12, 0.6).render(g, BG).tobytes()


def test_missing_font_falls_back_with_warning():
    with pytest.warns(UserWarning):
        a = GlyphAtlas("/nope/NoSuchFont.ttf", 12, 0.6)
    g = Grid(3, 1)
    g.text(0, 0, "ok", RED)
    assert a.render(g, BG).shape == (a.h, 3 * a.w, 3)


def test_save_png_roundtrip(tmp_path):
    a = GlyphAtlas("Menlo", 12, 0.6)
    g = Grid(20, 5)
    g.text(1, 2, "png", RED)
    img = a.render(g, BG)
    path = save_png(img, str(tmp_path / "sub" / "f.png"))
    back = np.asarray(Image.open(path).convert("RGB"))
    assert back.shape == img.shape and (back == img).all()


def test_render_speed_full_screen():
    """160×80 칸을 전부 채워도 한 프레임 렌더가 예산 안에 든다."""
    a = GlyphAtlas("Menlo", 12, 0.6)
    g = Grid(160, 80)
    rng = np.random.RandomState(0)
    ramp = np.array([ord(c) for c in ".:-=+*#%@"], np.uint32)
    g.ch[...] = ramp[rng.randint(0, len(ramp), (80, 160))]
    g.rgb[...] = rng.randint(0, 255, (80, 160, 3))
    a.render(g, BG)  # 아틀라스 준비
    t0 = time.perf_counter()
    n = 10
    for _ in range(n):
        a.render(g, BG)
    ms = (time.perf_counter() - t0) / n * 1000
    print("render 160x80: %.1f ms" % ms)
    assert ms < 40


def test_bgr_render_is_same_picture_with_swapped_channels():
    a = GlyphAtlas("Menlo", 12, 0.6)
    g = Grid(20, 4)
    g.text(1, 1, "rgb", (250, 120, 10))
    rgb = a.render(g, (5, 30, 60))
    bgr = a.render(g, (5, 30, 60), bgr=True)
    assert (bgr[..., ::-1] == rgb).all()
