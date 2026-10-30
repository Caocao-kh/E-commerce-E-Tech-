import random
import importlib.util
import sys
import os

# Load app.py directly
spec = importlib.util.spec_from_file_location("app_module", "app.py")
app_module = importlib.util.module_from_spec(spec)
sys.modules["app_module"] = app_module
spec.loader.exec_module(app_module)

app = app_module.app
db = app_module.db
User = app_module.User
Order = app_module.Order

def seed_database():
    with app.app_context():
        # Recreate the database
        db.drop_all()
        db.create_all()
        print("Database tables created.")

        # 1. Create Users
        # Admin user
        admin = User(
            username="admin",
            email="admin@e-tech.com",
            role="admin",
            phone="+1234567890",
            address="123 Admin St, Tech City, TC 10001",
            status=True
        )
        admin.set_password("admin123")
        db.session.add(admin)

        # Customers
        customers = []
        for i in range(1, 11):
            customer = User(
                username=f"customer{i}",
                email=f"customer{i}@example.com",
                role="customer",
                phone=f"+19876543{i:02d}",
                address=f"{i}00 Customer Ave, Web City, WC {10000+i}",
                status=True
            )
            customer.set_password("password123")
            customers.append(customer)
            db.session.add(customer)

        db.session.commit()
        print(f"Added Admin and {len(customers)} Customers.")

        # 2. Create Orders
        payment_methods = ["Credit / Debit Card", "PayPal", "Bank Transfer"]
        statuses = ["Processing", "Shipped", "Delivered", "Cancelled"]

        for i, customer in enumerate(customers):
            # Give each customer 1 to 3 orders
            num_orders = random.randint(1, 3)
            for j in range(num_orders):
                order_num = f"ORD-{1000 + i * 10 + j}-{random.randint(100, 999)}"
                subtotal = round(random.uniform(50.0, 1500.0), 2)
                shipping_fee = 15.0 if subtotal < 500 else 0.0
                
                order = Order(
                    order_number=order_num,
                    user_id=customer.id,
                    customer_name=customer.username,
                    customer_email=customer.email,
                    shipping_address=customer.address,
                    city=f"Web City {i}",
                    payment_method=random.choice(payment_methods),
                    subtotal=subtotal,
                    shipping_fee=shipping_fee,
                    total_amount=subtotal + shipping_fee,
                    status=random.choice(statuses),
                    items_summary=f"Item {random.randint(1, 5)} x {random.randint(1,3)}, Item {random.randint(6, 10)} x 1"
                )
                db.session.add(order)

        db.session.commit()
        print("Added sample orders.")
        print("Database seeded successfully with strong data!")

if __name__ == "__main__":
    seed_database()
