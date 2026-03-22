# Scripts

Some useful scripts for preparing training material and whatnot.

Make sure to run them in the listed out order.

## convert_all_to_jpg.sh

Given a folder full of pdf, jpg, png etc sources, convert them all to jpg.

## rename_all.sh

Rename all the jpg images in a folder to a proper systematic naming scheme.

## convert_all_to_tif.sh

Given a folder full of jpg/jpeg sources, convert them all to tif.
Make sure to run this after the convert to jpg one, as separate pdf pages cannot
be directly converted to tif by imagemagick.

## text_to_image.py

`text2image` provided by Tesseract will be of a lot of use when fine tuning.
Provided a text file with some Nepali text, use a command like this:

```bash
text2image \
    --text=data.txt \
    --ptsize=8 \
    --xsize=2000 \
    --ysize=2000 \
    --outputbase=output/sample \
    --font="Noto Sans Devanagari"
```

one can generate an image that can directly be used to train the OCR, as a sort
of "synthetic document"; the main advantage of this is that we already have
the ground truth so we don't have to manually pull it out from documents like
with real ones.

For `--outputbase` you can choose some other value, in this case `output/sample`
means the resulting output will be in a `output` folder and the files outputted
will be an image named `sample.tif` and coordinate information in `sample.box`.

`text2image` also provides a bunch of image deterioration options to emulate
imperfect digital scans.

`text_to_image.py` acts as a frontend for this tool, used to process an entire
folder filled with Nepali text files.

**Only run this if you are creating synthetic training data.**

## grayscalize.sh

Turn all images into grayscale versions.

## pick_initial.sh

For the initial test train. Picks 5 random documents to work with and puts them
in a directory.

## line_from_page.py

When training tesseract, images must be split into separate lines; as the model
trains on line images rather than entire pages directly. For this purpose, we
need something that can automate this process since obviously doing this
manually would be far too tedious.

A bash script by [Shreeshrii](https://github.com/Shreeshrii) on a GitHub issue
in the `tesstrain` repo has been adapted in Python for this script, which will
act on an entire folder of page images and turn them into separate line images.

This will also convert all the images into the tif format if they're not already
in it.

## line_from_page_synthetic.sh

Variant of `line_from_page.py` (or rather the original shell script by
Shreeshrii) to be used when creating synthetic data with text2image. **Do NOT
use this script except in that specific circumstance.**
