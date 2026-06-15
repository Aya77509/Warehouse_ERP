import hashlib

from Infrastructure.user_repository import UserRepository
from Kernel.entities import User, UserRole


class AuthService:
    """Handles user authentication and role checks."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username: str, password: str) -> User:
        if not username or not password:
            raise ValueError("Username and password are required.")

        user = self.user_repo.get_by_username(username.strip())
        if user is None:
            raise ValueError("Invalid username or password.")

        if user.password_hash != self._hash_password(password):
            raise ValueError("Invalid username or password.")

        return user

    def register(self, username: str, password: str, role: UserRole = UserRole.USER) -> User:
        if not username or not password:
            raise ValueError("Username and password are required.")

        if self.user_repo.get_by_username(username.strip()) is not None:
            raise ValueError(f"User '{username}' already exists.")

        user = User(id=None, username=username.strip(), password_hash=self._hash_password(password), role=role)
        user.id = self.user_repo.add(user)
        return user