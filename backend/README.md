# Backend

To test it, install the packages first (use uv)

```bash
uv sync
```

Run the server using uvicorn.

```bash
uv run uvicorn server:app --host 127.0.0.1 --port 8000
```

This will open up a HTTP server where you can make requests to the `/ocr`
endpoint with a file parameter to get the OCR result of it out.

This endpoint can be tested using the aftermentioned client, but for a quick check
you can run this:

```bash
curl -X POST "http://127.0.0.1:8000/ocr" \
     -F "file=@filename.jpg" | jq -r ".text" > out.txt
```

Replace `filename.jpg` with the file you want to test with.

Note that you'll need `curl` and `jq` installed to run this command.

Additionally, the backend also provides the `/documents` endpoint which can
take one of two requests:

- POST, with the following request body structure:

  ```typescript
  interface SaveResult {
      filename: string;
      raw_text: string;
      avg_conf: number;
  }
  ```

  This will save the document to the PostgreSQL database and send back a
  result with this interface:

  ```typescript
  interface SaveResult {
      id: number;
      category: string;
      keywords: [string, number][];
  }
  ```
- GET, to get all documents in the database.

Additionally, there is a dynamic `/documents/{doc_id}` endpoint to grab a
document with the database ID `doc_id`.

## How the OCR works

The OCR is powered by Tesseract 5, using specifically the LSTM-based engine that
was introduced in version 4.

The overall pipeline, based on the 2007 paper by Ray Smith and adjusted to
account for the LSTM engine introduced much later, goes as follows.

### 1. Input & Setup

An image is fed into the engine. The assumption made by Tesseract is that the
received image is binary (i.e. black and white), however Tesseract does perform
some preprocessing on its own as well.

### 2. Connected Component Analysis

The engine finds and stores the outlines of all shapes in the images. Based on
how they nest inside each other, Tesseract is also capable of detecting
white-on-black text instead of the usual black-on-white.

### 3. Line and Word Finding

This consists of multiple steps.

- Blob filtering, which removes any noise, drop-caps (i.e. enlarged initial
    capital letter used decoratively to start sections) and punctuation, by 
    referencing median character height.
- Line detection, which sorts these blobs by x-coordinate and assigns them
    to sloping text lines, hence it is also capable of handling somewhat skewed
    images.
- Baseline fitting, makes use of a quadratic spline to handle baselines that
    are curved, which is not uncommon in scans.
- Word segmentation, self-explanatory. Works differently for monospace and
    proportional fonts.

### 4. Recognition

In the system described by the 2007 paper, Tesseract utilized a two-pass
recognizer that worked as such:

- First pass: Attempt made at recognizing every word, successful results fed into
    an adaptive classifier as training data.
- Second pass: Goes back over data that was poorly recognized and attempts to
    re-recognize using the classifier.

Afterward, for text that is especially hard to read, Tesseract performed some
extra methods:

- The blobs with worst confidence were chopped off at concave points to see
    if the confidence becomes any better.
- If the chops do not improve on the confidence of the word, it is given to the
    associator. The associator uses an A* search to find any possible high
    confidence combinations of the broken characters.

Afterward, the small extent of language processing capability present in
Tesseract is used to pick the best word candidate from categories like dictionary
words, numbers, et cetera based on which has the lowest distance from the
predefined candidates.

Finally, some output text is provided.

However, the newer version of Tesseract used by us uses a different method.

Tesseract 4 and 5 use a type of recurrent neural network known as an LSTM (Long
Short-Term Memory) for its OCR engine.

#### LSTMs

A recurrent neural network (RNN) is a type of neural network designed to
handle sequential data, where the data at the next step might be influenced
by data from the previous step. This is achieved by providing not just the
current input to the network, but also a hidden state carried forward from the
previous step.

The problem with a traditional RNN however, is that long-term dependencies are 
overwritten very quickly and thus get forgotten by the time you're far away.

An LSTM is a type of neural network that solves this problem. It provides a 
solution to the vanishing gradient problem, which is the underlying reason
for RNNs forgetting long-term dependencies; by adding an extra "cell state"
which, unlike the hidden state, is not entirely overwritten at every state.

In the context of OCR, this means that the LSTM can look at an ambiguous line
of text and resolve it using context from the whole line, even if the affecting
context is far away.

