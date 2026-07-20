# parking_manager.py

import random
import socket

from constants import *
from vehicle import Vehicle
from allocation import HungarianAllocator, greedy_allocate, manhattan
from license_plate import release_plate


# ==================================
# 유니티로 상태 변화를 실시간으로 밀어넣는(push) UDP 송신부
# ==================================
# 프로토콜(유니티 수신 스크립트와 반드시 일치해야 함):
#   "SPAWN:{id}:{plate}:{type}:{r},{c};{r},{c};..."  - 차량 신규 생성 + 번호판 + 차종 + 입차 경로
#   "EXIT_START:{id}:{r},{c};{r},{c};..."             - 출차 시작 + 출차 경로
#   "REMOVE:{id}"                                     - 출차 완료, 유니티에서 제거
#
# plate 필드는 "00가0000" 형식(license_plate.py 참고)이며, 차량마다 고유하다.
# type 필드는 "SEDAN"/"SUV"/"RV"/"EV" 중 하나(constants.VEHICLE_TYPES 참고)이며,
# 유니티 쪽에서는 이 값으로 어떤 차량 프리팹을 생성할지 결정한다.
# 유니티 쪽에서는 LicensePlate.TrySetPlate(plate)로 이 값을 그대로 반영해서
# 파이썬 시뮬레이션과 유니티 차량의 번호판이 항상 일치하도록 한다.
# (나중에 카메라 인식 기능에서 인식된 문자열로 이 번호판과 매칭하게 됨)

UNITY_HOST = "127.0.0.1"
UNITY_PORT = 9000

_unity_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_to_unity(message):
    try:
        _unity_socket.sendto(
            message.encode("utf-8"),
            (UNITY_HOST, UNITY_PORT)
        )
    except OSError:
        # 유니티가 아직 안 켜져 있거나 소켓 문제여도 시뮬레이션 자체는 계속 돌아가야 함
        pass


def _path_to_str(path):
    return ";".join(f"{r},{c}" for r, c in path)


