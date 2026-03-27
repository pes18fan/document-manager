from sqlmodel import SQLModel, Field, Session, create_engine, select, delete
from sqlalchemy.exc import IntegrityError
from typing import Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import os
import hashlib

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


# The document table: saves an ID, filename, the raw OCR-d text, average
# confidence level of the OCR transcription, upload date, ID of the K-Means
# cluster the document is saved to, and the category (cluster) name.
class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # SHA256 hash of text, used for deduplication
    content_hash: str = Field(unique=True)
    filename: str
    image_path: str  # path to the image, used to preview in frontend
    raw_text: str
    avg_conf: float
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    cluster_id: Optional[int] = None
    category: Optional[str] = None


class DocumentExistsError(Exception):
    pass


# A keyword present in the document corpus. Contains a keyword ID, ID to its
# corresponding document, the keyword itself, and its TF-IDF score.
class Keyword(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    keyword: str
    tfidf_score: float


# Start up the database.
def init():
    # Uncomment the below line if the table structure is not final yet.
    # this line will drop and recreate all the tables on restarting the server;
    # all the data on the tables will be erased but this won't matter if all
    # the data is just for testing.
    # SQLModel.metadata.drop_all(engine)

    SQLModel.metadata.create_all(engine)


# Create a SHA256 hash of a string of text.
def make_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Save a document to the database. This also saves its corresponding keywords
# to the Keyword table. It returns a dictionary containing the database ID of
# the saved document, the name of the category (cluster) it was saved to, and
# a list containing the keywords it contains.
def save_document(
    filename: str,
    image_path: str,
    raw_text: str,
    avg_conf: float,
    keywords: list[str],
    cluster_id: int,
    category: str,
) -> dict[str, Any]:
    with Session(engine) as session:
        try:
            doc = Document(
                filename=filename,
                image_path=image_path,
                content_hash=make_hash(raw_text),
                raw_text=raw_text,
                avg_conf=avg_conf,
                cluster_id=cluster_id,
                category=category,
            )
        except IntegrityError:
            raise DocumentExistsError("Document with this content already exists.")

        session.add(doc)
        session.commit()
        session.refresh(doc)

        for word, score in keywords:
            session.add(Keyword(document_id=doc.id, keyword=word, tfidf_score=score))
        session.commit()

        # return some relevant info
        return {"id": doc.id, "category": category, "keywords": keywords}


# Delete a document from the Documents table.
def delete_document(doc_id: int) -> bool:
    with Session(engine) as session:
        doc = session.get(Document, doc_id)
        if not doc:
            return False

        session.exec(delete(Keyword).where(Keyword.document_id == doc_id))
        session.flush()  # ensure keywords are deleted before document
        session.delete(doc)
        session.commit()
        return True


# Select and return all the documents in the Documents table.
def get_all_documents():
    with Session(engine) as session:
        return session.exec(select(Document)).all()


# Grab a single document from the Documents table.
def get_document(doc_id: int):
    with Session(engine) as session:
        return session.get(Document, doc_id)


# Get all keywords for a specific document.
def get_document_keywords(doc_id: int) -> list[Keyword]:
    with Session(engine) as session:
        keywords = session.exec(
            select(Keyword).where(Keyword.document_id == doc_id)
        ).all()
        return list(keywords)


# Update a document's raw text and re-process NLP. This will:
# 1. Update the raw_text and content_hash
# 2. Delete all old keywords
# 3. Save new keywords
# 4. Update category and cluster_id
def update_document_text(
    doc_id: int,
    new_text: str,
    keywords: list[tuple[str, float]],
    cluster_id: int,
    category: str,
) -> dict[str, Any]:
    with Session(engine) as session:
        doc = session.get(Document, doc_id)
        if not doc:
            return None

        # Delete old keywords
        session.exec(delete(Keyword).where(Keyword.document_id == doc_id))
        session.flush()

        # Update document with new text and NLP results
        doc.raw_text = new_text
        doc.content_hash = make_hash(new_text)
        doc.cluster_id = cluster_id
        doc.category = category

        session.add(doc)
        session.commit()

        # Add new keywords
        for word, score in keywords:
            session.add(Keyword(document_id=doc.id, keyword=word, tfidf_score=score))
        session.commit()

        return {"id": doc.id, "category": category, "keywords": keywords}
