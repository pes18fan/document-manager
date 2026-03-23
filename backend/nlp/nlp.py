import re
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

SCRIPT_DIR = Path(__file__).resolve().parent
STOPWORDS_FILE = SCRIPT_DIR / "stopwords.txt"
MODEL_FILE = SCRIPT_DIR / "kmeans_model.pkl"
VECTORIZER_FILE = SCRIPT_DIR / "tfidf_vectorizer.pkl"
TOP_K = 15
N_CLUSTERS = 5

with open(STOPWORDS_FILE, encoding="utf-8") as f:
    STOPWORDS = f.read().splitlines()

# cluster id → human readable label, you fill these in after training
CLUSTER_LABELS = {
    0: "Uncategorized",
    1: "Uncategorized",
    2: "Uncategorized",
    3: "Uncategorized",
    4: "Uncategorized",
}


def preprocess(text: str) -> str:
    text = re.sub(r"[।॥,;:!?(){}\[\]\"'—\-/\–]", " ", text)
    text = re.sub(r"[०-९0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def train(documents: list[str]):
    """Train and save the vectorizer and KMeans model on a corpus."""
    if len(documents) < N_CLUSTERS:
        raise ValueError(f"Need at least {
                         N_CLUSTERS} documents to train, got {len(documents)}")

    processed = [preprocess(doc) for doc in documents]

    vectorizer = TfidfVectorizer(
        stop_words=STOPWORDS,
        ngram_range=(1, 2),
        token_pattern=r"(?u)[^\s]+",
        max_features=500,
        min_df=2
    )
    tfidf_matrix = vectorizer.fit_transform(processed)

    model = KMeans(n_clusters=N_CLUSTERS, random_state=42)
    model.fit(tfidf_matrix)

    joblib.dump(vectorizer, VECTORIZER_FILE)
    joblib.dump(model, MODEL_FILE)
    print("Training done, models saved.")

    # print top terms per cluster so you can fill in CLUSTER_LABELS
    terms = vectorizer.get_feature_names_out()
    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    for i in range(N_CLUSTERS):
        top = [terms[idx] for idx in order_centroids[i, :5]]
        print(f"Cluster {i}: {top}")


def extract_keywords(text: str) -> list[tuple[str, float]]:
    vectorizer = joblib.load(VECTORIZER_FILE)
    processed = preprocess(text)
    vec = vectorizer.transform([processed])
    feature_names = vectorizer.get_feature_names_out()
    row = vec.toarray()[0]
    top_indices = row.argsort()[-TOP_K:][::-1]
    return [(feature_names[i], round(row[i], 4)) for i in top_indices if row[i] > 0]


def classify(text: str) -> tuple[int, str]:
    vectorizer = joblib.load(VECTORIZER_FILE)
    model = joblib.load(MODEL_FILE)
    processed = preprocess(text)
    vec = vectorizer.transform([processed])
    cluster_id = int(model.predict(vec)[0])
    return cluster_id, CLUSTER_LABELS.get(cluster_id, "Uncategorized")
