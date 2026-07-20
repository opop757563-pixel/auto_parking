import socket
import json
import time

HOST = '127.0.0.1'
PORT = 9999

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"[파이썬 서버] 서버가 시작되었습니다. (Port: {PORT})")

    client_socket, addr = server_socket.accept()
    print(f"[파이썬 서버] 유니티 연결됨: {addr}")

    try:
        # 1. 처음 연결되었을 때는 두 차량을 생성(Spawn)하는 데이터 전송
        print("[파이썬 서버] 1단계: 차량 스폰 신호 전송")
        spawn_data = {
            "vehicles": [
                {"vehicle_id": "CAR_01", "row": 1, "col": 1, "action": "spawn"},
                {"vehicle_id": "CAR_02", "row": 2, "col": 5, "action": "spawn"}
            ]
        }
        json_message = json.dumps(spawn_data) + "\n"
        client_socket.sendall(json_message.encode('utf-8'))
        
        # 3초간 유니티 화면에 차가 잘 생기는지 구경하며 대기합니다.
        time.sleep(3.0)

        # 2. 3초 뒤, 생성된 두 차량을 다른 좌표로 이동(Move)시키는 데이터 전송
        print("[파이썬 서버] 2단계: 차량 이동 신호 전송")
        move_data = {
            "vehicles": [
                {"vehicle_id": "CAR_01", "row": 1, "col": 3, "action": "move"},
                {"vehicle_id": "CAR_02", "row": 4, "col": 5, "action": "move"}
            ]
        }
        json_message = json.dumps(move_data) + "\n"
        client_socket.sendall(json_message.encode('utf-8'))

        # 3초간 차가 스르륵 움직이는 걸 구경합니다.
        time.sleep(3.0)

        # 3. 3초 뒤, 한 대는 그대로 두고 한 대는 퇴차(Leave)시키는 데이터 전송
        print("[파이썬 서버] 3단계: CAR_01 퇴차 신호 전송")
        leave_data = {
            "vehicles": [
                {"vehicle_id": "CAR_01", "row": 1, "col": 3, "action": "leave"}
            ]
        }
        json_message = json.dumps(leave_data) + "\n"
        client_socket.sendall(json_message.encode('utf-8'))

        # 대기 후 종료
        time.sleep(5.0)

    except Exception as e:
        print(f"[파이썬 서버] 에러: {e}")

if __name__ == "__main__":
    run_server()