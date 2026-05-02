import os

LIBRARY_PATH = "/home/miquel/pi-reader/content/library"


def get_books_list():
    return sorted(os.listdir(LIBRARY_PATH))
