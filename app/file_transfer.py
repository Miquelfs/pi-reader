import os
import threading
from app import app
from flask import request, redirect
from werkzeug.utils import secure_filename
from app.text_converter import convert_pending
from config.paths import BOOKS_PATH, COMICS_PATH

app.config['UPLOAD_FOLDER_BOOKS']  = BOOKS_PATH
app.config['UPLOAD_FOLDER_COMICS'] = COMICS_PATH

BOOK_EXTENSIONS  = {'txt', 'pdf', 'azw3', 'epub', 'mobi'}
COMIC_EXTENSIONS = {'cbz', 'cbr', 'pdf'}


def _allowed(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


def _is_comic(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    # PDFs can be either — we treat them as books unless uploaded via the comic form
    return ext in {'cbz', 'cbr'}


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    message = ''
    error = ''

    if request.method == 'POST':
        kind = request.form.get('kind', 'book')
        file = request.files.get('file')

        if not file or file.filename == '':
            error = 'No file selected.'
        else:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

            if kind == 'comic':
                if ext not in COMIC_EXTENSIONS:
                    error = f'Unsupported comic format: .{ext}. Use CBZ, CBR or PDF.'
                else:
                    dest = os.path.join(app.config['UPLOAD_FOLDER_COMICS'], filename)
                    file.save(dest)
                    message = f'Comic "{filename}" uploaded. It will appear in the Comics section.'
            else:
                if ext not in BOOK_EXTENSIONS:
                    error = f'Unsupported book format: .{ext}. Use EPUB, MOBI, PDF, AZW3 or TXT.'
                else:
                    dest = os.path.join(app.config['UPLOAD_FOLDER_BOOKS'], filename)
                    file.save(dest)
                    threading.Thread(target=convert_pending, daemon=True).start()
                    message = f'Book "{filename}" uploaded — converting to text in the background. It will appear in the library in about a minute.'

    return f'''<!doctype html>
<html>
<head>
  <title>Pi Reader — Upload</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 540px; margin: 48px auto; padding: 0 16px; color: #111; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
    p.sub {{ color: #555; margin-top: 0; margin-bottom: 32px; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 24px; margin-bottom: 24px; }}
    .card h2 {{ margin-top: 0; font-size: 1.1rem; }}
    label {{ display: block; margin-bottom: 8px; font-size: 0.9rem; color: #444; }}
    input[type=file] {{ display: block; margin-bottom: 16px; }}
    button {{ background: #111; color: #fff; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-size: 1rem; }}
    button:hover {{ background: #333; }}
    .ok  {{ background: #e6f4ea; border: 1px solid #a8d5b0; color: #1a5c2a; padding: 12px 16px; border-radius: 6px; margin-bottom: 24px; }}
    .err {{ background: #fdecea; border: 1px solid #f5b7b1; color: #7b1c1c; padding: 12px 16px; border-radius: 6px; margin-bottom: 24px; }}
  </style>
</head>
<body>
  <h1>Pi Reader</h1>
  <p class="sub">Upload books or comics to your device over WiFi.</p>

  {'<div class="ok">' + message + '</div>' if message else ''}
  {'<div class="err">' + error   + '</div>' if error   else ''}

  <div class="card">
    <h2>📖 Upload a Book</h2>
    <form method="post" enctype="multipart/form-data">
      <input type="hidden" name="kind" value="book">
      <label>Supported formats: EPUB, MOBI, PDF, AZW3, TXT</label>
      <input type="file" name="file" accept=".epub,.mobi,.pdf,.azw3,.txt">
      <button type="submit">Upload Book</button>
    </form>
  </div>

  <div class="card">
    <h2>🗂 Upload a Comic</h2>
    <form method="post" enctype="multipart/form-data">
      <input type="hidden" name="kind" value="comic">
      <label>Supported formats: CBZ, CBR, PDF</label>
      <input type="file" name="file" accept=".cbz,.cbr,.pdf">
      <button type="submit">Upload Comic</button>
    </form>
  </div>
</body>
</html>'''
