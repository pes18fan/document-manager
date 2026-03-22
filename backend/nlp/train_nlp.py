# train_nlp.py
from nlp import train
from pathlib import Path

texts = []
for f in Path("nlp_text").glob("*.txt"):
    texts.append(f.read_text(encoding="utf-8"))

train(texts)
