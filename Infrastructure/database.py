import sqlite3
from pathlib import Path

DB_PATH = Path("warehouse.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn