from flask import Flask, render_template, request, redirect, flash, url_for
import os
from flask_mailman import Mail, EmailMessage
from itsdangerous import URLSafeTimedSerializer
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

# Local modules (each will define a route handler function)
from auth import login, logout, register
from inventory import home, update_quantity, manual_shirt_entry, upload
from landing import landingPage

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Upload folder for storing PDFs
uploadFolder = 'pdfsStoredOnServer'
os.makedirs(uploadFolder, exist_ok=True)


"""START EMAIL STUFF""" 

# Email configuration - Gmail
# app password = 'dkbw ynga jvfd gqjx'
# Mail configuration (example: Gmail SMTP)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'trackrbiz@gmail.com'
app.config['MAIL_PASSWORD'] = 'jrht uzci wzca wiht'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'trackrbiz@gmail.com'

####### ACCOUNT RECOVERY

mail = Mail()
mail.init_app(app)

# create the serializer - this generates secure tokens
serializer = URLSafeTimedSerializer(app.secret_key)



# renders account recovery email page which the user enters their email into
@app.route('/accountRecoveryEmail', methods=['GET', 'POST'])
def accountRecoveryEmail():
    return render_template('accountRecoveryEmail.html')

# Logic that takes in user Email & sends password recovery token
@app.route('/sendRecoveryEmail', methods=['GET', 'POST'])
def sendRecoveryEmail():
    # get users email for recovery
    email = request.form.get('email')

    # create the token the user will click on to be taken to password reset
    token = serializer.dumps(email, salt = "password-reset")

    # create the url the user will click on to reset their password
    resetURL = f"http://0.0.0.0/resetPassword/{token}"

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


@app.route('/resetPassword/<token>', methods=['GET', 'POST'])
def resetPassword(token):

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
            return redirect(f"http://0.0.0.0/resetPassword/{token}")

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






"""END RESET EMAIL """ 

'''Register routes using add_url_rule'''
###########################  BASE ROUTES  ###############################
# base route that shows landing page if user is not logged in
app.add_url_rule('/', view_func=landingPage)

app.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/register', view_func=register, methods=['GET', 'POST'])
app.add_url_rule('/home', view_func=home, methods=['GET'])

# updates quantity of shirt via increment/decrement button, reroutes to /home
app.add_url_rule('/update_quantity', view_func=update_quantity, methods=['POST'])

# manually adds shirt, reroutes to /home
app.add_url_rule('/manual_shirt_entry', view_func=manual_shirt_entry, methods=['GET', 'POST'])

# handles file upload, reroutes to /home
app.add_url_rule('/upload', view_func=upload, methods=['POST'])

 
if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')