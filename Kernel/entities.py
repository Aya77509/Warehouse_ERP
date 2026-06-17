from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


EXPIRY_WARNING_DAYS = 30  # alert if expiration is within this many days


class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class Product:
    id: int | None
    name: str
    quantity: int
    low_stock_threshold: int = 10
    supplier_id: int | None = None
    expiration_date: str | None = None  # format: "YYYY-MM-DD", None = no expiration

    def is_low_stock(self) -> bool:
        return self.quantity <= self.low_stock_threshold

    def days_until_expiration(self) -> int | None:
        """Returns the number of days until expiration, or None if not set."""
        if not self.expiration_date:
            return None
        try:
            exp_date = datetime.strptime(self.expiration_date, "%Y-%m-%d").date()
        except ValueError:
            return None
        return (exp_date - datetime.now().date()).days

    def is_expired(self) -> bool:
        days = self.days_until_expiration()
        return days is not None and days < 0

    def is_expiring_soon(self, threshold_days: int = EXPIRY_WARNING_DAYS) -> bool:
        """True if the product expires within `threshold_days` (including already expired)."""
        days = self.days_until_expiration()
        return days is not None and days <= threshold_days

    def validate(self):
        if not self.name or not self.name.strip():
            raise ValueError("Product name cannot be empty.")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if self.low_stock_threshold < 0:
            raise ValueError("Low stock threshold cannot be negative.")
        if self.expiration_date:
            try:
                datetime.strptime(self.expiration_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Expiration date must be in YYYY-MM-DD format.")


@dataclass
class Supplier:
    id: int | None
    name: str
    contact: str = ""
    email: str = ""
    address: str = ""

    def validate(self):
        if not self.name or not self.name.strip():
            raise ValueError("Supplier name cannot be empty.")


@dataclass
class StockMovement:
    id: int | None
    product_id: int
    product_name: str
    movement_type: MovementType
    quantity: int
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    note: str = ""

    def validate(self):
        if self.quantity <= 0:
            raise ValueError("Movement quantity must be greater than zero.")


@dataclass
class User:
    id: int | None
    username: str
    password_hash: str
    role: UserRole

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN