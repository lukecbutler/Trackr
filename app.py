from flask import Flask, request, render_template, redirect, jsonify, flash, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from betterDataExtract import getAllLinesFromPDF, extractTableContent
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for flash messages and session

# Database connection
DATABASE = "shirts.db"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Create the shirts table with indexes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shirts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            description TEXT NOT NULL,
            color TEXT NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for frequently queried columns
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shirts_brand ON shirts(brand)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shirts_description ON shirts(description)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shirts_color ON shirts(color)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shirts_size ON shirts(size)')
    
    # Create audit trail table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shirt_id INTEGER,
            old_quantity INTEGER,
            new_quantity INTEGER,
            change_type TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shirt_id) REFERENCES shirts(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Login required decorator with functools.wraps to preserve endpoint names
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Pull data from database - set as shirts variable
    shirts = cursor.execute('''
        SELECT id, brand, description, color, size, quantity FROM shirts;
    ''').fetchall()
    
    conn.close()
    return render_template("index.html", shirts=shirts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/update_quantity', methods=['POST'])
@login_required
def update_quantity():
    shirt_id = request.form['id']
    action = request.form['action']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT quantity FROM shirts WHERE id = ?', (shirt_id,))
        current_quantity = cursor.fetchone()['quantity']
        
        if action == 'increment':
            new_quantity = current_quantity + 1
        elif action == 'decrement':
            new_quantity = max(0, current_quantity - 1)
        
        if new_quantity == 0:
            cursor.execute('DELETE FROM shirts WHERE id = ?', (shirt_id,))
            flash('Shirt removed from inventory', 'success')
        else:
            cursor.execute('UPDATE shirts SET quantity = ? WHERE id = ?', (new_quantity, shirt_id))
            flash('Quantity updated successfully', 'success')
        
        cursor.execute('''
            INSERT INTO inventory_audit (shirt_id, old_quantity, new_quantity, change_type)
            VALUES (?, ?, ?, ?)
        ''', (shirt_id, current_quantity, new_quantity, action))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'Error updating quantity: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('home'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('home'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('home'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a PDF file.', 'error')
        return redirect(url_for('home'))
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        allLines = getAllLinesFromPDF(filepath)
        pdfTableData = extractTableContent(allLines)
        
        if not pdfTableData:
            flash('No valid data found in the PDF', 'error')
            return redirect(url_for('home'))
        
        shirtsToDatabase(pdfTableData)
        flash('File successfully processed and data imported', 'success')
        
        os.remove(filepath)
        
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('home'))
    
    return redirect(url_for('home'))

def shirtsToDatabase(pdfTableData):
    conn = get_db_connection()
    cursor = conn.cursor()

    for shirt in pdfTableData:
        brand, description, color, size, quantity = shirt

        cursor.execute('''
            SELECT id, quantity FROM shirts
            WHERE description = ? AND color = ? AND size = ?
        ''', (description, color, size))

        existing_shirt = cursor.fetchone()

        if existing_shirt:
            new_quantity = existing_shirt['quantity'] + int(quantity)
            cursor.execute('''
                UPDATE shirts
                SET quantity = ?
                WHERE id = ?
            ''', (new_quantity, existing_shirt['id']))
        else:
            cursor.execute('''
                INSERT INTO shirts (brand, description, color, size, quantity)
                VALUES (?, ?, ?, ?, ?)
            ''', (brand, description, color, size, int(quantity)))

    conn.commit()
    conn.close()

@app.route('/edit_shirt/<int:shirt_id>', methods=['GET', 'POST'])
@login_required
def edit_shirt(shirt_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        try:
            brand = request.form['brand']
            description = request.form['description']
            color = request.form['color']
            size = request.form['size']
            quantity = request.form['quantity']
            
            cursor.execute('SELECT quantity FROM shirts WHERE id = ?', (shirt_id,))
            current_quantity = cursor.fetchone()['quantity']
            
            cursor.execute('''
                UPDATE shirts
                SET brand = ?, description = ?, color = ?, size = ?, quantity = ?
                WHERE id = ?
            ''', (brand, description, color, size, quantity, shirt_id))
            
            if int(quantity) != current_quantity:
                cursor.execute('''
                    INSERT INTO inventory_audit (shirt_id, old_quantity, new_quantity, change_type)
                    VALUES (?, ?, ?, ?)
                ''', (shirt_id, current_quantity, quantity, 'edit'))
            
            conn.commit()
            flash('Shirt details updated successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error updating shirt: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('home'))
    
    shirt = cursor.execute('SELECT * FROM shirts WHERE id = ?', (shirt_id,)).fetchone()
    conn.close()
    
    if shirt is None:
        flash('Shirt not found', 'error')
        return redirect(url_for('home'))
    
    return jsonify({
        'id': shirt['id'],
        'brand': shirt['brand'],
        'description': shirt['description'],
        'color': shirt['color'],
        'size': shirt['size'],
        'quantity': shirt['quantity']
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=80, host='0.0.0.0')