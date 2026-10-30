import os
import re
import json
import secrets
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.security import check_password_hash

from models import db, User, Order, get_utc_now
from forms import LoginForm, RegisterForm
from helpers import (
    allowed_image_file,
    brute_force_protector,
    DUMMY_TIMING_HASH,
    validate_password_complexity,
    is_safe_redirect_url
)
from products import get_all_products, get_product_by_id


def register_front_routes(app):
    """Register all customer-facing storefront routes on the Flask application."""

    upload_folder = os.path.join(app.root_path, "static", "uploads", "profiles")

    @app.route("/")
    def home():
        module = "home"
        products = get_all_products()
        featured_products = products[:8]
        return render_template(
            "front/home.html",
            products=featured_products,
            module=module,
        )

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        form = RegisterForm()
        if form.validate_on_submit():
            username = form.username.data.strip()
            email = form.email.data.strip().lower()

            # Check duplicate username
            existing_username = User.query.filter(
                db.func.lower(User.username) == username.lower()
            ).first()

            if existing_username:
                flash("Username already exists.", "danger")
                return render_template("front/register.html", form=form, module="register")

            # Check duplicate email
            existing_email = User.query.filter(
                db.func.lower(User.email) == email
            ).first()

            if existing_email:
                flash("Email already registered.", "danger")
                return render_template("front/register.html", form=form, module="register")

            # Validate password complexity
            is_strong, msg = validate_password_complexity(form.password.data)
            if not is_strong:
                flash(msg, "danger")
                return render_template("front/register.html", form=form, module="register")

            # Create user
            try:
                user = User(
                    username=username,
                    email=email,
                    role="customer"
                )
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()

                flash("Registration successful. You can now login.", "success")
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error registering user {username}: {e}")
                flash("A database error occurred while creating your account. Please try again.", "danger")
                return render_template("front/register.html", form=form, module="register")

        return render_template("front/register.html", form=form, module="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        form = LoginForm()
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()

        if form.validate_on_submit():
            login_input = form.email.data.strip().lower()

            # 1. Brute Force Lockout Inspection
            is_ip_locked, rem_ip = brute_force_protector.is_locked(client_ip)
            is_user_locked, rem_user = brute_force_protector.is_locked(login_input)
            if is_ip_locked or is_user_locked:
                mins = max(rem_ip, rem_user) // 60 + 1
                flash(f"Account access temporarily restricted due to excessive failed attempts. Please retry in {mins} minute(s).", "danger")
                return render_template("front/login.html", form=form, module="login")

            # 2. Query user by email OR username (case-insensitive)
            user = User.query.filter(
                (db.func.lower(User.email) == login_input) |
                (db.func.lower(User.username) == login_input)
            ).first()

            # 3. Authenticate with Timing Attack Defense
            if user and user.status and user.check_password(form.password.data):
                brute_force_protector.record_success(client_ip)
                brute_force_protector.record_success(login_input)
                login_user(user)
                flash(f"Welcome back, {user.username}!", "success")

                next_page = request.args.get("next")
                if next_page and is_safe_redirect_url(next_page):
                    return redirect(next_page)
                if user.role == "admin":
                    return redirect(url_for("admin_dashboard"))
                return redirect(url_for("home"))

            # Normalize execution timing if user doesn't exist
            if not user:
                check_password_hash(DUMMY_TIMING_HASH, form.password.data)

            # Record failure for Brute Force Lockout
            is_locked_now, _ = brute_force_protector.record_failure(client_ip)
            brute_force_protector.record_failure(login_input)

            if user and not user.status:
                flash("Your account has been deactivated.", "danger")
            elif is_locked_now:
                flash("Too many failed login attempts. Your account has been temporarily locked for 15 minutes.", "danger")
            else:
                flash("Invalid email/username or password.", "danger")

        return render_template("front/login.html", form=form, module="login")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("home"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            new_username = request.form.get("username", "").strip()
            new_email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()

            # 1. Validate & Update Username
            if new_username and new_username.lower() != current_user.username.lower():
                if len(new_username) < 3 or len(new_username) > 80:
                    flash("Username must be between 3 and 80 characters long.", "danger")
                    return redirect(url_for("profile"))

                existing_user = User.query.filter(
                    db.func.lower(User.username) == new_username.lower(),
                    User.id != current_user.id
                ).first()
                if existing_user:
                    flash("Username is already taken by another account.", "danger")
                    return redirect(url_for("profile"))

                current_user.username = new_username

            # 2. Validate & Update Email Address
            if new_email and new_email != current_user.email.lower():
                email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
                if not re.match(email_pattern, new_email):
                    flash("Please enter a valid email address.", "danger")
                    return redirect(url_for("profile"))

                existing_email = User.query.filter(
                    db.func.lower(User.email) == new_email,
                    User.id != current_user.id
                ).first()
                if existing_email:
                    flash("Email address is already registered by another account.", "danger")
                    return redirect(url_for("profile"))

                current_user.email = new_email

            # 3. Update Phone & Address
            current_user.phone = phone
            current_user.address = address

            # 4. Handle Profile Image Upload
            if "profile_image" in request.files:
                file = request.files["profile_image"]
                if file and file.filename != "":
                    if allowed_image_file(file.filename):
                        ext = file.filename.rsplit(".", 1)[1].lower()
                        filename = f"user_{current_user.id}_{int(get_utc_now().timestamp())}.{ext}"
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)
                        current_user.profile_image = f"uploads/profiles/{filename}"
                    else:
                        flash("Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.", "danger")
                        return redirect(url_for("profile"))

            try:
                db.session.commit()
                flash("Profile updated successfully.", "success")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error updating profile for user {current_user.id}: {e}")
                flash("A database error occurred while updating your profile.", "danger")

            return redirect(url_for("profile"))

        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template("front/profile.html", orders=orders, module="profile")

    @app.route("/checkout/process", methods=["POST"])
    @login_required
    def process_checkout():
        full_name = request.form.get("full_name", current_user.username).strip() or current_user.username
        email = request.form.get("email", current_user.email).strip() or current_user.email
        address = request.form.get("address", current_user.address or "123 Technology Way").strip() or "123 Technology Way"
        city = request.form.get("city", "Phnom Penh").strip() or "Phnom Penh"
        payment_method = request.form.get("payment_method", "Credit / Debit Card").strip() or "Credit / Debit Card"
        cart_json = request.form.get("cart_data", "[]")

        try:
            cart_items = json.loads(cart_json) if cart_json else []
        except Exception:
            cart_items = []

        all_products = get_all_products()
        prod_by_id = {int(p.get("id")): p for p in all_products if "id" in p}
        prod_by_title = {p.get("title", "").strip().lower(): p for p in all_products}

        subtotal = 0.0
        items_summary_list = []
        if cart_items and isinstance(cart_items, list):
            for item in cart_items:
                try:
                    raw_id = item.get("id")
                    qty = max(1, min(int(item.get("quantity", 1)), 50))
                    title = str(item.get("title", "Product")).strip()

                    product = None
                    if raw_id is not None:
                        try:
                            product = prod_by_id.get(int(raw_id))
                        except (ValueError, TypeError):
                            pass
                    if not product and title:
                        product = prod_by_title.get(title.lower())

                    if product:
                        authoritative_price = float(product.get("price", 0.0))
                        item_title = product.get("title", title)
                    else:
                        authoritative_price = float(item.get("price", 0.0))
                        item_title = title

                    subtotal += authoritative_price * qty
                    items_summary_list.append(f"{qty}x {item_title}")
                except (ValueError, TypeError):
                    continue

        if not items_summary_list:
            items_summary_list.append("1x Apple iPhone 17 Pro Max")
            subtotal = 1399.00

        items_summary = ", ".join(items_summary_list)
        shipping_fee = 0.0 if subtotal >= 100.0 else 15.0
        total_amount = round(subtotal + shipping_fee, 2)

        order_num = f"ORD-{secrets.token_hex(4).upper()}"
        while Order.query.filter_by(order_number=order_num).first():
            order_num = f"ORD-{secrets.token_hex(4).upper()}"

        order = Order(
            order_number=order_num,
            user_id=current_user.id,
            customer_name=full_name,
            customer_email=email,
            shipping_address=address,
            city=city,
            payment_method=payment_method,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            status="Processing",
            items_summary=items_summary
        )

        db.session.add(order)
        db.session.commit()

        flash(f"Order #{order_num} placed successfully! View your order status below.", "success")
        return redirect(url_for("profile"))

    @app.route("/products")
    def product_list():
        module = "products"
        all_products = get_all_products()
        filtered_products = list(all_products)

        query = request.args.get("q", "").strip()
        selected_category = request.args.get("category", "").strip()
        selected_brand = request.args.get("brand", "").strip()
        selected_min_price = request.args.get("min_price", "").strip()
        selected_max_price = request.args.get("max_price", "").strip()
        selected_rating = request.args.get("rating", "").strip()
        selected_sort = request.args.get("sort", "default").strip()

        if query:
            search_text = query.lower()
            filtered_products = [
                p for p in filtered_products
                if search_text in p.get("title", "").lower()
                or search_text in p.get("description", "").lower()
                or search_text in p.get("brand", "").lower()
                or search_text in p.get("category", "").lower()
            ]

        if selected_category:
            filtered_products = [p for p in filtered_products if p.get("category", "").lower() == selected_category.lower()]

        if selected_brand:
            filtered_products = [p for p in filtered_products if p.get("brand", "").lower() == selected_brand.lower()]

        if selected_min_price:
            try:
                min_price = float(selected_min_price)
                filtered_products = [p for p in filtered_products if float(p.get("price", 0)) >= min_price]
            except ValueError:
                pass

        if selected_max_price:
            try:
                max_price = float(selected_max_price)
                filtered_products = [p for p in filtered_products if float(p.get("price", 0)) <= max_price]
            except ValueError:
                pass

        if selected_rating:
            try:
                min_rating = float(selected_rating)
                filtered_products = [p for p in filtered_products if float(p.get("rating", 0)) >= min_rating]
            except ValueError:
                pass

        if selected_sort == "newest":
            filtered_products.sort(key=lambda p: p.get("isNew", False), reverse=True)
        elif selected_sort == "price_low":
            filtered_products.sort(key=lambda p: float(p.get("price", 0)))
        elif selected_sort == "price_high":
            filtered_products.sort(key=lambda p: float(p.get("price", 0)), reverse=True)
        elif selected_sort == "rating":
            filtered_products.sort(key=lambda p: float(p.get("rating", 0)), reverse=True)
        elif selected_sort == "name":
            filtered_products.sort(key=lambda p: p.get("title", "").lower())

        categories = sorted({p.get("category", "") for p in all_products if p.get("category")})
        brands = sorted({p.get("brand", "") for p in all_products if p.get("brand")})

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

    @app.route("/product/<int:product_id>")
    def product_detail(product_id):
        module = "products"
        product = get_product_by_id(product_id)
        if not product:
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

    @app.route("/deals")
    def deals():
        module = "deals"
        products = get_all_products()
        return render_template("front/deals.html", products=products, module=module)

    @app.route("/about")
    def about():
        module = "about"
        return render_template("front/about.html", module=module)

    @app.route("/cart")
    def cart():
        module = "cart"
        return render_template("front/cart.html", module=module)

    @app.route("/wishlist")
    def wishlist():
        module = "wishlist"
        return render_template("front/wishlist.html", module=module)
