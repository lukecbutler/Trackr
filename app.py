from flask import Flask, request, render_template, redirect
from pdfDataExtraction import getAllLinesFromPDF, extractTableContent
import sqlite3

app = Flask(__name__)

# Database connection
DATABASE = "shirts.db"

# get database connection - used throughout program to get db access
# returns rows as key : value pairs
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    return conn

# home route - code runs when user enters trackr
@app.route('/', methods=['GET'])
def home():

    #get db connection & create cursor to run sql queries
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pull all information that goes into inventory table
    # returned as SQLite object, ie. shirts[0] is a single sqlite object
    # shirts[0][1] is the 2nd piece of data from that row 
    shirts = cursor.execute('''
        SELECT id, brand, description, color, size, quantity FROM shirts;
    ''').fetchall()
    conn.close()

    # return the index.html with shirts passed in
    return render_template("index.html", shirts=shirts)

# updates quantity of shirt in database, redirects back to single page application
@app.route('/update_quantity', methods=['POST'])
def update_quantity():

    # get the shirt key from the database & set it to shirt_id
    shirt_id = request.form['id']

    # pulls action value from button
    # value of incremnt/decremnt will be set as variable depending on user click
    action = request.form['action']

    # connect to database & create a cursor to run sql queries
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current quantity from shirt db, based on shirt id
    cursor.execute('SELECT quantity FROM shirts WHERE id = ?', (shirt_id,))

    # set current-quantity to the quantity key
    current_quantity = cursor.fetchone()['quantity']

    # Update based on action
    if action == 'increment':
        new_quantity = current_quantity + 1
    elif action == 'decrement':
        new_quantity = max(0, current_quantity - 1)  # Prevent negative quantities
        # delete shirt from database if quantity hits 0
        if new_quantity < 1:
            cursor.execute('DELETE FROM shirts WHERE id = ?', (shirt_id,))


    # if shirt quantity is not at 0, update the quantity
    # Update database
    cursor.execute('''
        UPDATE shirts
        SET quantity = ?
        WHERE id = ?
    ''', (new_quantity, shirt_id))

    # commit sql queries to database
    conn.commit()
    conn.close()

    # redirect back to the home directory
    return redirect("/")


# upload route - takes file, save it to server, 
# extract shirts from getAllLinesFromPDFf,
# Get shirts as array of arrays,
# Add the shirts to the database with shirtsToDatabase function

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(file.filename)

    # get lines of data from the pdf
    allLines = getAllLinesFromPDF(file.filename)

    # clean the lines of shirts & return needed data
    pdfTableData = extractTableContent(allLines)

    # ie. [['Comfort Colors', 'Garment-Dyed Heavyweight Long Sleeve T-Shirt', 'Grape', 'M', '1']]
    print(pdfTableData)

    # add the shirts to the database, accepts shirts as array of arrays
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


@app.route('/manual_shirt_entry', methods = ['GET', 'POST'])
def manual_shirt_entry():
    if request.method == 'POST':

        # get db connection & create cursor for sql queries
        conn = get_db_connection()
        cursor = conn.cursor()

        # get all shirt data from manual shirt entry web form
        # the name attribute from the input tag is what the .get is pulling from
        brand = request.form.get('brand')
        description = request.form.get('description')
        color = request.form.get('color')
        size = request.form.get('size')
        quantity = request.form.get('quantity')

        # sql query to input shirt into database
        cursor.execute('''
            INSERT INTO shirts (brand, description, color, size, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (brand, description, color, size, int(quantity)))

        conn.commit()
        conn.close()

        return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')