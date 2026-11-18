"""3D 도구 — 3D 공간의 물체·카메라·빛을 계산해 글자 칸에 그린다 ("돌아가는 ASCII 도넛" 방식).

좌표: x 오른쪽, y 위, z 화면 안쪽 (카메라가 +z 를 보면 +x 가 화면 오른쪽).

    Camera(위치, 바라볼 곳, fov)          광선 만들기(rays) · 3D 점을 화면 칸으로(project)
    sphere · box · round_box · torus · cylinder · capsule · plane      SDF 도형
    union · smooth_union · subtract · intersect · local                합치기 · 변환
    render_sdf(sdf, camera, …)            레이마칭 + 빛 (난반사·하이라이트·테두리 빛·그림자·AO·안개)
    load_obj · raster_mesh                OBJ 모델 면 칠하기 (각 면 단색 음영)
    to_grid(grid, r3d, ramp, …)           결과를 글자로 + 깊이(grid.z) 기록 → 뒤에 그리는 점·선이 가려짐
    draw_points · draw_line3d · wireframe 3D 점(가까운 것만)·선

render_sdf 와 raster_mesh 는 같은 형태(Render3D: rgb, depth, mask)를 돌려준다.
"""
import math
from collections import namedtuple

import numpy as np

from .shade import coords, field_to_grid, half_width

Render3D = namedtuple("Render3D", "rgb depth mask")   # rgb (rows, cols, 3) 0..1+, depth (rows, cols) 칸까지 거리(빈 곳 inf), mask 덮인 비율 0..1


# ---------- 벡터 · 회전 ----------
def normalize(v):
    v = np.asarray(v, np.float64)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)


def rot_euler(x=0.0, y=0.0, z=0.0):
    """x → y → z 축 순서로 돌리는 회전 (라디안)."""
    return rot_z(z) @ rot_y(y) @ rot_x(x)


# ---------- 카메라 ----------
class Camera:
    """원근 카메라. fov 는 세로 화각(도). 화면 좌표는 shade.coords 와 같다 (세로 −1..1)."""

    def __init__(self, position, target=(0, 0, 0), up=(0, 1, 0), fov=45.0):
        self.position = np.asarray(position, np.float64)
        self.forward = normalize(np.asarray(target, np.float64) - self.position)
        self.right = normalize(np.cross(np.asarray(up, np.float64), self.forward))
        self.up = np.cross(self.forward, self.right)
        self.tan = math.tan(math.radians(fov) / 2)

    def rays(self, X, Y):
        """화면 좌표 X, Y → (광선 시작점, 방향) (…, 3)."""
        d = (self.forward + self.right * (np.asarray(X)[..., None] * self.tan)
             + self.up * (np.asarray(Y)[..., None] * self.tan))
        return np.broadcast_to(self.position, d.shape), normalize(d)

    def project(self, pts, cols, rows, cell_aspect, near=1e-3):
        """3D 점 (N, 3) → (칸 x, 칸 y, 깊이, 보이는지). 칸 좌표는 실수 (floor 하면 칸 번호)."""
        rel = np.asarray(pts, np.float64) - self.position
        z = rel @ self.forward
        zz = np.maximum(z, near)
        sx = (rel @ self.right) / (zz * self.tan)
        sy = (rel @ self.up) / (zz * self.tan)
        hw = half_width(cols, rows, cell_aspect)
        col = (sx / hw + 1) / 2 * cols
        row = (1 - sy) / 2 * rows
        return col, row, z, z > near


# ---------- SDF 도형 (p: (…, 3)) ----------
def sphere(p, r):
    return np.linalg.norm(p, axis=-1) - r


def box(p, b):
    q = np.abs(p) - np.asarray(b, np.float64)
    return np.linalg.norm(np.maximum(q, 0), axis=-1) + np.minimum(q.max(axis=-1), 0)


def round_box(p, b, r):
    return box(p, np.asarray(b, np.float64) - r) - r


