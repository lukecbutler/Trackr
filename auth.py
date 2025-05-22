from flask import request, render_template, redirect, flash, make_response, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
import sqlite3



"""
Handle user registration.

Parameters:
    None (uses form data from POST request)

Behavior:
    - Validates matching passwords.
    - Hashes password.
    - Inserts new user into database.
    - Sets cookies for userID and email.
    - Redirects to home on success.
    - Flashes errors and redirects on failure.
"""
def register():
    if request.method == 'POST':
        # get form data
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # check if passwords match
        if password1 != password2:
            flash('Passwords did not matchy match!')
            return redirect('/register')

        # hash password
        hashedPassword = generate_password_hash(password1)

        try:
            # insert new user into database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (firstName, lastName, email, password)
                VALUES (?, ?, ?, ?)
            ''', (firstName, lastName, email, hashedPassword))
            conn.commit()
            userID = cursor.lastrowid
            conn.close()
        except sqlite3.IntegrityError:
            # email already in use
            flash("Email already in use!")
            return redirect('/register')

        # set cookie and send them home
        response = make_response(redirect('/'))
        response.set_cookie('userID', str(userID), max_age=60*60*24*30)
        response.set_cookie('email', email, max_age=60*60*24*30)
        return response

    return render_template('register.html')



"""
Handle user login.

Parameters:
    None (uses form data from POST request)

Behavior:
    - Fetches user by email.
    - Checks password hash.
    - Sets userID cookie and redirects on success.
    - Flashes errors and re-renders login on failure.
"""
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # check if user exists
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if not user:
            flash('no user found!')
            return render_template('login.html')

        # check if passwords match
        if user and check_password_hash(user['password'], password):
            resp = make_response(redirect(url_for('home')))
            resp.set_cookie('userID', str(user['id']), max_age=60*60*24*30)
            return resp
        else:
            flash('email & password do not match!')
            return render_template('login.html')

    return render_template('login.html')



"""
Log out user.

Parameters:
    None

Behavior:
    - Clears userID cookie.
    - Redirects to landing page.
"""
def logout():
    resp = make_response(redirect(url_for('landingPage')))
    resp.set_cookie('userID', '', expires=0)
    return resp
