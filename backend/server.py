from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image
from pytesseract import Output
from pdf2image import convert_from_bytes

import database as db
import s3_storage as s3
import nlp
import pytesseract
import cv2
import numpy as np
import base64
import re
import logging
import logging.config
import magic
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

DOCUMENT_PREVIEW_BUCKET = "document_previews"

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


class SaveDocumentPreviewRequest(BaseModel):
    path: str


@app.post("/documents")
async def save_document(req: SaveDocumentRequest) -> SaveDocumentResponse:
    keywords = nlp.extract_keywords(req.raw_text)
    cluster_id, category = nlp.classify(req.raw_text)

    # Save uploaded file to local cache
    content_hash = db.make_hash(req.raw_text)
    ext = Path(req.filename).suffix
    image_dest = UPLOAD_DIR / f"{content_hash}{ext}"

    image_bytes = base64.b64decode(req.image_data)
    with open(image_dest, "wb") as f:
        f.write(image_bytes)

    # Upload to S3 (primary storage)
    s3_success = s3.upload_file(DOCUMENT_PREVIEW_BUCKET, str(image_dest))
    if not s3_success:
        logger.warning(
            f"Failed to upload {
                content_hash} to S3, continuing with local storage only"
        )

    try:
        doc = db.save_document(
            filename=req.filename,
            image_path=str(image_dest),
            raw_text=req.raw_text,
            avg_conf=req.avg_conf,
            keywords=keywords,
            cluster_id=cluster_id,
            category=category,
        )
        logger.info(f"Saved document {content_hash} to DB and S3")
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


@app.get("/documents/{doc_id}/keywords")
def get_document_keywords(doc_id: int) -> list[db.Keyword]:
    keywords: list[db.Keyword] = db.get_document_keywords(doc_id)
    if not keywords:
        raise HTTPException(status_code=404, detail="Document not found")

    return keywords


class UpdateDocumentTextRequest(BaseModel):
    raw_text: str


class UpdateDocumentTextResponse(BaseModel):
    id: int
    category: str
    keywords: list[tuple[str, float]]


@app.put("/documents/{doc_id}/text")
async def update_document_text(
    doc_id: int, req: UpdateDocumentTextRequest
) -> UpdateDocumentTextResponse:
    """
    Update the raw text of a document and re-run NLP processing.
    This will:
    1. Update the document's raw_text and content_hash
    2. Delete all old keywords
    3. Extract new keywords using TF-IDF
    4. Re-classify the document into a category
    5. Save new keywords to the database
    """
    # Check if document exists
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Re-run NLP processing on the new text
    keywords = nlp.extract_keywords(req.raw_text)
    cluster_id, category = nlp.classify(req.raw_text)

    # Update document in database with new text and NLP results
    result = db.update_document_text(
        doc_id=doc_id,
        new_text=req.raw_text,
        keywords=keywords,
        cluster_id=cluster_id,
        category=category,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    logger.info(
        f"Updated document {doc_id}: new category={
            category}, {len(keywords)} keywords"
    )

    return result


@app.get("/documents/{doc_id}/preview")
def get_document_preview(doc_id: int):
    """
    Returns the document preview image using cache-aside pattern.
    Checks local cache first, downloads from S3 if not found.
    """
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Use the filename from image_path (e.g., "abc123.jpg" from "uploads/abc123.jpg")
    image_filename = Path(doc.image_path).name
    local_path = UPLOAD_DIR / image_filename

    # Cache hit: serve from local storage
    if local_path.exists():
        logger.info(f"Cache hit: serving {image_filename} from local storage")
        return FileResponse(local_path)

    # Cache miss: download from S3 to local cache
    logger.info(f"Cache miss: downloading {image_filename} from S3")
    s3_success = s3.download_file(
        DOCUMENT_PREVIEW_BUCKET, image_filename, str(local_path)
    )

    if not s3_success or not local_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Preview image not found in local cache or S3"
        )

    return FileResponse(local_path)


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    """
    Delete document from database, local cache, and S3.
    """
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from local cache
    image_path = Path(doc.image_path)
    if image_path.exists():
        image_path.unlink()
        logger.info(f"Deleted {image_path.name} from local cache")

    # Delete from S3
    image_filename = image_path.name
    s3_success = s3.delete_file(DOCUMENT_PREVIEW_BUCKET, image_filename)
    if not s3_success:
        logger.warning(f"Failed to delete {image_filename} from S3")

    # Delete from database
    success = db.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"ok": True}


def pdf_to_image(pdf_bytes: bytes) -> Image.Image:
    """
    Convert a single-page PDF to a PIL Image.
    Raises an HTTPException if the PDF does not have exactly one page.
    """
    try:
        pages = convert_from_bytes(pdf_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to process PDF: {str(e)}")

    if len(pages) != 1:
        raise HTTPException(
            status_code=400,
            detail=f"PDF must have exactly 1 page, but has {
                len(pages)} pages.",
        )

    return pages[0]


def postprocess_text(text: str) -> str:
    # normalize whitespace
    text = re.sub(r" +", " ", text)
    # normalize newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # remove lines that are only punctuation or symbols with no Devanagari
    lines = text.split("\n")
    lines = [line for line in lines if re.search(r"[\u0900-\u097F]", line)]
    # strip leading/trailing whitespace from each line
    lines = [line.strip() for line in lines]
    return "\n".join(lines)


@app.post("/ocr")
async def ocr(file: UploadFile):
    img_bytes = await file.read()

    # Check if file is a PDF and convert it to an image
    if file.content_type == "application/pdf" or file.filename.endswith(".pdf"):
        img = pdf_to_image(img_bytes)
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    else:
        # Process as a regular image
        cv_img = cv2.imdecode(np.frombuffer(
            img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if cv_img is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file. Please upload a valid image or single-page PDF.",
            )

    # image preprocessing
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    conv = cv2.cvtColor(th, cv2.COLOR_BGR2RGB)
    out_image = Image.fromarray(conv)

    data = pytesseract.image_to_data(
        out_image,
        lang="nep-ft-final",
        config=f'--tessdata-dir "{TESSDATA_DIR}"',
        output_type=Output.DICT,
    )

    word_confs = [c for c in data["conf"] if c != -1]
    avg_conf = float(np.mean(word_confs)) if word_confs else 0.0

    # reconstruct plain text
    lines = {}
    for i, line_num in enumerate(data["line_num"]):
        if line_num not in lines:
            lines[line_num] = []
        lines[line_num].append(data["text"][i])
    plain_text = "\n".join([" ".join(filter(None, line))
                           for line in lines.values()])
    plain_text = postprocess_text(plain_text)

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
