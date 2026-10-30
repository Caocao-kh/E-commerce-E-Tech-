import os
import re
import json
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from models import db, User, Order, get_utc_now
from forms import LoginForm
from helpers import (
    admin_required,
    allowed_image_file,
    brute_force_protector,
    DUMMY_TIMING_HASH,
    validate_password_complexity,
    is_safe_redirect_url
)
from products import get_all_products, get_product_by_id


def parse_order_items(summary_str, subtotal=0.0):
    """Parse an order's items_summary string or JSON into rich product item dicts."""
    items = []
    if not summary_str:
        return items

    all_prods = get_all_products()
    prod_map = {p.get("title", "").strip().lower(): p for p in all_prods}

    try:
        data = json.loads(summary_str)
        if isinstance(data, list):
            for it in data:
                title = it.get("title", "Product")
                qty = max(1, int(it.get("quantity", 1)))
                price = float(it.get("price", 0.0))
                image = it.get("image") or ""
                category = it.get("category", "General")
                if not image:
                    matched = prod_map.get(title.lower())
                    if matched:
                        image = matched.get("image", "")
                        category = matched.get("category", "General")
                        if price == 0:
                            price = float(matched.get("price", 0.0))
                items.append({
                    "title": title,
                    "quantity": qty,
                    "price": price,
                    "total": round(price * qty, 2),
                    "image": image or "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd",
                    "category": category,
                })
            if items:
                return items
    except Exception:
        pass

    parts = [p.strip() for p in summary_str.split(",") if p.strip()]
    for part in parts:
        match = re.match(r"^(\d+)\s*[xX]\s*(.+)$", part)
        if match:
            qty = max(1, int(match.group(1)))
            title = match.group(2).strip()
        else:
            qty = 1
            title = part.strip()

        matched = prod_map.get(title.lower())
        if not matched:
            for p_title, p_obj in prod_map.items():
                if p_title in title.lower() or title.lower() in p_title:
                    matched = p_obj
                    break

        price = float(matched.get("price", 0.0)) if matched else 0.0
        image = matched.get("image", "") if matched else ""
        category = matched.get("category", "General") if matched else "General"

        items.append({
            "title": matched.get("title", title) if matched else title,
            "quantity": qty,
            "price": price,
            "total": round(price * qty, 2),
            "image": image or "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd",
            "category": category,
        })

    total_calc = sum(it["total"] for it in items)
    if total_calc == 0 and subtotal > 0 and items:
        total_qty = sum(it["quantity"] for it in items)
        unit_price = round(subtotal / max(1, total_qty), 2)
        for it in items:
            it["price"] = unit_price
            it["total"] = round(unit_price * it["quantity"], 2)

    return items


