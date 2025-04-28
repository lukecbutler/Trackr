from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from betterDataExtract import getAllLinesFromPDF, extractTableContent
import os

app = Flask(__name__)
app.secret_key = 'password'  # Replace with secure key in production
DATABASE = "shirts.db"

# Configure upload settings
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shirts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            description TEXT NOT NULL,
            color TEXT NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route("/", methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('home'))
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                           (username, hashed_password))
                conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
    return render_template('register.html')

@app.route('/home', methods=['GET'])
def home():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    shirts = conn.execute('''
        SELECT id, brand, description, color, size, quantity 
        FROM shirts 
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template("index.html", shirts=shirts)

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    shirt_id = request.form['id']
    action = request.form['action']
    
    conn = get_db_connection()
    try:
        # Verify shirt belongs to user
        shirt = conn.execute('''
            SELECT quantity FROM shirts 
            WHERE id = ? AND user_id = ?
        ''', (shirt_id, session['user_id'])).fetchone()
        
        if not shirt:
            flash('Shirt not found', 'error')
            return redirect(url_for('home'))
        
        current_quantity = shirt['quantity']
        
        if action == 'increment':
            new_quantity = current_quantity + 1
        elif action == 'decrement':
            new_quantity = max(0, current_quantity - 1)
        
        if new_quantity == 0:
            conn.execute('DELETE FROM shirts WHERE id = ? AND user_id = ?', 
                       (shirt_id, session['user_id']))
            flash('Shirt removed from inventory', 'success')
        else:
            conn.execute('''
                UPDATE shirts
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (new_quantity, shirt_id, session['user_id']))
            flash('Quantity updated successfully', 'success')
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'Error updating quantity: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('home'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        flash('Please log in to upload files', 'error')
        return redirect(url_for('login'))
    
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
        # Secure filename handling
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        allLines = getAllLinesFromPDF(filename)
        pdfTableData = extractTableContent(allLines)
        
        if not pdfTableData:
            flash('No valid data found in the PDF', 'error')
            return redirect(url_for('home'))
        
        shirtsToDatabase(pdfTableData, session['user_id'])
        flash('File successfully processed and data imported', 'success')
        
        # Clean up the uploaded file
        os.remove(filename)
        
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
    
    return redirect(url_for('home'))

def shirtsToDatabase(pdfTableData, user_id):
    conn = get_db_connection()
    try:
        for shirt in pdfTableData:
            brand, description, color, size, quantity = shirt

            existing_shirt = conn.execute('''
                SELECT id, quantity FROM shirts
                WHERE description = ? AND color = ? AND size = ? AND user_id = ?
            ''', (description, color, size, user_id)).fetchone()

            if existing_shirt:
                new_quantity = existing_shirt['quantity'] + int(quantity)
                conn.execute('''
                    UPDATE shirts
                    SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (new_quantity, existing_shirt['id'], user_id))
            else:
                conn.execute('''
                    INSERT INTO shirts 
                    (brand, description, color, size, quantity, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (brand, description, color, size, int(quantity), user_id))
        
        conn.commit()
    finally:
        conn.close()

@app.route('/edit_shirt/<int:shirt_id>', methods=['GET', 'POST'])
def edit_shirt(shirt_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            brand = request.form['brand']
            description = request.form['description']
            color = request.form['color']
            size = request.form['size']
            quantity = request.form['quantity']
            
            conn.execute('''
                UPDATE shirts
                SET brand = ?, description = ?, color = ?, size = ?, 
                    quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (brand, description, color, size, quantity, shirt_id, session['user_id']))
            
            conn.commit()
            flash('Shirt details updated successfully', 'success')
            return redirect(url_for('home'))
        
        shirt = conn.execute('''
            SELECT * FROM shirts 
            WHERE id = ? AND user_id = ?
        ''', (shirt_id, session['user_id'])).fetchone()
        
        if not shirt:
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
    except Exception as e:
        conn.rollback()
        flash(f'Error updating shirt: {str(e)}', 'error')
        return redirect(url_for('home'))
    finally:
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=80, host='0.0.0.0')