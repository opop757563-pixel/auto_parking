# benchmark.py
#
# Baseline(그리디 최근접 배정) vs Improved(Hungarian 배정 + Cooperative A*)
# 성능 비교용 헤드리스(화면 없이) 벤치마크 스크립트.
#
# 측정 지표:
#   1) 평균 출차 대기시간 (exit_wait) - PARK_TIME이 끝나고 출차를
#      "요청"한 시점부터 실제로 출차 경로를 확보해 움직이기 시작할
#      때까지 걸린 시간. 병목/정체가 심할수록 이 값이 커진다.
#   2) 평균 입차 대기시간 (enter_wait) - 입구에 도착(요청)한 시점부터
#      자리를 배정받고 실제로 출발하기까지 걸린 시간.
#   3) 평균 회전 시간 (turnaround) - 도착부터 완전히 출차 완료까지.
#   4) 공간 효율성(%) - 시뮬레이션 동안 시간 평균 주차칸 사용률.
#   5) 처리량(throughput) - 동일 시간 동안 완료된 차량 수.
#
# 사용법:
#   python3 benchmark.py
#
# 결과: benchmark_result.png (막대그래프), 콘솔에 요약 표 출력

import os
import sys
import time
import statistics

import constants

# ------------------------------------------------------------
# 벤치마크는 짧은 시간 안에 여러 대의 입/출차 사이클을 관찰해야
# 하므로, 데모용 GUI 상수보다 훨씬 빠른(가속된) 값으로 오버라이드한다.
# (constants 모듈의 속성을 먼저 바꾼 뒤에 이를 사용하는 모듈들을
#  import 해야 "from constants import *" 로 가속된 값이 전달된다)
# ------------------------------------------------------------

constants.SPAWN_INTERVAL = 150      # 0.15초마다 새 차량 "도착 요청" (혼잡 상황 재현)
constants.DWELL_MIN = 3000          # 최소 주차 시간(ms)
constants.DWELL_MAX = 12000         # 최대 주차 시간(ms) - 자리가 귀해지도록 충분히 길게
constants.BATCH_WINDOW = 150        # 0.15초마다 대기열 일괄 배정
constants.RETRY_COOLDOWN = 100
constants.MAX_CAR = 10**9           # 벤치마크에서는 상한을 사실상 없앰


import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

pygame.init()


from map import ParkingMap
from reservation import ReservationTable
from astar import CooperativeAStar
from parking_manager import ParkingManager
from sim_clock import PygameWallClock


RUN_SECONDS = 40.0     # 모드별 시뮬레이션 실행 시간(실제 wall-clock 초)
TICK_DT = 0.02         # 시뮬레이션 스텝 간격(초) - FPS=5이던 GUI보다 촘촘하게


def run_simulation(mode, run_seconds=RUN_SECONDS):

    parking_map = ParkingMap()
    reservation = ReservationTable()
    astar = CooperativeAStar(parking_map, reservation)

    manager = ParkingManager(
        parking_map,
        astar,
        reservation,
        PygameWallClock(),
        mode=mode,
        max_cars=10**9,
    )

    space_samples = []

    start = time.time()

    while time.time() - start < run_seconds:

        manager.update()

        space_samples.append(manager.space_efficiency())

        time.sleep(TICK_DT)

    elapsed = time.time() - start

    avg_space = (
        statistics.mean(space_samples) if space_samples else 0.0
    )

    throughput_per_min = len(manager.stats) / elapsed * 60.0

    return {
        "mode": mode,
        "stats": manager.stats,
        "avg_space_efficiency": avg_space,
        "throughput_per_min": throughput_per_min,
        "elapsed": elapsed,
        "still_active": len(manager.vehicles),
        "still_pending": len(manager.pending),
    }


def summarize(result):

    stats = result["stats"]

    def avg(key):

        vals = [
            s[key] for s in stats
            if s.get(key) is not None
        ]

        return statistics.mean(vals) if vals else 0.0

    return {
        "mode": result["mode"],
        "completed": len(stats),
        "avg_enter_wait_ms": avg("enter_wait"),
        "avg_exit_wait_ms": avg("exit_wait"),
        "avg_turnaround_ms": avg("turnaround"),
        "avg_space_efficiency": result["avg_space_efficiency"],
        "throughput_per_min": result["throughput_per_min"],
    }


def print_table(summaries):

    headers = [
        "Mode",
        "Completed",
        "Avg Enter Wait(ms)",
        "Avg Exit Wait(ms)",
        "Avg Turnaround(ms)",
        "Space Eff(%)",
        "Throughput(/min)",
    ]

    rows = []

    for s in summaries:

        rows.append([
            s["mode"],
            str(s["completed"]),
            f'{s["avg_enter_wait_ms"]:.0f}',
            f'{s["avg_exit_wait_ms"]:.0f}',
            f'{s["avg_turnaround_ms"]:.0f}',
            f'{s["avg_space_efficiency"]:.1f}',
            f'{s["throughput_per_min"]:.1f}',
        ])

    widths = [
        max(len(headers[i]), *(len(r[i]) for r in rows))
        for i in range(len(headers))
    ]

    def fmt_row(cells):
        return " | ".join(
            cell.ljust(widths[i]) for i, cell in enumerate(cells)
        )

    print(fmt_row(headers))
    print("-+-".join("-"*w for w in widths))

    for r in rows:
        print(fmt_row(r))


def make_chart(summaries, out_path):

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    modes = [s["mode"] for s in summaries]

    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()

    metrics = [
        ("avg_enter_wait_ms", "Avg Entry Wait Time (ms)"),
        ("avg_turnaround_ms", "Avg Turnaround Time (ms)"),
        ("avg_space_efficiency", "Avg Space Efficiency (%)"),
        ("throughput_per_min", "Throughput (cars / min)"),
    ]

    colors = ["#9aa5b1", "#3b82f6"]

    for ax, (key, title) in zip(axes, metrics):

        values = [s[key] for s in summaries]

        bars = ax.bar(modes, values, color=colors[:len(modes)])

        ax.set_title(title, fontsize=11)
        ax.set_ylabel(title)

        for b, v in zip(bars, values):
            ax.text(
                b.get_x() + b.get_width()/2,
                v,
                f"{v:.0f}" if v >= 10 else f"{v:.1f}",
                ha="center", va="bottom", fontsize=9
            )

    fig.suptitle(
        "Baseline (Greedy) vs Improved (Hungarian + Cooperative A*)",
        fontsize=13
    )

    fig.tight_layout(rect=[0, 0, 1, 0.94])

    fig.savefig(out_path, dpi=150)

    print(f"\n차트 저장 완료: {out_path}")


def main():

    print(f"각 모드 {RUN_SECONDS:.0f}초씩 시뮬레이션 실행 중...\n")

    results = []

    for mode in ["baseline", "improved"]:

        print(f"--- {mode} 실행 중 ---")

        result = run_simulation(mode)

        results.append(result)

        print(
            f"{mode}: 완료 {len(result['stats'])}대, "
            f"현재 진행중 {result['still_active']}대, "
            f"대기중 {result['still_pending']}대"
        )

    summaries = [summarize(r) for r in results]

    print()
    print_table(summaries)

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "benchmark_result.png"
    )

    make_chart(summaries, out_path)


if __name__ == "__main__":
    main()
