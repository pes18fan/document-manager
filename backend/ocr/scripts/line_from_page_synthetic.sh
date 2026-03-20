#!/bin/bash
set -e

SOURCE="${1:-.}"
lang=nep

set -- "$SOURCE"/*.tif

for img_file; do
    echo -e "\r\n File: $img_file"
    
    base="${img_file%.*}"
    gt_file="${base}.gt.txt"  # existing ground truth text file, one line per line of text
    
    # Step 1: Run tesseract to get hocr (only for bounding boxes, not for OCR text)
    OMP_THREAD_LIMIT=1 tesseract "${img_file}" "${base}" \
        --psm 6 --oem 1 -l $lang -c page_separator='' hocr

    # Step 2: Extract line images using hocr bounding boxes
    PYTHONIOENCODING=UTF-8 hocr-extract-images \
        -b $SOURCE \
        -p "${base}"-%03d.exp0.tif \
        "${base}".hocr

    # Step 3: Write ground truth files from source text, matched by line number
    line_num=1
    while IFS= read -r line; do
        printf "%s" "$line" > "$(printf "${base}-%03d.exp0.gt.txt" $line_num)"
        ((line_num++))
    done < "$gt_file"

    extracted=$(ls "${base}"-*.exp0.tif 2>/dev/null | wc -l)
    expected=$(wc -l < "$gt_file")
    if [ "$extracted" -ne "$expected" ]; then
        echo "WARNING: line count mismatch for $img_file ($extracted extracted, $expected expected)"
    fi
done

# delete unwanted artifacts
find $SOURCE \( \
    \( -name "*.txt" ! -name "*.gt.txt" \) \    # hocr artifacts
    -o -name "*.hocr" \                         # hocr bounding boxes
    -o \( -name "*.gt.txt" ! -name "*exp0.gt.txt" \) \  # page level gt
    -o \( -name "*.tif" ! -name "*exp0.tif" \) \  # page level images
\) -delete

echo "Done. Line images and ground truth files are ready for training."
