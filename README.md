# Document categorizer thing

- get ocr working
- get image preprocessor working (NOTE: may not need if tesseract preprocessor works fine)
- get keyword grabbing working

## OCR

To test it, first create a venv, enter it, install the packages 

```bash
python -m venv .venv
source .venv/bin/activate   # on linux
pip install -r requirements.txt
```

Then run the OCR server using uvicorn

```bash
uvicorn ocr_server:app --host 127.0.0.1 --port 8000
```

This will open up a HTTP server where you can make requests to the `/ocr`
endpoint with a file parameter to get the OCR result of it out.

A client working with this endpoint is not ready yet, but to test it real quick
you can run this:

```bash
curl -X POST "http://127.0.0.1:8000/ocr" \
     -F "file=@filename.jpg" | jq -r ".text" > out.txt
```

Replace `filename.jpg` with the file you want to test with.

Note that you'll need `curl` and `jq` installed to run this command.

## Client

Uses the OCR server and later on the NLP server.

Will eventually be a proper Electron app. For now its a simple proof-of-concept
HTML page.
