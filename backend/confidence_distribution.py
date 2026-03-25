import matplotlib.pyplot as plt
import pytesseract
import cv2
import numpy as np
from PIL import Image
from pytesseract import Output
from pathlib import Path

TESSDATA_DIR = "./tessdata"
EVAL_FILES_DIR = "./eval_images"


def get_avg_conf(path: str, model: str) -> float:
    cv_img = cv2.imread(path)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    conv = cv2.cvtColor(th, cv2.COLOR_BGR2RGB)
    out_image = Image.fromarray(conv)

    # Use a PSM of 13 because the eval_images are raw lines, the same ones
    # used for training, where the PSM is also 13
    data = pytesseract.image_to_data(
        out_image,
        lang=model,
        config=f'--psm 13 --tessdata-dir "{TESSDATA_DIR}"',
        output_type=Output.DICT,
    )

    word_confs = [c for c in data["conf"] if c != -1]
    return float(np.mean(word_confs)) if word_confs else 0.0


def get_confs(model: str) -> list[float]:
    confs = []
    for img_path in sorted(Path("eval_images").glob("*.tif")):
        conf = get_avg_conf(str(img_path), model)
        if conf > 0:
            confs.append(conf)
        print(f"{model} - {img_path.name}: {conf:.2f}%")
    return confs


def main():
    base_confs = get_confs("nep")
    finetuned_confs = get_confs("nep-ft-final")

    plt.hist(base_confs, alpha=0.5, label="Base model", bins=20)
    plt.hist(finetuned_confs, alpha=0.5, label="Fine-tuned", bins=20)
    plt.xlabel("Average Confidence %")
    plt.ylabel("Document count")
    plt.legend()
    plt.savefig("confidence_comparison.png")


if __name__ == "__main__":
    main()
