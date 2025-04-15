import numpy as np
import time
import cv2
import tflite_runtime.interpreter as tflite
from cvzone.HandTrackingModule import HandDetector

class RSPTrained:
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
    text = ansToText[ans]

    # 시각적 표시
    cv2.rectangle(frame, (x1, y1), (x2, y2), colorList[ans], 2)
    cv2.putText(frame, text, (x1, y1 - 7), cv2.FONT_HERSHEY_PLAIN, 2, colorList[ans], 2)

    return text  # 인식된 결과를 반환

    # 정사각형 이미지 변환 함수
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