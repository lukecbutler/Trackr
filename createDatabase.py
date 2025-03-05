import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("shirts.db")
cursor = conn.cursor()

# Create the Workouts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS shirts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    color TEXT NOT NULL,
    size TEXT NOT NULL,
    quantity INTEGER
);
''')