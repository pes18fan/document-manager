from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy.exc import IntegrityError
from typing import Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from fastapi import HTTPException
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
def save_document(filename: str, raw_text: str, avg_conf: float,
                  keywords: list[str], cluster_id: int,
                  category: str) -> dict[str, Any]:
    with Session(engine) as session:
        try:
            doc = Document(filename=filename, content_hash=make_hash(raw_text),
                           raw_text=raw_text, avg_conf=avg_conf,
                           cluster_id=cluster_id, category=category)
        except IntegrityError:
            raise DocumentExistsError(
                "Document with this content already exists.")

        session.add(doc)
        session.commit()
        session.refresh(doc)

        for word, score in keywords:
            session.add(Keyword(document_id=doc.id,
                        keyword=word, tfidf_score=score))
        session.commit()

        # return some relevant info
        return {"id": doc.id, "category": category, "keywords": keywords}


# Select and return all the documents in the Documents table.
def get_all_documents():
    with Session(engine) as session:
        return session.exec(select(Document)).all()


# Grab a single document from the Documents table.
def get_document(doc_id: int):
    with Session(engine) as session:
        return session.get(Document, doc_id)
