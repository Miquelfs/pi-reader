import os

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_PATH   = os.path.join(BASE_DIR, 'content', 'books')
LIBRARY_PATH = os.path.join(BASE_DIR, 'content', 'library')
COMICS_PATH  = os.path.join(BASE_DIR, 'content', 'comics')
FONTS_DIR    = os.path.join(BASE_DIR, 'config', 'fonts')
BOOKMARKS_FILE = os.path.join(LIBRARY_PATH, '.bookmarks.json')
