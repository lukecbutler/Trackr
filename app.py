from flask import Flask, request, render_template, redirect
from dataExtract import pdfToListOfShirts
import sqlite3

app = Flask(__name__)

# Database connection
DATABASE = "shirts.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    return conn

@app.route('/', methods=['GET'])
def home():
    conn = get_db_connection()
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
    ''').fetchall()

    conn.close()
    return render_template("index.html", shirts=shirts)


# How to upload a file
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(file.filename)
    
    # Get this list into a database
    listOfShirts = pdfToListOfShirts(file.filename)
    shirtsToDatabase(listOfShirts)
    return redirect("/")

def shirtsToDatabase(listOfShirts):
    # Connect to the SQLite database using the connection function
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert or update each shirt in the database
    for shirt in listOfShirts:
        description, color, size, quantity = shirt

        # Check if the shirt already exists in the database
        cursor.execute('''
            SELECT id, quantity FROM shirts
            WHERE description = ? AND color = ? AND size = ?
        ''', (description, color, size))

        existing_shirt = cursor.fetchone()

        if existing_shirt:
            # If the shirt exists, update the quantity
            new_quantity = existing_shirt['quantity'] + int(quantity)  # Access by column name
            cursor.execute('''
                UPDATE shirts
                SET quantity = ?
                WHERE id = ?
            ''', (new_quantity, existing_shirt['id']))
        else:
            # If the shirt does not exist, insert a new record
            cursor.execute('''
                INSERT INTO shirts (description, color, size, quantity)
                VALUES (?, ?, ?, ?)
            ''', (description, color, size, int(quantity)))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')