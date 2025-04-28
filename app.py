from flask import Flask, request, render_template, redirect, jsonify, flash, session, url_for
from betterDataExtract import getAllLinesFromPDF, extractTableContent
import sqlite3
import os
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    shirts = conn.execute('SELECT * FROM shirts WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('index.html', shirts=shirts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                          (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                        (username, password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/update_quantity', methods=['POST'])
@login_required
def update_quantity():
    shirt_id = request.form['id']
    action = request.form['action']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current quantity
        cursor.execute('SELECT quantity FROM shirts WHERE id = ? AND user_id = ?', (shirt_id, session['user_id']))
        shirt = cursor.fetchone()
        
        if not shirt:
            return jsonify({'message': 'Shirt not found'}), 404
        
        current_quantity = shirt['quantity']
        
        # Update based on action
        if action == 'increment':
            new_quantity = current_quantity + 1
        elif action == 'decrement':
            new_quantity = max(0, current_quantity - 1)  # Prevent negative quantities
        
        if new_quantity == 0:
            # Delete the shirt if quantity reaches 0
            cursor.execute('DELETE FROM shirts WHERE id = ? AND user_id = ?', (shirt_id, session['user_id']))
            message = 'Shirt removed from inventory'
        else:
            # Update quantity if not zero
            cursor.execute('''
                UPDATE shirts
                SET quantity = ?
                WHERE id = ? AND user_id = ?
            ''', (new_quantity, shirt_id, session['user_id']))
            message = 'Quantity updated successfully'
        
        conn.commit()
        return jsonify({
            'message': message,
            'new_quantity': new_quantity
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Error updating quantity: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/delete_shirt', methods=['POST'])
@login_required
def delete_shirt():
    shirt_id = request.form['id']
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM shirts WHERE id = ? AND user_id = ?', (shirt_id, session['user_id']))
        conn.commit()
        flash('Shirt deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting shirt: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a PDF file.', 'error')
        return redirect(url_for('index'))
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Get lines of data from the PDF
        allLines = getAllLinesFromPDF(filepath)
        
        # Clean the lines of shirts & return needed data
        pdfTableData = extractTableContent(allLines)
        
        if not pdfTableData:
            flash('No valid data found in the PDF', 'error')
            return redirect(url_for('index'))
        
        # Add shirts to database with user_id
        conn = get_db_connection()
        for shirt in pdfTableData:
            brand, description, color, size, quantity = shirt
            conn.execute('''
                INSERT INTO shirts (brand, description, color, size, quantity, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (brand, description, color, size, int(quantity), session['user_id']))
        
        conn.commit()
        conn.close()
        
        flash('File successfully processed and data imported', 'success')
        
        # Clean up the uploaded file
        os.remove(filepath)
        
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/edit_shirt/<int:shirt_id>', methods=['GET', 'POST'])
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
            
            # Get current quantity for audit trail
            cursor.execute('SELECT quantity FROM shirts WHERE id = ?', (shirt_id,))
            current_quantity = cursor.fetchone()['quantity']
            
            # Update shirt details
            cursor.execute('''
                UPDATE shirts
                SET brand = ?, description = ?, color = ?, size = ?, quantity = ?
                WHERE id = ?
            ''', (brand, description, color, size, quantity, shirt_id))
            
            # Record the change in audit trail if quantity changed
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
        return redirect('/')
    
    # GET request - fetch shirt details
    shirt = cursor.execute('SELECT * FROM shirts WHERE id = ?', (shirt_id,)).fetchone()
    conn.close()
    
    if shirt is None:
        flash('Shirt not found', 'error')
        return redirect('/')
    
    return jsonify({
        'id': shirt['id'],
        'brand': shirt['brand'],
        'description': shirt['description'],
        'color': shirt['color'],
        'size': shirt['size'],
        'quantity': shirt['quantity']
    })

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')