# app/products.py


# ============================================================
# E-TECH PRODUCT DATA
# ============================================================

products = [

    # ========================================================
    # SMARTPHONES
    # ========================================================

    {
        "id": 1,
        "title": "iPhone 17 Pro Max",
        "isNew": True,
        "oldPrice": 1499,
        "price": 1399,
        "discountedPrice": 1329.05,
        "description": "The iPhone 17 Pro Max delivers powerful performance, an advanced camera system, a stunning display, and long-lasting battery life for everyday and professional use.",
        "category": "smartphones",
        "type": "iphone",
        "stock": 25,
        "brand": "Apple",
        "size": "6.9 inch",
        "color": ["Black Titanium", "Silver", "Natural Titanium"],
        "storage": ["256GB", "512GB", "1TB"],
        "image": "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd",
        "rating": 4.9,
    },

    {
        "id": 2,
        "title": "Samsung Galaxy S26 Ultra",
        "isNew": True,
        "oldPrice": 1399,
        "price": 1299,
        "discountedPrice": 1234.05,
        "description": "A premium Android smartphone featuring a high-resolution display, powerful processor, advanced camera system, and all-day battery performance.",
        "category": "smartphones",
        "type": "android-phone",
        "stock": 30,
        "brand": "Samsung",
        "size": "6.8 inch",
        "color": ["Black", "Silver", "Blue"],
        "storage": ["256GB", "512GB", "1TB"],
        "image": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf",
        "rating": 4.8,
    },

    {
        "id": 3,
        "title": "Google Pixel 10 Pro",
        "isNew": True,
        "oldPrice": 1099,
        "price": 999,
        "discountedPrice": 949.05,
        "description": "A premium Google smartphone with an intelligent camera system, smooth display, powerful performance, and clean Android experience.",
        "category": "smartphones",
        "type": "android-phone",
        "stock": 22,
        "brand": "Google",
        "size": "6.7 inch",
        "color": ["Obsidian", "Porcelain"],
        "storage": ["128GB", "256GB", "512GB"],
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97",
        "rating": 4.7,
    },

    {
        "id": 4,
        "title": "OnePlus 13 Pro",
        "isNew": True,
        "oldPrice": 899,
        "price": 799,
        "discountedPrice": 759.05,
        "description": "A high-performance Android smartphone featuring a smooth AMOLED display, fast charging, powerful processor, and advanced cameras.",
        "category": "smartphones",
        "type": "android-phone",
        "stock": 28,
        "brand": "OnePlus",
        "size": "6.8 inch",
        "color": ["Black", "Blue"],
        "storage": ["256GB", "512GB"],
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97",
        "rating": 4.6,
    },


    # ========================================================
    # LAPTOPS
    # ========================================================

    {
        "id": 5,
        "title": "MacBook Pro M4",
        "isNew": True,
        "oldPrice": 2499,
        "price": 2299,
        "discountedPrice": 2184.05,
        "description": "MacBook Pro powered by the Apple M4 chip, designed for developers, designers, students, and professionals who need high performance and reliability.",
        "category": "laptops",
        "type": "macbook",
        "stock": 15,
        "brand": "Apple",
        "size": "16 inch",
        "color": ["Space Black", "Silver"],
        "storage": ["512GB", "1TB", "2TB"],
        "ram": ["16GB", "24GB", "36GB"],
        "image": "https://images.unsplash.com/photo-1517336714739-489689fd1ca8",
        "rating": 4.9,
    },

    {
        "id": 6,
        "title": "ASUS ROG Strix G16",
        "isNew": True,
        "oldPrice": 1899,
        "price": 1699,
        "discountedPrice": 1614.05,
        "description": "A powerful gaming laptop built for demanding games, creative applications, and multitasking with a high-refresh-rate display and dedicated graphics.",
        "category": "laptops",
        "type": "gaming-laptop",
        "stock": 12,
        "brand": "ASUS",
        "size": "16 inch",
        "color": ["Eclipse Gray"],
        "storage": ["1TB"],
        "ram": ["16GB", "32GB"],
        "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302",
        "rating": 4.7,
    },

    {
        "id": 7,
        "title": "Dell XPS 15",
        "isNew": False,
        "oldPrice": 1799,
        "price": 1599,
        "discountedPrice": 1519.05,
        "description": "A premium Windows laptop featuring a powerful processor, high-quality display, sleek aluminum design, and excellent performance for work and study.",
        "category": "laptops",
        "type": "ultrabook",
        "stock": 16,
        "brand": "Dell",
        "size": "15.6 inch",
        "color": ["Silver"],
        "storage": ["512GB", "1TB"],
        "ram": ["16GB", "32GB"],
        "image": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6",
        "rating": 4.6,
    },

    {
        "id": 8,
        "title": "Lenovo Legion 7",
        "isNew": False,
        "oldPrice": 1999,
        "price": 1799,
        "discountedPrice": 1709.05,
        "description": "A high-performance gaming laptop designed for demanding games, creative workloads, and multitasking.",
        "category": "laptops",
        "type": "gaming-laptop",
        "stock": 10,
        "brand": "Lenovo",
        "size": "16 inch",
        "color": ["Storm Gray"],
        "storage": ["1TB", "2TB"],
        "ram": ["16GB", "32GB"],
        "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302",
        "rating": 4.7,
    },


    # ========================================================
    # TABLETS
    # ========================================================

    {
        "id": 9,
        "title": "iPad Pro M5",
        "isNew": True,
        "oldPrice": 1299,
        "price": 1199,
        "discountedPrice": 1139.05,
        "description": "A powerful professional tablet with a stunning display, fast processor, premium design, and support for creative and productivity workflows.",
        "category": "tablets",
        "type": "ipad",
        "stock": 20,
        "brand": "Apple",
        "size": "13 inch",
        "color": ["Space Black", "Silver"],
        "storage": ["256GB", "512GB", "1TB"],
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0",
        "rating": 4.8,
    },

    {
        "id": 10,
        "title": "Samsung Galaxy Tab S11",
        "isNew": True,
        "oldPrice": 899,
        "price": 799,
        "discountedPrice": 759.05,
        "description": "A premium Android tablet designed for entertainment, study, productivity, and creative work with a large immersive display.",
        "category": "tablets",
        "type": "android-tablet",
        "stock": 25,
        "brand": "Samsung",
        "size": "12.4 inch",
        "color": ["Gray", "Silver"],
        "storage": ["256GB", "512GB"],
        "image": "https://images.unsplash.com/photo-1561154464-82e9adf32764",
        "rating": 4.6,
    },


    # ========================================================
    # SMARTWATCHES
    # ========================================================

    {
        "id": 11,
        "title": "Apple Watch Ultra 3",
        "isNew": False,
        "oldPrice": 899,
        "price": 799,
        "discountedPrice": 759.05,
        "description": "A rugged premium smartwatch with health tracking, fitness features, GPS, notifications, and a durable design for active lifestyles.",
        "category": "smartwatches",
        "type": "smartwatch",
        "stock": 18,
        "brand": "Apple",
        "size": "49mm",
        "color": ["Titanium"],
        "image": "https://images.unsplash.com/photo-1544117519-31a4b719223d",
        "rating": 4.8,
    },

    {
        "id": 12,
        "title": "Samsung Galaxy Watch 8",
        "isNew": False,
        "oldPrice": 399,
        "price": 349,
        "discountedPrice": 331.55,
        "description": "A stylish smartwatch featuring health monitoring, fitness tracking, notifications, GPS, and seamless Android integration.",
        "category": "smartwatches",
        "type": "smartwatch",
        "stock": 30,
        "brand": "Samsung",
        "size": "44mm",
        "color": ["Black", "Silver"],
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
        "rating": 4.5,
    },


    # ========================================================
    # AUDIO
    # ========================================================

    {
        "id": 13,
        "title": "Sony WH-1000XM6",
        "isNew": False,
        "oldPrice": 449,
        "price": 399,
        "discountedPrice": 379.05,
        "description": "Premium wireless headphones with advanced noise cancellation, immersive sound quality, comfortable ear cushions, and long battery life.",
        "category": "audio",
        "type": "headphones",
        "stock": 40,
        "brand": "Sony",
        "color": ["Black", "Silver"],
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
        "rating": 4.8,
    },

    {
        "id": 14,
        "title": "AirPods Pro 3",
        "isNew": False,
        "oldPrice": 299,
        "price": 249,
        "discountedPrice": 236.55,
        "description": "Wireless earbuds with active noise cancellation, immersive audio, comfortable fit, and seamless connectivity with Apple devices.",
        "category": "audio",
        "type": "earbuds",
        "stock": 50,
        "brand": "Apple",
        "color": ["White"],
        "image": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1",
        "rating": 4.7,
    },

    {
        "id": 15,
        "title": "JBL Charge 6",
        "isNew": True,
        "oldPrice": 199,
        "price": 169,
        "discountedPrice": 160.55,
        "description": "A portable Bluetooth speaker delivering powerful sound, long battery life, and a durable design for indoor and outdoor listening.",
        "category": "audio",
        "type": "bluetooth-speaker",
        "stock": 35,
        "brand": "JBL",
        "color": ["Black", "Blue"],
        "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1",
        "rating": 4.6,
    },


    # ========================================================
    # CAMERAS
    # ========================================================

    {
        "id": 16,
        "title": "Canon EOS R50",
        "isNew": False,
        "oldPrice": 999,
        "price": 899,
        "discountedPrice": 854.05,
        "description": "A compact mirrorless camera designed for photography and video creation with excellent image quality and easy-to-use controls.",
        "category": "cameras",
        "type": "mirrorless-camera",
        "stock": 10,
        "brand": "Canon",
        "color": ["Black"],
        "image": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32",
        "rating": 4.7,
    },

    {
        "id": 17,
        "title": "Sony Alpha A7 IV",
        "isNew": False,
        "oldPrice": 2799,
        "price": 2499,
        "discountedPrice": 2374.05,
        "description": "A professional full-frame mirrorless camera offering high-resolution photography, advanced autofocus, and powerful video capabilities.",
        "category": "cameras",
        "type": "mirrorless-camera",
        "stock": 8,
        "brand": "Sony",
        "color": ["Black"],
        "image": "https://images.unsplash.com/photo-1510127034890-ba27508e9f1c",
        "rating": 4.9,
    },


    # ========================================================
    # MONITORS
    # ========================================================

    {
        "id": 18,
        "title": "LG UltraGear 27 Gaming Monitor",
        "isNew": False,
        "oldPrice": 499,
        "price": 399,
        "discountedPrice": 379.05,
        "description": "A high-performance gaming monitor with a fast refresh rate, sharp resolution, and responsive display technology for competitive gaming.",
        "category": "monitors",
        "type": "gaming-monitor",
        "stock": 20,
        "brand": "LG",
        "size": "27 inch",
        "color": ["Black"],
        "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf",
        "rating": 4.6,
    },

    {
        "id": 19,
        "title": "Samsung Odyssey G7",
        "isNew": False,
        "oldPrice": 799,
        "price": 699,
        "discountedPrice": 664.05,
        "description": "A premium curved gaming monitor designed for immersive gameplay with high refresh rates, fast response times, and excellent image quality.",
        "category": "monitors",
        "type": "gaming-monitor",
        "stock": 14,
        "brand": "Samsung",
        "size": "32 inch",
        "color": ["Black"],
        "image": "https://images.unsplash.com/photo-1585792180666-f7347c490ee2",
        "rating": 4.7,
    },


    # ========================================================
    # GAMING
    # ========================================================

    {
        "id": 20,
        "title": "PlayStation 5 Pro",
        "isNew": False,
        "oldPrice": 799,
        "price": 699,
        "discountedPrice": 664.05,
        "description": "A powerful gaming console delivering high-quality graphics, fast loading times, immersive gameplay, and access to a large game library.",
        "category": "gaming",
        "type": "gaming-console",
        "stock": 10,
        "brand": "Sony",
        "storage": "2TB",
        "color": ["White"],
        "image": "https://images.unsplash.com/photo-1606813907291-d86efa9b94db",
        "rating": 4.8,
    },

    {
        "id": 21,
        "title": "Xbox Series X",
        "isNew": False,
        "oldPrice": 599,
        "price": 549,
        "discountedPrice": 521.55,
        "description": "A powerful next-generation gaming console with fast loading, high-resolution gaming, and a large collection of games.",
        "category": "gaming",
        "type": "gaming-console",
        "stock": 12,
        "brand": "Microsoft",
        "storage": "1TB",
        "color": ["Black"],
        "image": "https://images.unsplash.com/photo-1621259182978-fbf93132d53d",
        "rating": 4.7,
    },


    # ========================================================
    # ACCESSORIES
    # ========================================================

    {
        "id": 22,
        "title": "Anker 737 Power Bank",
        "isNew": False,
        "oldPrice": 159,
        "price": 129,
        "discountedPrice": 122.55,
        "description": "A high-capacity portable power bank with fast charging technology, designed to keep smartphones, tablets, and other devices powered throughout the day.",
        "category": "accessories",
        "type": "power-bank",
        "stock": 60,
        "brand": "Anker",
        "capacity": "24000mAh",
        "color": ["Black"],
        "image": "https://images.unsplash.com/photo-1609592424946-5c7e5a5b1a9a",
        "rating": 4.6,
    },

    {
        "id": 23,
        "title": "Apple Magic Keyboard",
        "isNew": False,
        "oldPrice": 129,
        "price": 99,
        "discountedPrice": 94.05,
        "description": "A sleek wireless keyboard with a comfortable typing experience and reliable connectivity, perfect for work and everyday productivity.",
        "category": "accessories",
        "type": "keyboard",
        "stock": 45,
        "brand": "Apple",
        "color": ["White"],
        "image": "https://images.unsplash.com/photo-1587829741301-dc798b83add3",
        "rating": 4.5,
    },

    {
        "id": 24,
        "title": "Logitech MX Master 4",
        "isNew": False,
        "oldPrice": 129,
        "price": 99,
        "discountedPrice": 94.05,
        "description": "A premium wireless mouse designed for productivity with ergonomic comfort, precise tracking, customizable controls, and multi-device support.",
        "category": "accessories",
        "type": "mouse",
        "stock": 50,
        "brand": "Logitech",
        "color": ["Black", "Gray"],
        "image": "https://images.unsplash.com/photo-1527814050087-3793815479db",
        "rating": 4.7,
    },
]


# ============================================================
# PRODUCT FUNCTIONS
# ============================================================

def get_all_products():
    return products


def get_product_by_id(product_id):
    for p in products:
        if p.get("id") == int(product_id):
            return p
    return None


