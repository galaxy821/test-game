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
