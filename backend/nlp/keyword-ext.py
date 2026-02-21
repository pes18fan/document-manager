import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
import re

# Get absolute path to script directory
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


# CONFIG
TXT_DIR = SCRIPT_DIR / "text"  # directory containing .txt files
# file containing Nepali stopwords (one per line)
STOPWORDS_FILE = SCRIPT_DIR / "stopwords.txt"
TOP_K = 15        # keywords per document


documents = []
filenames = []


def preprocess_nepali(text):
    # Remove Nepali purnaviram (fullstop) and common punctuation
    text = re.sub(r"[।॥,;:!?(){}\[\]\"'—\-]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


for fname in sorted(TXT_DIR.glob("*.txt")):
    with open(fname, "r", encoding="utf-8") as f:
        documents.append(f.read())
        filenames.append(fname.name)

# load nepali stopwords
with open(STOPWORDS_FILE, encoding="utf-8") as f:
    nep_stopwords = f.read().splitlines()


documents = [preprocess_nepali(doc) for doc in documents]

# tf-idf vectorization
vectorizer = TfidfVectorizer(
    # min_df=2,      # appear in at least 2 documents
    # max_df=0.85,   # ignore too-common terms

    stop_words=nep_stopwords,  # use nepali stopwords
    ngram_range=(1, 2),  # unigrams + bigrams
    # match all non-whitespace sequences (including punctuation)
    token_pattern=r"(?u)[^\s]+"
)


tfidf_matrix = vectorizer.fit_transform(documents)
feature_names = vectorizer.get_feature_names_out()


# save keywords to JSON file
OUTPUT_FILE = SCRIPT_DIR / "keywords.json"
keywords_data = {}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for doc_idx, fname in enumerate(filenames):
        row = tfidf_matrix[doc_idx].toarray()[0]
        top_indices = row.argsort()[-TOP_K:][::-1]

        keywords = [(feature_names[i], round(row[i], 4))
                    for i in top_indices if row[i] > 0]

        keywords_data[fname] = keywords
    json.dump(keywords_data, f, ensure_ascii=False, indent=2)


# # save keywords to a .txt file
# OUTPUT_FILE = SCRIPT_DIR / "keywords.txt"
# with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#     for doc_idx, fname in enumerate(filenames):
#         row = tfidf_matrix[doc_idx].toarray()[0]
#         top_indices = row.argsort()[-TOP_K:][::-1]

#         keywords = [(feature_names[i], round(row[i], 4)) for i in top_indices if row[i] > 0]

#         f.write(f"{fname}\n")
#         for word, score in keywords:
#             f.write(f"  {word} → {score}\n")
#         f.write("\n")


print(f"Extracted keywords for {len(filenames)
                                } documents. Results saved to {OUTPUT_FILE}")
