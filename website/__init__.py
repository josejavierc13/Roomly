import os
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _default_sqlite_uri(app):
    db_path = os.path.normpath(os.path.join(app.root_path, '..', 'DATABASE', 'roomly.db'))
    normalized_path = db_path.replace('\\', '/')
    return f"sqlite:///{normalized_path}"


def _init_sqlite_schema_if_needed(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

    db_path = db_uri.replace('sqlite:///', '', 1)
    if os.path.exists(db_path):
        return

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    schema_path = os.path.normpath(os.path.join(app.root_path, '..', 'DATABASE', 'Roomly.sql'))
    if not os.path.exists(schema_path):
        return

    with open(schema_path, 'r', encoding='utf-8') as schema_file:
        schema_sql = schema_file.read()

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def _ensure_property_images_table(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS PROPERTY_IMAGES (
        image_id_pk int PRIMARY KEY,
        image_url varchar(255) NOT NULL,
        property_id_fk int NOT NULL,
        FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk)
    );
    '''

    with sqlite3.connect(db_path) as conn:
        conn.execute(create_table_sql)
        conn.commit()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or _default_sqlite_uri(app)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    _init_sqlite_schema_if_needed(app)
    _ensure_property_images_table(app)
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    
    return app