import os
from flask import Flask, request, render_template
from dataExtract import pdfToListOfShirts



app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")


# how to upload a file
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        file.save(file.filename)
        listOfShirts = pdfToListOfShirts(file.filename)

        return render_template('index.html', listOfShirts = listOfShirts)
    return render_template('index.html')



if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')
