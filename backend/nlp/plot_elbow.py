import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from nlp import preprocess, STOPWORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path


def plot_elbow(tfidf_matrix, max_k=10):
    inertias = []
    k_values = range(2, max_k + 1)

    for k in k_values:
        model = KMeans(n_clusters=k, random_state=42)
        model.fit(tfidf_matrix)
        inertias.append(model.inertia_)

    plt.plot(k_values, inertias, "bo-")
    plt.xlabel("k")
    plt.ylabel("Inertia")
    plt.title("Elbow Method")
    plt.xticks(k_values)
    plt.savefig("elbow.png")
    plt.show()


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

plot_elbow(tfidf_matrix)
