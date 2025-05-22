from flask import Flask, request, render_template, redirect, flash, make_response
from SSpdfDataExtraction import getAllLinesFromPDF, extractTableContent
import sqlite3
import os

app = Flask(__name__)

#set secret key for sessions - flash uses sessions to handle user specific data
app.secret_key = os.urandom(24)  # generates a random 24-byte secret key

# Database connection
DATABASE = "shirts.db"

# Upload Folder Name
uploadFolder = 'pdfsStoredOnServer'

# makes sure the uploadFolder is created automatically if it doesn't exist.
os.makedirs(uploadFolder, exist_ok=True)

# get database connection - used throughout program to get db access
# returns rows as key : value pairs

# if Alice is user id = 1, and you add a shirt with user_id = 1, you're telling the database:
# "This shirt belongs to Alice"
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    return conn

# home route - code runs when user enters trackr
@app.route('/', methods=['GET'])
def home():

    userID = request.cookies.get('userID')
    if not userID:
        return redirect('/login')

    #get db connection & create cursor to run sql queries
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pull all information that goes into inventory table
    # returned as SQLite object, ie. shirts[0] is a single sqlite object
    # shirts[0][1] is the 2nd piece of data from that row 
    shirts = cursor.execute('''
        SELECT id, brand, description, color, size, quantity 
        FROM shirts 
        WHERE user_id = ?;
    ''',(userID,)).fetchall()
    conn.close()

    # return the index.html with shirts passed in
    return render_template("index.html", shirts=shirts)

# updates quantity of shirt in database, redirects back to single page application
@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    shirt_id = request.form['id']
    action = request.form['action']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current quantity (pre user click of + or -)
    # execute, (executes) a tuple of parameters
    # .fetchone() returns a single row, which behaves like a dictionary due to sqlite.Row
    # ['quantity'] grabs the value under the quantity comumn for that shirt
    current_quantity = cursor.execute(
        'SELECT quantity FROM shirts WHERE id = ?', (shirt_id,)
    ).fetchone()['quantity']

    # Decide new quantity based on action
    if action == 'increment':
        new_quantity = current_quantity + 1
    elif action == 'decrement':
        new_quantity = max(0, current_quantity - 1)

    # If new quantity is 0, delete the shirt using the shirt id
    if new_quantity == 0:
        cursor.execute('DELETE FROM shirts WHERE id = ?', (shirt_id,))
    # Else set the shirt to the new quantity using the shirt id
    else:
        cursor.execute('''
            UPDATE shirts SET quantity = ? WHERE id = ?
        ''', (new_quantity, shirt_id))

    # Commit changes & close the db connection
    conn.commit()
    conn.close()

    # Redirect user back to single page application
    return redirect("/")


# upload route - takes file, save it to server, 
# extract shirts from getAllLinesFromPDFf,
# Get shirts as array of arrays,
# Add the shirts to the database with shirtsToDatabase function


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    # os.path.join(...) builds the correct file path for saving on the server
    filePath = os.path.join(uploadFolder, file.filename)
    # saves the file to the file path

    # handle no file uploaded bug
    if file:
        file.save(filePath)
    else:
        return redirect('/')

    # get lines of data from the pdf
    allLines = getAllLinesFromPDF(filePath)

    # clean the lines of shirts & return needed data
    pdfTableData = extractTableContent(allLines)

    # get user ID to specify who's shirt is whos
    userID = request.cookies.get('userID') # find userID via the cookie
    
    # safely type cast user id to an integer
    if userID is not None:
        userID = int(userID)

    # add the shirts to the database, accepts shirts as array of arrays
    shirtsToDatabase(pdfTableData, userID)
    return redirect("/")


def shirtsToDatabase(pdfTableData, userID):
    # Connect to the SQLite database using the connection function
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert or update each shirt in the database
    for shirt in pdfTableData:
        brand, description, color, size, quantity = shirt

        # Check if the shirt already exists in the database
        cursor.execute('''
            SELECT id, quantity FROM shirts
            WHERE description = ? AND color = ? AND size = ? AND user_id = ?
        ''', (description, color, size, userID))

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
                INSERT INTO shirts (brand, description, color, size, quantity, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (brand, description, color, size, int(quantity), userID))

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


        # get user ID to specify who's shirt is whos
        userID = request.cookies.get('userID') # find userID via the cookie
        
        # safely type cast user id to an integer
        if userID is not None:
            userID = int(userID)


        # sql query to input shirt into database
        cursor.execute('''
            INSERT INTO shirts (brand, description, color, size, quantity, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (brand, description, color, size, int(quantity), userID))

        conn.commit()
        conn.close()

        return redirect('/')

# TODO: make sure users are automatically logged in once they register
@app.route('/register', methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # get first name, last name, email, & password from html form - get form data
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # check if both passwords are the same - validate form data
        if password1 == password2:
            finalPassword = password1
        else:
            flash('Passwords did not matchy match!')
            return redirect('/register')

        # insert into database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users (firstName, lastName, email, password)
                VALUES(?,?,?,?)
            ''', (firstName, lastName, email, finalPassword))

            conn.commit()

        except sqlite3.IntegrityError:
            flash("Email already in use!")
            return redirect('/register')

        # grab id of the new user that just registered
        userID = cursor.lastrowid

        # create response (respose is anything like a redirect, or render template) - this response reidrects to the '/' route
        response = make_response(redirect('/'))

        # set cookie for browser to hold it for 30 days
        response.set_cookie('userID', str(userID), max_age = 60*60*24*30)

        # return a cookie email for users to log in easier next time
        # this allows browsers to automatically remember emails for a 'click-and-choose' experience with logging in.
        response.set_cookie('email', email, max_age=60*60*24*30)

        # return the user to the redirect, with the created cookies used for logging in
        return response
    else:
        return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': # occurs when users attempt to login

        # set email & password as variables from html form
        email = request.form.get('email')
        password = request.form.get('password')

        # get database connection & create cursor for queries
        conn = get_db_connection()
        cursor = conn.cursor()

        # get the user information from the database
        user = cursor.execute('''
            SELECT * FROM users WHERE email = ?
        ''', (email)).fetchone()

        # now we need to check if the users email & password match

        # if they do match, log in

        # if they don't match, do not log in & redirect back to login with error message 'incorrect email & password combo'





if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')

    # redirect(url_for('example')) looks up the function name associated with a route
    # it activates & routes to the def ...()
    # redirect('example') tells the browser to go to a specfic route