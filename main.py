# main.py

import pygame
import sys


from constants import *

from map import ParkingMap

from reservation import ReservationTable

from astar import CooperativeAStar

from parking_manager import ParkingManager
from sim_clock import PygameWallClock



# ==================================
# 주차장 그리기
# ==================================

def draw_map(screen, parking_map):


    for r in range(ROWS):

        for c in range(COLS):


            rect = pygame.Rect(

                c*TILE_SIZE,

                r*TILE_SIZE,

                TILE_SIZE-2,

                TILE_SIZE-2

            )


            value = parking_map.grid[r][c]



            if value == ROAD:

                color = ROAD_COLOR


            elif value == PARK:

                color = PARK_COLOR


            elif value == IN:

                color = ENTRY_COLOR


            elif value == OUT:

                color = EXIT_COLOR


            else:

                color = GRAY



            pygame.draw.rect(

                screen,

                color,

                rect

            )



# ==================================
# 차량 그리기
# ==================================

def draw_vehicle(screen, vehicles):


    font = pygame.font.SysFont(
        None,
        25
    )


    for car in vehicles:


        x = (
            car.col*TILE_SIZE
            +
            TILE_SIZE//2
        )


        y = (

            car.row*TILE_SIZE
            +
            TILE_SIZE//2

        )


        pygame.draw.circle(

            screen,

            CAR_COLOR,

            (x,y),

            TILE_SIZE//3

        )


        text = font.render(

            str(car.id),

            True,

            WHITE

        )


        screen.blit(

            text,

            (

                x-7,

                y-10

            )

        )



# ==================================
# 정보 표시
# ==================================

def draw_info(screen, manager):


    font = pygame.font.SysFont(

        None,

        28

    )


    mode_label = (
        "Hungarian+CoopA*"
        if manager.mode == "improved"
        else "Greedy (Baseline)"
    )


    lines = [

        f"Cars : {manager.count()} / {MAX_CAR}  (Mode: {mode_label})",

        f"Waiting to enter : {len(manager.pending)}   "
        f"Space used : {manager.space_efficiency():.0f}%",

        "Press M to switch mode (resets simulation)"

    ]


    for i, line in enumerate(lines):

        text = font.render(

            line,

            True,

            WHITE

        )


        pos = (10, 10 + i*24)


        # 밝은 타일 위에서도 잘 보이도록 텍스트 뒤에 어두운 반투명 박스를 깐다

        bg_rect = pygame.Rect(

            pos[0]-4,

            pos[1]-2,

            text.get_width()+8,

            text.get_height()+4

        )


        bg_surface = pygame.Surface(

            (bg_rect.width, bg_rect.height),

            pygame.SRCALPHA

        )


        bg_surface.fill((0, 0, 0, 160))


        screen.blit(bg_surface, (bg_rect.x, bg_rect.y))


        screen.blit(

            text,

            pos

        )



# ==================================
# Main
# ==================================

def main():


    pygame.init()



    screen = pygame.display.set_mode(

        (
            WIDTH,
            HEIGHT
        )

    )


    pygame.display.set_caption(

        "Cooperative A* Auto Parking Simulator"

    )



    clock = pygame.time.Clock()



    # 객체 생성 (모드에 따라 새로 구성 가능하도록 함수로 분리)

    def build_world(mode):

        parking_map = ParkingMap()

        reservation = ReservationTable()

        astar = CooperativeAStar(

            parking_map,

            reservation

        )

        manager = ParkingManager(

            parking_map,

            astar,

            reservation,

            PygameWallClock(),

            mode=mode

        )

        return parking_map, reservation, astar, manager


    current_mode = ALLOCATION_MODE

    parking_map, reservation, astar, manager = build_world(current_mode)



    running=True



    while running:


        clock.tick(FPS)


        # 이벤트

        for event in pygame.event.get():


            if event.type == pygame.QUIT:

                running=False


            if event.type == pygame.KEYDOWN:


                if event.key == pygame.K_ESCAPE:

                    running=False


                # M 키: Baseline(Greedy) <-> Improved(Hungarian) 전환 후 재시작
                if event.key == pygame.K_m:

                    current_mode = (
                        "baseline"
                        if current_mode == "improved"
                        else "improved"
                    )

                    parking_map, reservation, astar, manager = build_world(
                        current_mode
                    )



        # 차량 업데이트

        manager.update()



        # 화면 초기화

        screen.fill(GRAY)



        # 맵

        draw_map(

            screen,

            parking_map

        )


        # 차량

        draw_vehicle(

            screen,

            manager.get_vehicles()

        )


        # 정보

        draw_info(

            screen,

            manager

        )


        pygame.display.update()



    pygame.quit()

    sys.exit()



if __name__=="__main__":

    main()