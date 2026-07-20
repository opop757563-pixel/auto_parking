# sim_clock.py
#
# pygame.time.get_ticks() 대신 쓰는 순수 시뮬레이션 시계.
# 유니티(또는 어떤 엔진이든)가 dt_ms 만큼 "진행시켜라"라고 명령하면
# 그만큼만 흐르는 구조라서, 실제 벽시계와 무관하게 결정론적으로 동작한다.

class SimClock:

    def __init__(self):
        self.ms = 0

    def now(self):
        return self.ms

    def advance(self, dt_ms):
        self.ms += dt_ms


class PygameWallClock:
    """
    GUI(main.py)나 benchmark.py처럼 실제 벽시계 기준으로 돌리고 싶을 때 쓰는
    SimClock 호환 래퍼. now()는 pygame.time.get_ticks()를 그대로 반환하고,
    advance()는 아무 것도 하지 않는다(이미 벽시계가 알아서 흐르기 때문).
    """

    def __init__(self):
        import pygame
        self._pygame = pygame

    def now(self):
        return self._pygame.time.get_ticks()

    def advance(self, dt_ms):
        pass
