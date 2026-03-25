from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
from nlp import preprocess, STOPWORDS, MODEL_FILE
from pathlib import Path
import joblib

model = joblib.load(MODEL_FILE)
texts = [preprocess(f.read_text(encoding="utf-8"))
         for f in Path("nlp_text").glob("*.txt")]
vectorizer = TfidfVectorizer(
    stop_words=STOPWORDS,
    ngram_range=(1, 2),
    token_pattern=r"(?u)[^\s]+",
    max_features=500,
    min_df=2
)
tfidf_matrix = vectorizer.fit_transform(texts)

score = silhouette_score(tfidf_matrix, model.labels_, metric='cosine')
print(f"Silhouette Score (cosine): {score:.4f}")
