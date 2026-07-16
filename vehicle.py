# vehicle.py

import pygame

from constants import *
from astar import CooperativeAStar


class Vehicle:


    def __init__(
            self,
            vehicle_id,
            start,
            parking_slot,
            astar,
            reservation,
            dwell_time=None,
            tick=0):


        self.id = vehicle_id


        # 위치

        self.row = start[0]
        self.col = start[1]


        self.start = start

        self.parking_slot = parking_slot


        self.astar = astar

        self.reservation = reservation


        # 시뮬레이션 공용 시계(tick) - 예약 테이블과 시간축을 맞추기 위해 필요

        self.current_tick = tick



        # 예상/실제 주차 시간(ms)
        # 헝가리안 자리 배정의 비용 함수에 쓰이는 값과 동일한 값을
        # 실제 시뮬레이션에도 반영한다 (예상 = 실제로 가정)

        self.dwell_time = dwell_time if dwell_time is not None else PARK_TIME



        # 상태

        self.state = "ENTER"

        # ENTER
        # PARKING
        # PARKED
        # EXIT
        # DONE



        # 이동 경로

        self.path = self.astar.search(

            start,

            parking_slot,

            vehicle_id,

            start_time=tick

        )


        self.path_index = 0



        # 출차 경로

        self.exit_path = []



        # 주차 시간

        self.park_start = 0



        # ------------------------------------
        # 통계용 타임스탬프 (baseline vs improved
        # 성능 비교, 평균 출차 대기시간 계산용)
        # ------------------------------------

        self.spawn_time = pygame.time.get_ticks()

        self.exit_request_time = None   # 출차를 "요청"한 시각 (PARK_TIME 종료 시점)
        self.exit_start_time = None     # 실제로 출차 경로 탐색에 성공해 움직이기 시작한 시각
        self.done_time = None

        self.last_retry = -999999       # 출차 재탐색 쿨다운 타이머



        # 경로 예약

        if self.path:

            self.reservation.reserve(

                self.id,

                self.path,

                start_time=tick

            )



    # ==================================
    # 현재 위치
    # ==================================

    def position(self):

        return (
            self.row,
            self.col
        )



    # ==================================
    # 한 칸 이동
    # ==================================

    def move(self):


        if self.path_index >= len(self.path)-1:

            return False



        self.path_index += 1


        self.row, self.col = (

            self.path[self.path_index]

        )


        return True



    # ==================================
    # 업데이트
    # ==================================

    def update(self, tick=None):


        now = pygame.time.get_ticks()

        if tick is not None:

            self.current_tick = tick



        # -----------------------------
        # 입차 중
        # -----------------------------

        if self.state == "ENTER":


            moved = self.move()



            if not moved:


                self.state="PARKED"


                self.park_start = now



        # -----------------------------
        # 주차 상태
        # -----------------------------

        elif self.state=="PARKED":


            if self.exit_request_time is None:

                if now - self.park_start >= self.dwell_time:

                    # 출차를 "요청"한 시각 기록 (대기시간 측정 기준점)
                    self.exit_request_time = now


            if self.exit_request_time is not None:

                # 재탐색 스팸을 막기 위한 쿨다운(ms)
                if now - self.last_retry >= RETRY_COOLDOWN:

                    self.last_retry = now

                    self.start_exit()



        # -----------------------------
        # 출차 중
        # -----------------------------

        elif self.state=="EXIT":


            moved=self.move()



            if not moved:


                self.state="DONE"

                self.done_time = now



    # ==================================
    # 출차 시작
    # ==================================

    def start_exit(self):


        # 기존 예약 제거

        self.reservation.remove_vehicle(

            self.id

        )



        self.exit_path = self.astar.search(

            self.position(),

            EXIT,

            self.id,

            start_time=self.current_tick

        )



        if self.exit_path:


            self.path=self.exit_path


            self.path_index=0


            self.state="EXIT"


            if self.exit_start_time is None:

                self.exit_start_time = pygame.time.get_ticks()



            # 새로운 경로 예약

            self.reservation.reserve(

                self.id,

                self.path,

                start_time=self.current_tick

            )


        else:


            # 경로 실패 시 다시 대기

            self.state="PARKED"



    # ==================================
    # 출차 대기시간 (요청 -> 실제 출발)
    # ==================================

    def exit_wait_time(self):

        if self.exit_request_time is None or self.exit_start_time is None:

            return None

        return self.exit_start_time - self.exit_request_time



    # ==================================
    # 완료 확인
    # ==================================

    def finished(self):

        return self.state=="DONE"