def torus(p, R, r):
    """xz 평면에 누운 도넛 (큰 반지름 R, 굵기 r)."""
    q0 = np.hypot(p[..., 0], p[..., 2]) - R
    return np.hypot(q0, p[..., 1]) - r


def cylinder(p, r, h):
    """y 축으로 선 원기둥 (반지름 r, 반높이 h)."""
    dx = np.hypot(p[..., 0], p[..., 2]) - r
    dy = np.abs(p[..., 1]) - h
    return np.minimum(np.maximum(dx, dy), 0) + np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))


def capped_cone(p, h, r1, r2):
    """y 축으로 선 잘린 원뿔 (반높이 h, 아래 반지름 r1, 위 반지름 r2). r2=0 이면 뾰족한 원뿔. (iq sdCappedCone)"""
    qx = np.hypot(p[..., 0], p[..., 2])
    qy = p[..., 1]
    k2x, k2y = r2 - r1, 2.0 * h
    cax = qx - np.minimum(qx, np.where(qy < 0, r1, r2))
    cay = np.abs(qy) - h
    f = np.clip(((r2 - qx) * k2x + (h - qy) * k2y) / (k2x * k2x + k2y * k2y), 0, 1)
    cbx = qx - r2 + k2x * f
    cby = qy - h + k2y * f
    s = np.where((cbx < 0) & (cay < 0), -1.0, 1.0)
    return s * np.sqrt(np.minimum(cax * cax + cay * cay, cbx * cbx + cby * cby))


def capsule(p, a, b, r):
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - ba * h[..., None], axis=-1) - r


def plane(p, normal=(0, 1, 0), height=0.0):
    """normal 쪽이 바깥인 평면. 기본은 y = −height 바닥."""
    return p @ normalize(normal) + height


def union(*ds):
    return np.minimum.reduce(ds)


def subtract(a, b):
    """a 에서 b 를 파낸다."""
    return np.maximum(a, -b)


def intersect(a, b):
    return np.maximum(a, b)


