import socketio
import tkinter as tk
from tkinter import messagebox
import threading
import cv2
import time
import numpy as np
import tflite_runtime.interpreter as tflite
from cvzone.HandTrackingModule import HandDetector
from PIL import Image, ImageTk

# ---------------------------- 모델 초기화 ----------------------------
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
cap = None

# ---------------------------- SocketIO ----------------------------
sio = socketio.Client()
player_name = None

# ---------------------------- Tkinter ----------------------------
root = tk.Tk()
root.title("가위 바위 보 게임")
root.geometry("400x500")

name_entry = tk.Entry(root, font=("Arial", 14))
name_entry.pack(pady=10)

status_label = tk.Label(root, text="상태: 대기 중", font=("Arial", 12))
status_label.pack(pady=5)

cam_label = tk.Label(root)
cam_label.pack(pady=10)

ready_button = tk.Button(root, text="Ready!", font=("Arial", 14))
ready_button.pack(pady=10)

def update_status(msg):
    status_label.config(text=f"상태: {msg}")

def make_square_img(img):
    ho, wo = img.shape[:2]
    aspectRatio = ho / wo
    wbg = np.ones((IMG_SIZE, IMG_SIZE, 3), np.uint8) * 255
    if aspectRatio > 1:
        k = IMG_SIZE / ho
        wk = int(wo * k)
        img = cv2.resize(img, (wk, IMG_SIZE))
        d = (IMG_SIZE - wk) // 2
        wbg[:, d:d + wk] = img
    else:
        k = IMG_SIZE / wo
        hk = int(ho * k)
        img = cv2.resize(img, (IMG_SIZE, hk))
        d = (IMG_SIZE - hk) // 2
        wbg[d:d + hk, :] = img
    return wbg

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

def show_camera():
    if cap is None:
        return
    ret, frame = cap.read()
    if ret:
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        cam_label.imgtk = imgtk
        cam_label.configure(image=imgtk)
    root.after(30, show_camera)

@sio.event
def connect():
    print("서버에 연결됨")

@sio.event
def choose(data):
    global cap
    update_status("손 인식 중...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    show_camera()
    result = None
    timeout = time.time() + 5

    while time.time() < timeout:
        ret, frame = cap.read()
        if not ret:
            continue
        result = processImage(frame)
        if result:
            break

    cap.release()
    cap = None
    cam_label.config(image='')

    if result:
        update_status(f"인식 결과: {result}")
        sio.emit('choice', {'choice': result})
    else:
        update_status("인식 실패, 기본값 전송")
        sio.emit('choice', {'choice': 'rock'})

@sio.event
def round_result(data):
    losers = data.get('loser_names', [])
    alive = data.get('alive_names', [])

    if player_name in losers:
        update_status("탈락 ㅠㅠ")
    elif player_name in alive:
        update_status("생존!")
    else:
        update_status("결과 수신")

    msg = ""
    if not losers:
        msg += "무승부입니다.\n"
    else:
        msg += "탈락자:\n" + "\n".join(f" - {name}" for name in losers)
    msg += "\n\n생존자:\n" + "\n".join(f" - {name}" for name in alive)

    messagebox.showinfo("🎮 라운드 결과", msg)

@sio.event
def game_over(data):
    winner = data.get('winner_name')
    update_status("게임 종료")
    messagebox.showinfo("🏆 게임 종료", f"최종 우승자는 {winner}입니다!")

def on_ready_click():
    global player_name
    name = name_entry.get().strip()
    if not name:
        messagebox.showwarning("이름 필요", "이름을 입력해주세요!")
        return
    player_name = name
    update_status("서버 연결 중...")
    threading.Thread(target=connect_to_server).start()

def connect_to_server():
    try:
        sio.connect('http://10.56.130.245:5000')  # 실제 서버 주소로 변경하세요
        sio.emit('join', {'name': player_name})
        sio.emit('ready')
        update_status("게임 시작 대기 중...")
    except Exception as e:
        messagebox.showerror("연결 오류", f"서버에 연결할 수 없습니다:\n{e}")

ready_button.config(command=on_ready_click)
root.mainloop()