def register_admin_routes(app):
    """Register all administrator control panel routes on the Flask application."""

    upload_folder = os.path.join(app.root_path, "static", "uploads", "profiles")
    os.makedirs(upload_folder, exist_ok=True)

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if current_user.is_authenticated and getattr(current_user, "role", "") == "admin":
            return redirect(url_for("admin_dashboard"))

        form = LoginForm()
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()

        if form.validate_on_submit():
            login_input = form.email.data.strip().lower()

            # 1. Brute Force Lockout Inspection
            is_ip_locked, rem_ip = brute_force_protector.is_locked(client_ip)
            is_user_locked, rem_user = brute_force_protector.is_locked(login_input)
            if is_ip_locked or is_user_locked:
                mins = max(rem_ip, rem_user) // 60 + 1
                flash(f"Access temporarily restricted due to multiple failed login attempts. Retry in {mins} min.", "danger")
                return render_template("admin/login.html", form=form)

            # 2. Query user by email OR username (case-insensitive)
            user = User.query.filter(
                (db.func.lower(User.email) == login_input) |
                (db.func.lower(User.username) == login_input)
            ).first()

            # 3. Authenticate with Timing Attack Defense
            if user and user.status and user.check_password(form.password.data):
                if user.role != "admin":
                    flash("Access Denied: This account is a Customer account and does not have Administrator privileges.", "danger")
                    return render_template("admin/login.html", form=form)

                brute_force_protector.record_success(client_ip)
                brute_force_protector.record_success(login_input)
                login_user(user)
                flash(f"Welcome to Administration Portal, {user.username}!", "success")

                next_page = request.args.get("next")
                if next_page and is_safe_redirect_url(next_page) and not next_page.endswith("/login"):
                    return redirect(next_page)
                return redirect(url_for("admin_dashboard"))

            if not user:
                check_password_hash(DUMMY_TIMING_HASH, form.password.data)

            is_locked_now, _ = brute_force_protector.record_failure(client_ip)
            brute_force_protector.record_failure(login_input)

            if user and not user.status:
                flash("This administrator account has been deactivated.", "danger")
            elif is_locked_now:
                flash("Too many failed attempts. Login locked for 15 minutes.", "danger")
            else:
                flash("Invalid administrator credentials.", "danger")

        return render_template("admin/login.html", form=form)

    @app.route("/admin/logout")
    @login_required
    def admin_logout():
        logout_user()
        flash("You have been signed out of the Administrator Portal.", "info")
        return redirect(url_for("admin_login"))

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        products = get_all_products()
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
        total_orders = Order.query.count()
        total_sales = db.session.query(db.func.sum(Order.total_amount)).filter(Order.status != "Cancelled").scalar() or 0.0
        total_customers = User.query.filter_by(role="customer").count() or User.query.count()
        active_products_count = len(products)
        pending_orders_count = Order.query.filter(Order.status.in_(["Pending", "Processing"])).count()

        return render_template(
            "admin/dashboard.html",
            products=products,
            recent_orders=recent_orders,
            total_orders=total_orders,
            total_sales=total_sales,
            total_customers=total_customers,
            active_products_count=active_products_count,
            pending_orders_count=pending_orders_count,
            active_page="dashboard",
        )

    @app.route("/admin/products")
    @admin_required
    def admin_products():
        products = get_all_products()
        return render_template(
            "admin/products.html",
            products=products,
            active_page="products",
        )

    @app.route("/admin/products/new", methods=["GET", "POST"])
    @admin_required
    def admin_product_new():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            price_val = request.form.get("price", "0").strip()
            old_price_val = request.form.get("oldPrice", "0").strip()
            stock_val = request.form.get("stock", "20").strip()
            category = request.form.get("category", "smartphones").strip()
            brand = request.form.get("brand", "").strip()
            description = request.form.get("description", "").strip()
            image = request.form.get("image", "").strip() or "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd"
            is_new = bool(request.form.get("isNew"))

            try:
                price = float(price_val)
            except ValueError:
                price = 0.0

            try:
                old_price = float(old_price_val) if old_price_val else 0.0
            except ValueError:
                old_price = 0.0

            try:
                stock = int(stock_val)
            except ValueError:
                stock = 20

            all_prods = get_all_products()
            max_id = max([p.get("id", 0) for p in all_prods], default=0)
            new_prod = {
                "id": max_id + 1,
                "title": title,
                "isNew": is_new,
                "oldPrice": old_price,
                "price": price,
                "discountedPrice": price,
                "description": description,
                "category": category,
                "brand": brand,
                "stock": stock,
                "rating": 5.0,
                "reviewsCount": 0,
                "image": image
            }
            all_prods.append(new_prod)
            flash(f'Product "{title}" created successfully!', "success")
            return redirect(url_for("admin_products"))

        return render_template(
            "admin/product_form.html",
            product=None,
            is_edit=False,
            active_page="products",
        )

    @app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
    @admin_required
    def admin_product_edit(product_id):
        product = get_product_by_id(product_id)
        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for("admin_products"))

        if request.method == "POST":
            product["title"] = request.form.get("title", product.get("title")).strip()
            try:
                product["price"] = float(request.form.get("price", product.get("price")))
            except (ValueError, TypeError):
                pass

            try:
                product["oldPrice"] = float(request.form.get("oldPrice", product.get("oldPrice", 0)))
            except (ValueError, TypeError):
                pass

            try:
                product["stock"] = int(request.form.get("stock", product.get("stock")))
            except (ValueError, TypeError):
                pass

            product["category"] = request.form.get("category", product.get("category")).strip()
            product["brand"] = request.form.get("brand", product.get("brand")).strip()
            product["description"] = request.form.get("description", product.get("description")).strip()
            product["image"] = request.form.get("image", product.get("image")).strip()
            product["isNew"] = bool(request.form.get("isNew"))

            flash(f'Product "{product["title"]}" updated successfully!', "success")
            return redirect(url_for("admin_products"))

        return render_template(
            "admin/product_form.html",
            product=product,
            is_edit=True,
            active_page="products",
        )

    @app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
    @admin_required
    def admin_product_delete(product_id):
        all_prods = get_all_products()
        product = get_product_by_id(product_id)
        if product and product in all_prods:
            all_prods.remove(product)
            flash(f'Product "{product.get("title")}" deleted successfully.', 'warning')
        else:
            flash("Product not found.", "danger")
        return redirect(url_for("admin_products"))

    @app.route("/admin/categories", methods=["GET", "POST"])
    @admin_required
    def admin_categories():
        all_prods = get_all_products()
        category_counts = {}
        for p in all_prods:
            cat = p.get("category", "Uncategorized").title()
            category_counts[cat] = category_counts.get(cat, 0) + 1

        if request.method == "POST":
            cat_name = request.form.get("name", "").strip()
            if cat_name:
                flash(f'Category "{cat_name}" added successfully!', "success")
            return redirect(url_for("admin_categories"))

        return render_template(
            "admin/categories.html",
            category_counts=category_counts,
            active_page="categories",
        )

    @app.route("/admin/orders")
    @admin_required
    def admin_orders():
        status_filter = request.args.get("status", "").strip()
        search_query = request.args.get("q", "").strip()

        query = Order.query
        if status_filter and status_filter.lower() != "all":
            query = query.filter(db.func.lower(Order.status) == status_filter.lower())

        if search_query:
            search_like = f"%{search_query}%"
            query = query.filter(
                (Order.order_number.ilike(search_like))
                | (Order.customer_name.ilike(search_like))
                | (Order.customer_email.ilike(search_like))
                | (Order.items_summary.ilike(search_like))
            )

        orders = query.order_by(Order.created_at.desc()).all()

        status_counts = {
            "all": Order.query.count(),
            "pending": Order.query.filter(Order.status.ilike("pending")).count(),
            "processing": Order.query.filter(Order.status.ilike("processing")).count(),
            "shipped": Order.query.filter(Order.status.ilike("shipped")).count(),
            "delivered": Order.query.filter(Order.status.ilike("delivered")).count(),
            "cancelled": Order.query.filter(Order.status.ilike("cancelled")).count(),
        }

        return render_template(
            "admin/orders.html",
            orders=orders,
            status_counts=status_counts,
            current_status=status_filter or "all",
            search_query=search_query,
            active_page="orders",
        )

    @app.route("/admin/orders/<order_id>", methods=["GET", "POST"])
    @admin_required
    def admin_order_detail(order_id):
        filter_cond = (Order.order_number == order_id) | (Order.order_number == f"#{order_id}")
        if order_id.isdigit():
            filter_cond = filter_cond | (Order.id == int(order_id))
        order = Order.query.filter(filter_cond).first()

        if not order:
            flash(f"Order #{order_id} was not found.", "danger")
            return redirect(url_for("admin_orders"))

        if request.method == "POST":
            new_status = request.form.get("status", "").strip()
            allowed_statuses = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
            if new_status in allowed_statuses:
                order.status = new_status
                db.session.commit()
                flash(f"Order #{order.order_number} status updated to {new_status}!", "success")
                return redirect(url_for("admin_order_detail", order_id=order.order_number))
            else:
                flash("Invalid status specified.", "danger")

        order_items = parse_order_items(order.items_summary, order.subtotal)
        customer_order_count = Order.query.filter_by(customer_email=order.customer_email).count()

        return render_template(
            "admin/order_detail.html",
            order=order,
            order_id=order.order_number,
            order_items=order_items,
            customer_order_count=customer_order_count,
            active_page="orders",
        )

    @app.route("/admin/orders/<order_id>/status", methods=["POST"])
    @admin_required
    def admin_order_update_status(order_id):
        filter_cond = (Order.order_number == order_id) | (Order.order_number == f"#{order_id}")
        if order_id.isdigit():
            filter_cond = filter_cond | (Order.id == int(order_id))
        order = Order.query.filter(filter_cond).first()

        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for("admin_orders"))

        new_status = request.form.get("status", "").strip()
        allowed_statuses = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
        if new_status in allowed_statuses:
            order.status = new_status
            db.session.commit()
            flash(f"Order #{order.order_number} status updated to {new_status}!", "success")
        else:
            flash("Invalid status specified.", "danger")

        next_url = request.form.get("next") or request.referrer or url_for("admin_orders")
        return redirect(next_url)

    @app.route("/admin/orders/<order_id>/delete", methods=["POST"])
    @admin_required
    def admin_order_delete(order_id):
        filter_cond = (Order.order_number == order_id) | (Order.order_number == f"#{order_id}")
        if order_id.isdigit():
            filter_cond = filter_cond | (Order.id == int(order_id))
        order = Order.query.filter(filter_cond).first()

        if order:
            order_num = order.order_number
            db.session.delete(order)
            db.session.commit()
            flash(f"Order #{order_num} has been deleted.", "warning")
        else:
            flash("Order not found.", "danger")

        return redirect(url_for("admin_orders"))

    @app.route("/admin/customers")
    @admin_required
    def admin_customers():
        users = User.query.all()
        return render_template(
            "admin/customers.html",
            users=users,
            active_page="customers",
        )

    @app.route("/admin/deals")
    @admin_required
    def admin_deals():
        return render_template(
            "admin/deals.html",
            active_page="deals",
        )

    @app.route("/admin/settings")
    @admin_required
    def admin_settings():
        return render_template(
            "admin/settings.html",
            active_page="settings",
        )

    @app.route("/admin/profile", methods=["GET", "POST"])
    @admin_required
    def admin_profile():
        if request.method == "POST":
            action = request.form.get("action", "update_details")

            if action == "change_password":
                current_pwd = request.form.get("current_password", "")
                new_pwd = request.form.get("new_password", "")
                confirm_pwd = request.form.get("confirm_password", "")

                if not current_user.check_password(current_pwd):
                    flash("Current password is incorrect.", "danger")
                    return redirect(url_for("admin_profile"))

                if new_pwd != confirm_pwd:
                    flash("New passwords do not match.", "danger")
                    return redirect(url_for("admin_profile"))

                is_strong, msg = validate_password_complexity(new_pwd)
                if not is_strong:
                    flash(msg, "danger")
                    return redirect(url_for("admin_profile"))

                current_user.set_password(new_pwd)
                db.session.commit()
                flash("Administrator password changed successfully!", "success")
                return redirect(url_for("admin_profile"))

            # Default action: update personal details
            new_username = request.form.get("username", "").strip()
            new_email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()

            if new_username and new_username.lower() != current_user.username.lower():
                if len(new_username) < 3 or len(new_username) > 80:
                    flash("Username must be between 3 and 80 characters long.", "danger")
                    return redirect(url_for("admin_profile"))

                existing_user = User.query.filter(
                    db.func.lower(User.username) == new_username.lower(),
                    User.id != current_user.id
                ).first()
                if existing_user:
                    flash("Username is already taken by another account.", "danger")
                    return redirect(url_for("admin_profile"))

                current_user.username = new_username

            if new_email and new_email != current_user.email.lower():
                email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
                if not re.match(email_pattern, new_email):
                    flash("Please enter a valid email address.", "danger")
                    return redirect(url_for("admin_profile"))

                existing_email = User.query.filter(
                    db.func.lower(User.email) == new_email,
                    User.id != current_user.id
                ).first()
                if existing_email:
                    flash("Email address is already registered by another account.", "danger")
                    return redirect(url_for("admin_profile"))

                current_user.email = new_email

            current_user.phone = phone

            if "profile_image" in request.files:
                file = request.files["profile_image"]
                if file and file.filename != "":
                    if allowed_image_file(file.filename):
                        ext = file.filename.rsplit(".", 1)[1].lower()
                        filename = f"admin_{current_user.id}_{int(get_utc_now().timestamp())}.{ext}"
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)
                        current_user.profile_image = f"uploads/profiles/{filename}"
                    else:
                        flash("Invalid image format. Allowed: PNG, JPG, JPEG, GIF, WEBP.", "danger")
                        return redirect(url_for("admin_profile"))

            try:
                db.session.commit()
                flash("Administrator profile updated successfully!", "success")
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error updating admin profile: {e}")
                flash("A database error occurred while updating profile.", "danger")

            return redirect(url_for("admin_profile"))

        return render_template("admin/profile.html", active_page="profile")
