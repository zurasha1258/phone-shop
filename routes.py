from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, Phone, Purchased
from forms import LoginForm, UserForm, AddProductForm
from configs import app, db
import os
import math

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


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template('login.html', form=form)


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    ITEMS_PER_PAGE = 16  # Number of items per page
    phones = (
        Phone.query
        .filter((Phone.isdeleted == False) | (Phone.isdeleted == None))
        .limit(ITEMS_PER_PAGE)
        .offset((page - 1) * ITEMS_PER_PAGE)
        .all()
    )
    countAll = Phone.query.filter((Phone.isdeleted == False) | (Phone.isdeleted == None)).count()



    total_pages = math.ceil(countAll / ITEMS_PER_PAGE)

    print(total_pages)
    user = current_user if current_user.is_authenticated else None

    return render_template('index.html', images=images, phones=phones, current_user=user, total_pages=total_pages, current_page=page)




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


    return render_template('mobile.html', phone=phone)


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
                userid=current_user.id
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
        phone.isdeleted = True
        db.session.commit()
        flash("Phone has been deleted.", "success")
        return redirect(url_for('index'))

    return jsonify({"error": "You do not have permission to delete this phone."}), 403






@app.route('/add_user', methods=['GET', 'POST'])
def register():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists. Please log in.", "warning")
            return render_template('registration.html', form=form)

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password=hashed_password
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
    results = []
    if not query:
        return redirect(url_for('index'));
    if query:
        phones = Phone.query.filter((Phone.name.ilike(f"%{query}%"))).all()
        print(results)
    return render_template('index.html', query=query, phones=phones, images=images)


@app.route('/buy/<int:id>', methods=['POST'])
def buy(id):
    purchased = Purchased(phoneid=id, userid=current_user.id)
    db.session.add(purchased)
    db.session.commit()
    return redirect(url_for('self'))