class ParkingManager:


    def __init__(
            self,
            parking_map,
            astar,
            reservation,
            clock,
            mode=None,
            max_cars=None,
            auto_spawn=True):


        self.map = parking_map

        self.astar = astar

        self.reservation = reservation

        self.clock = clock


        # "improved"(Hungarian + Cooperative A*) / "baseline"(Greedy 최근접)
        self.mode = mode if mode is not None else ALLOCATION_MODE

        self.allocator = HungarianAllocator(ENTRY, EXIT)


        # 시뮬레이션 동안 총 몇 대까지 받을지 (데모: MAX_CAR / 벤치마크: 크게)
        self.max_cars = max_cars if max_cars is not None else MAX_CAR


        # 외부(유니티 등)가 도착 이벤트를 직접 보낼 경우 False로 끄면
        # 내부 랜덤 spawn_vehicle() 타이머가 동작하지 않는다.
        self.auto_spawn = auto_spawn


        # 현재 차량 (실제로 맵 위에서 움직이고 있는 차량들)

        self.vehicles = []


        # 아직 자리를 배정받지 못하고 입구에서 대기 중인 "요청" 큐
        # 항목: {"dwell": ms, "request_time": ms}
        self.pending = []


        # 생성(=요청 발생) 차량 수 (MAX_CAR 상한 체크용, pending 포함)

        self.vehicle_count = 0


        # 종료(출차 완료)된 차량들의 통계 기록
        self.stats = []


        # 마지막 생성 시간 / 마지막 배정(batch) 처리 시간

        self.last_spawn = self.clock.now()

        self.last_batch = self.clock.now()


        # 시뮬레이션 공용 시계 (모든 차량의 예약 시간축을 통일하기 위함)

        self.tick = 0



    # ==================================
    # 차량 도착(요청) 생성 - 내부 랜덤 spawn (데모/벤치마크용)
    # ==================================

    def spawn_vehicle(self):

        dwell = random.randint(DWELL_MIN, DWELL_MAX)

        self.request_arrival(dwell=dwell)



    # ==================================
    # 차량 도착(요청) 생성 - 외부(유니티 등)에서 호출하는 진입점
    # ==================================

    def request_arrival(self, dwell=None):

        total_requested = (

            self.vehicle_count
            +
            len(self.pending)

        )


        if total_requested >= self.max_cars:

            return False


        if dwell is None:
            dwell = random.randint(DWELL_MIN, DWELL_MAX)


        self.pending.append({

            "dwell": dwell,

            "request_time": self.clock.now()

        })

        return True



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

            matches = self.allocator.allocate(vehicles_info, free_slots)

        else:

            matches = greedy_allocate(vehicles_info, free_slots, ENTRY)


        if not matches:

            return


        matches_sorted = sorted(matches, key=lambda m: m[0], reverse=True)

        # 같은 배치에서 여러 대가 한꺼번에 ENTRY로 몰리면 화면상 겹쳐
        # 보이므로, 실제로 생성(입차 시작)되는 순서대로 입구 출발 시점을
        # ENTRY_STAGGER_TICKS 만큼씩 벌려준다.
        entry_order = 0


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

                self.clock,

                dwell_time=request["dwell"],

                tick=self.tick,

                entry_delay=entry_order * ENTRY_STAGGER_TICKS

            )


            # 경로 생성 실패 -> 자리 반환하고 다음 배치 라운드에서 재시도

            if car.path is None:


                self.map.release_slot(slot)

                self.vehicle_count -= 1

                continue


            car.enter_wait = self.clock.now() - request["request_time"]


            self.vehicles.append(car)


            del self.pending[idx]


            entry_order += 1


            # [유니티 연동] 차가 처음 태어나서 주차 칸으로 갈 때 전체 경로 전송

            send_to_unity(
                f"SPAWN:{car.id}:{car.plate}:{car.vehicle_type}:{_path_to_str(car.path)}"
            )



    # ==================================
    # 차량 업데이트
    # ==================================
    # dt_ms: 이번 업데이트에서 시계를 얼마나 진행시킬지.
    #        None이면 clock을 진행시키지 않고(=PygameWallClock처럼 이미
    #        알아서 흐르는 시계이거나, 외부에서 이미 advance 했다고 가정)

    def update(self, dt_ms=None):


        if dt_ms is not None:
            self.clock.advance(dt_ms)


        now = self.clock.now()


        self.tick += 1


        # 일정 시간마다 차량 도착(요청) 생성 (외부 도착 이벤트를 쓰는 경우 끔)

        if self.auto_spawn and (now - self.last_spawn >= SPAWN_INTERVAL):

            self.last_spawn = now

            self.spawn_vehicle()


        remove_list = []


        for car in self.vehicles:

            old_state = car.state

            car.update(self.tick)


            # [유니티 연동] 주차 중이던 차가 출차를 시작하는 순간

            if old_state == "PARKED" and car.state == "EXIT":

                send_to_unity(
                    f"EXIT_START:{car.id}:{_path_to_str(car.path)}"
                )


            if car.finished():

                remove_list.append(car)


        # 일정 시간마다 대기열 일괄 배정 (Hungarian / Greedy)
        #
        # 반드시 위의 차량 이동 루프보다 "뒤"에서 실행해야 한다.
        # 만약 이 루프보다 앞에서 새 차량을 만들면, 그 차량이 생성된
        # 바로 이번 tick의 이동 루프에도 포함되어 태어나자마자 한 칸
        # 더 움직여버린다. 그러면 그 차량의 실제 위치가 예약 테이블이
        # 가정한 시간보다 1틱 앞서게 되어(누적됨), 정상적으로 시간을
        # 계산한 다른 차량(특히 출차 중인 차량)과 실제로는 충돌하는데도
        # 예약 테이블상으로는 충돌이 아닌 것처럼 보이는 버그가 생긴다.
        # (신규 생성 차량은 다음 tick부터 움직이기 시작해야 정상)

        if now - self.last_batch >= BATCH_WINDOW:

            self.last_batch = now

            self.process_batch()


        # 완료 차량 제거 + 통계 기록 + 유니티에 제거 신호

        for car in remove_list:

            self.reservation.remove_vehicle(car.id)

            self.map.release_slot(car.parking_slot)

            release_plate(car.plate)


            # [유니티 연동] 주차장을 완전히 빠져나간 차 제거 신호

            send_to_unity(f"REMOVE:{car.id}")


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



    # ==================================
    # 외부(유니티 등)로 보낼 상태 스냅샷 (폴링 방식이 필요할 때 대비해 유지)
    # ==================================

    def get_state(self):

        return {

            "tick": self.tick,

            "cars": [
                {
                    "id": car.id,
                    "plate": car.plate,
                    "vehicle_type": car.vehicle_type,
                    "row": car.row,
                    "col": car.col,
                    "state": car.state,
                }
                for car in self.vehicles
            ],

            "pending": len(self.pending),

            "space_efficiency": self.space_efficiency(),

        }