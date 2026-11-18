# 용어집 — 크리스마스 트리

형식: `이름 : 뜻 : 단위·범위` (eyeTutorial Glossary.txt 방식 + 범위 칸). 이름 하나에 뜻 하나.
설정·함수 절은 `python tools/glossary.py pieces/christmas-tree/piece.py` 로 자동 갱신된다. 나머지 절은 손으로 쓴다.

--- 일반 용어 ---
칸 : 글자 하나가 들어가는 자리 (cell) : COLS×ROWS 개
램프 : 어두움→밝음 순으로 늘어놓은 글자열 : 문자열
phase : 모션 한 루프의 진행도. 0 과 1 이 같은 장면 : 0~1
p : 등장 진행도. 1 이면 완성 화면 : 0~1

<!-- auto settings -->

--- ① 장면 설정 ---
COLS : 가로 글자 칸 수 : 16~400
ROWS : 세로 글자 칸 수 (8~240) — 180×192 칸 × 6×10 px = 1080×1920 : 9:16
FONT : 글꼴 이름 또는 .ttf/.ttc 경로 — Menlo 에는 한글이 없음 : —
FONT_PX : 글자 크기 px (6~48) — 9 이면 칸 6×10 px : —
CELL_ASPECT : 칸 너비/높이 : 0.35~1.2
BACKGROUND : 바탕색 : RGB 0~255
SUPERSAMPLE : 칸 하나를 몇×몇 점으로 계산 : 1~3
RAMP : 밝기 순 글자 : 첫 글자는 빈칸
GAMMA : 밝기 감마 — 1 보다 작으면 어두운 글자가 늘어남 : 0.3~2
CUT : 이보다 어두우면 빈칸 : 0~1
DITHER : 칸마다 고정 디더 폭 — 띠 무늬 제거 : 0~2
MIN_COLOR : 글자 색 밝기 하한 : 0~1
SKY_TOP_RGB : 하늘 꼭대기 색 : RGB
SKY_LOW_RGB : 지평선 근처 하늘 색 : RGB
MOON_X : 달 가로 위치, 가운데 0 : 화면 좌표, 세로 절반 = 1
MOON_Y : 달 세로 위치 : −1 아래 … 1 위
MOON_R : 달 반지름 : 화면 좌표
MOON_RGB : 달 색 : RGB
MOON_SPOTS : 달 무늬 진하기 : 0~1
MOON_SPOT_SCALE : 달 무늬 촘촘함 : 1~40
MOON_LIMB : 달 가장자리가 어두워지는 정도 : 0~1
MOON_HALO : 달 둘레 빛 세기 : 0~1
MOON_HALO_R : 달 둘레 빛 번짐 거리 : 화면 좌표
MOON_RAMP : 달 글자 (밝기 순) — 고른 # 바탕이라 실루엣이 또렷함 : —
MOON_GAMMA : 달 글자 감마 — 작을수록 # 이 많아짐 : 0.1~2
MOON_DITHER : 달 글자 디더 폭 : 0~2
STARS : 하늘 칸 중 별이 있는 비율 : 0~0.2
STAR_CHARS : 별 글자 : 작은 별 → 큰 별
STAR_RGB : 별 색 : RGB
HILL_H : 먼 언덕 높이 : 화면 좌표
HILL_WAVES : 화면 너비에 들어가는 언덕 굴곡 수 : 0.5~12
HILL_RGB : 달빛 받은 먼 눈 언덕 색 : RGB
HILL_PINES : 언덕 위 작은 소나무 수 : 0~60
HILL_PINE_H : 작은 소나무 높이 : 화면 좌표
HILL_PINE_W : 작은 소나무 밑변 절반 : 화면 좌표
HILL_PINE_RGB : 작은 소나무 색 : RGB
SNOW_RGB : 가까운 눈 바닥 색 : RGB
SNOW_TOL : 칸 깊이가 바닥까지 거리의 이 비율 안이면 눈 바닥으로 봄 : 0.01~0.3
SNOW_RAMP : 눈 바닥 글자 (밝기 순) — 가로줄로 보이는 - 를 빼서 알갱이 느낌 : —
HILL_DIST : 이보다 먼 눈 바닥은 먼 언덕으로 덮음 : 거리
SNOW_GRAIN : 눈 바닥 얼룩 세기 : 0~1
SNOW_GRAIN_SCALE : 눈 바닥 얼룩 크기 : 1/거리
SNOW_SPARKLE : 눈 바닥 칸 중 반짝이는 비율 : 0~0.3
SNOW_SPARKLE_CHARS : 눈 반짝임 글자 : —
SNOW_SPARKLE_RGB : 눈 반짝임 색 : RGB
CAMERA_POS : 카메라 위치 : x 오른쪽, y 위, z 안쪽
CAMERA_TARGET : 카메라가 보는 곳 : —
FOV : 세로 화각 : 도, 10~120
LIGHT_DIR : 달빛이 오는 쪽 : 오른쪽 위 앞
AMBIENT : 그늘 밝기 : 0~1
RIM : 테두리 빛 세기 : 0~1
LIGHT_GAIN : 달빛 세기 배수 : 0~3
FOG : 거리 안개 세기 : FOG_START 보다 먼 곳이 지평선 색으로
FOG_START : 안개가 시작되는 거리 : 트리 바로 뒤
FOG_RGB : 먼 곳 색 : RGB
MAX_STEPS : 레이마칭 최대 걸음 : 16~200
MAX_DIST : 레이마칭 최대 거리 : 지평선
STEP_SAFETY : 가지 끝 물결 때문에 걸음을 줄이는 비율 : 0.3~1
TREE_H : 잎 부분 높이 : 가장 아래 가지 → 꼭대기
TREE_R : 가장 아래 층 반지름 — 높이:너비 ≈ 1.45 : 사진 1.5~1.6
TREE_BASE : 가장 아래 가지 높이 : 그 아래는 줄기
TIERS : 가지 층 수 : 1~9
TIER_OVERLAP : 층이 겹치는 비율 : 0~0.8
TIER_TOP : 층 위쪽 반지름 / 아래쪽 반지름 : 0~1
TIER_TWIST : 층마다 가지 끝을 엇갈리게 돌리는 각도 : 라디안
BRANCHES : 층마다 가지 끝 개수 : 3~30
SCALLOP : 가지 끝이 튀어나온 정도 : 0~0.3
NEEDLE_RGB : 밝은 잎 색 : RGB
NEEDLE_DARK_RGB : 안쪽 어두운 잎 색 : RGB
NEEDLE_GRAIN : 잎 결 촘촘함 : 1/거리
NEEDLE_GRAIN_MIX : 잎 결이 색에 섞이는 비율 : 0~1
TREE_OUTLINE : 트리 바깥 테두리를 방향 글자 / \ | - 로 : —
TREE_OUTLINE_RGB : 트리 테두리 글자 색 : RGB
TRUNK_R : 줄기 반지름 : —
TRUNK_RGB : 줄기 색 : RGB
ORNAMENTS : 장식 공 개수 : 0~120
ORNAMENT_R : 장식 공 반지름 : —
ORNAMENT_COLORS : 장식 공 색 : 클래식: 빨강, 금색
ORNAMENT_SHINE : 장식 공 하이라이트 세기 : 0~2
ORNAMENT_SHININESS : 장식 공 하이라이트 날카로움 : 2~200
ORNAMENT_FRONT : 장식 공을 앞쪽에 모으는 각도 범위 : 라디안, ±
ORNAMENT_LOW : 층 안에서 장식 공 높이 아래 끝 : 0~1, 0 = 층 아래
ORNAMENT_HIGH : 층 안에서 장식 공 높이 위 끝 : 0~1
BULBS : 전구 개수 : 0~600
LIGHT_TURNS : 전구 줄이 트리를 감는 바퀴 수 : —
BULB_TOP : 전구 줄이 올라가는 높이 : 잎 높이 비율, 0~1
BULB_LIFT : 잎 표면에서 전구를 띄운 거리 : —
BULB_CHAR : 전구 글자 : —
BULB_RGB : 전구 색 : RGB, 따뜻한 노랑
BULB_SPILL : 전구 빛이 잎·눈을 밝히는 세기 : 0~2
BULB_SPILL_R : 전구 빛 번짐 : 칸 높이 배수
ARC_SAMPLES : 전구 간격을 고르게 잡을 때 줄을 나누는 수 : —
TOPPER_LIFT : 별 가운데가 트리 꼭대기보다 높은 거리 : —
TOPPER_R : 별 반지름 : 화면 좌표
TOPPER_INNER : 별 안쪽 반지름 비율 : 0.2~0.9
TOPPER_RGB : 별 색 : RGB
TOPPER_RAY : 빛줄기 길이 : 화면 좌표
TOPPER_RAYS : 빛줄기 수 (0~16) — 별 꼭짓점 사이로 뻗음 : —
TOPPER_RAY_RGB : 빛줄기 색 : RGB
TOPPER_GLOW : 별 둘레 빛 세기 : 0~1
TOPPER_GLOW_R : 별 둘레 빛 번짐 거리 : 화면 좌표
GIFTS : — : —
GIFT_ROUND : 상자 모서리 둥글기 : —
RIBBON_W : 리본 절반 폭 : —
BOW_R : 리본 매듭 공 반지름 : —
GIFT_GAIN : 선물 상자 밝기 배수 — 트리 불빛을 받아 그늘에서도 보이게 : 1~3
TEAM_X : 썰매 가운데 가로 위치 : 화면 좌표
TEAM_Y : 썰매 가운데 세로 위치 : 화면 좌표
TEAM_SCALE : 썰매 단위 1 = 화면 길이 : 0.03~0.5
TEAM_TILT : 앞(왼쪽)이 들린 각도 : 라디안
FIG_RAMP : 썰매·순록 채움 글자 : 밝기 순
FIG_LIFT : 채움 글자 밝기 하한 (0~1) — 어두운 색도 글자가 보이게 : —
FIG_COVER : 칸이 이만큼 덮이면 그 부위로 칠함 : 0.05~0.95
FIG_OUTLINE : 테두리 칸은 방향 글자 / - \ | 로 : —
SILHOUETTE : 달과 겹친 부분은 검은 실루엣(빈칸)으로, 밖은 색 글자로 : —
SIL_EDGE : 실루엣 둘레의 달 글자를 윤곽 방향 글자 / \ | - 로 : —
FIG_GAP : 달 위에서 썰매·순록 둘레를 비우는 칸 수 : 0~3
FIG_PAD : 썰매 무리 계산 범위 여유 : 썰매 단위
SLEIGH_RGB : 썰매 몸통 색 : RGB
SLEIGH_TRIM_RGB : 썰매 금색 장식·날 색 : RGB
SLEIGH_BODY : 썰매 몸통 (꼭짓점): 높은 등받이, 앞이 휘어 올라감 : —
SLEIGH_SCROLL : 앞 장식 말림 : 금색 선
SLEIGH_RIM : 몸통 위 금색 테두리 : —
RUNNER : 썰매 날 : 앞이 말려 올라감
STRUTS : 날과 몸통을 잇는 기둥 : —
SACK : 선물 자루 (x, y, 가로 반지름, 세로 반지름) — 등받이 뒤로 보임 : —
SACK_RGB : 선물 자루 색 : RGB
SANTA_BODY : 산타 몸 : x, y, 가로 반지름, 세로 반지름
SANTA_HEAD : 얼굴 : x, y, 반지름
SANTA_BEARD : 수염 : x, y, 가로 반지름, 세로 반지름
SANTA_HAT : 모자 : 꼭짓점, 끝이 뒤로 넘어감
SANTA_HAT_TRIM : 모자 흰 테 : 시작, 끝, 두께
SANTA_POMPOM : 모자 끝 방울 : x, y, 반지름
SANTA_ARM : 팔 : 어깨, 손, 두께
SANTA_MITT_R : 장갑 반지름 : —
SANTA_COAT_RGB : 산타 옷 색 : RGB
SANTA_FUR_RGB : 흰 털·수염 색 : RGB
SANTA_SKIN_RGB : 얼굴 색 : RGB
SANTA_MITT_RGB : 장갑 색 : RGB
REINDEER : 순록 수, 맨 앞이 루돌프 (1~6) — 이 해상도에서 실루엣이 읽히는 크기로 2마리 : —
DEER_SIZE : 순록 크기 : 썰매 단위 배수
DEER_FIRST : 썰매 가운데 → 첫 순록 가운데 : 썰매 단위
DEER_GAP : 순록 사이 간격 (썰매 단위) — 앞 순록 뒷다리가 뒤 순록 머리에 닿지 않게 : —
DEER_Y : 순록 몸 높이 : 썰매 단위
DEER_RGB : 순록 털 색 : RGB
DEER_DARK_RGB : 다리·먼 쪽 색 : RGB
DEER_PALE_RGB : 목 갈기·엉덩이 흰 털 색 (RGB) — 사진에서 본 특징 : —
ANTLER_RGB : 뿔 색 : RGB
DEER_BODY : 몸통 : x, y, 가로 반지름, 세로 반지름
DEER_CHEST : 가슴 : 깊은 가슴
DEER_RUMP : 엉덩이 : —
DEER_NECK : 목 (시작, 끝, 굵기 시작, 굵기 끝) — 앞으로 뻗은 목 : —
DEER_HEAD : 머리 : 정수리, 코끝, 굵기 시작, 굵기 끝
DEER_RUFF : 목 아래 흰 갈기 : —
DEER_TAIL : 엉덩이 흰 꼬리 : —
ANTLER : — : —
ANTLER_FAR : 먼 쪽 뿔이 어긋난 정도 : —
SHOULDER : 앞다리 시작점 : —
HIP : 뒷다리 시작점 : —
LEG_UPPER : 윗다리 길이 — 순록 다리는 길고 가늘다 : 사진
LEG_LOWER : 아랫다리 길이 : —
LEG_R : 다리 굵기 : 반지름, 발굽 쪽은 LEG_R_END
LEG_R_END : 발굽 쪽 다리 굵기 : —
ANTLER_R : 뿔 굵기 : 반지름
LEG_POSE : 다리 각도 (도, 아래 0 → 앞 +): 가까운 앞, 먼 앞, 가까운 뒤, 먼 뒤 (윗다리, 아랫다리) — 하늘을 나는 자세 : —
NOSE : 루돌프 코 : x, y, 반지름
NOSE_RGB : 루돌프 코 색 : RGB
NOSE_CHAR : 루돌프 코 글자 : 실루엣 위에서도 보임
NOSE_GLOW : 코 둘레 빛 세기 : 0~1
NOSE_GLOW_R : 코 둘레 빛 번짐 거리 : 화면 좌표
COLLAR : 목줄 (순록 단위) — 고삐가 닿는 곳 : —
TRACE_FRONT : 끈이 순록 가슴에 닿는 곳 : 순록 단위
SLEIGH_HITCH : 끈이 썰매에 닿는 곳 : 썰매 단위
REIN_SAG : 고삐가 처지는 정도 : 길이 비율, 0~0.5
REIN_SEGMENTS : 고삐 곡선을 나누는 수 : 2~40
REIN_RGB : 고삐·끈 색 : RGB
FLAKES : 눈송이 수 : 0~800
FLAKE_CHARS : 눈송이 글자 : 작은 것 → 큰 것
FLAKE_RGB : 눈송이 색 : RGB

