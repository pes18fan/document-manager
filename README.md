# Document OCR and Management

Some stuff this does:

- Provide an interface to view documents. (TODO, a prototype works)
- Run OCR on the documents to provide the text. (full finetuning TODO)
- Extract top keywords from the document and use them to categorize them. (TODO, a prototype works)
- Allow manual organization using folders and tags (TODO)

## Tools used

- tesstrain
- hocr-tools (specifically hocr-extract-images for turning pages to lines)
- dvc (for managing the OCR dataset like git)

## Using dvc to manage the OCR dataset

[`dvc`](https://dvc.org) is a tool that can be used to manage datasets like Git.
In this case, it is being used to manage the OCR dataset, with DagsHub as 
the remote storage.

To set it up on your device, first install it:

```bash
uv tool install dvc
```

If you don't have `uv`, run

```bash
pipx install dvc
```

Now you can pull the dataset stored in DagsHub, using the relevant make command.

```bash
make pull
```

This will open a browser window for authentication. After this, the dataset will
be downloaded and extracted inside `backend/ocr/dataset`. You can work with
it now.

After you're done, you can update the changes by pushing:

```bash
make push
```

This will archive the set and update it in DagsHub.
