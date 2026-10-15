import psycopg
from psycopg.rows import dict_row


def get_connection():
    """Open a connection to the local RevenuePilot PostgreSQL database."""
    return psycopg.connect(
        "dbname=revenuepilot",
        row_factory=dict_row,
        connect_timeout=5,
    )
