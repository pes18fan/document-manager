import cv2
import numpy as np
import pytesseract


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


path = "printed-ocr-test.jpg"
img = cv2.imread(path)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.fastNlMeansDenoising(gray)
th = cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    31, 10
)

# # NOTE: needed for the deskewing, might work around this later
# img = cv2.bitwise_not(img)
#
# rot = deskew(img, 0)
cv2.imwrite("printed-ocr-test-fixed.jpg", th)

out = pytesseract.image_to_string(
    "printed-ocr-test.jpg", lang="nep")

with open("out.txt", "w") as f:
    f.write(out)
