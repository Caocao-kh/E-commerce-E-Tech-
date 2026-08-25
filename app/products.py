# ============================================================
# PRODUCTS
# ============================================================

products = [

    {
        "id": 1,
        "name": "iPhone 15 Pro",
        "brand": "Apple",
        "category": "Smartphones",
        "price": 999.00,
        "old_price": 1099.00,
        "stock": 15,
        "rating": 4.8,
        "image": "iphone-15-pro.jpg",
        "description": "Premium Apple smartphone with powerful performance and advanced camera system."
    },

    {
        "id": 2,
        "name": "Samsung Galaxy S24 Ultra",
        "brand": "Samsung",
        "category": "Smartphones",
        "price": 1199.00,
        "old_price": 1299.00,
        "stock": 12,
        "rating": 4.9,
        "image": "s24-ultra.jpg",
        "description": "Flagship Samsung smartphone with S Pen, advanced cameras and powerful performance."
    },

    {
        "id": 3,
        "name": "MacBook Air M3",
        "brand": "Apple",
        "category": "Laptops",
        "price": 1099.00,
        "old_price": 1199.00,
        "stock": 10,
        "rating": 4.9,
        "image": "macbook-air-m3.jpg",
        "description": "Lightweight MacBook Air powered by Apple's M3 chip."
    },

    {
        "id": 4,
        "name": "ASUS TUF Gaming F15",
        "brand": "ASUS",
        "category": "Laptops",
        "price": 899.00,
        "old_price": 999.00,
        "stock": 8,
        "rating": 4.7,
        "image": "asus-tuf-f15.jpg",
        "description": "Gaming laptop designed for powerful performance and everyday productivity."
    },

    {
        "id": 5,
        "name": "Sony WH-1000XM5",
        "brand": "Sony",
        "category": "Headphones",
        "price": 349.00,
        "old_price": 399.00,
        "stock": 20,
        "rating": 4.8,
        "image": "sony-xm5.jpg",
        "description": "Premium wireless noise-cancelling headphones."
    },

    {
        "id": 6,
        "name": "AirPods Pro 2",
        "brand": "Apple",
        "category": "Headphones",
        "price": 249.00,
        "old_price": 279.00,
        "stock": 25,
        "rating": 4.8,
        "image": "airpods-pro-2.jpg",
        "description": "Wireless earbuds with active noise cancellation and spatial audio."
    },

    {
        "id": 7,
        "name": "Apple Watch Series 9",
        "brand": "Apple",
        "category": "Smartwatches",
        "price": 399.00,
        "old_price": 429.00,
        "stock": 14,
        "rating": 4.7,
        "image": "apple-watch-9.jpg",
        "description": "Smartwatch with health, fitness and productivity features."
    },

    {
        "id": 8,
        "name": "Samsung Galaxy Watch 6",
        "brand": "Samsung",
        "category": "Smartwatches",
        "price": 299.00,
        "old_price": 329.00,
        "stock": 18,
        "rating": 4.6,
        "image": "galaxy-watch-6.jpg",
        "description": "Modern smartwatch with health tracking and smart features."
    },

    {
        "id": 9,
        "name": "iPad Air M2",
        "brand": "Apple",
        "category": "Tablets",
        "price": 599.00,
        "old_price": 649.00,
        "stock": 11,
        "rating": 4.8,
        "image": "ipad-air-m2.jpg",
        "description": "Powerful and versatile tablet powered by Apple's M2 chip."
    },

    {
        "id": 10,
        "name": "Samsung Galaxy Tab S9",
        "brand": "Samsung",
        "category": "Tablets",
        "price": 699.00,
        "old_price": 749.00,
        "stock": 9,
        "rating": 4.7,
        "image": "galaxy-tab-s9.jpg",
        "description": "Premium Android tablet with a high-quality display and S Pen."
    },

    {
        "id": 11,
        "name": "Logitech MX Master 3S",
        "brand": "Logitech",
        "category": "Accessories",
        "price": 99.00,
        "old_price": 119.00,
        "stock": 30,
        "rating": 4.8,
        "image": "mx-master-3s.jpg",
        "description": "Advanced wireless mouse designed for productivity."
    },

    {
        "id": 12,
        "name": "Keychron K2",
        "brand": "Keychron",
        "category": "Accessories",
        "price": 89.00,
        "old_price": 109.00,
        "stock": 22,
        "rating": 4.7,
        "image": "keychron-k2.jpg",
        "description": "Compact wireless mechanical keyboard."
    }

]


# ============================================================
# GET PRODUCT BY ID
# ============================================================

def get_product_by_id(product_id):

    for product in products:

        if product["id"] == product_id:
            return product

    return None


# ============================================================
# GET PRODUCTS BY CATEGORY
# ============================================================

def get_product_by_category(category):

    category = category.lower()

    return [
        product
        for product in products
        if product["category"].lower() == category
    ]


# ============================================================
# GET PRODUCTS BY BRAND
# ============================================================

def get_product_by_brand(brand):

    brand = brand.lower()

    return [
        product
        for product in products
        if product["brand"].lower() == brand
    ]