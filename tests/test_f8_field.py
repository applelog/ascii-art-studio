"""F8: 이미지 입력 — 이미지 → 필드, 배치, 그리기, 명령."""
import importlib.util
import json
import os
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image, ImageDraw

from asciiart.field import FieldError, ImageField, Placement, draw_field, make_field, save_field
from asciiart.grid import Grid
from asciiart.player import PieceRenderer
from asciiart.stages import link_report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_PNG = os.path.join(ROOT, "examples", "assets", "cat.png")
CAT_JPG = os.path.join(ROOT, "examples", "assets", "cat_on_paper.jpg")
DEMO = os.path.join(ROOT, "examples", "f8_demo.py")


def disc_image(size=(400, 300), r=100, transparent=True):
    """가운데 흰 원 (투명 배경 또는 검은 배경)."""
    mode, bg = ("RGBA", (0, 0, 0, 0)) if transparent else ("RGB", (0, 0, 0))
    img = Image.new(mode, size, bg)
    cx, cy = size[0] // 2, size[1] // 2
    ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255) if transparent else (255, 255, 255))
    return img


# ---------- 이미지 → 필드 ----------
def test_field_shapes_and_ss():
    f = ImageField(make_field(CAT_PNG, 60, 30, 0.6, ss=2))
    assert (f.H, f.W) == (60, 120) and f.rgb.shape == (60, 120, 3)
    for name in ("lum", "alpha", "edge"):
        a = getattr(f, name)
        assert a.min() >= 0 and a.max() <= 1


def test_alpha_from_png_and_from_paper_background_agree():
    a = make_field(CAT_PNG, 80, 40, 0.6)
    b = make_field(CAT_JPG, 80, 40, 0.6)
    assert a["alpha_from"] == "png" and b["alpha_from"] == "border-diff"
    ma = np.asarray(a["alpha"]) > 0.5
    mb = np.asarray(b["alpha"]) > 0.5
    iou = (ma & mb).sum() / float((ma | mb).sum())
    assert iou > 0.85                                          # 배경색 차이로도 피사체를 거의 같게 분리


def test_transparent_edges_do_not_turn_dark():
    """투명 배경 PNG: 가장자리 칸 색이 검게 번지지 않는다 (투명도 반영 평균)."""
    f = ImageField(make_field(disc_image(), 40, 20, 0.6))
    edge_cells = (f.alpha > 0.15) & (f.alpha < 0.85)
    assert edge_cells.sum() > 5
    assert f.lum[edge_cells].min() > 0.9                       # 흰 원의 가장자리는 여전히 흰색


def test_palette_comes_from_subject_only():
    f = make_field(CAT_PNG, 80, 40, 0.6, palette=5)
    lums = [0.30 * int(c[1:3], 16) + 0.60 * int(c[3:5], 16) + 0.10 * int(c[5:7], 16) for c in f["palette"]]
    assert min(lums) > 40                                       # 투명 배경의 검정이 섞이지 않음


def test_edge_directions_with_forced_rows():
    """rows 를 직접 정해 필드 칸 비율이 달라도 윤곽 방향은 맞다 (원의 위·아래 '-', 옆 '|')."""
    from asciiart.ramp import edge_chars
    f = ImageField(make_field(disc_image((400, 400), 150), 40, 40, 0.6))     # 일부러 정사각 칸 수
    g = edge_chars(np.cos(f.angle), np.sin(f.angle))
    strong = f.edge > 0.5
    ys, xs = np.nonzero(strong)
    top = ys.argmin()
    left = xs.argmin()
    assert chr(g[ys[top], xs[top]]) == "-" and chr(g[ys[left], xs[left]]) == "|"


def test_errors_for_missing_and_huge():
    with pytest.raises(FieldError):
        make_field("/nope/x.png", 40)
    with pytest.raises(FieldError):
        make_field(CAT_PNG, 4000, 2000, ss=4)


def test_save_load_roundtrip_and_version1(tmp_path):
    d = make_field(CAT_PNG, 40, 20, 0.6)
    p = save_field(d, str(tmp_path / "f.json"))
    f = ImageField.load(p)
    assert f.rgb.shape == (20, 40, 3) and abs(f.aspect - 800 / 900.0) < 1e-6
    old = {k: v for k, v in d.items() if k not in ("rgb", "ss", "src_size", "alpha_from")}
    old["version"] = 1
    f1 = ImageField(old)                                        # 예전 형식: 색은 팔레트로 대신
    assert f1.rgb.shape == (20, 40, 3)


# ---------- 읽기 · 배치 · 그리기 ----------
def test_sample_bilinear_and_outside():
    f = ImageField(make_field(disc_image(), 40, 20, 0.6))
    assert f.sample("alpha", 0.5, 0.5) > 0.99
    assert f.sample("alpha", -0.1, 0.5) == 0 and f.sample("lum", 0.5, 1.2) == 0
    mid = f.sample("alpha", np.array([0.5, 0.5]), np.array([0.5, 0.5]))
    assert mid.shape == (2,)
    assert f.sample("rgb", 0.5, 0.5).shape == (3,)


def test_placement_contain_and_cover():
    f = ImageField(make_field(CAT_PNG, 60, 30, 0.6))
    c = Placement(f, 120, 60, 0.6, "contain")
    u, v = c.cells()
    assert u.min() < 0 and v.min() > -0.02 and v.max() < 1.02  # 세로에 맞추고 가로로 여백
    cv = Placement(f, 120, 60, 0.6, "cover")
    u, v = cv.cells()
    assert u.min() >= 0 and u.max() <= 1 and v.min() >= 0 and v.max() <= 1   # 화면 전체가 이미지 안
    with pytest.raises(FieldError):
        Placement(f, 120, 60, 0.6, "stretch")


def test_draw_field_modes_and_edges():
    f = ImageField(make_field(CAT_PNG, 60, 30, 0.6, ss=2))
    u, v = Placement(f, 80, 40, 0.6).cells()
    g = Grid(80, 40)
    inside, edge = draw_field(g, f, u, v, edge_cut=0.4, edge_rgb=(255, 0, 0))
    assert inside.sum() > 200 and edge.sum() > 30
    assert ((g.ch != 0) & ~inside & ~edge).sum() == 0           # 피사체 밖에는 그리지 않음
    assert (g.rgb[edge] == (255, 0, 0)).all()
    assert set(chr(c) for c in np.unique(g.ch[edge])) <= set("|/-\\")
    g2 = Grid(80, 40)
    draw_field(g2, f, u, v, brightness="alpha", color=(10, 200, 30))
    assert (g2.ch[inside] != 0).mean() > 0.95                   # 실루엣: 안쪽이 거의 다 찬다
    with pytest.raises(FieldError):
        draw_field(Grid(80, 40), f, u, v, brightness="nope")


# ---------- 명령 ----------
def test_tool_cli(tmp_path):
    out = str(tmp_path / "f.json")
    tool = os.path.join(ROOT, "tools", "image_to_field.py")
    r = subprocess.run([sys.executable, "-I", tool, CAT_JPG, "--out", out, "--cols", "50", "--ss", "2"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "border-diff" in r.stdout
    assert json.load(open(out))["ss"] == 2
    r = subprocess.run([sys.executable, "-I", tool, "/nope.png", "--out", out], capture_output=True, text=True)
    assert r.returncode == 1 and "파일이 없습니다" in r.stderr


# ---------- 데모 작품 ----------
def load_demo(**over):
    spec = importlib.util.spec_from_file_location("f8demo", DEMO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ns = vars(m)
    ns.update(over)
    return ns


def test_demo_links_and_breathing():
    ns = load_demo()
    assert all(same for _, same, _ in link_report(ns))
    r = PieceRenderer(ns, part="motion")
    assert r.grid_at(0).digest() != r.grid_at(r.n // 4).digest()        # 숨쉬기: 1/4 지점에서 가장 큼
    still = PieceRenderer(load_demo(), part="scene").grid_at(0)
    assert 0.15 < still.filled_ratio() < 0.6
