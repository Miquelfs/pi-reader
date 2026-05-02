import os
import shlex
import subprocess



def convert_book(input, output):
    subprocess.call("ebook-convert" + " " + input  + " " + output, shell=True)


files_to_convert = [file for file in os.listdir("/home/miquel/pi-reader/content/books")]
converted_books = [book for book in os.listdir("/home/miquel/pi-reader/content/library")]

library =[]
for book in converted_books:
    filename, extension = os.path.splitext(book)
    library.append(filename)

for file in files_to_convert:
    # Remove extension for conversion to TXT 
    filename, extension = os.path.splitext(file)
    if extension ==".txt":
        continue
    elif filename in library:
        continue
    else:
        output = filename + ".txt"
        full_input = shlex.quote(os.path.join("/home/miquel/pi-reader/content/books", file))
        full_output = shlex.quote(os.path.join("/home/miquel/pi-reader/content/library", output))
        print(f"Creating {full_output} from previous extension {extension}")
        convert_book(full_input, full_output)
