# map.py

from constants import *

class ParkingMap:

    def __init__(self):

        self.grid = MAP

        # 모든 주차칸 저장
        self.parking_slots = []

        # 현재 비어있는 주차칸
        self.free_slots = set()

        for r in range(ROWS):
            for c in range(COLS):

                if self.grid[r][c] == PARK:

                    self.parking_slots.append((r, c))
                    self.free_slots.add((r, c))

    # --------------------------
    # 맵 범위 확인
    # --------------------------

    def in_range(self, pos):

        r, c = pos

        return 0 <= r < ROWS and 0 <= c < COLS

    # --------------------------
    # 이동 가능한 길인지 확인
    # --------------------------

    def is_driveable(self, pos, goal=None):

        r, c = pos

        value = self.grid[r][c]

        # 길
        if value == ROAD:
            return True

        # 입구
        if value == IN:
            return True

        # 출구
        if value == OUT:
            return True

        # 목적지인 주차칸만 진입 허용
        if value == PARK:

            if goal is not None and pos == goal:
                return True

        return False

    # --------------------------
    # 상하좌우 이웃
    # --------------------------

    def neighbors(self, pos, goal=None):

        r, c = pos

        dirs = [
            (-1,0),
            (1,0),
            (0,-1),
            (0,1)
        ]

        result = []

        for dr, dc in dirs:

            nxt = (r+dr, c+dc)

            if not self.in_range(nxt):
                continue

            if self.is_driveable(nxt, goal):
                result.append(nxt)

        return result

    # --------------------------
    # 빈 주차칸 반환
    # --------------------------

    def get_free_slots(self):

        return list(self.free_slots)

    # --------------------------
    # 주차칸 사용
    # --------------------------

    def occupy_slot(self, slot):

        self.free_slots.discard(slot)

    # --------------------------
    # 주차칸 반환
    # --------------------------

    def release_slot(self, slot):

        self.free_slots.add(slot)

    # --------------------------
    # 남은 자리 개수
    # --------------------------

    def free_count(self):

        return len(self.free_slots)

    # --------------------------
    # 가장 가까운 빈 주차칸
    # (맨해튼 거리 기준)
    # --------------------------

    def nearest_slot(self, start):

        if len(self.free_slots) == 0:
            return None

        best = None
        best_dist = 999999

        for slot in self.free_slots:

            d = abs(start[0]-slot[0]) + abs(start[1]-slot[1])

            if d < best_dist:

                best_dist = d
                best = slot

        return best