from flask import Blueprint

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return "<h1>Login Page</h1><p>Please enter your credentials to log in.</p>"

@auth.route('/signup')
def signup():
    return "<h1>Sign Up Page</h1><p>Please fill in your details to create an account.</p>"

@auth.route('/logout')
def logout():
    return "<h1>Logout</h1><p>You have been logged out successfully.</p>"