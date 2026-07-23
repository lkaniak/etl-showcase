CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(64) NOT NULL,
    seller_id VARCHAR(64) NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(32) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    shipping_state VARCHAR(64),
    shipping_city VARCHAR(128),
    coupon_code VARCHAR(64),
    PRIMARY KEY (order_id, seller_id, date)
);

CREATE TABLE IF NOT EXISTS order_payments (
    order_id VARCHAR(64) NOT NULL,
    payment_id VARCHAR(64) NOT NULL,
    seller_id VARCHAR(64) NOT NULL,
    method VARCHAR(64) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    paid_at DATE NOT NULL,
    PRIMARY KEY (order_id, payment_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(64) NOT NULL,
    product_sku_id VARCHAR(64) NOT NULL,
    seller_id VARCHAR(64) NOT NULL,
    date DATE NOT NULL,
    name VARCHAR(256),
    category VARCHAR(128),
    subcategory VARCHAR(128),
    department VARCHAR(128),
    brand VARCHAR(128),
    sales_price NUMERIC(12, 2),
    stock INT,
    reserved_stock INT,
    stock_coverage_in_days INT,
    PRIMARY KEY (product_id, product_sku_id, seller_id, date)
);

CREATE TABLE IF NOT EXISTS traffic (
    seller_id VARCHAR(64) NOT NULL,
    date DATE NOT NULL,
    source VARCHAR(128) NOT NULL,
    medium VARCHAR(128) NOT NULL,
    sessions INT NOT NULL,
    users INT NOT NULL,
    pageviews INT NOT NULL,
    PRIMARY KEY (seller_id, date, source, medium)
);
