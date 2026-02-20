from PIL import Image
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from pprint import pprint


def ocr(file: str):
    # NOTE: the opencv logic may not be needed, thing is working well enough
    # with tesseract's built-in preprocessing

    # converting from a PIL image to opencv image, not needed rn
    # cv_img = cv2.imdecode(
    #     np.frombuffer(img_bytes, np.uint8),
    #     cv2.IMREAD_COLOR
    # )
    cv_img = cv2.imread(file)
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


def main():
    data = ocr("printed-ocr-test-2.jpg")
    print("text:\n")
    print(f"\t{data["text"]}")
    print(f"confidence: {data["avg_conf"]}")


if __name__ == "__main__":
    main()
