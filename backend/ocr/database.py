from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    raw_text: str
    avg_conf: float
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    cluster_id: Optional[int] = None
    category: Optional[str] = None


class Keyword(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    keyword: str
    tfidf_score: float


def init():
    SQLModel.metadata.create_all(engine)


def save_document(filename, raw_text, avg_conf, keywords, cluster_id, category):
    with Session(engine) as session:
        doc = Document(filename=filename, raw_text=raw_text,
                       avg_conf=avg_conf, cluster_id=cluster_id, category=category)
        session.add(doc)
        session.commit()
        session.refresh(doc)

        for word, score in keywords:
            session.add(Keyword(document_id=doc.id,
                        keyword=word, tfidf_score=score))
        session.commit()

        # return some relevant info
        return {"id": doc.id, "category": category, "keywords": keywords}


def get_all_documents():
    with Session(engine) as session:
        return session.exec(select(Document)).all()


def get_document(doc_id: int):
    with Session(engine) as session:
        return session.get(Document, doc_id)
