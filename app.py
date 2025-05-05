from flask import Flask, request, render_template, redirect, jsonify
from betterDataExtract import getAllLinesFromPDF, extractTableContent
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
            brand TEXT NOT NULL,
            description TEXT NOT NULL,
            color TEXT NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER
        )
    ''')

    # Pull data from database - set as shirts variable
    shirts = cursor.execute('''
        SELECT id, brand, description, color, size, quantity FROM shirts;
    ''').fetchall()

    conn.close()
    return render_template("index.html", shirts=shirts)

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    shirt_id = request.form['id']
    action = request.form['action']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current quantity
    cursor.execute('SELECT quantity FROM shirts WHERE id = ?', (shirt_id,))
    current_quantity = cursor.fetchone()['quantity']
    
    # Update based on action
    if action == 'increment':
        new_quantity = current_quantity + 1
    elif action == 'decrement':
        new_quantity = max(0, current_quantity - 1)  # Prevent negative quantities
    
    # Update database
    cursor.execute('''
        UPDATE shirts
        SET quantity = ?
        WHERE id = ?
    ''', (new_quantity, shirt_id))
    
    conn.commit()
    conn.close()
    
    return redirect("/")


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(file.filename)
    
    # get lines of data from the pdf
    allLines = getAllLinesFromPDF(file.filename)

    # clean the lines of shirts & return needed data
    pdfTableData = extractTableContent(allLines)

    shirtsToDatabase(pdfTableData)
    return redirect("/")

def shirtsToDatabase(pdfTableData):
    # Connect to the SQLite database using the connection function
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert or update each shirt in the database
    for shirt in pdfTableData:
        brand, description, color, size, quantity = shirt

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
                INSERT INTO shirts (brand, description, color, size, quantity)
                VALUES (?, ?, ?, ?, ?)
            ''', (brand, description, color, size, int(quantity)))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')