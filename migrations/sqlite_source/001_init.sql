CREATE TABLE IF NOT EXISTS source_products (
    seller_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_sku_id TEXT NOT NULL,
    date TEXT NOT NULL,
    product_category_name TEXT,
    product_sub_category_name TEXT,
    product_department_name TEXT,
    product_brand TEXT,
    product_price TEXT,
    product_sold_quantity TEXT,
    product_stock_quantity INTEGER,
    product_stock_reserved_quantity INTEGER,
    product_stock_coverage_days INTEGER,
    PRIMARY KEY (seller_id, product_id, product_sku_id, date)
);
