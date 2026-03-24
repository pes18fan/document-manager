# Document OCR and Management

Some stuff this does:

- Provide an interface to view documents. (nicer UI TODO)
- Run OCR on the documents to provide the text. (full finetuning TODO)
- Extract top keywords from the document and use them to categorize them. 
    (DONE, minor tuning for classifier may be necessary)
- ~~Allow manual organization using folders and tags~~ Cancelled unless time
    found before external defense

## Tools used

- tesstrain to fine tune Tesseract
- hocr-tools (specifically hocr-extract-images for turning pages to lines)
- Svelte (JavaScript framework) for UI
- various JavaScript and Python libraries
