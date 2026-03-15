import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from . import db
from .models import Owner, Property, PropertyImage


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
            sqr_ft = int(request.form.get('sqr_ft', '0'))
        except ValueError:
            flash('Please enter valid numeric values for price, deposit, bedrooms, and size.', 'error')
            return render_template('list-property.html')

        if not all([title, description, address, city, state, country, postal_code]):
            flash('Please fill in all required text fields.', 'error')
            return render_template('list-property.html')

        if price_per_month <= 0 or deposit_amount < 0 or number_of_bedrooms <= 0 or sqr_ft <= 0:
            flash('Please enter positive values for monthly price, bedrooms, and square footage. Deposit cannot be negative.', 'error')
            return render_template('list-property.html')

        default_owner = Owner.query.order_by(Owner.owner_id_pk.asc()).first()
        if not default_owner:
            flash('No owner account exists yet. Please create an owner first.', 'error')
            return render_template('list-property.html')

        availability_status = request.form.get('availability_status', 'on') == 'on'
        image_file = request.files.get('image')

        if image_file and image_file.filename and not _is_allowed_image_file(image_file.filename):
            flash('Please upload a valid image file (png, jpg, jpeg, gif, webp).', 'error')
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
            sqr_ft=sqr_ft,
            availability_status=availability_status,
            owner_id_fk=default_owner.owner_id_pk,
            university_id_fk=None,
        )

        db.session.add(new_property)

        if image_file and image_file.filename:
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
    return render_template('browse.html', properties=[selected_property])
