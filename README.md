# Document categorizer thing

- get ocr working
- get image preprocessor working (NOTE: may not need if tesseract preprocessor works fine)
- get keyword grabbing working

## Tools used

- tesstrain
- hocr-tools (specifically hocr-extract-images for turning pages to lines)

also this shell script to extract lines out of pages:

```bash
#!/bin/bash
# credit to github.com/Shreeshrii

SOURCE="./myfiles/"
lang=nep
set -- "$SOURCE"*.png
for img_file; do
    echo -e  "\r\n File: $img_file"
    OMP_THREAD_LIMIT=1 tesseract --tessdata-dir ../tessdata_fast   "${img_file}" "${img_file%.*}"  --psm 6  --oem 1  -l $lang -c page_separator='' hocr
    source venv/bin/activate
    PYTHONIOENCODING=UTF-8 ./hocr-extract-images -b ./myfiles/ -p "${img_file%.*}"-%03d.exp0.tif  "${img_file%.*}".hocr 
    deactivate
done
rename s/exp0.txt/exp0.gt.txt/ ./myfiles/*exp0.txt

echo "Image files converted to tif. Correct the ground truth files and then run ocr-d train to create box and lstmf files"
```
