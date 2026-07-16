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

MAX_CAR = 50

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