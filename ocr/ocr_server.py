from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile
from PIL import Image
import cv2
import numpy as np
import pytesseract
from pytesseract import Output


# NOTE: may or may not be used
def deskew(img, angle):
    # find the skew angle
    h, w = img.shape[:2]

    src = cv2.bitwise_not(img)

    lines = cv2.HoughLinesP(src, rho=1, theta=np.pi/180,
                            threshold=100, minLineLength=w / 2, maxLineGap=20)

    disp_lines = np.zeros((h, w), dtype=np.uint8)

    angle = 0.0
    nb_lines = 0

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Draw line
            cv2.line(disp_lines, (x1, y1), (x2, y2), 255, 1)

            # Angle of the line relative to horizontal
            angle += np.atan2((y2 - y1), (x2 - x1))
            nb_lines += 1

    if nb_lines > 0:
        angle /= nb_lines  # mean angle in radians
        angle_deg = angle * 180 / np.pi
    else:
        angle_deg = 0.0

    # do the deskewing
    points = np.column_stack(np.where(img > 0))
    points = points[:, ::-1].astype(np.float32)
    rect = cv2.minAreaRect(points)
    cx, cy = rect[0]

    rot_mat = cv2.getRotationMatrix2D((cx, cy), angle_deg, 1)
    final = cv2.warpAffine(
        img, rot_mat, (img.shape[1], img.shape[0]), flags=cv2.INTER_CUBIC)

    return final


app = FastAPI()

# NOTE: this will not be needed when electron is needed, just using for the
# one-page browser thingy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ocr")
async def ocr(file: UploadFile):
    img_bytes = await file.read()

    # NOTE: the opencv logic may not be needed, thing is working well enough
    # with tesseract's built-in preprocessing
    cv_img = cv2.imdecode(
        np.frombuffer(img_bytes, np.uint8),
        cv2.IMREAD_COLOR
    )
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray)
    th = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 10
    )
    conv = cv2.cvtColor(th, cv2.COLOR_BGR2RGB)
    out_image = Image.fromarray(conv)

    data = pytesseract.image_to_data(
        out_image, lang="nep+eng", output_type=Output.DICT)

    word_confs = [c for c in data['conf'] if c != -1]
    avg_conf = float(np.mean(word_confs)) if word_confs else 0.0

    # reconstruct plain text (optional)
    lines = {}
    for i, line_num in enumerate(data['line_num']):
        if line_num not in lines:
            lines[line_num] = []
        lines[line_num].append(data['text'][i])
    plain_text = "\n".join([" ".join(filter(None, l)) for l in lines.values()])

    return {
        "text": plain_text,
        "avg_conf": avg_conf,
        "words": [
            {
                "text": data["text"][i],
                "conf": int(data["conf"][i]),
                "bbox": [data["left"][i], data["top"][i], data["width"][i], data["height"][i]]
            }
            for i in range(len(data["text"])) if data["text"][i].strip() != ""
        ]
    }
