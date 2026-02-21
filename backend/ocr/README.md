# Preprocessing

Not much preprocessing has been implemented yet, as so far the preprocessing 
done by Tesseract itself is deemed to be enough; however some level of deskewing 
might be necessary to implement.

To view the processed image that Tesseract generates before passing that image
into its OCR section, you can set the `tessedit_write_images` parameter to `1`
when running tesseract, like so:

```bash
tesseract file.jpg output -l "nep,eng" -c tessedit_write_images=1
```

# Preparing dataset

## Getting the documents

- retrieved from various government websites
    - Language Commission
    - Department of Education
    - Nepal Telecom
    - Public Service Commission (Loksewa Aayog)
    - Human Rights Commission
- retrieved various images and pdfs

## Cleaning up

Scripts used are in `scripts/`

- everything turned into `jpg` images via `convert_all_to_jpg.sh`
- everything renamed to a consistent name via `rename_all.sh`
- everything converted to `tif` (format used for tesstrain) via `convert_all_to_tif.sh`
    - `tif` conversion was done after `jpg` because `imagemagick` doesn't support
        directly converting PDFs to `tif`
- turn all images grayscale using `grayscalize.sh`
- pick five random docs for the initial tiny training material via `pick_initial.sh`
- use `line_from_page.py` to split each image into lines and extract text from
    them using tesseract itself (for the ground truth text)
    - obviously the extracted text is not going to be correct, this is corrected
        manually for each line

## Dataset structure

- not sure on this yet
- from what I know so far, it has:
    - line images, NOT page images, with extension `.tif`
    - ground truth `.gt.txt` file with transcripts for corresponding `.tif` image
        - created by correcting the approximate transcripts created via
            `line_from_page.py`
    - two created when running `make training`
        - `.box` file for each image, with coordinates for each char, seemingly not
            necessary to generate by hand?
        - `.lstmf` file, not sure what it is

## Training

steps according to the ideas given by the example on `github.com/tesseract-ocr/tesstrain`'s
readme.

- get the dataset ready and put it in a folder called `foo-ground-truth` in a structure like:

```
data
    foo/<empty>
    foo-ground-truth/
```

where "foo" is the name of the model.

- grab the nepali traineddata `nep.traineddata` provided by tesseract to fine 
    tune on. Make sure to use the best model provided at 
    `github.com/tesseract-ocr/tessdata_best`, as the normal integer models do 
    not work for training.
    - put it in a folder named `tessdata`

- run `make training` in tesstrain, providing the `MODEL_NAME` parameter for the
    name of the model, `START_MODEL` as `nep` and `TESSDATA` as the `./tessdata`
    folder you created earlier.

```bash
make training MODEL_NAME=foo START_MODEL=nep TESSDATA=./tessdata
```

