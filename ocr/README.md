# OCR

To test it, install the packages first (use uv)

```bash
uv sync
```

To test it out on one file, run `main.py`, choosing your file from within the
code.

```bash
uv run main.py
```

For an interactive OCR server, run the server using uvicorn.

```bash
uv run uvicorn ocr_server:app --host 127.0.0.1 --port 8000
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
