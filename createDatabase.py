import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("shirts.db")
cursor = conn.cursor()

# Create the Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstName TEXT NOT NULL,
    lastName TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT
);
''')

# Create the Shirts table with user_id foreign key
cursor.execute('''
CREATE TABLE IF NOT EXISTS shirts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    description TEXT NOT NULL,
    color TEXT NOT NULL,
    size TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
''')

# Create shirt log table
cursor.execute('''
CREATE TABLE IF NOT EXISTS shirt_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shirt_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    quantity_change INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shirt_id) REFERENCES shirts(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
'''
)

conn.commit()
conn.close()