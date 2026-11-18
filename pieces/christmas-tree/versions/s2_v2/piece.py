"""크리스마스 트리 — 눈 내린 밤, 불 켜진 트리와 달 앞을 나는 산타 썰매

요청: "이제 크리스마스니까 크리스마스 트리 만드는걸로 하자"
설명: brief.md   용어: GLOSSARY.md
단계: ① scene (완성 화면) → ② intro (등장) → ③ motion (모션)

    python piece.py                     창: 등장 한 번 → 모션 반복 (R: 등장부터 다시)
    python piece.py --stage 1           ① 완성 화면 PNG
    python piece.py --stage 2           ② 등장 MP4 + 프레임 띠
    python piece.py --stage 3           ③ 모션 MP4 + 프레임 띠
    python piece.py --final             최종 MP4 + 대표 그림
    python piece.py --check             단계 연결 검사 (① = ② 끝 = ③ 처음 = ③ 끝)
"""
# ===== ① 장면 설정: 여기 값만 바꾸면 아래 코드 전체가 따라 바뀝니다 =====
# --- 화면 ---
COLS           = 180                    # 가로 글자 칸 수 (16~400)
ROWS           = 192                    # 세로 글자 칸 수 (8~240) — 180×192 칸 × 6×10 px = 1080×1920 (9:16)
FONT           = "Menlo"                # 글꼴 이름 또는 .ttf/.ttc 경로 — Menlo 에는 한글이 없음
FONT_PX        = 9                      # 글자 크기 px (6~48) — 9 이면 칸 6×10 px
CELL_ASPECT    = 0.6                    # 칸 너비/높이 (0.35~1.2)
BACKGROUND     = (3, 5, 16)             # 바탕색 (RGB 0~255)
SUPERSAMPLE    = 2                      # 칸 하나를 몇×몇 점으로 계산 (1~3)
RAMP           = " .:-=+*#%@"           # 밝기 순 글자 (첫 글자는 빈칸)
GAMMA          = 0.85                   # 밝기 감마 — 1 보다 작으면 어두운 글자가 늘어남 (0.3~2)
CUT            = 0.05                   # 이보다 어두우면 빈칸 (0~1)
DITHER         = 1.0                    # 칸마다 고정 디더 폭 — 띠 무늬 제거 (0~2)
MIN_COLOR      = 0.35                   # 글자 색 밝기 하한 (0~1)
# --- 하늘 · 달 · 별 ---
SKY_TOP_RGB    = (3, 6, 22)             # 하늘 꼭대기 색 (RGB)
SKY_LOW_RGB    = (16, 26, 62)           # 지평선 근처 하늘 색 (RGB)
MOON_X         = 0.06                   # 달 가로 위치, 가운데 0 (화면 좌표, 세로 절반 = 1)
MOON_Y         = 0.6                    # 달 세로 위치 (−1 아래 … 1 위)
MOON_R         = 0.34                   # 달 반지름 (화면 좌표)
MOON_RGB       = (255, 240, 205)        # 달 색 (RGB)
MOON_SPOTS     = 0.12                   # 달 무늬 진하기 (0~1)
MOON_SPOT_SCALE = 6.0                   # 달 무늬 촘촘함 (1~40)
MOON_LIMB      = 0.15                   # 달 가장자리가 어두워지는 정도 (0~1)
MOON_HALO      = 0.15                   # 달 둘레 빛 세기 (0~1)
MOON_HALO_R    = 0.05                   # 달 둘레 빛 번짐 거리 (화면 좌표)
MOON_RAMP      = " .:-=+*#"             # 달 글자 (밝기 순) — 고른 # 바탕이라 실루엣이 또렷함
MOON_GAMMA     = 0.3                    # 달 글자 감마 — 작을수록 # 이 많아짐 (0.1~2)
MOON_DITHER    = 0.4                    # 달 글자 디더 폭 (0~2)
STARS          = 0.014                  # 하늘 칸 중 별이 있는 비율 (0~0.2)
STAR_CHARS     = ".'+*"                 # 별 글자 (작은 별 → 큰 별)
STAR_RGB       = (190, 205, 255)        # 별 색 (RGB)
# --- 땅 · 먼 언덕 ---
HILL_H         = 0.06                   # 먼 언덕 높이 (화면 좌표)
HILL_WAVES     = 3.0                    # 화면 너비에 들어가는 언덕 굴곡 수 (0.5~12)
HILL_RGB       = (70, 84, 126)          # 달빛 받은 먼 눈 언덕 색 (RGB)
HILL_PINES     = 16                     # 언덕 위 작은 소나무 수 (0~60)
HILL_PINE_H    = 0.05                   # 작은 소나무 높이 (화면 좌표)
HILL_PINE_W    = 0.018                  # 작은 소나무 밑변 절반 (화면 좌표)
HILL_PINE_RGB  = (12, 22, 40)           # 작은 소나무 색 (RGB)
SNOW_RGB       = (74, 86, 126)          # 가까운 눈 바닥 색 (RGB)
SNOW_TOL       = 0.06                   # 칸 깊이가 바닥까지 거리의 이 비율 안이면 눈 바닥으로 봄 (0.01~0.3)
SNOW_RAMP      = " .,:;=*"              # 눈 바닥 글자 (밝기 순) — 가로줄로 보이는 - 를 빼서 알갱이 느낌
HILL_DIST      = 22.0                   # 이보다 먼 눈 바닥은 먼 언덕으로 덮음 (거리)
SNOW_GRAIN     = 0.55                   # 눈 바닥 얼룩 세기 (0~1)
SNOW_GRAIN_SCALE = 1.2                  # 눈 바닥 얼룩 크기 (1/거리)
SNOW_SPARKLE   = 0.02                   # 눈 바닥 칸 중 반짝이는 비율 (0~0.3)
SNOW_SPARKLE_CHARS = "'*+"              # 눈 반짝임 글자
SNOW_SPARKLE_RGB = (235, 242, 255)      # 눈 반짝임 색 (RGB)
# --- 3D 카메라 · 달빛 ---
CAMERA_POS     = (0.0, 1.5, -12.2)      # 카메라 위치 (x 오른쪽, y 위, z 안쪽)
CAMERA_TARGET  = (0.0, 3.25, 0.0)       # 카메라가 보는 곳
FOV            = 40                     # 세로 화각 (도, 10~120)
LIGHT_DIR      = (0.55, 0.65, -0.5)     # 달빛이 오는 쪽 (오른쪽 위 앞)
AMBIENT        = 0.3                    # 그늘 밝기 (0~1)
RIM            = 0.18                   # 테두리 빛 세기 (0~1)
LIGHT_GAIN     = 1.45                   # 달빛 세기 배수 (0~3)
FOG            = 0.05                   # 거리 안개 세기 (FOG_START 보다 먼 곳이 지평선 색으로)
FOG_START      = 13.0                   # 안개가 시작되는 거리 (트리 바로 뒤)
FOG_RGB        = (12, 16, 34)           # 먼 곳 색 (RGB)
MAX_STEPS      = 90                     # 레이마칭 최대 걸음 (16~200)
MAX_DIST       = 40.0                   # 레이마칭 최대 거리 (지평선)
STEP_SAFETY    = 0.7                    # 가지 끝 물결 때문에 걸음을 줄이는 비율 (0.3~1)
# --- 트리 (단위: 바닥 위 거리) ---
TREE_H         = 3.3                    # 잎 부분 높이 (가장 아래 가지 → 꼭대기)
TREE_R         = 1.15                   # 가장 아래 층 반지름 — 높이:너비 ≈ 1.45 (사진 1.5~1.6)
TREE_BASE      = 0.32                   # 가장 아래 가지 높이 (그 아래는 줄기)
TIERS          = 5                      # 가지 층 수 (1~9)
TIER_OVERLAP   = 0.42                   # 층이 겹치는 비율 (0~0.8)
TIER_TOP       = 0.3                    # 층 위쪽 반지름 / 아래쪽 반지름 (0~1)
TIER_TWIST     = 1.3                    # 층마다 가지 끝을 엇갈리게 돌리는 각도 (라디안)
BRANCHES       = 12                     # 층마다 가지 끝 개수 (3~30)
SCALLOP        = 0.1                    # 가지 끝이 튀어나온 정도 (0~0.3)
NEEDLE_RGB     = (56, 168, 82)          # 밝은 잎 색 (RGB)
NEEDLE_DARK_RGB = (14, 64, 36)          # 안쪽 어두운 잎 색 (RGB)
NEEDLE_GRAIN   = 6.0                    # 잎 결 촘촘함 (1/거리)
NEEDLE_GRAIN_MIX = 0.45                 # 잎 결이 색에 섞이는 비율 (0~1)
TREE_OUTLINE   = True                   # 트리 바깥 테두리를 방향 글자 / \ | - 로
TREE_OUTLINE_RGB = (110, 214, 120)      # 트리 테두리 글자 색 (RGB)
TRUNK_R        = 0.16                   # 줄기 반지름
TRUNK_RGB      = (92, 58, 34)           # 줄기 색 (RGB)
ORNAMENTS      = 30                     # 장식 공 개수 (0~120)
ORNAMENT_R     = 0.11                   # 장식 공 반지름
ORNAMENT_COLORS = [(215, 28, 40), (242, 184, 58)]   # 장식 공 색 (클래식: 빨강, 금색)
ORNAMENT_SHINE = 0.9                    # 장식 공 하이라이트 세기 (0~2)
ORNAMENT_SHININESS = 24                 # 장식 공 하이라이트 날카로움 (2~200)
ORNAMENT_FRONT = 1.9                    # 장식 공을 앞쪽에 모으는 각도 범위 (라디안, ±)
ORNAMENT_LOW   = 0.2                    # 층 안에서 장식 공 높이 아래 끝 (0~1, 0 = 층 아래)
ORNAMENT_HIGH  = 0.7                    # 층 안에서 장식 공 높이 위 끝 (0~1)
# --- 전구 줄 ---
BULBS          = 150                    # 전구 개수 (0~600)
LIGHT_TURNS    = 5.5                    # 전구 줄이 트리를 감는 바퀴 수
BULB_TOP       = 0.93                   # 전구 줄이 올라가는 높이 (잎 높이 비율, 0~1)
BULB_LIFT      = 0.1                    # 잎 표면에서 전구를 띄운 거리
BULB_CHAR      = "*"                    # 전구 글자
BULB_RGB       = (255, 212, 112)        # 전구 색 (RGB, 따뜻한 노랑)
BULB_SPILL     = 0.5                    # 전구 빛이 잎·눈을 밝히는 세기 (0~2)
BULB_SPILL_R   = 2.6                    # 전구 빛 번짐 (칸 높이 배수)
ARC_SAMPLES    = 4000                   # 전구 간격을 고르게 잡을 때 줄을 나누는 수
# --- 꼭대기 별 ---
TOPPER_LIFT    = 0.12                   # 별 가운데가 트리 꼭대기보다 높은 거리
TOPPER_R       = 0.07                   # 별 반지름 (화면 좌표)
TOPPER_INNER   = 0.45                   # 별 안쪽 반지름 비율 (0.2~0.9)
TOPPER_RGB     = (255, 214, 80)         # 별 색 (RGB)
TOPPER_RAY     = 0.04                   # 빛줄기 길이 (화면 좌표)
TOPPER_RAYS    = 5                      # 빛줄기 수 (0~16) — 별 꼭짓점 사이로 뻗음
TOPPER_RAY_RGB = (255, 236, 160)        # 빛줄기 색 (RGB)
TOPPER_GLOW    = 0.22                   # 별 둘레 빛 세기 (0~1)
TOPPER_GLOW_R  = 0.04                   # 별 둘레 빛 번짐 거리 (화면 좌표)
# --- 선물 상자: (x, z, 너비, 높이, 깊이, 돌린 각도, 상자 색, 리본 색) ---
GIFTS          = [(-0.95, -1.05, 0.46, 0.36, 0.42, 0.35, (205, 30, 40), (245, 200, 80)),
                  (0.85, -1.1, 0.38, 0.5, 0.36, -0.3, (236, 190, 72), (205, 30, 40)),
                  (-0.08, -1.5, 0.42, 0.28, 0.38, 0.12, (232, 232, 238), (205, 30, 40)),
                  (1.5, -0.55, 0.32, 0.3, 0.32, 0.5, (40, 140, 80), (245, 200, 80)),
                  (-1.55, -0.45, 0.3, 0.24, 0.3, -0.4, (232, 232, 238), (40, 140, 80))]
