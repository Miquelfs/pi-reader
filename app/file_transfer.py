import html
import os
import threading
from app import app
from flask import request, send_file, jsonify
from werkzeug.utils import secure_filename
from app.text_converter import convert_pending
from config.paths import BOOKS_PATH, BASE_DIR

HIGHLIGHTS_FILE = os.path.join(BASE_DIR, 'content', 'highlights.json')

app.config['UPLOAD_FOLDER_BOOKS'] = BOOKS_PATH
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

BOOK_EXTENSIONS = {'txt', 'pdf', 'azw3', 'epub', 'mobi'}


@app.route('/highlights')
def download_highlights():
    if not os.path.exists(HIGHLIGHTS_FILE):
        return jsonify([])
    return send_file(HIGHLIGHTS_FILE, as_attachment=True, download_name='highlights.json', mimetype='application/json')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    message = ''
    error = ''

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            error = 'No file selected.'
        else:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext not in BOOK_EXTENSIONS:
                error = f'Unsupported format: .{ext}. Use EPUB, MOBI, PDF, AZW3 or TXT.'
            else:
                dest = os.path.join(app.config['UPLOAD_FOLDER_BOOKS'], filename)
                file.save(dest)
                threading.Thread(target=convert_pending, daemon=True).start()
                message = f'"{filename}" uploaded — converting in the background. Will appear in library within a minute.'
    return _page(message, error)


@app.route('/article', methods=['POST'])
def send_article():
    from utils.article import extract, fetch, save_to_library
    url = (request.form.get('url') or '').strip()
    if not url.startswith(('http://', 'https://')):
        return _page(error='Paste a full link starting with http:// or https://')
    try:
        title, text = extract(fetch(url))
    except Exception as e:
        return _page(error=f'Could not fetch that page ({e}).')
    if len(text.split()) < 50:
        return _page(error='Found almost no article text on that page. Try copying the text and using the box below.')
    save_to_library(title or url, text)
    return _page(f'"{title or url}" added to the library ({len(text.split()):,} words).')


@app.route('/text', methods=['POST'])
def send_text():
    from utils.article import save_to_library
    title = (request.form.get('title') or '').strip()
    text = (request.form.get('text') or '').strip()
    if not text:
        return _page(error='The text box is empty.')
    save_to_library(title or text.split('\n', 1)[0][:60], text)
    return _page(f'"{title or "Your text"}" added to the library ({len(text.split()):,} words).')


def _page(message='', error=''):
    message, error = html.escape(message), html.escape(error)
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
    label {{ display: block; margin-bottom: 8px; font-size: 0.9rem; color: #444; }}
    input[type=file] {{ display: block; margin-bottom: 16px; }}
    input[type=url], input[type=text], textarea {{ display: block; width: 100%; box-sizing: border-box; margin-bottom: 12px;
      padding: 10px; border: 1px solid #ccc; border-radius: 6px; font: inherit; }}
    textarea {{ min-height: 140px; }}
    button {{ background: #111; color: #fff; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-size: 1rem; }}
    button:hover {{ background: #333; }}
    .ok  {{ background: #e6f4ea; border: 1px solid #a8d5b0; color: #1a5c2a; padding: 12px 16px; border-radius: 6px; margin-bottom: 24px; }}
    .err {{ background: #fdecea; border: 1px solid #f5b7b1; color: #7b1c1c; padding: 12px 16px; border-radius: 6px; margin-bottom: 24px; }}
  </style>
</head>
<body>
  <h1>Pi Reader</h1>
  <p class="sub">Send books, articles and text to your reader over Wi-Fi.</p>
  {'<div class="ok">' + message + '</div>' if message else ''}
  {'<div class="err">' + error   + '</div>' if error   else ''}
  <div class="card">
    <form method="post" enctype="multipart/form-data">
      <label>Supported formats: EPUB, MOBI, PDF, AZW3, TXT</label>
      <input type="file" name="file" accept=".epub,.mobi,.pdf,.azw3,.txt">
      <button type="submit">Upload Book</button>
    </form>
  </div>
  <div class="card">
    <form method="post" action="/article">
      <label for="url">Article link: the reader fetches the page and keeps just the text</label>
      <input type="url" id="url" name="url" placeholder="https://…" required>
      <button type="submit">Send article</button>
    </form>
  </div>
  <div class="card">
    <form method="post" action="/text">
      <label for="title">Or paste text</label>
      <input type="text" id="title" name="title" placeholder="Title (optional)">
      <textarea id="text" name="text" placeholder="Paste here…" required></textarea>
      <button type="submit">Send text</button>
    </form>
  </div>
</body>
</html>'''
