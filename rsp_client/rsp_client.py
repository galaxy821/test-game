# ✨ 필요한 모듈 불러오기
import socketio
import numpy as np
import time
import cv2
import tflite_runtime.interpreter as tflite
from cvzone.HandTrackingModule import HandDetector

# ✨ 모델과 손 인식기 초기화
modelPath = 'RPS_PreTrained_DenseNet_Augmentation.tflite'
interpreter = tflite.Interpreter(model_path=modelPath)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_dtype = input_details[0]['dtype']
IMG_SIZE = 64
offset = 30
ansToText = {0: 'scissors', 1: 'rock', 2: 'paper'}
colorList = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
hd = HandDetector(maxHands=1)

# ✨ 정사각형 이미지 변환 함수
def make_square_img(img):
    ho, wo = img.shape[0], img.shape[1]
    aspectRatio = ho / wo
    wbg = np.ones((IMG_SIZE, IMG_SIZE, 3), np.uint8) * 255
    if aspectRatio > 1:
        k = IMG_SIZE / ho
        wk = int(wo * k)
        img = cv2.resize(img, (wk, IMG_SIZE))
        img_h, img_w = img.shape[:2]
        d = (IMG_SIZE - img_w) // 2
        wbg[:img_h, d:img_w + d] = img
    else:
        k = IMG_SIZE / wo
        hk = int(ho * k)
        img = cv2.resize(img, (IMG_SIZE, hk))
        img_h, img_w = img.shape[:2]
        d = (IMG_SIZE - img_h) // 2
        wbg[d:img_h + d, :img_w] = img
    return wbg

# ✨ 손 모양 인식 함수
def processImage(frame):
    hands, _ = hd.findHands(frame, draw=False)
    if not hands:
        return None

    x, y, w, h = hands[0]['bbox']
    if x < offset or y < offset or x + w + offset > 640 or y + h > 480:
        return None

    x1, y1 = x - offset, y - offset
    x2, y2 = x + w + offset, y + h
    img = frame[y1:y2, x1:x2]
    img = make_square_img(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = np.expand_dims(img, 0)

    interpreter.set_tensor(input_details[0]['index'], img.astype(input_dtype))
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])[0]
    ans = np.argmax(output_data)
    return ansToText[ans]

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