GIFT_ROUND     = 0.02                   # 상자 모서리 둥글기
RIBBON_W       = 0.045                  # 리본 절반 폭
BOW_R          = 0.055                  # 리본 매듭 공 반지름
GIFT_GAIN      = 1.7                    # 선물 상자 밝기 배수 — 트리 불빛을 받아 그늘에서도 보이게 (1~3)
# --- 산타 썰매 (썰매 단위: 썰매 길이 ≈ 2, 왼쪽이 앞, 화면에서는 TEAM_SCALE 배) ---
TEAM_X         = 0.255                  # 썰매 가운데 가로 위치 (화면 좌표)
TEAM_Y         = 0.538                  # 썰매 가운데 세로 위치 (화면 좌표)
TEAM_SCALE     = 0.11                   # 썰매 단위 1 = 화면 길이 (0.03~0.5)
TEAM_TILT      = 0.15                   # 앞(왼쪽)이 들린 각도 (라디안)
FIG_RAMP       = " -=+*#%@"             # 썰매·순록 채움 글자 (밝기 순)
FIG_LIFT       = 0.45                   # 채움 글자 밝기 하한 (0~1) — 어두운 색도 글자가 보이게
FIG_COVER      = 0.35                   # 칸이 이만큼 덮이면 그 부위로 칠함 (0.05~0.95)
FIG_OUTLINE    = False                  # 테두리 칸은 방향 글자 / - \ | 로
SILHOUETTE     = True                   # 달과 겹친 부분은 검은 실루엣(빈칸)으로, 밖은 색 글자로
SIL_EDGE       = True                   # 실루엣 둘레의 달 글자를 윤곽 방향 글자 / \ | - 로
FIG_GAP        = 1                      # 달 위에서 썰매·순록 둘레를 비우는 칸 수 (0~3)
FIG_PAD        = 0.3                    # 썰매 무리 계산 범위 여유 (썰매 단위)
SLEIGH_RGB     = (204, 28, 40)          # 썰매 몸통 색 (RGB)
SLEIGH_TRIM_RGB = (242, 192, 72)        # 썰매 금색 장식·날 색 (RGB)
SLEIGH_BODY    = [(0.8, -0.2), (0.9, 0.38), (0.84, 0.56), (0.64, 0.52), (0.42, 0.12), (-0.4, 0.1), (-0.66, 0.22), (-0.8, 0.42), (-0.96, 0.38), (-0.94, 0.16), (-0.8, -0.04), (-0.6, -0.2)]   # 썰매 몸통 (꼭짓점): 높은 등받이, 앞이 휘어 올라감
SLEIGH_SCROLL  = [(-0.8, 0.42), (-0.9, 0.5), (-1.0, 0.42), (-0.97, 0.32)]   # 앞 장식 말림 (금색 선)
SLEIGH_RIM     = [(0.84, 0.56), (0.64, 0.52), (0.42, 0.12), (-0.4, 0.1), (-0.66, 0.22), (-0.8, 0.42)]   # 몸통 위 금색 테두리
RUNNER         = [(0.92, -0.42), (-0.7, -0.42), (-0.92, -0.36), (-1.04, -0.2), (-1.02, -0.06), (-0.94, -0.04)]   # 썰매 날 (앞이 말려 올라감)
STRUTS         = [((-0.5, -0.42), (-0.5, -0.2)), ((0.55, -0.42), (0.55, -0.2))]   # 날과 몸통을 잇는 기둥
SACK           = (0.56, 0.62, 0.24, 0.24)   # 선물 자루 (x, y, 가로 반지름, 세로 반지름) — 등받이 뒤로 보임
SACK_RGB       = (140, 92, 50)          # 선물 자루 색 (RGB)
SANTA_BODY     = (0.08, 0.32, 0.25, 0.28)   # 산타 몸 (x, y, 가로 반지름, 세로 반지름)
SANTA_HEAD     = (0.0, 0.72, 0.11)    # 얼굴 (x, y, 반지름)
SANTA_BEARD    = (-0.06, 0.6, 0.13, 0.15)   # 수염 (x, y, 가로 반지름, 세로 반지름)
SANTA_HAT      = [(-0.13, 0.78), (0.16, 0.82), (0.42, 0.98)]   # 모자 (꼭짓점, 끝이 뒤로 넘어감)
SANTA_HAT_TRIM = ((-0.13, 0.79), (0.16, 0.83), 0.045)   # 모자 흰 테 (시작, 끝, 두께)
SANTA_POMPOM   = (0.44, 0.95, 0.06)     # 모자 끝 방울 (x, y, 반지름)
SANTA_ARM      = ((0.0, 0.44), (-0.4, 0.32), 0.075)   # 팔 (어깨, 손, 두께)
SANTA_MITT_R   = 0.06                   # 장갑 반지름
SANTA_COAT_RGB = (218, 30, 38)          # 산타 옷 색 (RGB)
SANTA_FUR_RGB  = (246, 246, 240)        # 흰 털·수염 색 (RGB)
SANTA_SKIN_RGB = (240, 186, 152)        # 얼굴 색 (RGB)
SANTA_MITT_RGB = (52, 40, 34)           # 장갑 색 (RGB)
# --- 순록 (순록 단위: 몸 길이 ≈ 0.9, 왼쪽이 앞) ---
REINDEER       = 2                      # 순록 수, 맨 앞이 루돌프 (1~6) — 이 해상도에서 실루엣이 읽히는 크기로 2마리
DEER_SIZE      = 1.0                    # 순록 크기 (썰매 단위 배수)
DEER_FIRST     = 1.9                    # 썰매 가운데 → 첫 순록 가운데 (썰매 단위)
DEER_GAP       = 1.7                    # 순록 사이 간격 (썰매 단위) — 앞 순록 뒷다리가 뒤 순록 머리에 닿지 않게
DEER_Y         = 0.16                   # 순록 몸 높이 (썰매 단위)
DEER_RGB       = (130, 86, 52)          # 순록 털 색 (RGB)
DEER_DARK_RGB  = (82, 56, 38)           # 다리·먼 쪽 색 (RGB)
DEER_PALE_RGB  = (226, 214, 190)        # 목 갈기·엉덩이 흰 털 색 (RGB) — 사진에서 본 특징
ANTLER_RGB     = (218, 198, 152)        # 뿔 색 (RGB)
DEER_BODY      = (0.0, 0.0, 0.42, 0.15)     # 몸통 (x, y, 가로 반지름, 세로 반지름)
DEER_CHEST     = (-0.28, 0.02, 0.19, 0.19)  # 가슴 (깊은 가슴)
DEER_RUMP      = (0.32, 0.04, 0.16, 0.16)   # 엉덩이
DEER_NECK      = ((-0.3, 0.08), (-0.5, 0.36), 0.1, 0.07)   # 목 (시작, 끝, 굵기 시작, 굵기 끝) — 앞으로 뻗은 목
DEER_HEAD      = ((-0.5, 0.4), (-0.78, 0.3), 0.075, 0.05)  # 머리 (정수리, 코끝, 굵기 시작, 굵기 끝)
DEER_RUFF      = (-0.4, 0.1, 0.06, 0.09)  # 목 아래 흰 갈기
DEER_TAIL      = (0.47, 0.1, 0.05, 0.06)    # 엉덩이 흰 꼬리
ANTLER         = [[(-0.48, 0.43), (-0.36, 0.62), (-0.2, 0.8), (-0.12, 1.02)],
                  [(-0.4, 0.56), (-0.6, 0.8)], [(-0.28, 0.72), (-0.36, 1.0)], [(-0.16, 0.9), (0.02, 0.98)]]   # 뿔: 뒤로 휜 줄기 + 앞·위·뒤 가지 (가지 사이를 2칸 이상 띄움)
