import math
import os

from alembic.util import status

from models import User, Phone, db
from flask import request, jsonify, flash, render_template, redirect, url_for
from flask_login import login_user, login_required, logout_user, LoginManager, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from configs import app
from forms import LoginForm, UserForm, AddProductForm, CardForm
from models import Purchased

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(app_dir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



images = [
        "https://cdn.mos.cms.futurecdn.net/6SxD9kBtDntRhMMBcPutjF.jpg",
        "https://www.apple.com/newsroom/images/2023/09/apple-unveils-iphone-15-pro-and-iphone-15-pro-max/article/Apple-iPhone-15-Pro-lineup-hero-230912_Full-Bleed-Image.jpg.large.jpg",
        "https://s.yimg.com/os/creatr-uploaded-images/2023-02/9039b320-b784-11ed-939f-683a71d03bde"
    ]

ITEMS_PER_PAGE = 8


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data) and user.status != "blocked" :
            login_user(user)
            flash("Login successful!", "success")

            # Check if the user is an admin
            if user.role == 'admin':
                return redirect(url_for('admin_users'))  # Redirect to the admin users page
            else:
                return redirect(url_for('index'))  # Redirect to the homepage for regular users
        else:
            flash("Invalid credentials.", "danger")

    return render_template('login.html', form=form)


@app.route('/')
def index():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin_users'))
    page = request.args.get('page', 1, type=int)
    phones = (
        Phone.query
        .filter(
            (Phone.status != "deleted") &
            (Phone.status != "blocked") &
            (Phone.status == 'active') |
            (Phone.status == None)
        )
        .limit(ITEMS_PER_PAGE)
        .offset((page - 1) * ITEMS_PER_PAGE)
        .all()
    )
    countAll = Phone.query.filter(
            (Phone.status != "deleted") &
            (Phone.status != "blocked") &
            (Phone.status == 'active') |
            (Phone.status == None)
        ).count()
    total_pages = math.ceil(countAll / ITEMS_PER_PAGE)

    user = current_user if current_user.is_authenticated else None

    return render_template('index.html', images=images, phones=phones, current_user=current_user, total_pages=total_pages, current_page=page)




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/myself')
@login_required
def self():
    purchasedItems = (
        db.session.query(Purchased, Phone)
        .join(Phone, Purchased.phoneid == Phone.id)
        .filter(Purchased.userid == current_user.id)
        .all()
    )
    uploadItems = Phone.query.filter(Phone.userid == current_user.id).all()
    return render_template('me.html', purchasedItem=purchasedItems, uploadItems=uploadItems)



@app.route('/phones/<int:id>')
def product_detail(id):
    phone = Phone.query.get(id)

    if not phone:
        return "Phone not found", 404


    return render_template('mobile.html', phone=phone, current_user=current_user)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = AddProductForm()
    if form.validate_on_submit():
        file = request.files['img']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

            new_phone = Phone(
                name=form.name.data,
                price=form.price.data,
                img=f'static/uploads/{filename}',
                userid=current_user.id,
                status='active'
            )
            db.session.add(new_phone)
            db.session.commit()
            flash("Product added successfully!", "success")
            return redirect(url_for('index'))
    return render_template('add_product.html', form=form)



@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_phone(id):
    phone = Phone.query.get(id)

    if not phone:
        return jsonify({"error": f"No phone found with ID {id}."}), 404

    if current_user.id == phone.userid:
        phone.status = "deleted"
        db.session.commit()
        flash("Phone has been deleted.", "success")
        return redirect(url_for('self'))

    return jsonify({"error": "You do not have permission to delete this phone."}), 403


