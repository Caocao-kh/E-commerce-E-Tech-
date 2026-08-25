import os
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    TextAreaField
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    ValidationError
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from flask_wtf.csrf import CSRFProtect

from products import get_all_products, get_product_by_id


# ============================================================
# APP CONFIGURATION
# ============================================================
app = Flask(__name__)
app.secret_key = "dev-secret-key"

# =========================================================
# CONFIGURATION
# =========================================================

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-secret-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///E_Tech.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session security & CSRF defense configuration
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in HTTPS production
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

# CSRF Session Defense
app.config["WTF_CSRF_ENABLED"] = True
app.config["WTF_CSRF_TIME_LIMIT"] = 3600
app.config["WTF_CSRF_CHECK_DEFAULT"] = True

# Maximum upload/request size: 2 MB
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


# =========================================================
# EXTENSIONS
# =========================================================

db = SQLAlchemy(app)

migrate = Migrate(app, db)

login_manager = LoginManager(app)

login_manager.login_view = "login"

csrf = CSRFProtect(app)

# =========================================================
# USER MODEL
# =========================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="customer"
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    address = db.Column(
        db.Text,
        nullable=True
    )

    profile_image = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -----------------------------------------------------
    # PASSWORD HASHING
    # -----------------------------------------------------

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

    def __repr__(self):
        return f"<User {self.username}>"

# =========================================================
# FLASK-LOGIN
# =========================================================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )

# =========================================================
# FORMS
# =========================================================

class LoginForm(FlaskForm):

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField(
        "Login"
    )


class RegisterForm(FlaskForm):

    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=80)
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128)
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Passwords must match."
            )
        ]
    )

    submit = SubmitField(
        "Create Account"
    )

# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    module = "home"
    products = get_all_products()

    # Show featured products on homepage
    featured_products = products[:8]

    return render_template(
        "front/home.html",
        products=featured_products,
        module=module,
    )

# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    form = RegisterForm()

    if form.validate_on_submit():

        username = form.username.data.strip()

        email = form.email.data.strip().lower()

        # Check duplicate username
        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash(
                "Username already exists.",
                "danger"
            )

            return render_template(
                "register.html",
                form=form
            )


        # Check duplicate email
        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash(
                "Email already registered.",
                "danger"
            )

            return render_template(
                "register.html",
                form=form
            )


        # Create user
        user = User(
            username=username,
            email=email,
            role="customer"
        )

        # NEVER store plaintext password
        user.set_password(
            form.password.data
        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Registration successful. You can now login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html",
        form=form
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    form = LoginForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()


        if (
            user
            and user.status
            and user.check_password(
                form.password.data
            )
        ):

            login_user(user)

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("home")
            )


        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template(
        "login.html",
        form=form
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html"
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(403)
def forbidden(error):

    return "403 Forbidden", 403


@app.errorhandler(404)
def page_not_found(error):

    return "404 Page Not Found", 404


@app.errorhandler(413)
def request_too_large(error):

    return "File or request too large.", 413


# =========================================================
# SECURITY HEADERS (XSS & CONTENT SECURITY POLICY)
# =========================================================

@app.after_request
def add_security_headers(response):
    """
    Add security headers to prevent Cross-Site Scripting (XSS),
    clickjacking, and MIME sniffing attacks.
    """
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp_policy
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ============================================================
# PRODUCTS
# ============================================================

@app.route("/products")
def product_list():
    module = "products"

    # --------------------------------------------------------
    # Get all products
    # --------------------------------------------------------
    all_products = get_all_products()
    filtered_products = list(all_products)  # copy to avoid mutation

    # --------------------------------------------------------
    # GET FILTER VALUES
    # --------------------------------------------------------
    query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()
    selected_brand = request.args.get("brand", "").strip()
    selected_min_price = request.args.get("min_price", "").strip()
    selected_max_price = request.args.get("max_price", "").strip()
    selected_rating = request.args.get("rating", "").strip()
    selected_sort = request.args.get("sort", "default").strip()

    # ========================================================
    # SEARCH
    # ========================================================
    if query:
        search_text = query.lower()
        filtered_products = [
            product for product in filtered_products
            if search_text in product.get("title", "").lower()
            or search_text in product.get("description", "").lower()
            or search_text in product.get("brand", "").lower()
            or search_text in product.get("category", "").lower()
        ]

    # ========================================================
    # CATEGORY FILTER
    # ========================================================
    if selected_category:
        filtered_products = [
            product for product in filtered_products
            if product.get("category", "").lower() == selected_category.lower()
        ]

    # ========================================================
    # BRAND FILTER
    # ========================================================
    if selected_brand:
        filtered_products = [
            product for product in filtered_products
            if product.get("brand", "").lower() == selected_brand.lower()
        ]

    # ========================================================
    # MINIMUM PRICE
    # ========================================================
    if selected_min_price:
        try:
            min_price = float(selected_min_price)
            filtered_products = [
                product for product in filtered_products
                if float(product.get("price", 0)) >= min_price
            ]
        except ValueError:
            pass

    # ========================================================
    # MAXIMUM PRICE
    # ========================================================
    if selected_max_price:
        try:
            max_price = float(selected_max_price)
            filtered_products = [
                product for product in filtered_products
                if float(product.get("price", 0)) <= max_price
            ]
        except ValueError:
            pass

    # ========================================================
    # RATING FILTER
    # ========================================================
    if selected_rating:
        try:
            minimum_rating = float(selected_rating)
            filtered_products = [
                product for product in filtered_products
                if float(product.get("rating", 0)) >= minimum_rating
            ]
        except ValueError:
            pass

    # ========================================================
    # SORTING
    # ========================================================
    if selected_sort == "newest":
        filtered_products.sort(
            key=lambda product: product.get("isNew", False),
            reverse=True
        )
    elif selected_sort == "price_low":
        filtered_products.sort(
            key=lambda product: float(product.get("price", 0))
        )
    elif selected_sort == "price_high":
        filtered_products.sort(
            key=lambda product: float(product.get("price", 0)),
            reverse=True
        )
    elif selected_sort == "rating":
        filtered_products.sort(
            key=lambda product: float(product.get("rating", 0)),
            reverse=True
        )
    elif selected_sort == "name":
        filtered_products.sort(
            key=lambda product: product.get("title", "").lower()
        )

    # ========================================================
    # FILTER OPTIONS
    # ========================================================
    categories = sorted({
        product.get("category", "")
        for product in all_products if product.get("category")
    })

    brands = sorted({
        product.get("brand", "")
        for product in all_products if product.get("brand")
    })

    # ========================================================
    # RENDER PRODUCTS PAGE
    # ========================================================
    return render_template(
        "front/products/products.html",
        products=filtered_products,
        categories=categories,
        brands=brands,
        query=query,
        selected_category=selected_category,
        selected_brand=selected_brand,
        selected_min_price=selected_min_price,
        selected_max_price=selected_max_price,
        selected_rating=selected_rating,
        selected_sort=selected_sort,
        module=module,
    )


# ============================================================
# PRODUCT DETAIL
# ============================================================

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    module = "products"
    product = get_product_by_id(product_id)
    if not product:
        # Fallback to first product if ID not found
        all_products = get_all_products()
        product = all_products[0] if all_products else {}

    all_products = get_all_products()
    related = [p for p in all_products if p.get("category") == product.get("category") and p.get("id") != product.get("id")][:4]

    return render_template(
        "front/products/detail.html",
        product=product,
        related_products=related,
        module=module,
    )


# ============================================================
# DEALS PAGE
# ============================================================

@app.route("/deals")
def deals():
    module = "deals"
    products = get_all_products()
    return render_template(
        "front/deals.html",
        products=products,
        module=module,
    )


# ============================================================
# ABOUT PAGE
# ============================================================

@app.route("/about")
def about():
    module = "about"
    return render_template(
        "front/about.html",
        module=module,
    )


# ============================================================
# CART PAGE
# ============================================================

@app.route("/cart")
def cart():
    module = "cart"
    return render_template(
        "front/cart.html",
        module=module,
    )


# ============================================================
# WISHLIST PAGE
# ============================================================

@app.route("/wishlist")
def wishlist():
    module = "wishlist"
    return render_template(
        "front/wishlist.html",
        module=module,
    )


# ============================================================
# ADMIN ROUTES
# ============================================================

@app.route("/admin")
def admin_dashboard():
    products = get_all_products()
    return render_template(
        "admin/dashboard.html",
        products=products,
        active_page="dashboard",
    )


@app.route("/admin/products")
def admin_products():
    products = get_all_products()
    return render_template(
        "admin/products.html",
        products=products,
        active_page="products",
    )


@app.route("/admin/products/new")
def admin_product_new():
    return render_template(
        "admin/product_form.html",
        product=None,
        is_edit=False,
        active_page="products",
    )


@app.route("/admin/products/edit/<int:product_id>")
def admin_product_edit(product_id):
    product = get_product_by_id(product_id)
    return render_template(
        "admin/product_form.html",
        product=product,
        is_edit=True,
        active_page="products",
    )


@app.route("/admin/categories")
def admin_categories():
    return render_template(
        "admin/categories.html",
        active_page="categories",
    )


@app.route("/admin/orders")
def admin_orders():
    return render_template(
        "admin/orders.html",
        active_page="orders",
    )


@app.route("/admin/orders/<order_id>")
def admin_order_detail(order_id):
    return render_template(
        "admin/order_detail.html",
        order_id=order_id,
        active_page="orders",
    )


@app.route("/admin/customers")
def admin_customers():
    return render_template(
        "admin/customers.html",
        active_page="customers",
    )


@app.route("/admin/deals")
def admin_deals():
    return render_template(
        "admin/deals.html",
        active_page="deals",
    )


@app.route("/admin/settings")
def admin_settings():
    return render_template(
        "admin/settings.html",
        active_page="settings",
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)

