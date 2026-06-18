import os
import threading
from app import app
from flask import flash, request, redirect
from werkzeug.utils import secure_filename
from app.text_converter import convert_pending

from config.paths import BOOKS_PATH
UPLOAD_FOLDER = BOOKS_PATH
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'azw3', 'epub', 'mobi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Convert in background so the browser doesn't time out on large books
            threading.Thread(target=convert_pending, daemon=True).start()
            return '''
            <!doctype html>
            <title>Upload successful</title>
            <h1>File uploaded — converting to text in the background.</h1>
            <p>The book will appear in the library within a minute. <a href="/">Upload another</a></p>
            '''
    return '''
    <!doctype html>
    <title>Pi Reader — Upload Book</title>
    <h1>Upload a book</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file accept=".txt,.pdf,.epub,.mobi,.azw3">
      <input type=submit value=Upload>
    </form>
    '''
