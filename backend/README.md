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
  interface {
      filename: string;
      raw_text: string;
      avg_conf: number;
  }
  ```

  This will save the document to the PostgreSQL database and send back a
  result with this interface:

  ```typescript
  interface {
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

1. Input & Setup

    An image is fed into the engine. The assumption made by Tesseract is that the
    received image is binary (i.e. black and white), however Tesseract does perform
    some preprocessing on its own as well.

2. Connected Component Analysis

    The engine finds and stores the outlines of all shapes in the images. Based on
    how they nest inside each other, Tesseract is also capable of detecting
    white-on-black text instead of the usual black-on-white.

3. Line and Word Finding

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

4. Recognition

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

### LSTMs

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
find for an **abugida** like Devanagari that does not have dedicated characters
for every sound, and instead has "incomplete" diacritics for those sounds, which
are more difficult to classify via a box file.

### In the context of Tesseract

In Tesseract 5, for recognition, the input is processed line-by-line, unlike the
old recognizer which processed individual characters. This eliminates a lot of
the character recognition work, which is performed by the LSTM implicitly while 
reading the entire line at once.

## How the NLP section works

The NLP section has two main parts: a keyword extractor which finds and extracts
words that have high importance in the corpus, and a classifier, which clusters
similar documents together.

### Preprocessing

Before either of the parts of this section are used, the text itself is passed
through a simple preprocessor function to strip either meaningless or
semantically useless information. It namely does the following things:

- Remove special characters like `/`, `,`, `।` and so on.
- Remove any English or Devanagari digits.
- Remove whitespace.

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
document, as well as for terms that are not in that document but are in the
corpus (they get a TF value 0). These values are combined to form a vector. 
Doing this for every document in the corpus, we get the $n$ vectors corresponding 
to each.

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

After the TF and IDF vectors are computed separately, we calculate the TF-IDF
score for each words by multiplying the word's TF score by its IDF score. This
results in a single vector per document.

#### Design Decisions

For the vectorizer, we decided to pick the `ngram_range` parameter to be
`(1, 2)`, which means that two-word phrases may also be captured as single
features. This is important because there exist many such phrases (e.g. मानव अधिकार)
that mean something different when separated.

Additionally, we chose the value for `min_df` to be `2`. `min_df` determines
how many documents a term must appear in to be included as a feature. This was
done to filter out any words that are either overly scarce (since IDF provides
emphasis to rarer words), or OCR errors that could slip into the final keywords.

We capped the maximum number of features to 500 to keep only the most important
words but also have a solid amount.

##### Stopwords

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

It is based on K-Means clustering.

K-Means clustering is an algorithm that is used to divide a set of data into
multiple sets known as clusters, based on how some of their properties differ
or are similar to each other.

For example, let's say you have a set of numbers like:

```
--xx-x-----------xxx-x-x--x-xxx-x--------------x-xx-x-xxxx----
```

Where each `x` represents a datapoint in the number line.

Visibly, it is clear that the numbers can are separated into three different
portions. A computer can find this out by making use of the K-Means clustering
algorithm.

This specific case handles one-dimensional data (numbers). In our specific case,
we work with vectors that represent documents, each vector having several
numerical values that each correspond to a certain feature and describe how
relevant this feature is for the document. Together, this entire vector is
a representation of where the document is in this "coordinate space" of sorts
where each "axis" is the direction at which a certain word has more importance.
Thus in this "coordinate space", documents heavy on certain words will sit
closer to other documents which are also heavy on those words.

Because the number of features is generally very high, the number of dimensions
to work with is also therefore very high. 

So, the K-Means clustering algorithm here works with a very high dimensional 
vector space, where the number of dimensions is equal to the number of features
extracted by the TF-IDF vectorizer, that is, the **total number of keywords**.

In our case, `scikit-learn` handles this algorithm, and as there are maximum
500 features due to the cap on the vectorizer, the algorithm works with
500-dimensional data.

The classifier goes through the following steps.

1. Picking $k$

    $k$ is the number of clusters that we wish to divide the data into. This is
    the "K" in K-Means clustering.

    We picked an initial value of 5 for $k$ in our case. This was chosen because
    it is a good starter choice that allows for a substantial amount of data to be
    in each cluster, while also allowing for variation.

2. Select initial clusters

    Now, $k$ (5) data points are randomly selected in the vector space. These vectors 
    are the initial cluster centroids.

3. Assign points to cluster

    We take the first point, which in this case will be a vector representing a
    certain random document, and measure how far it is from the 5 cluster centroids.

    The point is then assigned to the cluster that it is nearest to.

    Then, we do this for all of the other clusters. Once this is done, every 
    point will have been assigned to a cluster.

4. Calculate mean

    Calculate the mean for each of the clusters. 

    For this, we calculate the mean of a single cluster by taking every point that 
    is in that cluster, and finding the mean value for the points. We repeat this
    for all of the clusters.

    Once we have calculated the means, for each cluster, we replace the centroid
    of the cluster by the mean.

5. Repeat

    Repeat step 3 and 4, until an assignment does not make any changes to the 
    clustering. 

    In the case of `scikit-learn`, there is an additional stopping condition; 
    the clustering may also be completed if the number of iterations reaches
    the `max_iter` value.

K-Means is not guaranteed to find the best possible clustering. For this purpose,
one option is to cluster several times with different starting points, and
pick the result that has the least variation between the clusters. `scikit-learn`
handles this automatically via multiple restarts.
