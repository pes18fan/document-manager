#!/usr/bin/env python
# credit to github.com/Shreeshrii, python script adapted from their shell script
import os
import argparse
import subprocess
from pathlib import Path


def process_folder(folder_path, output_folder=None, lang="nep", separate_folders=False):
    # Convert string path to Path object and resolve to absolute path
    folder = Path(folder_path).resolve()

    if not folder.exists():
        print(f"Error: Folder '{folder}' does not exist.")
        return

    # Determine main output directory
    if output_folder:
        main_output_dir = Path(output_folder).resolve()
    else:
        main_output_dir = folder / "output"

    if not main_output_dir.exists():
        main_output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {main_output_dir}")

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

            # Define HOCR output path in the main output directory
            # Tesseract adds .hocr extension automatically
            hocr_output_base = main_output_dir / base_name

            tesseract_cmd = [
                "tesseract",
                str(file_path),
                str(hocr_output_base),
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

            # The HOCR file will be at main_output_dir / (base_name + ".hocr")
            hocr_file = main_output_dir / f"{base_name}.hocr"

            if not hocr_file.exists():
                print(f"Error: Expected HOCR file {hocr_file} not found.")
                continue

            # Determine output directory and pattern for lines
            if separate_folders:
                # Create a subfolder for the image lines inside the main output directory
                line_output_dir = main_output_dir / base_name
                line_output_dir.mkdir(exist_ok=True)
                # Pattern with subfolder
                pattern = str(line_output_dir / f"{base_name}-%03d.exp0.tif")
            else:
                # Pattern in the main output directory
                pattern = str(main_output_dir / f"{base_name}-%03d.exp0.tif")

            extract_cmd = [
                "hocr-extract-images",
                "-b",
                str(
                    folder
                    # Base dir for finding the source image (still the input folder)
                ),
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
    parser.add_argument(
        "--output",
        help="Output directory for HOCR and line image files (default: <input_folder>/output)",
    )

    args = parser.parse_args()

    process_folder(args.folder, args.output, args.lang, args.separate_folders)
