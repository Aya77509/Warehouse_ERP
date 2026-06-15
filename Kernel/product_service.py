from Infrastructure.product_repository import ProductRepository
from Kernel.entities import Product


class ProductService:
    """Business logic for product management."""

    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    def create_product(self, name: str, quantity: int, low_stock_threshold: int = 10,
                        supplier_id: int | None = None) -> Product:
        product = Product(
            id=None,
            name=name.strip(),
            quantity=quantity,
            low_stock_threshold=low_stock_threshold,
            supplier_id=supplier_id
        )
        product.validate()
        product.id = self.product_repo.add(product)
        return product

    def update_product(self, product: Product):
        product.validate()
        if product.id is None:
            raise ValueError("Cannot update a product without an ID.")
        existing = self.product_repo.get_by_id(product.id)
        if existing is None:
            raise ValueError(f"Product with ID {product.id} does not exist.")
        self.product_repo.update(product)

    def delete_product(self, product_id: int):
        existing = self.product_repo.get_by_id(product_id)
        if existing is None:
            raise ValueError(f"Product with ID {product_id} does not exist.")
        self.product_repo.delete(product_id)

    def get_product(self, product_id: int) -> Product:
        product = self.product_repo.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Product with ID {product_id} does not exist.")
        return product

    def list_products(self) -> list[Product]:
        return self.product_repo.get_all()

    def search_products(self, keyword: str) -> list[Product]:
        if not keyword.strip():
            return self.product_repo.get_all()
        return self.product_repo.search(keyword.strip())

    def get_low_stock_products(self) -> list[Product]:
        return self.product_repo.get_low_stock()

    def get_total_stock(self) -> int:
        return self.product_repo.get_total_stock()

    def get_total_products(self) -> int:
        return self.product_repo.count()