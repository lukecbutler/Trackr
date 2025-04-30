from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from betterDataExtract import getAllLinesFromPDF, extractTableContent

app = Flask(__name__)
app.secret_key = 'password'  # TODO: Replace this with a strong secret key in production

DATABASE = "shirts.db"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Set up app configs
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---- Helper Functions ----

def get_db_connection():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Check if uploaded file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Initialize database tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
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
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def user_logged_in():
    """Check if a user is logged in."""
    return 'user_id' in session

# ---- Routes ----

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))

        flash("Invalid username or password", "error")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/home")
def home():
    if not user_logged_in():
        flash("Please log in to access the home page.", "error")
        return redirect(url_for("login"))

    conn = get_db_connection()
    shirts = conn.execute(
        'SELECT id, brand, description, color, size, quantity FROM shirts WHERE user_id = ?', 
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("index.html", shirts=shirts)

@app.route("/upload", methods=["POST"])
def upload():
    if not user_logged_in():
        flash("Please log in to upload files.", "error")
        return redirect(url_for("login"))

    file = request.files.get("file")

    # if there is no file flask No file selected & redirect to home
    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("home"))

    # if any other file type than a pdf is uploaded flash the error & redirect to home
    if not allowed_file(file.filename):
        flash("Invalid file type. Only PDF files are allowed.", "error")
        return redirect(url_for("home"))


    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    all_lines = getAllLinesFromPDF(filepath)
    pdf_data = extractTableContent(all_lines)

    if not pdf_data:
        flash("No valid data found in the PDF.", "error")
        os.remove(filepath)
        return redirect(url_for("home"))

    save_shirts_to_database(pdf_data, session["user_id"])

    flash("File successfully processed and data imported!", "success")
    os.remove(filepath)
    return redirect(url_for("home"))

def save_shirts_to_database(pdf_data, user_id):
    """Save extracted shirt data to the database."""
    conn = get_db_connection()

    for shirt in pdf_data:
        brand, description, color, size, quantity = shirt

        existing_shirt = conn.execute('''
            SELECT id, quantity FROM shirts 
            WHERE description = ? AND color = ? AND size = ? AND user_id = ?
        ''', (description, color, size, user_id)).fetchone()

        if existing_shirt:
            new_quantity = existing_shirt["quantity"] + int(quantity)
            conn.execute('''
                UPDATE shirts 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            ''', (new_quantity, existing_shirt["id"], user_id))
        else:
            conn.execute('''
                INSERT INTO shirts (brand, description, color, size, quantity, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (brand, description, color, size, int(quantity), user_id))

    conn.commit()
    conn.close()

@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    if not user_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    shirt_id = request.form.get("id")
    action = request.form.get("action")

    conn = get_db_connection()
    shirt = conn.execute(
        'SELECT quantity FROM shirts WHERE id = ? AND user_id = ?', 
        (shirt_id, session["user_id"])
    ).fetchone()

    if not shirt:
        conn.close()
        flash("Shirt not found.", "error")
        return redirect(url_for("home"))

    quantity = shirt["quantity"]

    if action == "increment":
        quantity += 1
    elif action == "decrement":
        quantity = max(0, quantity - 1)

    if quantity == 0:
        conn.execute('DELETE FROM shirts WHERE id = ? AND user_id = ?', (shirt_id, session["user_id"]))
        flash("Shirt removed from inventory.", "success")
    else:
        conn.execute('''
            UPDATE shirts 
            SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (quantity, shirt_id, session["user_id"]))
        flash("Quantity updated successfully!", "success")

    conn.commit()
    conn.close()
    return redirect(url_for("home"))

@app.route("/edit_shirt/<int:shirt_id>", methods=["GET", "POST"])
def edit_shirt(shirt_id):
    if not user_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()

    if request.method == "POST":
        brand = request.form.get("brand")
        description = request.form.get("description")
        color = request.form.get("color")
        size = request.form.get("size")
        quantity = request.form.get("quantity")

        conn.execute('''
            UPDATE shirts 
            SET brand = ?, description = ?, color = ?, size = ?, quantity = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (brand, description, color, size, quantity, shirt_id, session["user_id"]))

        conn.commit()
        conn.close()

        flash("Shirt details updated successfully!", "success")
        return redirect(url_for("home"))

    shirt = conn.execute(
        'SELECT * FROM shirts WHERE id = ? AND user_id = ?', 
        (shirt_id, session["user_id"])
    ).fetchone()
    conn.close()

    if not shirt:
        flash("Shirt not found.", "error")
        return redirect(url_for("home"))

    return jsonify(dict(shirt))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

# ---- Main ----
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=80, host="0.0.0.0")
