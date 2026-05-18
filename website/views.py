import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from . import db
from .models import Amenity, Owner, Property, PropertyAmenity, PropertyImage, Reservation, Student, University
from .models import PropertyReview
from .models import Account


views = Blueprint('views', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _is_allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def _get_owner_account(owner_profile):
    if not owner_profile:
        return None
    return Account.query.filter_by(account_id_pk=owner_profile.account_id_fk).first()

@views.route('/')
def home():
    # Get the 3 most recent available properties for featured listings
    featured_properties = Property.query.filter_by(availability_status=True).order_by(Property.property_id_pk.desc()).limit(3).all()
    
    # Get university information for each property
    for prop in featured_properties:
        if prop.university_id_fk:
            prop.university = University.query.get(prop.university_id_fk)
        else:
            prop.university = None
    
    return render_template('index.html', featured_properties=featured_properties)

@views.route('/browse')
def browse():
    selected_filter = request.args.get('filter', 'newest')
    selected_university = request.args.get('university', '')

    query = Property.query.filter_by(availability_status=True)

    # Apply university filter if selected
    if selected_university:
        try:
            university_id = int(selected_university)
            query = query.filter_by(university_id_fk=university_id)
        except ValueError:
            pass

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
    
    # Get university information for each property
    for prop in properties:
        if prop.university_id_fk:
            prop.university = University.query.get(prop.university_id_fk)
        else:
            prop.university = None
    
    # Get all universities for the dropdown
    universities = University.query.all()
    
    return render_template('browse.html', properties=properties, selected_filter=selected_filter, universities=universities, selected_university=selected_university)

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

    # Get all universities for the dropdown
    universities = University.query.all()

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

        # Get the selected university
        university_id = request.form.get('university', '').strip()
        try:
            university_id = int(university_id) if university_id else None
        except ValueError:
            flash('Please select a valid university.', 'error')
            return render_template('list-property.html', universities=universities)

        if not all([title, description, address, city, state, country, postal_code]):
            flash('Please fill in all required text fields.', 'error')
            return render_template('list-property.html', universities=universities)

        if price_per_month <= 0 or deposit_amount < 0 or number_of_bedrooms <= 0 or number_of_bathrooms <= 0 or sqr_ft <= 0:
            flash('Please enter positive values for monthly price, bedrooms, bathrooms, and square footage. Deposit cannot be negative.', 'error')
            return render_template('list-property.html', universities=universities)
        
        if not university_id:
            flash('Please select a closest university.', 'error')
            return render_template('list-property.html', universities=universities)

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
            university_id_fk=university_id,
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

    return render_template('list-property.html', universities=universities)


@views.route('/property/<int:property_id>')
def property_detail(property_id):
    selected_property = Property.query.get_or_404(property_id)
    owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
    owner_account = _get_owner_account(owner_profile)
    account_id = session.get('account_id')    
    # Get the university information
    university = None
    if selected_property.university_id_fk:
        university = University.query.get(selected_property.university_id_fk)
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

    user_application = None
    if account_id:
        user_application = (
            Reservation.query
            .filter_by(property_id_fk=selected_property.property_id_pk, account_id_fk=account_id)
            .order_by(Reservation.reserved_at.desc())
            .first()
        )

    property_applications = []
    if owner_account and owner_account.account_id_pk == account_id:
        applications = (
            Reservation.query
            .filter_by(property_id_fk=selected_property.property_id_pk)
            .order_by(Reservation.reserved_at.desc())
            .all()
        )
        for application in applications:
            applicant = Account.query.filter_by(account_id_pk=application.account_id_fk).first()
            property_applications.append({'reservation': application, 'applicant': applicant})

    reviews = (
        PropertyReview.query
        .filter_by(property_id_fk=selected_property.property_id_pk)
        .order_by(PropertyReview.date_posted.desc())
        .all()
    )
    average_rating = None
    if reviews:
        average_rating = round(sum(review.rating for review in reviews) / len(reviews), 1)

    user_review = None
    if account_id:
        user_review = PropertyReview.query.filter_by(property_id_fk=selected_property.property_id_pk, account_id_fk=account_id).first()

    can_review = False
    if account_id and not user_review:
        approved_reservation = Reservation.query.filter_by(property_id_fk=selected_property.property_id_pk, account_id_fk=account_id, status='approved').first()
        can_review = approved_reservation is not None

    return render_template(
        'property-detail.html',
        property=selected_property,
        owner=owner_profile,
        owner_account=owner_account,
        university=university,
        amenity_names=amenity_names,
        user_application=user_application,
        property_applications=property_applications,
        reviews=reviews,
        average_rating=average_rating,
        user_review=user_review,
        can_review=can_review,
    )


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

    existing_application = (
        Reservation.query
        .filter(
            Reservation.property_id_fk == property_id,
            Reservation.account_id_fk == account_id,
            Reservation.status.in_(['pending', 'approved'])
        )
        .first()
    )
    if existing_application:
        flash('You already have an active application for this property.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    next_res_id = (db.session.query(db.func.max(Reservation.reservation_id_pk)).scalar() or 0) + 1
    reservation = Reservation(
        reservation_id_pk=next_res_id,
        property_id_fk=property_id,
        account_id_fk=account_id,
        status='pending',
    )
    db.session.add(reservation)
    db.session.commit()

    owner_contact = None
    if selected_property.owner_id_fk:
        owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
        if owner_profile:
            owner_account = _get_owner_account(owner_profile)
            if owner_account:
                owner_contact = {
                    'name': f'{owner_account.first_name} {owner_account.last_name}'.strip(),
                    'email': owner_account.email,
                    'phone_number': owner_account.phone_number,
                }

    msg = 'Application submitted for landlord review.'
    if owner_contact:
        contact_bits = [owner_contact['name']]
        if owner_contact['email']:
            contact_bits.append(owner_contact['email'])
        if owner_contact['phone_number']:
            contact_bits.append(owner_contact['phone_number'])
        msg += f" Landlord contact: {' | '.join(contact_bits)}"

    flash(msg, 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))


@views.route('/property/<int:property_id>/applications/<int:reservation_id>/approve', methods=['POST'])
def approve_application(property_id, reservation_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to manage applications.', 'error')
        return redirect(url_for('auth.login'))

    selected_property = Property.query.get_or_404(property_id)
    owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
    if not owner_profile or owner_profile.account_id_fk != account_id:
        flash('You can only review applications for your own properties.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    application = Reservation.query.filter_by(reservation_id_pk=reservation_id, property_id_fk=property_id).first()
    if not application:
        flash('Application not found.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    application.status = 'approved'
    selected_property.availability_status = False

    other_applications = (
        Reservation.query
        .filter(
            Reservation.property_id_fk == property_id,
            Reservation.reservation_id_pk != reservation_id,
            Reservation.status == 'pending'
        )
        .all()
    )
    for other_application in other_applications:
        other_application.status = 'denied'

    db.session.commit()
    flash('Application approved.', 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))


@views.route('/property/<int:property_id>/applications/<int:reservation_id>/deny', methods=['POST'])
def deny_application(property_id, reservation_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to manage applications.', 'error')
        return redirect(url_for('auth.login'))

    selected_property = Property.query.get_or_404(property_id)
    owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
    if not owner_profile or owner_profile.account_id_fk != account_id:
        flash('You can only review applications for your own properties.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    application = Reservation.query.filter_by(reservation_id_pk=reservation_id, property_id_fk=property_id).first()
    if not application:
        flash('Application not found.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    application.status = 'denied'
    db.session.commit()
    flash('Application denied.', 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))


@views.route('/property/<int:property_id>/applications/<int:reservation_id>/remove', methods=['POST'])
def remove_approved_application(property_id, reservation_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to manage applications.', 'error')
        return redirect(url_for('auth.login'))

    selected_property = Property.query.get_or_404(property_id)
    owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
    if not owner_profile or owner_profile.account_id_fk != account_id:
        flash('You can only manage applications for your own properties.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    application = Reservation.query.filter_by(reservation_id_pk=reservation_id, property_id_fk=property_id).first()
    if not application:
        flash('Application not found.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    if application.status != 'approved':
        flash('You can only remove approved applications.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    # Remove the approved application and set property back to available
    db.session.delete(application)
    selected_property.availability_status = True
    db.session.commit()
    flash('Approved application removed. Property is now available again.', 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))


@views.route('/property/<int:property_id>/review', methods=['POST'])
def review_property(property_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to leave a review.', 'error')
        return redirect(url_for('auth.login'))

    selected_property = Property.query.get_or_404(property_id)

    approved_reservation = Reservation.query.filter_by(
        property_id_fk=property_id,
        account_id_fk=account_id,
        status='approved',
    ).first()
    if not approved_reservation:
        flash('You can only review a property after your application has been approved.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    existing_review = PropertyReview.query.filter_by(property_id_fk=property_id, account_id_fk=account_id).first()
    if existing_review:
        flash('You have already reviewed this property.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    try:
        rating = int(request.form.get('rating', '0'))
    except ValueError:
        rating = 0
    comment = request.form.get('comment', '').strip()

    if rating < 1 or rating > 5:
        flash('Please choose a rating from 1 to 5.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    next_review_id = (db.session.query(db.func.max(PropertyReview.review_property_id_pk)).scalar() or 0) + 1
    student_profile = Student.query.filter_by(account_id_fk=account_id).first()
    if not student_profile:
        next_student_id = (db.session.query(db.func.max(Student.student_id_pk)).scalar() or 0) + 1
        # Provide minimal required fields for legacy DB schema: major and year_of_study
        student_profile = Student(
            student_id_pk=next_student_id,
            major='Other',
            year_of_study=1,
            account_id_fk=account_id,
        )
        db.session.add(student_profile)
        db.session.flush()

    review = PropertyReview(
        review_property_id_pk=next_review_id,
        property_id_fk=property_id,
        account_id_fk=account_id,
        student_id_fk=student_profile.student_id_pk,
        rating=rating,
        comment=comment or None,
    )
    db.session.add(review)
    db.session.commit()

    flash('Review submitted successfully.', 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))


@views.route('/property/<int:property_id>/release', methods=['POST'])
def release_property(property_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to release a reservation.', 'error')
        return redirect(url_for('auth.login'))

    reservation = (
        Reservation.query
        .filter_by(property_id_fk=property_id, account_id_fk=account_id)
        .order_by(Reservation.reserved_at.desc())
        .first()
    )
    if not reservation:
        flash('No application found for this property under your account.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    selected_property = Property.query.get_or_404(property_id)

    if reservation.status == 'approved':
        selected_property.availability_status = True

    db.session.delete(reservation)
    db.session.commit()

    flash('Application removed.', 'success')
    return redirect(url_for('views.property_detail', property_id=property_id))


@views.route('/property/<int:property_id>/delete', methods=['POST'])
def delete_property(property_id):
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to delete a property.', 'error')
        return redirect(url_for('auth.login'))

    selected_property = Property.query.get_or_404(property_id)

    # Check if current user is the property owner
    owner_profile = Owner.query.filter_by(owner_id_pk=selected_property.owner_id_fk).first()
    if not owner_profile or owner_profile.account_id_fk != account_id:
        flash('You can only delete your own property listings.', 'error')
        return redirect(url_for('views.property_detail', property_id=property_id))

    # Delete associated images from filesystem
    for image in selected_property.images:
        image_path = os.path.join(current_app.static_folder, image.image_url.lstrip('/static/'))
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass  # Continue even if file deletion fails

    # Delete any reservations for this property
    Reservation.query.filter_by(property_id_fk=property_id).delete()

    # Delete property amenity mappings
    PropertyAmenity.query.filter_by(property_id_pk_fk=property_id).delete()

    # Delete property images from database
    PropertyImage.query.filter_by(property_id_fk=property_id).delete()

    # Delete the property
    db.session.delete(selected_property)
    db.session.commit()

    flash('Property listing deleted successfully.', 'success')
    return redirect(url_for('views.browse'))
