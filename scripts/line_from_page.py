#!/usr/bin/env python
# credit to github.com/Shreeshrii, python script adapted from their shell script
import os
import argparse
import subprocess
from pathlib import Path


def process_folder(folder_path, lang="nep", separate_folders=False):
    # Convert string path to Path object and resolve to absolute path
    folder = Path(folder_path).resolve()

    if not folder.exists():
        print(f"Error: Folder '{folder}' does not exist.")
        return

    # extensions to look for
    extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

    # Iterate over files in the folder
    for file_path in folder.iterdir():
        if file_path.suffix.lower() in extensions:
            if ".exp0" in file_path.name:
                continue

            print(f"\nProcessing: {file_path}")

            # Base filename without extension
            base_name = file_path.stem
            # Full path without extension (for output naming)
            base_path = file_path.with_suffix("")

            # 1. Run Tesseract to generate HOCR
            # tesseract "{img_file}" "{img_file%.*}" --psm 6 --oem 1 -l $lang -c page_separator='' hocr
            # tesseract adds extension automatically
            hocr_output_base = str(base_path)

            tesseract_cmd = [
                "tesseract",
                str(file_path),
                hocr_output_base,
                "--psm",
                "6",
                "--oem",
                "1",
                "-l",
                lang,
                "-c",
                "page_separator=''",
                "hocr",
            ]

            # Set environment variable OMP_THREAD_LIMIT=1
            env = os.environ.copy()
            env["OMP_THREAD_LIMIT"] = "1"

            try:
                print(f"Running Tesseract on {file_path.name}...")
                subprocess.run(tesseract_cmd, env=env, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running tesseract on {file_path.name}: {e}")
                continue

            # 2. Run hocr-extract-images
            # PYTHONIOENCODING=UTF-8 hocr-extract-images -b ./images/ -p "${img_file%.*}"-%03d.exp0.tif "${img_file%.*}".hocr

            hocr_file = base_path.with_suffix(".hocr")

            if not hocr_file.exists():
                print(f"Error: Expected HOCR file {hocr_file} not found.")
                continue

            # Determine output directory and pattern
            if separate_folders:
                # Create a subfolder for the image lines
                output_dir = folder / base_name
                output_dir.mkdir(exist_ok=True)
                print(f"Output directory: {output_dir}")

                # Pattern with subfolder
                pattern = str(output_dir / f"{base_name}-%03d.exp0.tif")
            else:
                # Pattern in the same folder
                pattern = str(folder / f"{base_name}-%03d.exp0.tif")

            extract_cmd = [
                "hocr-extract-images",
                "-b",
                str(folder),  # Base dir for finding the source image
                "-p",
                pattern,
                str(hocr_file),
            ]

            # Set PYTHONIOENCODING=UTF-8
            env["PYTHONIOENCODING"] = "UTF-8"

            try:
                print(f"Extracting lines from {hocr_file.name}...")
                subprocess.run(extract_cmd, env=env, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error extracting images for {file_path.name}: {e}")
                continue

    print("\nProcessing complete.")
    print(
        "Image files converted to tif. Correct the ground truth files and then run ocr-d train to create box and lstmf files"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert page images to line images using Tesseract and hocr-extract-images."
    )
    parser.add_argument("folder", help="Path to the folder containing images")
    parser.add_argument(
        "--lang", default="nep", help="Language code for Tesseract (default: nep)"
    )
    parser.add_argument(
        "--separate-folders",
        action="store_true",
        help="Place separated lines for each image in its own separate folder",
    )

    args = parser.parse_args()

    process_folder(args.folder, args.lang, args.separate_folders)
