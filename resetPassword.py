from flask import Flask, render_template, request, redirect, flash, url_for
import os
from flask_mailman import Mail, EmailMessage
from itsdangerous import URLSafeTimedSerializer
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash



# renders account recovery email page which the user enters their email into
def accountRecoveryEmail():
    return render_template('accountRecoveryEmail.html')


# Logic that takes in user Email & sends password recovery token
def sendRecoveryEmail(serializer):
    # get users email for recovery
    email = request.form.get('email')

    # create the token the user will click on to be taken to password reset
    token = serializer.dumps(email, salt = "password-reset")

    # create the url the user will click on to reset their password
    resetURL = f"https://trackrbiz.pythonanywhere.com/resetPassword/{token}"

    # the email that is sent
    msg = EmailMessage(
        subject='Password Recovery',
        body = f"Click the link to reset your password: {resetURL}",
        to=[email]
    )

    # send the mail
    msg.send()

    print(f'Sending recovery email to: {email}')
    return render_template('emailSent.html')


def resetPassword(token, serializer):

    # try to decrypt the users email from the token
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except Exception as e:
        return "<h2>Invalid or expired token. Please go back.</h2>"

    # logic for when user submits new password form
    if request.method == 'POST':

        # get passwords from html form
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # check if passwords match
        if password1 != password2:
            flash('Passwords did not matchy match!')
            return redirect(f"https://trackrbiz.pythonanywhere.com/resetPassword/{token}")

        # hash password
        hashedPassword = generate_password_hash(password1)

        # update password of user based on email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET password = ?
            WHERE email = ?
        ''', (hashedPassword, email))
        conn.commit()
        conn.close()

        # redirect user to login after they reset their password
        flash('Password reset successful! Please log in with your new password.')
        return redirect('/login')

    # reset password html form page 
    else:
        return render_template('resetPasswordForm.html')
