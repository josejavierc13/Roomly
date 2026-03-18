from . import db


class Account(db.Model):
    __tablename__ = 'ACCOUNT'

    account_id_pk = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    date_created = db.Column(db.DateTime, nullable=True)
    account_status = db.Column(db.String(20), nullable=False)


class Owner(db.Model):
    __tablename__ = 'OWNER'

    owner_id_pk = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=True)


class University(db.Model):
    __tablename__ = 'UNIVERSITY'

    university_id_pk = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    


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
    sqr_ft = db.Column(db.Integer, nullable=False)
    availability_status = db.Column(db.Boolean, nullable=False)
    owner_id_fk = db.Column(db.Integer, nullable=False)
    university_id_fk = db.Column(db.Integer, nullable=True)
    images = db.relationship('PropertyImage', backref='property', lazy='select')

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


class PropertyImage(db.Model):
    __tablename__ = 'PROPERTY_IMAGES'

    image_id_pk = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255), nullable=False)
    property_id_fk = db.Column(db.Integer, db.ForeignKey('PROPERTY.property_id_pk'), nullable=False)
