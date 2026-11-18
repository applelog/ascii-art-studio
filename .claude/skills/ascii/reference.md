# /ascii 참고서 — 엔진 사용법 · 레시피 · 점검표

작품은 `pieces/<slug>/piece.py` 하나다. 엔진(`asciiart/`)은 모든 작품이 함께 쓴다.

## 1. 작품 파일 구조 (템플릿 그대로)

```
"""제목 — 설명 / 요청 원문 / 단계"""
# ===== ① 장면 설정 =====     ← 대문자 변수, 한 줄 주석 "뜻 (단위·범위)"
# ===== ② 등장 설정 =====     INTRO_SECONDS, INTRO_HOLD, …
# ===== ③ 모션 설정 =====     LOOP_SECONDS, FPS, LOOP, …
# ===== 최종 출력 =====       FINAL_LOOPS
# ===== 효과 =====            TRAIL, GLOW, GLOW_RADIUS, SEED, RANGES
# ===== 코드 =====            ← 이 줄이 경계 (테스트가 찾음). 아래는 숫자 금지 (0, 1, 2, 0.5 만)
setup() → state                 한 번. 좌표·마스크·순서·일정표. 난수는 np.random.RandomState(SEED)
draw(s, phase, grid)            그림 하나
scene(s, grid)      = draw(s, 0, grid)
intro(s, p, grid)   p=1 이면 scene 과 같게
motion(s, t, phase, grid) = draw(s, phase, grid)
if __name__ == "__main__": run(globals())
```

화면 좌표 (필드 렌더): 세로 −1(아래)..1(위), 가로 −half_w..half_w (`half_w = COLS·CELL_ASPECT / ROWS`). 칸 좌표: x 열(오른쪽 +), y 행(아래 +).

## 2. 엔진 함수

### grid.Grid(cols, rows)
`ch` (rows, cols) 글자 코드 (0 = 빈칸), `rgb` (rows, cols, 3), `z` 깊이.
`put(x, y, ch, rgb)`, `put_z(x, y, z, ch, rgb)`, `text(x, y, s, rgb)`, `fill(mask, ch_or_codes, rgb_or_array)`, `clear()`, `to_text()`, `digest()`, `filled_ratio()`

