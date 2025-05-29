from flask import Flask, render_template, request, redirect, flash, url_for
import os
from flask_mailman import Mail, EmailMessage
from itsdangerous import URLSafeTimedSerializer
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

# Local modules (each will define a route handler function)
from auth import login, logout, register
from inventory import home, updateQuantity, manual_shirt_entry, upload, deleteSelected
from landing import landingPage
from resetPassword import accountRecoveryEmail, sendRecoveryEmail, resetPassword

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Upload folder for storing PDFs
uploadFolder = 'pdfsStoredOnServer'
os.makedirs(uploadFolder, exist_ok=True)

# create the serializer - this generates secure tokens
serializer = URLSafeTimedSerializer(app.secret_key)

# configure sending email for password resets
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'trackrbiz@gmail.com'
app.config['MAIL_PASSWORD'] = 'jrht uzci wzca wiht'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'trackrbiz@gmail.com'

####### ACCOUNT RECOVERY ##########
mail = Mail()
mail.init_app(app)



###########################  BASE ROUTES  ###############################
# base route that shows landing page if user is not logged in
app.add_url_rule('/', view_func=landingPage)

app.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/register', view_func=register, methods=['GET', 'POST'])
app.add_url_rule('/home', view_func=home, methods=['GET'])

# updates quantity of shirt via increment/decrement button, reroutes to /home
app.add_url_rule('/updateQuantity', view_func=updateQuantity, methods=['POST'])

# manually adds shirt, reroutes to /home
app.add_url_rule('/manual_shirt_entry', view_func=manual_shirt_entry, methods=['GET', 'POST'])

# handles file upload, reroutes to /home
app.add_url_rule('/upload', view_func=upload, methods=['POST'])

# handles mass deletion by user
app.add_url_rule('/deleteSelected', view_func=deleteSelected, methods=['GET','POST'])


def sendRecoveryEmailRoute():
    return sendRecoveryEmail(serializer)

def resetPasswordRoute(token):
    return resetPassword(token, serializer)

# password recovery routes
app.add_url_rule('/accountRecoveryEmail', view_func=accountRecoveryEmail, methods=['GET', 'POST'])
app.add_url_rule('/sendRecoveryEmail', view_func=sendRecoveryEmailRoute, methods=['GET', 'POST'])
app.add_url_rule('/resetPassword/<token>', view_func=resetPasswordRoute, methods=['GET', 'POST'])

if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')