# astar.py

import heapq

from constants import *
from reservation import ReservationTable


class CooperativeAStar:


    def __init__(self, parking_map, reservation):

        self.map = parking_map
        self.reservation = reservation



    # ------------------------------
    # 휴리스틱
    # ------------------------------

    def heuristic(self, a, b):

        return (
            abs(a[0]-b[0])
            +
            abs(a[1]-b[1])
        )



    # ------------------------------
    # 시간 포함 이웃 탐색
    # ------------------------------

    def get_neighbors(self, position, goal=None):

        r,c = position


        moves = [

            (-1,0),   # 위
            (1,0),    # 아래
            (0,-1),   # 왼쪽
            (0,1),    # 오른쪽

            (0,0)     # 대기
        ]


        result=[]


        for dr,dc in moves:

            nr=r+dr
            nc=c+dc


            if not self.map.in_range((nr,nc)):
                continue


            # 대기(제자리)는 항상 허용, 이동은 주행 가능한 칸만 허용
            # (다른 차량의 주차칸을 그냥 통과하는 경로를 막는다)

            if (dr,dc) != (0,0):

                if not self.map.is_driveable((nr,nc), goal):
                    continue


            result.append(
                (nr,nc)
            )


        return result



    # ------------------------------
    # Cooperative A*
    # ------------------------------

    def search(
            self,
            start,
            goal,
            vehicle_id,
            max_time=200,
            start_time=0):


        """
        반환:
        [(row,col),
         (row,col),
         ...]

        start_time:
            이 탐색을 "시뮬레이션 전체 공용 시계" 상의 몇 시(tick)부터
            시작하는지 나타낸다. 항상 0으로 고정하면 서로 다른 시점에
            출발한 차량들의 예약 테이블 t값이 서로 어긋나서(동상이몽),
            실제로는 안 겹치는 경로를 겹친다고 오판하거나 반대로
            실제 충돌을 놓치는 문제가 생긴다. (기존 버그)
        """



        open_list=[]



        start_state=(start[0],start[1],start_time)



        heapq.heappush(

            open_list,

            (
                self.heuristic(start,goal),
                0,
                start_state
            )
        )



        came_from={}

        cost={}

        cost[start_state]=0



        while open_list:



            _, current_cost, state = heapq.heappop(
                open_list
            )


            r,c,t = state


            current=(r,c)



            # 목적지 도착

            if current==goal:


                return self.make_path(
                    came_from,
                    state
                )



            # 시간 제한 (절대 tick이 아니라 탐색 시작 후 경과 스텝 기준)

            if t - start_time >= max_time:

                continue



            # 다음 위치 탐색

            for nxt in self.get_neighbors(current, goal):


                next_time=t+1



                # 예약 충돌 확인

                if self.reservation.check_collision(

                    current,
                    nxt,
                    t

                ):

                    continue



                next_state=(

                    nxt[0],
                    nxt[1],
                    next_time

                )



                new_cost=current_cost+1



                if (

                    next_state not in cost

                    or

                    new_cost < cost[next_state]

                ):


                    cost[next_state]=new_cost



                    priority=(

                        new_cost

                        +

                        self.heuristic(
                            nxt,
                            goal
                        )

                    )


                    heapq.heappush(

                        open_list,

                        (
                            priority,
                            new_cost,
                            next_state
                        )

                    )


                    came_from[next_state]=state



        return None



    # ------------------------------
    # 경로 복원
    # ------------------------------

    def make_path(
            self,
            came_from,
            current):


        path=[]


        while current in came_from:


            path.append(
                (
                    current[0],
                    current[1]
                )
            )


            current=came_from[current]



        path.append(

            (
                current[0],
                current[1]
            )

        )


        path.reverse()


        return path