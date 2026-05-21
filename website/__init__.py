import os
import sqlite3
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Helper function to generate default SQLite URI
def _default_sqlite_uri(app):
    db_path = os.path.normpath(os.path.join(app.root_path, 'DATABASE', 'roomly.db'))
    normalized_path = db_path.replace('\\', '/')
    return f"sqlite:///{normalized_path}"

# Function to initialize SQLite schema if the database file does not exist
def _init_sqlite_schema_if_needed(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if os.path.exists(db_path):
        return

# Ensure the directory for the database file exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    schema_path = os.path.normpath(os.path.join(app.root_path, 'DATABASE', 'Roomly.sql'))
    if not os.path.exists(schema_path):
        return

# Read the SQL schema from the file and execute it to create the database
    with open(schema_path, 'r', encoding='utf-8') as schema_file:
        schema_sql = schema_file.read()

# Connect to the SQLite database and execute the schema SQL
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()

# Ensure the PROPERTY_IMAGES table exists in the database
def _ensure_property_images_table(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return
    
# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return
# Create the PROPERTY_IMAGES table if it does not exist
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS PROPERTY_IMAGES (
        image_id_pk int PRIMARY KEY,
        image_url varchar(255) NOT NULL,
        property_id_fk int NOT NULL,
        FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk)
    );
    '''

# Connect to the SQLite database and execute the SQL to create the PROPERTY_IMAGES table
    with sqlite3.connect(db_path) as conn:
        conn.execute(create_table_sql)
        conn.commit()

# Ensure the ACCOUNT table has the account_type column, and add it if it does not exist
def _ensure_account_type_column(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

# Connect to the SQLite database and check if the account_type column exists in the ACCOUNT table
    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(ACCOUNT);').fetchall()
        column_names = {column[1].lower() for column in columns}

# If the account_type column does not exist, add it to the ACCOUNT table with a default value of 'STUDENT'
        if 'account_type' not in column_names:
            conn.execute("ALTER TABLE ACCOUNT ADD COLUMN account_type VARCHAR(20) NOT NULL DEFAULT 'STUDENT';")
            conn.commit()

# Ensure the ACCOUNT table has the city column, and add it if it does not exist
def _ensure_account_city_column(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

# Connect to the SQLite database and check if the city column exists in the ACCOUNT table
    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(ACCOUNT);').fetchall()
        column_names = {column[1].lower() for column in columns}

# If the city column does not exist, add it to the ACCOUNT table
        if 'city' not in column_names:
            conn.execute('ALTER TABLE ACCOUNT ADD COLUMN city VARCHAR(255);')
            conn.commit()

# Ensure the PROPERTY table has the number_of_bathrooms and amenities columns, and add them if they do not exist
def _ensure_property_details_columns(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

# Connect to the SQLite database and check if the number_of_bathrooms and amenities columns exist in the PROPERTY table
    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(PROPERTY);').fetchall()
        column_names = {column[1].lower() for column in columns}

# If the number_of_bathrooms column does not exist, add it to the PROPERTY table with a default value of 1
        if 'number_of_bathrooms' not in column_names:
            conn.execute('ALTER TABLE PROPERTY ADD COLUMN number_of_bathrooms INTEGER NOT NULL DEFAULT 1;')

# If the amenities column does not exist, add it to the PROPERTY table as a TEXT column to store comma-separated amenity names
        if 'amenities' not in column_names:
            conn.execute('ALTER TABLE PROPERTY ADD COLUMN amenities TEXT;')

        conn.commit()

# Ensure the AMENITIES and PROPERTY_AMENITY tables exist in the database
def _ensure_amenities_tables(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

# SQL statement to create the AMENITIES table if it does not exist
    create_amenities_sql = '''
    CREATE TABLE IF NOT EXISTS AMENITIES (
        amenity_id_pk int PRIMARY KEY,
        name varchar(255) NOT NULL
    );
    '''
# SQL statement to create the PROPERTY_AMENITY table if it does not exist, which links properties to their amenities
    create_property_amenity_sql = '''
    CREATE TABLE IF NOT EXISTS PROPERTY_AMENITY (
        property_id_pk_fk int,
        amenity_id_pk_fk int,
        PRIMARY KEY (property_id_pk_fk, amenity_id_pk_fk),
        FOREIGN KEY (property_id_pk_fk) REFERENCES PROPERTY(property_id_pk),
        FOREIGN KEY (amenity_id_pk_fk) REFERENCES AMENITIES(amenity_id_pk)
    );
    '''

# Connect to the SQLite database and execute the SQL statements to create the AMENITIES and PROPERTY_AMENITY tables
    with sqlite3.connect(db_path) as conn:
        conn.execute(create_amenities_sql)
        conn.execute(create_property_amenity_sql)
        conn.commit()

# Ensure the PROPERTY_RESERVATION table exists in the database
def _ensure_reservations_table(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return
    
# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

# SQL statement to create the PROPERTY_RESERVATION table if it does not exist, which stores reservation information for properties
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

# Connect to the SQLite database and execute the SQL statement to create the PROPERTY_RESERVATION table
    with sqlite3.connect(db_path) as conn:
        conn.execute(create_reservations_sql)
        conn.commit()

# Ensure the PROPERTY_RESERVATION table has the status column, and add it if it does not exist
def _ensure_reservation_status_column(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return
    
# Connect to the SQLite database and check if the status column exists in the PROPERTY_RESERVATION table
    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(PROPERTY_RESERVATION);').fetchall()
        column_names = {column[1].lower() for column in columns}

        if 'status' not in column_names:
            conn.execute("ALTER TABLE PROPERTY_RESERVATION ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'pending';")
            conn.commit()

# Ensure the REVIEW_PROPERTY table exists in the database, which stores reviews for properties
def _ensure_review_table(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

# SQL statement to create the REVIEW_PROPERTY table if it does not exist, which includes foreign keys to the PROPERTY, ACCOUNT, and STUDENT tables
    create_review_sql = '''
    CREATE TABLE IF NOT EXISTS REVIEW_PROPERTY (
        review_property_id_pk int PRIMARY KEY,
        property_id_fk int NOT NULL,
        account_id_fk int NOT NULL,
        student_id_fk int,
        rating int NOT NULL,
        comment text,
        date_posted datetime NOT NULL,
        FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk),
        FOREIGN KEY (account_id_fk) REFERENCES ACCOUNT(account_id_pk),
        FOREIGN KEY (student_id_fk) REFERENCES STUDENT(student_id_pk),
        UNIQUE (account_id_fk, property_id_fk)
    );
    '''

# Connect to the SQLite database and execute the SQL statement to create the REVIEW_PROPERTY table
    with sqlite3.connect(db_path) as conn:
        conn.execute(create_review_sql)
        conn.commit()

# Ensure the REVIEW_PROPERTY table has the account_id_fk and student_id_fk columns,
# and add them if they do not exist. Also, populate these columns based on existing data if possible.
def _ensure_review_account_column(app):
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('sqlite:///'):
        return

# Extract the database file path from the URI
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.exists(db_path):
        return

# Connect to the SQLite database and check if the account_id_fk and student_id_fk columns exist in the REVIEW_PROPERTY table
    with sqlite3.connect(db_path) as conn:
        columns = conn.execute('PRAGMA table_info(REVIEW_PROPERTY);').fetchall()
        column_names = {column[1].lower() for column in columns}

        if 'account_id_fk' not in column_names:
            conn.execute('ALTER TABLE REVIEW_PROPERTY ADD COLUMN account_id_fk INTEGER;')

        if 'student_id_fk' not in column_names:
            conn.execute('ALTER TABLE REVIEW_PROPERTY ADD COLUMN student_id_fk INTEGER;')

        if 'student_id_fk' in column_names:
            conn.execute(
                '''
                UPDATE REVIEW_PROPERTY
                SET account_id_fk = (
                    SELECT account_id_fk
                    FROM STUDENT
                    WHERE STUDENT.student_id_pk = REVIEW_PROPERTY.student_id_fk
                )
                WHERE account_id_fk IS NULL;
                '''
            )

        conn.execute(
            '''
            UPDATE REVIEW_PROPERTY
            SET student_id_fk = (
                SELECT student_id_pk
                FROM STUDENT
                WHERE STUDENT.account_id_fk = REVIEW_PROPERTY.account_id_fk
            )
            WHERE student_id_fk IS NULL AND account_id_fk IS NOT NULL;
            '''
        )

        conn.commit()

# This function creates and configures the Flask application, initializes the database, and registers the blueprints for views and authentication.
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
    _ensure_reservation_status_column(app)
    _ensure_review_table(app)
    _ensure_review_account_column(app)
    _ensure_property_details_columns(app)
    _ensure_amenities_tables(app)
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    
    return app