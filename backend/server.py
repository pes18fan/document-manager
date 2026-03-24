from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
from pytesseract import Output

import database as db
import nlp
import pytesseract
import cv2
import numpy as np
import base64
import logging
import logging.config
from datetime import datetime
from pathlib import Path
from uvicorn.config import LOGGING_CONFIG

log_config = LOGGING_CONFIG.copy()

log_config["loggers"]["app"] = {
    "handlers": ["default"],
    "level": "INFO",
    "propagate": False,
}

logging.config.dictConfig(log_config)
logger = logging.getLogger("app")

app = FastAPI()

# NOTE: this will not be needed when electron is used, just using for the
# one-page browser thingy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Path for image uploads, used to preview them in the frontend
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

TESSDATA_DIR = "./tessdata"


@app.on_event("startup")
def on_startup():
    db.init()
    logger.info("Connected to PostgreSQL DB.")


class SaveDocumentRequest(BaseModel):
    filename: str
    raw_text: str
    avg_conf: float
    image_data: str


class SaveDocumentResponse(BaseModel):
    id: int
    category: str
    keywords: list[tuple[str, float]]


class Document(BaseModel):
    id: int
    content_hash: str
    filename: str
    image_path: str
    raw_text: str
    avg_conf: float
    uploaded_at: datetime
    cluster_id: int
    category: str


@app.post("/documents")
async def save_document(req: SaveDocumentRequest) -> SaveDocumentResponse:
    keywords = nlp.extract_keywords(req.raw_text)
    cluster_id, category = nlp.classify(req.raw_text)

    # save uploaded file first
    content_hash = db.make_hash(req.raw_text)
    ext = Path(req.filename).suffix
    image_dest = UPLOAD_DIR / f"{content_hash}{ext}"

    image_bytes = base64.b64decode(req.image_data)
    with open(image_dest, "wb") as f:
        f.write(image_bytes)

    try:
        doc = db.save_document(filename=req.filename,
                               image_path=str(image_dest),
                               raw_text=req.raw_text, avg_conf=req.avg_conf,
                               keywords=keywords, cluster_id=cluster_id,
                               category=category)
        logging.info(f"Saved document {content_hash} to DB")
    except db.DocumentExistsError as e:
        raise HTTPException(status_code=409, detail=e)

    return doc


@app.get("/documents")
def get_documents() -> list[Document]:
    return db.get_all_documents()


@app.get("/documents/{doc_id}")
def get_document(doc_id: int) -> Document:
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int):

    # Also delete the image file from disk
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    image_path = Path(doc.image_path)
    if image_path.exists():
        image_path.unlink()
    
    success = db.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"ok": True}


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
    plain_text = "\n".join([" ".join(filter(None, line))
                           for line in lines.values()])

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
