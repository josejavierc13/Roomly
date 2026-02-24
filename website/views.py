from flask import Blueprint, render_template

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('index.html')

@views.route('/browse')
def browse():
    return "<h1>Browse Listings</h1><p>Explore available student housing options.</p>"

@views.route('/list-property')
def list_property():
    return "<h1>List Property</h1><p>Add your property details to get started.</p>"
