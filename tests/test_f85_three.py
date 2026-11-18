"""F8.5: 3D 도구 (카메라·SDF·레이마칭·빛·점·선·OBJ) + 무거운 작품용 작업자 프로세스."""
import importlib.util
import math
import os
import time

import numpy as np
import pytest

from asciiart import three as T
from asciiart.grid import Grid
from asciiart.player import PieceRenderer
from asciiart.stages import link_report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "examples", "f85_demo.py")
SMALL = dict(COLS=44, ROWS=22, FONT_PX=8, INTRO_SECONDS=0.4, INTRO_HOLD=0.1, LOOP_SECONDS=0.6, POINTS=30,
             MAX_STEPS=40, FINAL_LOOPS=1)
CUBE = """v -1 -1 -1
v 1 -1 -1
v 1 1 -1
v -1 1 -1
v -1 -1 1
v 1 -1 1
v 1 1 1
v -1 1 1
f 1 4 3 2
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""


def load(**over):
    spec = importlib.util.spec_from_file_location("f85demo", DEMO)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ns = vars(m)
    ns.update(over)
    return ns


# ---------- 회전 · 카메라 ----------
def test_rotations_are_orthonormal():
    R = T.rot_euler(0.3, -1.1, 2.0)
    assert np.allclose(R @ R.T, np.eye(3)) and np.isclose(np.linalg.det(R), 1)
    assert np.allclose(T.rot_y(math.pi / 2) @ [1, 0, 0], [0, 0, -1])


def test_camera_rays_and_projection():
    cam = T.Camera((0, 0, -5), (0, 0, 0), fov=40)
    ro, rd = cam.rays(np.array([[0.0]]), np.array([[0.0]]))
    assert np.allclose(rd[0, 0], [0, 0, 1])                          # 화면 가운데 = 정면
    col, row, z, vis = cam.project(np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, -6]]), 80, 40, 0.6)
    assert np.isclose(col[0], 40) and np.isclose(row[0], 20) and np.isclose(z[0], 5)
    assert col[1] > 40 and row[2] < 20                               # 오른쪽은 오른쪽, 위는 위
    assert not vis[3]                                                # 카메라 뒤는 안 보임


# ---------- SDF ----------
def test_sdf_shapes_and_ops():
    p = np.array([[0, 0, 0], [2, 0, 0], [1, 1, 1]], np.float64)
    assert np.allclose(T.sphere(p, 1), [-1, 1, math.sqrt(3) - 1])
    assert np.isclose(T.box(np.array([[2.0, 0, 0]]), (1, 1, 1))[0], 1)
    assert np.isclose(T.torus(np.array([[1.0, 0, 0]]), 1, 0.25)[0], -0.25)
    assert np.isclose(T.plane(np.array([[0, 2.0, 0]]), (0, 1, 0), 0)[0], 2)
    a, b = np.array([0.3]), np.array([0.5])
    assert T.smooth_union(a, b, 0.5)[0] <= T.union(a, b)[0]
    assert T.subtract(np.array([-1.0]), np.array([-0.5]))[0] == 0.5
    q = T.local(np.array([[1.0, 0, 0]]), T.rot_y(math.pi / 2), (0, 0, 0))
    assert np.allclose(np.abs(q), [[0, 0, 1]], atol=1e-12)


def test_raymarch_distance_and_normal():
    cam = T.Camera((0, 0, -4), (0, 0, 0), fov=40)
    ro, rd = cam.rays(np.array([[0.0, 3.0]]), np.array([[0.0, 0.0]]))
    t, hit = T.raymarch(lambda p: T.sphere(p, 1), ro, rd)
    assert hit[0, 0] and abs(t[0, 0] - 3) < 1e-2 and not hit[0, 1]
    n = T.normal(lambda p: T.sphere(p, 1), np.array([[0, 0, -1.0]]))
    assert np.allclose(n, [[0, 0, -1]], atol=1e-3)


# ---------- 렌더 · 빛 ----------
def _sphere_render(**kw):
    cam = T.Camera((0, 0, -4), (0, 0, 0), fov=40)
    return T.render_sdf(lambda p: T.sphere(p, 1), cam, 60, 30, 0.6, **kw)


def test_render_sphere_is_round_and_lit_toward_light():
    r = _sphere_render(light_dir=(-1, 0, -0.3))
    ys, xs = np.nonzero(r.mask > 0.5)
    assert abs((xs.ptp() + 1) * 0.6 / (ys.ptp() + 1) - 1) < 0.08    # 화면에서 둥글다
    lum = r.rgb[..., 0]
    assert lum[15, 22] > lum[15, 38]                                  # 왼쪽에서 빛 → 왼쪽이 밝다
    assert np.isinf(r.depth[0, 0]) and abs(r.depth[15, 30] - 3) < 0.05


def test_shadow_darkens_floor_under_object_and_fog_dims_far():
    cam = T.Camera((0, 2.5, -5), (0, 0, 0), fov=45)
    sdf = lambda p: T.union(T.sphere(p - [0, 0.5, 0], 0.6), T.plane(p, (0, 1, 0), 0.4))
    kw = dict(light_dir=(0, 1, 0), ambient=0.0)
    lit = T.render_sdf(sdf, cam, 60, 30, 0.6, **kw)
    sh = T.render_sdf(sdf, cam, 60, 30, 0.6, shadows=True, **kw)
    floor = np.isfinite(lit.depth) & (lit.depth > 5.0)
    assert (sh.rgb[..., 0] < lit.rgb[..., 0] - 0.2).sum() > 5         # 그림자가 생긴 바닥 칸이 있다
    fog = T.render_sdf(sdf, cam, 60, 30, 0.6, fog=1.0, fog_start=4.0, **kw)
    assert fog.rgb[..., 0][floor].mean() < lit.rgb[..., 0][floor].mean()


# ---------- 점 · 선 · OBJ ----------
def test_points_nearest_wins_and_hidden_behind_surface():
    cam = T.Camera((0, 0, -5), (0, 0, 0), fov=40)
    g = Grid(40, 20)
    T.draw_points(g, np.array([[0, 0, 1.0], [0, 0, -1.0]]), cam, 0.6, np.array([ord("F"), ord("N")]), (255, 255, 255))
    assert "N" in g.to_text() and "F" not in g.to_text()             # 같은 칸이면 가까운 점
    g2 = Grid(40, 20)
    g2.z[...] = 4.5                                                   # 거리 4.5 에 벽이 있다고 가정
    assert T.draw_points(g2, np.array([[0, 0, 1.0]]), cam, 0.6, "X", (255, 0, 0)) == 0   # 벽 뒤 점은 가려짐


def test_line_chars_follow_direction():
    assert chr(T.line_char(1, 0)) == "-" and chr(T.line_char(0, 1)) == "|"
    assert chr(T.line_char(1, 1)) == "\\" and chr(T.line_char(-1, 1)) == "/"
    cam = T.Camera((0, 0, -5), (0, 0, 0), fov=40)
    g = Grid(60, 30)
    T.draw_line3d(g, (-1, 0, 0), (1, 0, 0), cam, 0.6, (255, 255, 255))
    assert set(g.to_text().replace(" ", "").replace("\n", "")) == {"-"}


def test_obj_load_edges_and_raster():
    verts, faces = T.load_obj(CUBE)
    assert verts.shape == (8, 3) and len(faces) == 6
    assert len(T.mesh_edges(faces)) == 12 and len(T.triangles(faces)) == 12
    cam = T.Camera((2.5, 2.0, -4.0), (0, 0, 0), fov=45)
    r = T.raster_mesh(verts, faces, cam, 60, 30, 0.6, light_dir=(-0.3, 1, -0.4))
    assert r.mask.sum() > 50 and np.isfinite(r.depth[r.mask > 0]).all()
    shades = np.unique(np.round(r.rgb[r.mask > 0][:, 0], 3))
    assert 2 <= len(shades) <= 3                                      # 보이는 면마다 단색 음영
    g = Grid(60, 30)
    T.wireframe(g, verts, T.mesh_edges(faces), cam, 0.6, (255, 255, 255))
    assert (g.ch != 0).sum() > 30
    with pytest.raises(ValueError):
        T.load_obj("# 빈 파일\n")


# ---------- 데모 · 작업자 프로세스 ----------
def test_demo_links_and_motion():
    ns = load(**SMALL)
    assert all(same for _, same, _ in link_report(ns))
    r = PieceRenderer(ns, part="motion")
    assert r.grid_at(0).digest() != r.grid_at(r.n // 3).digest()


def test_worker_processes_match_local_grids():
    """작업자 프로세스가 계산한 grid = 메인에서 계산한 grid."""
    ns = load(**SMALL)
    from asciiart.pool import GridPool
    r = PieceRenderer(ns)
    r.pool = GridPool(r, workers=2)
    try:
        deadline = time.time() + 30
        while time.time() < deadline and not all(r.cached(k) for k in range(12)):
            r.pool.request(range(0, 12))            # 한 번에 맡기는 양이 제한돼 있어 재생처럼 계속 요청
            time.sleep(0.05)
        assert all(r.cached(k) for k in range(12)), r.pool.errors
    finally:
        r.pool.close()
        r.pool = None
    local = PieceRenderer(load(**SMALL))
    for k in (0, 5, 11):
        assert r.grid_at(k).digest() == local.grid_at(k).digest()


def test_pool_failure_falls_back_to_local(tmp_path):
    """작업자가 작품을 못 불러와도 재생·저장은 메인 계산으로 계속된다."""
    from asciiart.pool import GridPool
    ns = load(**SMALL)
    bad = tmp_path / "broken.py"
    bad.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
    ns["__file__"] = str(bad)
    r = PieceRenderer(ns)
    r.pool = GridPool(r, workers=1)
    try:
        r.pool.request(range(1, 4))
        g = r.grid_at(2)                                             # 기다리다가(최대 몇 초) 직접 계산
        assert g.digest() == PieceRenderer(load(**SMALL)).grid_at(2).digest()
    finally:
        r.pool.close()
