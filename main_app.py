import datetime
import logging
import os
import secrets
import uuid

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

from helper import hash_password, verify_password, login_required
from models import init_db, Session, User, Product

app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True

UPLOAD_FOLDER = "static/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

with app.app_context():
    init_db()


@app.route("/date_time")
def date_time():
    return datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")


@app.route('/')
def index():
    with Session() as db_session:
        user = db_session.query(User).filter(User.username == session.get("username")).first()
        rows = db_session.query(Product).all()
    return render_template('index.html', user=user, rows=rows)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        re_password = request.form.get("re_password")

        if not all([fullname, username, email, password, re_password]):
            flash("All fields are required!", "Error")
            return render_template("signup.html")

        if password != re_password:
            flash("Passwords do not match!", "Error")
            return render_template("signup.html")

        if "@" not in email or "." not in email:
            flash("Invalid email format!", "Error")
            return render_template("signup.html")

        try:
            with Session() as db_session:
                existing_user = db_session.query(User).filter(
                    (User.username == username) | (User.email == email)).first()
                if existing_user:
                    flash("Username or Email already taken!", "Error")
                    return render_template("signup.html")

                pw_hash = hash_password(password)
                new_user = User(fullname=fullname, username=username, email=email, password=pw_hash)
                db_session.add(new_user)
                db_session.commit()

            flash("Account created successfully! Please log in.", "Success")
            logging.info(f"New user registered: {username}")
            return redirect(url_for("login"))
        except Exception as e:
            logging.error(f"Error during signup: {e}")
            flash("An error occurred. Please try again.", "Error")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not all([username, password]):
            flash("Both fields are required!", "Error")
            return render_template("login.html")

        try:
            with Session() as db_session:
                existing_user = db_session.query(User).filter(User.username == username).first()

                if not existing_user or not verify_password(password, existing_user.password):
                    flash("Invalid username or password.", "Error")
                    return render_template("login.html")

                session["username"] = existing_user.username
                flash("Login successful!", "Success")
                logging.info(f"User logged in: {username}")
                return redirect(url_for("dashboard"))
        except Exception as e:
            logging.error(f"Error during login: {e}")
            flash("An error occurred. Please try again.", "Error")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    with Session() as db_session:
        user = db_session.query(User).filter(User.username == session.get("username")).first()
        rows = db_session.query(Product).filter(Product.user_id == user.id).all()
        return render_template("dashboard.html", user=user, rows=rows)


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    with Session() as db_session:
        user = db_session.query(User).filter(User.username == session.get("username")).first()

    if request.method == "POST":
        image = request.files['image']
        if not allowed_file(image.filename):
            flash("Invalid file type. Please upload a valid image.", "Error")
            return render_template("add_product.html", user=user)

        filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(image.filename)[1])
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        category = request.form.get("category")
        name = request.form.get("product_name")
        description = request.form.get("description")
        price_range = request.form.get("price_range")
        comments = request.form.get("comments")

        if not all([category, name, description, price_range]):
            flash("All fields are required except comments.", category="Error")
            return render_template("add_product.html", user=user)

        try:
            with Session() as db_session:
                new_product = Product(
                    category=category,
                    name=name,
                    description=description,
                    price_range=price_range,
                    comments=comments,
                    filename=filename,
                    user=user
                )
                db_session.add(new_product)
                db_session.commit()

            flash("Product added successfully!", category="Success")
            logging.info(f"Product added by {user.username}: {name}")
            return redirect(url_for("dashboard"))
        except Exception as e:
            logging.error(f"Error during product addition: {e}")
            flash("An error occurred. Please try again.", "Error")

    return render_template("add_product.html", user=user)


@app.route("/edit_product")
@login_required
def edit_product():
    with Session() as db_session:
        user = db_session.query(User).filter(User.username == session.get("username")).first()
        rows = db_session.query(Product).filter(Product.user_id == user.id).all()

    return render_template("edit_product.html", rows=rows, user=user)


@app.route("/update_product/<int:pro_id>", methods=["GET", "POST"])
@login_required
def update_product(pro_id):
    try:
        with Session() as db_session:
            user = db_session.query(User).filter(User.username == session.get("username")).first()
            product = db_session.get(Product, pro_id)
            if not product or product.user != user:
                flash("You are not authorized to edit this product", "Error")
                return redirect(url_for("edit_product"))

            if request.method == "POST":
                category = request.form.get("category")
                name = request.form.get("product_name")
                description = request.form.get("description")
                price_range = request.form.get("price_range")
                comments = request.form.get("comments")

                if not all([category, name, description, price_range]):
                    flash("All fields are required except comments.", category="Error")
                    return render_template("add_product.html", user=user)

                product.category = category
                product.name = name
                product.description = description
                product.comments = comments
                product.price_range = price_range
                db_session.commit()

                flash("Product updated successfully", "Success")
                logging.info(f"Product updated by {user.username}: {product.name}")
                return redirect(url_for("edit_product"))

            return render_template("update_product.html", row=product, user=user)
    except Exception as e:
        logging.error(f"Error during product update: {e}")
        flash("An error occurred. Please try again.", "Error")
        return redirect(url_for("edit_product"))


@app.route("/delete_product/<int:pro_id>")
@login_required
def delete_product(pro_id):
    try:
        with Session() as db_session:
            user = db_session.query(User).filter(User.username == session.get("username")).first()
            product = db_session.get(Product, pro_id)
            if not product or product.user != user:
                flash("You are not authorized to delete this product", "Error")
                return redirect(url_for("edit_product"))
            db_session.delete(product)
            db_session.commit()
            flash("Product deleted successfully", "Success")
            logging.info(f"Product deleted by {user.username}: {product.name}")
            return redirect(url_for("edit_product"))
    except Exception as e:
        logging.error(f"Error during product deletion: {e}")
        flash("An error occurred. Please try again.", "Error")
        return redirect(url_for("edit_product"))


@app.route("/logout")
@login_required
def logout():
    username = session.get("username")
    session.clear()
    flash("You have been logged out.", "Success")
    logging.info(f"User logged out: {username}")
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8181, debug=True)
