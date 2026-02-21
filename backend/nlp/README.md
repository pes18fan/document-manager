# TF-IDF Keyword Extraction

1. load `.txt` files from text directory
2. calculate TF-IDF scores for each term
3. extract top 15 keywords per document
4. save results to `keywords_output.json`

stopwords.txt contains common nepali stopwords

## Setup

Requires the `scikit-learn` package.\
The text directory should contain `.txt` files (output from ocr).\
Then, just run `keyword-ext.py`. \

```bash
python keyword-ext.py
```


## 
Added temporary `.txt` files for testing in text.
