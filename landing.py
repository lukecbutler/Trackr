from flask import request, render_template, redirect

"""
Display the landing page or redirect logged-in users to their home page.

Checks for a 'userID' cookie:
- If present, redirects to the '/home' route.
- Otherwise, renders the 'landingPage.html' template.

Parameters:
    None (relies on cookies from the request).

Returns:
    A redirect response to '/home' or the rendered landing page HTML.
"""

def landingPage():
    # if user has a cookie, send them to home page
    userID = request.cookies.get('userID')
    if userID:
        return redirect('/home')
    
    # otherwise, show them the welcome / landing page
    return render_template('landingPage.html')
