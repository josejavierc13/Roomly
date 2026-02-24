from flask import Blueprint

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return "<h1>Welcome to Roomly!</h1><p>Your ultimate room booking solution.</p>" 
