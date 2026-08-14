DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE sellers (
    seller_id               VARCHAR(64) PRIMARY KEY,
    seller_zip_code_prefix  VARCHAR(10),
    seller_city             VARCHAR(128),
    seller_state            VARCHAR(2)
);

CREATE TABLE products (
    product_id                     VARCHAR(64) PRIMARY KEY,
    product_category_name          VARCHAR(128),
    product_category_name_english  VARCHAR(128),
    product_name_lenght            INTEGER,
    product_description_lenght     INTEGER,
    product_photos_qty             INTEGER,
    product_weight_g               NUMERIC,
    product_length_cm              NUMERIC,
    product_height_cm              NUMERIC,
    product_width_cm               NUMERIC
);

CREATE TABLE orders (
    order_id                        VARCHAR(64) PRIMARY KEY,
    customer_id                     VARCHAR(64),
    seller_id                       VARCHAR(64) REFERENCES sellers(seller_id),
    product_id                      VARCHAR(64) REFERENCES products(product_id),
    order_status                    VARCHAR(32),
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP,
    price                           NUMERIC,
    freight_value                   NUMERIC,
    customer_state                  VARCHAR(2),
    delivery_delay_days             NUMERIC,
    is_late                         SMALLINT,
    distance_km                     NUMERIC
);

CREATE INDEX idx_orders_purchase_date ON orders (order_purchase_timestamp);
CREATE INDEX idx_sellers_state        ON sellers (seller_state);


CREATE INDEX idx_orders_seller_id  ON orders (seller_id);
CREATE INDEX idx_orders_product_id ON orders (product_id);