The potential of LSTMs is reflected in the results given by the LSTM recognizer;
it provides significantly higher level of accuracy on document images. However,
the trade-off is that the required compute power and training data is also much
higher.

However, creating the training data for the LSTM-based recognizer is far
easier, since it simply requires line images and corresponding transcriptions.
In contrast, old versions required complex box files containg information on
the coordinates for every single character, which is especially difficult to
find for a abugida-based script like Devanagari that does not have dedicated
characters for every sound, and instead has "incomplete" diacritics for those
sounds, which are more difficult to classify via a box file.

#### In the context of Tesseract

In Tesseract 5, for recognition, the input is processed line-by-line, unlike the
old recognizer which processed individual characters. This eliminates a lot of
the character recognition work, which is performed by the LSTM implicitly while 
reading the entire line at once.

## How the NLP section works

The NLP section has two main parts: a keyword extractor which finds and extracts
words that have high importance in the corpus, and a classifier, which clusters
similar documents together.

### Keyword Extractor

It is based on TF-IDF (Term Frequency-Inverse Document Frequency).

TF-IDF is an algorithm that is used to extract features from text. It is a
Bag-of-Words like algorithm, where you compute a vectorized feature for each
document in a corpus of documents.

It is called Bag-of-Words like because the order of the words in the sentence 
does not matter for this algorithm. This is one of the disadvantages of this
algorithm, as the order of words can make a huge difference in their importance.
However, this algorithm fits well with our current workflow as well as with the
classifier which will be discussed in a bit.

Given $n$ documents in a corpus, the algorithm will compute $n$ vectors, one for
each, where each vector has numerical values corresponding to words found across
the corpus.

#### TF

The first part of this algorithm calculates the TF (Term Frequency) for each
word found in the document, calculated by this formula:

$$
tf(t, d) = \frac{f_{t,d}}{\sum_{t' \in d} f_{t', d}}
$$

It calculates the ratio of the number of occurences of a certain term $t$ in a
document $d$ divided by the total number of terms in $d$.

For each document, this TF value is be calculated for every term in that
document as well as for terms that are not in that document but are in the
corpus. These values are combined to form a vector. Doing this for every
document in the corpus, we get the $n$ vectors corresponding to each.

The role of the TF part is simply to find out which terms might be of importance
based on how often they appear.

#### IDF

The second part of the algorithm deals with IDF (Inverse Document Frequency),
calculated by this formula:

$$
idf(t, D) = \log \frac{N}{|\left\\{d \in D : t \in d\right\\}|}
$$

It calculates the logarithm of the ratio of the number of documents divided by
the number of documents in the corpus $D$ that contain the term $t$. The
logarithm of the ratio is used rather than the ratio itself, because the ratio
can explode if there is a large number of documents or if very few documents have
the term $t$. Any logarithm can be used; in the case of `scikit-learn` which
our project uses, the natural log $\ln$ is used.

Similarly as with the TF, the IDF is used to calculate individual values for $n$ 
vectors, each vector corresponding to a document.

The role of the IDF part is somewhat opposite of TF. For terms that are
very common, the IDF value is quite low; for example a word appearing in every
document actually gets an IDF value of zero. On the other hand, less frequent
words are provided some more emphasis.

After the TF and IDF vectors are computed separately, they are multiplied
together to form the final TF-IDF vectors. Each document TF vector multiplies
with its corresponding IDF vector, and the multiplication method is dot product.

#### Stopwords

There exist many different words that are often present a lot in documents,
but do not carry any useful semantic meaning. For example, in English, these
include articles like "the, a, an", common verbs, conjunctions, et cetera.

The IDF section in the TF-IDF algorithm does help in minimizing such words
to a certain extent, but it is better if they are not there at all. Therefore,
to stop them from polluting the keyword list, we set them as stopwords.

A stopword is a feature that should be stripped from the text before passing
it over to the feature extractor. In our case, the `TfidfVectorizer` provides
a `stop_words` parameter to add a list of such stopwords. We prepared a list
of common semantically meaningless or not highly meaningful features for Nepali
in the file `stopwords.txt`, which we are using as the stopword list.

### Classifier

It is based on K-Means Clustering.
