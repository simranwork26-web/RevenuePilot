
from pathlib import Path


RAW_DATA_DIR = Path("data/raw/olist")

DATASET_MANIFEST = {
    "olist_customers_dataset.csv": {
        "expected_rows": 99_441,
        "required_columns": [
            "customer_id",
            "customer_unique_id",
        ],
    },
    "olist_geolocation_dataset.csv": {
        "expected_rows": 1_000_163,
        "required_columns": [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
    },
    "olist_order_items_dataset.csv": {
        "expected_rows": 112_650,
        "required_columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value",
        ],
    },
    "olist_order_payments_dataset.csv": {
        "expected_rows": 103_886,
        "required_columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_value",
        ],
    },
    "olist_order_reviews_dataset.csv": {
        "expected_rows": 99_224,
        "required_columns": [
            "review_id",
            "order_id",
            "review_score",
        ],
    },
    "olist_orders_dataset.csv": {
        "expected_rows": 99_441,
        "required_columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
        ],
    },
    "olist_products_dataset.csv": {
        "expected_rows": 32_951,
        "required_columns": [
            "product_id",
            "product_category_name",
        ],
    },
    "olist_sellers_dataset.csv": {
        "expected_rows": 3_095,
        "required_columns": [
            "seller_id",
        ],
    },
    "product_category_name_translation.csv": {
        "expected_rows": 71,
        "required_columns": [
            "product_category_name",
            "product_category_name_english",
        ],
    },
}