ANTLER_FAR     = (0.16, -0.02)          # 먼 쪽 뿔이 어긋난 정도
SHOULDER       = (-0.3, -0.08)          # 앞다리 시작점
HIP            = (0.3, -0.06)           # 뒷다리 시작점
LEG_UPPER      = 0.28                   # 윗다리 길이 — 순록 다리는 길고 가늘다 (사진)
LEG_LOWER      = 0.3                    # 아랫다리 길이
LEG_R          = 0.055                  # 다리 굵기 (반지름, 발굽 쪽은 LEG_R_END)
LEG_R_END      = 0.04                   # 발굽 쪽 다리 굵기
ANTLER_R       = 0.04                   # 뿔 굵기 (반지름)
LEG_POSE       = [(60, -20), (35, -50), (-60, -85), (-40, -70)]   # 다리 각도 (도, 아래 0 → 앞 +): 가까운 앞, 먼 앞, 가까운 뒤, 먼 뒤 (윗다리, 아랫다리) — 하늘을 나는 자세
NOSE           = (-0.8, 0.3, 0.045)     # 루돌프 코 (x, y, 반지름)
NOSE_RGB       = (255, 44, 30)          # 루돌프 코 색 (RGB)
NOSE_CHAR      = "@"                    # 루돌프 코 글자 (실루엣 위에서도 보임)
NOSE_GLOW      = 0.6                    # 코 둘레 빛 세기 (0~1)
NOSE_GLOW_R    = 0.035                  # 코 둘레 빛 번짐 거리 (화면 좌표)
COLLAR         = ((-0.36, 0.0), (-0.47, 0.24))   # 목줄 (순록 단위) — 고삐가 닿는 곳
TRACE_FRONT    = (-0.3, -0.02)          # 끈이 순록 가슴에 닿는 곳 (순록 단위)
SLEIGH_HITCH   = (-0.94, -0.04)         # 끈이 썰매에 닿는 곳 (썰매 단위)
REIN_SAG       = 0.12                   # 고삐가 처지는 정도 (길이 비율, 0~0.5)
REIN_SEGMENTS  = 10                     # 고삐 곡선을 나누는 수 (2~40)
REIN_RGB       = (205, 160, 112)        # 고삐·끈 색 (RGB)
# --- 내리는 눈 ---
FLAKES         = 240                    # 눈송이 수 (0~800)
FLAKE_CHARS    = ".*+"                  # 눈송이 글자 (작은 것 → 큰 것)
FLAKE_RGB      = (226, 234, 255)        # 눈송이 색 (RGB)
# ===== ② 등장 설정: 트리가 아래부터 글자로 차오름 → 장식이 하나씩 켜지고 달이 차오름 → 별 반짝 → 썰매가 날아 들어옴 =====
INTRO_SECONDS  = 6.0                    # 등장 길이 (초)
INTRO_HOLD     = 1.0                    # 등장 검토 영상 끝에 완성 화면을 보여 주는 시간 (초)
T_GROUND       = 0.0                    # 하늘 별·눈 바닥·눈송이가 스며 나오기 시작 (초)
T_GROUND_D     = 0.8                    # 위 길이 (초)
T_TREE         = 0.3                    # 트리가 아래(줄기)부터 글자로 차오르기 시작 (초)
T_TREE_D       = 2.5                    # 위 길이 (초)
FILL_JITTER    = 0.08                   # 차오르는 줄의 들쭉날쭉함 (순서 0~1 기준, 0~0.5)
FRONT_W        = 0.06                   # 막 채워진 글자가 빛나는 띠의 두께 (순서 0~1 기준, 0.01~0.5)
FRONT_RGB      = (225, 255, 238)        # 막 채워진 글자의 빛 색 (RGB) — 자리 잡으며 제 색으로
FLY_SHARE      = 0.03                   # 트리 글자 중 멀리서 날아와 자리를 찾는 비율 (0~0.3) — 날아와 자리를 찾는 연출
FLY_CELLS      = 10                     # 날아오는 글자가 출발하는 거리 (칸, 0~40)
T_DECOR        = 2.8                    # 장식 공·선물이 하나씩 반짝 켜지고 전구가 줄을 따라 켜지기 시작 (초)
T_DECOR_D      = 1.4                    # 위 길이 (초)
T_MOON         = 2.8                    # 달이 오른쪽부터 글자로 채워지며 보름달로 차오르기 시작 (초) — 장식과 동시에
T_MOON_D       = 1.4                    # 위 길이 (초)
T_TOP          = 4.2                    # 꼭대기 별이 반짝하며 나타나기 시작 (초)
T_TOP_D        = 0.8                    # 위 길이 (초)
TOP_BOUNCE     = 2.2                    # 별이 커졌다가 제 크기로 돌아오는 정도 (0~5)
TOP_FLASH      = 2.0                    # 반짝일 때 빛줄기가 늘어나는 배수 (0~5)
T_TEAM         = 4.6                    # 썰매가 오른쪽 하늘에서 날아 들어오기 시작 (초)
T_TEAM_D       = 1.4                    # 위 길이 (초) — T_TEAM + T_TEAM_D 가 INTRO_SECONDS 를 넘지 않게
FLY_FROM_X     = 0.9                    # 날아오기 시작하는 곳: 제자리에서 오른쪽으로 (화면 좌표)
FLY_FROM_Y     = 0.1                    # 날아오기 시작하는 곳: 제자리에서 위로 (화면 좌표)
FLY_SWING      = 22                     # 날아오는 동안 다리를 휘젓는 각도 (도, 도착하면 0)
FLY_STRIDES    = 3                      # 날아오는 동안 다리를 휘젓는 횟수 (0~8)
INPAINT_REACH  = 12                     # 장식 공·전구·선물이 나오기 전 그 자리를 메울 옆 칸을 찾는 거리 (칸, 0~40)
LAYER_REACH    = 3                      # 달무리·별 둘레 빛을 그 층으로 묶는 거리 (번짐 거리 배수)
# ===== ③ 모션 설정 =====
LOOP_SECONDS   = 6                      # 한 루프 길이 (초)
FPS            = 30                     # 초당 프레임 (12 | 24 | 30 | 60)
LOOP           = True                   # 모션 반복
# ===== 최종 출력 =====
FINAL_LOOPS    = 2                      # 최종 영상에서 모션 반복 횟수 (1~20)
# ===== 효과 =====
TRAIL          = 0.0                    # 잔상 (0~0.97)
GLOW           = 0.3                    # 글로우 (0~1)
GLOW_RADIUS    = 0.8                    # 글로우 번짐 (칸 높이 배수)
SEED           = 7                      # 장식 위치·별·눈송이 seed
RANGES         = {"SUPERSAMPLE": (1, 3), "FLY_CELLS": (0, 40), "FILL_JITTER": (0, 0.5), "FRONT_W": (0.01, 0.5), "FLY_SHARE": (0, 0.3), "INPAINT_REACH": (0, 40), "FLY_STRIDES": (0, 8), "TIERS": (1, 9), "BRANCHES": (3, 30),
                  "ORNAMENTS": (0, 120), "BULBS": (0, 600), "REINDEER": (1, 6), "FLAKES": (0, 800),
                  "FIG_COVER": (0.05, 0.95), "FIG_GAP": (0, 3), "STEP_SAFETY": (0.3, 1), "FOV": (10, 120),
                  "MAX_STEPS": (16, 200), "TOPPER_RAYS": (0, 16), "HILL_PINES": (0, 60), "REIN_SEGMENTS": (2, 40)}
# ===== 코드 =====
import math
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(_d, "asciiart")) and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

import numpy as np  # noqa: E402

from asciiart import shapes as S  # noqa: E402
from asciiart import three as T  # noqa: E402
from asciiart.color import rgb01  # noqa: E402
from asciiart.ease import ease_out, overshoot, segment, smoothstep  # noqa: E402
from asciiart.grid import Grid  # noqa: E402
from asciiart.noise import fbm, noise2  # noqa: E402
from asciiart.post import blur  # noqa: E402
from asciiart.ramp import cell_hash, codes_of, edge_chars, edges, ramp_chars  # noqa: E402
from asciiart.run import run  # noqa: E402
from asciiart.shade import coords, field_to_grid, half_width, luminance, shade  # noqa: E402


# ---------- 3D: 트리 · 장식 공 · 선물 · 눈 바닥 ----------
def tier_table():
    """층마다 (아래 높이, 층 높이, 아래 반지름, 위 반지름), 아래 층부터. 맨 위 층은 뾰족하다."""
    n = int(TIERS)
    tier_h = TREE_H / (1 + (n - 1) * (1 - TIER_OVERLAP))
    step = tier_h * (1 - TIER_OVERLAP)
    out = []
    for i in range(n):
        r1 = TREE_R * (1 - i * step / TREE_H)
        out.append((TREE_BASE + i * step, tier_h, r1, 0.0 if i == n - 1 else r1 * TIER_TOP))
    return out


