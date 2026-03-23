from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from PIL import Image
from pytesseract import Output

import database as db
import nlp
import pytesseract
import cv2
import numpy as np

app = FastAPI()

# NOTE: this will not be needed when electron is used, just using for the
# one-page browser thingy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


TESSDATA_DIR = "./tessdata"


@app.on_event("startup")
def on_startup():
    db.init()
    print("log: Connected to PostgreSQL DB")


class SaveDocumentRequest(BaseModel):
    filename: str
    raw_text: str
    avg_conf: float


class SaveDocumentResponse(BaseModel):
    id: int
    category: str
    keywords: list[tuple[str, float]]


@app.post("/documents")
async def save_document(req: SaveDocumentRequest) -> SaveDocumentResponse:
    keywords = nlp.extract_keywords(req.raw_text)
    cluster_id, category = nlp.classify(req.raw_text)

    try:
        doc = db.save_document(filename=req.filename, raw_text=req.raw_text,
                               avg_conf=req.avg_conf, keywords=keywords,
                               cluster_id=cluster_id, category=category)
    except db.DocumentExistsError as e:
        raise HTTPException(status_code=409, detail=e)

    return doc


@app.get("/documents")
def get_documents():
    return db.get_all_documents()


@app.get("/documents/{doc_id}")
def get_document(doc_id: int):
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


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
        "filename": file.filename,
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
