import sqlite3
import os
import hashlib


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "warehouse.db")


class Database:
    """Handles raw SQLite connection and schema initialization."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_schema()
        self._migrate_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT DEFAULT '',
                email TEXT DEFAULT '',
                address TEXT DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                low_stock_threshold INTEGER NOT NULL DEFAULT 10,
                supplier_id INTEGER,
                expiration_date TEXT,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                date TEXT NOT NULL,
                note TEXT DEFAULT '',
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            )
        """)

        # Seed default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            user_hash = hashlib.sha256("user123".encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", admin_hash, "admin")
            )
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("user", user_hash, "user")
            )

        conn.commit()
        conn.close()

    def _migrate_schema(self):
        """
        Adds missing columns to existing tables.
        This fixes 'No item with that key' errors caused by an old DB
        that was created before new columns were added.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get existing columns for each table
        def get_columns(table: str) -> list[str]:
            cursor.execute(f"PRAGMA table_info({table})")
            return [row["name"] for row in cursor.fetchall()]

        # products table migrations
        product_cols = get_columns("products")
        if "low_stock_threshold" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN low_stock_threshold INTEGER NOT NULL DEFAULT 10")
        if "supplier_id" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN supplier_id INTEGER")
        if "expiration_date" not in product_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN expiration_date TEXT")

        # movements table migrations
        movement_cols = get_columns("movements")
        if "product_name" not in movement_cols:
            cursor.execute("ALTER TABLE movements ADD COLUMN product_name TEXT NOT NULL DEFAULT ''")
        if "note" not in movement_cols:
            cursor.execute("ALTER TABLE movements ADD COLUMN note TEXT DEFAULT ''")

        # suppliers table migrations
        supplier_cols = get_columns("suppliers")
        if "contact" not in supplier_cols:
            cursor.execute("ALTER TABLE suppliers ADD COLUMN contact TEXT DEFAULT ''")
        if "email" not in supplier_cols:
            cursor.execute("ALTER TABLE suppliers ADD COLUMN email TEXT DEFAULT ''")
        if "address" not in supplier_cols:
            cursor.execute("ALTER TABLE suppliers ADD COLUMN address TEXT DEFAULT ''")

        conn.commit()
        conn.close()
