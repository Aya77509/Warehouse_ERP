from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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

    def is_low_stock(self) -> bool:
        return self.quantity <= self.low_stock_threshold

    def validate(self):
        if not self.name or not self.name.strip():
            raise ValueError("Product name cannot be empty.")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if self.low_stock_threshold < 0:
            raise ValueError("Low stock threshold cannot be negative.")


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