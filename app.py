from flask import Flask, request, render_template, redirect
from dataExtract import pdfToListOfShirts
import sqlite3


app = Flask(__name__)

# Database connection
DATABASE = "shirts.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def home():

    conn = sqlite3.connect('shirts.db')
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shirts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            color TEXT NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER
        )
    ''')

    # Pull data from database - set as shirts variable
    shirts = cursor.execute('''
    SELECT description, color, size, quantity FROM shirts;
    ''')
    print(shirts)
    return render_template("index.html", shirts = shirts)



# how to upload a file
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(file.filename)
    
    # Get this list into a database
    listOfShirts = pdfToListOfShirts(file.filename)
    shirtsToDatabase(listOfShirts)
    print(listOfShirts)
    return redirect("/")



def shirtsToDatabase(listOfShirts):
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('shirts.db')
    cursor = conn.cursor()

    # Insert each shirt into the database
    for shirt in listOfShirts:
        description, color, size, quantity = shirt
        cursor.execute('''
            INSERT INTO shirts (description, color, size, quantity)
            VALUES (?, ?, ?, ?)
        ''', (description, color, size, int(quantity)))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()



if __name__ == "__main__":
    app.run(debug=True)
