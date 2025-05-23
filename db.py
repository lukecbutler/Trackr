import sqlite3

DATABASE = "shirts.db"


"""
Creates and returns a SQLite database connection with row access by column name.

Returns:
    sqlite3.Connection: A connection object to the database.
"""
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # allows accessing columns by name
    return conn


'''
Parameters:
    pdfData (list): A list of shirts, where each shirt is a list or tuple in the form:
                    [brand, description, color, size, quantity]
    userID (int): The ID of the user who owns the shirts. Used to associate shirts with the correct user.

Behavior:
    - If a shirt with the same description, color, size, and userID exists,
        its quantity is increased by the incoming amount.
    - If the shirt does not exist, it is inserted as a new record.
'''
def pdfDataToDatabase(pdfData, userID):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(pdfData)

    # go through each shirt in the table data
    for shirt in pdfData:
        brand, description, color, size, quantity = shirt

        # check if this shirt already exists in the database
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
