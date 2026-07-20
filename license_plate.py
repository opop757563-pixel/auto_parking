# license_plate.py
#
# 한국 승용차 번호판 형식(예: "12가3456") 문자열을 생성/관리하는 모듈.
# 유니티 쪽 LicensePlateGenerator.cs와 형식(앞2자리+한글1글자+뒤4자리)을
# 반드시 동일하게 유지할 것 - 나중에 카메라 인식(OCR) 결과와 파이썬
# 시뮬레이션의 차량을 매칭할 때 서로 다른 포맷이면 매칭이 깨진다.
#
# 사용법:
#   from license_plate import generate_unique_plate, release_plate
#
#   plate = generate_unique_plate()   # 새 차량 생성 시
#   ...
#   release_plate(plate)              # 차량이 시뮬레이션에서 완전히 나갈 때

import random

# 실제 승용차(비사업용) 번호판에 사용되는 한글 글자 목록
PLATE_LETTERS = [
    "가", "나", "다", "라", "마",
    "거", "너", "더", "러", "머", "버", "서", "어", "저",
    "고", "노", "도", "로", "모", "보", "소", "오", "조",
    "구", "누", "두", "루", "무", "부", "수", "우", "주",
    "아", "바", "사", "자", "하", "허", "호",
]

# 시뮬레이션 전체에서 현재 사용 중인 번호판 집합 (중복 방지용)
_active_plates = set()


def _generate_random_plate():
    front = random.randint(1, 99)
    letter = random.choice(PLATE_LETTERS)
    back = random.randint(0, 9999)

    return f"{front:02d}{letter}{back:04d}"


def generate_unique_plate(max_attempts=1000):
    """
    현재 사용 중이지 않은 고유 번호판을 생성하고, 사용 중 집합에 등록한다.
    """

    for _ in range(max_attempts):

        candidate = _generate_random_plate()

        if candidate not in _active_plates:

            _active_plates.add(candidate)

            return candidate

    raise RuntimeError(
        f"[license_plate] {max_attempts}회 시도했지만 고유한 번호판을 생성하지 못했습니다. "
        f"현재 사용 중인 번호판 수: {len(_active_plates)}"
    )


def release_plate(plate):
    """
    차량이 시뮬레이션을 완전히 벗어날 때(REMOVE 시점) 번호판을 반납한다.
    반납하지 않으면 사용 중 집합이 계속 쌓여서, 시뮬레이션이 오래 돌수록
    번호판 조합이 고갈되어 generate_unique_plate()가 느려지거나 실패할 수 있다.
    """

    _active_plates.discard(plate)


def is_valid_format(plate):
    """
    문자열이 "00가0000" 형식에 맞는지 검사.
    (나중에 카메라 인식 결과를 검증할 때도 재사용 가능)
    """

    if not plate or len(plate) != 7:
        return False

    if not (plate[0].isdigit() and plate[1].isdigit()):
        return False

    if plate[2] not in PLATE_LETTERS:
        return False

    if not plate[3:7].isdigit():
        return False

    return True


def active_plate_count():
    return len(_active_plates)
