from Infrastructure.database import Database
from Kernel.entities import StockMovement, MovementType


class MovementRepository:
    """Handles persistence of StockMovement entities."""

    def __init__(self, db: Database):
        self.db = db

    def add(self, movement: StockMovement) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO movements (product_id, product_name, movement_type, quantity, date, note) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (movement.product_id, movement.product_name, movement.movement_type.value,
                 movement.quantity, movement.date, movement.note)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_all(self) -> list[StockMovement]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movements ORDER BY id DESC")
            return [self._row_to_movement(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_recent(self, limit: int = 10) -> list[StockMovement]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM movements ORDER BY id DESC LIMIT ?", (limit,))
            return [self._row_to_movement(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def _row_to_movement(row) -> StockMovement:
        return StockMovement(
            id=row["id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            movement_type=MovementType(row["movement_type"]),
            quantity=row["quantity"],
            date=row["date"],
            note=row["note"]
        )