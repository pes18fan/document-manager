#!/usr/bin/env python
# Given a folder of text files, wrap all lines to be no longer than 80
# characters. Needed for text2image processing.
import os
import glob
import sys


def manual_wrap(text, width=80):
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + (1 if current_line else 0) > width:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            if current_line:
                current_length += 1  # space
            current_line.append(word)
            current_length += len(word)

    if current_line:
        lines.append(' '.join(current_line))

    return '\n'.join(lines)


def wrap_file(file_path, output_path, width=80):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    paragraphs = []
    current_paragraph = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            current_paragraph.append(stripped)
        else:
            if current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
            paragraphs.append('')  # Preserve blank lines as empty paragraphs

    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))

    wrapped_paragraphs = []
    for para in paragraphs:
        if para == '':
            wrapped_paragraphs.append('')
        else:
            wrapped = manual_wrap(para, width=width)
            wrapped_paragraphs.append(wrapped)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(wrapped_paragraphs))

    print(f"wrapped {file_path}")


def process_folder(folder_path):
    for file_path in glob.glob(os.path.join(folder_path, '*.txt')):
        base, ext = os.path.splitext(file_path)
        wrap_file(file_path, file_path)  # replace existing file


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: segment_lines.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"error: {folder_path} is not a valid directory.")
        sys.exit(1)

    process_folder(folder_path)
    print("processing complete. Wrapped and replaced files.")
