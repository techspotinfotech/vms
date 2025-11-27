import mysql.connector
from config import DB_CONFIG

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG.get('port', 3306)  # cloud DB needs port
        )
        return conn
    except Exception as e:
        print("DATABASE CONNECTION ERROR:", e)
        return None
