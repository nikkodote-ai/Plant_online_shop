import os
from functools import wraps

import stripe
from flask import Flask, render_template, request, url_for, redirect, flash, abort, session
from flask_bootstrap import Bootstrap
from flask_login import UserMixin
from flask_login import login_user, LoginManager, current_user, logout_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from forms import LoginForm, RegisterForm, CreateForm, CareGuideForm

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants_ecom.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

# ----------MODELS--------------

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    def __repr__(self):
        return '<User: {}>'.format(self.id)


class Plant(db.Model):
    __tablename__ = 'plants'
    id = db.Column(db.Integer, primary_key=True)
    plant_name = db.Column(db.String(250), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250))
    details = db.Column(db.String(500))
    quantity = db.Column(db.Integer)  # update quantity everytime someone buys or you put something

    # Foreign Key link to Careguide
    # care_guide = db.Column(db.Integer, db.ForeignKey('care_guides.id'))  # connect to table named "care_guide", get id
    care_guide = relationship("CareGuide", backref="guide")

    def __repr__(self):
        return '<User: {}>'.format(self.id)
    # room for planters
    # care_guide_id = db.Column(db.Integer, db.ForeignKey('care_guide.id'))  # connect to table named "care_guide", get id
    # care_guide = relationship("CareGuide", backref="care_guide", foreign_keys=[author_id])


class CareGuide(db.Model):
    __tablename__ = 'care_guides'
    id = db.Column(db.Integer, primary_key=True)
    guide_detail = db.Column(db.String(500))
    care_guide_code = db.Column(db.String(500))
    # one-to-many relationship - one careguide, many plants
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'))  # connect to table named "care_guide", get id
    # a care guide can have many pants
    # plant = relationship("Plant", back_populates="guide")

    # class AddProduct(db.Model):
    #     __tablename__ = 'add_products'
    #     id = db.Column(db.Integer, primary_key=True)
    #     product_name = db.Column(db.String(250), unique=True, nullable=False)
    #     price = db.Column(db.Integer, nullable=False)
    #     img_url = db.Column(db.String(250), nullable=False)
    #     quantity_to_order = db.Column(db.Integer, nullable =False)

    # Foreign Key link to Careguide
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'))  # connect to table named "care_guide", get id
    plant = relationship("Plant", backref="plant")

    def __repr__(self):
        return '<Cafe: {}>'.format(self.id)


# db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# for deleting posts
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def home():
    all_plants = Plant.query.all()
    return render_template('index.html',
                           all_plants=all_plants,
                           current_user=current_user,
                           )


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/<int:plant_id>', methods=['POST', 'GET'])
def open_plant_page(plant_id):
    plant = Plant.query.get(plant_id)
    care_guide = CareGuide.query.get(plant_id)
    return render_template('product_details.html', plant=plant, current_user=current_user, care_guide=care_guide)


@app.route('/add_new_plant', methods=['POST', 'GET'])
def create_new_plant():
    form = CreateForm()
    if form.validate_on_submit():
        new_plant = Plant(
            plant_name=form.plant_name.data,
            price=form.price.data,
            img_url=form.img_url.data,
            title=form.title.data,
            details=form.details.data,
            quantity=form.quantity.data,
        )

        db.session.add(new_plant)
        db.session.commit()
        return redirect(url_for('home'))
        #
        # except:
        #     flash('plant name already added. Try Editing existing entry.')
        #     return render_template('create_new_plant.html', form=form, add_new=True)
    return render_template('create_new_plant.html', form=form, add_new=True)


@app.route('/add_new_care_guide', methods=['POST', 'GET'])
def create_new_care_guide():
    form = CareGuideForm()
    if form.validate_on_submit():
        try:
            new_guide = CareGuide(
                guide_detail=form.guide_detail.data,
                care_guide_code=form.care_guide_code.data,
            )

            db.session.add(new_guide)
            db.session.commit()
            return redirect(url_for('home'))

        except:
            flash('plant name already added. Try Editing existing entry.')
            return render_template('create_new_care_guide.html', form=form, add_new=True)
    return render_template('create_new_care_guide.html', form=form, add_new=True)


