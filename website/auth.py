from flask import Blueprint, render_template

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('log-in.html') # Render the log-in.html template when the /login route is accessed

@auth.route('/signup')
def signup():
    return render_template('sign-up.html') # Render the sign-up.html template when the /signup route is accessed

@auth.route('/logout')
def logout():
    return "<h1>Logout</h1><p>You have been logged out successfully.</p>"