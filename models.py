from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def get_utc_now():
    """Return timezone-naive UTC timestamp for SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256:600000",
            salt_length=16
        )

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(80), nullable=True)
    payment_method = db.Column(db.String(50), default="Credit / Debit Card")
    subtotal = db.Column(db.Float, default=0.0)
    shipping_fee = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), default="Processing")
    items_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    user = db.relationship(
        "User",
        backref=db.backref("orders", lazy=True, order_by="desc(Order.created_at)")
    )

    def __repr__(self):
        return f"<Order {self.order_number}>"