--- ② 등장 설정 ---
INTRO_SECONDS : 등장 길이 : 초
INTRO_HOLD : 등장 검토 영상 끝에 완성 화면을 보여 주는 시간 : 초
T_GROUND : 하늘 별·눈 바닥·눈송이가 스며 나오기 시작 : 초
T_GROUND_D : 위 길이 : 초
T_TREE : 트리가 아래(줄기)부터 글자로 차오르기 시작 : 초
T_TREE_D : 위 길이 : 초
FILL_JITTER : 차오르는 줄의 들쭉날쭉함 : 순서 0~1 기준, 0~0.5
FRONT_W : 막 채워진 글자가 빛나는 띠의 두께 : 순서 0~1 기준, 0.01~0.5
FRONT_RGB : 막 채워진 글자의 빛 색 (RGB) — 자리 잡으며 제 색으로 : —
FLY_SHARE : 트리 글자 중 멀리서 날아와 자리를 찾는 비율 (0~0.3) — 날아와 자리를 찾는 연출 : —
FLY_CELLS : 날아오는 글자가 출발하는 거리 : 칸, 0~40
T_DECOR : 장식 공·선물이 하나씩 반짝 켜지고 전구가 줄을 따라 켜지기 시작 : 초
T_DECOR_D : 위 길이 : 초
T_MOON : 달이 오른쪽부터 글자로 채워지며 보름달로 차오르기 시작 (초) — 장식과 동시에 : —
T_MOON_D : 위 길이 : 초
T_TOP : 꼭대기 별이 반짝하며 나타나기 시작 : 초
T_TOP_D : 위 길이 : 초
TOP_BOUNCE : 별이 커졌다가 제 크기로 돌아오는 정도 : 0~5
TOP_FLASH : 반짝일 때 빛줄기가 늘어나는 배수 : 0~5
T_TEAM : 썰매가 오른쪽 하늘에서 날아 들어오기 시작 : 초
T_TEAM_D : 위 길이 (초) — T_TEAM + T_TEAM_D 가 INTRO_SECONDS 를 넘지 않게 : —
FLY_FROM_X : 날아오기 시작하는 곳: 제자리에서 오른쪽으로 : 화면 좌표
FLY_FROM_Y : 날아오기 시작하는 곳: 제자리에서 위로 : 화면 좌표
FLY_SWING : 날아오는 동안 다리를 휘젓는 각도 : 도, 도착하면 0
FLY_STRIDES : 날아오는 동안 다리를 휘젓는 횟수 : 0~8
INPAINT_REACH : 장식 공·전구·선물이 나오기 전 그 자리를 메울 옆 칸을 찾는 거리 : 칸, 0~40
LAYER_REACH : 달무리·별 둘레 빛을 그 층으로 묶는 거리 : 번짐 거리 배수

