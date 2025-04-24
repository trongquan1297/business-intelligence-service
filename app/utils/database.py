# database.py
from clickhouse_driver import Client
from config import CLICKHOUSE_CONFIG, MYSQL_CONFIG
import mysql.connector


def get_clickhouse_client():
    return Client(
        host=CLICKHOUSE_CONFIG['host'],
        port=CLICKHOUSE_CONFIG['port'],
        user=CLICKHOUSE_CONFIG['user'],
        password=CLICKHOUSE_CONFIG['password'],
        database=CLICKHOUSE_CONFIG['database']
    )

def get_mysql_connection():
    return mysql.connector.connect(
        host=MYSQL_CONFIG['host'],
        port=MYSQL_CONFIG['port'],
        user=MYSQL_CONFIG['user'],
        password=MYSQL_CONFIG['password'],
        database=MYSQL_CONFIG['database']
    )

    
