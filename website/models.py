from . import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

# Define the Account model representing user accounts in the database, 
# with fields for email, password, name, contact information, profile picture, 
# account status, and account type.
class Account(db.Model):
    __tablename__ = 'ACCOUNT'

    account_id_pk = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    date_created = db.Column(db.DateTime, nullable=True)
    account_status = db.Column(db.String(20), nullable=False)
    account_type = db.Column(db.String(20), nullable=False, default='STUDENT')

# Define the Owner model representing property owners in the database,
# with fields for company name, verification status, and a foreign key linking to the Account model.
class Owner(db.Model):
    __tablename__ = 'OWNER'

    owner_id_pk = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=True)
    verified_status = db.Column(db.Boolean, nullable=True)
    account_id_fk = db.Column(db.Integer, nullable=False)

# Define the University model representing universities in the database,
# with fields for university name and a primary key.
class University(db.Model):
    __tablename__ = 'UNIVERSITY'

    university_id_pk = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

# Define the Amenity model representing amenities available for properties in the database,
# with fields for amenity name and a primary key.
class Amenity(db.Model):
    __tablename__ = 'AMENITIES'

    amenity_id_pk = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    

# Define the Property model representing rental properties in the database,
# with fields for property details, pricing, location, availability, and relationships to images, amenities, and reviews.
class Property(db.Model):
    __tablename__ = 'PROPERTY'

    property_id_pk = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    price_per_month = db.Column(db.Float, nullable=False)
    deposit_amount = db.Column(db.Float, nullable=False)
    number_of_bedrooms = db.Column(db.Integer, nullable=False)
    number_of_bathrooms = db.Column(db.Integer, nullable=False, default=1)
    sqr_ft = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.Text, nullable=True)
    availability_status = db.Column(db.Boolean, nullable=False)
    owner_id_fk = db.Column(db.Integer, nullable=False)
    university_id_fk = db.Column(db.Integer, nullable=True)
    images = db.relationship('PropertyImage', backref='property', lazy='select')
    amenity_links = db.relationship('PropertyAmenity', backref='property', lazy='select')
    reviews = db.relationship('PropertyReview', backref='property', lazy='select', cascade='all, delete-orphan')

    @property
    def id(self):
        return self.property_id_pk

    @property
    def price(self):
        return self.price_per_month

    @property
    def image_url(self):
        if self.images:
            return self.images[0].image_url
        return '/static/logoRoomly.png'

# Define the PropertyImage model representing images associated with properties in the database,
# with fields for image URL and a foreign key linking to the Property model.
class PropertyImage(db.Model):
    __tablename__ = 'PROPERTY_IMAGES'

    image_id_pk = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255), nullable=False)
    property_id_fk = db.Column(db.Integer, db.ForeignKey('PROPERTY.property_id_pk'), nullable=False)

# Define the Reservation model representing property reservations in the database,
# with fields for reservation details, status, and foreign keys linking to the Property and Account models
class Reservation(db.Model):
    __tablename__ = 'PROPERTY_RESERVATION'

    reservation_id_pk = db.Column(db.Integer, primary_key=True)
    property_id_fk = db.Column(db.Integer, db.ForeignKey('PROPERTY.property_id_pk'), nullable=False)
    account_id_fk = db.Column(db.Integer, nullable=False)
    reserved_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(30), nullable=False, default='pending')

# Define the PropertyReview model representing reviews for properties in the database
class PropertyReview(db.Model):
    __tablename__ = 'REVIEW_PROPERTY'
    __table_args__ = (
        UniqueConstraint('account_id_fk', 'property_id_fk', name='uq_review_property_account'),
    )

    review_property_id_pk = db.Column(db.Integer, primary_key=True)
    property_id_fk = db.Column(db.Integer, db.ForeignKey('PROPERTY.property_id_pk'), nullable=False)
    account_id_fk = db.Column(db.Integer, db.ForeignKey('ACCOUNT.account_id_pk'), nullable=False)
    student_id_fk = db.Column(db.Integer, db.ForeignKey('STUDENT.student_id_pk'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Define the Student model representing student users in the database,
# with fields for academic information, preferences, and a foreign key linking to the Account model.
class Student(db.Model):
    __tablename__ = 'STUDENT'

    student_id_pk = db.Column(db.Integer, primary_key=True)
    major = db.Column(db.String(255), nullable=False)
    year_of_study = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.String(255), nullable=True)
    budget_min = db.Column(db.Float, nullable=True)
    budget_max = db.Column(db.Float, nullable=True)
    smoking_preference = db.Column(db.Boolean, nullable=True)
    pets_preference = db.Column(db.Boolean, nullable=True)
    sleep_schedule_preference = db.Column(db.String(50), nullable=True)
    student_active_status = db.Column(db.Boolean, nullable=True)
    university_id_fk = db.Column(db.Integer, nullable=True)
    account_id_fk = db.Column(db.Integer, db.ForeignKey('ACCOUNT.account_id_pk'), nullable=False)

# Define the PropertyAmenity model representing the many-to-many relationship between properties and amenities in the database,
# with composite primary keys and foreign keys linking to the Property and Amenity models.
class PropertyAmenity(db.Model):
    __tablename__ = 'PROPERTY_AMENITY'

    property_id_pk_fk = db.Column(db.Integer, db.ForeignKey('PROPERTY.property_id_pk'), primary_key=True)
    amenity_id_pk_fk = db.Column(db.Integer, db.ForeignKey('AMENITIES.amenity_id_pk'), primary_key=True)
