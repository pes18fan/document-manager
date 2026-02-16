# Scripts

Some useful scripts for preparing training material and whatnot

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

`text_to_image.py` acts as a frontend for this tool.

## line_from_page.py

When training tesseract, images must be split into separate lines; as the model
trains on line images rather than entire pages directly. For this purpose, we
need something that can automate this process since obviously doing this
manually would be far too tedious.

A bash script by [Shreeshrii](https://github.com/Shreeshrii) on a GitHub issue
in the `tesstrain` repo has been adapted in Python for this script, which will
act on an entire folder of page images and turn them into separate line images.
