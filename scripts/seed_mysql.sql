CREATE DATABASE IF NOT EXISTS marketplace_source;
USE marketplace_source;

CREATE TABLE IF NOT EXISTS source_products (
    seller_id VARCHAR(64) NOT NULL,
    product_id VARCHAR(64) NOT NULL,
    product_sku_id VARCHAR(64) NOT NULL,
    date DATE NOT NULL,
    product_category_name VARCHAR(128),
    product_sub_category_name VARCHAR(128),
    product_department_name VARCHAR(128),
    product_brand VARCHAR(128),
    product_price VARCHAR(32),
    product_sold_quantity VARCHAR(32),
    product_stock_quantity INT,
    product_stock_reserved_quantity INT,
    product_stock_coverage_days INT,
    PRIMARY KEY (seller_id, product_id, product_sku_id, date)
);

INSERT INTO source_products VALUES
('seller_a', 'prod-1', 'sku-1', '2024-06-01', 'Electronics', 'Phones', 'Mobile', 'Acme', '999.90', '10', 50, 5, 12),
('seller_a', 'prod-2', 'sku-2', '2024-06-01', 'Home', 'Kitchen', 'Appliances', 'Beta', '450,00', '3', 20, 2, NULL),
('seller_a', 'prod-3', 'sku-3', '2024-06-01', 'Sports', NULL, NULL, 'Gamma', '120.00', NULL, 15, 1, 8);

INSERT INTO source_products VALUES
('seller_b', 'prod-9', 'sku-9', '2024-06-10', 'Fashion', 'Shoes', 'Footwear', 'Delta', '199.00', '5', 30, 3, 10);

INSERT INTO source_products VALUES
('seller_a', 'prod-1', 'sku-1', '2024-07-05', 'Electronics', 'Phones', 'Mobile', 'Acme', '979.90', '14', 42, 4, 9),
('seller_a', 'prod-4', 'sku-4', '2024-07-20', 'Home', 'Kitchen', 'Appliances', 'Beta', '210,00', '6', 12, 1, 7);

INSERT INTO source_products VALUES
('seller_b', 'prod-9', 'sku-9', '2024-07-12', 'Fashion', 'Shoes', 'Footwear', 'Delta', '189.00', '8', 22, 2, 6);
