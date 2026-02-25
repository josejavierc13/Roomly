from flask import Blueprint, render_template

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('index.html')

@views.route('/browse')
def browse():
    return render_template('browse.html')

@views.route('/list-property')
def list_property():
    return render_template('list-property.html')
