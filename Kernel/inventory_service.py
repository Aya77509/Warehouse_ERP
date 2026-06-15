from datetime import datetime

from Infrastructure.product_repository import ProductRepository
from Infrastructure.movement_repository import MovementRepository
from Kernel.entities import StockMovement, MovementType


class InventoryService:
    """Business logic for stock movements (IN / OUT) with quantity validation."""

    def __init__(self, product_repo: ProductRepository, movement_repo: MovementRepository):
        self.product_repo = product_repo
        self.movement_repo = movement_repo

    def stock_in(self, product_id: int, quantity: int, note: str = "") -> StockMovement:
        if quantity <= 0:
            raise ValueError("Quantity for Stock IN must be greater than zero.")

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Product with ID {product_id} does not exist.")

        product.quantity += quantity
        self.product_repo.update(product)

        movement = StockMovement(
            id=None,
            product_id=product.id,
            product_name=product.name,
            movement_type=MovementType.IN,
            quantity=quantity,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note=note
        )
        movement.validate()
        movement.id = self.movement_repo.add(movement)
        return movement

    def stock_out(self, product_id: int, quantity: int, note: str = "") -> StockMovement:
        if quantity <= 0:
            raise ValueError("Quantity for Stock OUT must be greater than zero.")

        product = self.product_repo.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Product with ID {product_id} does not exist.")

        if product.quantity - quantity < 0:
            raise ValueError(
                f"Insufficient stock for '{product.name}'. "
                f"Available: {product.quantity}, Requested: {quantity}."
            )

        product.quantity -= quantity
        self.product_repo.update(product)

        movement = StockMovement(
            id=None,
            product_id=product.id,
            product_name=product.name,
            movement_type=MovementType.OUT,
            quantity=quantity,
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            note=note
        )
        movement.validate()
        movement.id = self.movement_repo.add(movement)
        return movement

    def get_history(self) -> list[StockMovement]:
        return self.movement_repo.get_all()

    def get_recent_movements(self, limit: int = 10) -> list[StockMovement]:
        return self.movement_repo.get_recent(limit)