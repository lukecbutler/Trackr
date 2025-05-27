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

    # get argument that describes how to sort the inventory
    sortBy = request.args.get('sortBy', 'brand') 

    # order is pulled from the url - pulls 'order' from the url argument. 'asc' is the default value
    sortOrder = request.args.get('order', 'asc')

    # get optional search query from the URL (e.g., ?search=blue)
    search = request.args.get('search', '')

    # SQL INJECTION PROTECTION
    # If url argument is tampered with, default to 'brand'
    if sortBy not in ['brand', 'description', 'color', 'size', 'quantity']:
        sortBy = 'brand'

    # Only allow 'asc' or 'desc'
    if sortOrder not in ['asc', 'desc']:
        sortOrder = 'asc'

    # Connect to database and show user's shirt inventory
    conn = get_db_connection()
    cursor = conn.cursor()

    # Handle custom sort order for size
    if sortBy == 'size':
        order_clause = f'''
            ORDER BY CASE size
                WHEN 'NB' THEN 1
                WHEN '0-3M' THEN 2
                WHEN '3-6M' THEN 3
                WHEN '6-9M' THEN 4
                WHEN '12M' THEN 5
                WHEN '18M' THEN 6
                WHEN '24M' THEN 7
                WHEN '2T' THEN 8
                WHEN '3T' THEN 9
                WHEN '4T' THEN 10
                WHEN '5T' THEN 11
                WHEN 'XS' THEN 12
                WHEN 'S' THEN 13
                WHEN 'M' THEN 14
                WHEN 'L' THEN 15
                WHEN 'XL' THEN 16
                WHEN '2XL' THEN 17
                WHEN '3XL' THEN 18
                WHEN '4XL' THEN 19
                ELSE 20
            END {sortOrder}
        '''
    else:
        order_clause = f'ORDER BY {sortBy} {sortOrder}'

    # If a search term was entered, use LIKE to match any partial matches in brand, description, color, or size
    if search:
        search_query = f"%{search}%"
        shirts = cursor.execute(f'''
            SELECT id, brand, description, color, size, quantity 
            FROM shirts 
            WHERE userID = ?
            AND (
                brand LIKE ? OR
                description LIKE ? OR
                color LIKE ? OR
                size LIKE ?
            )
            {order_clause};
        ''', (userID, search_query, search_query, search_query, search_query)).fetchall()
    else:
        shirts = cursor.execute(f'''
            SELECT id, brand, description, color, size, quantity 
            FROM shirts 
            WHERE userID = ?
            {order_clause};
        ''', (userID,)).fetchall()

    conn.close()
    
    # Pass search term to template so it can stay in the search box
    return render_template("index.html", shirts=shirts, search=search)


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

    # check if shirt already exists (same description, color, size, and user)
    cursor.execute('''
        SELECT id, quantity FROM shirts
        WHERE description = ? AND color = ? AND size = ? AND userID = ?
    ''', (description, color, size, userID))
    existing = cursor.fetchone()

    if existing:
        # if it does, update the quantity
        new_quantity = existing['quantity'] + int(quantity)
        cursor.execute('UPDATE shirts SET quantity = ? WHERE id = ?', (new_quantity, existing['id']))
    else:
        # if it doesn't, insert the new shirt
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
