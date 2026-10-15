CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_purchase_timestamp TIMESTAMP NOT NULL,
    item_count INTEGER,
    item_value NUMERIC(14, 2),
    freight_value NUMERIC(14, 2),
    payment_value NUMERIC(14, 2),
    review_score NUMERIC(3, 1),
    CONSTRAINT orders_item_count_nonnegative
        CHECK (item_count IS NULL OR item_count >= 0),
    CONSTRAINT orders_item_value_nonnegative
        CHECK (item_value IS NULL OR item_value >= 0),
    CONSTRAINT orders_freight_value_nonnegative
        CHECK (freight_value IS NULL OR freight_value >= 0),
    CONSTRAINT orders_payment_value_nonnegative
        CHECK (payment_value IS NULL OR payment_value >= 0),
    CONSTRAINT orders_review_score_range
        CHECK (review_score IS NULL OR review_score BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS category_analytics (
    category TEXT PRIMARY KEY,
    item_count BIGINT NOT NULL CHECK (item_count >= 0),
    order_count BIGINT NOT NULL CHECK (order_count >= 0),
    delivered_item_count BIGINT NOT NULL CHECK (delivered_item_count >= 0),
    delivered_order_count BIGINT NOT NULL CHECK (delivered_order_count >= 0),
    item_value_total NUMERIC(16, 2) NOT NULL,
    delivered_item_value NUMERIC(16, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_segmentation (
    customer_unique_id TEXT PRIMARY KEY,
    order_count BIGINT NOT NULL CHECK (order_count >= 0),
    first_purchase TIMESTAMP NOT NULL,
    last_purchase TIMESTAMP NOT NULL,
    delivered_order_count BIGINT NOT NULL CHECK (delivered_order_count >= 0),
    delivered_item_value NUMERIC(16, 2) NOT NULL,
    delivered_payment_value NUMERIC(16, 2) NOT NULL,
    recency_days INTEGER NOT NULL CHECK (recency_days >= 0),
    segment TEXT NOT NULL,
    reference_date DATE NOT NULL,
    high_value_threshold NUMERIC(24, 14)
);

CREATE TABLE IF NOT EXISTS monthly_revenue_analytics (
    month DATE PRIMARY KEY,
    order_count BIGINT NOT NULL CHECK (order_count >= 0),
    delivered_order_count BIGINT NOT NULL CHECK (delivered_order_count >= 0),
    item_value_total NUMERIC(16, 2) NOT NULL,
    delivered_item_value NUMERIC(16, 2) NOT NULL,
    recorded_payment_value_total NUMERIC(16, 2) NOT NULL,
    low_volume_month BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS regional_analytics (
    customer_state TEXT PRIMARY KEY,
    order_count BIGINT NOT NULL CHECK (order_count >= 0),
    delivered_order_count BIGINT NOT NULL CHECK (delivered_order_count >= 0),
    unique_customer_count BIGINT NOT NULL CHECK (unique_customer_count >= 0),
    item_value_total NUMERIC(16, 2) NOT NULL,
    delivered_item_value NUMERIC(16, 2) NOT NULL,
    freight_value_total NUMERIC(16, 2) NOT NULL,
    average_delivered_item_value_per_order NUMERIC(16, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_purchase_timestamp
    ON orders (order_purchase_timestamp);

CREATE INDEX IF NOT EXISTS idx_orders_customer_unique_id
    ON orders (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders (order_status);
