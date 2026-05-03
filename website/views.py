import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from . import db
from .models import Amenity, Owner, Property, PropertyAmenity, PropertyImage, Reservation
from .models import Account


views = Blueprint('views', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _is_allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@views.route('/')
def home():
    return render_template('index.html')

@views.route('/browse')
def browse():
    selected_filter = request.args.get('filter', 'newest')

    query = Property.query.filter_by(availability_status=True)

    if selected_filter == 'price_low_high':
        query = query.order_by(Property.price_per_month.asc())
    elif selected_filter == 'price_high_low':
        query = query.order_by(Property.price_per_month.desc())
    elif selected_filter == 'oldest':
        query = query.order_by(Property.property_id_pk.asc())
    else:
        selected_filter = 'newest'
        query = query.order_by(Property.property_id_pk.desc())

    properties = query.all()
    return render_template('browse.html', properties=properties, selected_filter=selected_filter)

@views.route('/list-property', methods=['GET', 'POST'])
def list_property():
    account_id = session.get('account_id')

    if not account_id:
        flash('Please log in to list a property.', 'error')
        return redirect(url_for('auth.login'))

    owner_profile = Owner.query.filter_by(account_id_fk=account_id).first()
    if not owner_profile:
        # Create an owner profile for the user
        next_owner_id = (db.session.query(db.func.max(Owner.owner_id_pk)).scalar() or 0) + 1
        owner_profile = Owner(owner_id_pk=next_owner_id, account_id_fk=account_id)
        db.session.add(owner_profile)
        db.session.commit()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', '').strip()
        postal_code = request.form.get('postal_code', '').strip()

        try:
            price_per_month = float(request.form.get('price_per_month', '0'))
            deposit_amount = float(request.form.get('deposit_amount', '0'))
            number_of_bedrooms = int(request.form.get('number_of_bedrooms', '0'))
            number_of_bathrooms = int(request.form.get('number_of_bathrooms', '0'))
            sqr_ft = int(request.form.get('sqr_ft', '0'))
        except ValueError:
            flash('Please enter valid numeric values for price, deposit, beds, baths, and size.', 'error')
            return render_template('list-property.html')

        selected_amenities = request.form.getlist('amenities')
        formatted_amenities = [amenity.replace('-', ' ').title() for amenity in selected_amenities]
        amenities_value = ', '.join(formatted_amenities) if formatted_amenities else None

        if not all([title, description, address, city, state, country, postal_code]):
            flash('Please fill in all required text fields.', 'error')
            return render_template('list-property.html')

        if price_per_month <= 0 or deposit_amount < 0 or number_of_bedrooms <= 0 or number_of_bathrooms <= 0 or sqr_ft <= 0:
            flash('Please enter positive values for monthly price, bedrooms, bathrooms, and square footage. Deposit cannot be negative.', 'error')
            return render_template('list-property.html')

        availability_status = request.form.get('availability_status', 'on') == 'on'
        image_files = request.files.getlist('images')

        # Filter out empty files and validate
        image_files = [f for f in image_files if f and f.filename]
        
        for image_file in image_files:
            if not _is_allowed_image_file(image_file.filename):
                flash('Please upload valid image files (png, jpg, jpeg, webp).', 'error')
                return render_template('list-property.html')

        next_id = (db.session.query(db.func.max(Property.property_id_pk)).scalar() or 0) + 1

        new_property = Property(
            property_id_pk=next_id,
            title=title,
            description=description,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            price_per_month=price_per_month,
            deposit_amount=deposit_amount,
            number_of_bedrooms=number_of_bedrooms,
            number_of_bathrooms=number_of_bathrooms,
            sqr_ft=sqr_ft,
            amenities=amenities_value,
            availability_status=availability_status,
            owner_id_fk=owner_profile.owner_id_pk,
            university_id_fk=None,
        )

        db.session.add(new_property)

        for amenity_name in formatted_amenities:
            amenity = Amenity.query.filter(db.func.lower(Amenity.name) == amenity_name.lower()).first()
            if not amenity:
                next_amenity_id = (db.session.query(db.func.max(Amenity.amenity_id_pk)).scalar() or 0) + 1
                amenity = Amenity(amenity_id_pk=next_amenity_id, name=amenity_name)
                db.session.add(amenity)

            mapping = PropertyAmenity(
                property_id_pk_fk=next_id,
                amenity_id_pk_fk=amenity.amenity_id_pk,
            )
            db.session.add(mapping)

        # Save all uploaded images
        for image_file in image_files:
            extension = image_file.filename.rsplit('.', 1)[1].lower()
            safe_name = secure_filename(image_file.filename.rsplit('.', 1)[0]) or 'property'
            unique_name = f"{safe_name}_{uuid.uuid4().hex}.{extension}"

            images_dir = os.path.join(current_app.static_folder, 'property_images')
            os.makedirs(images_dir, exist_ok=True)
            file_path = os.path.join(images_dir, unique_name)
            image_file.save(file_path)

            next_image_id = (db.session.query(db.func.max(PropertyImage.image_id_pk)).scalar() or 0) + 1
            image_row = PropertyImage(
                image_id_pk=next_image_id,
                image_url=f'/static/property_images/{unique_name}',
                property_id_fk=next_id,
            )
            db.session.add(image_row)

        db.session.commit()
        flash('Property listed successfully.', 'success')
        return redirect(url_for('views.browse'))

    return render_template('list-property.html')


@views.route('/property/<int:property_id>')
def property_detail(property_id):
    selected_property = Property.query.get_or_404(property_id)
    owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()

    amenity_names = []
    if selected_property.amenities:
        amenity_names = [name.strip() for name in selected_property.amenities.split(',') if name.strip()]

    if not amenity_names:
        amenity_rows = (
            db.session.query(Amenity.name)
            .join(PropertyAmenity, Amenity.amenity_id_pk == PropertyAmenity.amenity_id_pk_fk)
            .filter(PropertyAmenity.property_id_pk_fk == selected_property.property_id_pk)
            .all()
        )
        amenity_names = [row[0] for row in amenity_rows]

    reservation = Reservation.query.filter_by(property_id_fk=selected_property.property_id_pk).first()
    reserver = None
    if reservation:
        reserver = Account.query.filter_by(account_id_pk=reservation.account_id_fk).first()

    # Check if current user already has an active reservation
    user_has_active_reservation = False
    account_id = session.get('account_id')
    if account_id:
        user_has_active_reservation = Reservation.query.filter_by(account_id_fk=account_id).first() is not None

    return render_template('property-detail.html', property=selected_property, owner=owner_profile, amenity_names=amenity_names, reservation=reservation, reserver=reserver, user_has_active_reservation=user_has_active_reservation)


@views.route('/property/<int:property_id>/claim', methods=['POST'])
def claim_property(property_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to claim a property.', 'error')
        return redirect(url_for('auth.login'))

    selected_property = Property.query.get_or_404(property_id)

    # Prevent owner from claiming their own property
    if selected_property.owner_id_fk:
        owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
        if owner_profile and owner_profile.account_id_fk == account_id:
            flash('You cannot claim your own property.', 'error')
            return redirect(url_for('views.property_detail', property_id=property_id))

    existing_reservation = Reservation.query.filter_by(property_id_fk=property_id).first()
    if existing_reservation:
        flash('This property has already been claimed.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    # Prevent user from claiming more than one property at a time
    user_existing = Reservation.query.filter_by(account_id_fk=account_id).first()
    if user_existing:
        flash('You already have a reserved property. Release it before claiming another.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    next_res_id = (db.session.query(db.func.max(Reservation.reservation_id_pk)).scalar() or 0) + 1
    reservation = Reservation(
        reservation_id_pk=next_res_id,
        property_id_fk=property_id,
        account_id_fk=account_id,
        status='reserved',
    )
    db.session.add(reservation)

    # mark property as not available while reserved
    selected_property.availability_status = False
    db.session.commit()

    # Fetch owner contact info if possible
    owner_contact = None
    if selected_property.owner_id_fk:
        owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
        if owner_profile:
            owner_account = Account.query.filter_by(account_id_pk=owner_profile.account_id_fk).first()
            if owner_account:
                owner_contact = owner_account.email

    msg = 'Property claimed and reserved for you.'
    if owner_contact:
        msg += f' Owner contact: {owner_contact}'

    flash(msg, 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))


@views.route('/property/<int:property_id>/release', methods=['POST'])
def release_property(property_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to release a reservation.', 'error')
        return redirect(url_for('auth.login'))

    reservation = Reservation.query.filter_by(property_id_fk=property_id, account_id_fk=account_id).first()
    if not reservation:
        flash('No reservation found for this property under your account.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    selected_property = Property.query.get_or_404(property_id)

    # Remove reservation and mark property available
    db.session.delete(reservation)
    selected_property.availability_status = True
    db.session.commit()

    flash('Reservation released and property is now available.', 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))
