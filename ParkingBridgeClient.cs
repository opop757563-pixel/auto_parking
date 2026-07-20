using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class ParkingBridgeClient : MonoBehaviour
{
    [Header("통신 설정")]
    [SerializeField] private int port = 9000; // 파이썬이 보낼 포트 (필요시 수정)

    private UdpClient udpClient;
    private Thread receiveThread;
    private bool isRunning = true;

    // 메인 스레드에서 안전하게 데이터를 처리하기 위한 메시지 큐
    private Queue<string> messageQueue = new Queue<string>();
    private readonly object queueLock = new object();

    private void Start()
    {
        try
        {
            udpClient = new UdpClient(port);
            receiveThread = new Thread(new ThreadStart(ReceiveData));
            receiveThread.IsBackground = true;
            receiveThread.Start();
            Debug.Log($"🛰️ ParkingBridgeClient 수신 시작 (Port: {port})");
        }
        catch (Exception e)
        {
            Debug.LogError($"❌ 소켓 초기화 실패: {e.Message}");
        }
    }

    // 백그라운드 스레드에서 파이썬의 신호를 실시간으로 무한 대기
    private void ReceiveData()
    {
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
        while (isRunning)
        {
            try
            {
                byte[] data = udpClient.Receive(ref anyIP);
                string text = Encoding.UTF8.GetString(data);
                
                // 메인 스레드로 넘겨주기 위해 큐에 담기
                lock (queueLock)
                {
                    messageQueue.Enqueue(text);
                }
            }
            catch (Exception)
            {
                // 소켓이 닫힐 때 발생하는 예외 무시
            }
        }
    }

    private void Update()
    {
        // 유니티 메인 스레드에서 안전하게 데이터를 꺼내 처리
        lock (queueLock)
        {
            while (messageQueue.Count > 0)
            {
                string msg = messageQueue.Dequeue();
                ParseAndProcessMessage(msg);
            }
        }
    }

    /// <summary>
    /// 파이썬에서 온 문자열 패킷을 쪼개어 ParkingGridManager에게 전달하는 핵심 함수.
    ///
    /// 프로토콜 (parking_manager.py 와 반드시 일치해야 함):
    ///   "SPAWN:{id}:{plate}:{r},{c};{r},{c};..."       - 신규 생성 (번호판 포함)
    ///   "EXIT_START:{id}:{r},{c};{r},{c};..."          - 기존 차량 경로 갱신 (번호판 없음)
    ///   "REMOVE:{id}"                                  - 차량 제거
    /// </summary>
    private void ParseAndProcessMessage(string message)
    {
        if (string.IsNullOrEmpty(message)) return;

        string[] tokens = message.Split(':');
        if (tokens.Length < 2) return;

        string action = tokens[0].Trim();
        string carId = tokens[1].Trim();

        // 1. 차량 소멸 신호 처리
        if (action == "REMOVE")
        {
            ParkingGridManager.Instance.RemoveVehicle(carId);
            return;
        }

        // 2. 차량 생성(SPAWN) - id, 번호판, 경로 3개 필드
        if (action == "SPAWN" && tokens.Length >= 4)
        {
            string plate = tokens[2].Trim();
            string pathString = tokens[3];

            List<Vector3> worldPath = ParsePathString(pathString);
            ParkingGridManager.Instance.UpdateVehiclePath(carId, plate, worldPath);
            return;
        }

        // 3. 출차 시작(EXIT_START) - id, 경로 2개 필드 (번호판 없음, 기존 차량이라 필요 없음)
        if (action == "EXIT_START" && tokens.Length >= 3)
        {
            string pathString = tokens[2];

            List<Vector3> worldPath = ParsePathString(pathString);
            ParkingGridManager.Instance.UpdateVehiclePath(carId, null, worldPath);
            return;
        }
    }

    private List<Vector3> ParsePathString(string pathString)
    {
        string[] nodes = pathString.Split(';');
        List<Vector3> worldPath = new List<Vector3>();

        foreach (string node in nodes)
        {
            string[] coords = node.Split(',');
            if (coords.Length == 2)
            {
                if (int.TryParse(coords[0], out int r) && int.TryParse(coords[1], out int c))
                {
                    // 매니저의 변환 공식을 거쳐 3D 월드 좌표로 변환
                    Vector3 worldPos = ParkingGridManager.Instance.GridToWorldPosition(r, c);
                    worldPath.Add(worldPos);
                }
            }
        }

        return worldPath;
    }

    private void OnApplicationQuit()
    {
        isRunning = false;
        if (udpClient != null)
        {
            udpClient.Close();
        }
        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Abort();
        }
    }
}
