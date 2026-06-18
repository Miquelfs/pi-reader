import os
import shlex
import subprocess
from config.paths import BOOKS_PATH, LIBRARY_PATH


def _already_converted(filename):
    stem, _ = os.path.splitext(filename)
    return (stem + ".txt") in os.listdir(LIBRARY_PATH)


def convert_book(input_path, output_path):
    """Run ebook-convert and return True on success."""
    cmd = f"ebook-convert {shlex.quote(input_path)} {shlex.quote(output_path)}"
    result = subprocess.call(cmd, shell=True)
    return result == 0


def convert_pending():
    """Convert every file in books/ that isn't already in library/. Returns list of converted filenames."""
    converted = []
    for filename in os.listdir(BOOKS_PATH):
        stem, ext = os.path.splitext(filename)
        if ext.lower() == ".txt":
            continue
        if _already_converted(filename):
            continue
        input_path  = os.path.join(BOOKS_PATH, filename)
        output_path = os.path.join(LIBRARY_PATH, stem + ".txt")
        print(f"Converting {filename} → {stem}.txt")
        if convert_book(input_path, output_path):
            converted.append(stem + ".txt")
        else:
            print(f"  ebook-convert failed for {filename}")
    return converted
