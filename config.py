import os

SECRET_KEY = "techspot_vms_secret_123"

DB_CONFIG = {
    'host': os.getenv("DB_HOST", "sql12.freesqldatabase.com"),
    'user': os.getenv("DB_USER", "sql1278945"),
    'password': os.getenv("DB_PASS", "9sd8sd8sd8"),
    'database': os.getenv("DB_NAME", "sql1278945"),
    'port': int(os.getenv("DB_PORT", 3306))
}
