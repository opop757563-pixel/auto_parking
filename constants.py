# constants.py

TILE_SIZE = 60

MAP = [
    [0,0,0,0,0,0,0,0,0,3],
    [1,1,1,0,1,1,1,1,1,1],
    [0,0,0,0,0,0,0,0,0,0],
    [1,1,1,0,1,1,1,1,1,1],
    [0,0,0,0,0,0,0,0,0,0],
    [1,1,1,0,1,1,1,1,1,1],
    [0,0,0,0,0,0,0,0,0,0],
    [1,1,1,0,1,1,1,1,1,1],
    [0,0,0,0,0,0,0,0,0,0],
    [1,1,1,0,1,1,1,1,1,1],
    [4,0,0,0,0,0,0,0,0,0]
]

ROWS = len(MAP)
COLS = len(MAP[0])

WIDTH = COLS*TILE_SIZE
HEIGHT = ROWS*TILE_SIZE

ENTRY = (0,9)
EXIT = (10,0)

ROAD = 0
PARK = 1
IN = 3
OUT = 4

WHITE = (245,245,245)
GRAY = (70,70,70)

ROAD_COLOR = (240,240,240)
PARK_COLOR = (180,220,255)

ENTRY_COLOR = (40,220,80)
EXIT_COLOR = (240,70,70)

CAR_COLOR = (60,130,255)

FPS = 5

MAX_CAR = 30

SPAWN_INTERVAL = 1000

PARK_TIME = 20000

# --------------------------------------
# 개선 알고리즘 관련 설정
# --------------------------------------

# 자리 배정 방식: "improved" (Hungarian) / "baseline" (Greedy 최근접)
ALLOCATION_MODE = "improved"

# 차량별 예상/실제 주차 시간 범위(ms) - 헝가리안 비용함수에 사용
DWELL_MIN = 10000
DWELL_MAX = 35000

# 출차 재탐색(replan) 쿨다운 (ms) - 매 프레임 재탐색으로 인한 스팸 방지
RETRY_COOLDOWN = 300

# 입차 대기열을 몇 ms 단위로 모아서 한번에(batch) 배정할지
# (동시에 여러 대가 들어오는 상황을 재현 -> Hungarian이 진가를 발휘하는 지점)
BATCH_WINDOW = 400

# 같은 배치(batch)에서 여러 대가 동시에 배정될 때, 입구(ENTRY)에서
# 차량이 실제로 출발하기 시작하는 시점을 서로 몇 tick씩 벌려줄지.
# (0이면 같은 tick에 여러 대가 ENTRY에 동시에 나타나 겹쳐 보이는 문제 발생)
ENTRY_STAGGER_TICKS = 3

# --------------------------------------
# 차종 설정
# --------------------------------------

# 차종 종류 (유니티 쪽 프리팹 이름과 매칭되는 식별 문자열)
VEHICLE_TYPE_SEDAN = "SEDAN"   # 승용차
VEHICLE_TYPE_SUV = "SUV"       # SUV
VEHICLE_TYPE_RV = "RV"         # RV
VEHICLE_TYPE_EV = "EV"         # 전기차

VEHICLE_TYPES = [
    VEHICLE_TYPE_SEDAN,
    VEHICLE_TYPE_SUV,
    VEHICLE_TYPE_RV,
    VEHICLE_TYPE_EV,
]

# 차종별 배정 가중치 (실제 국내 등록 비율에 대략 맞춤 - 숫자만 바꾸면 비율 조정 가능)
# 반드시 VEHICLE_TYPES와 같은 순서/개수여야 한다.
VEHICLE_TYPE_WEIGHTS = [
    45,  # SEDAN
    30,  # SUV
    15,  # RV
    10,  # EV
]