def envelope(y, tiers):
    """높이 y 에서 트리 바깥 반지름 (그 높이를 지나는 층 중 가장 넓은 것)."""
    r = np.zeros_like(np.asarray(y, np.float64))
    for y0, h, r1, r2 in tiers:
        v = (y - y0) / h
        r = np.where((v >= 0) & (v <= 1), np.maximum(r, r1 + (r2 - r1) * v), r)
    return r


PARTS = ["snow", "trunk", "foliage", "balls", "gifts"]      # parts() 가 돌려주는 순서
SNOW, TRUNK, FOLIAGE, BALLS, GIFT = range(len(PARTS))


def gift_half(g):
    """선물 상자 반 크기 (너비, 높이, 깊이) / 2."""
    x, z, w, h, d, turn, box_rgb, ribbon_rgb = g
    return np.array([w, h, d]) / 2


def gift_local(p, g):
    x, z, w, h, d, turn, box_rgb, ribbon_rgb = g
    return T.local(p, T.rot_y(turn), (x, h / 2, z))


def tier_dists(p, s):
    """점마다 층별 거리 목록 (가지 끝 물결 포함), 아래 층부터."""
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    ang = np.arctan2(z, x)
    out = []
    for i, (y0, h, r1, r2) in enumerate(s["tiers"]):
        v = np.clip(1 - (y - y0) / h, 0, 1)                      # 층 아래 끝일수록 가지 끝이 튀어나옴
        k = 1 + SCALLOP * v * np.cos(BRANCHES * ang + i * TIER_TWIST)
        q = np.stack([x / k, y - (y0 + h / 2), z / k], -1)
        out.append(T.capped_cone(q, h / 2, r1, r2))
    return out


def parts(p, s):
    """점마다 물체별 거리: 눈 바닥, 줄기, 잎, 장식 공, 선물 (각각 (N,))."""
    y = p[..., 1]
    foliage = np.minimum.reduce(tier_dists(p, s))
    trunk = T.cylinder(p - np.array([0, TREE_BASE / 2, 0]), TRUNK_R, TREE_BASE)
    orn = s["orn_pos"]
    balls = (np.linalg.norm(p[..., None, :] - orn, axis=-1).min(axis=-1) - ORNAMENT_R) if len(orn) else np.full(y.shape, np.inf)
    gifts = np.full(y.shape, np.inf)
    for g in GIFTS:
        q = gift_local(p, g)
        half = gift_half(g)
        box = T.round_box(q, half, GIFT_ROUND)
        top = half[1] + BOW_R / 2
        bow = np.minimum(T.sphere(q - np.array([BOW_R, top, 0]), BOW_R), T.sphere(q - np.array([-BOW_R, top, 0]), BOW_R))
        gifts = np.minimum(gifts, np.minimum(box, bow))
    return [y, trunk, foliage, balls, gifts]


def make_sdf(s):
    def sdf(p):
        return np.minimum.reduce(parts(p, s)) * STEP_SAFETY
    return sdf


def make_color(s):
    tiers = s["tiers"]
    light = T.normalize(np.array(LIGHT_DIR, np.float64))
    cam = np.array(CAMERA_POS, np.float64)
    orn_rgb = np.array([rgb01(ORNAMENT_COLORS[k % len(ORNAMENT_COLORS)]) for k in range(len(s["orn_pos"]))])

    def color(p, n):
        which = np.argmin(np.stack(parts(p, s), -1), axis=-1)
        out = np.empty(p.shape)
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        # 눈 바닥: 얼룩
        grain = fbm(x * SNOW_GRAIN_SCALE, z * SNOW_GRAIN_SCALE, seed=SEED)
        out[:] = rgb01(SNOW_RGB) * (1 - SNOW_GRAIN + SNOW_GRAIN * grain)[:, None]
        # 줄기
        out[which == TRUNK] = rgb01(TRUNK_RGB)
        # 잎: 바깥 가지 끝은 밝고 안쪽·위층 그늘은 어둡다 + 잎 결
        m = which == FOLIAGE
        if m.any():
            radial = np.clip(np.hypot(x[m], z[m]) / np.maximum(envelope(y[m], tiers), TRUNK_R), 0, 1)
            g = fbm(x[m] * NEEDLE_GRAIN, y[m] * NEEDLE_GRAIN, z[m] * NEEDLE_GRAIN, seed=SEED)
            t = np.clip((1 - NEEDLE_GRAIN_MIX) * radial + NEEDLE_GRAIN_MIX * g, 0, 1)[:, None]
            out[m] = rgb01(NEEDLE_DARK_RGB) * (1 - t) + rgb01(NEEDLE_RGB) * t
        # 장식 공: 색 + 하이라이트
        m = which == BALLS
        if m.any():
            k = np.argmin(np.linalg.norm(p[m][:, None, :] - s["orn_pos"], axis=-1), axis=-1)
            view = T.normalize(cam - p[m])
            half_v = T.normalize(view + light)
            spec = np.clip((n[m] * half_v).sum(-1), 0, 1) ** ORNAMENT_SHININESS
            out[m] = orn_rgb[k] + ORNAMENT_SHINE * spec[:, None]
        # 선물: 상자 색 + 리본 (십자 띠와 위 매듭)
        m = which == GIFT
        if m.any():
            pm = p[m]
            best = np.full(len(pm), np.inf)
            col = np.zeros((len(pm), len(out[0])))
            for g in GIFTS:
                q = gift_local(pm, g)
                half = gift_half(g)
                d = T.round_box(q, half, GIFT_ROUND)
                ribbon = (np.abs(q[:, 0]) < RIBBON_W) | (np.abs(q[:, 2]) < RIBBON_W) | (q[:, 1] > half[1])
                c = np.where(ribbon[:, None], rgb01(g[len(g) - 1]), rgb01(g[len(g) - 2])) * GIFT_GAIN
                d = np.minimum(d, np.where(q[:, 1] > half[1], np.abs(q[:, 1] - half[1]), np.inf))
                near = d < best
                col[near], best[near] = c[near], d[near]
            out[m] = col
        return out

    return color


def ornament_positions(rng, tiers):
    """장식 공: 층 아래쪽 가지 끝에 걸리게, 앞쪽(카메라 쪽)에 모아서."""
    pos = []
    for _ in range(int(ORNAMENTS)):
        y0, h, r1, r2 = tiers[rng.integers(len(tiers))]
        v = rng.uniform(ORNAMENT_LOW, ORNAMENT_HIGH)
        a = -math.pi / 2 + rng.uniform(-ORNAMENT_FRONT, ORNAMENT_FRONT)    # −z 쪽이 카메라
        r = r1 + (r2 - r1) * (1 - v)
        y = y0 + h * (1 - v)
        pos.append((r * math.cos(a), y, r * math.sin(a)))
    return np.array(pos, np.float64).reshape(-1, len(LIGHT_DIR))     # (N, 3)


def bulb_positions(tiers):
    """전구 줄: 트리 바깥을 아래에서 위로 LIGHT_TURNS 바퀴 감고, 줄 길이를 따라 고르게."""
    u = np.linspace(0, 1, int(ARC_SAMPLES))
    y = TREE_BASE + TREE_H * BULB_TOP * u
    r = envelope(y, tiers) + BULB_LIFT
    a = -math.pi / 2 + 2 * math.pi * LIGHT_TURNS * u
    pts = np.stack([r * np.cos(a), y, r * np.sin(a)], -1)
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=-1))])
    pick = np.searchsorted(arc, np.linspace(0, arc[len(arc) - 1], int(BULBS)))
    return pts[np.clip(pick, 0, len(pts) - 1)]


# ---------- 2D: 하늘 · 달 · 언덕 ----------
def horizon_y(cam):
    """눈 바닥이 MAX_DIST 에서 끝나는 화면 높이 (지평선)."""
    far = np.array([[CAMERA_POS[0], 0, CAMERA_POS[2] + MAX_DIST]])
    _, row, _, _ = cam.project(far, COLS, ROWS, CELL_ASPECT)
    return 1 - row[0] / ROWS * 2


def hill_top(X, yh):
    return yh + HILL_H * noise2(X / half_width(COLS, ROWS, CELL_ASPECT) * HILL_WAVES, 0, seed=SEED)


def backdrop(s):
    """하늘 그라데이션 + 달(무늬·가장자리 어둡게) + 달무리 + 먼 언덕과 작은 소나무. (rows, cols, 3)"""
    yh = s["horizon"]

    def fn(X, Y):
        t = np.clip((Y - yh) / (1 - yh), 0, 1)[..., None]
        rgb = rgb01(SKY_LOW_RGB) * (1 - t) + rgb01(SKY_TOP_RGB) * t
        r = np.hypot(X - MOON_X, Y - MOON_Y)
        glow = MOON_HALO * np.exp(-np.maximum(r - MOON_R, 0) / MOON_HALO_R)
        rgb = rgb + rgb01(MOON_RGB) * np.where(r < MOON_R, moon_face(X, Y), glow)[..., None]
        top = hill_top(X, yh)
        hill = Y < top
        shade_h = np.clip(1 - (top - Y) * (1 - AMBIENT) / HILL_H, AMBIENT, 1) if HILL_H > 0 else np.ones(X.shape)
        rgb = np.where(hill[..., None], rgb01(HILL_RGB) * shade_h[..., None], rgb)
        pines = np.full(X.shape, np.inf)
        hw = half_width(COLS, ROWS, CELL_ASPECT)
        ks = np.arange(int(HILL_PINES))
        jitter, size = cell_hash(ks, ks * 0, SEED), cell_hash(ks, ks * 0 + 1, SEED)
        for k in ks:
            px = -hw + (k + jitter[k]) / max(1, HILL_PINES) * hw * 2
            base = float(hill_top(np.array([px]), yh)[0])
            ph = HILL_PINE_H * (1 - size[k] / 2)
            tri = [(px - HILL_PINE_W, base - ph / 2), (px + HILL_PINE_W, base - ph / 2), (px, base + ph)]
            pines = np.minimum(pines, S.polygon2(X, Y, tri))
        return np.where((pines < 0)[..., None], rgb01(HILL_PINE_RGB), rgb)

    return shade(fn, COLS, ROWS, CELL_ASPECT, int(SUPERSAMPLE))


