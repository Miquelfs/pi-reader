import os
from config.paths import LIBRARY_PATH


def get_books_list():
    try:
        return [f for f in sorted(os.listdir(LIBRARY_PATH)) if not f.startswith('.')]
    except FileNotFoundError:
        return []
