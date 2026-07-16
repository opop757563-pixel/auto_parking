# parking_manager.py

import random

import pygame

from constants import *
from vehicle import Vehicle
from allocation import HungarianAllocator, greedy_allocate, manhattan


class ParkingManager:


    def __init__(
            self,
            parking_map,
            astar,
            reservation,
            mode=None,
            max_cars=None):


        self.map = parking_map

        self.astar = astar

        self.reservation = reservation


        # "improved"(Hungarian + Cooperative A*) / "baseline"(Greedy 최근접)
        self.mode = mode if mode is not None else ALLOCATION_MODE

        self.allocator = HungarianAllocator(ENTRY, EXIT)


        # 시뮬레이션 동안 총 몇 대까지 받을지 (데모: MAX_CAR / 벤치마크: 크게)
        self.max_cars = max_cars if max_cars is not None else MAX_CAR


        # 현재 차량 (실제로 맵 위에서 움직이고 있는 차량들)

        self.vehicles = []


        # 아직 자리를 배정받지 못하고 입구에서 대기 중인 "요청" 큐
        # 항목: {"dwell": ms, "request_time": ms}
        self.pending = []


        # 생성(=요청 발생) 차량 수 (MAX_CAR 상한 체크용, pending 포함)

        self.vehicle_count = 0


        # 종료(출차 완료)된 차량들의 통계 기록
        # {"dwell", "enter_wait"(입차 대기), "exit_wait"(출차 대기), "turnaround"}
        self.stats = []


        # 마지막 생성 시간

        self.last_spawn = pygame.time.get_ticks()

        # 마지막 배정(batch) 처리 시간

        self.last_batch = pygame.time.get_ticks()


        # 시뮬레이션 공용 시계 (모든 차량의 예약 시간축을 통일하기 위함)
        # update() 가 호출될 때마다 1씩 증가한다.

        self.tick = 0



    # ==================================
    # 차량 도착(요청) 생성
    # ==================================
    # 실제 자리 배정은 여기서 하지 않고 pending 큐에만 쌓는다.
    # -> process_batch() 에서 여러 대를 "동시에" 놓고 최적 배정한다.

    def spawn_vehicle(self):


        total_requested = (

            self.vehicle_count
            +
            len(self.pending)

        )


        if total_requested >= self.max_cars:

            return


        dwell = random.randint(DWELL_MIN, DWELL_MAX)


        self.pending.append({

            "dwell": dwell,

            "request_time": pygame.time.get_ticks()

        })



    # ==================================
    # 대기 중인 요청을 자리에 일괄 배정
    # ==================================

    def process_batch(self):


        if not self.pending:

            return


        free_slots = self.map.get_free_slots()


        if not free_slots:

            return


        vehicles_info = self.pending


        if self.mode == "improved":

            matches = self.allocator.allocate(

                vehicles_info,

                free_slots

            )

        else:

            matches = greedy_allocate(

                vehicles_info,

                free_slots,

                ENTRY

            )


        if not matches:

            return


        # 뒤에서부터 pop 해야 인덱스가 안 꼬인다

        matches_sorted = sorted(

            matches,

            key=lambda m: m[0],

            reverse=True

        )


        for idx, slot in matches_sorted:


            request = self.pending[idx]


            self.map.occupy_slot(slot)


            self.vehicle_count += 1


            car = Vehicle(

                self.vehicle_count,

                ENTRY,

                slot,

                self.astar,

                self.reservation,

                dwell_time=request["dwell"],

                tick=self.tick

            )


            # 경로 생성 실패 -> 자리 반환하고 다음 배치 라운드에서 재시도

            if car.path is None:


                self.map.release_slot(slot)

                self.vehicle_count -= 1

                continue


            # 통계용: 입차 대기시간 (요청 시각 -> 실제 배정/출발 시각)

            car.enter_wait = (

                pygame.time.get_ticks()
                -
                request["request_time"]

            )


            self.vehicles.append(car)


            del self.pending[idx]



    # ==================================
    # 차량 업데이트
    # ==================================

    def update(self):


        now = pygame.time.get_ticks()


        # 공용 시계 전진 (모든 차량이 한 스텝씩 같이 움직이는 기준)

        self.tick += 1



        # 일정 시간마다 차량 도착(요청) 생성

        if (

            now - self.last_spawn

            >= SPAWN_INTERVAL

        ):


            self.last_spawn = now


            self.spawn_vehicle()



        # 일정 시간마다 대기열 일괄 배정 (Hungarian / Greedy)

        if (

            now - self.last_batch

            >= BATCH_WINDOW

        ):


            self.last_batch = now


            self.process_batch()



        remove_list=[]



        for car in self.vehicles:


            car.update(self.tick)



            if car.finished():

                remove_list.append(car)



        # 완료 차량 제거 + 통계 기록

        for car in remove_list:


            self.reservation.remove_vehicle(

                car.id

            )


            self.map.release_slot(

                car.parking_slot

            )


            self.stats.append({

                "dwell": car.dwell_time,

                "enter_wait": getattr(car, "enter_wait", 0),

                "exit_wait": car.exit_wait_time(),

                "turnaround": (

                    car.done_time - car.spawn_time
                    if car.done_time is not None
                    else None

                )

            })


            self.vehicles.remove(car)



    # ==================================
    # 현재 차량 반환
    # ==================================

    def get_vehicles(self):

        return self.vehicles



    # ==================================
    # 차량 수 (현재 맵 위 + 대기중)
    # ==================================

    def count(self):

        return len(self.vehicles) + len(self.pending)



    # ==================================
    # 공간 효율성 (%) - 현재 시점 스냅샷
    # ==================================

    def space_efficiency(self):

        total = len(self.map.parking_slots)

        if total == 0:

            return 0.0

        used = total - self.map.free_count()

        return 100.0 * used / total
