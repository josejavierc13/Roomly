from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import Account, Owner

auth = Blueprint('auth', __name__)

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