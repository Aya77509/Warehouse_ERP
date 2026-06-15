from Infrastructure.database import Database
from Kernel.entities import Product


class ProductRepository:
    """Handles persistence of Product entities. No business logic here."""

    def __init__(self, db: Database):
        self.db = db

    def add(self, product: Product) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, quantity, low_stock_threshold, supplier_id) "
                "VALUES (?, ?, ?, ?)",
                (product.name, product.quantity, product.low_stock_threshold, product.supplier_id)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update(self, product: Product):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET name=?, quantity=?, low_stock_threshold=?, supplier_id=? WHERE id=?",
                (product.name, product.quantity, product.low_stock_threshold, product.supplier_id, product.id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, product_id: int):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()
        finally:
            conn.close()

    def get_by_id(self, product_id: int) -> Product | None:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
            row = cursor.fetchone()
            return self._row_to_product(row) if row else None
        finally:
            conn.close()

    def get_all(self) -> list[Product]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY id")
            return [self._row_to_product(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def search(self, keyword: str) -> list[Product]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE ? ORDER BY id",
                (f"%{keyword}%",)
            )
            return [self._row_to_product(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_low_stock(self) -> list[Product]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE quantity <= low_stock_threshold ORDER BY id")
            return [self._row_to_product(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_total_stock(self) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM products")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def count(self) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    @staticmethod
    def _row_to_product(row) -> Product:
        return Product(
            id=row["id"],
            name=row["name"],
            quantity=row["quantity"],
            low_stock_threshold=row["low_stock_threshold"],
            supplier_id=row["supplier_id"]
        )