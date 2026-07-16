# reservation.py

class ReservationTable:
    """
    Cooperative A*용 시간-공간 예약 테이블

    저장 형태:
    {
        time : {(row, col), (row, col), ...}
    }

    예)
    {
        0 : {(0,9)},
        1 : {(1,9)},
        2 : {(2,9)}
    }
    """

    def __init__(self):

        # 시간별 점유 위치
        self.table = {}


        # 차량별 예약 경로 저장
        # vehicle_id : [(time,row,col), ...]
        self.vehicle_paths = {}


    # --------------------------------
    # 특정 시간 위치가 예약되어 있는지
    # --------------------------------

    def is_reserved(self, time, position):

        if time not in self.table:
            return False

        return position in self.table[time]


    # --------------------------------
    # 위치 예약
    # --------------------------------

    def reserve(self, vehicle_id, path, start_time=0):

        """
        path:
        [(row,col),
         (row,col),
         (row,col)]

        시간은 start_time + path index 기준
        (astar.search() 에 넘긴 start_time과 반드시 동일해야
         서로 다른 차량들의 예약이 같은 시계를 기준으로 정렬된다)
        """

        reservations = []


        for i, pos in enumerate(path):

            t = start_time + i

            if t not in self.table:

                self.table[t] = set()


            self.table[t].add(pos)

            reservations.append(
                (t,pos)
            )


        self.vehicle_paths[vehicle_id] = reservations



    # --------------------------------
    # 충돌 검사
    # --------------------------------

    def check_collision(
            self,
            current,
            next_pos,
            current_time):


        next_time = current_time + 1


        # 1. 같은 시간 같은 위치 충돌

        if self.is_reserved(
            next_time,
            next_pos
        ):

            return True



        # 2. 서로 자리 바꾸는 충돌

        # 다른 차량이
        # next_pos -> current 로 이동하는 경우

        if self.is_reserved(
            next_time,
            current
        ):

            if self.is_reserved(
                current_time,
                next_pos
            ):

                return True



        return False



    # --------------------------------
    # 차량 예약 제거
    # --------------------------------

    def remove_vehicle(self, vehicle_id):


        if vehicle_id not in self.vehicle_paths:
            return


        for t,pos in self.vehicle_paths[vehicle_id]:


            if t in self.table:

                if pos in self.table[t]:

                    self.table[t].remove(pos)


                if len(self.table[t]) == 0:

                    del self.table[t]


        del self.vehicle_paths[vehicle_id]



    # --------------------------------
    # 전체 예약 초기화
    # --------------------------------

    def clear(self):

        self.table.clear()

        self.vehicle_paths.clear()



    # --------------------------------
    # 디버깅용 출력
    # --------------------------------

    def print_table(self):

        print("===== Reservation Table =====")


        for t in sorted(self.table):

            print(
                f"time {t}: {self.table[t]}"
            )