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

Additionally, there is a dynamic `GET /documents/{doc_id}` endpoint to grab a
document with the database ID `doc_id`, and a dynamic `DELETE /documents/{doc_id}`
endpoint to delete the document.

