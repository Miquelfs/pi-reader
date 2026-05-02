import os

def get_books_list():
    path = sorted(os.listdir("/home/miquel/pi-reader/content/library"))
    return path
