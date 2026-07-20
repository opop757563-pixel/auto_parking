# vehicle.py

import random

from constants import *
from astar import CooperativeAStar
from license_plate import generate_unique_plate


class Vehicle:


    def __init__(
            self,
            vehicle_id,
            start,
            parking_slot,
            astar,
            reservation,
            clock,
            dwell_time=None,
            tick=0,
            entry_delay=0):


        self.id = vehicle_id

        # 고유 번호판 (예: "12가3456")
        # 유니티 쪽 LicensePlate와 매칭할 때 이 값을 그대로 사용한다.
        self.plate = generate_unique_plate()

        # 차종 (SEDAN/SUV/RV/EV) - 가중치 랜덤 배정 (constants.VEHICLE_TYPE_WEIGHTS 참고)
        # 유니티 쪽에서는 이 값으로 어떤 프리팹을 생성할지 결정한다.
        self.vehicle_type = random.choices(
            VEHICLE_TYPES,
            weights=VEHICLE_TYPE_WEIGHTS,
            k=1
        )[0]


        # 위치

        self.row = start[0]
        self.col = start[1]


        self.start = start

        self.parking_slot = parking_slot


        self.astar = astar

        self.reservation = reservation

        self.clock = clock


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



        # 같은 배치에서 여러 대가 한번에 ENTRY로 배정될 때, 실제로 움직이기
        # 시작하는 시점을 차량마다 조금씩 벌려서(entry_delay) 화면에서
        # 겹쳐 보이지 않게 한다. astar 탐색 자체는 "실제로 출발하는 시점"
        # 기준(tick+entry_delay)으로 하고, 그 앞에 ENTRY에 그대로 머무는
        # 대기 구간(wait step)을 경로 맨 앞에 붙여서 시간축을 맞춘다.

        self.entry_delay = entry_delay

        actual_start_tick = tick + entry_delay

        searched_path = self.astar.search(

            start,

            parking_slot,

            vehicle_id,

            start_time=actual_start_tick

        )


        if searched_path is not None:

            self.path = [start] * entry_delay + searched_path

        else:

            self.path = None


        self.path_index = 0



        # 출차 경로

        self.exit_path = []



        # 주차 시간

        self.park_start = 0



        # ------------------------------------
        # 통계용 타임스탬프 (baseline vs improved
        # 성능 비교, 평균 출차 대기시간 계산용)
        # ------------------------------------

        self.spawn_time = self.clock.now()

        self.exit_request_time = None   # 출차를 "요청"한 시각 (PARK_TIME 종료 시점)
        self.exit_start_time = None     # 실제로 출차 경로 탐색에 성공해 움직이기 시작한 시각
        self.done_time = None

        self.last_retry = -999999       # 출차 재탐색 쿨다운 타이머



        # 경로 예약

        if self.path:

            # self.path는 [ENTRY 대기 구간] + [실제 탐색 경로] 이므로,
            # start_time을 원래 배치 시각(tick)으로 두면 인덱스별 시간이
            # 대기 구간과 실제 탐색 결과(start_time=actual_start_tick) 양쪽과
            # 정확히 일치한다.

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


        now = self.clock.now()

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

                self.exit_start_time = self.clock.now()



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