@app.route('/edit_rating/<int:plant_id>', methods=['POST', 'GET'])
def edit_rating(plant_id):
    plant = Plant.query.get(plant_id)
    edit_form = CreateForm(
        id=plant.id,
        plant_name=plant.plant_name,
        price=plant.price,
        img_url=plant.img_url,
        title=plant.title,
        details=plant.details,
        quantity_left=plant.details,
    )
    if edit_form.validate_on_submit():
        plant.name = edit_form.name.data
        plant.map_url = edit_form.map_url.data
        plant.img_url = edit_form.img_url.data
        plant.location = edit_form.location.data
        plant.has_sockets = edit_form.has_sockets.data
        plant.has_toilet = edit_form.has_toilet.data
        plant.has_wifi = edit_form.has_wifi.data
        plant.can_take_calls = edit_form.can_take_calls.data
        plant.seats = edit_form.seats.data
        plant.coffee_price = edit_form.coffee_price.data
        db.session.commit()
        return render_template('product_details.html', id=plant_id, plant=plant)

    return render_template('edit_ratings.html', plant=plant, form=edit_form)


@app.route('/about_me')
def about():
    return render_template('about.html')


def merge_dicts(dict1, dict2):
    """inspired by Jamal Bugti https://www.youtube.com/watch?v=nBAxuxM9tpw"""
    if isinstance(dict1, list) and isinstance(dict2, list):
        print('E')
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        print('G')
        print(f'DICT1: {dict1}, DICT2: {dict2}')
        session['ShoppingCart'] = {}
        return dict(list(dict1.items()) + list(dict2.items()))
    return False


@app.route('/add_to_cart', methods=['POST', 'GET'])
def add_to_cart():
    try:
        product_id = request.form.get('product_id')
        quantity_ordered = request.form.get('quantity')
        plant_to_order = Plant.query.filter_by(id=product_id).first()
        print(f'product id = {product_id}, plant_to_order {plant_to_order}, quantity = {quantity_ordered}')
        if product_id and quantity_ordered and request.method == 'POST':
            items_dict = {product_id: {'name': plant_to_order.plant_name,
                                       'price': plant_to_order.price,
                                       'quantity': quantity_ordered,
                                       'image': plant_to_order.img_url}}
            print(f'items_dict {items_dict}')
            if 'ShoppingCart' in session:
                # session['ShoppingCart'] = items_dict
                # print('F')
                if product_id in session['ShoppingCart']:
                    print(
                        f"length:{len(session['ShoppingCart'])} This product is already in your shopping cart : {session['ShoppingCart']}")
                else:
                    print('B')
                    session['ShoppingCart'] = merge_dicts(session['ShoppingCart'], items_dict)
                    print('A')
                    return redirect(request.referrer)

            else:
                session['ShoppingCart'] = items_dict
                print(f"D your shopping cart: {session['ShoppingCart']}")
                return redirect(request.referrer)

    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)


@app.route('/my_cart')
def my_cart():
    if 'ShoppingCart' not in session or len(session['ShoppingCart']) <= 0:
        return redirect(request.referrer)
    grand_total = 0
    for key, product in session['ShoppingCart'].items():
        print(f'EXCEPT key {key}, product {product["price"]}')
        grand_total += float(product["price"])
    return render_template('cart.html', grand_total=grand_total)


@app.route('/deleteitem/<int:id>')
def delete_item(id):
    if 'ShoppingCart' not in session and len(session['ShoppingCart']) <= 0:
        return redirect(url_for('home'))
    try:
        session.modified = True
        for key, item in session['ShoppingCart'].items():
            if int(key) == id:
                session['ShoppingCart'].pop(key, None)
            return redirect(url_for('my_cart'))

    except Exception as e:
        print(e)
        return redirect(url_for('my_cart'))


@app.route('/checkout', methods=['POST', 'GET'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'product': 'prod_LQvmKfBCmQbBlX',
                    # 'price': 'price_1Kk3uYEnlwvGwDmRil1HYen8',
                    'unit_amount': 1500,
                    'currency': 'aud',
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('success', _external=True),
            cancel_url=url_for('cancel', _external=True),
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)


@app.route('/pay', methods=['POST'])
def payment():
    session['ShoppingCart'] = {}
    amount = int(float(request.form['amount']))
    customer = stripe.Customer.create(
        email=request.form['stripeEmail'],
        source=request.form['stripeToken'],
    )

    charge = stripe.Charge.create(
        customer=customer.id,
        description='Checkout',
        amount=amount,
        currency='aud',
    )
    return redirect(url_for('success'))


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/cancel')
def cancel():
    return render_template('cancel.html')


if __name__ == '__main__':
    app.run(debug=True)
