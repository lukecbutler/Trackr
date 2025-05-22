from flask import Flask
import os

# Local modules (each will define a route handler function)
from auth import login, logout, register
from inventory import home, update_quantity, manual_shirt_entry, upload
from landing import landingPage

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Upload folder for storing PDFs
uploadFolder = 'pdfsStoredOnServer'
os.makedirs(uploadFolder, exist_ok=True)

# Register routes using add_url_rule
app.add_url_rule('/', view_func=landingPage)
app.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/register', view_func=register, methods=['GET', 'POST'])
app.add_url_rule('/home', view_func=home, methods=['GET'])
app.add_url_rule('/update_quantity', view_func=update_quantity, methods=['POST'])
app.add_url_rule('/manual_shirt_entry', view_func=manual_shirt_entry, methods=['GET', 'POST'])
app.add_url_rule('/upload', view_func=upload, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')

    # redirect(url_for('example')) looks up the function name associated with a route
    # it activates & routes to the def ...()
    # redirect('example') tells the browser to go to a specfic route