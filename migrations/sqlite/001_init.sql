CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL,
    total_amount REAL NOT NULL,
    shipping_state TEXT,
    shipping_city TEXT,
    coupon_code TEXT,
    PRIMARY KEY (order_id, seller_id, date)
);

CREATE TABLE IF NOT EXISTS order_payments (
    order_id TEXT NOT NULL,
    payment_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    method TEXT NOT NULL,
    amount REAL NOT NULL,
    paid_at TEXT NOT NULL,
    PRIMARY KEY (order_id, payment_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT NOT NULL,
    product_sku_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    date TEXT NOT NULL,
    name TEXT,
    category TEXT,
    subcategory TEXT,
    department TEXT,
    brand TEXT,
    sales_price REAL,
    stock INTEGER,
    reserved_stock INTEGER,
    stock_coverage_in_days INTEGER,
    PRIMARY KEY (product_id, product_sku_id, seller_id, date)
);

CREATE TABLE IF NOT EXISTS traffic (
    seller_id TEXT NOT NULL,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    medium TEXT NOT NULL,
    sessions INTEGER NOT NULL,
    users INTEGER NOT NULL,
    pageviews INTEGER NOT NULL,
    PRIMARY KEY (seller_id, date, source, medium)
);
