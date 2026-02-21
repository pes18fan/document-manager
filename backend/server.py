from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from PIL import Image
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import re

app = FastAPI()

# NOTE: this will not be needed when electron is used, just using for the
# one-page browser thingy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


TESSDATA_DIR = "./ocr/tessdata"


@app.post("/ocr")
async def ocr(file: UploadFile):
    img_bytes = await file.read()

    # NOTE: the opencv logic may not be needed, thing is working well enough
    # with tesseract's built-in preprocessing
    cv_img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    conv = cv2.cvtColor(th, cv2.COLOR_BGR2RGB)
    out_image = Image.fromarray(conv)

    data = pytesseract.image_to_data(
        out_image,
        lang="nep-ft",
        config=f'--tessdata-dir "{TESSDATA_DIR}"',
        output_type=Output.DICT,
    )

    word_confs = [c for c in data["conf"] if c != -1]
    avg_conf = float(np.mean(word_confs)) if word_confs else 0.0

    # reconstruct plain text (optional)
    lines = {}
    for i, line_num in enumerate(data["line_num"]):
        if line_num not in lines:
            lines[line_num] = []
        lines[line_num].append(data["text"][i])
    plain_text = "\n".join([" ".join(filter(None, l)) for l in lines.values()])

    return {
        "text": plain_text,
        "avg_conf": avg_conf,
        "words": [
            {
                "text": data["text"][i],
                "conf": int(data["conf"][i]),
                "bbox": [
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                ],
            }
            for i in range(len(data["text"]))
            if data["text"][i].strip() != ""
        ],
    }


STOPWORDS_FILE = Path(__file__).resolve().parent / "nlp" / "stopwords.txt"
CORPUS = []
STOPWORDS = []

with open(STOPWORDS_FILE, encoding="utf-8") as f:
    STOPWORDS = f.read().splitlines()

TOP_K = 15  # keywords per document


class KeywordsRequest(BaseModel):
    text: str


def preprocess_nepali(text: str):
    # Remove Nepali purnaviram (fullstop) and common punctuation
    text = re.sub(r"[।॥,;:!?(){}\[\]\"'—\-]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


@app.post("/keywords")
def keywords(req: KeywordsRequest):
    CORPUS.append(preprocess_nepali(req.text))

    # tf-idf vectorization
    vectorizer = TfidfVectorizer(
        # min_df=2,      # appear in at least 2 documents
        # max_df=0.85,   # ignore too-common terms
        stop_words=STOPWORDS,  # use nepali stopwords
        ngram_range=(1, 2),  # unigrams + bigrams
        # match all non-whitespace sequences (including punctuation)
        token_pattern=r"(?u)[^\s]+",
    )

    tfidf_matrix = vectorizer.fit_transform(CORPUS)
    feature_names = vectorizer.get_feature_names_out()

    row = tfidf_matrix[len(CORPUS) - 1].toarray()[0]
    top_indices = row.argsort()[-TOP_K:][::-1]

    keywords = [
        {"word": feature_names[i], "count": round(row[i], 4)}
        for i in top_indices
        if row[i] > 0
    ]

    return {"keywords": keywords}