def smooth_union(a, b, k):
    """부드럽게 합치기 (k 가 클수록 이음매가 둥글다)."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def local(p, rotation=None, translate=(0, 0, 0)):
    """물체를 rotation 으로 돌리고 translate 로 옮겼을 때, 물체 기준 좌표. (p − t) · R"""
    q = p - np.asarray(translate, np.float64)
    return q @ rotation if rotation is not None else q


# ---------- 레이마칭 · 법선 ----------
def raymarch(sdf, ro, rd, max_steps=64, max_dist=20.0, eps=1e-3):
    """광선마다 표면까지 거리 t 와 부딪혔는지. 아직 안 끝난 광선만 계속 계산한다."""
    shape = rd.shape[:-1]
    ro = np.ascontiguousarray(np.broadcast_to(ro, rd.shape)).reshape(-1, 3)
    rd = rd.reshape(-1, 3)
    t = np.zeros(len(rd))
    hit = np.zeros(len(rd), bool)
    act = np.arange(len(rd))
    for _ in range(int(max_steps)):
        if not len(act):
            break
        d = sdf(ro[act] + rd[act] * t[act, None])
        h = d < eps * (1 + t[act])
        hit[act[h]] = True
        t[act] += np.where(h, 0, d)
        act = act[~h & (t[act] < max_dist)]
    return t.reshape(shape), hit.reshape(shape)


_TETRA = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], np.float64)


def normal(sdf, p, eps=1e-3):
    """표면 방향 (사면체 4점 차분)."""
    n = sum(k * sdf(p + k * eps)[..., None] for k in _TETRA)
    return normalize(n)


def soft_shadow(sdf, p, light_dir, k=8.0, steps=32, tmin=0.02, tmax=8.0):
    """빛 쪽으로 광선을 쏴서 가려진 정도 (1 = 다 받음, 0 = 그림자). k 가 클수록 그림자 경계가 날카롭다."""
    res = np.ones(len(p))
    t = np.full(len(p), tmin)
    act = np.arange(len(p))
    for _ in range(int(steps)):
        if not len(act):
            break
        d = sdf(p[act] + light_dir * t[act, None])
        res[act] = np.minimum(res[act], k * d / t[act])
        t[act] += np.clip(d, 0.01, 0.5)
        act = act[(d > 1e-4) & (t[act] < tmax) & (res[act] > 0)]
    return np.clip(res, 0, 1)


def ambient_occlusion(sdf, p, n, samples=5, step=0.08):
    """구석일수록 어둡게 (1 = 트임, 0 = 막힘)."""
    occ, w = 0.0, 1.0
    for i in range(1, int(samples) + 1):
        h = step * i
        occ = occ + (h - sdf(p + n * h)) * w
        w *= 0.5
    return np.clip(1 - 3 * occ, 0, 1)


def _downsample(a, ss, reduce="mean"):
    if ss == 1:
        return a
    h, w = a.shape[0] // ss, a.shape[1] // ss
    b = a.reshape((h, ss, w, ss) + a.shape[2:])
    return b.min(axis=(1, 3)) if reduce == "min" else b.mean(axis=(1, 3))


def render_sdf(sdf, camera, cols, rows, cell_aspect, ss=1, color=(1.0, 1.0, 1.0), light_dir=(-0.5, 0.7, -0.5),
               light_rgb=(1.0, 1.0, 1.0), ambient=0.08, diffuse=0.9, specular=0.0, shininess=24.0, rim=0.0,
               rim_power=3.0, shadows=False, shadow_k=8.0, ao=0.0, fog=0.0, fog_start=0.0, fog_rgb=(0.0, 0.0, 0.0),
               background=(0.0, 0.0, 0.0), max_steps=64, max_dist=20.0):
    """SDF 장면을 레이마칭으로 그린다 → Render3D.

    color: (r, g, b) 0..1 또는 함수 color(p, n) → (k, 3)   (점 위치·법선으로 무늬를 칠할 때)
    light_dir: 빛이 오는 쪽 방향.  shadows: 부드러운 그림자 (느려짐).  ao: 구석 어둡게 세기 0..1
    fog: 거리 안개 세기 (거리 1 당), fog_start 보다 먼 곳만 흐려짐.  background: 아무것도 없는 곳의 색
    """
    X, Y = coords(cols, rows, cell_aspect, ss)
    ro, rd = camera.rays(X, Y)
    t, hit = raymarch(sdf, ro, rd, max_steps, max_dist)
    H, W = X.shape
    rgb = np.empty((H, W, 3))
    rgb[...] = background
    depth = np.full((H, W), np.inf)
    if hit.any():
        rd_h = rd[hit]
        p = camera.position + rd_h * t[hit][:, None]
        n = normal(sdf, p)
        l = normalize(light_dir)
        v = -rd_h
        lam = np.clip(n @ l, 0, 1)
        if shadows:
            lit = lam > 0                                      # 빛을 등진 면은 어차피 어두우니 그림자 계산 생략
            if lit.any():
                lam[lit] = lam[lit] * soft_shadow(sdf, p[lit] + n[lit] * 2e-3, l, shadow_k)
        base = np.asarray(color(p, n) if callable(color) else np.broadcast_to(color, p.shape), np.float64)
        shade = ambient + diffuse * lam
        if ao > 0:
            shade = shade * (1 - ao + ao * ambient_occlusion(sdf, p, n))
        col = base * shade[:, None] * np.asarray(light_rgb)
        if specular > 0:
            hv = normalize(l + v)
            col = col + specular * (np.clip(n @ hv.T if hv.ndim == 1 else (n * hv).sum(-1), 0, 1)
                                    ** shininess)[:, None] * np.asarray(light_rgb) * (lam > 0)[:, None]
        if rim > 0:
            col = col + rim * ((1 - np.clip((n * v).sum(-1), 0, 1)) ** rim_power)[:, None]
        if fog > 0:
            f = np.exp(-fog * np.maximum(t[hit] - fog_start, 0))[:, None]
            col = col * f + np.asarray(fog_rgb) * (1 - f)
        rgb[hit] = col
        depth[hit] = t[hit]
    return Render3D(_downsample(rgb, ss), _downsample(depth, ss, "min"), _downsample(hit.astype(np.float64), ss))


# ---------- OBJ 모델 ----------
def load_obj(source):
    """OBJ 파일 경로 또는 내용 문자열 → (꼭짓점 (N, 3), 면 목록 [[i, j, k, …], …]). 법선·텍스처는 무시."""
    text = source
    if "\n" not in source and source.lower().endswith(".obj"):
        with open(source, encoding="utf-8", errors="replace") as f:
            text = f.read()
    verts, faces = [], []
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            verts.append([float(x) for x in parts[1:4]])
        elif parts[0] == "f":
            idx = []
            for tok in parts[1:]:
                i = int(tok.split("/")[0])
                idx.append(i - 1 if i > 0 else len(verts) + i)
            faces.append(idx)
    if not verts or not faces:
        raise ValueError("OBJ 에 꼭짓점(v)이나 면(f)이 없습니다")
    return np.asarray(verts, np.float64), faces


def triangles(faces):
    """다각형 면 → 삼각형 (부채꼴로 나눔) (M, 3)."""
    return np.asarray([[f[0], f[i], f[i + 1]] for f in faces for i in range(1, len(f) - 1)], np.int64)


def mesh_edges(faces):
    """다각형 면의 모서리 (중복 없이) — 와이어프레임용."""
    out = set()
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            out.add((min(a, b), max(a, b)))
    return sorted(out)


def raster_mesh(verts, faces, camera, cols, rows, cell_aspect, color=(1.0, 1.0, 1.0), light_dir=(-0.5, 0.7, -0.5),
                ambient=0.12, diffuse=0.88, cull_back=True, background=(0.0, 0.0, 0.0)):
    """모델을 칸 단위로 칠한다 (각 면 단색 음영, 깊이 비교) → Render3D.

    color: (r, g, b) 0..1 또는 면마다 (M, 3) 배열.
    """
    tris = triangles(faces)
    v = np.asarray(verts, np.float64)
    cx, cy, z, vis = camera.project(v, cols, rows, cell_aspect)
    rgb = np.empty((rows, cols, 3))
    rgb[...] = background
    depth = np.full((rows, cols), np.inf)
    mask = np.zeros((rows, cols))
    l = normalize(light_dir)
    cols_face = np.broadcast_to(np.asarray(color, np.float64), (len(tris), 3)) if np.ndim(color) == 1 \
        else np.asarray(color, np.float64)
    for k, (a, b, c) in enumerate(tris):
        if not (vis[a] and vis[b] and vis[c]):
            continue
        n = normalize(np.cross(v[b] - v[a], v[c] - v[a]))
        center = (v[a] + v[b] + v[c]) / 3
        if cull_back and n @ (camera.position - center) <= 0:
            continue
        xs, ys = np.array([cx[a], cx[b], cx[c]]), np.array([cy[a], cy[b], cy[c]])
        x0, x1 = int(max(0, np.floor(xs.min()))), int(min(cols - 1, np.ceil(xs.max())))
        y0, y1 = int(max(0, np.floor(ys.min()))), int(min(rows - 1, np.ceil(ys.max())))
        if x0 > x1 or y0 > y1:
            continue
        gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
        den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(den) < 1e-12:
            continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        zz = w0 * z[a] + w1 * z[b] + w2 * z[c]
        sub = depth[y0:y1 + 1, x0:x1 + 1]
        win = inside & (zz < sub)
        sub[win] = zz[win]
        mask[y0:y1 + 1, x0:x1 + 1][win] = 1
        rgb[y0:y1 + 1, x0:x1 + 1][win] = cols_face[k] * (ambient + diffuse * max(0.0, float(n @ l)))
    return Render3D(rgb, depth, mask)


# ---------- 글자로 · 점 · 선 ----------
def to_grid(grid, r3d, ramp, coverage=0.5, **kw):
    """Render3D → 글자 (field_to_grid). 덮인 칸의 깊이를 grid.z 에 남겨, 뒤에 그리는 점·선이 가려지게 한다."""
    mask = r3d.mask >= coverage
    field_to_grid(r3d.rgb, grid, ramp, mask=mask, **kw)
    grid.z[mask] = np.minimum(grid.z[mask], r3d.depth[mask])
    return mask


def draw_points(grid, pts, camera, cell_aspect, chars, colors):
    """3D 점들을 찍는다. 한 칸에 여러 점이면 가장 가까운 점, grid.z 보다 먼 점은 가려져 안 그림.

    chars: 한 글자 / 점마다 글자 코드 배열,  colors: (r, g, b) / 점마다 (N, 3)
    """
    pts = np.asarray(pts, np.float64)
    if not len(pts):
        return 0
    col, row, z, vis = camera.project(pts, grid.cols, grid.rows, cell_aspect)
    x, y = np.floor(col).astype(np.int64), np.floor(row).astype(np.int64)
    ok = vis & (x >= 0) & (y >= 0) & (x < grid.cols) & (y < grid.rows)
    if not ok.any():
        return 0
    ids = np.nonzero(ok)[0]
    cell = y[ids] * grid.cols + x[ids]
    order = np.argsort(z[ids], kind="stable")                       # 가까운 순
    _, first = np.unique(cell[order], return_index=True)
    pick = ids[order[first]]
    flat = y[pick] * grid.cols + x[pick]
    front = z[pick] < grid.z.reshape(-1)[flat]
    pick, flat = pick[front], flat[front]
    codes = np.full(len(pts), ord(chars), np.uint32) if isinstance(chars, str) else np.asarray(chars, np.uint32)
    rgb = np.broadcast_to(np.asarray(colors, np.uint8), (len(pts), 3))
    grid.ch.reshape(-1)[flat] = codes[pick]
    grid.rgb.reshape(-1, 3)[flat] = rgb[pick]
    grid.z.reshape(-1)[flat] = z[pick]
    return len(pick)


def line_char(dx, dy):
    """화면 위 선의 방향 (오른쪽 +x, 아래 +y, 칸 높이 단위) → - \\ | / 글자 코드."""
    ang = (math.degrees(math.atan2(dy, dx)) % 180.0)
    return ord("-\\|/"[int(round(ang / 45.0)) % 4])


def draw_line3d(grid, a, b, camera, cell_aspect, color, char=None, density=2.0):
    """3D 선분 a–b 를 그린다 (방향에 맞는 글자, 깊이 비교). density: 칸당 점 수."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    ca, ra, _, _ = camera.project(a[None], grid.cols, grid.rows, cell_aspect)
    cb, rb, _, _ = camera.project(b[None], grid.cols, grid.rows, cell_aspect)
    dx, dy = (cb[0] - ca[0]) * cell_aspect, rb[0] - ra[0]
    n = int(max(2, math.ceil(max(abs(cb[0] - ca[0]), abs(rb[0] - ra[0])) * density)))
    s = np.linspace(0, 1, n)[:, None]
    ch = char if char is not None else chr(line_char(dx, dy))
    return draw_points(grid, a + (b - a) * s, camera, cell_aspect, ch, color)


def wireframe(grid, verts, edges, camera, cell_aspect, color, char=None):
    for i, j in edges:
        draw_line3d(grid, verts[i], verts[j], camera, cell_aspect, color, char)