@app.route('/add_user', methods=['GET', 'POST'])
def register():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists. Please log in.", "warning")
            return render_template('registration.html', form=form)

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

        # Check if email is 'admin@gmail.com' and set role accordingly
        if form.email.data == 'admin@gmail.com':
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                password=hashed_password,
                role='admin',  # Admin role set here
                status=None
            )
        else:
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                password=hashed_password,
                role=None,  # Normal user role
                status=None
            )

        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    if not form.validate_on_submit():
        print("Form validation errors:", form.errors)
        print("no submit")

    return render_template('registration.html', form=form)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('name')
    page = request.args.get('page', 1, type=int)
    if not query and not page:
        return redirect(url_for('index'))

    phones = (
        Phone.query
        .filter(
            (Phone.status != "deleted") &
            (Phone.status != "blocked") &
            (Phone.status == 'active') &  # Correct way to check for NULL values
            Phone.name.ilike(f"%{query}%")  # Name search filter
        )
        .limit(ITEMS_PER_PAGE)
        .offset((page - 1) * ITEMS_PER_PAGE)
        .all()
    )

    countAll = (
        Phone.query
        .filter(
            (Phone.status != "deleted") &
            (Phone.status != "blocked") &
            (Phone.status == 'active') &  # Correct way to check for NULL values
            Phone.name.ilike(f"%{query}%")  # Name search filter
        )
        .count()
    )

    total_pages = math.ceil(countAll / ITEMS_PER_PAGE)

    return render_template('index.html', query=query, phones=phones, total_pages=total_pages, current_page=page)


@app.route('/card/<int:id>', methods=['POST', 'GET'])
@login_required
def buy(id):
    form = CardForm()
    print(form.data)
    if form.validate_on_submit():
        purchased = Purchased(phoneid=id, userid=current_user.id)
        db.session.add(purchased)
        db.session.commit()
        return redirect(url_for('self'))
    return render_template('card.html', phone=id, form=form)



@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if current_user.role != 'admin':  # Ensure only admin can access this page
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('index'))  # Redirect to homepage if not admin

    users = User.query.all()  # Get all users from the database
    return render_template('admin_users.html', users=users)  # Render the 'admin_users.html' template


@app.route('/admin/phones', methods=['GET', 'POST'])
@login_required
def admin_phones():
    if current_user.role != 'admin':  # Ensure only admin can access this page
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('index'))  # Redirect to homepage if not admin

    phones = Phone.query.all()  # Get all phones from the database
    return render_template('admin_phones.html', phones=phones)  # Render the 'admin_phones.html' template


@app.route('/admin/user/block/<int:id>', methods=['POST'])
@login_required
def block_user(id):
    if current_user.role != 'admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('index'))

    user_to_block = User.query.get_or_404(id)
    user_to_block.status = "blocked"  # Block the user
    db.session.commit()
    flash(f"User {user_to_block.name} has been blocked.", "success")
    return redirect(url_for('admin_users'))


@app.route('/admin/user/unblock/<int:id>', methods=['POST'])
@login_required
def unblock_user(id):  # Rename function to unblock_user
    if current_user.role != 'admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('index'))

    user_to_unblock = User.query.get_or_404(id)
    user_to_unblock.status = "active"  # Unblock the user
    db.session.commit()
    flash(f"User {user_to_unblock.name} has been unblocked.", "success")
    return redirect(url_for('admin_users'))


@app.route('/admin/phone/block/<int:id>', methods=['POST'])
@login_required
def block_phone(id):
    if current_user.role != 'admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('index'))

    phone_to_block = Phone.query.get_or_404(id)
    phone_to_block.status = "blocked"
    db.session.commit()
    flash(f"User {phone_to_block.name} has been blocked.", "success")
    return redirect(url_for('admin_phones'))


@app.route('/admin/phone/unblock/<int:id>', methods=['POST'])
@login_required
def unblock_phone(id):
    if current_user.role != 'admin':
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('index'))

    phone_to_unblock = Phone.query.get_or_404(id)
    phone_to_unblock.status = "active"  # Unblock the user
    db.session.commit()
    flash(f"User {phone_to_unblock.name} has been unblocked.", "success")
    return redirect(url_for('admin_phones'))


