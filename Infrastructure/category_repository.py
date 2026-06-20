from Infrastructure.database import Database
from Kernel.entities import Category


class CategoryRepository:
    """Handles persistence of Category entities."""

    def __init__(self, db: Database):
        self.db = db

    def _get_smallest_available_id(self, cursor) -> int:
        """Finds the smallest unused ID (fills gaps left by deleted categories)."""
        cursor.execute("SELECT id FROM categories ORDER BY id")
        existing_ids = [row["id"] for row in cursor.fetchall()]

        expected_id = 1
        for current_id in existing_ids:
            if current_id != expected_id:
                return expected_id
            expected_id += 1
        return expected_id

    def add(self, category: Category) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            new_id = self._get_smallest_available_id(cursor)
            cursor.execute(
                "INSERT INTO categories (id, name) VALUES (?, ?)",
                (new_id, category.name)
            )
            conn.commit()
            return new_id
        finally:
            conn.close()

    def update(self, category: Category):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE categories SET name=? WHERE id=?",
                (category.name, category.id)
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, category_id: int):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE id=?", (category_id,))
            conn.commit()
        finally:
            conn.close()

    def get_by_id(self, category_id: int) -> Category | None:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE id=?", (category_id,))
            row = cursor.fetchone()
            return self._row_to_category(row) if row else None
        finally:
            conn.close()

    def get_all(self) -> list[Category]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name")
            return [self._row_to_category(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            if exclude_id is None:
                cursor.execute(
                    "SELECT COUNT(*) FROM categories WHERE LOWER(name) = LOWER(?)", (name,)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM categories WHERE LOWER(name) = LOWER(?) AND id != ?",
                    (name, exclude_id)
                )
            return cursor.fetchone()[0] > 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_category(row) -> Category:
        return Category(
            id=row["id"],
            name=row["name"],
        )
