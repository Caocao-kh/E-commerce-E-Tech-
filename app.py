import os
import sys
from datetime import timedelta
from flask import Flask, request, abort
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from dotenv import load_dotenv
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        load_dotenv()
except ImportError:
    pass

# Import modular models, forms, helpers, and route modules
from models import db, User, Order, get_utc_now
from forms import LoginForm, RegisterForm
from helpers import (
    rate_limiter,
    brute_force_protector,
    validate_password_complexity,
    BLOCKED_USER_AGENTS,
    detect_waf_threat,
    contains_malicious_js,
)
from front import register_front_routes
from admin import register_admin_routes

# ============================================================
# APP INITIALIZATION & CONFIGURATION
# ============================================================

INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DEFAULT_DB_PATH = os.path.join(INSTANCE_DIR, "E_Tech.db").replace("\\", "/")

app = Flask(
    __name__,
    root_path=BASE_DIR,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    instance_path=INSTANCE_DIR,
)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "development-secret-key")
app.secret_key = app.config["SECRET_KEY"]

raw_db_url = os.getenv("DATABASE_URL", "").strip()
if not raw_db_url or ("sqlite:///" in raw_db_url and ("E_Tech.db" in raw_db_url or "etech.db" in raw_db_url)):
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DEFAULT_DB_PATH}"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"timeout": 30},
}

# Session security configuration
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

# Static upload folders
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "profiles")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
# EXTENSIONS INITIALIZATION
# ============================================================

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "warning"
csrf = CSRFProtect(app)


# ============================================================
# FLASK-LOGIN USER LOADER
# ============================================================

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


# ============================================================
# SECURITY HOOKS & MIDDLEWARE
# ============================================================

@app.before_request
def global_security_defense():
    """
    Global pre-request security hook:
    1. DDoS / Rate Limiting defense against flood attacks.
    2. WAF Scanner Blocking against automated scanners (sqlmap, nikto, etc.).
    3. WAF Path Traversal, Command Injection & SQLi detection.
    4. URL JS & Form JS Code Defense.
    """
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()

    # 1. DDoS / Rate Limiting (exempt in automated testing)
    is_testing = bool(app.config.get("TESTING"))
    allowed, retry_after = rate_limiter.check(client_ip, request.path, is_testing=is_testing)
    if not allowed:
        return "429 Too Many Requests: DDoS protection active. Rate limit exceeded.", 429, {"Retry-After": str(retry_after)}

    # 2. Block Automated Security Scanners
    user_agent = (request.user_agent.string or "").lower()
    for scanner in BLOCKED_USER_AGENTS:
        if scanner in user_agent:
            abort(403, description=f"Access blocked by WAF: Automated security scanner detected ({scanner}).")

    # 3. Path & Query Inspection (Path Traversal & XSS)
    path_threat = detect_waf_threat(request.path)
    if path_threat:
        abort(400, description=f"WAF Alert: {path_threat} detected in request path.")

    for param_name, param_value in request.args.items():
        if contains_malicious_js(param_value):
            abort(400, description="WAF Alert: Malicious JavaScript detected in URL query.")
        threat = detect_waf_threat(param_value)
        # Allow literal search query terms in ?q unless they are explicit dangerous exploits
        if threat and not (param_name == "q" and threat == "SQL Injection Attack Signature" and "'" in param_value):
            abort(400, description=f"WAF Alert: {threat} detected in URL query.")

    # 4. Form & Body Threat Inspection
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        for field_name, field_value in request.form.items():
            if contains_malicious_js(field_value):
                abort(400, description="WAF Alert: Unsafe JavaScript code detected in form input field.")
            threat = detect_waf_threat(field_value)
            if threat:
                abort(400, description=f"WAF Alert: {threat} detected in form input.")

        if request.is_json:
            json_data = request.get_json(silent=True) or {}
            if isinstance(json_data, dict):
                for k, v in json_data.items():
                    if isinstance(v, str):
                        if contains_malicious_js(v):
                            abort(400, description="WAF Alert: Unsafe JavaScript payload detected in JSON body.")
                        threat = detect_waf_threat(v)
                        if threat:
                            abort(400, description=f"WAF Alert: {threat} detected in JSON body.")


@app.after_request
def add_security_headers(response):
    """
    Add security headers to prevent Cross-Site Scripting (XSS),
    clickjacking, and MIME sniffing attacks.
    """
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
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


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(400)
def bad_request(error):
    return "400 Bad Request", 400


@app.errorhandler(403)
def forbidden(error):
    return "403 Forbidden", 403


@app.errorhandler(404)
def page_not_found(error):
    return "404 Page Not Found", 404


@app.errorhandler(413)
def request_too_large(error):
    return "File or request too large.", 413


@app.errorhandler(500)
def internal_server_error(error):
    return "500 Internal Server Error", 500


# ============================================================
# REGISTER MODULAR ROUTES
# ============================================================

register_front_routes(app)
register_admin_routes(app)


# ============================================================
# INITIALIZE DATABASE & DEFAULT SEED DATA
# ============================================================

with app.app_context():
    db.create_all()

    # Seed default admin user
    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            email="admin@etech.com",
            role="admin",
            status=True
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)

    # Seed default customer user
    demo_user = User.query.filter_by(username="demo").first()
    if not demo_user:
        demo_user = User(
            username="demo",
            email="demo@example.com",
            role="customer",
            phone="+855 12 345 678",
            address="123 Technology Way, Suite 400, Phnom Penh",
            status=True
        )
        demo_user.set_password("password123")
        db.session.add(demo_user)
        db.session.commit()

    # Seed initial orders for demo user if none exist
    if demo_user and not Order.query.filter_by(user_id=demo_user.id).first():
        order1 = Order(
            order_number="ORD-1092",
            user_id=demo_user.id,
            customer_name="Demo User",
            customer_email="demo@example.com",
            shipping_address="123 Technology Way, Suite 400",
            city="Phnom Penh",
            payment_method="Credit / Debit Card",
            subtotal=1399.00,
            shipping_fee=0.0,
            total_amount=1399.00,
            status="Delivered",
            items_summary="1x Apple iPhone 17 Pro Max (256GB)",
            created_at=get_utc_now() - timedelta(days=2)
        )
        order2 = Order(
            order_number="ORD-1085",
            user_id=demo_user.id,
            customer_name="Demo User",
            customer_email="demo@example.com",
            shipping_address="123 Technology Way, Suite 400",
            city="Phnom Penh",
            payment_method="ABA PAY / Bakong QR",
            subtotal=399.00,
            shipping_fee=0.0,
            total_amount=399.00,
            status="Delivered",
            items_summary="1x Sony WH-1000XM6 Wireless Headphones",
            created_at=get_utc_now() - timedelta(days=40)
        )
        db.session.add_all([order1, order2])

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


# ============================================================
# RE-EXPORTS FOR BACKWARDS COMPATIBILITY & TEST SUITES
# ============================================================

__all__ = [
    "app",
    "db",
    "User",
    "Order",
    "LoginForm",
    "RegisterForm",
    "brute_force_protector",
    "validate_password_complexity",
    "rate_limiter",
]


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
