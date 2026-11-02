import json
import os
import re
import shlex
import shutil
import subprocess
import threading
from datetime import date
from config.paths import BOOKS_PATH, LIBRARY_PATH

# Module-level conversion state — read by upload_screen.py to show progress
conversion_state = {
    'status': 'idle',      # 'idle' | 'converting' | 'done' | 'error'
    'filename': '',
    'last_title': '',
}

# One ebook-convert at a time: the Pi Zero has 512 MB, and two runs triggered
# by back-to-back uploads would otherwise race on the same file.
_convert_lock = threading.Lock()


def _already_converted(filename):
    stem, _ = os.path.splitext(filename)
    return (stem + ".txt") in os.listdir(LIBRARY_PATH)


def _clean_filename(stem):
    """Derive a readable title from a filename stem as last-resort fallback."""
    name = re.sub(r'[_\-]+', ' ', stem)
    return name.strip().title()


def _extract_metadata(input_path, stem):
    """
    Try ebook-meta (Calibre) to get title/author.
    Returns (title, author) strings, falling back to filename.
    """
    title = _clean_filename(stem)
    author = ''
    try:
        result = subprocess.run(
            ['ebook-meta', input_path],
            capture_output=True, text=True, timeout=15,
        )
        for line in result.stdout.splitlines():
            if line.lower().startswith('title'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    val = parts[1].strip()
                    if val and val.lower() != 'unknown':
                        title = val
            elif line.lower().startswith('author'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    val = parts[1].strip()
                    if val and val.lower() != 'unknown':
                        author = val
    except Exception:
        pass
    return title, author


def _word_count(txt_path):
    try:
        with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
            return len(f.read().split())
    except Exception:
        return 0


def _write_meta(stem, title, author, word_count):
    meta_path = os.path.join(LIBRARY_PATH, stem + '.meta.json')
    meta = {
        'title': title,
        'author': author,
        'word_count': word_count,
        'converted_at': date.today().isoformat(),
    }
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def convert_book(input_path, output_path):
    """Run ebook-convert and return True on success."""
    cmd = f"ebook-convert {shlex.quote(input_path)} {shlex.quote(output_path)}"
    result = subprocess.call(cmd, shell=True)
    return result == 0


def convert_pending():
    """Convert every file in books/ that isn't already in library/. Returns list of converted filenames."""
    with _convert_lock:
        return _convert_pending()


def _convert_pending():
    converted = []
    for filename in os.listdir(BOOKS_PATH):
        if filename.startswith('.'):
            continue
        stem, ext = os.path.splitext(filename)
        if not ext or _already_converted(filename):
            continue
        input_path  = os.path.join(BOOKS_PATH, filename)
        output_path = os.path.join(LIBRARY_PATH, stem + ".txt")

        if ext.lower() == ".txt":
            shutil.copyfile(input_path, output_path)
            title = _clean_filename(stem)
            _write_meta(stem, title, '', _word_count(output_path))
            conversion_state['status'] = 'done'
            conversion_state['filename'] = filename
            conversion_state['last_title'] = title
            converted.append(stem + ".txt")
            continue

        print(f"Converting {filename} → {stem}.txt")
        conversion_state['status'] = 'converting'
        conversion_state['filename'] = filename
        conversion_state['last_title'] = _clean_filename(stem)
        # Dot-prefixed temp name so the library never lists a half-written book
        tmp_path = os.path.join(LIBRARY_PATH, "." + stem + ".converting.txt")
        if convert_book(input_path, tmp_path):
            os.replace(tmp_path, output_path)
            title, author = _extract_metadata(input_path, stem)
            wc = _word_count(output_path)
            _write_meta(stem, title, author, wc)
            conversion_state['status'] = 'done'
            conversion_state['last_title'] = title
            converted.append(stem + ".txt")
        else:
            print(f"  ebook-convert failed for {filename}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            conversion_state['status'] = 'error'
    if not converted and conversion_state['status'] != 'error':
        conversion_state['status'] = 'idle'
    return converted
