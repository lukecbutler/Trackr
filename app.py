import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from dataExtract import pdfToListOfShirts



app = Flask(__name__)

@app.route('/')
def home():
    listOfShirts = pdfToListOfShirts()
    return render_template("index.html", listOfShirts = listOfShirts)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('index.html')
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
