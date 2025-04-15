import socketio
import numpy as np
import time
import cv2
import tflite_runtime.interpreter as tflite
from cvzone.HandTrackingModule import HandDetector

# ✨ SocketIO 클라이언트 정의
sio = socketio.Client()

@sio.event
def connect():
    print("✅ 서버에 연결되었습니다.")
    name = input("Enter your name: ")
    sio.emit('join', {'name': name})

@sio.event
def choose(data):
    print("✋ 손 모양을 카메라에 보여주세요! 최대 5초 동안 인식 시도 중...")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    result = None
    timeout = time.time() + 5

    while time.time() < timeout:
        ret, frame = cap.read()
        if not ret:
            continue

        result = processImage(frame)
        cv2.imshow("cam", frame)

        if result:
            print(f"✅ 인식된 손 모양: {result}")
            break

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if result:
        sio.emit('choice', {'choice': result})
    else:
        print("⚠️ 손 인식 실패! 기본값 'rock' 전송.")
        sio.emit('choice', {'choice': 'rock'})

@sio.event
def round_result(data):
    print("\n🎮 라운드 결과")
    losers = data.get('loser_names', [])
    alive = data.get('alive_names', [])

    if not losers:
        print("무승부! 아무도 탈락하지 않았습니다.")
    else:
        print("❌ 탈락한 플레이어:")
        for name in losers:
            print(f" - {name}")

    print("🟢 생존자:")
    for name in alive:
        print(f" - {name}")

def start():
    sio.connect('http://127.0.0.1:5000')  # 👉 서버 주소 수정
    while True:
        cmd = input("Type 'ready' to join round: ")
        if cmd.strip().lower() == 'ready':
            sio.emit('ready')

if __name__ == '__main__':
    start()
