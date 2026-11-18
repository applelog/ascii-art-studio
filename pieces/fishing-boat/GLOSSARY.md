# 용어집 — 달빛 아래 낚시배

형식: `이름 : 뜻 : 단위·범위` (eyeTutorial Glossary.txt 방식 + 범위 칸). 이름 하나에 뜻 하나.

--- 일반 용어 ---
칸 : 글자 하나가 들어가는 자리 (cell) : COLS×ROWS 개
램프 : 어두움→밝음 순으로 늘어놓은 글자열 : 문자열
디더 : 칸마다 고정된 작은 흔들림을 더해 밝기 띠 무늬를 없애는 것 : 램프 단계
실루엣 : 배 안쪽 칸을 비워 어두운 형태로 보이게 하는 것 : —

--- ① 장면 설정 (맨 앞 상수) ---
COLS : 가로 칸 수 : 칸, 16~400
ROWS : 세로 칸 수 : 칸, 8~240
FONT : 글꼴 이름 또는 파일 경로 : "Menlo" 등
FONT_PX : 글자 크기 : px, 6~48
CELL_ASPECT : 칸 너비/높이 : 0.35~1.2
BACKGROUND : 바탕색 : RGB 0~255
PALETTE : 밝기에 따른 글자 색 (어두움→밝음) : RGB 목록
LANTERN_RGB : 등불·창 불빛 색 : RGB
RIM_RGB : 달빛 받은 배 윤곽선 색 : RGB
SKY_RAMP : 하늘·달 램프 : 문자열
WATER_RAMP : 바다 램프 (가로로 긴 글자 위주) : 문자열
STAR_CHARS : 별 글자 (작은 별→큰 별) : 문자열
GAMMA : 밝기 감마, 1보다 작으면 어두운 글자가 늘어남 : 0.3~2
DITHER : 칸마다 더하는 디더 폭 : 램프 단계, 0~2
DARK_CUT : 이보다 어두운 칸은 비움 : 밝기 0~1
MIN_COLOR : 글자 색 밝기 하한 : 0~1
HORIZON : 수평선 높이 : 화면 비율, 0(위)~1(아래)
SKY_GLOW : 수평선 근처 하늘 밝기 : 0~1
STAR_COUNT : 별 개수 : 개
STAR_MAX : 가장 밝은 별 밝기 : 0~1
STAR_MIN : 가장 어두운 별 밝기 : 0~1
STAR_MARGIN : 수평선 바로 위에 별을 두지 않는 여백 : 하늘 높이 비율
STAR_SKY_MAX : 이보다 밝은 하늘(달무리 등)에는 별을 두지 않음 : 밝기 0~1
SKY_GLOW_POW : 하늘이 수평선 쪽으로 밝아지는 곡선, 클수록 수평선 가까이만 밝음 : 지수 1~6
MOON_X : 달 가로 위치 : 화면 비율 0~1
MOON_Y : 달 세로 위치 : 화면 비율 0~1
MOON_R : 달 반지름 : 화면 높이 비율
CRATER : 달 표면 얼룩 세기 : 0~1
CRATER_SCALE : 달 얼룩 크기, 작을수록 큰 얼룩 : 배수
CRATER_GAIN : 달 얼룩 대비 (노이즈 × GAIN − BIAS) : 배수
CRATER_BIAS : 달 얼룩 기준값 : 0~1
MOON_LIMB : 달 가장자리가 어두워지는 정도 : 0~1
MOON_EDGE : 달 테두리 부드러움 : 칸
HALO : 달무리 밝기 : 0~1
HALO_SIZE : 달무리 퍼짐 : 화면 높이 비율
WATER_BASE : 달빛 밖 물결 기본 밝기 : 0~1
FAR_WATER : 먼 바다 물결 밝기 비율 : 0~1
WAVE_X : 물결 가로 잘게 나누는 정도 : 배수
WAVE_ROWS : 물결 세로 촘촘함 : 배수
PATH_W0 : 수평선에서 달빛 길 폭 : 화면 너비 비율
PATH_W1 : 아래로 갈수록 달빛 길 폭 증가 : 화면 너비 비율
PATH_BRIGHT : 달빛 길 밝기 : 배수
PATH_FLOOR : 반짝임이 없는 곳의 달빛 길 밝기 : 0~1
PATH_FADE : 화면 아래로 갈수록 달빛 길이 약해지는 정도 : 0~1
GLITTER_GAIN : 달빛 반짝임 대비 (물결 × GAIN − BIAS) : 배수
GLITTER_BIAS : 달빛 반짝임 기준값 : 0~2
PERSPECTIVE : 원근 세기, 작을수록 수평선 쪽 물결이 촘촘 : 0.01~0.3
WAVE_NEAR : 수평선 근처 물결이 가로로 늘어나는 한계 : 0.01~0.5
WAVE_FLOOR : 물결 밝기 바닥값 : 0~1
RIPPLE2_MIX : 잔물결(두 번째 물결 층) 섞는 비율 : 0~1
RIPPLE2_SCALE : 잔물결 크기 (가로, 세로) : 배수 쌍
BOAT_X : 배 가운데 가로 위치 : 화면 비율 0~1
BOAT_Y : 배 흘수선 세로 위치 : 화면 비율 0~1
BOAT_W : 배 길이 : 화면 너비 비율
HULL_ROWS : 선체 높이 : 칸
HULL_TAPER : 선체 아래가 좁아지는 정도 (한쪽) : 배 길이 비율
CABIN_W : 조타실 너비 : 배 길이 비율
CABIN_ROWS : 조타실 높이 : 칸
CABIN_X : 조타실 위치 (−는 뒤쪽) : 배 길이 비율
MAST_ROWS : 돛대 높이 : 칸
MAST_X : 돛대 위치 : 배 길이 비율
ROD_ROWS : 낚싯대 높이 : 칸
ROD_COLS : 낚싯대가 뒤로 뻗는 길이 : 칸
LANTERN_GLOW : 등불 빛이 퍼지는 거리 : 칸
LANTERN_TINT : 등불 근처 글자에 주황을 섞는 최대 비율 : 0~1
LANTERN_DX : 등불이 돛대 꼭대기에서 오른쪽으로 떨어진 거리 : 칸
LANTERN_DY : 등불이 돛대 꼭대기에서 아래로 떨어진 거리 : 칸
LANTERN_CHAR : 등불 글자 : 한 글자
WINDOW_CHAR : 조타실 불 켜진 창 글자 : 한 글자
MAST_TOP_CHAR : 돛대 꼭대기 글자 : 한 글자
ROD_INSET : 낚싯대 뿌리가 배 뒤 끝에서 안쪽으로 들어온 거리 : 칸
LINE_RGB : 낚싯줄 색 : RGB
LINE_CHAR : 낚싯줄 글자 : 한 글자
LINE_GAP : 낚싯줄 점 간격 : 칸
LINE_DEPTH : 낚싯줄이 물속으로 들어가는 길이 : 칸
REFLECT_ROWS : 물에 비친 등불 길이 : 칸
REFLECT_GAP : 등불 반사 줄 간격 : 칸
REFLECT_CHARS : 등불 반사 글자 (가까운 쪽, 먼 쪽) : 두 글자
REFLECT_SPLIT : 이 밝기 아래부터 두 번째 반사 글자 : 0~1
REFLECT_MIN : 등불 반사 끝 밝기 비율 : 0~1
SEED : 별·물결·디더 난수 seed : 정수
NOISE_SIZE : 노이즈 난수표 크기 : 칸, 16~512
MOON_SPOT_SHIFT : 달 얼룩 무늬 위치, 바꾸면 얼룩 배치만 달라짐 : 노이즈 좌표
RIPPLE2_SHIFT : 잔물결 무늬 위치, 바꾸면 물결 배치만 달라짐 : 노이즈 좌표 쌍

--- 함수 ---
cell_hash : 칸 좌표 → 0~1 고정 값 (디더용) : —
value_noise : 난수표를 부드럽게 보간한 노이즈 : 0~1
lum_to_chars : 밝기 → 램프 글자 코드 : —
palette_color : 밝기 → PALETTE 보간 색 : RGB
setup : 좌표·노이즈 표·별 위치를 한 번 계산 : —
sky_and_moon : 하늘·달·달무리 밝기와 달 마스크 : —
sea : 원근 물결 + 달빛 길 밝기 : —
boat_shape : 배 실루엣 마스크와 윤곽 글자 목록 : —
scene : ① 완성 화면을 grid 에 채움 : —

--- 장면 변수 (setup 결과) ---
xx, yy : 칸의 열·행 번호 배열 : 칸
px, py : 칸 중심 좌표 (칸 높이 단위, 정사각) : 칸 높이
width : 화면 너비 (칸 높이 단위) : 칸 높이
u, v : 화면 비율 좌표 (가로, 세로) : 0~1
noise : 값 노이즈 난수표 : 128×128
stars : 별 (열, 행, 밝기) 목록 : —

--- 키 (창 보기) ---
아무 키 : 창 닫기 (재생 키는 F3에서 추가)