def moon_face(X, Y):
    """달 원판의 밝기 (무늬 · 가장자리 어둡게), 원판 밖은 0."""
    r = np.hypot(X - MOON_X, Y - MOON_Y)
    spots = fbm((X - MOON_X) / MOON_R * MOON_SPOT_SCALE, (Y - MOON_Y) / MOON_R * MOON_SPOT_SCALE, seed=SEED)
    return np.where(r < MOON_R, (1 - MOON_SPOTS * spots) * (1 - MOON_LIMB * (r / MOON_R) ** 2), 0)


def halo(cx, cy, strength, radius):
    """(cx, cy) 둘레 빛 (rows, cols) — 칸 하나에 한 점."""
    X, Y = coords(COLS, ROWS, CELL_ASPECT, 1)
    return strength * np.exp(-(np.hypot(X - cx, Y - cy) / radius) ** 2)


# ---------- 2D 그림 조립: 썰매 · 산타 · 순록 ----------
class Frame:
    """부위 좌표계: 원점 (ox, oy), 1 단위 = scale (화면), tilt 만큼 돌림 (라디안, 반시계)."""

    def __init__(self, ox, oy, scale, tilt):
        self.ox, self.oy, self.scale = ox, oy, scale
        self.c, self.s = math.cos(tilt), math.sin(tilt)

    def screen(self, x, y):
        return (self.ox + self.scale * (x * self.c - y * self.s), self.oy + self.scale * (x * self.s + y * self.c))

    def local(self, X, Y):
        dx, dy = X - self.ox, Y - self.oy
        return (dx * self.c + dy * self.s) / self.scale, (-dx * self.s + dy * self.c) / self.scale

    def child(self, x, y, scale):
        ox, oy = self.screen(x, y)
        return Frame(ox, oy, self.scale * scale, math.atan2(self.s, self.c))

    def pts(self, pts):
        return [self.screen(x, y) for x, y in pts]


def ell(x, y, e):
    return S.ellipse2(x, y, *e)


def leg(base, a1, a2):
    """다리 꺾은선 (순록 단위): 시작 → 무릎 → 발굽. 각도는 도, 아래 0 → 앞(−x) +."""
    a1, a2 = math.radians(a1), math.radians(a2)
    knee = (base[0] - LEG_UPPER * math.sin(a1), base[1] - LEG_UPPER * math.cos(a1))
    hoof = (knee[0] - LEG_LOWER * math.sin(a2), knee[1] - LEG_LOWER * math.cos(a2))
    return [base, knee, hoof]


def strokes(frame, pts, r, r_end=None):
    """꺾은선을 두께 있는 막대들로 (부호 거리 함수). r_end 를 주면 끝으로 갈수록 가늘어짐.
    fn.screen_pts 에 화면 좌표 점을 남겨 계산 범위를 잡을 때 쓴다."""
    segs = list(zip(pts[:-1], pts[1:]))
    n = len(segs)

    def fn(X, Y):
        x, y = frame.local(X, Y)
        out = np.full(np.shape(X), np.inf)
        for k, (a, b) in enumerate(segs):
            ra = r if r_end is None else r + (r_end - r) * k / n
            rb = r if r_end is None else r + (r_end - r) * (k + 1) / n
            out = np.minimum(out, S.capsule2(x, y, a, b, ra, rb))
        return out
    fn.screen_pts = frame.pts(pts)
    return fn


