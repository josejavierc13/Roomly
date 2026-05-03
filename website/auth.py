import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import Account, Owner, Property, Reservation

auth = Blueprint('auth', __name__)

ALLOWED_PROFILE_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def _is_allowed_profile_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PROFILE_IMAGE_EXTENSIONS

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter your email and password.', 'error')
            return render_template('log-in.html')

        account = Account.query.filter(db.func.lower(Account.email) == email).first()
        if not account or not check_password_hash(account.hashed_password, password):
            flash('Invalid email or password.', 'error')
            return render_template('log-in.html')

        if account.account_status != 'active':
            flash('This account is not active.', 'error')
            return render_template('log-in.html')

        session.clear()
        session['account_id'] = account.account_id_pk
        session['account_first_name'] = account.first_name
        session['account_email'] = account.email
        session['account_type'] = (account.account_type or 'STUDENT').upper()
        session.permanent = True

        flash('Welcome back.', 'success')
        return redirect(url_for('views.browse'))

    return render_template('log-in.html') # Render the log-in.html template when the /login route is accessed

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        city = request.form.get('city', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        account_type = request.form.get('account_type', 'STUDENT').strip().upper()

        if not all([first_name, last_name, email, password, confirm_password]):
            flash('Please complete all sign-up fields.', 'error')
            return render_template('sign-up.html')

        if account_type not in {'OWNER', 'STUDENT'}:
            flash('Please choose a valid account type.', 'error')
            return render_template('sign-up.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('sign-up.html')

        if password != confirm_password:
            flash('Password and confirmation do not match.', 'error')
            return render_template('sign-up.html')

        existing_account = Account.query.filter(db.func.lower(Account.email) == email).first()
        if existing_account:
            flash('An account with this email already exists.', 'error')
            return render_template('sign-up.html')

        next_account_id = (db.session.query(db.func.max(Account.account_id_pk)).scalar() or 0) + 1
        hashed_password = generate_password_hash(password)

        account = Account(
            account_id_pk=next_account_id,
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            city=city or None,
            phone_number=None,
            profile_picture=None,
            account_status='active',
            account_type=account_type,
        )

        db.session.add(account)

        if account_type == 'OWNER':
            next_owner_id = (db.session.query(db.func.max(Owner.owner_id_pk)).scalar() or 0) + 1
            owner = Owner(
                owner_id_pk=next_owner_id,
                company_name=None,
                verified_status=False,
                account_id_fk=next_account_id,
            )
            db.session.add(owner)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Unable to create account. Please try again.', 'error')
            return render_template('sign-up.html')

        flash('Your account was created successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('sign-up.html') # Render the sign-up.html template when the /signup route is accessed

@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/profile', methods=['GET', 'POST'])
def profile():
    account_id = session.get('account_id')
    if not account_id:
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('auth.login'))

    account = Account.query.filter_by(account_id_pk=account_id).first()
    if not account:
        session.clear()
        flash('Account not found. Please log in again.', 'error')
        return redirect(url_for('auth.login'))

    owner_profile = Owner.query.filter_by(account_id_fk=account.account_id_pk).first()
    owned_properties = []
    if owner_profile:
        owned_properties = (
            Property.query
            .filter_by(owner_id_fk=owner_profile.owner_id_pk)
            .order_by(Property.property_id_pk.desc())
            .all()
        )

    listed_properties = [property_row for property_row in owned_properties if property_row.availability_status]
    rented_properties = [property_row for property_row in owned_properties if not property_row.availability_status]

    # Properties this account has reserved/claimed
    reserved_properties = []
    user_reservations = Reservation.query.filter_by(account_id_fk=account.account_id_pk).order_by(Reservation.reserved_at.desc()).all()
    for res in user_reservations:
        prop = Property.query.get(res.property_id_fk)
        if prop:
            reserved_properties.append({'property': prop, 'reservation': res})

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        city = request.form.get('city', '').strip()

        if not email or not first_name or not last_name:
            flash('Email, name, and last name are required.', 'error')
            return redirect(url_for('auth.profile'))

        existing_account = Account.query.filter(db.func.lower(Account.email) == email).first()
        if existing_account and existing_account.account_id_pk != account.account_id_pk:
            flash('That email is already used by another account.', 'error')
            return redirect(url_for('auth.profile'))

        account.email = email
        account.first_name = first_name
        account.last_name = last_name
        account.city = city or None

        profile_picture = request.files.get('profile_picture')
        if profile_picture and profile_picture.filename:
            if not _is_allowed_profile_image(profile_picture.filename):
                flash('Please upload a valid image file (png, jpg, jpeg, webp).', 'error')
                return redirect(url_for('auth.profile'))

            extension = profile_picture.filename.rsplit('.', 1)[1].lower()
            safe_name = secure_filename(profile_picture.filename.rsplit('.', 1)[0]) or 'profile'
            unique_name = f"{safe_name}_{uuid.uuid4().hex}.{extension}"

            pictures_dir = os.path.join(current_app.static_folder, 'profile_pictures')
            os.makedirs(pictures_dir, exist_ok=True)
            file_path = os.path.join(pictures_dir, unique_name)
            profile_picture.save(file_path)

            account.profile_picture = f'/static/profile_pictures/{unique_name}'

        db.session.commit()
        session['account_first_name'] = account.first_name
        session['account_email'] = account.email

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template(
        'profile.html',
        account=account,
        listed_properties=listed_properties,
        rented_properties=rented_properties,
        reserved_properties=reserved_properties,
    )