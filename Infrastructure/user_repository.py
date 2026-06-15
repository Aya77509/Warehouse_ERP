from Infrastructure.database import Database
from Kernel.entities import User, UserRole


class UserRepository:
    """Handles persistence of User entities."""

    def __init__(self, db: Database):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None
        finally:
            conn.close()

    def add(self, user: User) -> int:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (user.username, user.password_hash, user.role.value)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_all(self) -> list[User]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id")
            return [self._row_to_user(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            role=UserRole(row["role"])
        )