def sag_curve(a, b, sag):
    """a → b 사이를 아래로 처진 곡선 (2차 베지어)으로."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - sag * math.hypot(b[0] - a[0], b[1] - a[1])
    u = np.linspace(0, 1, int(REIN_SEGMENTS) + 1)
    x = (1 - u) ** 2 * a[0] + 2 * (1 - u) * u * mx + u ** 2 * b[0]
    y = (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * my + u ** 2 * b[1]
    return list(zip(x, y))


def team_layout(pose, dx=0.0, dy=0.0):
    """썰매·산타·순록을 부위 목록으로. fills: [(부호거리 함수(X, Y), 색)] 아래→위,
    lines: [(화면 점 목록, 색, 뒤에 그릴지)]. pose: 다리 각도 목록 (순록마다). dx, dy: 제자리에서 옮긴 거리."""
    sl = Frame(TEAM_X + dx, TEAM_Y + dy, TEAM_SCALE, -TEAM_TILT)
    fills, lines = [], []
    deer_frames = [sl.child(-(DEER_FIRST + i * DEER_GAP), DEER_Y, DEER_SIZE) for i in range(int(REINDEER))]

    # 끈: 썰매 앞 → 순록 가슴을 차례로 잇는 한 줄
    trace = [sl.screen(*SLEIGH_HITCH)] + [f.screen(*TRACE_FRONT) for f in deer_frames]
    lines.append((trace, REIN_RGB, True))

    for i, f in enumerate(deer_frames):
        near_front, far_front, near_hind, far_hind = pose[i]
        loc = f.local
        fills.append((strokes(f, leg(SHOULDER, *far_front), LEG_R, LEG_R_END), DEER_DARK_RGB))   # 먼 앞다리
        fills.append((strokes(f, leg(HIP, *far_hind), LEG_R, LEG_R_END), DEER_DARK_RGB))        # 먼 뒷다리
        for a in ANTLER:                                                                         # 먼 쪽 뿔
            fills.append((strokes(f, [(x + ANTLER_FAR[0], y + ANTLER_FAR[1]) for x, y in a], ANTLER_R), DEER_DARK_RGB))
        fills += [
            (lambda X, Y, loc=loc: ell(*loc(X, Y), DEER_RUMP), DEER_RGB),
            (lambda X, Y, loc=loc: ell(*loc(X, Y), DEER_BODY), DEER_RGB),
            (lambda X, Y, loc=loc: ell(*loc(X, Y), DEER_CHEST), DEER_RGB),
            (lambda X, Y, loc=loc: S.capsule2(*loc(X, Y), *DEER_NECK), DEER_RGB),
            (lambda X, Y, loc=loc: S.capsule2(*loc(X, Y), *DEER_HEAD), DEER_RGB),
            (lambda X, Y, loc=loc: ell(*loc(X, Y), DEER_RUFF), DEER_PALE_RGB),
            (lambda X, Y, loc=loc: ell(*loc(X, Y), DEER_TAIL), DEER_PALE_RGB),
        ]
        fills.append((strokes(f, leg(SHOULDER, *near_front), LEG_R, LEG_R_END), DEER_RGB))        # 가까운 앞다리
        fills.append((strokes(f, leg(HIP, *near_hind), LEG_R, LEG_R_END), DEER_RGB))             # 가까운 뒷다리
        for a in ANTLER:
            fills.append((strokes(f, a, ANTLER_R), ANTLER_RGB))

    # 썰매와 산타
    loc = sl.local
    fills += [
        (lambda X, Y: ell(*loc(X, Y), SACK), SACK_RGB),
        (lambda X, Y: ell(*loc(X, Y), SANTA_BODY), SANTA_COAT_RGB),
        (lambda X, Y: S.circle2(*loc(X, Y), *SANTA_HEAD), SANTA_SKIN_RGB),
        (lambda X, Y: ell(*loc(X, Y), SANTA_BEARD), SANTA_FUR_RGB),
        (lambda X, Y: S.polygon2(*loc(X, Y), SANTA_HAT), SANTA_COAT_RGB),
        (lambda X, Y: S.capsule2(*loc(X, Y), *SANTA_HAT_TRIM), SANTA_FUR_RGB),
        (lambda X, Y: S.circle2(*loc(X, Y), *SANTA_POMPOM), SANTA_FUR_RGB),
        (lambda X, Y: S.polygon2(*loc(X, Y), SLEIGH_BODY), SLEIGH_RGB),
        (lambda X, Y: S.capsule2(*loc(X, Y), *SANTA_ARM), SANTA_COAT_RGB),
        (lambda X, Y: S.circle2(*loc(X, Y), SANTA_ARM[1][0], SANTA_ARM[1][1], SANTA_MITT_R), SANTA_MITT_RGB),
    ]
    lines.append((sl.pts(SLEIGH_RIM), SLEIGH_TRIM_RGB, False))
    lines.append((sl.pts(SLEIGH_SCROLL), SLEIGH_TRIM_RGB, False))
    lines.append((sl.pts(RUNNER), SLEIGH_TRIM_RGB, False))
    for a, b in STRUTS:
        lines.append((sl.pts([a, b]), SLEIGH_TRIM_RGB, False))
    # 고삐: 산타 손 → 가장 가까운 순록 목줄
    hand = sl.screen(*SANTA_ARM[1])
    lines.append((sag_curve(hand, deer_frames[0].screen(*COLLAR[0]), REIN_SAG), REIN_RGB, False))
    nose = deer_frames[len(deer_frames) - 1].screen(NOSE[0], NOSE[1])
    return fills, lines, sl, nose


def team_bounds(sl, lines, fills):
    """썰매 무리가 차지하는 화면 세로 범위: 선·다리·뿔의 모든 점 + 모자 끝, 여유 FIG_PAD."""
    ys = [y for pts, _, _ in lines for _, y in pts]
    ys += [y for fn, _ in fills for _, y in getattr(fn, "screen_pts", [])]
    ys += [y for _, y in sl.pts(SANTA_HAT + [SANTA_POMPOM[:len(SANTA_POMPOM) - 1]])]
    pad = FIG_PAD * TEAM_SCALE
    return max(ys) + pad, min(ys) - pad


def window(y_top, y_bot):
    """슈퍼샘플 좌표 중 화면 높이 y_bot..y_top 줄만 → (X, Y, 첫 줄, 끝 줄)."""
    ss = int(SUPERSAMPLE)
    X, Y = coords(COLS, ROWS, CELL_ASPECT, ss)
    _, rt = S.to_cell(0, y_top, COLS, ROWS, CELL_ASPECT)
    _, rb = S.to_cell(0, y_bot, COLS, ROWS, CELL_ASPECT)
    r0, r1 = int(np.clip(np.floor(rt), 0, ROWS)), int(np.clip(np.ceil(rb), 0, ROWS))
    return X[r0 * ss:r1 * ss], Y[r0 * ss:r1 * ss], r0, r1


def grow(mask, n):
    """마스크를 n 칸 넓힌다 (상하좌우·대각)."""
    m = mask.copy()
    for _ in range(int(n)):
        p = np.pad(m, 1)
        m = (p[:-2, :-2] | p[:-2, 1:-1] | p[:-2, 2:] | p[1:-1, :-2] | p[1:-1, 1:-1] | p[1:-1, 2:]
             | p[2:, :-2] | p[2:, 1:-1] | p[2:, 2:])
    return m


def paint_shapes(grid, fills, lines, y_top, y_bot, moon_disk, moon_cells):
    """채움 부위 → 밝기 글자 (+ 테두리 방향 글자), 선 → 방향 글자. 손댄 칸 마스크를 돌려준다.

    SILHOUETTE 이면 달(moon_disk)과 겹친 칸은 빈칸 = 검은 실루엣. 아니면 달·달무리(moon_cells) 위에서 둘레를 비운다.
    """
    ss = int(SUPERSAMPLE)
    X, Y, r0, r1 = window(y_top, y_bot)
    owner = np.full((r1 - r0, COLS), -1)
    union = np.full(X.shape, np.inf)
    for k, (fn, _) in enumerate(fills):
        d = fn(X, Y)
        owner[S.coverage(d, ss) >= FIG_COVER] = k
        union = np.minimum(union, d)
    inside = np.zeros((ROWS, COLS), bool)
    inside[r0:r1] = owner >= 0
    # 선 (임시 grid 에 그려 마스크를 얻는다)
    tmp_back, tmp_front = Grid(COLS, ROWS), Grid(COLS, ROWS)
    back = np.zeros((ROWS, COLS), bool)
    front = np.zeros((ROWS, COLS), bool)
    for pts, rgb, behind in lines:
        if behind:
            back |= S.draw_polyline2(tmp_back, pts, CELL_ASPECT, None, rgb)
        else:
            front |= S.draw_polyline2(tmp_front, pts, CELL_ASPECT, None, rgb)
    back &= ~inside
    figure = inside | back | front
    touched = figure.copy()
    if not SILHOUETTE:                       # 색 글자가 달 위에 겹치면 둘레 FIG_GAP 칸을 비워 떨어져 보이게
        ring = grow(figure, FIG_GAP) & ~figure & moon_cells
        grid.ch[ring] = 0
        touched |= ring
    # 채움 글자
    rgb = np.array([rgb01(c) for _, c in fills])[np.maximum(owner, 0)]
    lum = FIG_LIFT + (1 - FIG_LIFT) * luminance(rgb)
    yy, xx = np.mgrid[r0:r1, 0:COLS]
    codes = ramp_chars(lum, FIG_RAMP, dither=DITHER, xx=xx, yy=yy, seed=SEED)
    if FIG_OUTLINE:
        _, gx, gy = edges(S.coverage(union, ss), CELL_ASPECT)
        p = np.pad(owner >= 0, 1)
        edge = (owner >= 0) & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        codes = np.where(edge, edge_chars(gx, gy), codes)
    peak = rgb.max(axis=-1, keepdims=True)
    color = np.clip(rgb * np.maximum(peak, MIN_COLOR) / np.where(peak > 0, peak, 1), 0, 1) * np.iinfo(np.uint8).max
    sel = owner >= 0
    sub = grid.ch[r0:r1], grid.rgb[r0:r1]
    sub[0][sel], sub[1][sel] = codes[sel], color[sel].astype(np.uint8)
    for m, src in ((back, tmp_back), (front, tmp_front)):
        grid.ch[m], grid.rgb[m] = src.ch[m], src.rgb[m]
    if SILHOUETTE:
        grid.ch[figure & moon_disk] = 0
        if SIL_EDGE:                         # 실루엣에 맞닿은 달 칸 = 윤곽 방향 글자 (모양이 또렷해짐)
            cover = figure.astype(np.float64)
            cover[r0:r1] = np.maximum(cover[r0:r1], S.coverage(union, ss))
            _, gx, gy = edges(cover, CELL_ASPECT)
            rim = moon_disk & ~figure & grow(figure, 1)
            grid.ch[rim] = edge_chars(gx, gy)[rim]
            touched |= rim
    return touched


def paint_topper(grid, cx, cy, scale=1.0, ray_scale=1.0):
    """꼭대기 별: 별 모양 채움 + 테두리 방향 글자 + 둘레 빛줄기. scale: 별 크기 배수, ray_scale: 빛줄기 길이 배수.
    그린 칸 마스크를 돌려준다."""
    if scale <= 0:
        return np.zeros((ROWS, COLS), bool)
    ss = int(SUPERSAMPLE)
    radius = TOPPER_R * scale
    X, Y, r0, r1 = window(cy + radius * 2, cy - radius * 2)
    d = S.star2(X, Y, cx, cy, radius, TOPPER_INNER)
    cov = S.coverage(d, ss)
    inside = cov >= FIG_COVER
    yy, xx = np.mgrid[r0:r1, 0:COLS]
    codes = ramp_chars(np.ones(cov.shape), RAMP, xx=xx, yy=yy, seed=SEED)
    _, gx, gy = edges(cov, CELL_ASPECT)
    p = np.pad(inside, 1)
    edge = inside & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    codes = np.where(edge, edge_chars(gx, gy), codes)
    sub_ch, sub_rgb = grid.ch[r0:r1], grid.rgb[r0:r1]
    sub_ch[inside], sub_rgb[inside] = codes[inside], TOPPER_RGB
    star = np.zeros((ROWS, COLS), bool)
    star[r0:r1] = inside
    tmp = Grid(COLS, ROWS)
    rays = np.zeros((ROWS, COLS), bool)
    for k in range(int(TOPPER_RAYS)):
        a = math.pi / 2 + k * 2 * math.pi / max(1, TOPPER_RAYS) + math.pi / max(1, TOPPER_RAYS)
        r_in = radius * (TOPPER_INNER + 1) / 2 + TOPPER_RAY / 2
        r_out = r_in + TOPPER_RAY * ray_scale
        S.draw_line2(tmp, (cx + r_in * math.cos(a), cy + r_in * math.sin(a)),
                     (cx + r_out * math.cos(a), cy + r_out * math.sin(a)), CELL_ASPECT, None, TOPPER_RAY_RGB, mask=rays)
    rays &= ~star
    grid.ch[rays], grid.rgb[rays] = tmp.ch[rays], tmp.rgb[rays]
    return star | rays


# ---------- 준비 · 그리기 ----------
def pick_chars(chars, u):
    """u (0..1) → chars 중 하나의 글자 코드 (작은 u → 앞 글자)."""
    return codes_of(chars)[np.clip((np.asarray(u) * len(chars)).astype(int), 0, len(chars) - 1)]


def setup():
    """한 번만 계산: 3D 트리 렌더, 배경, 전구·별·눈송이 위치. 난수는 SEED 로만."""
    rng = np.random.default_rng(SEED)
    cam = T.Camera(CAMERA_POS, CAMERA_TARGET, fov=FOV)
    s = {"cam": cam, "tiers": tier_table()}
    s["orn_pos"] = ornament_positions(rng, s["tiers"])
    s["horizon"] = horizon_y(cam)
    r = T.render_sdf(make_sdf(s), cam, COLS, ROWS, CELL_ASPECT, int(SUPERSAMPLE), color=make_color(s),
                     light_dir=LIGHT_DIR, light_rgb=(LIGHT_GAIN,) * len(LIGHT_DIR), ambient=AMBIENT, rim=RIM, shadows=True, fog=FOG, fog_start=FOG_START,
                     fog_rgb=rgb01(FOG_RGB), max_steps=int(MAX_STEPS), max_dist=MAX_DIST)
    hit = r.mask >= 0.5
    X, Y = coords(COLS, ROWS, CELL_ASPECT, 1)
    far_hill = (Y < hill_top(X, s["horizon"])) & ~(hit & (r.depth < HILL_DIST))
    hit &= ~far_hill
    ro, rd = cam.rays(X, Y)
    down = rd[..., 1] < 0
    to_floor = np.where(down, -ro[..., 1] / np.where(down, rd[..., 1], -1), np.inf)   # 칸 가운데 광선이 바닥에 닿는 거리
    base = backdrop(s)
    # 전구: 줄 위치, 보이는 전구의 빛을 잎과 눈에 번지게
    bulbs = bulb_positions(s["tiers"])
    col, row, z, vis = cam.project(bulbs, COLS, ROWS, CELL_ASPECT)
    bx, by = np.floor(col).astype(int), np.floor(row).astype(int)
    ok = vis & (bx >= 0) & (by >= 0) & (bx < COLS) & (by < ROWS)
    ok[ok] &= z[ok] < r.depth[by[ok], bx[ok]]
    spill = np.zeros((ROWS, COLS))
    np.add.at(spill, (by[ok], bx[ok]), 1.0)
    spill = blur(spill, BULB_SPILL_R, CELL_ASPECT)
    spill = spill / spill.max() if spill.max() > 0 else spill
    lit = r.rgb + BULB_SPILL * spill[..., None] * rgb01(BULB_RGB)
    base[hit] = lit[hit]
    # 꼭대기 별 위치와 둘레 빛
    tip = np.array([[0, TREE_BASE + TREE_H + TOPPER_LIFT, 0]])
    tc, tr, _, _ = cam.project(tip, COLS, ROWS, CELL_ASPECT)
    tx, ty = S.to_screen(tc[0], tr[0], COLS, ROWS, CELL_ASPECT)
    base = base + halo(tx, ty, TOPPER_GLOW, TOPPER_GLOW_R)[..., None] * rgb01(TOPPER_RGB)
    s.update(base=base, hit=hit, depth=np.where(hit, r.depth, np.inf), bulbs=bulbs, topper=(float(tx), float(ty)))
    # 별: 하늘(언덕 위, 3D 없음, 달무리 밖)에서 SEED 로 고른 칸
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    sky = (Y > hill_top(X, s["horizon"])) & ~hit & (np.hypot(X - MOON_X, Y - MOON_Y) > MOON_R + MOON_HALO_R)
    h = cell_hash(xx, yy, SEED)
    s["stars"] = sky & (h < STARS)
    s["star_codes"] = pick_chars(STAR_CHARS, h / STARS if STARS > 0 else h)
    # 눈 반짝임: 눈 바닥 칸 (3D 바닥) 중 일부
    hs = cell_hash(xx, yy, SEED + 1)
    s["floor"] = hit & down & (r.depth > to_floor * (1 - SNOW_TOL))
    s["sparkle"] = s["floor"] & (hs < SNOW_SPARKLE)
    s["sparkle_codes"] = pick_chars(SNOW_SPARKLE_CHARS, hs / SNOW_SPARKLE if SNOW_SPARKLE > 0 else hs)
    # 썰매 무리가 겹칠 때 둘레를 비울 곳 = 달과 달무리
    s["moon_cells"] = np.hypot(X - MOON_X, Y - MOON_Y) < MOON_R + MOON_HALO_R
    ss = int(SUPERSAMPLE)
    cov = shade(lambda X, Y: (np.hypot(X - MOON_X, Y - MOON_Y) < MOON_R).astype(np.float64), COLS, ROWS, CELL_ASPECT, ss)
    s["moon_disk"] = cov >= 0.5
    face = shade(moon_face, COLS, ROWS, CELL_ASPECT, ss) / np.maximum(cov, 0.5)
    face = face / face.max()
    s["moon_codes"] = ramp_chars(face, MOON_RAMP, gamma=MOON_GAMMA, dither=MOON_DITHER, xx=xx, yy=yy, seed=SEED)
    s["moon_rgb"] = (np.clip(face, MIN_COLOR, 1)[..., None] * MOON_RGB).astype(np.uint8)
    # 트리 테두리: 칸마다 맞은 물체를 찾아 잎·장식 공 칸의 바깥 둘레
    pts = (ro + rd * np.where(hit, r.depth, 0)[..., None])[hit]
    which = np.full((ROWS, COLS), -1)
    which[hit] = np.argmin(np.stack(parts(pts, s), -1), axis=-1)
    tree = (which == FOLIAGE) | (which == BALLS)
    p = np.pad(tree, 1)
    s["tree_edge"] = tree & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]) & bool(TREE_OUTLINE)
    _, gx, gy = edges(tree.astype(np.float64), CELL_ASPECT)
    s["tree_edge_codes"] = edge_chars(gx, gy)
    # 눈송이
    hw = half_width(COLS, ROWS, CELL_ASPECT)
    s["flakes"] = np.stack([rng.uniform(-hw, hw, int(FLAKES)), rng.uniform(-1, 1, int(FLAKES)),
                            rng.uniform(0, 1, int(FLAKES))], -1)
    # ② 등장용 ─ 필드 글자가 어느 층(layer)에 속하는지: 하늘 / 땅 / 달 / 꼭대기 별 빛 / 트리 / 장식 공 / 선물
    layer = np.full((ROWS, COLS), SKY_L)
    layer[(Y < hill_top(X, s["horizon"])) & ~hit] = GROUND_L
    layer[(np.hypot(X - MOON_X, Y - MOON_Y) < MOON_R + MOON_HALO_R * LAYER_REACH) & ~hit] = MOON_L
    layer[(np.hypot(X - tx, Y - ty) < TOPPER_GLOW_R * LAYER_REACH) & ~hit] = TOPPER_L
    for part, lay in ((SNOW, GROUND_L), (TRUNK, TREE_L), (FOLIAGE, TREE_L), (BALLS, ORN_L), (GIFT, GIFT_L)):
        layer[hit & (which == part)] = lay
    s["field_layer"] = layer
    # 전구 칸과 줄을 따라간 순서 (0 = 맨 아래 전구)
    bulb_order = np.full((ROWS, COLS), np.inf)
    idx = np.nonzero(ok)[0]
    np.minimum.at(bulb_order, (by[idx], bx[idx]), idx / max(1, len(bulbs)))
    s["bulb_cells"], s["bulb_order"] = np.isfinite(bulb_order), bulb_order
    s["moon_rel"] = ((X - MOON_X) / MOON_R, (Y - MOON_Y) / MOON_R)
    s["order"] = cell_hash(xx, yy, SEED + 1 + 1)                  # 흩어져 나타날 때 칸마다 순서 0..1
    return s


LAYERS = ["sky", "star", "flake", "ground", "tree", "ornament", "gift", "bulb", "moon", "topper", "team"]
SKY_L, STAR_L, FLAKE_L, GROUND_L, TREE_L, ORN_L, GIFT_L, BULB_L, MOON_L, TOPPER_L, TEAM_L = range(len(LAYERS))


def draw(s, phase, grid, owner=None, team=True, topper=True):
    """완성 화면을 phase(0..1) 로 그린다. ① 에서는 움직임이 없다 (③ 에서 phase 로 움직임을 넣음).

    owner: (rows, cols) 배열을 주면 칸마다 마지막에 그린 층(LAYERS 번호)을 적는다 (② 등장에서 씀).
    team, topper: False 면 썰매 무리·꼭대기 별을 그리지 않는다 (② 에서 따로 움직여 그림).
    """
    own = owner if owner is not None else np.zeros((ROWS, COLS), int)
    pose = [LEG_POSE] * int(REINDEER)
    fills, lines, sl, nose = team_layout(pose)
    field = s["base"]
    if team:
        field = field + halo(nose[0], nose[1], NOSE_GLOW, NOSE_GLOW_R)[..., None] * rgb01(NOSE_RGB)
    field_to_grid(field, grid, RAMP, cut=CUT, gamma=GAMMA, dither=DITHER, seed=SEED, min_color=MIN_COLOR)
    own[...] = s["field_layer"]
    grid.z[...] = s["depth"]
    grid.fill(s["tree_edge"], s["tree_edge_codes"], TREE_OUTLINE_RGB)
    own[s["tree_edge"]] = TREE_L
    grid.fill(s["moon_disk"], s["moon_codes"], s["moon_rgb"])
    own[s["moon_disk"]] = MOON_L
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    snow = ramp_chars(luminance(np.clip(field, 0, 1)), SNOW_RAMP, cut=CUT, gamma=GAMMA, dither=DITHER, xx=xx, yy=yy, seed=SEED)
    grid.ch[s["floor"]] = snow[s["floor"]]
    # 별 · 눈 반짝임
    star_cells = s["stars"] & (grid.ch == 0)
    grid.fill(star_cells, s["star_codes"], STAR_RGB)
    own[star_cells] = STAR_L
    grid.fill(s["sparkle"], s["sparkle_codes"], SNOW_SPARKLE_RGB)
    # 전구 (트리 뒤로 돌아가면 가려짐)
    T.draw_points(grid, s["bulbs"], s["cam"], CELL_ASPECT, BULB_CHAR, BULB_RGB)
    own[s["bulb_cells"]] = BULB_L
    if topper:
        own[paint_topper(grid, *s["topper"])] = TOPPER_L
    figure = np.zeros((ROWS, COLS), bool)
    if team:
        figure = paint_team(s, grid, fills, lines, sl, nose)
        own[figure] = TEAM_L
    # 내리는 눈 (빈 칸에만)
    fx, fy, size = s["flakes"].T
    c, r = S.to_cell(fx, fy, COLS, ROWS, CELL_ASPECT)
    c, r = np.floor(c).astype(int), np.floor(r).astype(int)
    ok = (c >= 0) & (r >= 0) & (c < COLS) & (r < ROWS)
    c, r, size = c[ok], r[ok], size[ok]
    free = (grid.ch[r, c] == 0) & ~figure[r, c]
    codes = pick_chars(FLAKE_CHARS, size)
    grid.ch[r[free], c[free]] = codes[free]
    grid.rgb[r[free], c[free]] = FLAKE_RGB
    own[r[free], c[free]] = FLAKE_L


def paint_team(s, grid, fills, lines, sl, nose):
    """썰매 무리 + 루돌프 코. 손댄 칸 마스크를 돌려준다."""
    y_top, y_bot = team_bounds(sl, lines, fills)
    touched = paint_shapes(grid, fills, lines, y_top, y_bot, s["moon_disk"], s["moon_cells"])
    nc, nr = S.to_cell(nose[0], nose[1], COLS, ROWS, CELL_ASPECT)
    if 0 <= nc < COLS and 0 <= nr < ROWS:
        grid.put(nc, nr, NOSE_CHAR, NOSE_RGB)                                 # 루돌프 코
        touched[int(nr), int(nc)] = True
    return touched


def scene(s, grid):
    """① 완성 화면 = 모션의 처음."""
    draw(s, 0.0, grid)


def intro_layers(s):
    """② 에 쓸 층 그림 (한 번만 계산해 s 에 둔다).

    final: 썰매·꼭대기 별을 뺀 완성 화면과 칸마다 층.
    base : final 에서 장식 공·전구 칸은 같은 줄 옆 잎 글자로, 선물 칸은 옆 눈 글자로 메운 것 → 트리 층이 떨어질 때 구멍이 없음.
    """
    if "intro" in s:
        return s["intro"]
    final, own = Grid(COLS, ROWS), np.zeros((ROWS, COLS), int)
    draw(s, 0.0, final, own, team=False, topper=False)
    ch, rgb, base_own = final.ch.copy(), final.rgb.copy(), own.copy()
    late = np.isin(own, [ORN_L, BULB_L, GIFT_L])
    base_own[late] = SKY_L
    ch[late] = 0
    cc = np.arange(COLS)[None, :]
    # 장식 공·전구 자리는 옆 잎 글자로, 선물 자리는 옆 눈 글자로 (테두리 글자 / \ | 는 늘이면 줄무늬가 되어 뺌)
    for todo, source in ((np.isin(own, [ORN_L, BULB_L]), (own == TREE_L) & ~s["tree_edge"]),
                         (own == GIFT_L, own == GROUND_L)):
        for d in range(1, int(INPAINT_REACH) + 1):
            for k in (-d, d):
                take = todo & np.roll(source, -k, axis=1) & (cc + k >= 0) & (cc + k < COLS)
                for dst, src in ((ch, final.ch), (rgb, final.rgb), (base_own, own)):
                    dst[take] = np.roll(src, -k, axis=1)[take]
                todo &= ~take
    # 채움 순서 (0 → 1): 트리는 아래부터, 달은 오른쪽부터 (차오르는 달 모양 경계), 칸마다 조금씩 들쭉날쭉
    yy, xx = np.mgrid[0:ROWS, 0:COLS]
    names = ["jitter", "fly", "fly_x", "fly_y"]                          # 칸마다 고정 난수 (SEED 로 정해짐)
    jitter, fly, fly_x, fly_y = (cell_hash(xx, yy, SEED + len(LAYERS) + k) for k in range(len(names)))
    tree = base_own == TREE_L
    r_top, r_bot = yy[tree].min(), yy[tree].max()
    tree_order = np.clip((r_bot - yy) / max(1, r_bot - r_top), 0, 1) * (1 - FILL_JITTER) + jitter * FILL_JITTER
    u, v = s["moon_rel"]
    w = np.sqrt(np.clip(1 - v ** 2, 0, 1))
    wax = np.clip((1 - np.where(w > 0, u / np.where(w > 0, w, 1), 0)) / 2, 0, 1)   # 0 = 오른쪽 끝, 1 = 왼쪽 끝
    s["intro"] = {"final": final, "own": own, "base_ch": ch, "base_rgb": rgb, "base_own": base_own,
                  "tree_order": tree_order, "moon_order": wax * (1 - FILL_JITTER) + jitter * FILL_JITTER,
                  "fly": fly < FLY_SHARE, "fly_dx": (fly_x - 0.5) * 2 * FLY_CELLS, "fly_dy": (fly_y - 0.5) * 2 * FLY_CELLS}
    return s["intro"]


def fill_in(grid, ch, rgb, mask, rv, L=None):
    """채워지는 칸: rv (0..1) 가 0 을 넘으면 나타나 FRONT_RGB 로 빛나다가 1 이면 제 색. 
    L 을 주면 날아오는 칸(L["fly"])은 떨어진 곳에서 출발해 rv 가 1 이 될 때 제자리에 닿는다."""
    e = smoothstep(0, 1, rv)
    color = (rgb * e[..., None] + np.asarray(FRONT_RGB) * (1 - e)[..., None]).astype(np.uint8)
    moving = mask & (rv < 1) & (L["fly"] if L is not None else False)
    home = mask & ~moving
    grid.ch[home], grid.rgb[home] = ch[home], color[home]
    rr, cc = np.nonzero(moving)
    if len(rr):
        r2 = np.round(rr + L["fly_dy"][rr, cc] * (1 - e[rr, cc])).astype(int)
        c2 = np.round(cc + L["fly_dx"][rr, cc] * (1 - e[rr, cc])).astype(int)
        ok = (r2 >= 0) & (r2 < ROWS) & (c2 >= 0) & (c2 < COLS)
        grid.ch[r2[ok], c2[ok]] = ch[rr[ok], cc[ok]]
        grid.rgb[r2[ok], c2[ok]] = color[rr[ok], cc[ok]]


def progress(t, start, length, order):
    """채움 진행: 앞줄(head)이 순서 0→1 을 지나가고, 칸마다 앞줄이 지난 뒤 FRONT_W 동안 0→1."""
    head = float(segment(t, start, start + length)) * (1 + FRONT_W)
    return np.clip((head - order) / FRONT_W, 0, 1)


def copy_cells(grid, ch, rgb, mask):
    grid.ch[mask], grid.rgb[mask] = ch[mask], rgb[mask]


def swing_pose(swing):
    """다리 휘젓기: 앞다리와 뒷다리를 서로 반대로 swing 도 만큼."""
    near_front, far_front, near_hind, far_hind = LEG_POSE

    def add(leg_angles, d):
        return (leg_angles[0] + d, leg_angles[1] + d)
    return [add(near_front, swing), add(far_front, -swing), add(near_hind, -swing), add(far_hind, swing)]


def intro(s, p, grid):
    """② 트리가 아래부터 글자로 차오름 → 장식이 하나씩 켜지고 달이 차오름 → 꼭대기 별 반짝 → 썰매가 날아 들어옴.
    p=1 이면 scene 그대로."""
    if p >= 1:
        scene(s, grid)
        return
    L = intro_layers(s)
    t = p * INTRO_SECONDS
    order = s["order"]
    # 1. 무대: 하늘 점·별·눈송이·눈 바닥이 흩어져 스며 나옴
    q = segment(t, T_GROUND, T_GROUND + T_GROUND_D)
    copy_cells(grid, L["base_ch"], L["base_rgb"], np.isin(L["base_own"], [SKY_L, STAR_L, FLAKE_L, GROUND_L]) & (order < q))
    # 2. 트리: 아래(줄기)부터 위로 글자가 차오름. 막 채워진 앞줄이 빛나고, 몇 글자는 멀리서 날아와 자리를 찾음
    rv = progress(t, T_TREE, T_TREE_D, L["tree_order"])
    fill_in(grid, L["base_ch"], L["base_rgb"], (L["base_own"] == TREE_L) & (rv > 0), rv, L)
    # 3. 달: 오른쪽부터 글자로 채워지며 초승달 → 보름달 (장식과 동시에)
    rv = progress(t, T_MOON, T_MOON_D, L["moon_order"])
    fill_in(grid, s["moon_codes"], s["moon_rgb"], s["moon_disk"] & (rv > 0), rv)
    head = float(segment(t, T_MOON, T_MOON + T_MOON_D))
    copy_cells(grid, L["final"].ch, L["final"].rgb, (L["own"] == MOON_L) & ~s["moon_disk"] & (order < head))
    # 4. 장식: 장식 공·선물이 하나씩 반짝 켜지고, 전구는 줄을 따라 아래부터 켜짐
    decor_order = np.where(L["own"] == BULB_L, s["bulb_order"], order)
    rv = progress(t, T_DECOR, T_DECOR_D, decor_order)
    fill_in(grid, L["final"].ch, L["final"].rgb, np.isin(L["own"], [ORN_L, GIFT_L, BULB_L]) & (rv > 0), rv)
    # 5. 꼭대기 별: 커졌다가 제 크기로, 빛줄기가 길게 번쩍였다가 줄어듦
    q = float(segment(t, T_TOP, T_TOP + T_TOP_D))
    if q > 0:
        copy_cells(grid, L["final"].ch, L["final"].rgb, (L["own"] == TOPPER_L) & (order < q))
        paint_topper(grid, *s["topper"], scale=float(overshoot(q, TOP_BOUNCE)), ray_scale=1 + TOP_FLASH * math.sin(math.pi * q))
    # 6. 썰매: 오른쪽 위 하늘 밖에서 날아와 달 앞 제자리에 멈춤 (다리를 휘젓다가 도착하면 완성 자세)
    q = float(segment(t, T_TEAM, T_TEAM + T_TEAM_D))
    if q > 0:
        e = float(ease_out(q))
        swing = FLY_SWING * math.sin(2 * math.pi * FLY_STRIDES * q) * (1 - q)
        fills, lines, sl, nose = team_layout([swing_pose(swing)] * int(REINDEER), FLY_FROM_X * (1 - e), FLY_FROM_Y * (1 - e))
        paint_team(s, grid, fills, lines, sl, nose)


def motion(s, t, phase, grid):
    """③ (아직 없음) 완성 화면 그대로."""
    draw(s, phase, grid)


if __name__ == "__main__":
    run(globals())
