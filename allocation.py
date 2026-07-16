# allocation.py
#
# 차량 <-> 주차칸 최적 할당 모듈
#
# 기존 방식(그리디):
#   그냥 입구에서 가장 가까운 빈 자리에 순서대로 배정 (map.nearest_slot)
#
# 개선 방식(헝가리안 메소드):
#   여러 대의 차량과 여러 개의 빈 자리를 "동시에" 놓고,
#   전체 비용(Cost)의 합이 최소가 되도록 1:1 최적 매칭을 구한다.
#
#   비용 함수 설계:
#     cost(i, j) = 이동거리(입구->자리j) + 이동거리(자리j->출구)
#                  + ALPHA * 예상주차시간(i) * 입구근접도(j)
#
#   - 앞의 항(이동거리)은 "가까운 자리에 넣을수록 좋다"는 그리디의 장점을 그대로 반영
#   - 뒤의 항은 "오래 머무를 차량일수록 입구/출구에서 먼 자리에 배정"해서
#     회전율이 높은(금방 나갈) 차량이 쓸 좋은 자리를 오래 비워두지 않도록 함
#     => 결과적으로 공간 효율(자리 회전율)이 올라간다.

from scipy.optimize import linear_sum_assignment


ALPHA = 0.08  # 예상 주차시간이 자리 배정에 미치는 가중치


def manhattan(a, b):

    return abs(a[0]-b[0]) + abs(a[1]-b[1])


class HungarianAllocator:
    """
    여러 대의 대기 차량과 여러 개의 빈 자리를
    헝가리안 알고리즘으로 한번에 최적 매칭한다.
    """

    def __init__(self, entry, exit_pos):

        self.entry = entry
        self.exit_pos = exit_pos


    # --------------------------------
    # 비용 행렬 계산
    # --------------------------------

    def build_cost_matrix(self, vehicles_info, slots):

        """
        vehicles_info : [{"dwell": 예상 주차 시간(tick)}, ...]
        slots         : [(row,col), ...]  빈 자리 목록

        반환: (len(vehicles_info) x len(slots)) 크기의 비용 행렬
        """

        n = len(vehicles_info)
        m = len(slots)

        cost = [[0.0]*m for _ in range(n)]

        for i, info in enumerate(vehicles_info):

            dwell = info.get("dwell", 0)

            for j, slot in enumerate(slots):

                travel = (
                    manhattan(self.entry, slot)
                    +
                    manhattan(slot, self.exit_pos)
                )

                proximity = 1.0 / (1 + manhattan(self.entry, slot))

                cost[i][j] = travel + ALPHA*dwell*proximity

        return cost


    # --------------------------------
    # 최적 할당 수행
    # --------------------------------

    def allocate(self, vehicles_info, slots):

        """
        반환: [(vehicle_index, slot), ...]
        차량 수 / 자리 수가 다를 경우 min(n,m) 개만 매칭되고
        나머지는 다음 라운드로 넘어간다 (대기).
        """

        if len(vehicles_info) == 0 or len(slots) == 0:
            return []

        cost = self.build_cost_matrix(vehicles_info, slots)

        row_ind, col_ind = linear_sum_assignment(cost)

        result = []

        for r, c in zip(row_ind, col_ind):

            result.append(
                (r, slots[c])
            )

        return result


# --------------------------------
# 베이스라인(그리디) 배정 - 성능 비교용
# --------------------------------

def greedy_allocate(vehicles_info, slots, entry):

    """
    각 차량마다 그 시점에서 입구와 가장 가까운 빈 자리를 순서대로 배정.
    (기존 map.nearest_slot() 과 동일한 방식 - Baseline 용)
    """

    remaining = list(slots)

    result = []

    for i in range(len(vehicles_info)):

        if not remaining:
            break

        best = min(
            remaining,
            key=lambda s: manhattan(entry, s)
        )

        remaining.remove(best)

        result.append((i, best))

    return result