--- ③ 모션 설정 ---
LOOP_SECONDS : 한 루프 길이 : 초
FPS : 초당 프레임 : 12 | 24 | 30 | 60
LOOP : 모션 반복 : —
ENV_RAMP : 루프 이음매 앞뒤로 전구 흐름·별 반짝임이 잦아드는 구간 (루프 비율, 0.01~0.3) — 이음매 = ① 정지 그림 : —
ORBITS : 한 루프 동안 썰매가 하늘을 도는 바퀴 수 : 정수, 0~4
ORBIT_R : 썰매 궤도 가로 반지름 (화면 좌표) — 크면 옆으로 화면 밖까지 나감 : —
ORBIT_DEPTH : 멀어질 때 작아지는 정도 : 0 = 크기 그대로
ORBIT_DROP : 멀어질 때 내려가는 정도 : 화면 좌표, 아래에서 올려다보는 시점
TURN_MIN : 돌아설 때 가장 좁아지는 폭 : 0.05~1
STRIDES : 한 루프 동안 순록 질주 횟수 (정수) — 30 이면 한 번에 0.4초 : —
GALLOP_SWING : 질주할 때 다리를 휘젓는 각도 : 도, 0~60
BOB : 질주할 때 순록 몸이 출렁이는 높이 : 썰매 단위
SNAPS : 한 루프 동안 산타가 고삐를 치는 횟수 : 정수, 0~12
SNAP_AT : 고삐 주기 안에서 치기 시작하는 때 : 0~1
SNAP_D : 치는 동작 길이 : 고삐 주기 비율, 0.05~0.7
ARM_LIFT : 칠 때 손이 올라가는 정도 : 썰매 단위 가로, 세로
REIN_WAVE : 칠 때 고삐 물결 높이 : 고삐 길이 비율, 0~0.5
REIN_WAVES : 고삐 위 물결 수 : —
FALL_MIN : 작은 눈송이가 한 루프 동안 화면 위→아래를 지나는 횟수 : 정수
FALL_MAX : 큰 눈송이가 지나는 횟수 (정수) — 큰 눈이 빨리 떨어짐 : —
SWAY : 눈송이 좌우 흔들림 : 화면 좌표
SWAY_CYCLES : 한 루프 동안 좌우로 흔들리는 횟수 : 정수
CHASE_LAPS : 한 루프 동안 빛 묶음이 전구 줄을 따라 지나가는 횟수 : 정수
CHASE_WAVES : 전구 줄 위의 빛 묶음 수 : 정수
CHASE_DIM : 빛 묶음 사이 전구가 어두워지는 정도 : 0~1
CHASE_BOOST : 빛 묶음 가운데 전구가 더 밝아지는 정도 : 0~2
CHASE_SHARP : 빛 묶음의 날카로움 : 1~16
BULB_PEAK_CHAR : 가장 밝은 전구 글자 : —
BULB_PEAK_AT : 이만큼 더 밝아지면 BULB_PEAK_CHAR : 0~2
BULB_DIM_CHAR : 어두워진 전구 글자 : —
BULB_DIM_AT : 밝기가 이보다 낮으면 BULB_DIM_CHAR : 0~1
BULB_PEAK_RGB : 빛 묶음 가운데 더해지는 빛 색 : RGB
TWINKLE : 하늘 별 반짝임 세기 : 0~1
TWINKLE_MIN : 별 하나가 한 루프 동안 반짝이는 횟수 하한 : 정수
TWINKLE_MAX : 상한 : 정수
STAR_HIDE : 반짝이다 이보다 어두워지면 잠깐 사라짐 : 0~1
TOP_PULSES : 한 루프 동안 꼭대기 별 빛줄기가 늘었다 줄어드는 횟수 : 정수
TOP_PULSE : 빛줄기가 늘어나는 정도 : 길이 배수, 0~3

