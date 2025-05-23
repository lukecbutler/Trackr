from flask import request, redirect, render_template
from SSpdfDataExtraction import processPDF
from db import get_db_connection, pdfDataToDatabase
import os

uploadFolder = 'pdfsStoredOnServer'

"""
Display the logged-in user's shirt inventory.

Parameters:
    None (relies on userID cookie)

Behavior:
    - Queries database for user's shirts.
    - Renders inventory template with shirt data.
"""
def home():
    # get the user id from the cookie
    userID = request.cookies.get('userID')
    
    # if user doesn't have a cookie, they need to login first
    if not userID:
        return redirect('/login')

    # if they do, then connect to database and show their shirt inventory
    conn = get_db_connection()
    cursor = conn.cursor()

    shirts = cursor.execute('''
        SELECT id, brand, description, color, size, quantity 
        FROM shirts 
        WHERE userID = ?;
    ''', (userID,)).fetchall()

    conn.close()
    return render_template("index.html", shirts=shirts)

"""
Update quantity of a shirt or delete it if quantity reaches zero.

Parameters:
    id (from form): Shirt ID
    action (from form): 'increment' or 'decrement'

Behavior:
    - Adjusts shirt quantity in database based on action.
    - Deletes shirt if quantity reaches zero.
    - Redirects back to inventory page.
"""
def update_quantity():
    # Get data from form
    shirt_id = request.form['id']
    action = request.form['action']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current quantity of the shirt
    current_quantity = cursor.execute(
        'SELECT quantity FROM shirts WHERE id = ?', (shirt_id,)
    ).fetchone()['quantity']

    # Adjust quantity up or down based on the action
    if action == 'increment':
        new_quantity = current_quantity + 1
    elif action == 'decrement':
        new_quantity = max(0, current_quantity - 1)

    # If the new quantity is 0, delete the shirt
    if new_quantity == 0:
        cursor.execute('DELETE FROM shirts WHERE id = ?', (shirt_id,))
    else:
        cursor.execute('UPDATE shirts SET quantity = ? WHERE id = ?', (new_quantity, shirt_id))

    conn.commit()
    conn.close()

    return redirect('/')

"""
Add a single shirt entry manually via form.

Parameters:
    brand, description, color, size, quantity (from form)
    userID (from cookie)

Behavior:
    - Inserts new shirt into database for the logged-in user.
    - Redirects to inventory page.
"""
def manual_shirt_entry():
    from flask import request
    conn = get_db_connection()
    cursor = conn.cursor()

    # get data from form
    brand = request.form.get('brand')
    description = request.form.get('description')
    color = request.form.get('color')
    size = request.form.get('size')
    quantity = request.form.get('quantity')

    # get userID from cookie
    userID = request.cookies.get('userID')
    if userID:
        userID = int(userID)

    # add shirt to database
    cursor.execute('''
        INSERT INTO shirts (brand, description, color, size, quantity, userID)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (brand, description, color, size, int(quantity), userID))

    conn.commit()
    conn.close()

    return redirect('/')

"""
Handle PDF upload and imports shirt data.

Parameters:
    file (from form upload)
    userID (from cookie)

Behavior:
    - Saves uploaded PDF to server.
    - Extracts shirt data from PDF via other helper methods.
    - Adds extracted shirts to database for the user.
    - Redirects to the home page.
"""
def upload():
    # get file from form
    file = request.files['file']
    if not file:
        return redirect('/')

    # save file to server
    filePath = os.path.join(uploadFolder, file.filename)
    file.save(filePath)

    # extract shirt data from the PDF
    pdfData = processPDF(filePath)

    # get userID from cookie
    userID = request.cookies.get('userID')
    if userID:
        userID = int(userID)

    # insert shirt data (pdf data as a list of list) into database
    pdfDataToDatabase(pdfData, userID)

    return redirect("/")