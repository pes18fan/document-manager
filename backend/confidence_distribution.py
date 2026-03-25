import matplotlib.pyplot as plt
import pytesseract
import cv2
import numpy as np
from PIL import Image
from pytesseract import Output
from pathlib import Path

TESSDATA_DIR = "./tessdata"
EVAL_LINE_IMAGE_DIR = "./eval_images"
EVAL_PAGE_IMAGE_DIR = "./eval_pages"


def get_avg_conf(path: str, model: str, psm: int) -> float:
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
        config=f'--psm {psm} --tessdata-dir "{TESSDATA_DIR}"',
        output_type=Output.DICT,
    )

    word_confs = [c for c in data["conf"] if c != -1]
    return float(np.mean(word_confs)) if word_confs else 0.0


def get_confs(image_dir: str, model: str, psm: int) -> list[float]:
    confs = []
    for img_path in sorted(Path(image_dir).glob("*.tif")):
        conf = get_avg_conf(str(img_path), model, psm)
        if conf > 0:
            confs.append(conf)
        print(f"{model} - {img_path.name}: {conf:.2f}%")
    return confs


def compare_confs_lineimg():
    plt.figure()
    print("Comparing confidence for lines.\n")
    base_confs = get_confs(image_dir=EVAL_LINE_IMAGE_DIR, model="nep", psm=13)
    finetuned_confs = get_confs(
        image_dir=EVAL_LINE_IMAGE_DIR, model="nep-ft-final", psm=13)

    plt.hist(base_confs, alpha=0.5, label="Base model", bins=20)
    plt.hist(finetuned_confs, alpha=0.5, label="Fine-tuned (final)", bins=20)
    plt.xlabel("Average Confidence %")
    plt.ylabel("Document count")
    plt.title("Confidence Level Comparison (Line Images)")
    plt.legend()
    plt.savefig("confidence_comparison_line.png")
    plt.close()


def compare_confs_pageimg():
    plt.figure()
    print("Comparing confidence for pages.\n")
    base_confs = get_confs(image_dir=EVAL_PAGE_IMAGE_DIR, model="nep", psm=3)
    finetuned_confs = get_confs(
        image_dir=EVAL_PAGE_IMAGE_DIR, model="nep-ft-final", psm=3)

    plt.hist(base_confs, alpha=0.5, label="Base model", bins=20)
    plt.hist(finetuned_confs, alpha=0.5, label="Fine-tuned (final)", bins=20)
    plt.xlabel("Average Confidence %")
    plt.ylabel("Document count")
    plt.title("Confidence Level Comparison (Page Images)")
    plt.legend()
    plt.savefig("confidence_comparison_page.png")
    plt.close()


def main():
    compare_confs_lineimg()
    compare_confs_pageimg()


if __name__ == "__main__":
    main()