--- 최종 출력 ---
FINAL_LOOPS : 최종 영상에서 모션 반복 횟수 : 1~20

--- 효과 ---
TRAIL : 잔상 : 0~0.97
GLOW : 글로우 : 0~1
GLOW_RADIUS : 글로우 번짐 : 칸 높이 배수
SEED : 장식 위치·별·눈송이 seed : —
<!-- end auto settings -->

<!-- auto functions -->

--- 함수 ---
tier_table : 층마다 (아래 높이, 층 높이, 아래 반지름, 위 반지름), 아래 층부터. 맨 위 층은 뾰족하다. : —
envelope : 높이 y 에서 트리 바깥 반지름 (그 높이를 지나는 층 중 가장 넓은 것). : —
gift_half : 선물 상자 반 크기 (너비, 높이, 깊이) / 2. : —
gift_local : — : —
tier_dists : 점마다 층별 거리 목록 (가지 끝 물결 포함), 아래 층부터. : —
parts : 점마다 물체별 거리: 눈 바닥, 줄기, 잎, 장식 공, 선물 (각각 (N,)). : —
make_sdf : — : —
make_color : — : —
ornament_positions : 장식 공: 층 아래쪽 가지 끝에 걸리게, 앞쪽(카메라 쪽)에 모아서. : —
bulb_positions : 전구 줄: 트리 바깥을 아래에서 위로 LIGHT_TURNS 바퀴 감고, 줄 길이를 따라 고르게. : —
horizon_y : 눈 바닥이 MAX_DIST 에서 끝나는 화면 높이 (지평선). : —
hill_top : — : —
backdrop : 하늘 그라데이션 + 달(무늬·가장자리 어둡게) + 달무리 + 먼 언덕과 작은 소나무. (rows, cols, 3) : —
moon_face : 달 원판의 밝기 (무늬 · 가장자리 어둡게), 원판 밖은 0. : —
halo : (cx, cy) 둘레 빛 (rows, cols) — 칸 하나에 한 점. : —
ell : — : —
leg : 다리 꺾은선 (순록 단위): 시작 → 무릎 → 발굽. 각도는 도, 아래 0 → 앞(−x) +. : —
strokes : 꺾은선을 두께 있는 막대들로 (부호 거리 함수). r_end 를 주면 끝으로 갈수록 가늘어짐. : —
sag_curve : a → b 사이를 아래로 처진 곡선 (2차 베지어)으로. wave: 위아래 물결 높이 (길이 비율), shift: 물결이 흘러간 정도. : —
team_layout : 썰매·산타·순록을 부위 목록으로. fills: [(부호거리 함수(X, Y), 색)] 아래→위, : —
team_bounds : 썰매 무리가 차지하는 화면 세로 범위: 선·다리·뿔의 모든 점 + 모자 끝, 여유 FIG_PAD. : —
window : 슈퍼샘플 좌표 중 화면 높이 y_bot..y_top 줄만 → (X, Y, 첫 줄, 끝 줄). : —
grow : 마스크를 n 칸 넓힌다 (상하좌우·대각). : —
paint_shapes : 채움 부위 → 밝기 글자 (+ 테두리 방향 글자), 선 → 방향 글자. 손댄 칸 마스크를 돌려준다. : —
paint_topper : 꼭대기 별: 별 모양 채움 + 테두리 방향 글자 + 둘레 빛줄기. scale: 별 크기 배수, ray_scale: 빛줄기 길이 배수. : —
pick_chars : u (0..1) → chars 중 하나의 글자 코드 (작은 u → 앞 글자). : —
setup : 한 번만 계산: 3D 트리 렌더, 배경, 전구·별·눈송이 위치. 난수는 SEED 로만. : —
loop_env : 루프 이음매(phase 0·1)에서 0, 가운데서 1. 반짝임·흐름에 곱해 이음매 = ① 정지 그림. : —
team_motion : ③ 썰매 무리: 하늘을 ORBITS 바퀴 돎 (가까우면 크게 왼쪽으로, 멀면 작게 오른쪽으로 → 달 뒤·화면 밖으로 사라짐), : —
bulb_states : ③ 전구: 빛 묶음이 줄을 따라 아래→위로 흐름. → (밝기 배수, 더해지는 빛) 전구마다. : —
draw : 완성 화면을 phase(0..1) 로 그린다. ① 에서는 움직임이 없다 (③ 에서 phase 로 움직임을 넣음). : —
paint_team : 썰매 무리 + 루돌프 코. 손댄 칸 마스크를 돌려준다. : —
scene : ① 완성 화면 = 모션의 처음. : —
intro_layers : ② 에 쓸 층 그림 (한 번만 계산해 s 에 둔다). : —
fill_in : 채워지는 칸: rv (0..1) 가 0 을 넘으면 나타나 FRONT_RGB 로 빛나다가 1 이면 제 색.  : —
progress : 채움 진행: 앞줄(head)이 순서 0→1 을 지나가고, 칸마다 앞줄이 지난 뒤 FRONT_W 동안 0→1. : —
copy_cells : — : —
swing_pose : 다리 휘젓기: 앞다리와 뒷다리를 서로 반대로 swing 도 만큼. : —
intro : ② 트리가 아래부터 글자로 차오름 → 장식이 하나씩 켜지고 달이 차오름 → 꼭대기 별 반짝 → 썰매가 날아 들어옴. : —
motion : ③ 썰매가 하늘을 돌며 왔다 갔다·사라졌다 돌아옴 (질주·고삐), 눈이 내리고, 전구 빛이 줄을 따라 흐르고, : —
<!-- end auto functions -->

--- 키 (창 재생) ---
Space : 정지 / 재생 : —
R : 등장부터 다시 : —
S : 지금 프레임을 PNG 로 저장 : —
←→ : 한 프레임 이동 : —
Esc : 끝내기 : —
