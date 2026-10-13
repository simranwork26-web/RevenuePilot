from pathlib import Path


RAW_DATA_DIR = Path("data/raw/olist")


DATASET_MANIFEST = {
    "olist_customers_dataset.csv": {
        "expected_rows": 99_441,
        "required_columns": [
            "customer_id",
            "customer_unique_id",
        ],
        "unique_columns": ["customer_id"],
        "foreign_keys": [],
        "optional_foreign_keys": [],
    },
    "olist_geolocation_dataset.csv": {
        "expected_rows": 1_000_163,
        "required_columns": [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
        "unique_columns": [],
        "foreign_keys": [],
        "optional_foreign_keys": [],
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
        "unique_columns": [],
        "foreign_keys": [
            {
                "column": "order_id",
                "parent_file": "olist_orders_dataset.csv",
                "parent_column": "order_id",
            },
            {
                "column": "product_id",
                "parent_file": "olist_products_dataset.csv",
                "parent_column": "product_id",
            },
            {
                "column": "seller_id",
                "parent_file": "olist_sellers_dataset.csv",
                "parent_column": "seller_id",
            },
        ],
        "optional_foreign_keys": [],
    },
    "olist_order_payments_dataset.csv": {
        "expected_rows": 103_886,
        "required_columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_value",
        ],
        "unique_columns": [],
        "foreign_keys": [
            {
                "column": "order_id",
                "parent_file": "olist_orders_dataset.csv",
                "parent_column": "order_id",
            }
        ],
        "optional_foreign_keys": [],
    },
    "olist_order_reviews_dataset.csv": {
        "expected_rows": 99_224,
        "required_columns": [
            "review_id",
            "order_id",
            "review_score",
        ],
        "unique_columns": [],
        "foreign_keys": [
            {
                "column": "order_id",
                "parent_file": "olist_orders_dataset.csv",
                "parent_column": "order_id",
            }
        ],
        "optional_foreign_keys": [],
    },
    "olist_orders_dataset.csv": {
        "expected_rows": 99_441,
        "required_columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
        ],
        "unique_columns": ["order_id"],
        "foreign_keys": [
            {
                "column": "customer_id",
                "parent_file": "olist_customers_dataset.csv",
                "parent_column": "customer_id",
            }
        ],
        "datetime_columns": [
            {"column": "order_purchase_timestamp", "allow_blank": False},
            {"column": "order_approved_at", "allow_blank": True},
            {"column": "order_delivered_carrier_date", "allow_blank": True},
            {"column": "order_delivered_customer_date", "allow_blank": True},
            {"column": "order_estimated_delivery_date", "allow_blank": False},
        ],
        "optional_foreign_keys": [],
    },
    "olist_products_dataset.csv": {
        "expected_rows": 32_951,
        "required_columns": [
            "product_id",
            "product_category_name",
        ],
        "unique_columns": ["product_id"],
        "foreign_keys": [],
        "optional_foreign_keys": [
            {
                "column": "product_category_name",
                "parent_file": "product_category_name_translation.csv",
                "parent_column": "product_category_name",
                "allowed_unmatched": [
                    "pc_gamer",
                    "portateis_cozinha_e_preparadores_de_alimentos",
                ],
            }
        ],
    },
    "olist_sellers_dataset.csv": {
        "expected_rows": 3_095,
        "required_columns": [
            "seller_id",
        ],
        "unique_columns": ["seller_id"],
        "foreign_keys": [],
        "optional_foreign_keys": [],
    },
    "product_category_name_translation.csv": {
        "expected_rows": 71,
        "required_columns": [
            "product_category_name",
            "product_category_name_english",
        ],
        "unique_columns": ["product_category_name"],
        "foreign_keys": [],
        "optional_foreign_keys": [],
    },
}
