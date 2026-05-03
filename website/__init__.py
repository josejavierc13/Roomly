import os
import sqlite3
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _default_sqlite_uri(app):
    db_path = os.path.normpath(os.path.join(app.root_path, 'DATABASE', 'roomly.db'))
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
    schema_path = os.path.normpath(os.path.join(app.root_path, 'DATABASE', 'Roomly.sql'))
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


def _ensure_account_type_column(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(ACCOUNT);').fetchall()
        column_names = {column[1].lower() for column in columns}

        if 'account_type' not in column_names:
            conn.execute("ALTER TABLE ACCOUNT ADD COLUMN account_type VARCHAR(20) NOT NULL DEFAULT 'STUDENT';")
            conn.commit()


def _ensure_account_city_column(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(ACCOUNT);').fetchall()
        column_names = {column[1].lower() for column in columns}

        if 'city' not in column_names:
            conn.execute('ALTER TABLE ACCOUNT ADD COLUMN city VARCHAR(255);')
            conn.commit()


def _ensure_property_details_columns(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(PROPERTY);').fetchall()
        column_names = {column[1].lower() for column in columns}

        if 'number_of_bathrooms' not in column_names:
            conn.execute('ALTER TABLE PROPERTY ADD COLUMN number_of_bathrooms INTEGER NOT NULL DEFAULT 1;')

        if 'amenities' not in column_names:
            conn.execute('ALTER TABLE PROPERTY ADD COLUMN amenities TEXT;')

        conn.commit()


def _ensure_amenities_tables(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

    create_amenities_sql = '''
    CREATE TABLE IF NOT EXISTS AMENITIES (
        amenity_id_pk int PRIMARY KEY,
        name varchar(255) NOT NULL
    );
    '''

    create_property_amenity_sql = '''
    CREATE TABLE IF NOT EXISTS PROPERTY_AMENITY (
        property_id_pk_fk int,
        amenity_id_pk_fk int,
        PRIMARY KEY (property_id_pk_fk, amenity_id_pk_fk),
        FOREIGN KEY (property_id_pk_fk) REFERENCES PROPERTY(property_id_pk),
        FOREIGN KEY (amenity_id_pk_fk) REFERENCES AMENITIES(amenity_id_pk)
    );
    '''

    with sqlite3.connect(db_path) as conn:
        conn.execute(create_amenities_sql)
        conn.execute(create_property_amenity_sql)
        conn.commit()


def _ensure_reservations_table(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

    create_reservations_sql = '''
    CREATE TABLE IF NOT EXISTS PROPERTY_RESERVATION (
        reservation_id_pk int PRIMARY KEY,
        property_id_fk int NOT NULL,
        account_id_fk int NOT NULL,
        reserved_at datetime NOT NULL,
        status varchar(30) NOT NULL,
        FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk)
    );
    '''

    with sqlite3.connect(db_path) as conn:
        conn.execute(create_reservations_sql)
        conn.commit()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or _default_sqlite_uri(app)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

    _init_sqlite_schema_if_needed(app)
    _ensure_property_images_table(app)
    _ensure_account_type_column(app)
    _ensure_account_city_column(app)
    _ensure_reservations_table(app)
    _ensure_property_details_columns(app)
    _ensure_amenities_tables(app)
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    
    return app