### ramp — 밝기 → 글자
- `RAMPS["short" | "long" | "blocks" | "dots" | "digits" | "water"]`, `GLYPH_POOLS`
- `ramp_chars(lum, ramp, gamma=, cut=, dither=, mode="hash"|"bayer", shimmer=, step=, xx=, yy=, seed=)` → 글자 코드 배열
- `pool_chars(lum, pools, step=, …)`: 밝기 단계별 글자 풀 (칸마다 묶음 안에서 고름, step 으로 반짝임)
- `edges(lum, cell_aspect)` → (세기, gx, gy)
- `edge_chars(gx, gy)` → `| / - \`
- `thin_edges(mag, gx, gy, threshold)` → 한 칸 두께 윤곽 마스크
- `cell_hash(xx, yy, seed)` → 칸마다 고정 0..1
- `codes_of("문자열")`

### color
`rgb01((r, g, b))` → 0..1, `palette_color(lum, PALETTE, min_color)`, `quantize(rgb, levels)`

### shade — 필드 렌더 (eyeTutorial 방식)
- `shade(fn, COLS, ROWS, CELL_ASPECT, SUPERSAMPLE)`: `fn(X, Y)` → (H, W, 3) 색 0..1+ → 칸마다 평균
- `coords(...)`, `half_width(...)`, `luminance(rgb)`
- `field_to_grid(rgb, grid, RAMP, cut=, gamma=, dither=, seed=, color_levels=, min_color=, mask=, shimmer=, step=)`

### post — 글자로 바꾸기 전 색 필드 후처리
`bloom(rgb, strength, radius, threshold, cell_aspect)`, `tonemap(rgb, exposure, keep_color=True, white=)`, `vignette(rgb, amount, cell_aspect)`, `blur(a, radius, cell_aspect)`

### ease — 연출 곡선
`segment(t, 시작, 끝)` (막 진행도 0..1), `smoothstep(a, b, x)`, `ease_in / ease_out / ease_in_out(p)`, `overshoot(p, back)`, `keyframes(t, [(시각, 값), …])`, `exp_lerp(a, b, p)` (줌), `loop_sin(phase, cycles, offset)` (정수 주기), `loop_cycles(c)`

### noise — seed 값 노이즈
`noise1(t)`, `noise2(x, y)`, `noise3(x, y, z)`, `fbm(x, y, z=None, octaves=)`, `loop_noise(x, y, phase, radius, octaves, seed)` (phase 0 = 1)

### schedule — 무작위 사건
`make_schedule(seed, count, span, duration=(lo, hi), min_gap=)` → `[{start, dur, rand[8]}]`
`active(events, t, span, loop=True)` → `[(사건, 진행도 p)]`

### effects
설정 `TRAIL` · `GLOW` · `GLOW_RADIUS`를 두면 엔진이 알아서 건다. 작품 코드에서 부를 필요는 없다.

### field — 이미지
`ImageField.load(path)`, `Placement(field, COLS, ROWS, CELL_ASPECT, fit="contain"|"cover", scale, cx, cy)`
- `.cells()` → u, v / `.uv(xp, yp)`
- `draw_field(grid, field, u, v, ramp, brightness="lum"|"inverse"|"alpha", alpha_cut, cut, gamma, dither, seed, color="original"|"palette"|(r,g,b), min_color, edge_cut, edge_rgb, cell_aspect, shimmer, step)` → (안쪽 마스크, 윤곽 마스크)
- `field.sample("lum"|"alpha"|"edge"|"rgb"|"angle"|"index", u, v)`

### three — 3D
- `Camera(위치, 바라볼 곳, fov)`: `.rays(X, Y)`, `.project(pts, COLS, ROWS, CELL_ASPECT)`
- 도형: `sphere(p, r)`, `box(p, b)`, `round_box(p, b, r)`, `torus(p, R, r)`, `cylinder(p, r, h)`, `capsule(p, a, b, r)`, `plane(p, normal, height)`
- 합치기·변환: `union`, `smooth_union(a, b, k)`, `subtract`, `intersect`, `local(p, R, t)`
- 회전: `rot_x / rot_y / rot_z / rot_euler`
- `render_sdf(sdf, cam, COLS, ROWS, CELL_ASPECT, ss, color=(r,g,b) 또는 fn(p, n), light_dir, ambient, diffuse, specular, shininess, rim, shadows, ao, fog, fog_start, background, max_steps)` → Render3D
- `load_obj(경로|문자열)`, `raster_mesh(verts, faces, cam, …)` → Render3D, `mesh_edges(faces)`
- `to_grid(grid, r3d, RAMP, **field_to_grid 인자)` → 깊이를 `grid.z`에 남김
- `draw_points(grid, pts, cam, CELL_ASPECT, chars, colors)`: 가까운 점만, 가려지면 안 그림
- `draw_line3d(...)`, `wireframe(grid, verts, edges, cam, CELL_ASPECT, rgb)`

### 실행기 (piece.py 의 명령)
`--stage 1|2|3`, `--final`, `--check`, `--version 이름`, `--set KEY=VALUE`, `--mp4 [--loops N]`, `--gif`, `--strip [--strip-count N]`, `--png N`, `--seconds N`, `--player auto|pygame|opencv`

## 3. 레시피

**밝게 빛나는 물체 (필드 렌더)**: `shade(fn)` → `bloom` → `tonemap(white=)` → `vignette` → `field_to_grid`. 빛은 `nx*LX + ny*LY + nz*LZ` (구 법선). 예: `examples/f5_demo.py`

**또렷한 윤곽**: 밝기·마스크 필드에 `edges` → `thin_edges` → `edge_chars`로 덮어 그린다. 예: `examples/f4_demo.py` 6번

**이미지에서**: `tools/image_to_field.py` → `ImageField.load` → `Placement` → `draw_field(edge_cut=)`. 예: `examples/f8_demo.py`

**3D**: `Camera` + SDF 함수 → `render_sdf` → `to_grid` → `draw_points`(입자, 가려짐 처리). 회전은 `rot_y(2π·round(SPIN)·phase)`. 예: `examples/f85_demo.py`

**등장 (intro)**: `setup()`에서 칸마다 순서 0..1을 만들고 `order < p`인 칸만 보인다. 이 패턴 하나로 여러 방식을 만든다.

| 방식 | 순서를 만드는 법 |
|---|---|
| 스캔 | 행 번호 |
| 퍼짐 | 중심에서 거리 |
| 해독 | 순서 + `DECODE_SPAN` 동안 무작위 글자 (`cell_hash(…, step)`) |
| 윤곽 먼저 | 윤곽 칸은 둘레 각도, 나머지는 `cv2.distanceTransform` 거리 |
| 깊이 순 (3D) | `grid.z` 깊이 |

순서에 `cell_hash × SOFT`를 섞으면 경계가 자연스럽다. 예: `f75_demo`(해독), `f8_demo`(윤곽 먼저), `f85_demo`(깊이 순)

**모션 (motion)**: 모두 phase 의 정수 주기로 만든다.

| 움직임 | 쓰는 것 |
|---|---|
| 회전 | `2π·round(SPIN)·phase` |
| 맥박·숨쉬기 | `1 + A·sin(2π·round(N)·phase)` |
| 흐름 | `loop_noise(x, y, phase, radius)` |
| 반짝임 | `step = int(phase·STEPS) % STEPS` 를 `shimmer/step` 에 |
| 별 반짝임 | `loop_sin(phase, N, 별마다 offset)` |
| 별똥별 같은 사건 | `make_schedule` + `active` + 잔상 `TRAIL` |
| 빠르게 움직이는 것 | 직전 프레임 위치부터 선을 이어 그린다 (점선 방지) |

**장면 전환 (막)**: 막마다 `segment(t, T_A, T_A + T_A_D)`로 진행도를 내고, `ease_*`·`overshoot`로 곡선을 준다. 줌은 `exp_lerp`. 막 시각은 설정 변수 `T_<막>`, `T_<막>_D`로 둔다.

## 4. 품질 점검표 (단계마다)

- [ ] `pytest tests/test_pieces.py -k <slug>` 통과
  - 설정 먼저, 숫자 금지, random/time 없음, 결정성, 용어집, 단계 연결, 미리보기 = 코드
- [ ] `--check`: ① = ② 끝 = ③ 처음 = ③ 끝
- [ ] PNG·프레임 띠를 직접 보고 확인
  - 형태가 읽힌다
  - 너무 빽빽하거나 비지 않다 (글자 비율 대략 15~70%)
  - 어두운 곳은 비어 있다 (`CUT`)
  - 띠 무늬가 없다 (`DITHER`)
- [ ] 색: 어두운 글자가 안 보이면 `MIN_COLOR`, 색이 바래면 `tonemap(keep_color=True)`
- [ ] 속도: 창 재생이 초당 30프레임에 가까운지 (무거우면 setup으로 옮기고, 해상도·SUPERSAMPLE·MAX_STEPS를 줄인다)
- [ ] `brief.md` 진행 상태·수정 기록, `tools/glossary.py`로 용어집 갱신

## 5. 자주 하는 실수

| 증상 | 원인 → 해결 |
|---|---|
| 하늘·바다가 점으로 다 덮임 | 어두운 곳까지 디더가 글자를 찍음 → `CUT` 올리기 |
| 물체가 어둡게 묻힘 | 안개를 카메라부터 걸음 → `fog_start`, 빛 방향, `AMBIENT`·`RIM` |
| 루프 끝에서 튐 | 주기가 정수가 아님 → `round()`, `loop_sin`, `loop_noise` |
| 등장 끝에서 튐 | `intro(p=1)` ≠ `scene` → p≥1 이면 완성 화면을 그대로 복사 |
| `_`·`g`가 잘림 | 칸 높이 문제 → 엔진이 `LINE_HEIGHT` 1.15로 처리함 (FONT_PX 를 너무 작게 하지 않기) |
| 한글이 □로 나옴 | Menlo 에 한글이 없음 → 영어·기호로 쓰거나 한글 글꼴 경로를 `FONT` 에 |
| 별똥별 꼬리가 점선 | 한 프레임에 여러 칸 이동 → 직전 위치부터 선으로 잇기 |
| 창이 끊김 | 프레임 계산이 무거움 → setup 미리 계산, 해상도↓. 12ms 넘는 작품은 엔진이 작업자 프로세스로 미리 계산 |
| 같은 프레임인데 그림이 다름 | random·time 사용, setup 밖에서 난수 → SEED·일정표 |
