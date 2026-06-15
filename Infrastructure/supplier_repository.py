from Infrastructure.database import Database
from Kernel.entities import Supplier


class SupplierRepository:
    """Handles persistence of Supplier entities."""

    def __init__(self, db: Database):
        self.db = db

    def add(self, supplier: Supplier) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO suppliers (name, contact, email, address) VALUES (?, ?, ?, ?)",
                (supplier.name, supplier.contact, supplier.email, supplier.address)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update(self, supplier: Supplier):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE suppliers SET name=?, contact=?, email=?, address=? WHERE id=?",
                (supplier.name, supplier.contact, supplier.email, supplier.address, supplier.id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, supplier_id: int):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
            conn.commit()
        finally:
            conn.close()

    def get_by_id(self, supplier_id: int) -> Supplier | None:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,))
            row = cursor.fetchone()
            return self._row_to_supplier(row) if row else None
        finally:
            conn.close()

    def get_all(self) -> list[Supplier]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers ORDER BY id")
            return [self._row_to_supplier(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def _row_to_supplier(row) -> Supplier:
        return Supplier(
            id=row["id"],
            name=row["name"],
            contact=row["contact"],
            email=row["email"],
            address=row["address"]
        )